import React from 'react';
import { Card } from '@/components/ui/Card';

export default function AgentRunsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">Agent Runs</h1>
        <p className="text-sm text-slate-400 mt-1">Step-by-step execution traces, latency, token costs, and tool calls.</p>
      </div>
      <Card>
        <div className="py-8 text-center text-slate-400">
          <p className="text-sm">Agent Runs module active and ready.</p>
        </div>
      </Card>
    </div>
  );
}
