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
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  if (window.location.hostname.endsWith('.app.github.dev')) {
    const hostname = window.location.hostname;
    const parts = hostname.split('-');
    if (parts.length > 1) {
      const portPart = parts[parts.length - 1].split('.')[0];
      if (portPart === '3000') {
        const apiHostname = hostname.replace('-3000.app.github.dev', '-8000.app.github.dev');
        return `https://${apiHostname}`;
      }
    }
  }

  return 'http://localhost:8000';
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
  const { data } = await api.get('/metrics');
  return data;
};

export const fetchAgents = async (): Promise<Agent[]> => {
  const { data } = await api.get('/agents');
  return data;
};

export const fetchSources = async (): Promise<Source[]> => {
  const { data } = await api.get('/sources');
  return data;
};

export const fetchContent = async (): Promise<ContentItem[]> => {
  const { data } = await api.get('/content');
  return data;
};

export const submitContent = async (contentId: string) => {
  const { data } = await api.post(`/content/${contentId}/submit`);
  return data;
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
  const { data } = await axios.get(`${API_BASE_URL}/health`);
  return data;
};

export const fetchCalendar = async (): Promise<ContentItem[]> => {
  const { data } = await api.get('/calendar');
  return data;
};

export const fetchProposals = async (): Promise<EngagementProposal[]> => {
  const { data } = await api.get('/engagement/proposals');
  return data;
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
  const { data } = await api.post(`/content/${contentId}/publish`);
  return data;
};

export const fetchPayments = async (): Promise<Payment[]> => {
  const { data } = await api.get('/payments');
  return data;
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
