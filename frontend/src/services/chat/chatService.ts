import { apiClient } from '../api/client';
import { chatApi } from '../chatApi';
import { UnifiedChatRequest, UnifiedChatResponse } from '../../types';

export const chatService = {
  // Legacy conversation messages endpoint
  sendMessage: async (conversationId: string, content: string) => {
    const res = await apiClient.post(`/chat/conversations/${conversationId}/messages`, { content });
    return res.data;
  },

  // Unified multi-agent orchestration chat
  chat: async (request: UnifiedChatRequest): Promise<UnifiedChatResponse> => {
    return chatApi.chat(request);
  },

  resume: chatApi.resume,
  cancel: chatApi.cancel,
  getStatus: chatApi.getStatus,
  getEvents: chatApi.getEvents,
};
