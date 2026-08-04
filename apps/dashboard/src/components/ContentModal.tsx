import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Send } from 'lucide-react';
import Modal from './Modal';
import { submitContent, createContent } from '../lib/api';

interface ContentModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ContentModal({ isOpen, onClose }: ContentModalProps) {
  const [title, setTitle] = useState('');
  const [objective, setObjective] = useState('');
  const [channel, setChannel] = useState('twitter');
  const [body, setBody] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const queryClient = useQueryClient();

  const submitMutation = useMutation({
    mutationFn: (contentId: string) => submitContent(contentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content'] });
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
      onClose();
      resetForm();
    },
  });

  const createContentMutation = useMutation({
    mutationFn: (data: any) => createContent(data),
    onSuccess: (response) => {
      // Automatically submit for review
      submitMutation.mutate(response.id);
    },
  });

  const resetForm = () => {
    setTitle('');
    setObjective('');
    setChannel('twitter');
    setBody('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !objective.trim()) return;

    setIsSubmitting(true);
    try {
      await createContentMutation.mutate({
        title: title.trim(),
        objective: objective.trim(),
        channel,
        body: body.trim(),
        target_audience: 'general',
        format: 'post',
        cta: 'Learn more',
        author_agent: 'Human Operator',
        status: 'draft'
      });
    } catch (error) {
      console.error('Failed to create content:', error);
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create Content" size="lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Title
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Content title..."
            className="w-full px-4 py-3 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3] text-white placeholder-gray-500 focus:outline-none focus:border-accent transition-colors"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Channel
          </label>
          <select
            value={channel}
            onChange={(e) => setChannel(e.target.value)}
            className="w-full px-4 py-3 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3] text-white focus:outline-none focus:border-accent transition-colors"
          >
            <option value="twitter">Twitter/X</option>
            <option value="linkedin">LinkedIn</option>
            <option value="google">Google / SEO</option>
            <option value="blog">Blog</option>
            <option value="moltbook">Moltbook</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Objective
          </label>
          <textarea
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            placeholder="What's the goal of this content?"
            className="w-full px-4 py-3 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3] text-white placeholder-gray-500 focus:outline-none focus:border-accent transition-colors resize-none"
            rows={3}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Content Body
          </label>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Write your content here..."
            className="w-full px-4 py-3 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3] text-white placeholder-gray-500 focus:outline-none focus:border-accent transition-colors resize-none"
            rows={6}
          />
        </div>

        <div className="flex gap-3 pt-4">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 px-4 py-2 rounded-lg border border-[#3730a3] text-gray-300 hover:bg-[#3730a3]/30 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting || !title.trim() || !objective.trim()}
            className="flex-1 px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Creating...
              </>
            ) : (
              <>
                <Send size={18} />
                Create & Submit
              </>
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
}
