import React from 'react';
import { cn } from '@/utils/cn';
import { Link } from 'react-router-dom';

export interface SidebarNavItemProps {
  name: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  isActive: boolean;
  onClick?: () => void;
}

export const SidebarNavItem: React.FC<SidebarNavItemProps> = ({
  name,
  path,
  icon: Icon,
  isActive,
  onClick,
}) => {
  const base = 'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors';
  const active = 'bg-brand-accent/10 text-brand-accent font-medium border border-brand-accent/30';
  const inactive = 'text-graphite hover:text-ink hover:bg-softPaper/50';

  return (
    <Link
      to={path}
      className={cn(base, isActive ? active : inactive)}
      onClick={onClick}
    >
      <Icon className="w-4 h-4" />
      <span>{name}</span>
    </Link>
  );
};
