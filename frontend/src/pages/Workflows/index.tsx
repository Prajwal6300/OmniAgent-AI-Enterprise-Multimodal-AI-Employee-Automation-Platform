import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { FilledActionButton } from '@/components/ui/FilledActionButton';
import { workflowApi } from '@/services/workflowApi';
import { Workflow, WorkflowRun } from '@/types';
import { WorkflowList } from '@/components/workflows/WorkflowList';
import { WorkflowEditor } from '@/components/workflows/WorkflowEditor';
import { WorkflowRunHistory } from '@/components/workflows/WorkflowRunHistory';
import { Plus, RefreshCw, GitBranch, Play, AlertCircle } from 'lucide-react';

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [runningWorkflowId, setRunningWorkflowId] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchWorkflows = async () => {
    setLoading(true);
    try {
      const data = await workflowApi.listWorkflows();
      setWorkflows(data);
      if (data.length > 0 && !selectedWorkflow) {
        setSelectedWorkflow(data[0]);
        fetchRuns(data[0].id);
      }
    } catch (err: any) {
      console.error('Failed fetching workflows:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchRuns = async (workflowId: string) => {
    try {
      const runList = await workflowApi.listRuns(workflowId);
      setRuns(runList);
    } catch (err: any) {
      console.error('Failed fetching workflow runs:', err);
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const handleSelectWorkflow = (wf: Workflow) => {
    setSelectedWorkflow(wf);
    setIsEditing(false);
    fetchRuns(wf.id);
  };

  const handleRunWorkflow = async (wf: Workflow) => {
    setRunningWorkflowId(wf.id);
    setNotification(null);
    try {
      const newRun = await workflowApi.runWorkflow(wf.id);
      setNotification({
        type: 'success',
        message: `Workflow run started! Status: ${newRun.status}`,
      });
      fetchRuns(wf.id);
    } catch (err: any) {
      setNotification({
        type: 'error',
        message: err.response?.data?.detail || err.message || 'Failed to trigger workflow run.',
      });
    } finally {
      setRunningWorkflowId(null);
    }
  };

  const handleDeleteWorkflow = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this workflow?')) return;
    try {
      await workflowApi.deleteWorkflow(id);
      setNotification({ type: 'success', message: 'Workflow deleted successfully.' });
      if (selectedWorkflow?.id === id) {
        setSelectedWorkflow(null);
        setRuns([]);
      }
      fetchWorkflows();
    } catch (err: any) {
      setNotification({
        type: 'error',
        message: err.response?.data?.detail || err.message || 'Failed to delete workflow.',
      });
    }
  };

  const handleSaveWorkflow = async (data: any) => {
    if (selectedWorkflow && isEditing) {
      await workflowApi.updateWorkflow(selectedWorkflow.id, data);
      setNotification({ type: 'success', message: 'Workflow updated successfully.' });
    } else {
      await workflowApi.createWorkflow(data);
      setNotification({ type: 'success', message: 'Workflow created successfully.' });
    }
    setIsEditing(false);
    fetchWorkflows();
  };

  const handleCancelRun = async (runId: string) => {
    try {
      await workflowApi.cancelRun(runId);
      if (selectedWorkflow) {
        fetchRuns(selectedWorkflow.id);
      }
    } catch (err: any) {
      console.error('Cancel run error:', err);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto text-xs">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-ink">
              Enterprise Workflows & Automation
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-brand-accent/5 text-brand-accent/80 border border-brand-accent/20">
              Production DAG Runtime
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Build and monitor deterministic business automation pipelines combining specialized agents, conditional branches, human approvals, and verified operations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            className="flex items-center gap-1.5"
            onClick={fetchWorkflows}
            disabled={loading}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            size="sm"
            className="bg-brand-accent text-white flex items-center gap-1.5"
            onClick={() => {
              setSelectedWorkflow(null);
              setIsEditing(true);
            }}
          >
            <Plus className="w-4 h-4" />
            New Workflow
          </Button>
        </div>
      </div>

      {/* Global Notifications */}
      {notification && (
        <div
          className={`p-3.5 rounded-lg flex items-center justify-between text-xs font-medium ${
            notification.type === 'success'
              ? 'bg-softPaper text-emerald-700 border-warm-mist'
              : 'bg-parchment text-rose-600 border-warm-mist'
          }`}
        >
          <span>{notification.message}</span>
          <button onClick={() => setNotification(null)} className="text-slate-500 hover:text-slate-400">
            ✕
          </button>
        </div>
      )}

      {/* Workflow Editor Mode */}
      {isEditing ? (
        <WorkflowEditor
          initialWorkflow={selectedWorkflow}
          onSave={handleSaveWorkflow}
          onCancel={() => setIsEditing(false)}
        />
      ) : (
        <div className="space-y-6">
          {/* Workflows List */}
          <WorkflowList
            workflows={workflows}
            onSelect={handleSelectWorkflow}
            onRun={handleRunWorkflow}
            onDelete={handleDeleteWorkflow}
          />

          {/* Selected Workflow Detail & Run History */}
          {selectedWorkflow && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-2">
              {/* Left Column: Workflow Detail */}
              <Card className="lg:col-span-1 p-5 bg-slate-100 border-warm-mist space-y-4">
                <div className="flex items-center justify-between border-b border-warm-mist pb-3">
                  <div className="flex items-center gap-2">
                    <GitBranch className="w-4 h-4 text-brand-accent" />
                    <h3 className="font-semibold text-ink text-sm">{selectedWorkflow.name}</h3>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-500 text-[10px] font-mono">
                    {selectedWorkflow.trigger_type}
                  </span>
                </div>

                <div className="space-y-2 text-slate-500">
                  <p className="text-slate-400 leading-relaxed">
                    {selectedWorkflow.description || 'No description provided.'}
                  </p>

                  <div className="space-y-1.5 pt-2">
                    <span className="font-semibold text-slate-500 uppercase text-[10px] tracking-wider block">
                      Pipeline Architecture:
                    </span>
                    <ol className="space-y-1.5 font-mono text-[11px] list-decimal list-inside pl-1 text-slate-400">
                      {selectedWorkflow.graph_definition?.steps?.map((step, idx) => (
                        <li key={idx} className="p-1.5 rounded bg-slate-100 border border-warm-mist/50">
                          <span className="font-bold text-brand-accent uppercase">{step.type}: </span>
                          <span>{step.agent || step.action || `${step.field} ${step.operator}`}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                </div>

                <div className="pt-3 border-t border-warm-mist flex items-center justify-between">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setIsEditing(true)}
                  >
                    Edit Definition
                  </Button>
                  <Button
                    size="sm"
                    className="bg-brand-accent text-white flex items-center gap-1.5"
                    disabled={runningWorkflowId === selectedWorkflow.id}
                    onClick={() => handleRunWorkflow(selectedWorkflow)}
                  >
                    <Play className="w-3.5 h-3.5" />
                    {runningWorkflowId === selectedWorkflow.id ? 'Starting...' : 'Execute Now'}
                  </Button>
                </div>
              </Card>

              {/* Right Column: Execution Run History */}
              <div className="lg:col-span-2">
                <Card className="p-5 bg-slate-100 border-warm-mist">
                  <WorkflowRunHistory runs={runs} onCancelRun={handleCancelRun} />
                </Card>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}