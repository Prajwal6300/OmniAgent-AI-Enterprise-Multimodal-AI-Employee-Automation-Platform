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
  }
};
