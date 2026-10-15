import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { FilledActionButton } from '@/components/ui/FilledActionButton';
import { agentService, Citation, RAGResponseData } from '@/services/agents/agentService';
import {
  Search,
  BookOpen,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  Database,
  Layers,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';

const SUGGESTED_QUERIES = [
  "What is the company's leave policy?",
  "What is the payment term mentioned in the vendor agreement?",
  "What are the safety requirements for this machine?",
  "What is the company's password policy?",
  "What procedure should be followed when a machine fails?",
];

export default function KnowledgeBasePage() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState('');
  const [result, setResult] = useState<RAGResponseData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (textToSearch?: string) => {
    const question = textToSearch || query;
    if (!question.trim() || loading) return;

    setLoading(true);
    setError(null);
    setLoadingStage('Understanding question...');

    try {
      setTimeout(() => {
        setLoadingStage('Searching company knowledge via pgvector...');
      }, 300);

      const response = await agentService.queryRAG(question);

      if (response && response.data) {
        setLoadingStage('Generating answer...');
        setResult(response.data);
      } else {
        throw new Error('Invalid response structure from RAG Agent API.');
      }
    } catch (err: any) {
      setError(
        err.response?.data?.error?.message ||
        err.message ||
        'Failed to retrieve knowledge from RAG Agent.'
      );
    } finally {
      setLoading(false);
      setLoadingStage('');
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-ink">
              Enterprise Knowledge Base
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-brand-accent/5 text-brand-accent/80 border border-brand-accent/20">
              RAG Agent Active
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Semantic similarity search across uploaded company documents with verifiable source citations.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-100/80 px-3 py-2 rounded-lg border border-warm-mist">
          <Database className="w-4 h-4 text-brand-accent" />
          <span>PostgreSQL + pgvector • Tenant Isolated</span>
        </div>
      </div>

      {/* Search Input Bar */}
      <Card className="p-6 space-y-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSearch();
          }}
          className="flex gap-3"
        >
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question about policies, agreements, SOPs, or machine manuals..."
              className="w-full pl-10 pr-4 py-2.5 bg-slate-100 border border-warm-mist rounded-lg text-sm text-ink placeholder-slate-400 focus:outline-none focus:border-brand-accent transition-colors"
            />
          </div>
          <FilledActionButton
            type="submit"
            disabled={!query.trim() || loading}
            className="px-6 bg-brand-accent hover:bg-brand-accent/90 text-white font-medium"
          >
            {loading ? 'Retrieving...' : 'Search'}
          </FilledActionButton>
        </form>

        {/* Suggested Queries */}
        <div className="space-y-2 pt-1">
          <span className="text-xs text-slate-500 font-medium flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-brand-accent" />
            Suggested Questions:
          </span>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_QUERIES.map((sq, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuery(sq);
                  handleSearch(sq);
                }}
                disabled={loading}
                className="text-xs px-3 py-1.5 rounded-lg bg-slate-100 border border-warm-mist text-slate-500 hover:text-brand-accent hover:border-warm-mist/50 transition-colors text-left"
              >
                {sq}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Loading State */}
      {loading && (
        <Card className="p-8 text-center space-y-3">
          <div className="flex items-center justify-center gap-2 text-brand-accent font-medium text-sm animate-pulse">
            <BookOpen className="w-5 h-5" />
            <span>{loadingStage || 'Processing knowledge query...'}</span>
          </div>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Filtering by organization ID, performing cosine similarity search, and verifying factual context.
          </p>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <div className="p-4 rounded-lg bg-parchment border border-warm-mist text-xs text-brand-accent flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-brand-accent shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-semibold text-brand-accent">Retrieval Error</h4>
            <p className="text-slate-300 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Results Display */}
      {result && !loading && (
        <Card className="p-6 space-y-6">
          {/* Status Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-warm-mist pb-4">
            <div className="flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-brand-accent" />
              <h2 className="text-base font-semibold text-ink">Grounded Answer</h2>
            </div>
            <div className="flex items-center gap-2">
              {result.grounded ? (
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-brand-accent/10 text-brand-accent border border-brand-accent/30">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Grounded in Company Documents
                </span>
              ) : (
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-parchment text-slate-500 border border-warm-mist">
                  <AlertTriangle className="w-3.5 h-3.5" /> Refusal: Insufficient Info
                </span>
              )}
              <span className="text-xs text-slate-400 bg-slate-100 px-2.5 py-1 rounded">
                {(result.confidence * 100).toFixed(0)}% confidence
              </span>
            </div>
          </div>

          {/* Answer Content */}
          <div className="p-5 rounded-lg bg-parchment border border-warm-mist leading-relaxed text-sm text-ink">
            {result.answer}
          </div>

          {/* Citations List */}
          {result.citations && result.citations.length > 0 ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-brand-accent" />
                  Source Documents ({result.citations.length})
                </span>
                <span className="text-xs text-slate-500">
                  {result.retrieved_chunks} chunks evaluated
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {result.citations.map((citation, cIdx) => (
                  <div
                    key={cIdx}
                    className="p-4 rounded-lg bg-slate-100 border border-warm-mist space-y-2 hover:border-warm-mist/50 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-lg">📄</span>
                        <div className="min-w-0">
                          <p className="text-xs font-semibold text-ink truncate">
                            {citation.document_name}
                          </p>
                          <p className="text-[11px] text-slate-400">
                            {citation.page_number ? `Page ${citation.page_number}` : 'Entire Document'}
                            {citation.section ? ` • ${citation.section}` : ''}
                          </p>
                        </div>
                      </div>
                      {citation.relevance_score && (
                        <span className="text-[11px] font-mono text-brand-accent shrink-0">
                          {(citation.relevance_score * 100).toFixed(0)}% match
                        </span>
                      )}
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono truncate">
                      Chunk ID: {citation.chunk_id}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-500 italic p-3 bg-slate-100 rounded-lg border border-warm-mist">
              No citations attached because no supporting documents contained sufficient verified facts.
            </div>
          )}
        </Card>
      )}
    </div>
  );
}