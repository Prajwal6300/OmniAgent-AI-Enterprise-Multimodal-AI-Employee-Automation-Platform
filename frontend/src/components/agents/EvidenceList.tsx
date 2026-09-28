import React, { useState } from 'react';
import { EvidenceItem } from '../../types';
import { Layers, ChevronDown, ChevronUp, Database, Eye, FileText, BookOpen } from 'lucide-react';

interface EvidenceListProps {
  evidence: EvidenceItem[];
}

export const EvidenceList: React.FC<EvidenceListProps> = ({ evidence }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!evidence || evidence.length === 0) return null;

  const getSourceIcon = (sourceType: string) => {
    switch (sourceType.toLowerCase()) {
      case 'database':
        return <Database className="w-3.5 h-3.5 text-emerald-400" />;
      case 'vision':
        return <Eye className="w-3.5 h-3.5 text-purple-400" />;
      case 'rag':
        return <BookOpen className="w-3.5 h-3.5 text-cyan-400" />;
      case 'document':
      default:
        return <FileText className="w-3.5 h-3.5 text-blue-400" />;
    }
  };

  const displayedEvidence = isExpanded ? evidence : evidence.slice(0, 2);

  return (
    <div className="space-y-2 pt-2 border-t border-slate-800">
      <div className="flex items-center justify-between">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-indigo-400" />
          <span>Evidence Collected ({evidence.length})</span>
        </div>
        {evidence.length > 2 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            {isExpanded ? (
              <>
                <span>Show Less</span>
                <ChevronUp className="w-3 h-3" />
              </>
            ) : (
              <>
                <span>Show All ({evidence.length})</span>
                <ChevronDown className="w-3 h-3" />
              </>
            )}
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {displayedEvidence.map((ev, idx) => (
          <div
            key={idx}
            className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs space-y-1.5"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 font-medium text-slate-200">
                {getSourceIcon(ev.source_type)}
                <span className="uppercase tracking-wider text-[11px] text-indigo-400 font-mono">
                  [{ev.source_type}]
                </span>
                <span className="truncate max-w-[160px]">{ev.source_name || 'Source'}</span>
              </div>
              {ev.confidence !== undefined && ev.confidence !== null && (
                <span className="text-[10px] text-slate-500">
                  {(ev.confidence * 100).toFixed(0)}% conf
                </span>
              )}
            </div>

            <p className="text-slate-300 leading-relaxed text-[12px] line-clamp-3">
              {ev.content}
            </p>

            {ev.page_number && (
              <div className="text-[10px] text-slate-500 font-mono">
                Page: {ev.page_number}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
