import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { cn } from '../lib/api';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export default function Modal({ isOpen, onClose, title, children, size = 'md' }: ModalProps) {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl'
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className={cn(
        "relative bg-[#1e1b4b] border border-[#3730a3] rounded-2xl shadow-2xl w-full",
        "transform transition-all duration-300 scale-100 opacity-100",
        sizeClasses[size]
      )}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[#3730a3]">
          <h2 className="text-xl font-semibold gradient-text">{title}</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-[#3730a3] transition-colors"
          >
            <X size={20} className="text-gray-400" />
          </button>
        </div>
        
        {/* Content */}
        <div className="p-6 max-h-[70vh] overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );
}
