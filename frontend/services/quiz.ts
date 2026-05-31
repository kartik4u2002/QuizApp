import { api } from './api';

export const quizService = {
  getLatestQuizzes: async (limit: number = 10) => {
    const response = await api.get(`/api/v1/quizzes/latest?limit=${limit}`);
    return response.data;
  },
  generateQuiz: async (articleId: string) => {
    const response = await api.post('/api/v1/quizzes/generate', { article_id: articleId });
    return response.data;
  },
  submitQuiz: async (data: any) => {
    const response = await api.post('/api/quiz/submit/', data);
    return response.data;
  },
  getStats: async () => {
    const response = await api.get('/api/stats/');
    return response.data;
  }
};
