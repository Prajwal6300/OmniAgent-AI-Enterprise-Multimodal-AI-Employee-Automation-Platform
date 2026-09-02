import React from 'react';
import { Card } from '@/components/ui/Card';

export default function TasksPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">Tasks</h1>
        <p className="text-sm text-slate-400 mt-1">Track scheduled tasks and asynchronous agent background jobs.</p>
      </div>
      <Card>
        <div className="py-8 text-center text-slate-400">
          <p className="text-sm">Tasks module active and ready.</p>
        </div>
      </Card>
    </div>
  );
}
