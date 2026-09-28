import { apiClient } from './api/client';
import { UnifiedChatRequest, UnifiedChatResponse } from '../types';

export const chatApi = {
  chat: async (request: UnifiedChatRequest): Promise<UnifiedChatResponse> => {
    const res = await apiClient.post('/chat', request);
    return res.data?.data;
  },

  resume: async (
    requestId: string,
    approvalId: string,
    decision: 'APPROVED' | 'REJECTED' = 'APPROVED',
    reason?: string
  ): Promise<UnifiedChatResponse> => {
    const res = await apiClient.post(`/orchestration/${requestId}/resume`, {
      approval_id: approvalId,
      decision,
      reason,
    });
    return res.data?.data;
  },

  cancel: async (requestId: string): Promise<UnifiedChatResponse> => {
    const res = await apiClient.post(`/orchestration/${requestId}/cancel`);
    return res.data?.data;
  },

  getStatus: async (requestId: string): Promise<UnifiedChatResponse> => {
    const res = await apiClient.get(`/orchestration/${requestId}/status`);
    return res.data?.data;
  },

  getEvents: async (requestId: string): Promise<any[]> => {
    const res = await apiClient.get(`/orchestration/${requestId}/events`);
    return res.data?.data || [];
  },
};
