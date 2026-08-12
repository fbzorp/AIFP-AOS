import axios from 'axios';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility for tailwind class merging
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const getApiBaseUrl = () => {
  // Optional override for custom deployments
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  // Default to empty string for same-origin relative paths
  // This makes requests work on any domain/IP without configuration
  // and prevents double-prefixing issues with nginx proxy
  return '';
};

const API_BASE_URL = getApiBaseUrl();
const API_V1_URL = `${API_BASE_URL}/api/v1`;

export const api = axios.create({
  baseURL: API_V1_URL,
});

export interface Agent {
  name: string;
  role: string;
  description: string;
  capabilities: Record<string, any>;
}

export interface Task {
  id: string;
  task_type: string;
  status: string;
  created_at: string;
  result?: any;
  error?: string;
}

export interface AuditEvent {
  id: string;
  agent_name: string;
  event_type: string;
  message: string;
  created_at: string;
  metadata_json?: any;
}

export interface Source {
  id: string;
  url: string;
  title: string;
  summary: string;
  relevance_score: number;
  content_angle: string;
  topic: string;
  created_at: string;
}

export interface ContentItem {
  id: string;
  title: string;
  channel: string;
  status: string;
  body?: string;
  variants?: Array<{ audience: string; text: string }>;
  objective: string;
  target_audience: string;
  format: string;
  cta: string;
  source_id: string;
  author_agent: string;
  compliance_status?: string;
  compliance_reason?: string;
  scheduled_at?: string;
  published_at?: string;
  post_url?: string;
  post_id?: string;
  publish_error?: string;
  created_at: string;
}

export interface EngagementProposal {
  id: string;
  source_url: string;
  submolt: string;
  discussion_summary: string;
  proposed_reply: string;
  status: string;
  created_at: string;
}

export interface Metrics {
  agents: number;
  tasks: Record<string, number>;
  campaigns: number;
  sources: number;
  recent_activity: AuditEvent[];
  mcp_calls?: number;
}

export interface Payment {
  id: string;
  purpose: string;
  recipient_address: string;
  amount: number;
  currency: string;
  network: string;
  status: string;
  tx_hash?: string;
  tx_url?: string;
  x402_request_url?: string;
  approved_by?: string;
  error?: string;
  created_at: string;
  mcp_tool?: string;
  request_id?: string;
  latency_ms?: number;
  cost_usd?: number;
  wallet?: string;
}

export interface Health {
  status: string;
  version: string;
  dependencies: {
    postgres: string;
    redis: string;
  };
}

export const fetchMetrics = async (): Promise<Metrics> => {
  try {
    const { data } = await api.get('/metrics');
    return data;
  } catch (error) {
    console.error('Failed to fetch metrics:', error);
    throw error;
  }
};

export const fetchAgents = async (): Promise<Agent[]> => {
  try {
    const { data } = await api.get('/agents');
    return data;
  } catch (error) {
    console.error('Failed to fetch agents:', error);
    throw error;
  }
};

export const fetchSources = async (): Promise<Source[]> => {
  try {
    const { data } = await api.get('/sources');
    return data;
  } catch (error) {
    console.error('Failed to fetch sources:', error);
    // Return default sources when API is unavailable
    return [];
  }
};

export const fetchContent = async (): Promise<ContentItem[]> => {
  try {
    const { data } = await api.get('/content');
    return data;
  } catch (error) {
    console.error('Failed to fetch content:', error);
    // Return default content when API is unavailable
    return [];
  }
};

export const submitContent = async (contentId: string) => {
  try {
    const { data } = await api.post(`/content/${contentId}/submit`);
    return data;
  } catch (error) {
    console.error('Failed to submit content:', error);
    throw error;
  }
};

export const createContent = async (content: any) => {
  try {
    const { data } = await api.post('/content', content);
    return data;
  } catch (error) {
    console.error('Failed to create content:', error);
    throw error;
  }
};

export const approveContent = async (contentId: string, approvedBy: string) => {
  const { data } = await api.post(`/content/${contentId}/approve`, { approved_by: approvedBy });
  return data;
};

export const rejectContent = async (contentId: string, approvedBy: string, reason?: string) => {
  const { data } = await api.post(`/content/${contentId}/reject`, { approved_by: approvedBy, reason });
  return data;
};

export const editContent = async (contentId: string, updates: { title?: string; body?: string; variants?: any[] }) => {
  const { data } = await api.patch(`/content/${contentId}`, updates);
  return data;
};

