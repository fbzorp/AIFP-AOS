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

export interface Metrics {
  agents: number;
  tasks: Record<string, number>;
  campaigns: number;
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

/**
 * Fetches high-level system metrics for the dashboard stats cards.
 */
export const fetchMetrics = async (): Promise<Metrics> => {
  const { data } = await api.get('/metrics');
  return data;
};

/**
 * Fetches the list of specialized agents and their capabilities.
 */
export const fetchAgents = async (): Promise<Agent[]> => {
  const { data } = await api.get('/agents');
  return data;
};

/**
 * Fetches the system health status from the root /health endpoint.
 */
export const fetchHealth = async (): Promise<Health> => {
  const { data } = await axios.get(`${API_BASE_URL}/health`);
  return data;
};
