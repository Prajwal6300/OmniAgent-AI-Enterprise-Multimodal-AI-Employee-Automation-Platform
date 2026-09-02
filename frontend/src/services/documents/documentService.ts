import { apiClient } from '../api/client';

export const documentService = {
  listDocuments: async () => {
    const res = await apiClient.get('/documents');
    return res.data;
  }
};
