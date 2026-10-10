import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Bot, Loader2, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function AgentRunsPage() {
  const [state, setState] = useState<'loading' | 'empty' | 'error' | 'success'>('loading');

  const loadingState = (
    <Card className="p-12 text-center text-slate-500">
      <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3 text-brand-accent" />
      <p className="text-sm">Loading agent run traces...</p>
    </Card>
  );

  const emptyState = (
    <Card className="p-12 text-center text-slate-500 border-dashed">
      <Bot className="w-10 h-10 text-brand-accent mx-auto mb-3" />
      <h3 className="text-base font-medium text-ink">No agent runs</h3>
      <p className="text-sm text-slate-500 mt-1">
        Agent execution traces, latency, token costs, and tool calls will appear here.
      </p>
    </Card>
  );

  const errorState = (
    <Card className="p-8 text-center border border-warm-mist">
      <AlertTriangle className="w-8 h-8 text-warm-mist mb-3" />
      <h3 className="text-base font-semibold text-graphite">Error loading agent runs</h3>
      <p className="text-sm text-slate-400 mt-1">Could not retrieve agent run data.</p>
      <Button variant="outline" size="sm" onClick={() => setState('loading')}>
        Retry
      </Button>
    </Card>
  );

  const successState = (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-ink">Agent Runs</h1>
        <p className="text-sm text-slate-500 mt-1">Step-by-step execution traces, latency, token costs, and tool calls.</p>
      </div>

      <Card className="space-y-4">
        <div className="py-8 text-center text-slate-500">
          <p className="text-sm">Agent execution data would appear here.</p>
        </div>
      </Card>
    </div>
  );

  return (
    <div className="space-y-6">
      {state === 'loading' && <div>{loadingState}</div>}
      {state === 'empty' && <div>{emptyState}</div>}
      {state === 'error' && <div>{errorState}</div>}
      {state === 'success' && <div>{successState}</div>}
    </div>
  );
}
