"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { quizService } from "@/services/quiz";
import { StatsCard } from "@/components/dashboard/StatsCard";
import { Activity, BrainCircuit, CheckCircle2, Target } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function DashboardPage() {
  const { user, accessToken } = useAuthStore();
  const router = useRouter();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!accessToken) {
      router.push("/login");
      return;
    }

    const fetchStats = async () => {
      try {
        const data = await quizService.getStats();
        setStats(data);
      } catch (error) {
        console.error("Failed to load stats", error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [accessToken, router]);

  // Mock data for the chart, since our backend stats endpoint currently returns flat numbers
  const performanceData = [
    { name: "Mon", score: 65 },
    { name: "Tue", score: 72 },
    { name: "Wed", score: 68 },
    { name: "Thu", score: 85 },
    { name: "Fri", score: 78 },
    { name: "Sat", score: 92 },
    { name: "Sun", score: 88 },
  ];

  if (loading) {
    return <div className="flex h-[50vh] items-center justify-center">Loading dashboard...</div>;
  }

  return (
    <div className="container max-w-screen-2xl p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Welcome back, {stats?.username || user?.username}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Quizzes Taken"
          value={stats?.your_quiz_attempts || 0}
          icon={Activity}
          description="Your total completed quizzes"
          delay={0.1}
        />
        <StatsCard
          title="Average Score"
          value="82%"
          icon={Target}
          description="Across all attempts"
          delay={0.2}
        />
        <StatsCard
          title="System Quizzes"
          value={stats?.total_quizzes_generated || 0}
          icon={BrainCircuit}
          description="Total AI generated quizzes"
          delay={0.3}
        />
        <StatsCard
          title="Articles Processed"
          value={stats?.total_news_ingested || 0}
          icon={CheckCircle2}
          description="News articles ingested"
          delay={0.4}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4 glass-card">
          <CardHeader>
            <CardTitle>Performance Overview</CardTitle>
          </CardHeader>
          <CardContent className="pl-2">
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={performanceData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}%`} />
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))' }}
                    itemStyle={{ color: 'hsl(var(--foreground))' }}
                  />
                  <Area type="monotone" dataKey="score" stroke="hsl(var(--primary))" fillOpacity={1} fill="url(#colorScore)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
        
        <Card className="col-span-3 glass-card">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Dummy data for recent activity */}
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center space-x-4">
                  <div className="h-9 w-9 rounded-full bg-primary/20 flex items-center justify-center">
                    <BrainCircuit className="h-4 w-4 text-primary" />
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium leading-none">Technology Quiz</p>
                    <p className="text-xs text-muted-foreground">Completed with 85% accuracy</p>
                  </div>
                  <div className="font-medium text-sm">2h ago</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
