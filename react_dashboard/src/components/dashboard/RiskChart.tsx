import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid, Legend } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3 } from "lucide-react";

interface RiskChartProps {
  data: any[];
  loading?: boolean;
}

export default function RiskChart({ data, loading }: RiskChartProps) {
  if (loading) {
    return (
      <Card className="glass-card col-span-2 h-[350px] flex items-center justify-center">
        <div className="text-muted-foreground">Loading chart data...</div>
      </Card>
    );
  }

  const colors = ["#ef4444", "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"];

  // Extract keys (AP serials) from the first data point, excluding 'timestamp'
  const keys = data.length > 0 ? Object.keys(data[0]).filter(k => k !== 'timestamp') : [];

  // Show empty state when no data
  if (data.length === 0 || keys.length === 0) {
    return (
      <Card className="glass-card col-span-2 h-[350px]">
        <CardHeader>
          <CardTitle>Risk Score Trend</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[280px] text-muted-foreground">
          <BarChart3 className="h-12 w-12 mb-4 opacity-30" />
          <p className="font-medium">No Chart Data</p>
          <p className="text-sm mt-1">Risk trend will appear when agents are running</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass-card col-span-2">
      <CardHeader>
        <CardTitle>Risk Score Trend</CardTitle>
      </CardHeader>
      <CardContent className="pl-2">
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="timestamp" 
                stroke="#888888" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false}
                tickFormatter={(value) => new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              />
              <YAxis 
                stroke="#888888" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false} 
                domain={[0, 100]}
              />
              <Tooltip 
                contentStyle={{ backgroundColor: 'rgba(17, 25, 40, 0.9)', border: '1px solid rgba(255,255,255,0.1)' }}
                labelStyle={{ color: '#fff' }}
              />
              <Legend />
              {keys.map((key, index) => (
                <Line 
                  key={key}
                  type="monotone" 
                  dataKey={key} 
                  stroke={colors[index % colors.length]} 
                  strokeWidth={2} 
                  dot={false}
                  activeDot={{ r: 4 }}
                  name={key}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
