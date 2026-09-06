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
  }
};
