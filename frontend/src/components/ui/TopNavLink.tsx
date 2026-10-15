import React from 'react';
import { cn } from '@/utils/cn';

export const TopNavLink: React.FC<{ name: string; path: string; isActive?: boolean }> = ({
  name,
  path,
  isActive = false,
}) => {
  const base = 'text-graphite hover:text-ink cursor-pointer';
  const active = 'text-ink font-medium';

  return (
    <span className={cn(isActive ? active : base)}>
      {name}
    </span>
  );
};
