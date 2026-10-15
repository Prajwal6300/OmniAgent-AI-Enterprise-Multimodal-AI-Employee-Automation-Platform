import React from 'react';
import { cn } from '@/utils/cn';

export interface FilledActionButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
}

export const FilledActionButton: React.FC<FilledActionButtonProps> = ({
  children,
  className,
  variant = 'primary',
  size = 'md',
  ...props
}) => {
  const base = "inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none";
  const sizes = {
    sm: "px-3 py-1.5",
    md: "px-4 py-2",
    lg: "px-6 py-3",
  };
  const variants = {
    primary: "bg-brand-accent text-white hover:bg-brand-accent/90 focus:ring-brand-accent",
    secondary: "bg-transparent text-slate-800 border border-warm-mist hover:bg-warm-mist/40 focus:ring-warm-mist",
    ghost: "bg-transparent text-slate-700 hover:bg-warm-mist/40 focus:ring-warm-mist",
    outline: "bg-transparent text-slate-800 border border-warm-mist hover:bg-warm-mist/40 focus:ring-warm-mist",
  };

  return (
    <button className={cn(base, variants[variant], sizes[size], className)} {...props}>
      {children}
    </button>
  );
};
