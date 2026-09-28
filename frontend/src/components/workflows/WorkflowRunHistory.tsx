import React, { useState } from 'react';
import { WorkflowRun } from '../../types';
import { Button } from '../ui/Button';
import { CheckCircle2, Clock, XCircle, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { workflowApi } from '../../services/workflowApi';

interface WorkflowRunHistoryProps {
  runs: WorkflowRun[];
  onCancelRun?: (runId: string) => void;
}

export const WorkflowRunHistory: React.FC<WorkflowRunHistoryProps> = ({
  runs,
  onCancelRun,
}) => {
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);

  if (!runs || runs.length === 0) {
    return (
      <div className="p-6 text-center text-xs text-slate-500 rounded-lg border border-dashed border-slate-800 bg-slate-900/30">
        No execution runs recorded for this workflow yet.
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'COMPLETED':
        return (
          <span className="flex items-center gap-1 text-emerald-400 font-mono text-xs">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>COMPLETED</span>
          </span>
        );
      case 'PAUSED':
        return (
          <span className="flex items-center gap-1 text-amber-400 font-mono text-xs animate-pulse">
            <Clock className="w-3.5 h-3.5" />
            <span>PAUSED (APPROVAL)</span>
          </span>
        );
      case 'FAILED':
        return (
          <span className="flex items-center gap-1 text-rose-400 font-mono text-xs">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>FAILED</span>
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="flex items-center gap-1 text-slate-500 font-mono text-xs">
            <XCircle className="w-3.5 h-3.5" />
            <span>CANCELLED</span>
          </span>
        );
      case 'RUNNING':
      default:
        return (
          <span className="flex items-center gap-1 text-cyan-400 font-mono text-xs">
            <Clock className="w-3.5 h-3.5 animate-spin" />
            <span>RUNNING</span>
          </span>
        );
    }
  };

  const calculateDuration = (started: string, finished?: string) => {
    if (!finished) return 'Running';
    const s = new Date(started).getTime();
    const f = new Date(finished).getTime();
    const diff = f - s;
    if (diff < 1000) return `${diff}ms`;
    return `${(diff / 1000).toFixed(1)}s`;
  };

  return (
    <div className="space-y-3 text-xs">
      <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
        Workflow Run History ({runs.length})
      </div>

      <div className="space-y-2">
        {runs.map((run) => {
          const isExpanded = expandedRunId === run.id;
          const stepHistory = run.output_payload?.steps || [];

          return (
            <div
              key={run.id}
              className="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden"
            >
              <div
                className="p-3.5 flex items-center justify-between hover:bg-slate-800/40 transition-colors cursor-pointer"
                onClick={() => setExpandedRunId(isExpanded ? null : run.id)}
              >
                <div className="flex items-center gap-3">
                  {getStatusBadge(run.status)}
                  <span className="font-mono text-slate-400 text-[11px] truncate max-w-[140px]">
                    Run: {run.id.slice(0, 8)}...
                  </span>
                  <span className="text-slate-500 text-[11px]">
                    Step: {run.current_step || '1'}
                  </span>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right text-[11px] font-mono text-slate-400 hidden sm:block">
                    <span>Duration: {calculateDuration(run.started_at, run.finished_at)}</span>
                    <span className="text-slate-600 block text-[10px]">
                      {new Date(run.started_at).toLocaleTimeString()}
                    </span>
                  </div>

                  {run.status === 'RUNNING' && onCancelRun && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-6 text-[10px] text-rose-400 border-rose-900/40 hover:bg-rose-950/40"
                      onClick={(e) => {
                        e.stopPropagation();
                        onCancelRun(run.id);
                      }}
                    >
                      Cancel
                    </Button>
                  )}

                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  )}
                </div>
              </div>

              {isExpanded && (
                <div className="p-3.5 border-t border-slate-800 bg-slate-950/70 space-y-2.5 font-mono text-[11px]">
                  <div className="text-slate-400 font-semibold uppercase text-[10px] tracking-wider">
                    Step Progression
                  </div>

                  {stepHistory.length === 0 ? (
                    <div className="text-slate-500 italic text-[11px]">
                      No individual step trace records saved for this run.
                    </div>
                  ) : (
                    <div className="space-y-1.5">
                      {stepHistory.map((step, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-2 rounded bg-slate-900/60 border border-slate-800/60"
                        >
                          <div className="flex items-center gap-2">
                            <span className="w-4 h-4 rounded-full bg-slate-800 flex items-center justify-center text-[10px] font-bold text-slate-300">
                              {step.step_index || idx + 1}
                            </span>
                            <span className="capitalize text-slate-200">
                              {step.name || step.step_type}
                            </span>
                          </div>

                          <div className="flex items-center gap-3">
                            {step.duration_ms !== undefined && (
                              <span className="text-slate-500 text-[10px]">{step.duration_ms}ms</span>
                            )}
                            <span
                              className={`text-[10px] font-bold uppercase ${
                                step.status === 'COMPLETED'
                                  ? 'text-emerald-400'
                                  : step.status === 'PAUSED'
                                  ? 'text-amber-400'
                                  : 'text-rose-400'
                              }`}
                            >
                              {step.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {run.error_details && (
                    <div className="p-2.5 rounded bg-rose-950/40 border border-rose-900/50 text-rose-300 text-[11px]">
                      <span className="font-bold block">Error:</span>
                      {run.error_details}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
