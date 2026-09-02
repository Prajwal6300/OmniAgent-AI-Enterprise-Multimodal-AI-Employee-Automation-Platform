import { apiClient } from '../api/client';

export const authService = {
  login: async (email: string, password: string) => {
    const res = await apiClient.post('/auth/login', { email, password });
    return res.data;
  },
  getCurrentUser: async () => {
    const res = await apiClient.get('/users/me');
    return res.data;
  }
};
