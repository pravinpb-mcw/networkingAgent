import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid, Cell, LabelList } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3, Bot, Power, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface RiskBarChartProps {
  data: Array<{
    ap_name: string;
    risk_score: number;
    factors: {
      latency: number;
      jitter: number;
      packet_loss: number;
      client_count: number;
    };
    timestamp: string;
  }>;
  loading?: boolean;
  isSystemOnline?: boolean;
  onConnect?: () => void;
  connecting?: boolean;
}

export default function RiskBarChart({ data, loading, isSystemOnline, onConnect, connecting }: RiskBarChartProps) {
  if (loading) {
    return (
      <Card className="glass-card h-[350px] flex items-center justify-center">
        <div className="text-muted-foreground">Loading risk data...</div>
      </Card>
    );
  }

  // Transform data for the bar chart
  const chartData = data.map(item => ({
    name: item.ap_name,
    risk: item.risk_score,
    latency: item.factors.latency,
    jitter: item.factors.jitter,
  }));

  // Color based on risk level
  const getBarColor = (risk: number) => {
    if (risk > 70) return "#ef4444"; // Red - critical
    if (risk > 40) return "#f59e0b"; // Amber - warning
    return "#10b981"; // Green - healthy
  };

  // Show empty state when no data
  if (data.length === 0) {
    return (
      <Card className="glass-card h-[350px]">
        <CardHeader>
          <CardTitle>Current Risk Analysis</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[280px] text-muted-foreground">
          {!isSystemOnline ? (
            <>
              <Bot className="h-10 w-10 mb-3 opacity-30" />
              <p className="font-medium">Agents Disconnected</p>
              <p className="text-sm mt-1 mb-3">Connect agents to start monitoring</p>
              {onConnect && (
                <Button 
                  onClick={onConnect} 
                  disabled={connecting}
                  size="sm"
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
            </>
          ) : (
            <>
              <BarChart3 className="h-12 w-12 mb-4 opacity-30" />
              <p className="font-medium">No Risk Data</p>
              <p className="text-sm mt-1">Waiting for agent data...</p>
            </>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle>Current Risk Analysis</CardTitle>
      </CardHeader>
      <CardContent className="pl-2">
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" horizontal={true} vertical={false} />
              <XAxis 
                type="number" 
                domain={[0, 100]} 
                stroke="#888888" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false}
              />
              <YAxis 
                type="category" 
                dataKey="name" 
                stroke="#888888" 
                fontSize={11} 
                tickLine={false} 
                axisLine={false}
                width={100}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(17, 25, 40, 0.95)', 
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  padding: '12px'
                }}
                labelStyle={{ color: '#fff', fontWeight: 'bold', marginBottom: '8px' }}
                formatter={(value: number, name: string) => {
                  if (name === 'risk') return [`${value}`, 'Risk Score'];
                  if (name === 'latency') return [`${value}ms`, 'Latency'];
                  if (name === 'jitter') return [`${value}ms`, 'Jitter'];
                  return [value, name];
                }}
              />
              <Bar 
                dataKey="risk" 
                radius={[0, 4, 4, 0]}
                maxBarSize={30}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getBarColor(entry.risk)} />
                ))}
                <LabelList 
                  dataKey="risk" 
                  position="right" 
                  fill="#fff"
                  fontSize={12}
                  fontWeight="bold"
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
