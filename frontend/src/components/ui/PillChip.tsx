import React from 'react';
import { cn } from '@/utils/cn';

export interface PillChipProps {
  children: React.ReactNode;
  variant?: 'default' | 'active';
  size?: 'sm' | 'md';
}

export const PillChip: React.FC<PillChipProps> = ({
  children,
  variant = 'default',
  size = 'md',
}) => {
  const base = "inline-flex items-center gap-1.5 rounded-full transition-colors";
  const sizes = {
    sm: "px-3 py-2 text-xs",
    md: "px-4 py-2 text-xs",
  };
  const variants = {
    default: "text-graphite border-warm-mist/30 hover:border-warm-mist",
    active: "text-brand-accent bg-brand-accent/10 border-brand-accent/20",
  };

  return (
    <span className={cn(base, variants[variant], sizes[size])}>
      {children}
    </span>
  );
};