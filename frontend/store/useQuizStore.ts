import { create } from 'zustand';

interface QuizState {
  currentQuiz: any | null;
  setCurrentQuiz: (quiz: any) => void;
  clearQuiz: () => void;
}

export const useQuizStore = create<QuizState>((set) => ({
  currentQuiz: null,
  setCurrentQuiz: (quiz) => set({ currentQuiz: quiz }),
  clearQuiz: () => set({ currentQuiz: null }),
}));
