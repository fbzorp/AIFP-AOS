import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Send, ExternalLink, CheckCircle } from 'lucide-react';
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
  const queryClient = useQueryClient();

  const publishMutation = useMutation({
    mutationFn: (id: string) => api.post(`/content/${id}/publish`),
    onSuccess: (result: any) => {
      setPublishResult(result.data);
      queryClient.invalidateQueries({ queryKey: ['content'] });
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
      queryClient.invalidateQueries({ queryKey: ['calendar'] });
      setIsPublishing(false);
    },
    onError: (error) => {
      console.error('Publish failed:', error);
      setIsPublishing(false);
    },
  });

  const handlePublish = () => {
    if (!contentId) return;
    setIsPublishing(true);
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

        {publishResult ? (
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
