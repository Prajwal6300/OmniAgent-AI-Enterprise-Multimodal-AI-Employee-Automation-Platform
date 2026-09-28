import { apiClient } from './api/client';
import { Workflow, WorkflowRun } from '../types';

export const workflowApi = {
  listWorkflows: async (): Promise<Workflow[]> => {
    const res = await apiClient.get('/workflows');
    return res.data?.data || [];
  },

  getWorkflow: async (id: string): Promise<Workflow> => {
    const res = await apiClient.get(`/workflows/${id}`);
    return res.data?.data;
  },

  createWorkflow: async (data: {
    name: string;
    description?: string;
    trigger_type: string;
    trigger_config?: Record<string, any>;
    graph_definition: Record<string, any>;
    is_active?: boolean;
  }): Promise<Workflow> => {
    const res = await apiClient.post('/workflows', data);
    return res.data?.data;
  },

  updateWorkflow: async (id: string, data: Partial<Workflow>): Promise<Workflow> => {
    const res = await apiClient.put(`/workflows/${id}`, data);
    return res.data?.data;
  },

  deleteWorkflow: async (id: string): Promise<void> => {
    await apiClient.delete(`/workflows/${id}`);
  },

  runWorkflow: async (id: string, inputPayload: Record<string, any> = {}): Promise<WorkflowRun> => {
    const res = await apiClient.post(`/workflows/${id}/run`, { input_payload: inputPayload });
    return res.data?.data;
  },

  listRuns: async (workflowId: string): Promise<WorkflowRun[]> => {
    const res = await apiClient.get(`/workflows/${workflowId}/runs`);
    return res.data?.data || [];
  },

  getRun: async (runId: string): Promise<WorkflowRun> => {
    const res = await apiClient.get(`/workflow-runs/${runId}`);
    return res.data?.data;
  },

  cancelRun: async (runId: string): Promise<WorkflowRun> => {
    const res = await apiClient.post(`/workflow-runs/${runId}/cancel`);
    return res.data?.data;
  },
};
