import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Send, X, ExternalLink, CheckCircle, AlertCircle, Sparkles } from 'lucide-react';
import Modal from './Modal';
import { api, cn, publishContentItem } from '../lib/api';

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
  const queryClient = useQueryClient();

  const publishMutation = useMutation({
    mutationFn: (id: string) => api.post(`/content/${id}/publish`),
    onSuccess: (result) => {
      setPublishResult(result.data);
      queryClient.invalidateQueries({ queryKey: ['content'] });
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
      queryClient.invalidateQueries({ queryKey: ['calendar'] });
      setIsPublishing(false);
    },
    onError: (error) => {
      console.error('Failed to publish:', error);
      setPublishResult({ error: 'Failed to publish content' });
      setIsPublishing(false);
    },
  });

  const handlePublish = () => {
    if (!contentId) return;
    setIsPublishing(true);
    publishMutation.mutate(contentId);
  };

  const handleClose = () => {
    setPublishResult(null);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Publish to Moltbook" size="lg">
      <div className="space-y-6">
        {!publishResult ? (
          <>
            <div className="p-4 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3]/30">
              <h3 className="font-semibold text-white mb-2">Content Preview</h3>
              <div className="space-y-2">
                <div>
                  <span className="text-xs text-gray-400">Title:</span>
                  <p className="text-white">{contentTitle || 'Untitled'}</p>
                </div>
                <div>
                  <span className="text-xs text-gray-400">Channel:</span>
                  <p className="text-white capitalize">{channel || 'twitter'}</p>
                </div>
                <div>
                  <span className="text-xs text-gray-400">Content:</span>
                  <p className="text-white text-sm line-clamp-3">{contentBody || 'No content body'}</p>
                </div>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <Sparkles size={20} className="text-blue-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-blue-400 mb-1">Moltbook Publishing</h4>
                <p className="text-sm text-gray-300">
                  This will publish the content to the Moltbook platform. The content will be visible to the target audience immediately after successful publication.
                </p>
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <button
                onClick={handleClose}
                className="flex-1 px-4 py-2 rounded-lg border border-[#3730a3] text-gray-300 hover:bg-[#3730a3]/30 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handlePublish}
                disabled={isPublishing || !contentId}
                className="flex-1 px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isPublishing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Publishing...
                  </>
                ) : (
                  <>
                    <Send size={18} />
                    Publish Now
                  </>
                )}
              </button>
            </div>
          </>
        ) : (
          <div className="text-center space-y-4">
            {publishResult.error ? (
              <>
                <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mx-auto">
                  <AlertCircle size={32} className="text-red-400" />
                </div>
                <h3 className="text-xl font-semibold text-red-400">Publish Failed</h3>
                <p className="text-gray-400">{publishResult.error}</p>
                <button
                  onClick={handleClose}
                  className="px-4 py-2 rounded-lg border border-[#3730a3] text-gray-300 hover:bg-[#3730a3]/30 transition-colors"
                >
                  Close
                </button>
              </>
            ) : (
              <>
                <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto">
                  <CheckCircle size={32} className="text-green-400" />
                </div>
                <h3 className="text-xl font-semibold text-green-400">Published Successfully!</h3>
                <p className="text-gray-400">Your content has been published to Moltbook</p>
                {publishResult.post_url && (
                  <a
                    href={publishResult.post_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#3730a3]/30 border border-[#6366f1]/30 text-white hover:bg-[#3730a3]/50 transition-colors"
                  >
                    <ExternalLink size={16} />
                    View Post
                  </a>
                )}
                <button
                  onClick={handleClose}
                  className="px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors"
                >
                  Done
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
}
