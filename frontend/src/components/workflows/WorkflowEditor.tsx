import React, { useState } from 'react';
import { Workflow, WorkflowDefinition, WorkflowStep } from '../../types';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Plus, Trash2, ArrowDown, Bot, Scale, ShieldAlert, Zap, Check } from 'lucide-react';

interface WorkflowEditorProps {
  initialWorkflow?: Workflow | null;
  onSave: (data: {
    name: string;
    description: string;
    trigger_type: string;
    trigger_config: Record<string, any>;
    graph_definition: WorkflowDefinition;
    is_active: boolean;
  }) => Promise<void>;
  onCancel: () => void;
}

export const WorkflowEditor: React.FC<WorkflowEditorProps> = ({
  initialWorkflow,
  onSave,
  onCancel,
}) => {
  const [name, setName] = useState(initialWorkflow?.name || '');
  const [description, setDescription] = useState(initialWorkflow?.description || '');
  const [triggerType, setTriggerType] = useState(initialWorkflow?.trigger_type || 'MANUAL');
  const [isActive, setIsActive] = useState(initialWorkflow ? initialWorkflow.is_active : true);
  const [steps, setSteps] = useState<WorkflowStep[]>(
    initialWorkflow?.graph_definition?.steps || [
      { type: 'agent', agent: 'vision_agent', prompt: 'Analyze component image' },
      { type: 'agent', agent: 'database_agent', prompt: 'Check failure history' },
      { type: 'condition', field: 'database_agent.row_count', operator: '>', value: 0 },
      { type: 'approval', required: true },
      { type: 'action', action: 'create_ticket' },
    ]
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addStep = (type: 'agent' | 'condition' | 'approval' | 'action') => {
    if (type === 'agent') {
      setSteps([...steps, { type: 'agent', agent: 'reasoning_agent', prompt: 'Synthesize evidence' }]);
    } else if (type === 'condition') {
      setSteps([...steps, { type: 'condition', field: 'confidence', operator: '>=', value: 0.8 }]);
    } else if (type === 'approval') {
      setSteps([...steps, { type: 'approval', required: true }]);
    } else {
      setSteps([...steps, { type: 'action', action: 'send_notification' }]);
    }
  };

  const removeStep = (index: number) => {
    setSteps(steps.filter((_, i) => i !== index));
  };

  const updateStep = (index: number, updated: Partial<WorkflowStep>) => {
    setSteps(steps.map((st, i) => (i === index ? { ...st, ...updated } : st)));
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Workflow name is required.');
      return;
    }
    setError(null);
    setIsSubmitting(true);

    try {
      const defn: WorkflowDefinition = {
        name,
        trigger: { type: triggerType as any },
        steps,
      };
      await onSave({
        name,
        description,
        trigger_type: triggerType,
        trigger_config: {},
        graph_definition: defn,
        is_active: isActive,
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to save workflow.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="p-6 bg-slate-900 border-slate-800 space-y-6 text-xs">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <h3 className="text-base font-semibold text-slate-100">
          {initialWorkflow ? 'Edit Workflow' : 'Create Enterprise Automation Workflow'}
        </h3>
        <span className="text-slate-400 font-mono text-[11px]">DAG Definition Editor</span>
      </div>

      <form onSubmit={handleFormSubmit} className="space-y-4">
        {error && (
          <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-900 text-rose-300">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="font-medium text-slate-300">Workflow Name *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Machine Issue Detection & Escalation"
              className="w-full px-3 py-2 rounded bg-slate-950 border border-slate-700 text-slate-100 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            />
          </div>

          <div className="space-y-1">
            <label className="font-medium text-slate-300">Trigger Type</label>
            <select
              value={triggerType}
              onChange={(e) => setTriggerType(e.target.value)}
              className="w-full px-3 py-2 rounded bg-slate-950 border border-slate-700 text-slate-100 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            >
              <option value="MANUAL">MANUAL (On Demand)</option>
              <option value="EVENT">EVENT (Data / File Change)</option>
              <option value="SCHEDULE">SCHEDULE (Periodic Cron)</option>
            </select>
          </div>
        </div>

        <div className="space-y-1">
          <label className="font-medium text-slate-300">Description</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Operational purpose of this workflow..."
            className="w-full px-3 py-2 rounded bg-slate-950 border border-slate-700 text-slate-100 focus:outline-none focus:ring-1 focus:ring-cyan-500"
          />
        </div>

        {/* Workflow Steps Sequence */}
        <div className="space-y-3 pt-3 border-t border-slate-800">
          <div className="flex items-center justify-between">
            <label className="font-semibold text-slate-200 uppercase tracking-wider text-[11px]">
              Execution Steps ({steps.length})
            </label>
            <div className="flex items-center gap-1.5">
              <Button
                type="button"
                size="sm"
                variant="outline"
                className="h-7 px-2 text-[11px] flex items-center gap-1"
                onClick={() => addStep('agent')}
              >
                <Bot className="w-3 h-3 text-cyan-400" />
                + Agent
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                className="h-7 px-2 text-[11px] flex items-center gap-1"
                onClick={() => addStep('condition')}
              >
                <Scale className="w-3 h-3 text-amber-400" />
                + Condition
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                className="h-7 px-2 text-[11px] flex items-center gap-1"
                onClick={() => addStep('approval')}
              >
                <ShieldAlert className="w-3 h-3 text-rose-400" />
                + Approval
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                className="h-7 px-2 text-[11px] flex items-center gap-1"
                onClick={() => addStep('action')}
              >
                <Zap className="w-3 h-3 text-emerald-400" />
                + Action
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            {steps.map((step, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between gap-3 font-mono"
              >
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center font-bold text-slate-300 text-xs">
                    {idx + 1}
                  </span>

                  {step.type === 'agent' && (
                    <div className="flex items-center gap-2">
                      <span className="text-cyan-400 font-semibold uppercase text-[11px]">Agent:</span>
                      <select
                        value={step.agent}
                        onChange={(e) => updateStep(idx, { agent: e.target.value })}
                        className="px-2 py-1 rounded bg-slate-900 border border-slate-700 text-slate-200 text-xs"
                      >
                        <option value="vision_agent">vision_agent</option>
                        <option value="database_agent">database_agent</option>
                        <option value="reasoning_agent">reasoning_agent</option>
                        <option value="rag_agent">rag_agent</option>
                        <option value="document_agent">document_agent</option>
                        <option value="action_agent">action_agent</option>
                      </select>
                    </div>
                  )}

                  {step.type === 'condition' && (
                    <div className="flex items-center gap-2">
                      <span className="text-amber-400 font-semibold uppercase text-[11px]">If:</span>
                      <input
                        type="text"
                        value={step.field || ''}
                        onChange={(e) => updateStep(idx, { field: e.target.value })}
                        placeholder="field (e.g. database_agent.row_count)"
                        className="px-2 py-1 rounded bg-slate-900 border border-slate-700 text-slate-200 text-xs w-44"
                      />
                      <select
                        value={step.operator}
                        onChange={(e) => updateStep(idx, { operator: e.target.value })}
                        className="px-2 py-1 rounded bg-slate-900 border border-slate-700 text-slate-200 text-xs"
                      >
                        <option value="==">==</option>
                        <option value="!=">!=</option>
                        <option value=">">&gt;</option>
                        <option value="<">&lt;</option>
                        <option value=">=">&gt;=</option>
                        <option value="<=">&lt;=</option>
                        <option value="contains">contains</option>
                        <option value="exists">exists</option>
                      </select>
                      <input
                        type="text"
                        value={step.value !== undefined ? String(step.value) : ''}
                        onChange={(e) => updateStep(idx, { value: e.target.value })}
                        placeholder="expected value"
                        className="px-2 py-1 rounded bg-slate-900 border border-slate-700 text-slate-200 text-xs w-28"
                      />
                    </div>
                  )}

                  {step.type === 'approval' && (
                    <div className="flex items-center gap-2">
                      <span className="text-rose-400 font-semibold uppercase text-[11px]">Gate:</span>
                      <span className="text-slate-300">Mandatory Human Authorization Check</span>
                    </div>
                  )}

                  {step.type === 'action' && (
                    <div className="flex items-center gap-2">
                      <span className="text-emerald-400 font-semibold uppercase text-[11px]">Action:</span>
                      <select
                        value={step.action}
                        onChange={(e) => updateStep(idx, { action: e.target.value })}
                        className="px-2 py-1 rounded bg-slate-900 border border-slate-700 text-slate-200 text-xs"
                      >
                        <option value="create_ticket">create_ticket</option>
                        <option value="send_notification">send_notification</option>
                        <option value="send_email">send_email</option>
                        <option value="create_report">create_report</option>
                        <option value="run_agent">run_agent</option>
                      </select>
                    </div>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => removeStep(idx)}
                  className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
          <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            type="submit"
            className="bg-cyan-600 hover:bg-cyan-500 text-white flex items-center gap-1.5"
            disabled={isSubmitting}
          >
            <Check className="w-4 h-4" />
            {isSubmitting ? 'Saving...' : initialWorkflow ? 'Update Workflow' : 'Save Workflow'}
          </Button>
        </div>
      </form>
    </Card>
  );
};
