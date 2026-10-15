import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api/client';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { FilledActionButton } from '@/components/ui/FilledActionButton';
import {
  Activity,
  DollarSign,
  Cpu,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
} from 'lucide-react';

interface AnalyticsData {
  period_days: number;
  total_runs: number;
  successful_runs: number;
  success_rate_percent: number;
  total_tokens: number;
  total_cost_usd: number;
  pending_approvals: number;
  total_workflow_runs: number;
  latency: {
    avg_ms: number;
    p50_ms: number;
    p95_ms: number;
    p99_ms: number;
  };
  agent_breakdown: Array<{
    agent: string;
    count: number;
    tokens: number;
    cost_usd: number;
  }>;
}

export default function AnalyticsPage() {
  const [days, setDays] = useState<number>(30);

  const { data, isLoading, isError, refetch } = useQuery<AnalyticsData>({
    queryKey: ['analytics-overview', days],
    queryFn: async () => {
      const res = await apiClient.get(`/analytics/overview?days=${days}`);
      return res.data.data;
    },
  });

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">Enterprise Analytics</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time token utilization, cost governance, and latency telemetry.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex bg-slate-100 border border-warm-mist rounded-lg p-1 text-xs">
            {[7, 30, 90].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                  days === d
                    ? 'bg-brand-accent text-white shadow-sm'
                    : 'text-slate-500 hover:text-slate-400'
                }`}
              >
                {d}d
              </button>
            ))}
          </div>
          <FilledActionButton
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            className="flex items-center gap-1.5 text-xs text-slate-500 border-warm-mist hover:bg-slate-100"
          >
            <RotateCw className="w-3.5 h-3.5" />
            Refresh
          </FilledActionButton>
        </div>
      </div>

      {isLoading ? (
        <Card className="p-12 text-center text-slate-500">Loading telemetry data...</Card>
      ) : isError || !data ? (
        <Card className="p-8 text-center text-slate-500 border-warm-mist">
          Failed to load analytics data. Ensure backend services are online.
        </Card>
      ) : (
        <>
          {/* Top Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="p-5 border-warm-mist bg-slate-100/60">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium uppercase tracking-wider text-slate-500">Total Agent Runs</span>
                <Activity className="w-4 h-4 text-brand-accent" />
              </div>
              <div className="mt-2 text-2xl font-bold text-ink">{data.total_runs.toLocaleString()}</div>
              <div className="mt-1 text-xs text-brand-accent flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                {data.success_rate_percent}% success rate
              </div>
            </Card>

            <Card className="p-5 border-warm-mist bg-slate-100/60">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium uppercase tracking-wider text-slate-500">Total Tokens</span>
                <Cpu className="w-4 h-4 text-purple-400" />
              </div>
              <div className="mt-2 text-2xl font-bold text-ink">{data.total_tokens.toLocaleString()}</div>
              <div className="mt-1 text-xs text-slate-400">Model: GPT-4o & text-embedding-3-large</div>
            </Card>

            <Card className="p-5 border-warm-mist bg-slate-100/60">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium uppercase tracking-wider text-slate-500">Cost Incurred</span>
                <DollarSign className="w-4 h-4 text-brand-accent" />
              </div>
              <div className="mt-2 text-2xl font-bold text-ink">${data.total_cost_usd.toFixed(4)}</div>
              <div className="mt-1 text-xs text-slate-400">Last {days} days total</div>
            </Card>

            <Card className="p-5 border-warm-mist bg-slate-100/60">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium uppercase tracking-wider text-slate-500">Pending Approvals</span>
                <AlertTriangle className="w-4 h-4 text-brand-accent" />
              </div>
              <div className="mt-2 text-2xl font-bold text-ink">{data.pending_approvals}</div>
              <div className="mt-1 text-xs text-brand-accent/80">Human-in-the-loop queue</div>
            </Card>
          </div>

          {/* Latency Telemetry */}
          <Card className="p-6 border-warm-mist bg-slate-100/60">
            <h2 className="text-base font-semibold text-ink mb-4 flex items-center gap-2">
              <Clock className="w-4 h-4 text-brand-accent" />
              Latency Telemetry (ms)
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-slate-100/50 p-4 rounded-lg border border-warm-mist/30">
                <div className="text-xs text-slate-500">Average Latency</div>
                <div className="text-xl font-bold text-ink mt-1">{data.latency.avg_ms} ms</div>
              </div>
              <div className="bg-slate-100/50 p-4 rounded-lg border border-warm-mist/30">
                <div className="text-xs text-slate-500">p50 (Median)</div>
                <div className="text-xl font-bold text-ink mt-1">{data.latency.p50_ms} ms</div>
              </div>
              <div className="bg-slate-100/50 p-4 rounded-lg border border-warm-mist/30">
                <div className="text-xs text-slate-500">p95 Percentile</div>
                <div className="text-xl font-bold text-ink mt-1">{data.latency.p95_ms} ms</div>
              </div>
              <div className="bg-slate-100/50 p-4 rounded-lg border border-warm-mist/30">
                <div className="text-xs text-slate-500">p99 Percentile</div>
                <div className="text-xl font-bold text-ink mt-1">{data.latency.p99_ms} ms</div>
              </div>
            </div>
          </Card>

          {/* Agent Breakdown Table */}
          <Card className="p-6 border-warm-mist bg-slate-100/60">
            <h2 className="text-base font-semibold text-ink mb-4">Agent Execution Breakdown</h2>
            {data.agent_breakdown.length === 0 ? (
              <p className="text-sm text-slate-500">No agent run data recorded in this period.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-500">
                  <thead className="text-xs uppercase bg-slate-100/60 text-slate-500 border-b border-warm-mist">
                    <tr>
                      <th className="px-4 py-3">Agent Specialized Role</th>
                      <th className="px-4 py-3 text-right">Runs</th>
                      <th className="px-4 py-3 text-right">Tokens Consumed</th>
                      <th className="px-4 py-3 text-right">Cost (USD)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-warm-mist/30">
                    {data.agent_breakdown.map((row) => (
                      <tr key={row.agent} className="hover:bg-slate-100/30 transition-colors">
                        <td className="px-4 py-3 font-medium text-ink">{row.agent}</td>
                        <td className="px-4 py-3 text-right">{row.count.toLocaleString()}</td>
                        <td className="px-4 py-3 text-right">{row.tokens.toLocaleString()}</td>
                        <td className="px-4 py-3 text-right font-mono text-brand-accent">
                          ${row.cost_usd.toFixed(4)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}