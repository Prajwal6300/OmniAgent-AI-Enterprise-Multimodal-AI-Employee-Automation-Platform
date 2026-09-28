import { apiClient } from './api/client';
import { ActionApprovalItem, ActionHistoryItem } from './approvals/approvalService';

export const approvalApi = {
  getApprovals: async (status?: string, skip: number = 0, limit: number = 50): Promise<ActionApprovalItem[]> => {
    const params: Record<string, any> = { skip, limit };
    if (status) params.status = status;
    const res = await apiClient.get('/agents/action/approvals', { params });
    return res.data?.data || [];
  },

  approve: async (approvalId: string, reason?: string): Promise<ActionApprovalItem> => {
    const res = await apiClient.post(`/agents/action/approvals/${approvalId}/approve`, { reason });
    return res.data?.data;
  },

  reject: async (approvalId: string, reason?: string): Promise<ActionApprovalItem> => {
    const res = await apiClient.post(`/agents/action/approvals/${approvalId}/reject`, { reason });
    return res.data?.data;
  },

  getActionHistory: async (skip: number = 0, limit: number = 50): Promise<ActionHistoryItem[]> => {
    const res = await apiClient.get('/agents/action/history', { params: { skip, limit } });
    return res.data?.data || [];
  },

  resumeOrchestration: async (
    requestId: string,
    approvalId: string,
    decision: 'APPROVED' | 'REJECTED' = 'APPROVED',
    reason?: string
  ) => {
    const res = await apiClient.post(`/orchestration/${requestId}/resume`, {
      approval_id: approvalId,
      decision,
      reason,
    });
    return res.data?.data;
  },
};
