import React from 'react';
import { Card } from '@/components/ui/Card';

export default function AIAgentsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">AI Agents</h1>
        <p className="text-sm text-slate-400 mt-1">Inspect and coordinate LangGraph Supervisor and worker agents.</p>
      </div>
      <Card>
        <div className="py-8 text-center text-slate-400">
          <p className="text-sm">AI Agents module active and ready.</p>
        </div>
      </Card>
    </div>
  );
}
