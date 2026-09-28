import React from 'react';
import { Workflow } from '../../types';
import { Button } from '../ui/Button';
import { Play, Trash2, Edit3, CheckCircle2, XCircle, Clock } from 'lucide-react';

interface WorkflowListProps {
  workflows: Workflow[];
  onSelect: (workflow: Workflow) => void;
  onRun: (workflow: Workflow) => void;
  onDelete: (workflowId: string) => void;
}

export const WorkflowList: React.FC<WorkflowListProps> = ({
  workflows,
  onSelect,
  onRun,
  onDelete,
}) => {
  if (!workflows || workflows.length === 0) {
    return (
      <div className="p-8 text-center rounded-lg border border-dashed border-slate-800 bg-slate-900/40 text-slate-400 text-sm">
        No enterprise workflows created yet. Create a new automation workflow above.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-900">
      <table className="w-full text-left text-xs text-slate-300">
        <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
          <tr>
            <th className="px-4 py-3">Name</th>
            <th className="px-4 py-3">Trigger</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Steps</th>
            <th className="px-4 py-3">Created</th>
            <th className="px-4 py-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60 font-mono">
          {workflows.map((wf) => {
            const stepsCount = wf.graph_definition?.steps?.length || 0;
            return (
              <tr key={wf.id} className="hover:bg-slate-800/40 transition-colors">
                <td className="px-4 py-3 font-semibold text-slate-100 font-sans">
                  <button
                    onClick={() => onSelect(wf)}
                    className="hover:text-cyan-400 transition-colors text-left"
                  >
                    {wf.name}
                  </button>
                  {wf.description && (
                    <p className="text-[11px] text-slate-400 font-normal line-clamp-1">
                      {wf.description}
                    </p>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono text-[11px]">
                    {wf.trigger_type}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {wf.is_active ? (
                    <span className="flex items-center gap-1.5 text-emerald-400 font-sans font-medium">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Active
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5 text-slate-500 font-sans font-medium">
                      <XCircle className="w-3.5 h-3.5" />
                      Disabled
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-slate-400 font-sans">
                  {stepsCount} step{stepsCount !== 1 ? 's' : ''}
                </td>
                <td className="px-4 py-3 text-slate-500 text-[11px]">
                  {new Date(wf.created_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-3 text-right font-sans">
                  <div className="flex items-center justify-end gap-1.5">
                    <Button
                      size="sm"
                      className="bg-cyan-600 hover:bg-cyan-500 text-white h-7 px-2.5 text-xs flex items-center gap-1"
                      onClick={() => onRun(wf)}
                    >
                      <Play className="w-3 h-3" />
                      Run
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 px-2 text-xs"
                      onClick={() => onSelect(wf)}
                    >
                      <Edit3 className="w-3 h-3" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 px-2 text-xs text-rose-400 border-rose-900/50 hover:bg-rose-950/40"
                      onClick={() => onDelete(wf.id)}
                    >
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
