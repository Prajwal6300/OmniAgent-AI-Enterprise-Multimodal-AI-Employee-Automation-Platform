import React from 'react';
import { Card } from '@/components/ui/Card';
import { Bot, CheckCircle2, ShieldCheck, Activity } from 'lucide-react';

export default function DashboardPage() {
  const stats = [
    { title: 'Active Agents', value: '7 Specialists', icon: Bot, change: '100% online' },
    { title: 'Pending Approvals', value: '2 Actions', icon: CheckCircle2, change: 'Require review' },
    { title: 'Security Status', value: 'Zero Violations', icon: ShieldCheck, change: 'RLS & HMAC active' },
    { title: 'Total Workflow Runs', value: '1,429', icon: Activity, change: '+12% this week' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">Enterprise Dashboard</h1>
        <p className="text-sm text-slate-400 mt-1">Real-time status of multimodal AI operations and governance.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s, idx) => {
          const Icon = s.icon;
          return (
            <Card key={idx} className="p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">{s.title}</span>
                <Icon className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="text-2xl font-bold text-slate-100 mt-2">{s.value}</div>
              <div className="text-xs text-slate-500 mt-1">{s.change}</div>
            </Card>
          );
        })}
      </div>

      <Card>
        <h3 className="text-base font-semibold text-slate-200 mb-3">Active Multi-Agent Orchestrator</h3>
        <p className="text-sm text-slate-400">
          Supervisor agent running on LangGraph state machine with 6 specialized workers: Vision, Document, RAG, Database, Reasoning, and Action agents.
        </p>
      </Card>
    </div>
  );
}
