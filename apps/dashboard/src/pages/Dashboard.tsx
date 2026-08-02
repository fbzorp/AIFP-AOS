import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  Users,
  CheckCircle,
  AlertCircle,
  Zap,
  ShieldCheck,
  Search,
  Database,
  FileText,
  ExternalLink,
  Target,
  ThumbsUp,
  ThumbsDown,
  Plus,
  Send
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  fetchMetrics, 
  fetchAgents, 
  fetchHealth, 
  fetchSources, 
  fetchContent, 
  approveContent, 
  rejectContent,
  publishContentItem,
  cn 
} from '../lib/api';
import CreateTaskModal from '../components/CreateTaskModal';
import ContentModal from '../components/ContentModal';
import PublishModal from '../components/PublishModal';

const Dashboard: React.FC = () => {
  const [isCreateTaskModalOpen, setIsCreateTaskModalOpen] = useState(false);
  const [isCreateContentModalOpen, setIsCreateContentModalOpen] = useState(false);
  const [isPublishModalOpen, setIsPublishModalOpen] = useState(false);
  const [selectedContentForPublish, setSelectedContentForPublish] = useState<any>(null);
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['metrics'],
    queryFn: fetchMetrics,
    refetchInterval: 3000,
    retry: 1,
  });

  const { data: agents, isLoading: agentsLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: fetchAgents,
    retry: 1,
  });

  const { data: sources } = useQuery({
    queryKey: ['sources'],
    queryFn: fetchSources,
    refetchInterval: 10000,
    retry: 1,
  });

  const queryClient = useQueryClient();

  const { data: content, isLoading: contentLoading } = useQuery({
    queryKey: ['content'],
    queryFn: fetchContent,
    refetchInterval: 3000,
    retry: 1,
  });

  const approveMutation = useMutation({
    mutationFn: ({ id }: { id: string }) => approveContent(id, 'Human Operator'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content'] });
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id }: { id: string }) => rejectContent(id, 'Human Operator', 'Rejected via dashboard'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content'] });
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
    },
  });

  const publishMutation = useMutation({
    mutationFn: ({ id }: { id: string }) => publishContentItem(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content'] });
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
      queryClient.invalidateQueries({ queryKey: ['calendar'] });
    },
  });

  const pendingApprovals = content?.filter(item => item.status === 'draft' || item.status === 'pending_review') || [];
  const readyToPublish = content?.filter(item => item.status === 'approved') || [];

  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 10000,
    retry: 1,
  });

  // Show loading state if everything is loading
  if (metricsLoading && agentsLoading && contentLoading && healthLoading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
          <p className="text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight gradient-text">Growth Orchestrator</h1>
          <p className="text-gray-400 mt-1">Autonomous Marketing Operations Center</p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsCreateContentModalOpen(true)}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-[#3730a3]/30 border border-[#6366f1]/30 text-white hover:bg-[#3730a3]/50 transition-colors font-medium"
          >
            <Send size={18} />
            <span>Create Content</span>
          </button>
          <button
            onClick={() => setIsCreateTaskModalOpen(true)}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors font-medium"
          >
            <Plus size={18} />
            <span>Create Task</span>
          </button>
          <div className="flex items-center space-x-2 px-4 py-2 rounded-full bg-[#3730a3]/30 border border-[#6366f1]/30">
            <div className={cn(
              "w-2 h-2 rounded-full",
              health?.status === 'ok' ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" : "bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.6)]"
            )} />
            <span className="text-xs font-medium text-gray-300">System: {health?.status || 'connecting...'}</span>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
        <Link to="/agents" className="stat-card group block">
          <div className="flex justify-between items-start">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-400 truncate">Active Agents</p>
              <h3 className="text-2xl font-bold mt-1 group-hover:text-accent transition-colors">{metricsLoading ? '...' : (agents?.length || 0)}</h3>
            </div>
            <div className="p-2 rounded-lg flex-shrink-0 ml-2 bg-accent/10 text-accent">
              <Users size={20} />
            </div>
          </div>
        </Link>
        <Link to="/campaigns" className="stat-card group block">
          <div className="flex justify-between items-start">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-400 truncate">Campaigns</p>
              <h3 className="text-2xl font-bold mt-1 group-hover:text-accent transition-colors">{metricsLoading ? '...' : (metrics?.campaigns || 0)}</h3>
            </div>
            <div className="p-2 rounded-lg flex-shrink-0 ml-2 bg-purple-500/10 text-purple-400">
              <Target size={20} />
            </div>
          </div>
        </Link>
        <Link to="/content-queue" className="stat-card group block">
          <div className="flex justify-between items-start">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-400 truncate">Content Queue</p>
              <h3 className="text-2xl font-bold mt-1 group-hover:text-accent transition-colors">{metricsLoading ? '...' : (content?.length || 0)}</h3>
            </div>
            <div className="p-2 rounded-lg flex-shrink-0 ml-2 bg-accent/10 text-accent">
              <FileText size={20} />
            </div>
          </div>
        </Link>
        <Link to="/content-queue" className="stat-card group block">
          <div className="flex justify-between items-start">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-400 truncate">Pending Approvals</p>
              <h3 className="text-2xl font-bold mt-1 group-hover:text-accent transition-colors">{metricsLoading ? '...' : (pendingApprovals?.length || 0)}</h3>
            </div>
            <div className="p-2 rounded-lg flex-shrink-0 ml-2 bg-indigo-500/10 text-indigo-400">
              <ShieldCheck size={20} />
            </div>
          </div>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Activity & Sources */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Approval Queue */}
          <div id="approval-queue" className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <ShieldCheck size={20} className="text-accent" />
                <h2 className="text-xl font-semibold">Human Approval Queue</h2>
              </div>
              <span className="px-2 py-1 rounded-md bg-accent/10 text-accent text-xs font-bold">
                {pendingApprovals.length} Pending
              </span>
            </div>
            <div className="space-y-4">
              {pendingApprovals.length > 0 ? pendingApprovals.map((item) => (
                <Link key={item.id} to="/content-queue" className="block">
                  <div className="p-4 rounded-xl bg-[#1e1b4b]/30 border border-[#3730a3]/50 flex items-center justify-between card-clickable cursor-pointer">
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#3730a3] text-gray-300 uppercase">
                          {item.channel}
                        </span>
                        <h3 className="font-medium text-white">{item.title}</h3>
                      </div>
                      <p className="text-xs text-gray-400 line-clamp-1">{item.objective}</p>
                      <p className="text-[10px] text-gray-500">Generated by {item.author_agent}</p>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <button 
                        onClick={(e) => {
                          e.preventDefault();
                          rejectMutation.mutate({ id: item.id });
                        }}
                        disabled={rejectMutation.isPending}
                        className="p-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
                        title="Reject"
                      >
                        <ThumbsDown size={18} />
                      </button>
                      <button 
                        onClick={(e) => {
                          e.preventDefault();
                          approveMutation.mutate({ id: item.id });
                        }}
                        disabled={approveMutation.isPending}
                        className="p-2 rounded-lg bg-accent/10 text-accent hover:bg-accent/20 transition-colors"
                        title="Approve"
                      >
                        <ThumbsUp size={18} />
                      </button>
                    </div>
                  </div>
                </Link>
              )) : (
                <div className="text-center py-4 text-gray-500 italic text-sm">No content awaiting approval</div>
              )}
            </div>
          </div>

          {/* Ready to Publish Queue */}
          <div id="ready-to-publish" className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <CheckCircle size={20} className="text-green-400" />
                <h2 className="text-xl font-semibold">Ready to Publish</h2>
              </div>
              <span className="px-2 py-1 rounded-md bg-green-500/10 text-green-400 text-xs font-bold">
                {readyToPublish.length} Approved
              </span>
            </div>
            <div className="space-y-4">
              {readyToPublish.length > 0 ? readyToPublish.map((item) => (
                <Link key={item.id} to="/content-queue" className="block">
                  <div className="p-4 rounded-xl bg-[#1e1b4b]/30 border border-[#3730a3]/50 flex items-center justify-between card-clickable cursor-pointer">
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#3730a3] text-gray-300 uppercase">
                          {item.channel}
                        </span>
                        <h3 className="font-medium text-white">{item.title}</h3>
                      </div>
                      <p className="text-xs text-gray-400 line-clamp-1">{item.objective}</p>
                      <p className="text-[10px] text-gray-500">Scheduled for {item.scheduled_at ? new Date(item.scheduled_at).toLocaleDateString() : 'immediate'}</p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        setSelectedContentForPublish(item);
                        setIsPublishModalOpen(true);
                      }}
                      disabled={publishMutation.isPending}
                      className="px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors text-sm font-bold flex items-center gap-2"
                    >
                      <Zap size={14} /> Publish Now
                    </button>
                  </div>
                </Link>
              )) : (
                <div className="text-center py-4 text-gray-500 italic text-sm">No approved content ready for publication</div>
              )}
            </div>
          </div>

          {/* Recent Intelligence Sources */}
          <div id="sources" className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <Database size={20} className="text-indigo-400" />
                <h2 className="text-xl font-semibold">Market Intelligence Feed</h2>
              </div>
            </div>
            <div className="space-y-4">
              {sources?.slice(0, 3).map((source) => (
                <a key={source.id} href={source.url} target="_blank" rel="noreferrer" className="block">
                  <div className="p-4 rounded-xl bg-[#1e1b4b]/30 border border-[#3730a3]/50 hover:border-[#6366f1]/30 transition-all card-clickable cursor-pointer">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold text-white flex items-center gap-2">
                        {source.title}
                        <ExternalLink size={14} className="text-gray-500 hover:text-indigo-400" />
                      </h3>
                      <span className="text-xs font-bold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400">
                        Score: {source.relevance_score.toFixed(2)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400 line-clamp-2 mb-2">{source.summary}</p>
                    <div className="flex items-center gap-4 text-[10px] text-gray-500 uppercase tracking-wider">
                      <span className="flex items-center gap-1"><Target size={10} /> {source.topic}</span>
                      <span>{new Date(source.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </a>
              )) || <div className="text-center py-8 text-gray-500 italic">No intelligence gathered yet</div>}
            </div>
          </div>

          {/* Planned Content Queue */}
          <div id="planned-content" className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <FileText size={20} className="text-green-400" />
                <h2 className="text-xl font-semibold">Planned Content Queue</h2>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {content?.slice(0, 4).map((item) => (
                <Link key={item.id} to="/content-queue" className="block">
                  <div className="p-4 rounded-xl bg-[#1e1b4b]/30 border border-[#3730a3]/50 card-clickable cursor-pointer">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#3730a3] text-gray-300 uppercase">
                        {item.channel}
                      </span>
                      <span className="text-[10px] text-gray-500">
                        {new Date(item.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <h3 className="font-medium text-white mb-1">{item.title}</h3>
                    <p className="text-xs text-gray-400 mb-3 line-clamp-1">{item.objective}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-accent font-medium">By {item.author_agent}</span>
                      <div className="flex items-center gap-1 text-[10px] text-gray-500">
                        <ShieldCheck size={10} /> {item.status}
                      </div>
                    </div>
                  </div>
                </Link>
              )) || <div className="col-span-2 text-center py-8 text-gray-500 italic">No content planned yet</div>}
            </div>
          </div>
        </div>

        {/* Right Column: Agents & Activity */}
        <div className="space-y-8">
          {/* Activity Feed */}
          <div id="activity" className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <Activity size={20} className="text-accent" />
                <h2 className="text-xl font-semibold">Live Activity</h2>
              </div>
            </div>
            <div className="space-y-4">
              {metrics?.recent_activity?.slice(0, 5).map((event) => (
                <div key={event.id} className="flex items-start space-x-3 text-xs">
                  <div className="mt-1">
                    {event.event_type.includes('success') ? <ShieldCheck size={14} className="text-green-400" /> : 
                     event.event_type.includes('fail') ? <AlertCircle size={14} className="text-red-400" /> :
                     <Zap size={14} className="text-accent" />}
                  </div>
                  <div>
                    <p className="font-medium text-gray-200">{event.agent_name}</p>
                    <p className="text-gray-500">{event.message}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Specialized Agents */}
          <div id="agents" className="space-y-4">
            <div className="flex items-center space-x-2">
              <Search size={20} className="text-accent" />
              <h2 className="text-xl font-semibold text-white">Agent Fleet</h2>
            </div>
            {agents?.slice(0, 4).map((agent) => (
              <Link key={agent.name} to={`/agent/${encodeURIComponent(agent.name)}`} className="block">
                <div className="glass-card p-4 card-clickable cursor-pointer group">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="text-sm font-bold text-accent group-hover:text-white transition-colors">{agent.name}</h3>
                    <span className="text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-[#3730a3] text-gray-400">
                      {agent.role}
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-400 line-clamp-2">
                    {agent.description}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Create Task Modal */}
      <CreateTaskModal 
        isOpen={isCreateTaskModalOpen}
        onClose={() => setIsCreateTaskModalOpen(false)}
      />

      {/* Create Content Modal */}
      <ContentModal 
        isOpen={isCreateContentModalOpen}
        onClose={() => setIsCreateContentModalOpen(false)}
      />

      {/* Publish Modal */}
      <PublishModal 
        isOpen={isPublishModalOpen}
        onClose={() => setIsPublishModalOpen(false)}
        contentId={selectedContentForPublish?.id}
        contentTitle={selectedContentForPublish?.title}
        contentBody={selectedContentForPublish?.body}
        channel={selectedContentForPublish?.channel}
      />
    </div>
  );
};

export default Dashboard;
