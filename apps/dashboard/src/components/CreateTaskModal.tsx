import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Sparkles, Target, FileText, Shield, Zap, Users, Search } from 'lucide-react';
import Modal from './Modal';
import { api, cn, createCampaign } from '../lib/api';

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const taskTypes = [
  { 
    id: 'campaign', 
    name: 'Create Campaign', 
    description: 'Launch a new marketing campaign with the Growth Orchestrator',
    icon: Target,
    color: 'text-accent',
    bgColor: 'bg-accent/10'
  },
  { 
    id: 'content_strategy', 
    name: 'Content Strategy', 
    description: 'Generate weekly content plan and strategy',
    icon: FileText,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10'
  },
  { 
    id: 'compliance', 
    name: 'Compliance Check', 
    description: 'Run compliance and brand safety checks',
    icon: Shield,
    color: 'text-green-400',
    bgColor: 'bg-green-500/10'
  },
  { 
    id: 'intelligence', 
    name: 'Market Intelligence', 
    description: 'Gather market intelligence and trends',
    icon: Search,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10'
  },
];

export default function CreateTaskModal({ isOpen, onClose }: CreateTaskModalProps) {
  const [selectedTask, setSelectedTask] = useState<string | null>(null);
  const [objective, setObjective] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const queryClient = useQueryClient();

  const createCampaignMutation = useMutation({
    mutationFn: (data: { objective: string }) => createCampaign(data.objective),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      onClose();
      setObjective('');
      setSelectedTask(null);
    },
  });

  const createTaskMutation = useMutation({
    mutationFn: (data: { task_type: string; input_data: any }) => 
      api.post('/tasks', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      onClose();
      setObjective('');
      setSelectedTask(null);
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTask || !objective.trim()) return;

    setIsSubmitting(true);
    try {
      if (selectedTask === 'campaign') {
        await createCampaignMutation.mutate({ objective: objective.trim() });
      } else {
        // Map task types to agent names
        const taskTypeMap: Record<string, string> = {
          'content_strategy': 'Content Strategy',
          'compliance': 'Compliance & Brand',
          'intelligence': 'Market Intelligence'
        };
        
        const taskType = taskTypeMap[selectedTask];
        if (taskType) {
          await createTaskMutation.mutate({
            task_type: taskType,
            input_data: { objective: objective.trim() }
          });
        }
      }
    } catch (error) {
      console.error('Failed to create task:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create New Task" size="lg">
      <div className="space-y-6">
        {/* Task Type Selection */}
        {!selectedTask ? (
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Sparkles size={20} className="text-accent" />
              Select Task Type
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {taskTypes.map((task) => (
                <button
                  key={task.id}
                  onClick={() => setSelectedTask(task.id)}
                  className={cn(
                    "p-4 rounded-xl border border-[#3730a3]/50 hover:border-accent/50",
                    "transition-all duration-200 text-left group",
                    "hover:bg-[#3730a3]/30"
                  )}
                >
                  <div className="flex items-start gap-3">
                    <div className={cn("p-2 rounded-lg", task.bgColor, task.color)}>
                      <task.icon size={20} />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-white group-hover:text-accent transition-colors">
                        {task.name}
                      </h4>
                      <p className="text-sm text-gray-400 mt-1">{task.description}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <button
              type="button"
              onClick={() => setSelectedTask(null)}
              className="text-sm text-gray-400 hover:text-white transition-colors flex items-center gap-1"
            >
              ← Back to task types
            </button>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Task Objective
              </label>
              <textarea
                value={objective}
                onChange={(e) => setObjective(e.target.value)}
                placeholder="Describe what you want to accomplish..."
                className="w-full px-4 py-3 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3] text-white placeholder-gray-500 focus:outline-none focus:border-accent transition-colors resize-none"
                rows={4}
                required
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
                disabled={isSubmitting || !objective.trim()}
                className="flex-1 px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Creating...
                  </>
                ) : (
                  <>
                    <Plus size={18} />
                    Create Task
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </Modal>
  );
}
