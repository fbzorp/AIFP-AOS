import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileText,
  ThumbsUp,
  ThumbsDown,
  Edit2,
  AlertCircle,
  CheckCircle,
  Clock,
  Send,
  Plus
} from 'lucide-react';
import { useState } from 'react';
import { 
  fetchContent, 
  approveContent, 
  rejectContent,
  editContent,
  cn 
} from '../lib/api';
import PublishModal from '../components/PublishModal';
import ContentModal from '../components/ContentModal';

const ContentQueue: React.FC = () => {
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ title: '', body: '' });
  const [isCreateContentModalOpen, setIsCreateContentModalOpen] = useState(false);
  const [isPublishModalOpen, setIsPublishModalOpen] = useState(false);
  const [selectedContentForPublish, setSelectedContentForPublish] = useState<any>(null);

  const { data: content, isLoading } = useQuery({
    queryKey: ['content'],
    queryFn: fetchContent,
    refetchInterval: 5000,
  });

  const approveMutation = useMutation({
    mutationFn: ({ id }: { id: string }) => approveContent(id, 'Human Operator'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content'] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id }: { id: string }) => rejectContent(id, 'Human Operator', 'Rejected via queue'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content'] });
    },
  });

  const editMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: any }) => editContent(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content'] });
      setEditingId(null);
      setEditForm({ title: '', body: '' });
    },
  });

  const publishMutation = useMutation({
    mutationFn: ({ id }: { id: string }) => api.post(`/content/${id}/publish`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content'] });
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
      queryClient.invalidateQueries({ queryKey: ['calendar'] });
    },
  });

  const handleEditClick = (item: any) => {
    setEditingId(item.id);
    setEditForm({ title: item.title, body: item.body || '' });
  };

  const handleSaveEdit = (id: string) => {
    editMutation.mutate({ id, updates: editForm });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle size={16} className="text-green-400" />;
      case 'rejected':
        return <AlertCircle size={16} className="text-red-400" />;
      case 'pending_review':
        return <Clock size={16} className="text-yellow-400" />;
      default:
        return <Clock size={16} className="text-blue-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-500/10 text-green-400';
      case 'rejected':
        return 'bg-red-500/10 text-red-400';
      case 'pending_review':
        return 'bg-yellow-500/10 text-yellow-400';
      default:
        return 'bg-blue-500/10 text-blue-400';
    }
  };

  if (isLoading) {
    return <div className="p-8">Loading content queue...</div>;
  }

  const pendingItems = content?.filter(item => item.status === 'draft' || item.status === 'pending_review') || [];
  const approvedItems = content?.filter(item => item.status === 'approved') || [];
  const rejectedItems = content?.filter(item => item.status === 'rejected') || [];

  return (
    <div className="p-8 space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FileText size={24} className="text-accent" />
          <h1 className="text-3xl font-bold tracking-tight gradient-text">Content Queue Management</h1>
        </div>
        <button
          onClick={() => setIsCreateContentModalOpen(true)}
          className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors font-medium"
        >
          <Plus size={18} />
          <span>Create Content</span>
        </button>
      </div>

      {/* Pending Review Section */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-2">
            <Clock size={20} className="text-yellow-400" />
            <h2 className="text-xl font-semibold">Pending Review ({pendingItems.length})</h2>
          </div>
        </div>
        <div className="space-y-4">
          {pendingItems.length > 0 ? pendingItems.map((item: any) => (
            <div key={item.id} className="p-4 rounded-xl bg-[#1e1b4b]/30 border border-[#3730a3]/50 card-clickable cursor-pointer">
              {editingId === item.id ? (
                <div className="space-y-4">
                  <input
                    type="text"
                    value={editForm.title}
                    onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-[#1e1b4b] border border-[#3730a3] text-white"
                    placeholder="Title"
                  />
                  <textarea
                    value={editForm.body}
                    onChange={(e) => setEditForm({ ...editForm, body: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-[#1e1b4b] border border-[#3730a3] text-white h-24"
                    placeholder="Body content"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleSaveEdit(item.id)}
                      disabled={editMutation.isPending}
                      className="px-4 py-2 rounded-lg bg-green-500/10 text-green-400 hover:bg-green-500/20 transition-colors"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="px-4 py-2 rounded-lg bg-[#3730a3]/50 text-gray-400 hover:bg-[#3730a3] transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#3730a3] text-gray-300 uppercase">
                          {item.channel}
                        </span>
                        <span className={cn("text-[10px] font-bold px-1.5 py-0.5 rounded flex items-center gap-1", getStatusColor(item.status))}>
                          {getStatusIcon(item.status)} {item.status}
                        </span>
                      </div>
                      <h3 className="font-medium text-white mb-1">{item.title}</h3>
                      {item.body && <p className="text-sm text-gray-400 mb-2 line-clamp-2">{item.body}</p>}
                      <p className="text-xs text-gray-500">Generated by {item.author_agent}</p>
                      {item.compliance_status && (
                        <p className="text-xs text-gray-500 mt-1">Compliance: {item.compliance_status}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => handleEditClick(item)}
                        className="p-2 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-colors"
                        title="Edit"
                      >
                        <Edit2 size={18} />
                      </button>
                      <button
                        onClick={() => rejectMutation.mutate({ id: item.id })}
                        disabled={rejectMutation.isPending}
                        className="p-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
                        title="Reject"
                      >
                        <ThumbsDown size={18} />
                      </button>
                      <button
                        onClick={() => approveMutation.mutate({ id: item.id })}
                        disabled={approveMutation.isPending}
                        className="p-2 rounded-lg bg-accent/10 text-accent hover:bg-accent/20 transition-colors"
                        title="Approve"
                      >
                        <ThumbsUp size={18} />
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          )) : (
            <div className="text-center py-8 text-surface-500 italic">No content awaiting review</div>
          )}
        </div>
      </div>

      {/* Approved Section */}
      {approvedItems.length > 0 && (
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-2">
              <CheckCircle size={20} className="text-green-400" />
              <h2 className="text-xl font-semibold">Approved ({approvedItems.length})</h2>
            </div>
          </div>
          <div className="space-y-4">
            {approvedItems.map((item: any) => (
              <div key={item.id} className="p-4 rounded-xl bg-[#1e1b4b]/30 border border-green-500/20 card-clickable cursor-pointer">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#3730a3] text-gray-300 uppercase">
                    {item.channel}
                  </span>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-green-500/10 text-green-400 flex items-center gap-1">
                    <CheckCircle size={12} /> Approved
                  </span>
                </div>
                <h3 className="font-medium text-white">{item.title}</h3>
                <p className="text-xs text-gray-500 mt-1">By {item.author_agent}</p>
                <button
                  onClick={() => {
                    setSelectedContentForPublish(item);
                    setIsPublishModalOpen(true);
                  }}
                  className="mt-3 w-full px-3 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors text-sm font-medium flex items-center justify-center gap-2"
                >
                  <Send size={14} /> Publish
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rejected Section */}
      {rejectedItems.length > 0 && (
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-2">
              <AlertCircle size={20} className="text-red-400" />
              <h2 className="text-xl font-semibold">Rejected ({rejectedItems.length})</h2>
            </div>
          </div>
          <div className="space-y-4">
            {rejectedItems.map((item: any) => (
              <div key={item.id} className="p-4 rounded-xl bg-[#1e1b4b]/30 border border-red-500/20 card-clickable cursor-pointer">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#3730a3] text-gray-300 uppercase">
                    {item.channel}
                  </span>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 flex items-center gap-1">
                    <AlertCircle size={12} /> Rejected
                  </span>
                </div>
                <h3 className="font-medium text-white">{item.title}</h3>
                <p className="text-xs text-gray-500 mt-1">By {item.author_agent}</p>
              </div>
            ))}
          </div>
        </div>
      )}

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

export default ContentQueue;
