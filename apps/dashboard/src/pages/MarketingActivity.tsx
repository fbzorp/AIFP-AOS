import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  FileText,
  ExternalLink,
  CheckCircle,
  AlertCircle,
  Clock,
  Filter,
  Download,
  Globe,
  Share2,
  Zap,
  Search,
  TrendingUp
} from 'lucide-react';
import {
  fetchMarketingActivity,
  exportMarketingActivityCSV
} from '../lib/api';

const MarketingActivity: React.FC = () => {
  const [filterChannel, setFilterChannel] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [onlyReal, setOnlyReal] = useState<boolean>(false);

  const { data: activity, isLoading, error } = useQuery({
    queryKey: ['marketingActivity', filterChannel, filterStatus, onlyReal],
    queryFn: () => fetchMarketingActivity({
      channel: filterChannel || undefined,
      status: filterStatus || undefined,
      only_real: onlyReal
    }),
    refetchInterval: 10000,
  });

  const handleExportCSV = async () => {
    try {
      const blob = await exportMarketingActivityCSV({
        channel: filterChannel || undefined,
        status: filterStatus || undefined,
        only_real: onlyReal
      });
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `marketing_activity_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Failed to export CSV:', error);
    }
  };

  const channels = Array.from(new Set(activity?.items.map(item => item.channel).filter(Boolean) || []));
  const statuses = Array.from(new Set(activity?.items.map(item => item.status).filter(Boolean) || []));

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
          <p className="text-gray-400">Loading marketing activity...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="text-center py-12">
          <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">Failed to load marketing activity</h3>
          <p className="text-gray-400">Please try again later</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight gradient-text">Marketing Activity & Evidence Registry</h1>
          <p className="text-gray-400 mt-1">Complete lineage: created → approved → published → live URLs</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleExportCSV}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-[#3730a3]/30 border border-[#6366f1]/30 hover:bg-[#3730a3]/50 transition-colors"
          >
            <Download size={16} className="text-gray-300" />
            <span className="text-sm font-medium text-gray-300">Export CSV</span>
          </button>
          <div className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-[#3730a3]/30 border border-[#6366f1]/30">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span className="text-sm font-medium text-gray-300">
              {activity?.real_publish_count || 0} Real
            </span>
          </div>
          <div className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-[#3730a3]/30 border border-[#6366f1]/30">
            <div className="w-2 h-2 rounded-full bg-amber-500"></div>
            <span className="text-sm font-medium text-gray-300">
              {activity?.dry_run_count || 0} Dry-Run
            </span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="glass-card p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center space-x-2">
            <Filter size={18} className="text-gray-400" />
            <span className="text-sm font-medium text-gray-300">Filters:</span>
          </div>
          
          <select
            value={filterChannel}
            onChange={(e) => setFilterChannel(e.target.value)}
            className="px-3 py-2 rounded-lg bg-[#1e1b4b]/30 border border-[#3730a3]/50 text-white text-sm focus:outline-none focus:border-accent"
          >
            <option value="">All Channels</option>
            {channels.map(channel => (
              <option key={channel} value={channel}>{channel}</option>
            ))}
          </select>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 rounded-lg bg-[#1e1b4b]/30 border border-[#3730a3]/50 text-white text-sm focus:outline-none focus:border-accent"
          >
            <option value="">All Statuses</option>
            {statuses.map(status => (
              <option key={status} value={status}>{status}</option>
            ))}
          </select>

          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={onlyReal}
              onChange={(e) => setOnlyReal(e.target.checked)}
              className="w-4 h-4 rounded border-gray-600 bg-[#1e1b4b]/30 text-accent focus:ring-accent"
            />
            <span className="text-sm text-gray-300">Only Real Publications</span>
          </label>
        </div>
      </div>

      {/* Activity Table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#3730a3]/30">
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Title</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Agent</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Channel</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Keyword</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Created</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Published</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Live URL</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Analytics</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Type</th>
              </tr>
            </thead>
            <tbody>
              {activity?.items.length === 0 ? (
                <tr>
                  <td colSpan={10} className="px-4 py-12 text-center text-gray-500">
                    <FileText className="h-12 w-12 mx-auto mb-4 text-gray-600" />
                    <p>No marketing activity found</p>
                  </td>
                </tr>
              ) : (
                activity?.items.map((item) => (
                  <tr key={item.id} className="border-b border-[#3730a3]/20 hover:bg-[#1e1b4b]/20 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center space-x-2">
                        {item.status === 'published' && item.is_real_publish ? (
                          <CheckCircle size={16} className="text-green-400" />
                        ) : item.status === 'published' && !item.is_real_publish ? (
                          <Clock size={16} className="text-amber-400" />
                        ) : item.status === 'draft' || item.status === 'pending_review' ? (
                          <Clock size={16} className="text-blue-400" />
                        ) : (
                          <AlertCircle size={16} className="text-red-400" />
                        )}
                        <span className="text-sm text-gray-300">{item.status}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm font-medium text-white">{item.title}</div>
                      {item.objective && (
                        <div className="text-xs text-gray-500 line-clamp-1">{item.objective}</div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-gray-300">{item.agent}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs font-bold px-2 py-1 rounded bg-[#3730a3] text-gray-300 uppercase">
                        {item.channel || 'N/A'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-xs text-gray-400">
                        {item.target_keyword || 'N/A'}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-xs text-gray-400">
                        {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'N/A'}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-xs text-gray-400">
                        {item.published_at ? new Date(item.published_at).toLocaleDateString() : 'N/A'}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {item.live_url ? (
                        <a
                          href={item.live_url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center space-x-1 text-accent hover:text-white transition-colors"
                        >
                          <span className="text-xs">{item.live_url.substring(0, 30)}...</span>
                          <ExternalLink size={12} />
                        </a>
                      ) : item.post_url ? (
                        <span className="text-xs text-gray-500 line-clamp-1">{item.post_url}</span>
                      ) : (
                        <span className="text-xs text-gray-500">Not published</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center space-x-2 text-xs text-gray-400">
                        {item.impressions !== undefined && item.impressions > 0 && (
                          <span title="Impressions"><TrendingUp size={12} /> {item.impressions}</span>
                        )}
                        {item.clicks !== undefined && item.clicks > 0 && (
                          <span title="Clicks">{item.clicks}</span>
                        )}
                        {item.engagement !== undefined && item.engagement > 0 && (
                          <span title="Engagement">{item.engagement}</span>
                        )}
                        {(item.impressions === undefined || item.impressions === 0) && (
                          <span>N/A</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {item.is_real_publish ? (
                        <span className="flex items-center space-x-1 text-xs text-green-400">
                          <Globe size={12} />
                          Real
                        </span>
                      ) : (
                        <span className="flex items-center space-x-1 text-xs text-amber-400">
                          <Share2 size={12} />
                          Dry-Run
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Total Items</p>
              <p className="text-2xl font-bold text-white">{activity?.total_count || 0}</p>
            </div>
            <FileText className="text-accent" size={24} />
          </div>
        </div>
        <div className="glass-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Real Publications</p>
              <p className="text-2xl font-bold text-green-400">{activity?.real_publish_count || 0}</p>
            </div>
            <Globe className="text-green-400" size={24} />
          </div>
        </div>
        <div className="glass-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Dry-Run Items</p>
              <p className="text-2xl font-bold text-amber-400">{activity?.dry_run_count || 0}</p>
            </div>
            <Zap className="text-amber-400" size={24} />
          </div>
        </div>
        <div className="glass-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">SEO Pages Indexed</p>
              <p className="text-2xl font-bold text-blue-400">
                {activity?.items.filter(i => i.indexing_status === 'indexed').length || 0}
              </p>
            </div>
            <Search className="text-blue-400" size={24} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketingActivity;