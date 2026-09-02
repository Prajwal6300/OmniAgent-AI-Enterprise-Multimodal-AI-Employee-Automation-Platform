import { apiClient } from '../api/client';

export const agentService = {
  runAgent: async (agentName: string, task: string) => {
    const res = await apiClient.post('/agents/run', { agent_name: agentName, task_description: task });
    return res.data;
  }
};
