import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Users, Play, ArrowRight } from 'lucide-react';
import { fetchAgents } from '../lib/api';

const Agents: React.FC = () => {
  const { data: agents, isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: fetchAgents,
  });

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto"></div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Users size={24} className="text-accent" />
          <h1 className="text-3xl font-bold tracking-tight gradient-text">Agent Fleet</h1>
        </div>
        <div className="flex items-center space-x-2 px-4 py-2 rounded-full bg-[#3730a3]/30 border border-[#6366f1]/30">
          <span className="text-xs font-medium text-gray-300">{agents?.length || 0} Total Agents</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents?.map((agent) => (
          <Link 
            key={agent.name} 
            to={`/agent/${encodeURIComponent(agent.name)}`}
            className="glass-card p-6 card-clickable cursor-pointer group"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h3 className="text-lg font-bold text-accent group-hover:text-white transition-colors">{agent.name}</h3>
                <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-[#3730a3] text-gray-400 mt-1 inline-block">
                  {agent.role}
                </span>
              </div>
              <div className="p-2 rounded-lg bg-accent/10 text-accent group-hover:bg-accent group-hover:text-white transition-colors">
                <Play size={16} />
              </div>
            </div>
            
            <p className="text-sm text-gray-400 line-clamp-2 mb-4 min-h-[40px]">
              {agent.description}
            </p>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Capabilities</span>
                <span className="text-gray-400">
                  {Object.keys(agent.capabilities || {}).length} features
                </span>
              </div>
              
              {Object.entries(agent.capabilities || {}).slice(0, 2).map(([key]) => (
                <div key={key} className="flex items-center gap-2 text-xs">
                  <div className="w-1.5 h-1.5 rounded-full bg-accent"></div>
                  <span className="text-gray-400 capitalize">{key.replace(/_/g, ' ')}</span>
                </div>
              ))}
            </div>

            <div className="mt-4 pt-4 border-t border-[#3730a3]/30 flex items-center text-accent text-sm opacity-0 group-hover:opacity-100 transition-opacity">
              View Details <ArrowRight size={16} className="ml-2" />
            </div>
          </Link>
        ))}
      </div>

      {agents?.length === 0 && (
        <div className="glass-card p-12 text-center">
          <Users size={48} className="text-gray-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-400 mb-2">No Agents Found</h3>
          <p className="text-gray-500">The agent fleet is currently empty. Check back later.</p>
        </div>
      )}
    </div>
  );
};

export default Agents;
