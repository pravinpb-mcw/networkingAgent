import { RefreshCw, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useEffect, useState } from 'react';

interface HeaderProps {
  onRefresh: () => void;
  refreshing: boolean;
  lastRefresh: number | null;
}

export default function Header({ onRefresh, refreshing, lastRefresh }: HeaderProps) {
  const [time, setTime] = useState(new Date());
  const [timeSinceRefresh, setTimeSinceRefresh] = useState<string>('Just now');

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!lastRefresh) return;
    
    const updateTimeSince = () => {
      const seconds = Math.floor((Date.now() - lastRefresh) / 1000);
      if (seconds < 5) setTimeSinceRefresh('Just now');
      else setTimeSinceRefresh(`${seconds}s ago`);
    };

    const timer = setInterval(updateTimeSince, 1000);
    updateTimeSince();
    
    return () => clearInterval(timer);
  }, [lastRefresh]);

  return (
    <header className="h-16 border-b border-border/50 bg-background/80 backdrop-blur-md sticky top-0 z-20 px-6 flex items-center justify-between">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-muted-foreground">Overview</span>
        <span className="text-muted-foreground">/</span>
        <span className="font-medium text-foreground">Real-time Monitor</span>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent/50 border border-border/50 text-xs text-muted-foreground">
          <RefreshCw className="h-3 w-3 animate-spin" />
          <span>Auto-refresh: 5s</span>
        </div>

        <div className="h-4 w-[1px] bg-border" />

        <span className="text-xs text-muted-foreground">
          Updated: {timeSinceRefresh}
        </span>

        <Button 
          variant="outline" 
          size="icon" 
          onClick={onRefresh}
          disabled={refreshing}
          className="h-8 w-8"
        >
          <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} />
        </Button>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-accent text-sm font-mono">
          <Clock className="h-4 w-4 text-primary" />
          <span>{time.toLocaleTimeString()}</span>
        </div>
      </div>
    </header>
  );
}

import { cn } from '@/lib/utils';
