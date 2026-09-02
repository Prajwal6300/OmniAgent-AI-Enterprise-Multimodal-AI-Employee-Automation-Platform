import React from 'react';
import { cn } from '@/utils/cn';

export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, children, ...props }) => (
  <div className={cn("bg-slate-900 border border-slate-800 rounded-xl shadow-sm p-6", className)} {...props}>
    {children}
  </div>
);
