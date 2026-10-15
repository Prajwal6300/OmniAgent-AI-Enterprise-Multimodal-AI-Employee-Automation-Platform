import React from 'react';
import { cn } from '@/utils/cn';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
}

export const Button: React.FC<ButtonProps> = ({
  children,
  className,
  variant = 'primary',
  size = 'md',
  ...props
}) => {
  const base = "inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none";
  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
  };
  const variants = {
    primary: "bg-brand-accent hover:bg-brand-accent/90 text-white focus:ring-brand-accent",
    secondary: "bg-transparent border border-warm-mist text-ink hover:bg-warm-mist/20 focus:ring-warm-mist",
    outline: "border border-warm-mist text-ink hover:bg-softPaper/30 focus:ring-warm-mist",
    ghost: "border-transparent text-ink hover:bg-warm-mist/20 focus:ring-warm-mist",
  };

  return (
    <button className={cn(base, variants[variant], sizes[size], className)} {...props}>
      {children}
    </button>
  );
};
