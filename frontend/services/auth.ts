import { api } from './api';

export const authService = {
  login: async (credentials: any) => {
    const response = await api.post('/users/token/', credentials);
    return response.data;
  },
  register: async (data: any) => {
    const response = await api.post('/users/register/', data);
    return response.data;
  }
};
