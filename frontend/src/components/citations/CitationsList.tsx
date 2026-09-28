import React from 'react';
import { CitationItem } from '../../types';
import { FileText, ExternalLink } from 'lucide-react';

interface CitationsListProps {
  citations: CitationItem[];
}

export const CitationsList: React.FC<CitationsListProps> = ({ citations }) => {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="space-y-2 pt-2 border-t border-slate-800">
      <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
        <FileText className="w-3.5 h-3.5 text-cyan-400" />
        <span>Verified Citations ({citations.length})</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {citations.map((c, idx) => (
          <div
            key={idx}
            className="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-slate-700 transition-colors text-xs"
          >
            <span className="text-sm">📄</span>
            <div className="space-y-0.5 min-w-0">
              <div className="font-medium text-slate-200 truncate">
                {c.document_name || 'Enterprise Document'}
              </div>
              <div className="text-slate-400 text-[11px]">
                {c.page_number ? `Page ${c.page_number}` : 'Full Artifact'}
                {c.section ? ` • ${c.section}` : ''}
              </div>
              {c.relevance_score !== undefined && c.relevance_score !== null && (
                <div className="text-cyan-400 text-[10px]">
                  Match: {(c.relevance_score * 100).toFixed(0)}%
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
