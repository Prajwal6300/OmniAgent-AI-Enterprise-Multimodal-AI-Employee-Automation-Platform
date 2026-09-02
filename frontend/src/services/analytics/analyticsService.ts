import { apiClient } from '../api/client';

export const analyticsService = {
  getOverview: async () => {
    const res = await apiClient.get('/analytics/overview');
    return res.data;
  }
};
