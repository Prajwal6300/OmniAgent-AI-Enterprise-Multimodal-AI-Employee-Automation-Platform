import React from 'react';
import { cn } from '@/utils/cn';

export interface SearchInputProps {
  placeholder?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => void;
  onKeyDown?: (e: React.KeyboardEvent) => void;
  rows?: number;
  type?: HTMLTextAreaElement['type'];
  className?: string;
}

export const SearchInput: React.FC<SearchInputProps> = ({
  placeholder = 'Ask a question, query business database, request document analysis, or trigger an authorized action...',
  value,
  onChange,
  onKeyDown,
  rows = 3,
  className,
}) => {
  const textareaClass = cn(
    "w-full rounded-lg bg-parchment border border-warm-mist px-4 py-3 text-ink placeholder-slate-400 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-accent focus:border-transparent resize-none",
    className
  );

  return (
    <div className="relative">
      <textarea
        value={value ?? ''}
        onChange={onChange}
        placeholder={placeholder}
        rows={rows}
        className={textareaClass}
        onKeyDown={onKeyDown}
      />
    </div>
  );
};
