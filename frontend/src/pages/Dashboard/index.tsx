import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Bot, CheckCircle2, ShieldCheck, Activity, AlertTriangle, Loader2 } from 'lucide-react';

export default function DashboardPage() {
  const [state, setState] = useState<'loading' | 'empty' | 'error' | 'success'>('loading');

  const loadingSkeletons = [
    <Card key={1} className="p-4 animate-pulse">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-graphite">Active Agents</span>
        <Loader2 className="w-4 h-4 text-slate-400" />
      </div>
      <div className="h-6 w-full rounded bg-slate-100/30 mt-2" />
    </Card>,
    <Card key={2} className="p-4 animate-pulse">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-graphite">Pending Approvals</span>
        <Loader2 className="w-4 h-4 text-slate-400" />
      </div>
      <div className="h-6 w-full rounded bg-slate-100/30 mt-2" />
    </Card>,
    <Card key={3} className="p-4 animate-pulse">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-graphite">Security Status</span>
        <Loader2 className="w-4 h-4 text-slate-400" />
      </div>
      <div className="h-6 w-full rounded bg-slate-100/30 mt-2" />
    </Card>,
    <Card key={4} className="p-4 animate-pulse">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-graphite">Total Workflow Runs</span>
        <Loader2 className="w-4 h-4 text-slate-400" />
      </div>
      <div className="h-6 w-full rounded bg-slate-100/30 mt-2" />
    </Card>,
  ];

  const emptyState = (
    <Card className="p-12 text-center text-slate-500">
      <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin" />
      <h3 className="text-base font-medium text-graphite">No dashboard data</h3>
      <p className="text-sm text-slate-400 mt-1">Dashboard statistics will appear here once connected.</p>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setState('success')}
        className="mt-3"
      >
        Load Stats
      </Button>
    </Card>
  );

  const errorState = (
    <Card className="p-8 text-center border border-warm-mist">
      <AlertTriangle className="w-8 h-8 text-warm-mist mb-3" />
      <h3 className="text-base font-semibold text-graphite">Error loading dashboard</h3>
      <p className="text-sm text-slate-400 mt-1">Could not retrieve dashboard statistics.</p>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setState('loading')}
        className="mt-3"
      >
        Retry
      </Button>
    </Card>
  );

  const successState = (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-ink">Enterprise Dashboard</h1>
        <p className="text-sm text-graphite mt-1">Real-time status of multimodal AI operations and governance.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-graphite">Active Agents</span>
            <Bot className="w-4 h-4 text-brand-accent" />
          </div>
          <div className="text-2xl font-bold text-ink">6</div>
          <div className="text-xs text-graphite">Running</div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-graphite">Pending Approvals</span>
            <CheckCircle2 className="w-4 h-4 text-brand-accent" />
          </div>
          <div className="text-2xl font-bold text-ink">2</div>
          <div className="text-xs text-graphite">Pending</div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-graphite">Security Status</span>
            <ShieldCheck className="w-4 h-4 text-brand-accent" />
          </div>
          <div className="text-2xl font-bold text-ink">Secure</div>
          <div className="text-xs text-graphite">No threats</div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-graphite">Total Workflow Runs</span>
            <Activity className="w-4 h-4 text-brand-accent" />
          </div>
          <div className="text-2xl font-bold text-ink">156</div>
          <div className="text-xs text-graphite">Completed</div>
        </Card>
      </div>

      <Card>
        <h3 className="text-base font-semibold text-graphite mb-3">Active Multi-Agent Orchestrator</h3>
        <p className="text-sm text-graphite">
          Supervisor agent running on LangGraph state machine with 6 specialized workers: Vision, Document, RAG, Database, Reasoning, and Action agents.
        </p>
      </Card>
    </div>
  );

  return (
    <div className="space-y-6">
      {state === 'loading' && <div>{loadingSkeletons}</div>}
      {state === 'empty' && <div>{emptyState}</div>}
      {state === 'error' && <div>{errorState}</div>}
      {state === 'success' && <div>{successState}</div>}
    </div>
  );
}