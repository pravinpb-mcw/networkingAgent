import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: string;
  trendUp?: boolean;
  status?: "normal" | "warning" | "critical" | "success";
  loading?: boolean;
}

export default function KPICard({ 
  title, 
  value, 
  icon: Icon, 
  trend, 
  trendUp, 
  status = "normal",
  loading = false
}: KPICardProps) {
  
  const statusColors = {
    normal: "text-foreground",
    warning: "text-yellow-500",
    critical: "text-red-500",
    success: "text-green-500"
  };

  const bgColors = {
    normal: "bg-primary/10 text-primary",
    warning: "bg-yellow-500/10 text-yellow-500",
    critical: "bg-red-500/10 text-red-500",
    success: "bg-green-500/10 text-green-500"
  };

  return (
    <Card className="glass-card border-border/50 shadow-lg">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div className={cn("h-8 w-8 rounded-lg flex items-center justify-center", bgColors[status])}>
          <Icon className="h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {loading ? (
            <div className="h-8 w-24 bg-muted animate-pulse rounded" />
          ) : (
            <span className={statusColors[status]}>{value}</span>
          )}
        </div>
        {trend && (
          <p className="text-xs text-muted-foreground mt-1">
            <span className={cn(trendUp ? "text-green-500" : "text-red-500")}>
              {trend}
            </span> vs last hour
          </p>
        )}
      </CardContent>
    </Card>
  );
}
