import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { chatApi } from '@/services/chatApi';
import { UnifiedChatResponse } from '@/types';
import { CitationsList } from '@/components/citations/CitationsList';
import { EvidenceList } from '@/components/agents/EvidenceList';
import { AgentActivitySection } from '@/components/execution/AgentActivitySection';
import { ApprovalCard } from '@/components/approvals/ApprovalCard';
import {
  Send,
  Bot,
  User,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  Zap,
} from 'lucide-react';

interface ChatEntry {
  id: string;
  userMessage: string;
  timestamp: string;
  loading: boolean;
  response?: UnifiedChatResponse;
  error?: string;
}

const SAMPLE_PROMPTS = [
  'What does the uploaded safety manual say about emergency shutdown?',
  'Show production failures this month.',
  'Analyze this machine image.',
  'Compare this machine image with maintenance records and create a ticket if the issue is confirmed.',
  'Send this report to my manager.',
  'Show failed inspections in production database.',
];

export default function UnifiedChatPage() {
  const [inputMessage, setInputMessage] = useState('');
  const [entries, setEntries] = useState<ChatEntry[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);

  const handleSubmit = async (textToSubmit?: string) => {
    const message = textToSubmit || inputMessage;
    if (!message.trim() || isSubmitting) return;

    const entryId = `entry_${Date.now()}`;
    const newEntry: ChatEntry = {
      id: entryId,
      userMessage: message,
      timestamp: new Date().toLocaleTimeString(),
      loading: true,
    };

    setEntries((prev) => [newEntry, ...prev]);
    setInputMessage('');
    setIsSubmitting(true);

    try {
      // Calls unified POST /api/v1/chat
      const response = await chatApi.chat({
        message,
        conversation_id: conversationId,
      });

      if (response && response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      setEntries((prev) =>
        prev.map((item) =>
          item.id === entryId
            ? { ...item, loading: false, response }
            : item
        )
      );
    } catch (err: any) {
      setEntries((prev) =>
        prev.map((item) =>
          item.id === entryId
            ? {
                ...item,
                loading: false,
                error:
                  err.response?.data?.error?.message ||
                  err.response?.data?.detail ||
                  err.message ||
                  'Failed to communicate with OmniAgent AI platform.',
              }
            : item
        )
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApprovalResolved = (entryId: string, updatedAnswer?: string) => {
    if (!updatedAnswer) return;
    setEntries((prev) =>
      prev.map((item) =>
        item.id === entryId && item.response
          ? {
              ...item,
              response: {
                ...item.response,
                status: 'COMPLETED',
                answer: `${item.response.answer}\n\n✓ ${updatedAnswer}`,
                approval: null,
              },
            }
          : item
      )
    );
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">
              OmniAgent AI — Unified Employee Chat
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              Day 8 Full Orchestration
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Autonomous multi-agent intelligence spanning documents, pgvector semantic RAG, production databases, visual inspections, cross-modal reasoning, and human-in-the-loop action governance.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-800/80 px-3 py-2 rounded-lg border border-slate-700">
          <Bot className="w-4 h-4 text-cyan-400" />
          <span>7 Specialized Agents Connected</span>
        </div>
      </div>

      {/* Input Card */}
      <Card className="p-4 bg-slate-900 border-slate-800">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
          className="space-y-3"
        >
          <div className="relative">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask a question, query business database, request document analysis, or trigger an authorized action..."
              rows={3}
              className="w-full rounded-lg bg-slate-950 border border-slate-700 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent resize-none"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
            />
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3">
            {/* Quick Prompts */}
            <div className="flex flex-wrap items-center gap-1.5 text-xs">
              <span className="text-slate-500 font-medium">Quick Scenarios:</span>
              {SAMPLE_PROMPTS.map((prompt, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSubmit(prompt)}
                  disabled={isSubmitting}
                  className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors text-xs border border-slate-700/60"
                >
                  {prompt}
                </button>
              ))}
            </div>

            <Button
              type="submit"
              disabled={isSubmitting || !inputMessage.trim()}
              className="ml-auto flex items-center gap-2 bg-cyan-600 hover:bg-cyan-500 text-white"
            >
              <Send className="w-4 h-4" />
              {isSubmitting ? 'Orchestrating...' : 'Send Message'}
            </Button>
          </div>
        </form>
      </Card>

      {/* Chat Stream Feed */}
      <div className="space-y-4">
        {entries.length === 0 ? (
          <Card className="p-8 text-center border-dashed border-slate-800 bg-slate-900/40">
            <div className="w-12 h-12 mx-auto rounded-full bg-slate-800 flex items-center justify-center text-slate-400 mb-3">
              <Sparkles className="w-6 h-6 text-cyan-400" />
            </div>
            <h3 className="text-base font-semibold text-slate-200">Start an AI Employee Conversation</h3>
            <p className="text-sm text-slate-400 max-w-lg mx-auto mt-1">
              Ask about corporate SOPs, inspect production SQL tables, analyze machine images, or request cross-modal actions. The central orchestrator will route tasks, synthesize verified evidence, and pause for approval when required.
            </p>
          </Card>
        ) : (
          entries.map((entry) => (
            <Card key={entry.id} className="p-5 bg-slate-900 border-slate-800 space-y-4">
              {/* User Query Header */}
              <div className="flex items-start justify-between border-b border-slate-800 pb-3">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-300 shrink-0">
                    <User className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-200">{entry.userMessage}</p>
                    <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-500">
                      <Clock className="w-3 h-3" />
                      <span>{entry.timestamp}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Loading State */}
              {entry.loading && (
                <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                  <div className="flex items-center gap-2 text-sm text-cyan-400 font-medium animate-pulse">
                    <Bot className="w-4 h-4 animate-spin" />
                    <span>Orchestrating multi-agent cognitive pipeline...</span>
                  </div>
                  <div className="text-xs text-slate-500 pl-6">
                    Evaluating intent with Supervisor Agent and coordinating downstream specialists...
                  </div>
                </div>
              )}

              {/* Error State */}
              {entry.error && (
                <div className="p-4 rounded-lg bg-red-950/40 border border-red-900/50 flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-semibold text-red-300">Execution Error</h4>
                    <p className="text-xs text-red-400 mt-0.5">{entry.error}</p>
                  </div>
                </div>
              )}

              {/* AI Response */}
              {entry.response && (
                <div className="space-y-4">
                  {/* Status Banner */}
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                    <div className="flex items-center gap-2">
                      <span
                        className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-semibold uppercase text-[11px] ${
                          entry.response.status === 'COMPLETED'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : entry.response.status === 'WAITING_FOR_APPROVAL'
                            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30 animate-pulse'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                        }`}
                      >
                        {entry.response.status === 'COMPLETED' && <CheckCircle2 className="w-3 h-3" />}
                        {entry.response.status === 'WAITING_FOR_APPROVAL' && <Clock className="w-3 h-3" />}
                        <span>{entry.response.status.replace(/_/g, ' ')}</span>
                      </span>

                      {entry.response.grounded && (
                        <span className="text-slate-400 font-mono text-[11px]">
                          Grounded ({(entry.response.confidence * 100).toFixed(0)}% confidence)
                        </span>
                      )}
                    </div>

                    {entry.response.agents_used && entry.response.agents_used.length > 0 && (
                      <div className="flex items-center gap-1.5 font-mono text-[11px] text-slate-400">
                        <span>Agents:</span>
                        {entry.response.agents_used.map((ag, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 capitalize"
                          >
                            {ag.replace('_agent', '')}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Answer Content */}
                  <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-sm text-slate-200 leading-relaxed whitespace-pre-line">
                    {entry.response.answer}
                  </div>

                  {/* Human-in-the-Loop Approval Card if pending */}
                  {entry.response.approval && (
                    <ApprovalCard
                      approval={entry.response.approval}
                      requestId={entry.response.request_id}
                      onResolved={(updated) => handleApprovalResolved(entry.id, updated)}
                    />
                  )}

                  {/* Action Completed Badge if executed */}
                  {entry.response.action && entry.response.action.success && (
                    <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-800/40 flex items-center justify-between text-xs text-emerald-300">
                      <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4 text-emerald-400" />
                        <span className="font-semibold capitalize">
                          Action: {entry.response.action.action_type.replace(/_/g, ' ')}
                        </span>
                        {entry.response.action.external_reference && (
                          <span className="text-slate-400 font-mono">
                            Ref: {entry.response.action.external_reference}
                          </span>
                        )}
                      </div>
                      <span className="text-emerald-400 font-bold uppercase tracking-wider text-[10px]">
                        Verified
                      </span>
                    </div>
                  )}

                  {/* Citations List */}
                  {entry.response.citations && entry.response.citations.length > 0 && (
                    <CitationsList citations={entry.response.citations} />
                  )}

                  {/* Evidence Collected */}
                  {entry.response.evidence && entry.response.evidence.length > 0 && (
                    <EvidenceList evidence={entry.response.evidence} />
                  )}

                  {/* Expandable Agent Activity Progression */}
                  {entry.response.execution_steps && entry.response.execution_steps.length > 0 && (
                    <AgentActivitySection
                      steps={entry.response.execution_steps}
                      agentsUsed={entry.response.agents_used}
                      status={entry.response.status}
                    />
                  )}
                </div>
              )}
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
