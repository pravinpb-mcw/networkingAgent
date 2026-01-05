import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid, Legend } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Wifi, BarChart3 } from "lucide-react";

interface APMetricsChartProps {
  data: Array<{
    ap_name: string;
    risk_score: number;
    factors: {
      latency: number;
      jitter: number;
      packet_loss: number;
      client_count: number;
    };
    snr?: number;
    timestamp: string;
  }>;
  loading?: boolean;
}

export default function APMetricsChart({ data, loading }: APMetricsChartProps) {
  if (loading) {
    return (
      <Card className="glass-card h-[350px] flex items-center justify-center">
        <div className="text-muted-foreground">Loading metrics...</div>
      </Card>
    );
  }

  // Transform data for the grouped bar chart
  const chartData = data.map(item => ({
    name: item.ap_name,
    Latency: item.factors.latency,
    Jitter: item.factors.jitter,
    SNR: item.snr || 35, // Default SNR if not available
  }));

  // Show empty state when no data
  if (data.length === 0) {
    return (
      <Card className="glass-card h-[350px]">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Wifi className="h-5 w-5 text-cyan-400" />
            Access Points Metrics
            <span className="text-xs text-muted-foreground font-normal ml-2">Latency, Jitter & SNR</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[280px] text-muted-foreground">
          <BarChart3 className="h-12 w-12 mb-4 opacity-30" />
          <p className="font-medium">No Metrics Data</p>
          <p className="text-sm mt-1">Waiting for AP data...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass-card">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Wifi className="h-5 w-5 text-cyan-400" />
          Access Points Metrics
          <span className="text-xs text-muted-foreground font-normal ml-2">Latency, Jitter & SNR</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="pl-2">
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
              <XAxis 
                dataKey="name" 
                stroke="#888888" 
                fontSize={11} 
                tickLine={false} 
                axisLine={false}
              />
              <YAxis 
                yAxisId="left"
                stroke="#888888" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false}
                label={{ value: 'ms', angle: -90, position: 'insideLeft', fill: '#888888', fontSize: 10 }}
              />
              <YAxis 
                yAxisId="right"
                orientation="right"
                stroke="#888888" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false}
                label={{ value: 'dB', angle: 90, position: 'insideRight', fill: '#888888', fontSize: 10 }}
              />
              <Tooltip 
                cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
                wrapperStyle={{ backgroundColor: 'transparent' }}
                contentStyle={{ 
                  backgroundColor: '#111827', 
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  padding: '12px',
                  color: '#e2e8f0',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
                }}
                labelStyle={{ color: '#00f2ff', fontWeight: 'bold', marginBottom: '8px' }}
                itemStyle={{ color: '#e2e8f0' }}
                formatter={(value: number, name: string) => {
                  if (name === 'SNR') return [`${value} dB`, name];
                  return [`${value} ms`, name];
                }}
              />
              <Legend 
                wrapperStyle={{ paddingTop: '10px' }}
                formatter={(value) => <span style={{ color: '#e2e8f0', fontSize: '12px' }}>{value}</span>}
              />
              <Bar 
                yAxisId="left"
                dataKey="Latency" 
                fill="rgba(0, 242, 255, 0.7)" 
                radius={[4, 4, 0, 0]}
                maxBarSize={40}
                isAnimationActive={false}
              />
              <Bar 
                yAxisId="left"
                dataKey="Jitter" 
                fill="rgba(245, 158, 11, 0.7)" 
                radius={[4, 4, 0, 0]}
                maxBarSize={40}
                isAnimationActive={false}
              />
              <Bar 
                yAxisId="right"
                dataKey="SNR" 
                fill="rgba(0, 217, 126, 0.7)" 
                radius={[4, 4, 0, 0]}
                maxBarSize={40}
                isAnimationActive={false}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
