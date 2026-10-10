import React from 'react';
import { cn } from '@/utils/cn';

export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, children, ...props }) => (
  <div className={cn("bg-parchment rounded-2xl border border-warm-mist p-6 shadow-subtle transition-shadow hover:shadow-none", className)} {...props}>
    {children}
  </div>
);
