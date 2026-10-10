import React from 'react';
import { cn } from '@/utils/cn';

export interface SuggestionCardProps {
  children: React.ReactNode;
  className?: string;
}

export const SuggestionCard: React.FC<SuggestionCardProps> = ({
  children,
  className,
}) => (
  <div
    className={cn("bg-softPaper rounded-2xl border border-warm-mist p-6 shadow-subtle", className)}
  >
    {children}
  </div>
);