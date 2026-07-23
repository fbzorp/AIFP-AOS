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
  Search
} from 'lucide-react';
import { fetchMetrics, fetchAgents, fetchHealth, cn } from '../lib/api';

const Dashboard: React.FC = () => {
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['metrics'],
    queryFn: fetchMetrics,
    refetchInterval: 5000,
  });

  const { data: agents, isLoading: agentsLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: fetchAgents,
  });

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 10000,
  });

  const stats = [
    { label: 'Active Agents', value: metrics?.agents || 0, icon: Users, color: 'text-blue-400' },
    { label: 'Tasks Succeeded', value: metrics?.tasks?.succeeded || 0, icon: CheckCircle, color: 'text-green-400' },
    { label: 'Pending Tasks', value: metrics?.tasks?.pending || 0, icon: Clock, color: 'text-amber-400' },
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
        {/* Activity Feed */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <Activity size={20} className="text-primary-400" />
                <h2 className="text-xl font-semibold">Live Agent Activity</h2>
              </div>
              <span className="text-xs text-surface-500">Auto-refreshing</span>
            </div>
            
            <div className="space-y-4">
              {metrics?.recent_activity?.map((event) => (
                <div key={event.id} className="flex items-start space-x-4 p-3 rounded-xl hover:bg-surface-800/40 transition-colors">
                  <div className="mt-1">
                    {event.event_type.includes('success') ? <ShieldCheck size={16} className="text-green-400" /> : 
                     event.event_type.includes('fail') ? <AlertCircle size={16} className="text-red-400" /> :
                     <Zap size={16} className="text-primary-400" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-center">
                      <p className="text-sm font-medium text-surface-100">{event.agent_name}</p>
                      <span className="text-[10px] text-surface-500">
                        {new Date(event.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm text-surface-400 truncate">{event.message}</p>
                  </div>
                </div>
              )) || (
                <div className="py-8 text-center text-surface-500 italic">No recent activity detected</div>
              )}
            </div>
          </div>

          {/* Task Breakdown */}
          <div className="glass-card p-6">
            <div className="flex items-center space-x-2 mb-6">
              <BarChart3 size={20} className="text-primary-400" />
              <h2 className="text-xl font-semibold">Task Execution Status</h2>
            </div>
            <div className="space-y-4">
              {['succeeded', 'running', 'pending', 'failed'].map((status) => {
                const count = metrics?.tasks?.[status] || 0;
                const total = Object.values(metrics?.tasks || {}).reduce((a, b) => a + b, 0) || 1;
                const percent = Math.round((count / total) * 100);
                
                return (
                  <div key={status} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="capitalize text-surface-300">{status}</span>
                      <span className="text-surface-500">{count} tasks</span>
                    </div>
                    <div className="h-2 w-full bg-surface-800 rounded-full overflow-hidden">
                      <div 
                        className={cn(
                          "h-full transition-all duration-500",
                          status === 'succeeded' ? "bg-green-500" :
                          status === 'running' ? "bg-primary-500" :
                          status === 'pending' ? "bg-amber-500" : "bg-red-500"
                        )}
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Agent Grid */}
        <div className="space-y-6">
          <div className="flex items-center space-x-2">
            <Search size={20} className="text-primary-400" />
            <h2 className="text-xl font-semibold">Specialized Agents</h2>
          </div>
          <div className="space-y-4">
            {agents?.map((agent) => (
              <div key={agent.name} className="glass-card p-4 hover:translate-x-1">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-bold text-primary-400">{agent.name}</h3>
                  <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded bg-surface-800 text-surface-400">
                    {agent.role}
                  </span>
                </div>
                <p className="text-xs text-surface-400 line-clamp-2 mb-3">
                  {agent.description}
                </p>
                <div className="flex flex-wrap gap-1">
                  {Object.keys(agent.capabilities).slice(0, 3).map(cap => (
                    <span key={cap} className="text-[9px] px-1.5 py-0.5 rounded-sm bg-surface-800/50 text-surface-500 border border-surface-700/50">
                      {cap}
                    </span>
                  ))}
                </div>
              </div>
            )) || <div className="animate-pulse space-y-4">
                {[1,2,3].map(i => <div key={i} className="h-24 bg-surface-900 rounded-2xl" />)}
              </div>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
