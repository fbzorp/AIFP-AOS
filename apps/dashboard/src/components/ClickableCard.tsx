import { React, ReactNode } from 'react';
import { cn } from '../lib/api';

interface ClickableCardProps {
  children: ReactNode;
  onClick?: () => void;
  className?: string;
  hover?: boolean;
  active?: boolean;
  disabled?: boolean;
}

export default function ClickableCard({
  children,
  onClick,
  className,
  hover = true,
  active = false,
  disabled = false,
}: ClickableCardProps) {
  return (
    <div
      onClick={disabled ? undefined : onClick}
      className={cn(
        'p-4 rounded-xl border transition-all duration-200',
        'bg-[#1e1b4b]/50 border-[#3730a3]/50',
        hover && !disabled && 'card-clickable cursor-pointer',
        active && 'border-accent bg-accent/10',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
    >
      {children}
    </div>
  );
}
