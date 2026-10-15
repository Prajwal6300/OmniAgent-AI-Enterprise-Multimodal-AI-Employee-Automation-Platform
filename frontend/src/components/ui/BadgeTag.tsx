import React from 'react';
import { cn } from '@/utils/cn';

export const BadgeTag: React.FC<React.HTMLAttributes<HTMLSpanElement>> = ({
  children,
  className,
}) => (
  <span
    className={cn(
      "bg-brand-accent text-white rounded-full text-xs font-medium capitalize py-1 px-2 transition-colors",
      className
    )}
  >
    {children}
  </span>
);