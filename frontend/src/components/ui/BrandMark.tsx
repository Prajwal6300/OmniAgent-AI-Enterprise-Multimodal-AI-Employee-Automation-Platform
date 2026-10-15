import React from 'react';
import { cn } from '@/utils/cn';
import { Link } from 'react-router-dom';

export const BrandMark: React.FC<{ className?: string; to?: string }> = ({
  className,
  to,
}) => {
  return (
    <Link
      to={to || '/'}
      className={cn(
        "w-8 h-8 rounded-lg bg-brand-accent flex items-center justify-center font-bold text-white",
        className
      )}
    >
      Ω
    </Link>
  );
};