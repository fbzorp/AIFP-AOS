import axios from 'axios';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility for tailwind class merging
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
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

export const fetchHealth = async (): Promise<Health> => {
  const { data } = await axios.get(`${API_BASE_URL}/health`);
  return data;
};
