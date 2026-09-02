import { apiClient } from '../api/client';

export const approvalService = {
  decide: async (approvalId: string, decision: 'APPROVED' | 'REJECTED', reason?: string) => {
    const res = await apiClient.post(`/approvals/${approvalId}/decide`, { decision, reason });
    return res.data;
  }
};
