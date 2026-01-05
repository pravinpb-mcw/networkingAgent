import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid, Legend, ReferenceLine } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, BarChart3 } from "lucide-react";

interface RiskWaveChartProps {
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
}

// Custom dot that changes color based on risk level
const CustomDot = (props: any) => {
  const { cx, cy, payload } = props;
  const risk = payload?.risk || 0;
  
  let fillColor = '#10b981'; // Green for low risk
  if (risk >= 60) {
    fillColor = '#ef4444'; // Red for high risk
  } else if (risk >= 25) {
    fillColor = '#f59e0b'; // Amber for medium risk
  }
  
  return (
    <circle 
      cx={cx} 
      cy={cy} 
      r={8} 
      fill={fillColor} 
      stroke="#fff" 
      strokeWidth={2}
      style={{ filter: 'drop-shadow(0 0 4px rgba(0,0,0,0.3))' }}
    />
  );
};

export default function RiskWaveChart({ data, loading }: RiskWaveChartProps) {
  if (loading) {
    return (
      <Card className="glass-card h-[350px] flex items-center justify-center">
        <div className="text-muted-foreground">Loading risk data...</div>
      </Card>
    );
  }

  // Transform data for the line chart
  const chartData = data.map(item => ({
    name: item.ap_name,
    risk: item.risk_score,
  }));

  // Show empty state when no data
  if (data.length === 0) {
    return (
      <Card className="glass-card h-[350px]">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <TrendingUp className="h-5 w-5 text-cyan-400" />
            Current Risk Factors
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[280px] text-muted-foreground">
          <BarChart3 className="h-12 w-12 mb-4 opacity-30" />
          <p className="font-medium">No Risk Data</p>
          <p className="text-sm mt-1">Waiting for agent data...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass-card">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <TrendingUp className="h-5 w-5 text-cyan-400" />
          Current Risk Factors
        </CardTitle>
      </CardHeader>
      <CardContent className="pl-2">
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
              <defs>
                <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00f2ff" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#00f2ff" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
              <XAxis 
                dataKey="name" 
                stroke="#888888" 
                fontSize={11} 
                tickLine={false} 
                axisLine={false}
              />
              <YAxis 
                stroke="#888888" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false}
                domain={[0, 100]}
                ticks={[0, 25, 50, 75, 100]}
              />
              <Tooltip 
                cursor={{ stroke: 'rgba(255, 255, 255, 0.1)', strokeWidth: 1 }}
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
                formatter={(value: number) => {
                  let status = 'Low Risk';
                  if (value >= 60) status = 'High Risk';
                  else if (value >= 25) status = 'Medium Risk';
                  return [`${value} (${status})`, 'Risk Score'];
                }}
              />
              <Legend 
                wrapperStyle={{ paddingTop: '10px' }}
                formatter={() => <span style={{ color: '#e2e8f0', fontSize: '12px' }}>Risk Score</span>}
              />
              {/* Reference lines for risk thresholds */}
              <ReferenceLine y={60} stroke="#ef4444" strokeDasharray="5 5" strokeOpacity={0.5} />
              <ReferenceLine y={25} stroke="#f59e0b" strokeDasharray="5 5" strokeOpacity={0.5} />
              <Line 
                type="monotone"
                dataKey="risk" 
                stroke="#00f2ff"
                strokeWidth={3}
                fill="url(#riskGradient)"
                dot={<CustomDot />}
                activeDot={{ r: 10, stroke: '#fff', strokeWidth: 2 }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