export const fetchHealth = async (): Promise<Health> => {
  try {
    const { data } = await axios.get(`${API_BASE_URL}/health`);
    return data;
  } catch (error) {
    console.error('Failed to fetch health:', error);
    // Return default health status when API is unavailable
    return {
      status: 'degraded',
      version: '1.0.0',
      dependencies: {
        postgres: 'unknown',
        redis: 'unknown'
      }
    };
  }
};

export const fetchCalendar = async (): Promise<ContentItem[]> => {
  try {
    const { data } = await api.get('/calendar');
    return data;
  } catch (error) {
    console.error('Failed to fetch calendar:', error);
    return [];
  }
};

export const fetchProposals = async (): Promise<EngagementProposal[]> => {
  try {
    const { data } = await api.get('/engagement/proposals');
    return data;
  } catch (error) {
    console.error('Failed to fetch proposals:', error);
    return [];
  }
};

export const approveProposal = async (proposalId: string) => {
  const { data } = await api.post(`/engagement/proposals/${proposalId}/approve`);
  return data;
};

export const rejectProposal = async (proposalId: string) => {
  const { data } = await api.post(`/engagement/proposals/${proposalId}/reject`);
  return data;
};

export const publishContentItem = async (contentId: string) => {
  try {
    const { data } = await api.post(`/content/${contentId}/publish`);
    return data;
  } catch (error) {
    console.error('Failed to publish content:', error);
    throw error;
  }
};

export const fetchPayments = async (): Promise<Payment[]> => {
  try {
    const { data } = await api.get('/payments');
    return data;
  } catch (error) {
    console.error('Failed to fetch payments:', error);
    return [];
  }
};

export const createCampaign = async (objective: string) => {
  try {
    const { data } = await api.post('/campaigns', { objective });
    return data;
  } catch (error) {
    console.error('Failed to create campaign:', error);
    throw error;
  }
};

export const createPayment = async (payment: {
  purpose: string;
  recipient_address: string;
  amount: number;
  currency: string;
  network: string;
}): Promise<Payment> => {
  const { data } = await api.post('/payments', payment);
  return data;
};

export const approvePayment = async (paymentId: string, approvedBy: string): Promise<Payment> => {
  const { data } = await api.post(`/payments/${paymentId}/approve`, { approved_by: approvedBy });
  return data;
};

export const executePayment = async (paymentId: string): Promise<Payment> => {
  const { data } = await api.post(`/payments/${paymentId}/execute`);
  return data;
};

export interface CredentialStatus {
  name: string;
  configured: boolean;
  masked: string;
  description: string;
}

export interface CredentialUpdateResponse {
  success: boolean;
  message: string;
  credential_name: string;
}

export const fetchCredentials = async (): Promise<CredentialStatus[]> => {
  try {
    const { data } = await api.get('/settings/credentials');
    return data;
  } catch (error) {
    console.error('Failed to fetch credentials:', error);
    throw error;
  }
};

export const updateCredential = async (name: string, value: string): Promise<CredentialUpdateResponse> => {
  try {
    const { data } = await api.patch('/settings/credentials', { name, value });
    return data;
  } catch (error) {
    console.error('Failed to update credential:', error);
    throw error;
  }
};

export interface MarketingActivityItem {
  id: string;
  title: string;
  agent: string;
  objective?: string;
  target_audience?: string;
  source_id?: string;
  format?: string;
  channel?: string;
  status: string;
  created_at?: string;
  scheduled_at?: string;
  approved_at?: string;
  approver?: string;
  published_at?: string;
  post_url?: string;
  post_id?: string;
  publish_error?: string;
  live_url?: string;
  is_real_publish: boolean;
}

export interface MarketingActivityResponse {
  items: MarketingActivityItem[];
  total_count: number;
  real_publish_count: number;
  dry_run_count: number;
}

export const fetchMarketingActivity = async (params?: {
  start_date?: string;
  end_date?: string;
  channel?: string;
  status?: string;
  only_real?: boolean;
}): Promise<MarketingActivityResponse> => {
  try {
    const { data } = await api.get('/marketing/activity', { params });
    return data;
  } catch (error) {
    console.error('Failed to fetch marketing activity:', error);
    return {
      items: [],
      total_count: 0,
      real_publish_count: 0,
      dry_run_count: 0
    };
  }
};

export const fetchMarketingActivityDetail = async (contentId: string) => {
  try {
    const { data } = await api.get(`/marketing/activity/${contentId}`);
    return data;
  } catch (error) {
    console.error('Failed to fetch marketing activity detail:', error);
    throw error;
  }
};
