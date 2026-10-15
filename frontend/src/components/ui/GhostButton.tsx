import React from 'react';
import { cn } from '@/utils/cn';

export interface GhostButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default';
  size?: 'sm' | 'md' | 'lg';
}

export const GhostButton: React.FC<GhostButtonProps> = ({
  children,
  className,
  variant = 'default',
  size = 'md',
  ...props
}) => {
  const base = "inline-flex items-center justify-center rounded-lg text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2";
  const sizes = {
    sm: "px-3 py-1.5",
    md: "px-4 py-2",
    lg: "px-6 py-3",
  };
  const variants = {
    default: "border border-warm-mist text-ink hover:bg-warm-mist/20 focus:ring-warm-mist",
  };

  return (
    <button
      className={cn(base, variants[variant], sizes[size], className)}
      {...props}
    >
      {children}
    </button>
  );
};