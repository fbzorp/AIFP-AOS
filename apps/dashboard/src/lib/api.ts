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
  objective: string;
  target_audience: string;
  format: string;
  cta: string;
  source_id: string;
  author_agent: string;
  created_at: string;
}

export interface Metrics {
  agents: number;
  tasks: Record<string, number>;
  campaigns: number;
  sources: number;
  recent_activity: AuditEvent[];
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

export const fetchHealth = async (): Promise<Health> => {
  const { data } = await axios.get(`${API_BASE_URL}/health`);
  return data;
};
