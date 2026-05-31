"use client";

import { useEffect, useState } from "react";
import { newsService } from "@/services/news";
import { NewsCard } from "@/components/dashboard/NewsCard";
import { Input } from "@/components/ui/input";
import { Search, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NewsFeedPage() {
  const [articles, setArticles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const fetchNews = async () => {
    try {
      const data = await newsService.getLatestNews(30);
      setArticles(data);
    } catch (error) {
      console.error("Failed to fetch news", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchNews();
    
    // Auto refresh every 30 seconds
    const interval = setInterval(() => {
      fetchNews();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const handleManualRefresh = () => {
    setRefreshing(true);
    fetchNews();
  };

  const filteredArticles = articles.filter(a => 
    a.title?.toLowerCase().includes(search.toLowerCase()) || 
    a.content?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="container max-w-screen-2xl p-6 space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Live News Feed</h1>
          <p className="text-muted-foreground">Real-time articles ready for AI quiz generation.</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="relative w-full md:w-64">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search news..."
              className="pl-8 bg-background/50"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Button variant="outline" size="icon" onClick={handleManualRefresh} disabled={refreshing}>
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex h-[40vh] items-center justify-center">
          <RefreshCw className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filteredArticles.map((article, index) => (
            <NewsCard key={article.article_id} article={article} delay={index * 0.05} />
          ))}
          
          {filteredArticles.length === 0 && (
            <div className="col-span-full py-12 text-center text-muted-foreground border border-dashed rounded-lg">
              No news articles found matching your search.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
