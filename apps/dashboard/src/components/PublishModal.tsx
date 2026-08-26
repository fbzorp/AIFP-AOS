import { useState, useEffect } from 'react';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { Send, ExternalLink, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import Modal from './Modal';
import { api } from '../lib/api';

interface PublishModalProps {
  isOpen: boolean;
  onClose: () => void;
  contentId?: string;
  contentTitle?: string;
  contentBody?: string;
  channel?: string;
}

export default function PublishModal({ isOpen, onClose, contentId, contentTitle, contentBody, channel }: PublishModalProps) {
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishResult, setPublishResult] = useState<any>(null);
  const [publishError, setPublishError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Poll for content status to check if publish completed
  const { data: content } = useQuery({
    queryKey: ['content'],
    queryFn: () => api.get('/content').then(res => res.data),
    refetchInterval: isPublishing ? 2000 : false, // Poll every 2s while publishing
    enabled: isPublishing && !!contentId,
  });

  // Check if the content has been published successfully
  useEffect(() => {
    if (isPublishing && contentId && content) {
      const item = content.find((c: any) => c.id === contentId);
      if (item) {
        if (item.status === 'published' && item.post_url) {
          // Successfully published with URL
          setPublishResult({ status: 'published', post_url: item.post_url });
          setIsPublishing(false);
          setPublishError(null);
        } else if (item.publish_error) {
          // Publish failed
          setPublishError(item.publish_error);
          setIsPublishing(false);
          setPublishResult(null);
        }
        // If still in approved state or status changed but no URL yet, keep polling
      }
    }
  }, [content, isPublishing, contentId]);

  const publishMutation = useMutation({
    mutationFn: (id: string) => api.post(`/content/${id}/publish`),
    onSuccess: (result: any) => {
      // The publish endpoint returns {status: "publish_enqueued"}
      // We don't show success yet - we wait for the actual publish to complete
      setPublishResult({ status: 'enqueued' });
      setIsPublishing(true); // Start polling
      queryClient.invalidateQueries({ queryKey: ['content'] });
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to enqueue publish';
      setPublishError(errorMessage);
      setIsPublishing(false);
    },
  });

  const handlePublish = () => {
    if (!contentId) return;
    setIsPublishing(true);
    setPublishError(null);
    setPublishResult(null);
    publishMutation.mutate(contentId);
  };

  if (!isOpen) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Publish Content">
      <div className="space-y-4">
        {contentTitle && (
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Title</label>
            <p className="text-white">{contentTitle}</p>
          </div>
        )}
        
        {channel && (
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Channel</label>
            <p className="text-white">{channel}</p>
          </div>
        )}

        {contentBody && (
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Content Preview</label>
            <div className="p-3 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3]/30 max-h-48 overflow-y-auto">
              <p className="text-sm text-gray-300 whitespace-pre-wrap">{contentBody.substring(0, 500)}{contentBody.length > 500 ? '...' : ''}</p>
            </div>
          </div>
        )}

        {publishError && (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30">
            <div className="flex items-center gap-2 text-red-400 mb-2">
              <AlertCircle size={20} />
              <span className="font-semibold">Publish Failed</span>
            </div>
            <p className="text-sm text-red-300">{publishError}</p>
          </div>
        )}

        {publishResult?.status === 'published' ? (
          <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/30">
            <div className="flex items-center gap-2 text-green-400 mb-2">
              <CheckCircle size={20} />
              <span className="font-semibold">Published Successfully</span>
            </div>
            {publishResult.post_url && (
              <a
                href={publishResult.post_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300"
              >
                <ExternalLink size={16} />
                <span>View Post</span>
              </a>
            )}
          </div>
        ) : publishResult?.status === 'enqueued' || isPublishing ? (
          <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/30">
            <div className="flex items-center gap-2 text-blue-400 mb-2">
              <Clock size={20} />
              <span className="font-semibold">Publish enqueued — processing</span>
            </div>
            <p className="text-sm text-blue-300">Content is being published. This may take a few moments...</p>
          </div>
        ) : (
          <button
            onClick={handlePublish}
            disabled={isPublishing}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isPublishing ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Publishing...</span>
              </>
            ) : (
              <>
                <Send size={18} />
                <span>Publish Now</span>
              </>
            )}
          </button>
        )}
      </div>
    </Modal>
  );
}
