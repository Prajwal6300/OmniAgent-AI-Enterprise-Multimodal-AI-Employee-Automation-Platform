import { apiClient } from '../api/client';

export interface SupervisorDecision {
  intent: string;
  task_type: string;
  capability: string;
  selected_agent: string;
  priority: 'low' | 'medium' | 'high';
  confidence: number;
  requires_tool: boolean;
  requires_approval: boolean;
  task_plan: string[];
  explanation: string;
}

export interface Citation {
  document_id: string;
  document_name: string;
  page_number?: number | null;
  chunk_id: string;
  relevance_score?: number | null;
  section?: string | null;
}

export interface RAGResponseData {
  answer: string;
  grounded: boolean;
  confidence: number;
  citations: Citation[];
  retrieved_chunks: number;
}

export interface DatabaseResponseData {
  question: string;
  summary: string;
  columns: string[];
  rows: Record<string, any>[];
  row_count: number;
  query_executed: boolean;
  confidence: number;
  limited?: boolean;
  error?: string | null;
}

export interface ReasoningEvidence {
  source_type: string;
  source_id?: string | null;
  source_name?: string | null;
  content: string;
  page_number?: number | null;
  confidence?: number | null;
  metadata?: Record<string, any>;
}

export interface ReasoningConflict {
  source_a: string;
  source_b: string;
  claim_a: string;
  claim_b: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | string;
}

export interface ReasoningResponseData {
  answer: string;
  task_type: string;
  grounded: boolean;
  confidence: number;
  evidence: ReasoningEvidence[];
  conflicts: ReasoningConflict[];
  missing_information: string[];
  contributing_agents: string[];
  execution_plan: Array<Record<string, any>>;
  requires_approval: boolean;
  latency_ms?: number | null;
}

export const agentService = {
  runAgent: async (agentName: string, task: string) => {
    const res = await apiClient.post('/agents/run', { agent_name: agentName, task_description: task });
    return res.data;
  },

  analyzeSupervisor: async (message: string, conversationId?: string, context?: Record<string, any>) => {
    const res = await apiClient.post<{ success: boolean; data: SupervisorDecision }>('/agents/supervisor/analyze', {
      message,
      conversation_id: conversationId,
      context: context || {}
    });
    return res.data;
  },

  queryRAG: async (question: string, documentId?: string | null, topK?: number) => {
    const res = await apiClient.post<{ success: boolean; data: RAGResponseData }>('/agents/rag/query', {
      question,
      document_id: documentId || null,
      top_k: topK || 5
    });
    return res.data;
  },

  queryDatabase: async (question: string, limit?: number) => {
    const res = await apiClient.post<{ success: boolean; data: DatabaseResponseData }>('/agents/database/query', {
      question,
      limit: limit || 50
    });
    return res.data;
  },

  analyzeReasoning: async (
    question: string,
    conversationId?: string,
    imageId?: string,
    documentId?: string,
    context?: Record<string, any>
  ) => {
    const res = await apiClient.post<{ success: boolean; data: ReasoningResponseData }>('/agents/reasoning/analyze', {
      question,
      conversation_id: conversationId,
      image_id: imageId,
      document_id: documentId,
      context: context || {}
    });
    return res.data;
  }
};

