import { apiClient } from '../api/client';
import { ImageArtifact, VisionAnalysisData } from '@/types';

export const visionService = {
  uploadImage: async (file: File): Promise<ImageArtifact> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post('/agents/vision/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data.data;
  },

  analyzeImage: async (
    imageId: string,
    question: string,
    taskType?: string
  ): Promise<VisionAnalysisData> => {
    const res = await apiClient.post('/agents/vision/analyze', {
      image_id: imageId,
      question,
      task_type: taskType || undefined,
    });
    return res.data.data;
  },

  listImages: async (): Promise<ImageArtifact[]> => {
    const res = await apiClient.get('/agents/vision/images');
    return res.data.data || [];
  },

  getImage: async (imageId: string): Promise<ImageArtifact> => {
    const res = await apiClient.get(`/agents/vision/images/${imageId}`);
    return res.data.data;
  },
};
