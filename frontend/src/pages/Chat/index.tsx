import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { agentService, Citation, DatabaseResponseData, RAGResponseData, SupervisorDecision } from '@/services/agents/agentService';
import {
  Send,
  Bot,
  User,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  ArrowRight,
  Sparkles,
  ListOrdered,
  Clock,
  HelpCircle,
  BookOpen,
  FileText,
  Search,
  Check,
  Database,
  Table as TableIcon,
} from 'lucide-react';

interface AnalysisEntry {
  id: string;
  userMessage: string;
  timestamp: string;
  loading: boolean;
  loadingStep?: string;
  decision?: SupervisorDecision;
  ragResult?: RAGResponseData;
  databaseResult?: DatabaseResponseData;
  error?: string;
}

const SAMPLE_PROMPTS = [
  'How many pending orders do we have?',
  'Show failed inspections',
  'What are the top 5 machines by failures?',
  'What is the average production time?',
  'What is the company\'s leave policy?',
  'Summarize this PDF',
  'Send this report to the manager',
  'Delete the employee record',
];

export default function MultimodalChatPage() {
  const [inputMessage, setInputMessage] = useState('');
  const [entries, setEntries] = useState<AnalysisEntry[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (textToAnalyze?: string) => {
    const message = textToAnalyze || inputMessage;
    if (!message.trim() || isSubmitting) return;

    const entryId = `entry_${Date.now()}`;
    const newEntry: AnalysisEntry = {
      id: entryId,
      userMessage: message,
      timestamp: new Date().toLocaleTimeString(),
      loading: true,
      loadingStep: 'Analyzing intent with Supervisor Agent...',
    };

    setEntries((prev) => [newEntry, ...prev]);
    setInputMessage('');
    setIsSubmitting(true);

    try {
      const response = await agentService.analyzeSupervisor(message);
      if (response && response.data) {
        const decision = response.data;
        let ragData: RAGResponseData | undefined = undefined;
        let dbData: DatabaseResponseData | undefined = undefined;

        // If Supervisor selects RAG Agent, execute knowledge search
        if (decision.selected_agent === 'rag_agent' || decision.task_type === 'KNOWLEDGE_SEARCH') {
          setEntries((prev) =>
            prev.map((item) =>
              item.id === entryId
                ? { ...item, decision, loadingStep: 'Searching company knowledge...' }
                : item
            )
          );

          try {
            const ragRes = await agentService.queryRAG(message);
            if (ragRes && ragRes.data) {
              ragData = ragRes.data;
            }
          } catch (ragErr: any) {
            console.warn('RAG Query non-fatal notice:', ragErr);
          }
        }

        // If Supervisor selects Database Agent, execute business database query
        if (decision.selected_agent === 'database_agent' || decision.task_type === 'DATABASE_QUERY') {
          setEntries((prev) =>
            prev.map((item) =>
              item.id === entryId
                ? { ...item, decision, loadingStep: 'Querying business data…' }
                : item
            )
          );

          try {
            const dbRes = await agentService.queryDatabase(message);
            if (dbRes && dbRes.data) {
              dbData = dbRes.data;
            }
          } catch (dbErr: any) {
            console.warn('Database Query error:', dbErr);
          }
        }

        setEntries((prev) =>
          prev.map((item) =>
            item.id === entryId
              ? {
                  ...item,
                  loading: false,
                  loadingStep: undefined,
                  decision,
                  ragResult: ragData,
                  databaseResult: dbData,
                }
              : item
          )
        );
      } else {
        throw new Error('Invalid response structure from Supervisor API.');
      }
    } catch (err: any) {

      setEntries((prev) =>
        prev.map((item) =>
          item.id === entryId
            ? {
                ...item,
                loading: false,
                loadingStep: undefined,
                error: err.response?.data?.error?.message || err.message || 'Failed to communicate with Supervisor Agent.',
              }
            : item
        )
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">
              Supervisor Agent Console
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Day 1 Active
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Natural language intent classification, capability mapping, risk assessment, and operational DAG synthesis.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-800/80 px-3 py-2 rounded-lg border border-slate-700">
          <Bot className="w-4 h-4 text-cyan-400" />
          <span>Specialist execution locked • Routing determination only</span>
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
              placeholder="Enter an enterprise task (e.g. 'Summarize this PDF', 'What is the total sales amount from the database?')..."
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
            {/* Sample Chips */}
            <div className="flex flex-wrap items-center gap-1.5 text-xs">
              <span className="text-slate-500 font-medium">Quick Prompts:</span>
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
              {isSubmitting ? 'Analyzing...' : 'Analyze Task'}
            </Button>
          </div>
        </form>
      </Card>

      {/* Results Feed */}
      <div className="space-y-4">
        {entries.length === 0 ? (
          <Card className="p-8 text-center border-dashed border-slate-800 bg-slate-900/40">
            <div className="w-12 h-12 mx-auto rounded-full bg-slate-800 flex items-center justify-center text-slate-400 mb-3">
              <Sparkles className="w-6 h-6 text-cyan-400" />
            </div>
            <h3 className="text-base font-semibold text-slate-200">No Task Evaluated Yet</h3>
            <p className="text-sm text-slate-400 max-w-md mx-auto mt-1">
              Submit an enterprise prompt above or select a quick prompt to observe the Supervisor Agent classify intent, select target agents, and build structured plans.
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

              {/* Status / Loading State */}
              {entry.loading && (
                <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                  <div className="flex items-center gap-2 text-sm text-cyan-400 font-medium animate-pulse">
                    <Bot className="w-4 h-4" />
                    <span>{entry.loadingStep || 'Understanding question & analyzing intent...'}</span>
                  </div>
                  <div className="text-xs text-slate-500 pl-6">
                    {entry.loadingStep?.includes('knowledge')
                      ? 'Generating query vector embedding and searching pgvector semantic store...'
                      : 'Executing LangGraph routing and capability determination...'}
                  </div>
                </div>
              )}

              {/* Error State */}
              {entry.error && (
                <div className="p-4 rounded-lg bg-red-950/40 border border-red-900/50 flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-semibold text-red-300">Analysis Error</h4>
                    <p className="text-xs text-red-400 mt-0.5">{entry.error}</p>
                  </div>
                </div>
              )}

              {/* Structured Supervisor Decision */}
              {entry.decision && (
                <div className="space-y-4">
                  {/* Step Indicators */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center gap-2.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      <div className="text-xs">
                        <span className="text-slate-500 block">Identified Intent</span>
                        <span className="font-semibold text-slate-200 capitalize">
                          {entry.decision.intent.replace(/_/g, ' ')}
                        </span>
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center gap-2.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      <div className="text-xs">
                        <span className="text-slate-500 block">Required Capability</span>
                        <span className="font-semibold text-slate-200 uppercase">
                          {entry.decision.task_type}
                        </span>
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-950 border border-cyan-900/40 flex items-center gap-2.5">
                      <ArrowRight className="w-4 h-4 text-cyan-400 shrink-0" />
                      <div className="text-xs">
                        <span className="text-slate-500 block">Target Specialist</span>
                        <span className="font-semibold text-cyan-300 font-mono">
                          {entry.decision.selected_agent}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Badges & Risk Evaluation */}
                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    {/* Priority */}
                    <span
                      className={`px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wider ${
                        entry.decision.priority === 'high'
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          : entry.decision.priority === 'medium'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      }`}
                    >
                      Priority: {entry.decision.priority}
                    </span>

                    {/* Approval Gate */}
                    {entry.decision.requires_approval ? (
                      <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                        <ShieldAlert className="w-3.5 h-3.5" />
                        Human Approval Required
                      </span>
                    ) : (
                      <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
                        No Approval Required
                      </span>
                    )}

                    {/* Tool Requirement */}
                    {entry.decision.requires_tool && (
                      <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        Tool Invocation Required
                      </span>
                    )}

                    {/* Confidence Meter */}
                    <span className="ml-auto text-xs text-slate-400">
                      Confidence: <strong className="text-slate-200">{(entry.decision.confidence * 100).toFixed(0)}%</strong>
                    </span>
                  </div>

                  {/* Structured Task Plan */}
                  {entry.decision.task_plan && entry.decision.task_plan.length > 0 && (
                    <div className="rounded-lg bg-slate-950 p-4 border border-slate-800 space-y-2">
                      <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                        <ListOrdered className="w-4 h-4 text-cyan-400" />
                        <span>Structured Operational Task Plan</span>
                      </div>
                      <ol className="space-y-1.5 list-decimal list-inside text-xs text-slate-300 pl-1">
                        {entry.decision.task_plan.map((step, idx) => (
                          <li key={idx} className="leading-relaxed">
                            <span className="text-slate-200 font-medium">{step}</span>
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}

                  {/* Explanation / Reasoning Summary */}
                  {entry.decision.explanation && (
                    <div className="text-xs text-slate-400 flex items-start gap-2 bg-slate-800/40 p-3 rounded-lg border border-slate-800">
                      <HelpCircle className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-medium text-slate-300">Supervisor Rationale: </span>
                        <span>{entry.decision.explanation}</span>
                      </div>
                    </div>
                  )}

                  {/* RAG Agent Grounded Answer & Citations */}
                  {entry.ragResult && (
                    <div className="rounded-lg bg-slate-900 border border-cyan-500/30 p-5 space-y-4 shadow-lg shadow-cyan-950/20">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                        <div className="flex items-center gap-2">
                          <BookOpen className="w-5 h-5 text-cyan-400" />
                          <h3 className="text-sm font-semibold text-slate-100">
                            RAG Agent Knowledge Answer
                          </h3>
                        </div>
                        <div className="flex items-center gap-2">
                          {entry.ragResult.grounded ? (
                            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              Grounded in Documents
                            </span>
                          ) : (
                            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                              <AlertTriangle className="w-3.5 h-3.5" />
                              Refusal: Insufficient Info
                            </span>
                          )}
                          <span className="text-xs text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                            {(entry.ragResult.confidence * 100).toFixed(0)}% confidence
                          </span>
                        </div>
                      </div>

                      {/* Answer Text */}
                      <div className="text-sm text-slate-200 leading-relaxed bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
                        {entry.ragResult.answer}
                      </div>

                      {/* Sources & Citations */}
                      {entry.ragResult.citations && entry.ragResult.citations.length > 0 && (
                        <div className="space-y-2 pt-1">
                          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                            <FileText className="w-3.5 h-3.5 text-cyan-400" />
                            <span>Sources</span>
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {entry.ragResult.citations.map((c, cIdx) => (
                              <div
                                key={cIdx}
                                className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-950 border border-slate-800 hover:border-slate-700 transition-colors"
                              >
                                <span className="text-base">📄</span>
                                <div className="text-xs space-y-0.5 min-w-0">
                                  <div className="font-semibold text-slate-200 truncate">
                                    {c.document_name}
                                  </div>
                                  <div className="text-slate-400">
                                    {c.page_number ? `Page ${c.page_number}` : 'Full Document'}
                                    {c.section ? ` • ${c.section}` : ''}
                                  </div>
                                  {c.relevance_score && (
                                    <div className="text-cyan-400 text-[10px]">
                                      Match score: {(c.relevance_score * 100).toFixed(0)}%
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Database Agent Real Business Query Results */}
                  {/* Database Agent Real Business Query Results */}
                  {entry.databaseResult && (() => {
                    const db = entry.databaseResult;
                    return (
                      <div className="rounded-lg bg-slate-900 border border-emerald-500/30 p-5 space-y-4 shadow-lg shadow-emerald-950/20">
                        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                          <div className="flex items-center gap-2">
                            <Database className="w-5 h-5 text-emerald-400" />
                            <h3 className="text-sm font-semibold text-slate-100">
                              Database Agent Query Result
                            </h3>
                          </div>
                          <div className="flex items-center gap-2">
                            {db.query_executed ? (
                              <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                Executed (Read-Only)
                              </span>
                            ) : (
                              <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                                <AlertTriangle className="w-3.5 h-3.5" />
                                Query Refused
                              </span>
                            )}
                            <span className="text-xs text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                              {db.row_count} row{db.row_count !== 1 ? 's' : ''}
                              {db.limited ? ' (limited)' : ''}
                            </span>
                          </div>
                        </div>

                        {/* Summary Box */}
                        <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                          <div className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">
                            Summary
                          </div>
                          <div className="text-sm text-slate-200 leading-relaxed font-medium">
                            {db.summary}
                          </div>
                        </div>

                        {/* Results Table (Real Data) */}
                        {db.rows && db.rows.length > 0 && db.columns && (
                          <div className="space-y-2 pt-1">
                            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                              <TableIcon className="w-3.5 h-3.5 text-emerald-400" />
                              <span>Results</span>
                            </div>
                            <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950">
                              <table className="w-full text-left text-xs text-slate-300">
                                <thead className="bg-slate-900/80 text-slate-400 uppercase font-semibold border-b border-slate-800">
                                  <tr>
                                    {db.columns.map((col, cIdx) => (
                                      <th key={cIdx} className="px-4 py-2.5 tracking-wider font-mono">
                                        {col}
                                      </th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800/60 font-mono text-[12px]">
                                  {db.rows.map((row, rIdx) => (
                                    <tr key={rIdx} className="hover:bg-slate-900/50 transition-colors">
                                      {db.columns.map((col, cIdx) => (
                                        <td key={cIdx} className="px-4 py-2 text-slate-200 whitespace-nowrap">
                                          {row[col] !== null && row[col] !== undefined ? String(row[col]) : <span className="text-slate-600">null</span>}
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })()}
                </div>
              )}
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
