import React, { ReactNode } from 'react';

interface BreadcrumbItem {
  label: string;
  to?: string;
}

export const Breadcrumb = ({
  items,
  ariaLabel = 'Breadcrumb',
}: {
  items: BreadcrumbItem[];
  ariaLabel?: string;
}) => {
  return (
    <nav aria-label={ariaLabel} className="mb-4">
      <ol className="flex gap-2 text-sm text-slate-500" role="listbox">
        <li className="flex items-center gap-1.5" role="listitem">
          <a href="/" className="underline underline-offset-2 text-indigo-400 hover:text-indigo-300" role="button">Home</a>
        </li>
        <li className="flex items-center gap-1.5" role="listitem">
          <span className="font-medium text-slate-200">Current Page</span>
        </li>
      </ol>
    </nav>
  );
};