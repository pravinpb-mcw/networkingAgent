import { useEffect, useState } from 'react';
import { 
  RefreshCw, 
  WifiOff, 
  Wifi,
  HeartPulse,
  Loader2,
  CheckCircle,
  Terminal,
  ChevronDown,
  ChevronUp,
  Trash2,
  Bot,
  Activity,
  AlertCircle,
  Power
} from 'lucide-react';
import { 
  getScenariosAPs,
  failAP,
  recoverAP,
  getAllAgentLogs,
  clearAgentLogs,
  getSystemStatus,
  AgentLogEntry,
  AP,
  SystemStatus
} from '@/api/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useNavigate } from 'react-router-dom';

interface AgentLogsState {
  agent1: AgentLogEntry[];
  agent2: AgentLogEntry[];
  agent3: AgentLogEntry[];
  phoenix: AgentLogEntry[];
  risk_updater: AgentLogEntry[];
}

export default function Controls() {
  // Scenario State
  const [aps, setAps] = useState<AP[]>([]);
  const [selectedAp, setSelectedAp] = useState<string>('');
  const [selectedRecoverAp, setSelectedRecoverAp] = useState<string>('');
  const [latency, setLatency] = useState([350]);
  const [jitter, setJitter] = useState([55]);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [recoverLoading, setRecoverLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const navigate = useNavigate();

  // Agent Logs State
  const [agentLogs, setAgentLogs] = useState<AgentLogsState>({
    agent1: [],
    agent2: [],
    agent3: [],
    phoenix: [],
    risk_updater: []
  });
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set(['agent1', 'agent2', 'agent3', 'phoenix', 'risk_updater']));

  // Check if agents are running
  const agentsConnected = systemStatus && (
    systemStatus.agent1 === 'running' || 
    systemStatus.agent2 === 'running' || 
    systemStatus.agent3 === 'running'
  );

  useEffect(() => {
    checkSystemStatus();
    loadAgentLogs();
    // Poll for status and logs every 5 seconds
    const interval = setInterval(() => {
      checkSystemStatus();
      loadAgentLogs();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Only load APs when agents are connected
  useEffect(() => {
    if (agentsConnected) {
      loadAPs();
    }
  }, [agentsConnected]);

  const checkSystemStatus = async () => {
    try {
      const status = await getSystemStatus();
      setSystemStatus(status);
    } catch (error) {
      console.error("Failed to check system status", error);
    }
  };

  const loadAPs = async () => {
    try {
      const data = await getScenariosAPs();
      setAps(data);
      if (data.length > 0) {
        setSelectedAp(data[0].serial);
        setSelectedRecoverAp(data[0].serial);
      }
    } catch (error) {
      console.error("Failed to load APs", error);
    }
  };

  const handleFailAP = async () => {
    if (!selectedAp) return;
    setScenarioLoading(true);
    try {
      await failAP(selectedAp, latency[0], jitter[0]);
      toast.success(`Failure simulated on AP ${selectedAp}`);
      loadAPs(); // Refresh status
    } catch (error) {
      toast.error("Failed to simulate failure");
    } finally {
      setScenarioLoading(false);
    }
  };

  const handleRecoverAP = async (serial: string) => {
    setScenarioLoading(true);
    try {
      await recoverAP(serial);
      toast.success(`AP ${serial} recovered`);
      loadAPs(); // Refresh status
    } catch (error) {
      toast.error("Failed to recover AP");
    } finally {
      setScenarioLoading(false);
    }
  };

  const handleRestoreSelectedAP = async () => {
    if (!selectedRecoverAp) return;
    setRecoverLoading(true);
    try {
      await recoverAP(selectedRecoverAp);
      const apName = aps.find(ap => ap.serial === selectedRecoverAp)?.name || selectedRecoverAp;
      toast.success(`${apName} restored to healthy state`);
      loadAPs(); // Refresh status
    } catch (error) {
      toast.error("Failed to restore AP");
    } finally {
      setRecoverLoading(false);
    }
  };

  // Agent Logs Functions
  const loadAgentLogs = async () => {
    try {
      const logs = await getAllAgentLogs();
      setAgentLogs(logs);
    } catch (error) {
      console.error("Failed to load agent logs", error);
    }
  };

  const handleClearLogs = async (agentName: string) => {
    try {
      await clearAgentLogs(agentName);
      setAgentLogs(prev => ({ ...prev, [agentName]: [] }));
      toast.success(`Logs cleared for ${agentName}`);
    } catch (error) {
      toast.error("Failed to clear logs");
    }
  };

  const toggleAgent = (agentName: string) => {
    setExpandedAgents(prev => {
      const newSet = new Set(prev);
      if (newSet.has(agentName)) {
        newSet.delete(agentName);
      } else {
        newSet.add(agentName);
      }
      return newSet;
    });
  };

  const getAgentInfo = (agentName: string) => {
    const info: Record<string, { title: string; color: string; icon: React.ReactNode }> = {
      agent1: { title: 'Agent 1 - Risk Calculator', color: 'text-blue-400', icon: <Bot className="h-4 w-4" /> },
      agent2: { title: 'Agent 2 - AP Proximity', color: 'text-green-400', icon: <Bot className="h-4 w-4" /> },
      agent3: { title: 'Agent 3 - Failover Coordinator', color: 'text-purple-400', icon: <Bot className="h-4 w-4" /> },
      phoenix: { title: 'Phoenix Trace Server', color: 'text-orange-400', icon: <Activity className="h-4 w-4" /> },
      risk_updater: { title: 'Risk Score Updater', color: 'text-cyan-400', icon: <RefreshCw className="h-4 w-4" /> }
    };
    return info[agentName] || { title: agentName, color: 'text-gray-400', icon: <Terminal className="h-4 w-4" /> };
  };

  const renderAgentLogBox = (agentName: string) => {
    const logs = agentLogs[agentName as keyof AgentLogsState] || [];
    const isExpanded = expandedAgents.has(agentName);
    const { title, color, icon } = getAgentInfo(agentName);

    return (
      <Card key={agentName} className="glass-card border-border/50">
        <div 
          className="flex items-center justify-between p-4 cursor-pointer hover:bg-muted/30 transition-colors"
          onClick={() => toggleAgent(agentName)}
        >
          <div className="flex items-center gap-3">
            <span className={color}>{icon}</span>
            <span className="font-medium">{title}</span>
            <Badge variant="outline" className="ml-2">
              {logs.length} logs
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="ghost"
              onClick={(e) => {
                e.stopPropagation();
                handleClearLogs(agentName);
              }}
              className="h-7 px-2 text-muted-foreground hover:text-red-400"
            >
              <Trash2 className="h-3 w-3" />
            </Button>
            {isExpanded ? (
              <ChevronUp className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        </div>
        {isExpanded && (
          <CardContent className="pt-0">
            <ScrollArea className="h-[200px] w-full rounded-md border border-border/30 bg-black/30 p-3">
              {logs.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  <Terminal className="h-8 w-8 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">No logs available</p>
                  <p className="text-xs mt-1">Logs will appear when agent is running</p>
                </div>
              ) : (
                <div className="space-y-1 font-mono text-xs">
                  {logs.slice(-100).map((log, idx) => (
                    <div key={idx} className="flex gap-2">
                      <span className="text-muted-foreground shrink-0">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                      <span className={
                        log.level === 'error' ? 'text-red-400' :
                        log.level === 'warn' ? 'text-yellow-400' :
                        log.level === 'success' ? 'text-green-400' :
                        'text-foreground'
                      }>
                        {log.message}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        )}
      </Card>
    );
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <h2 className="text-3xl font-bold tracking-tight">System Controls</h2>

      <Tabs defaultValue="scenarios" className="w-full">
        <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
          <TabsTrigger value="scenarios" className="gap-2">
            <WifiOff className="h-4 w-4" />
            Scenarios
          </TabsTrigger>
          <TabsTrigger value="agents" className="gap-2">
            <Terminal className="h-4 w-4" />
            Agent Logs
          </TabsTrigger>
        </TabsList>

        <TabsContent value="scenarios" className="mt-6">
          {!agentsConnected ? (
            <Card className="glass-card">
              <CardContent className="flex flex-col items-center justify-center py-16">
                <div className="relative mb-6">
                  <Power className="h-16 w-16 text-muted-foreground opacity-30" />
                  <AlertCircle className="h-6 w-6 text-yellow-500 absolute -bottom-1 -right-1" />
                </div>
                <p className="text-xl font-medium mb-2">Agents Not Connected</p>
                <p className="text-sm text-muted-foreground text-center max-w-md mb-6">
                  Network scenarios and device controls require connected agents.
                  Start the agents to access failure simulation and recovery features.
                </p>
                <Button 
                  onClick={() => navigate('/ai-analysis')}
                  className="gap-2 bg-green-600 hover:bg-green-700"
                >
                  <Power className="h-4 w-4" />
                  Go to AI Analysis to Connect
                </Button>
              </CardContent>
            </Card>
          ) : (
          <div className="grid gap-6 md:grid-cols-2">
        {/* Failure Simulation */}
        <Card className="glass-card border-red-500/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <WifiOff className="h-5 w-5 text-red-500" />
              Simulate AP Failure
            </CardTitle>
            <CardDescription>Inject faults into network devices to test agent response</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Target Access Point</Label>
              <select 
                className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={selectedAp}
                onChange={(e) => setSelectedAp(e.target.value)}
              >
                {aps.map(ap => (
                  <option key={ap.serial} value={ap.serial}>
                    {ap.name} ({ap.serial})
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Latency Injection</Label>
                  <span className="text-sm text-muted-foreground">{latency}ms</span>
                </div>
                <Slider 
                  value={latency} 
                  onValueChange={setLatency} 
                  max={1000} 
                  step={10} 
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Jitter Injection</Label>
                  <span className="text-sm text-muted-foreground">{jitter}ms</span>
                </div>
                <Slider 
                  value={jitter} 
                  onValueChange={setJitter} 
                  max={200} 
                  step={5} 
                />
              </div>
            </div>

            <Button 
              onClick={handleFailAP} 
              disabled={scenarioLoading || !selectedAp}
              variant="destructive" 
              className="w-full"
            >
              <WifiOff className="mr-2 h-4 w-4" /> Apply
            </Button>
          </CardContent>
        </Card>

        {/* Restore AP Health */}
        <Card className="glass-card border-green-500/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <HeartPulse className="h-5 w-5 text-green-500" />
              Restore AP Health
            </CardTitle>
            <CardDescription>Reset AP metrics to healthy state</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Select Access Point</Label>
              <select 
                className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={selectedRecoverAp}
                onChange={(e) => setSelectedRecoverAp(e.target.value)}
              >
                {aps.map(ap => (
                  <option key={ap.serial} value={ap.serial}>
                    {ap.name} ({ap.serial}) {ap.status === 'failed' ? '⚠️ Failed' : '✓ Healthy'}
                  </option>
                ))}
              </select>
            </div>

            <p className="text-sm text-muted-foreground">
              This will restore the selected access point to optimal healthy metrics.
            </p>

            <Button 
              onClick={handleRestoreSelectedAP}
              disabled={recoverLoading || !selectedRecoverAp}
              className="w-full bg-green-600 hover:bg-green-700"
            >
              {recoverLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Restoring...
                </>
              ) : (
                <>
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Restore Normal
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Device Status */}
        <Card className="glass-card md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wifi className="h-5 w-5" />
              Device Status
            </CardTitle>
            <CardDescription>Current health status of all access points</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[250px]">
              <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
                {aps.map(ap => (
                  <div key={ap.serial} className="flex items-center justify-between p-3 rounded-lg bg-muted/30 border border-border/50">
                    <div className="text-sm">
                      <div className="font-medium">{ap.name}</div>
                      <div className="text-xs text-muted-foreground">{ap.serial}</div>
                    </div>
                    {ap.status === 'failed' ? (
                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="h-7 text-green-500 hover:text-green-600 hover:bg-green-500/10"
                        onClick={() => handleRecoverAP(ap.serial)}
                        disabled={scenarioLoading}
                      >
                        <RefreshCw className="mr-1 h-3 w-3" /> Recover
                      </Button>
                    ) : (
                      <Badge className="bg-green-500/10 text-green-500 border-green-500/20">
                        Healthy
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
          </div>
          )}
        </TabsContent>

        <TabsContent value="agents" className="mt-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium">Agent Logs</h3>
                <p className="text-sm text-muted-foreground">Monitor real-time logs from all agents</p>
              </div>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={loadAgentLogs}
                className="gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh
              </Button>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {renderAgentLogBox('risk_updater')}
              {renderAgentLogBox('agent1')}
              {renderAgentLogBox('agent2')}
              {renderAgentLogBox('agent3')}
              {renderAgentLogBox('phoenix')}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
