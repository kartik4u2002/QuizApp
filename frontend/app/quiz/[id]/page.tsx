"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { quizService } from "@/services/quiz";
import { useAuthStore } from "@/store/useAuthStore";
import { QuizCard } from "@/components/quiz/QuizCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Trophy, RefreshCw, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";

export default function QuizPage() {
  const { id } = useParams();
  const router = useRouter();
  const { accessToken } = useAuthStore();
  
  const [quiz, setQuiz] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [score, setScore] = useState(0);
  const [isFinished, setIsFinished] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [answersRecord, setAnswersRecord] = useState<any[]>([]);

  useEffect(() => {
    if (!accessToken) {
      router.push("/login");
      return;
    }

    const fetchQuiz = async () => {
      try {
        // Since we don't have a GET /quiz/{id} endpoint yet, we'll fetch all and filter, 
        // or for the sake of the walkthrough we mock it if not found
        const quizzes = await quizService.getLatestQuizzes(50);
        const found = quizzes.find((q: any) => q.quiz_id === id);
        
        if (found) {
          setQuiz(found);
        } else {
          console.error("Quiz not found");
          router.push("/dashboard");
        }
      } catch (error) {
        console.error("Failed to load quiz", error);
      } finally {
        setLoading(false);
      }
    };

    fetchQuiz();
  }, [id, accessToken, router]);

  const handleAnswerSubmit = (isCorrect: boolean, selectedAnswer: string) => {
    if (isCorrect) {
      setScore((prev) => prev + 1);
    }

    setAnswersRecord((prev) => [
      ...prev,
      {
        question: quiz.questions[currentIndex].question,
        selected_answer: selectedAnswer,
        is_correct: isCorrect
      }
    ]);

    if (currentIndex < quiz.questions.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    } else {
      handleFinishQuiz();
    }
  };

  const handleFinishQuiz = async () => {
    setIsFinished(true);
    setSubmitting(true);
    
    // Calculate final score out of 100
    const finalScore = Math.round((score / quiz.questions.length) * 100);

    try {
      await quizService.submitQuiz({
        quiz_id: quiz.quiz_id,
        score: finalScore,
        answers: answersRecord
      });
    } catch (error) {
      console.error("Failed to submit score", error);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!quiz || !quiz.questions || quiz.questions.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p>Invalid quiz data.</p>
      </div>
    );
  }

  if (isFinished) {
    const finalScore = Math.round((score / quiz.questions.length) * 100);
    return (
      <div className="flex min-h-[80vh] items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          <Card className="glass-card text-center border-white/10">
            <CardHeader>
              <div className="mx-auto mb-4 bg-primary/20 p-4 rounded-full w-20 h-20 flex items-center justify-center">
                <Trophy className="h-10 w-10 text-primary" />
              </div>
              <CardTitle className="text-3xl">Quiz Complete!</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-6xl font-black text-primary mb-2">{finalScore}%</div>
              <p className="text-muted-foreground">
                You answered {score} out of {quiz.questions.length} questions correctly.
              </p>
            </CardContent>
            <CardFooter className="flex flex-col space-y-4">
              <Button className="w-full" onClick={() => router.push("/dashboard")} disabled={submitting}>
                {submitting ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : null}
                Return to Dashboard
              </Button>
            </CardFooter>
          </Card>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="container max-w-screen-xl py-12 px-4 flex justify-center items-center min-h-[80vh]">
      <QuizCard 
        question={quiz.questions[currentIndex]}
        currentQuestionIndex={currentIndex}
        totalQuestions={quiz.questions.length}
        onAnswerSubmit={handleAnswerSubmit}
      />
    </div>
  );
}
