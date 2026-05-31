"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, XCircle } from "lucide-react";

interface QuizCardProps {
  question: any;
  currentQuestionIndex: number;
  totalQuestions: number;
  onAnswerSubmit: (isCorrect: boolean, selectedAnswer: string) => void;
}

export function QuizCard({ question, currentQuestionIndex, totalQuestions, onAnswerSubmit }: QuizCardProps) {
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [isAnswered, setIsAnswered] = useState(false);
  const [timeLeft, setTimeLeft] = useState(30); // 30 seconds per question

  useEffect(() => {
    setSelectedOption(null);
    setIsAnswered(false);
    setTimeLeft(30);
  }, [question]);

  useEffect(() => {
    if (isAnswered || timeLeft === 0) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft, isAnswered]);

  useEffect(() => {
    if (timeLeft === 0 && !isAnswered) {
      handleOptionSelect(""); // Automatically fail if time runs out
    }
  }, [timeLeft]);

  const handleOptionSelect = (option: string) => {
    if (isAnswered) return;
    
    setSelectedOption(option);
    setIsAnswered(true);
    
    const isCorrect = option === question.correct_answer;
    
    // Give user a brief moment to see if they were right before moving on
    setTimeout(() => {
      onAnswerSubmit(isCorrect, option);
    }, 2000);
  };

  const getOptionStyle = (option: string) => {
    if (!isAnswered) {
      return selectedOption === option ? "border-primary bg-primary/10" : "hover:border-primary/50 hover:bg-card/80";
    }
    
    if (option === question.correct_answer) {
      return "border-green-500 bg-green-500/20 text-green-500";
    }
    
    if (selectedOption === option) {
      return "border-destructive bg-destructive/20 text-destructive";
    }
    
    return "opacity-50 grayscale";
  };

  return (
    <Card className="glass-card w-full max-w-3xl mx-auto border-white/10 shadow-2xl overflow-hidden relative">
      {/* Background Gradient Effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent pointer-events-none" />
      
      <CardHeader>
        <div className="flex justify-between items-center mb-6">
          <span className="text-sm font-medium text-muted-foreground tracking-wider uppercase">
            Question {currentQuestionIndex + 1} of {totalQuestions}
          </span>
          <div className="flex items-center space-x-2">
            <div className={`text-xl font-mono font-bold ${timeLeft < 10 ? 'text-destructive animate-pulse' : 'text-primary'}`}>
              00:{timeLeft.toString().padStart(2, '0')}
            </div>
          </div>
        </div>
        <Progress value={(currentQuestionIndex / totalQuestions) * 100} className="h-1 bg-border/50" />
      </CardHeader>
      
      <CardContent className="pt-6 pb-8 space-y-8">
        <motion.div
          key={`q-${currentQuestionIndex}`}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3 }}
        >
          <CardTitle className="text-2xl leading-relaxed font-semibold">
            {question.question}
          </CardTitle>
          
          <div className="mt-8 grid gap-4 grid-cols-1 md:grid-cols-2">
            {question.options.map((option: string, index: number) => (
              <motion.button
                key={index}
                whileHover={!isAnswered ? { scale: 1.02 } : {}}
                whileTap={!isAnswered ? { scale: 0.98 } : {}}
                onClick={() => handleOptionSelect(option)}
                disabled={isAnswered}
                className={`
                  relative flex w-full items-center justify-between p-4 rounded-xl border-2 transition-all duration-200
                  ${getOptionStyle(option)}
                `}
              >
                <span className="text-left font-medium">{option}</span>
                
                <AnimatePresence>
                  {isAnswered && option === question.correct_answer && (
                    <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="absolute right-4 text-green-500">
                      <CheckCircle2 className="h-5 w-5" />
                    </motion.div>
                  )}
                  {isAnswered && selectedOption === option && option !== question.correct_answer && (
                    <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="absolute right-4 text-destructive">
                      <XCircle className="h-5 w-5" />
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.button>
            ))}
          </div>
        </motion.div>
      </CardContent>
    </Card>
  );
}
