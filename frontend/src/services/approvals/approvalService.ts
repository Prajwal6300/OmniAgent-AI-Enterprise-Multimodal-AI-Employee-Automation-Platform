import { apiClient } from '../api/client';

export interface ActionApprovalItem {
  id: string;
  action_id: string;
  action_type: string;
  organization_id: string;
  requested_by?: string;
  payload_summary: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED' | 'CANCELLED';
  approved_by?: string;
  approved_at?: string;
  rejected_at?: string;
  expires_at: string;
  created_at: string;
}

export interface ActionHistoryItem {
  id: string;
  action_type: string;
  risk_level: string;
  status: string;
  requested_by?: string;
  external_reference?: string;
  verified: boolean;
  created_at: string;
  completed_at?: string;
}

export const approvalService = {
  // Legacy method maintaining backward compatibility
  decide: async (approvalId: string, decision: 'APPROVED' | 'REJECTED', reason?: string) => {
    const res = await apiClient.post(`/approvals/${approvalId}/decide`, { decision, reason });
    return res.data;
  },

  // Action Agent Approvals API
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

  executeAction: async (actionType: string, input: Record<string, any>, reason?: string, idempotencyKey?: string) => {
    const res = await apiClient.post('/agents/action/execute', {
      action_type: actionType,
      input,
      reason,
      idempotency_key: idempotencyKey,
    });
    return res.data?.data;
  },
};
