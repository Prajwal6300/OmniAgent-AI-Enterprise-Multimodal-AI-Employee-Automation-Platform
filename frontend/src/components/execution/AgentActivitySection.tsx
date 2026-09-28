import React, { useState } from 'react';
import { ExecutionStepItem } from '../../types';
import { Bot, CheckCircle2, Clock, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';

interface AgentActivitySectionProps {
  steps: ExecutionStepItem[];
  agentsUsed?: string[];
  status?: string;
}

export const AgentActivitySection: React.FC<AgentActivitySectionProps> = ({
  steps,
  agentsUsed = [],
  status = 'COMPLETED',
}) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!steps || steps.length === 0) return null;

  const getStatusBadge = (stepStatus: string) => {
    switch (stepStatus.toUpperCase()) {
      case 'COMPLETED':
        return (
          <span className="flex items-center gap-1 text-emerald-400 font-mono text-xs">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>✓</span>
          </span>
        );
      case 'PAUSED':
        return (
          <span className="flex items-center gap-1 text-amber-400 font-mono text-xs animate-pulse">
            <Clock className="w-3.5 h-3.5" />
            <span>⏸</span>
          </span>
        );
      case 'FAILED':
        return (
          <span className="flex items-center gap-1 text-rose-400 font-mono text-xs">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>✗</span>
          </span>
        );
      case 'RUNNING':
      case 'STARTED':
      default:
        return (
          <span className="flex items-center gap-1 text-cyan-400 font-mono text-xs animate-spin">
            <Clock className="w-3.5 h-3.5" />
            <span>⏳</span>
          </span>
        );
    }
  };

  return (
    <div className="rounded-lg bg-slate-950/70 border border-slate-800 text-xs overflow-hidden">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3.5 py-2.5 flex items-center justify-between hover:bg-slate-900/60 transition-colors text-slate-300"
      >
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-cyan-400" />
          <span className="font-semibold text-slate-200">Orchestration Trace</span>
          <span className="text-slate-500 font-mono">
            ({steps.length} step{steps.length !== 1 ? 's' : ''})
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Summary inline preview of agents */}
          <div className="hidden sm:flex items-center gap-2 font-mono text-[11px]">
            {steps.slice(-3).map((st, i) => (
              <span key={i} className="flex items-center gap-1 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                <span className="text-slate-300 capitalize">{st.agent.replace('_agent', '')}</span>
                {getStatusBadge(st.status)}
              </span>
            ))}
          </div>

          {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </div>
      </button>

      {isOpen && (
        <div className="p-3.5 border-t border-slate-800/80 space-y-2 bg-slate-950">
          <div className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold mb-2">
            Execution Log (Safe Telemetry)
          </div>
          <div className="space-y-1.5 font-mono text-[11px]">
            {steps.map((st, idx) => (
              <div
                key={idx}
                className="flex items-start justify-between p-2 rounded bg-slate-900/50 border border-slate-800/60"
              >
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-200 capitalize">
                      {st.agent.replace('_agent', ' Agent')}
                    </span>
                    <span className="text-slate-500 text-[10px]">{st.action}</span>
                  </div>
                  {st.output_summary && (
                    <p className="text-slate-400 text-[10px] line-clamp-1">{st.output_summary}</p>
                  )}
                </div>

                <div className="flex items-center gap-2 shrink-0 ml-3">
                  {st.duration_ms !== undefined && st.duration_ms !== null && (
                    <span className="text-slate-500 text-[10px]">{st.duration_ms}ms</span>
                  )}
                  {getStatusBadge(st.status)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
