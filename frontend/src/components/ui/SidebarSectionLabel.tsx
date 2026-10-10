import React from 'react';

export const SidebarSectionLabel: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => (
  <span className="text-slate-500 text-xs uppercase tracking-wider font-medium">
    {children}
  </span>
);