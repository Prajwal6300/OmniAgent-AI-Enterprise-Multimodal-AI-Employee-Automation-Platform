import React from 'react';
import { cn } from '@/utils/cn';

export const BrandMark: React.FC<{ className?: string }> = ({
  className,
}) => (
  <div
    className={cn(
      "w-8 h-8 rounded-lg bg-brand-accent flex items-center justify-center font-bold text-white",
      className
    )}
  >
    Ω
  </div>
);
