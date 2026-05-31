import { api } from './api';

export const newsService = {
  getLatestNews: async (limit: number = 20) => {
    const response = await api.get(`/api/v1/news/latest?limit=${limit}`);
    return response.data;
  },
  getNewsById: async (articleId: string) => {
    const response = await api.get(`/api/v1/news/${articleId}`);
    return response.data;
  }
};
