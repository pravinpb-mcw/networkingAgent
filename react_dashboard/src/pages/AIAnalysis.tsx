import { useEffect, useState, type ReactNode } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Bot, Clock, FileText, ChevronDown, ChevronUp, RefreshCw, Power, PowerOff, Loader2 } from 'lucide-react';
import { getAnalysisHistory, getSystemStatus, startSystem, stopSystem, AnalysisEntry, SystemStatus } from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

export default function AIAnalysis() {
  const context = useOutletContext<{ refreshTrigger: number }>();
  const refreshTrigger = context?.refreshTrigger ?? 0;
  const [history, setHistory] = useState<AnalysisEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set([0])); // First item expanded by default
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);

  const isConnected = systemStatus && (
    systemStatus.agent1 === 'running' || 
    systemStatus.agent2 === 'running' || 
    systemStatus.agent3 === 'running'
  );

  const fetchStatus = async () => {
    try {
      const status = await getSystemStatus();
      setSystemStatus(status);
    } catch (error) {
      console.error("Failed to fetch system status", error);
      setSystemStatus(null);
    }
  };

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await getAnalysisHistory();
      // Sort by timestamp desc
      const sorted = data.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
      setHistory(sorted);
    } catch (error) {
      console.error("Failed to fetch analysis history", error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    setConnecting(true);
    try {
      await startSystem();
      // Wait a moment for agents to start
      await new Promise(resolve => setTimeout(resolve, 2000));
      await fetchStatus();
      await fetchHistory();
    } catch (error) {
      console.error("Failed to connect agents", error);
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    setDisconnecting(true);
    try {
      await stopSystem();
      await new Promise(resolve => setTimeout(resolve, 1000));
      await fetchStatus();
    } catch (error) {
      console.error("Failed to disconnect agents", error);
    } finally {
      setDisconnecting(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchHistory();
  }, [refreshTrigger]);

  useEffect(() => {
    // Poll for status changes every 5 seconds
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const toggleExpanded = (index: number) => {
    setExpandedItems(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  // Simple markdown to HTML converter for the analysis reports
  const renderMarkdown = (markdown: string) => {
    const lines = markdown.split('\n');
    const elements: ReactNode[] = [];
    let inTable = false;
    let tableRows: string[][] = [];
    let tableHeaders: string[] = [];

    const flushTable = () => {
      if (tableHeaders.length > 0) {
        elements.push(
          <div key={`table-${elements.length}`} className="overflow-x-auto my-3">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-border">
                  {tableHeaders.map((h, i) => (
                    <th key={i} className="text-left p-2 font-semibold text-muted-foreground">{h.trim()}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tableRows.map((row, ri) => (
                  <tr key={ri} className="border-b border-border/50">
                    {row.map((cell, ci) => (
                      <td key={ci} className="p-2">{cell.trim()}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        tableHeaders = [];
        tableRows = [];
      }
    };

    lines.forEach((line, i) => {
      // Table detection
      if (line.startsWith('|') && line.endsWith('|')) {
        const cells = line.split('|').filter(c => c.trim() !== '');
        if (!inTable) {
          inTable = true;
          tableHeaders = cells;
        } else if (line.includes('---')) {
          // Skip separator row
        } else {
          tableRows.push(cells);
        }
        return;
      } else if (inTable) {
        flushTable();
        inTable = false;
      }

      // Headers
      if (line.startsWith('# ')) {
        elements.push(<h1 key={i} className="text-xl font-bold mt-4 mb-2 text-primary">{line.slice(2)}</h1>);
      } else if (line.startsWith('## ')) {
        elements.push(<h2 key={i} className="text-lg font-semibold mt-4 mb-2 text-primary/90">{line.slice(3)}</h2>);
      } else if (line.startsWith('### ')) {
        elements.push(<h3 key={i} className="text-base font-semibold mt-3 mb-1">{line.slice(4)}</h3>);
      } else if (line.startsWith('**') && line.endsWith('**')) {
        elements.push(<p key={i} className="font-semibold my-1">{line.slice(2, -2)}</p>);
      } else if (line.startsWith('- ')) {
        elements.push(<li key={i} className="ml-4 my-0.5 list-disc">{line.slice(2)}</li>);
      } else if (line.startsWith('* ')) {
        elements.push(<li key={i} className="ml-4 my-0.5 list-disc">{line.slice(2)}</li>);
      } else if (line.startsWith('---')) {
        elements.push(<hr key={i} className="my-3 border-border" />);
      } else if (line.trim() === '') {
        elements.push(<div key={i} className="h-2" />);
      } else {
        // Regular paragraph with bold/italic support
        const formattedLine = line
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\*(.*?)\*/g, '<em>$1</em>');
        elements.push(<p key={i} className="my-1" dangerouslySetInnerHTML={{ __html: formattedLine }} />);
      }
    });

    // Flush any remaining table
    if (inTable) {
      flushTable();
    }

    return elements;
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">AI Analysis Log</h2>
          <p className="text-muted-foreground">Network failover analysis reports from autonomous agents</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Connect/Disconnect Buttons */}
          {isConnected ? (
            <Button 
              variant="destructive" 
              size="sm" 
              onClick={handleDisconnect}
              disabled={disconnecting}
              className="gap-2"
            >
              {disconnecting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <PowerOff className="h-4 w-4" />
              )}
              {disconnecting ? 'Disconnecting...' : 'Disconnect'}
            </Button>
          ) : (
            <Button 
              variant="default" 
              size="sm" 
              onClick={handleConnect}
              disabled={connecting}
              className="gap-2 bg-green-600 hover:bg-green-700"
            >
              {connecting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Power className="h-4 w-4" />
              )}
              {connecting ? 'Connecting...' : 'Connect'}
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={fetchHistory} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Badge 
            variant={isConnected ? "default" : "secondary"} 
            className={`gap-2 ${isConnected ? 'bg-green-600' : ''}`}
          >
            <Bot className="h-4 w-4" />
            {isConnected ? 'Connected' : 'Disconnected'}
          </Badge>
        </div>
      </div>

      <Card className="glass-card">
        <CardHeader>
          <CardTitle>Analysis Reports</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[600px] pr-4">
            <div className="space-y-4">
              {history.map((entry, i) => (
                <div 
                  key={i} 
                  className="rounded-lg bg-muted/30 border border-border/50 hover:border-border transition-colors overflow-hidden"
                >
                  <button
                    onClick={() => toggleExpanded(i)}
                    className="w-full flex items-center justify-between p-4 text-left hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-primary" />
                      <div>
                        <span className="font-semibold text-foreground">
                          Report #{entry.iteration || history.length - i}
                        </span>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                          <Clock className="h-3 w-3" />
                          {new Date(entry.timestamp).toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-xs">
                        {entry.risk_data?.includes('No APs found above threshold') ? 'Healthy' : 'Action Required'}
                      </Badge>
                      {expandedItems.has(i) ? (
                        <ChevronUp className="h-5 w-5 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="h-5 w-5 text-muted-foreground" />
                      )}
                    </div>
                  </button>
                  
                  {expandedItems.has(i) && (
                    <div className="px-4 pb-4 border-t border-border/50">
                      <div className="mt-4 p-4 rounded-lg bg-background/50">
                        {renderMarkdown(entry.analysis)}
                      </div>
                      
                      {entry.risk_data && (
                        <div className="mt-4">
                          <h4 className="text-sm font-semibold mb-2 text-muted-foreground">Risk Data Summary</h4>
                          <pre className="p-3 rounded bg-black/30 text-xs font-mono overflow-x-auto whitespace-pre-wrap">
                            {entry.risk_data}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
              {history.length === 0 && !loading && (
                <div className="text-center py-12 text-muted-foreground">
                  <Bot className="h-12 w-12 mx-auto mb-4 opacity-20" />
                  {!isConnected ? (
                    <>
                      <p className="text-lg font-medium">Agents Disconnected</p>
                      <p className="text-sm mt-2">Click "Connect" to start the AI agents and begin generating reports.</p>
                      <Button 
                        onClick={handleConnect} 
                        disabled={connecting}
                        className="mt-4 gap-2 bg-green-600 hover:bg-green-700"
                      >
                        {connecting ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Power className="h-4 w-4" />
                        )}
                        {connecting ? 'Connecting...' : 'Connect Agents'}
                      </Button>
                    </>
                  ) : (
                    <>
                      <p>No analysis reports found yet.</p>
                      <p className="text-sm mt-2">Agents are running. Reports will appear shortly.</p>
                    </>
                  )}
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
