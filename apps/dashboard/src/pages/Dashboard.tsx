import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Activity, 
  Users, 
  CheckCircle, 
  Clock, 
  AlertCircle,
  BarChart3,
  Zap,
  ShieldCheck,
  Search,
  Database,
  FileText,
  ExternalLink,
  Target
} from 'lucide-react';
import { fetchMetrics, fetchAgents, fetchHealth, fetchSources, fetchContent, cn } from '../lib/api';

const Dashboard: React.FC = () => {
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['metrics'],
    queryFn: fetchMetrics,
    refetchInterval: 5000,
  });

  const { data: agents } = useQuery({
    queryKey: ['agents'],
    queryFn: fetchAgents,
  });

  const { data: sources } = useQuery({
    queryKey: ['sources'],
    queryFn: fetchSources,
    refetchInterval: 10000,
  });

  const { data: content } = useQuery({
    queryKey: ['content'],
    queryFn: fetchContent,
    refetchInterval: 10000,
  });

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 10000,
  });

  const stats = [
    { label: 'Active Agents', value: metrics?.agents || 0, icon: Users, color: 'text-blue-400' },
    { label: 'Intelligence Sources', value: metrics?.sources || 0, icon: Database, color: 'text-indigo-400' },
    { label: 'Tasks Succeeded', value: metrics?.tasks?.succeeded || 0, icon: CheckCircle, color: 'text-green-400' },
    { label: 'Active Campaigns', value: metrics?.campaigns || 0, icon: Zap, color: 'text-purple-400' },
  ];

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight gradient-text">Growth Orchestrator</h1>
          <p className="text-surface-400 mt-1">Autonomous Marketing Operations Center</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-surface-900 border border-surface-800">
            <div className={cn(
              "w-2 h-2 rounded-full",
              health?.status === 'ok' ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" : "bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.6)]"
            )} />
            <span className="text-xs font-medium text-surface-300">System: {health?.status || 'connecting...'}</span>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <div key={i} className="stat-card">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm font-medium text-surface-400">{stat.label}</p>
                <h3 className="text-2xl font-bold mt-1">{metricsLoading ? '...' : stat.value}</h3>
              </div>
              <div className={cn("p-2 rounded-lg bg-surface-800", stat.color)}>
                <stat.icon size={20} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Activity & Sources */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Recent Intelligence Sources */}
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <Database size={20} className="text-indigo-400" />
                <h2 className="text-xl font-semibold">Market Intelligence Feed</h2>
              </div>
            </div>
            <div className="space-y-4">
              {sources?.slice(0, 3).map((source) => (
                <div key={source.id} className="p-4 rounded-xl bg-surface-800/30 border border-surface-700/50 hover:border-indigo-500/30 transition-all">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-surface-100 flex items-center gap-2">
                      {source.title}
                      <a href={source.url} target="_blank" rel="noreferrer" className="text-surface-500 hover:text-indigo-400">
                        <ExternalLink size={14} />
                      </a>
                    </h3>
                    <span className="text-xs font-bold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400">
                      Score: {source.relevance_score.toFixed(2)}
                    </span>
                  </div>
                  <p className="text-sm text-surface-400 line-clamp-2 mb-2">{source.summary}</p>
                  <div className="flex items-center gap-4 text-[10px] text-surface-500 uppercase tracking-wider">
                    <span className="flex items-center gap-1"><Target size={10} /> {source.topic}</span>
                    <span>{new Date(source.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              )) || <div className="text-center py-8 text-surface-500 italic">No intelligence gathered yet</div>}
            </div>
          </div>

          {/* Planned Content Queue */}
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <FileText size={20} className="text-green-400" />
                <h2 className="text-xl font-semibold">Planned Content Queue</h2>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {content?.slice(0, 4).map((item) => (
                <div key={item.id} className="p-4 rounded-xl bg-surface-800/30 border border-surface-700/50">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-surface-700 text-surface-300 uppercase">
                      {item.channel}
                    </span>
                    <span className="text-[10px] text-surface-500">
                      {new Date(item.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <h3 className="font-medium text-surface-100 mb-1">{item.title}</h3>
                  <p className="text-xs text-surface-400 mb-3 line-clamp-1">{item.objective}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-primary-400 font-medium">By {item.author_agent}</span>
                    <div className="flex items-center gap-1 text-[10px] text-surface-500">
                      <ShieldCheck size={10} /> {item.status}
                    </div>
                  </div>
                </div>
              )) || <div className="col-span-2 text-center py-8 text-surface-500 italic">No content planned yet</div>}
            </div>
          </div>
        </div>

        {/* Right Column: Agents & Activity */}
        <div className="space-y-8">
          {/* Activity Feed */}
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <Activity size={20} className="text-primary-400" />
                <h2 className="text-xl font-semibold">Live Activity</h2>
              </div>
            </div>
            <div className="space-y-4">
              {metrics?.recent_activity?.slice(0, 5).map((event) => (
                <div key={event.id} className="flex items-start space-x-3 text-xs">
                  <div className="mt-1">
                    {event.event_type.includes('success') ? <ShieldCheck size={14} className="text-green-400" /> : 
                     event.event_type.includes('fail') ? <AlertCircle size={14} className="text-red-400" /> :
                     <Zap size={14} className="text-primary-400" />}
                  </div>
                  <div>
                    <p className="font-medium text-surface-200">{event.agent_name}</p>
                    <p className="text-surface-500">{event.message}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Specialized Agents */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Search size={20} className="text-primary-400" />
              <h2 className="text-xl font-semibold text-surface-100">Agent Fleet</h2>
            </div>
            {agents?.slice(0, 4).map((agent) => (
              <div key={agent.name} className="glass-card p-4">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="text-sm font-bold text-primary-400">{agent.name}</h3>
                  <span className="text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-surface-800 text-surface-400">
                    {agent.role}
                  </span>
                </div>
                <p className="text-[11px] text-surface-400 line-clamp-2">
                  {agent.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
