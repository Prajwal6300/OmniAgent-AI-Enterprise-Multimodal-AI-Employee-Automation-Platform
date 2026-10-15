import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api/client';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import {
  Layers,
  Plus,
  Trash2,
  Play,
  CheckCircle2,
  XCircle,
  Key,
  Calendar,
} from 'lucide-react';

interface IntegrationItem {
  id: string;
  organization_id: string;
  service_name: string;
  is_enabled: boolean;
  config: Record<string, any>;
  created_at: string;
  updated_at: string;
}

interface TestResult {
  success: boolean;
  message: string;
  latency_ms: number;
}

export default function IntegrationsPage() {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [serviceName, setServiceName] = useState('');
  const [configJson, setConfigJson] = useState('{\n  "api_key": "",\n  "url": ""\n}');
  const [testResults, setTestResults] = useState<Record<string, TestResult>>({});

  const { data: integrations = [], isLoading } = useQuery<IntegrationItem[]>({
    queryKey: ['integrations'],
    queryFn: async () => {
      const res = await apiClient.get('/integrations');
      return res.data.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      let parsed = {};
      try {
        parsed = JSON.parse(configJson);
      } catch {
        throw new Error('Invalid JSON format for configuration');
      }
      await apiClient.post('/integrations', {
        service_name: serviceName,
        is_enabled: true,
        config: parsed,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
      setShowAddModal(false);
      setServiceName('');
      setConfigJson('{\n  "api_key": "",\n  "url": ""\n}');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/integrations/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
    },
  });

  const handleTestConnection = async (id: string) => {
    try {
      const res = await apiClient.post(`/integrations/${id}/test`);
      setTestResults((prev) => ({ ...prev, [id]: res.data.data }));
    } catch (err: any) {
      setTestResults((prev) => ({
        ...prev,
        [id]: {
          success: false,
          message: err.response?.data?.detail || 'Connection test failed',
          latency_ms: 0,
        },
      }));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">Integrations</h1>
          <p className="text-sm text-graphite mt-1">
            Fernet-encrypted connectors for enterprise webhooks, email relays, and APIs.
          </p>
        </div>
        <Button
          onClick={() => setShowAddModal(true)}
          className="bg-brand-accent hover:bg-brand-accent/90 text-white text-xs flex items-center gap-1.5"
        >
          <Plus className="w-4 h-4" />
          Add Integration
        </Button>
      </div>

      {/* List */}
      {isLoading ? (
        <Card className="p-12 text-center text-slate-400">Loading integrations...</Card>
      ) : integrations.length === 0 ? (
        <Card className="p-12 text-center text-graphite border-warm-mist bg-parchment/40">
          <Layers className="w-10 h-10 text-graphite mx-auto mb-3" />
          <p className="text-base font-medium text-graphite">No integrations configured</p>
          <p className="text-xs text-graphite mt-1">
            Add a webhook, Slack, or SMTP email connector to enable external actions.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {integrations.map((item) => {
            const testResult = testResults[item.id];
            return (
              <Card key={item.id} className="p-5 border-slate-800 bg-slate-900/60 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-base font-semibold text-slate-100 uppercase tracking-wide">
                        {item.service_name}
                      </span>
                      <span
                        className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                          item.is_enabled
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        {item.is_enabled ? 'Active' : 'Disabled'}
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteMutation.mutate(item.id)}
                      className="text-slate-500 hover:text-red-400 p-1"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>

                  {/* Redacted Config Display */}
                  <div className="mt-3 bg-slate-950/70 p-3 rounded-md border border-slate-800/80 font-mono text-xs text-slate-300">
                    <div className="flex items-center gap-1.5 text-[11px] text-slate-400 mb-1.5 font-sans">
                      <Key className="w-3.5 h-3.5 text-blue-400" />
                      Encrypted Configuration (Secrets Masked)
                    </div>
                    {Object.entries(item.config).length === 0 ? (
                      <span className="text-slate-500 italic">No parameters defined</span>
                    ) : (
                      <div className="space-y-1">
                        {Object.entries(item.config).map(([k, v]) => (
                          <div key={k} className="flex justify-between">
                            <span className="text-slate-400">{k}:</span>
                            <span className="text-slate-200">{String(v)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-1.5 text-[11px] text-slate-500 mt-3">
                    <Calendar className="w-3 h-3" />
                    <span>Configured: {new Date(item.created_at).toLocaleDateString()}</span>
                  </div>

                  {/* Test Result Display */}
                  {testResult && (
                    <div
                      className={`mt-3 p-2.5 rounded text-xs flex items-center gap-2 border ${
                        testResult.success
                          ? 'bg-emerald-950/30 border-emerald-800/60 text-emerald-300'
                          : 'bg-rose-950/30 border-rose-800/60 text-rose-300'
                      }`}
                    >
                      {testResult.success ? (
                        <CheckCircle2 className="w-4 h-4 shrink-0" />
                      ) : (
                        <XCircle className="w-4 h-4 shrink-0" />
                      )}
                      <div className="flex-1 truncate">
                        <span>{testResult.message}</span>
                        {testResult.latency_ms > 0 && (
                          <span className="ml-1 text-[10px] text-slate-400">({testResult.latency_ms}ms)</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/60 flex justify-end">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleTestConnection(item.id)}
                    className="text-xs flex items-center gap-1.5 border-slate-700 text-slate-300 hover:bg-slate-800"
                  >
                    <Play className="w-3.5 h-3.5 text-blue-400" />
                    Test Connection
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <Card className="w-full max-w-lg p-6 bg-slate-900 border-slate-800 shadow-2xl">
            <h2 className="text-lg font-bold text-slate-100">Add Enterprise Integration</h2>
            <p className="text-xs text-slate-400 mt-1">
              Configuration fields will be encrypted at rest using Fernet before storage.
            </p>

            <div className="space-y-4 mt-4">
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">Service Identifier</label>
                <input
                  type="text"
                  placeholder="e.g. slack_alerts, jira_tickets, smtp_relay"
                  value={serviceName}
                  onChange={(e) => setServiceName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">
                  Configuration JSON (API keys, endpoints, tokens)
                </label>
                <textarea
                  rows={6}
                  value={configJson}
                  onChange={(e) => setConfigJson(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded p-3 font-mono text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                />
              </div>

              {createMutation.isError && (
                <div className="text-xs text-red-400">
                  {createMutation.error?.message || 'Failed to save integration'}
                </div>
              )}
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowAddModal(false)}
                className="border-slate-800 text-slate-400 hover:text-slate-200"
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={() => createMutation.mutate()}
                disabled={!serviceName.trim() || createMutation.isPending}
                className="bg-blue-600 hover:bg-blue-500 text-white"
              >
                Save Encrypted Integration
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
