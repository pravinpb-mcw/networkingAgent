import axios from 'axios';

// Create axios instance
const api = axios.create({
  baseURL: '', // Relative path since we are proxying
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface SystemStatus {
  agent1?: string;
  agent2?: string;
  agent3?: string;
  phoenix?: string;
  riskUpdater?: string;
  dashboard?: string;
}

export interface RiskScore {
  ap_name: string;
  risk_score: number;
  factors: {
    latency: number;
    jitter: number;
    packet_loss: number;
    client_count: number;
  };
  timestamp: string;
}

export interface NearestAP {
  client_mac: string;
  nearest_ap: string;
  rssi: number;
  timestamp: string;
}

export interface AnalysisEntry {
  timestamp: string;
  analysis: string;
  risk_data: string;
  nearest_data: Record<string, any>;
  iteration: number;
}

export interface AP {
  serial: string;
  name: string;
  mac: string;
  model?: string;
  status?: string;
  tags?: string[];
}

// API Functions
export const getSystemStatus = async (): Promise<SystemStatus> => {
  const response = await api.get('/status');
  return response.data;
};

export const getRiskScores = async (): Promise<RiskScore[]> => {
  const response = await api.get('/metrics/risk');
  const data = response.data;
  
  // Handle empty or invalid response
  if (!data || typeof data !== 'object') {
    return [];
  }
  
  // Transform dictionary to array
  return Object.entries(data).map(([serial, ap]: [string, any]) => ({
    ap_name: ap?.current?.ap_name || ap?.ap_serial || serial || 'Unknown AP',
    risk_score: Math.round(ap?.current?.risk_score ?? 0),
    factors: {
      latency: Math.round(ap?.current?.metrics?.latency_ms || 0),
      jitter: Math.round((ap?.current?.metrics?.jitter_ms || 0) * 10) / 10,
      packet_loss: Math.round(ap?.current?.metrics?.retrans_per_min || 0),
      client_count: ap?.current?.metrics?.client_count || 0
    },
    timestamp: ap?.current?.timestamp || new Date().toISOString()
  }));
};

export const getNearestAPs = async (): Promise<NearestAP[]> => {
  const response = await api.get('/metrics/nearest');
  return response.data;
};

export const getAnalysisHistory = async (): Promise<AnalysisEntry[]> => {
  const response = await api.get('/analysis/history');
  return response.data;
};

export const startSystem = async () => {
  return api.post('/system/start');
};

export const stopSystem = async () => {
  return api.post('/system/stop');
};

export const getTimeseriesData = async (type: string, hours: number = 24) => {
  const response = await api.get(`/metrics/timeseries/${type}?hours=${hours}`);
  return response.data;
};

export const getWebhookSettings = async () => {
  const response = await api.get('/settings/webhook');
  return response.data;
};

export const updateWebhookSettings = async (url: string, enabled: boolean) => {
  return api.post('/settings/webhook', { url, enabled });
};

export const testWebhook = async () => {
  return api.post('/settings/webhook/test');
};

export const getScenariosAPs = async (): Promise<AP[]> => {
  const response = await api.get('/scenarios/aps');
  return response.data;
};

export const failAP = async (apSerial: string, latency: number = 350, jitter: number = 55) => {
  return api.post('/scenarios/fail-ap', { ap_serial: apSerial, latency_ms: latency, jitter_ms: jitter });
};

export const recoverAP = async (apSerial: string) => {
  return api.post('/scenarios/recover-ap', { ap_serial: apSerial });
};

// Agent Logs
export interface AgentLogEntry {
  timestamp: string;
  message: string;
  level: string;
}

export interface AllAgentLogs {
  agent1: AgentLogEntry[];
  agent2: AgentLogEntry[];
  agent3: AgentLogEntry[];
  phoenix: AgentLogEntry[];
  risk_updater: AgentLogEntry[];
}

export const getAllAgentLogs = async (): Promise<AllAgentLogs> => {
  const response = await api.get('/system/logs');
  return response.data;
};

export const getAgentLogs = async (agentName: string): Promise<AgentLogEntry[]> => {
  const response = await api.get(`/system/logs/${agentName}`);
  return response.data.logs;
};

export const clearAgentLogs = async (agentName: string) => {
  return api.delete(`/system/logs/${agentName}`);
};
