import { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { 
  AlertTriangle, 
  Activity, 
  Bot, 
  ShieldAlert,
  RefreshCw
} from 'lucide-react';
import KPICard from '@/components/dashboard/KPICard';
import APMetricsChart from '@/components/dashboard/APMetricsChart';
import RiskWaveChart from '@/components/dashboard/RiskWaveChart';
import { getRiskScores, getSystemStatus, RiskScore, SystemStatus } from '@/api/client';
import { Button } from '@/components/ui/button';

export default function Dashboard() {
  const context = useOutletContext<{ refreshTrigger: number }>();
  const refreshTrigger = context?.refreshTrigger ?? 0;
  
  const [riskScores, setRiskScores] = useState<RiskScore[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async (isInitial = false) => {
    try {
      const [risk, status] = await Promise.all([
        getRiskScores(),
        getSystemStatus(),
      ]);
      
      setRiskScores(risk);
      setSystemStatus(status);
      setError(null);
    } catch (error) {
      console.error("Failed to fetch dashboard data", error);
      if (isInitial) {
        setError("Failed to load dashboard data");
      }
    } finally {
      if (isInitial) {
        setInitialLoading(false);
      }
    }
  };

  // Background refresh - no loading indicator
  useEffect(() => {
    if (refreshTrigger > 0) {
      fetchData(false);
    }
  }, [refreshTrigger]);

  // Initial load only
  useEffect(() => {
    fetchData(true);
  }, []);

  // Calculate aggregate metrics
  const avgRisk = riskScores.length > 0 
    ? Math.round(riskScores.reduce((acc, curr) => acc + curr.risk_score, 0) / riskScores.length) 
    : 0;
  
  const highRiskCount = riskScores.filter(r => r.risk_score > 70).length;
  
  // Count running agents from the status object
  const activeAgents = systemStatus ? 
    [systemStatus.agent1, systemStatus.agent2, systemStatus.agent3].filter(s => s === 'running').length 
    : 0;
  
  const isSystemOnline = systemStatus && (
    systemStatus.agent1 === 'running' || 
    systemStatus.agent2 === 'running' || 
    systemStatus.agent3 === 'running'
  );

  if (error && initialLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-destructive" />
          <p className="text-lg font-semibold">{error}</p>
          <Button onClick={() => fetchData(true)} className="mt-4">
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Network Risk Overview</h2>
      </div>

      {/* KPI Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard 
          title="Network Risk Level" 
          value={`${avgRisk}/100`}
          icon={ShieldAlert}
          status={avgRisk > 70 ? "critical" : avgRisk > 40 ? "warning" : "success"}
          loading={initialLoading}
        />
        <KPICard 
          title="Active Agents" 
          value={`${activeAgents}/3`}
          icon={Bot}
          status={activeAgents === 3 ? "success" : "warning"}
          loading={initialLoading}
        />
        <KPICard 
          title="High Risk APs" 
          value={highRiskCount}
          icon={AlertTriangle}
          status={highRiskCount > 0 ? "critical" : "success"}
          loading={initialLoading}
        />
        <KPICard 
          title="System Status" 
          value={isSystemOnline ? "Online" : "Offline"}
          icon={Activity}
          status={isSystemOnline ? "success" : "critical"}
          loading={initialLoading}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* AP Metrics Chart - Latency, Jitter, SNR */}
        <APMetricsChart data={riskScores} loading={initialLoading} />

        {/* Risk Wave Chart - Curved line with points */}
        <RiskWaveChart data={riskScores} loading={initialLoading} />
      </div>
    </div>
  );
}
