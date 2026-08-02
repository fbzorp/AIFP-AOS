import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Target, Play, Clock, CheckCircle, AlertCircle, Plus, ArrowRight, Zap } from 'lucide-react';
import { api, cn } from '../lib/api';
import CreateTaskModal from '../components/CreateTaskModal';

const Campaigns: React.FC = () => {
  const [isCreateCampaignModalOpen, setIsCreateCampaignModalOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data: campaigns, isLoading } = useQuery({
    queryKey: ['campaigns'],
    queryFn: () => api.get('/campaigns').then(res => res.data),
    refetchInterval: 5000,
  });

  const { data: tasks } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => api.get('/tasks').then(res => res.data),
    refetchInterval: 5000,
  });

  const createCampaignMutation = useMutation({
    mutationFn: (objective: string) => api.post('/campaigns', { objective }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
      setIsCreateCampaignModalOpen(false);
    },
  });

  return (
    <div className="p-8 space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Target size={24} className="text-accent" />
          <h1 className="text-3xl font-bold tracking-tight gradient-text">Campaigns Workflow</h1>
        </div>
        <button
          onClick={() => setIsCreateCampaignModalOpen(true)}
          className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors font-medium"
        >
          <Plus size={18} />
          <span>New Campaign</span>
        </button>
      </div>

      {/* Campaign Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-card p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Target size={16} className="text-accent" />
            <span className="text-sm text-gray-400">Active Campaigns</span>
          </div>
          <p className="text-2xl font-bold text-white">{campaigns?.length || 0}</p>
        </div>
        <div className="glass-card p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Play size={16} className="text-green-400" />
            <span className="text-sm text-gray-400">Running Tasks</span>
          </div>
          <p className="text-2xl font-bold text-white">{tasks?.filter((t: any) => t.status === 'running').length || 0}</p>
        </div>
        <div className="glass-card p-4">
          <div className="flex items-center space-x-2 mb-2">
            <CheckCircle size={16} className="text-blue-400" />
            <span className="text-sm text-gray-400">Completed</span>
          </div>
          <p className="text-2xl font-bold text-white">{tasks?.filter((t: any) => t.status === 'succeeded').length || 0}</p>
        </div>
        <div className="glass-card p-4">
          <div className="flex items-center space-x-2 mb-2">
            <AlertCircle size={16} className="text-red-400" />
            <span className="text-sm text-gray-400">Failed</span>
          </div>
          <p className="text-2xl font-bold text-white">{tasks?.filter((t: any) => t.status === 'failed').length || 0}</p>
        </div>
      </div>

      {/* Active Campaigns */}
      <div className="glass-card p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center space-x-2">
          <Zap size={20} className="text-accent" />
          <span>Active Campaigns</span>
        </h2>
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
          </div>
        ) : campaigns && campaigns.length > 0 ? (
          <div className="space-y-4">
            {campaigns.map((campaign: any) => (
              <div key={campaign.id} className="p-4 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3]/30">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-white mb-1">{campaign.objective}</h3>
                    <div className="flex items-center space-x-4 text-xs text-gray-400">
                      <span className="flex items-center gap-1">
                        <Clock size={12} />
                        {new Date(campaign.created_at).toLocaleDateString()}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-green-500/10 text-green-400">
                        Active
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">
            <Target size={48} className="mx-auto mb-4 opacity-50" />
            <p>No active campaigns</p>
            <button
              onClick={() => setIsCreateCampaignModalOpen(true)}
              className="mt-4 px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors"
            >
              Create First Campaign
            </button>
          </div>
        )}
      </div>

      {/* Recent Tasks */}
      <div className="glass-card p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center space-x-2">
          <Play size={20} className="text-green-400" />
          <span>Recent Tasks</span>
        </h2>
        {tasks && tasks.length > 0 ? (
          <div className="space-y-3">
            {tasks.slice(0, 10).map((task: any) => (
              <div key={task.id} className="flex items-center justify-between p-3 rounded-lg bg-[#1e1b4b]/30 border border-[#3730a3]/30">
                <div className="flex-1">
                  <p className="text-sm font-medium text-white">{task.task_type}</p>
                  <p className="text-xs text-gray-400">ID: {task.id}</p>
                </div>
                <span className={`text-xs px-2 py-1 rounded ${
                  task.status === 'succeeded' ? 'bg-green-500/10 text-green-400' :
                  task.status === 'running' ? 'bg-blue-500/10 text-blue-400' :
                  task.status === 'failed' ? 'bg-red-500/10 text-red-400' :
                  'bg-gray-500/10 text-gray-400'
                }`}>
                  {task.status}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">
            <p>No tasks yet</p>
          </div>
        )}
      </div>

      {/* Create Campaign Modal */}
      <CreateTaskModal
        isOpen={isCreateCampaignModalOpen}
        onClose={() => setIsCreateCampaignModalOpen(false)}
      />
    </div>
  );
};

export default Campaigns;
