import { apiClient } from '../api/client';

export const workflowService = {
  listWorkflows: async () => {
    const res = await apiClient.get('/workflows');
    return res.data;
  }
};
