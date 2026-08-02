import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { ArrowLeft, Shield, Zap, Database, Users, Clock, Play, Pause, RotateCcw } from 'lucide-react';
import { fetchAgents, api, cn } from '../lib/api';

const AgentDetails: React.FC = () => {
  const { agentName } = useParams<{ agentName: string }>();
  const navigate = useNavigate();
  const [isExecuting, setIsExecuting] = useState(false);
  
  const { data: agents, isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: fetchAgents,
  });

  const agent = agents?.find(a => a.name === agentName);

  const executeAgentMutation = useMutation({
    mutationFn: (inputData: any) => api.post('/tasks', {
      task_type: agentName,
      input_data: inputData
    }),
    onSuccess: () => {
      setIsExecuting(false);
    },
    onError: () => {
      setIsExecuting(false);
    }
  });

  const handleExecuteAgent = () => {
    if (!agent) return;
    setIsExecuting(true);
    executeAgentMutation.mutate({
      objective: 'Manual execution from dashboard'
    });
  };

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto"></div>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="p-8">
        <div className="glass-card p-8 text-center">
          <h2 className="text-xl font-semibold mb-4">Agent not found</h2>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/')}
            className="p-2 rounded-lg hover:bg-[#3730a3] transition-colors"
          >
            <ArrowLeft size={24} className="text-white" />
          </button>
          <div>
            <h1 className="text-3xl font-bold gradient-text">{agent.name}</h1>
            <p className="text-gray-400 mt-1">{agent.role}</p>
          </div>
        </div>
        <button
          onClick={handleExecuteAgent}
          disabled={isExecuting}
          className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isExecuting ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              Executing...
            </>
          ) : (
            <>
              <Play size={18} />
              Execute Agent
            </>
          )}
        </button>
      </div>

      {/* Agent Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Basic Info */}
        <div className="glass-card p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center space-x-2">
            <Users size={20} className="text-accent" />
            <span>Agent Information</span>
          </h2>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-400 mb-1">Name</p>
              <p className="text-white font-medium">{agent.name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-400 mb-1">Role</p>
              <p className="text-white font-medium">{agent.role}</p>
            </div>
            <div>
              <p className="text-sm text-gray-400 mb-1">Description</p>
              <p className="text-white">{agent.description}</p>
            </div>
          </div>
        </div>

        {/* Capabilities */}
        <div className="glass-card p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center space-x-2">
            <Zap size={20} className="text-accent" />
            <span>Capabilities</span>
          </h2>
          <div className="space-y-3">
            {Object.entries(agent.capabilities || {}).length > 0 ? (
              Object.entries(agent.capabilities).map(([key, value]) => (
                <div key={key} className="p-3 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3]/30">
                  <p className="text-sm font-medium text-white capitalize">{key.replace(/_/g, ' ')}</p>
                  <p className="text-xs text-gray-400 mt-1">{String(value)}</p>
                </div>
              ))
            ) : (
              <p className="text-gray-400 text-sm">No capabilities defined</p>
            )}
          </div>
        </div>
      </div>

      {/* Performance Stats */}
      <div className="glass-card p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center space-x-2">
          <Shield size={20} className="text-accent" />
          <span>Performance Metrics</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-4 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3]/30">
            <div className="flex items-center space-x-2 mb-2">
              <Clock size={16} className="text-green-400" />
              <span className="text-sm text-gray-400">Tasks Completed</span>
            </div>
            <p className="text-2xl font-bold text-white">-</p>
          </div>
          <div className="p-4 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3]/30">
            <div className="flex items-center space-x-2 mb-2">
              <Database size={16} className="text-blue-400" />
              <span className="text-sm text-gray-400">Success Rate</span>
            </div>
            <p className="text-2xl font-bold text-white">-</p>
          </div>
          <div className="p-4 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3]/30">
            <div className="flex items-center space-x-2 mb-2">
              <Zap size={16} className="text-accent" />
              <span className="text-sm text-gray-400">Avg Response Time</span>
            </div>
            <p className="text-2xl font-bold text-white">-</p>
          </div>
        </div>
      </div>

      {/* Recent Tasks */}
      <div className="glass-card p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center space-x-2">
          <RotateCcw size={20} className="text-accent" />
          <span>Recent Task Activity</span>
        </h2>
        <div className="text-center py-8 text-gray-400">
          Task history would be displayed here
        </div>
      </div>
    </div>
  );
};

export default AgentDetails;
