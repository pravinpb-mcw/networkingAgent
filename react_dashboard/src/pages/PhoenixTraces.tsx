import { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ExternalLink, Activity, Loader2, RefreshCw, AlertCircle } from 'lucide-react';

export default function PhoenixTraces() {
  const phoenixUrl = "http://localhost:6006"; // Default Phoenix port
  const [isPhoenixRunning, setIsPhoenixRunning] = useState<boolean | null>(null);
  const [checking, setChecking] = useState(true);

  const checkPhoenixStatus = async () => {
    setChecking(true);
    try {
      // Try to fetch from Phoenix - use a timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      
      await fetch(phoenixUrl, { 
        mode: 'no-cors',
        signal: controller.signal 
      });
      clearTimeout(timeoutId);
      
      // If we get here without error, Phoenix might be running
      // no-cors doesn't give us status, so we assume it's running if no error
      setIsPhoenixRunning(true);
    } catch {
      setIsPhoenixRunning(false);
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    checkPhoenixStatus();
    // Recheck every 10 seconds if not running
    const interval = setInterval(() => {
      if (!isPhoenixRunning) {
        checkPhoenixStatus();
      }
    }, 10000);
    return () => clearInterval(interval);
  }, [isPhoenixRunning]);

  return (
    <div className="space-y-6 h-[calc(100vh-8rem)] animate-in fade-in duration-500 flex flex-col">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Phoenix Traces</h2>
          <p className="text-muted-foreground">Deep dive into agent execution traces and spans</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            className="gap-2" 
            onClick={checkPhoenixStatus}
            disabled={checking}
          >
            {checking ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Check Status
          </Button>
          <Button 
            variant="outline" 
            className="gap-2" 
            onClick={() => window.open(phoenixUrl, '_blank')}
            disabled={!isPhoenixRunning}
          >
            Open in New Tab
            <ExternalLink className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <Card className="glass-card flex-1 overflow-hidden border-0">
        <CardContent className="p-0 h-full">
          {checking ? (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
              <Loader2 className="h-12 w-12 animate-spin mb-4 text-cyan-400" />
              <p className="text-lg font-medium">Checking Phoenix Status...</p>
            </div>
          ) : isPhoenixRunning ? (
            <iframe 
              src={phoenixUrl} 
              className="w-full h-full border-0 bg-white"
              title="Phoenix Traces"
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
              <div className="relative mb-6">
                <Activity className="h-16 w-16 text-orange-400 opacity-30" />
                <AlertCircle className="h-6 w-6 text-yellow-500 absolute -bottom-1 -right-1" />
              </div>
              <p className="text-xl font-medium mb-2">Phoenix Server Not Running</p>
              <p className="text-sm text-center max-w-md mb-6">
                The Phoenix observability server is not available at <code className="text-cyan-400">{phoenixUrl}</code>
              </p>
              <div className="bg-muted/30 rounded-lg p-4 border border-border/50 max-w-lg">
                <p className="text-sm font-medium mb-2">To start Phoenix:</p>
                <p className="text-sm">
                  Go to <span className="text-cyan-400">AI Analysis</span> tab and click <span className="text-green-400">"Connect Agents"</span>
                </p>
              </div>
              <Button 
                variant="outline" 
                className="mt-6 gap-2"
                onClick={checkPhoenixStatus}
              >
                <RefreshCw className="h-4 w-4" />
                Check Again
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
