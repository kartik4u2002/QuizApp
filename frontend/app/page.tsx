"use client";

import { Button } from "@/components/ui/button";
import { Brain, ArrowRight, Sparkles, BookOpen } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useAuthStore } from "@/store/useAuthStore";
import { useEffect, useState } from "react";

export default function Home() {
  const { accessToken } = useAuthStore();
  const [mounted, setMounted] = useState(false);

  // Avoid Next.js hydration mismatch since Zustand store is persisted in localStorage
  useEffect(() => {
    setMounted(true);
  }, []);

  const getStartedHref = mounted && accessToken ? "/dashboard" : "/register";
  const browseNewsHref = mounted && accessToken ? "/news" : "/login";

  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="relative flex-1 flex flex-col items-center justify-center text-center px-4 py-24 overflow-hidden">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/20 via-background to-background"></div>
        
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-4xl mx-auto space-y-8"
        >
          <div className="inline-flex items-center rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-sm font-medium text-primary mb-4">
            <Sparkles className="mr-2 h-4 w-4" />
            Powered by BERT & T5 Transformers
          </div>
          
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight">
            Real-Time AI Quizzes <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-blue-400">
              from Live News
            </span>
          </h1>
          
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            Stay informed and test your knowledge simultaneously. Our NLP pipeline ingests global news every 5 minutes and automatically generates multiple-choice quizzes using state-of-the-art AI.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link href={getStartedHref}>
              <Button size="lg" className="h-12 px-8 text-base">
                Get Started
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link href={browseNewsHref}>
              <Button size="lg" variant="outline" className="h-12 px-8 text-base bg-background/50 backdrop-blur">
                <BookOpen className="mr-2 h-5 w-5" />
                Browse Live News
              </Button>
            </Link>
          </div>
        </motion.div>

        {/* Floating AI Elements */}
        <motion.div 
          animate={{ y: [0, -10, 0] }}
          transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
          className="absolute top-1/4 left-[10%] hidden lg:block opacity-40"
        >
          <div className="bg-primary/20 p-4 rounded-2xl backdrop-blur-xl border border-primary/30">
            <Brain className="h-12 w-12 text-primary" />
          </div>
        </motion.div>
      </section>

      {/* Features Grid */}
      <section className="border-t border-border/40 bg-background/50 py-24">
        <div className="container max-w-screen-xl px-4">
          <div className="grid md:grid-cols-3 gap-8">
            <div className="glass p-6 rounded-2xl space-y-4">
              <div className="h-12 w-12 bg-primary/20 rounded-xl flex items-center justify-center">
                <BookOpen className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-bold">Live Ingestion</h3>
              <p className="text-muted-foreground">Automatically fetches the latest headlines from NewsAPI and GNews using async microservices.</p>
            </div>
            <div className="glass p-6 rounded-2xl space-y-4">
              <div className="h-12 w-12 bg-primary/20 rounded-xl flex items-center justify-center">
                <Brain className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-bold">NLP Pipeline</h3>
              <p className="text-muted-foreground">Cleans text and extracts Named Entities using spaCy for high-quality quiz subjects.</p>
            </div>
            <div className="glass p-6 rounded-2xl space-y-4">
              <div className="h-12 w-12 bg-primary/20 rounded-xl flex items-center justify-center">
                <Sparkles className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-bold">Generative AI</h3>
              <p className="text-muted-foreground">Uses T5 for advanced Question Generation and BERT for plausible distractor generation.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
