import { apiClient } from '../api/client';
import { Document, DocumentAnalysisData } from '@/types';

export const documentService = {
  listDocuments: async (): Promise<Document[]> => {
    const res = await apiClient.get('/documents');
    return res.data.data || [];
  },

  getDocument: async (documentId: string): Promise<Document> => {
    const res = await apiClient.get(`/documents/${documentId}`);
    return res.data.data;
  },

  uploadDocument: async (file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data.data;
  },

  analyzeDocument: async (
    documentId: string,
    task: string = 'summarize',
    query?: string
  ): Promise<DocumentAnalysisData> => {
    const res = await apiClient.post('/agents/document/analyze', {
      document_id: documentId,
      task,
      query,
    });
    return res.data.data;
  },
};
