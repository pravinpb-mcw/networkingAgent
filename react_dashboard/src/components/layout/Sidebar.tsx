import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Bot, Flame, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function Sidebar() {
  const location = useLocation();

  const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
    { icon: Bot, label: 'AI Analysis', path: '/analysis' },
    { icon: Flame, label: 'Phoenix Traces', path: '/phoenix' },
    { icon: Settings, label: 'Controls', path: '/controls' },
  ];

  return (
    <div className="h-screen w-64 bg-card border-r border-border flex flex-col fixed left-0 top-0 z-30">
      <div className="p-6 flex items-center justify-center border-b border-border/50">
        <div className="rounded-lg bg-black dark:bg-transparent px-4 py-2.5">
          <img src="/logo-1.png" alt="NetAgent Logo" className="h-12 w-auto object-contain" />
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200",
                isActive 
                  ? "bg-primary/10 text-primary shadow-sm border border-primary/20" 
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <item.icon className={cn("h-5 w-5", isActive ? "text-primary" : "text-muted-foreground")} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-border/50">
        <div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-green-500/10 border border-green-500/20">
          <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs font-medium text-green-500">System Active</span>
        </div>
      </div>
    </div>
  );
}
