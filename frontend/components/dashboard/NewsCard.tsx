"use client";

import { useState } from "react";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ExternalLink, BrainCircuit, Loader2, CheckCircle2 } from "lucide-react";
import { quizService } from "@/services/quiz";
import { motion } from "framer-motion";
import Link from "next/link";

interface NewsCardProps {
  article: any;
  delay?: number;
}

export function NewsCard({ article, delay = 0 }: NewsCardProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [success, setSuccess] = useState(article.status === "processed");

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      await quizService.generateQuiz(article.article_id);
      // We simulate waiting for background job, or just show success state immediately for UX
      setTimeout(() => {
        setSuccess(true);
        setIsGenerating(false);
      }, 1500);
    } catch (error) {
      console.error("Failed to generate quiz", error);
      setIsGenerating(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
    >
      <Card className="glass-card flex flex-col h-full hover:bg-card/80 transition-colors group">
        <CardHeader>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium px-2 py-1 bg-primary/10 text-primary rounded-full">
              {article.source}
            </span>
            <span className="text-xs text-muted-foreground">
              {new Date(article.published_at).toLocaleDateString()}
            </span>
          </div>
          <CardTitle className="text-lg line-clamp-2 leading-tight">
            {article.title}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1">
          <p className="text-sm text-muted-foreground line-clamp-3">
            {article.content}
          </p>
        </CardContent>
        <CardFooter className="flex justify-between items-center border-t border-border/50 pt-4">
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-muted-foreground hover:text-foreground flex items-center transition-colors"
          >
            Read Source <ExternalLink className="ml-1 h-3 w-3" />
          </a>
          
          {article.quiz_id ? (
            <Link href={`/quiz/${article.quiz_id}`}>
              <Button size="sm" variant="secondary" className="bg-green-500/20 text-green-500 hover:bg-green-500/30 cursor-pointer">
                <CheckCircle2 className="mr-2 h-4 w-4" />
                Take Quiz
              </Button>
            </Link>
          ) : success ? (
            <Button size="sm" variant="secondary" className="bg-green-500/20 text-green-500 hover:bg-green-500/30" disabled>
              <CheckCircle2 className="mr-2 h-4 w-4 animate-pulse" />
              Quiz Ready
            </Button>
          ) : (
            <Button size="sm" onClick={handleGenerate} disabled={isGenerating}>
              {isGenerating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <BrainCircuit className="mr-2 h-4 w-4 group-hover:scale-110 transition-transform" />
                  Generate Quiz
                </>
              )}
            </Button>
          )}
        </CardFooter>
      </Card>
    </motion.div>
  );
}
