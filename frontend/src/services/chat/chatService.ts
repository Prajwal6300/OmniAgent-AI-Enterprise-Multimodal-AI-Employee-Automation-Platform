import { apiClient } from '../api/client';

export const chatService = {
  sendMessage: async (conversationId: string, content: string) => {
    const res = await apiClient.post(`/chat/conversations/${conversationId}/messages`, { content });
    return res.data;
  }
};
