"use client";

import { format } from "date-fns";
import DOMPurify from "dompurify";
import { Search, Loader2, Clock, FileText, MessageSquare, X } from "lucide-react";
import { useState, useEffect, useCallback } from "react";
// XSS 방지를 위해 서버에서 반환된 HTML을 렌더링하기 전에 반드시 새니타이즈(sanitize) 처리해야 합니다.

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiClient } from "@/lib/api/client";
import { useToast } from "@/lib/hooks/use-toast";

// ---------- Types ----------

interface SearchScopeOption {
  id: string;
  name: string;
  location_path: string;
}

interface ChunkResult {
  id: string;
  document_name: string;
  content: string;
  score: number;
  highlights: string[];
  metadata?: Record<string, unknown>;
}

interface ChatResult {
  answer: string;
  citations: {
    document_name: string;
    content: string;
    page?: number;
  }[];
}

interface SearchHistoryEntry {
  id: string;
  query: string;
  search_type: string;
  scope_name: string;
  timestamp: string;
  result_count: number;
}

type SearchType = "hybrid" | "chatbot" | "qa" | "keyword";

// ---------- Component ----------

export default function SearchTestPage() {
  const { addToast } = useToast();

  // Scopes
  const [scopes, setScopes] = useState<SearchScopeOption[]>([]);
  const [selectedScopeId, setSelectedScopeId] = useState<string>("");
  const [scopesLoading, setScopesLoading] = useState(true);

  // Search
  const [searchType, setSearchType] = useState<SearchType>("hybrid");
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);

  // Results
  const [chunkResults, setChunkResults] = useState<ChunkResult[]>([]);
  const [chatResult, setChatResult] = useState<ChatResult | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  // History
  const [history, setHistory] = useState<SearchHistoryEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [showHistory, setShowHistory] = useState(true);

  // ---------- Fetch scopes ----------

  const fetchScopes = useCallback(async () => {
    try {
      const data = await apiClient.get<SearchScopeOption[]>("/search-scopes/options");
      setScopes(data);
      if (data.length > 0) setSelectedScopeId(data[0].id);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to load scopes", "error");
    } finally {
      setScopesLoading(false);
    }
  }, [addToast]);

  // ---------- Fetch history ----------

  const fetchHistory = useCallback(async () => {
    try {
      const data = await apiClient.get<SearchHistoryEntry[]>("/search/history");
      setHistory(data);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to load search history", "error");
    } finally {
      setHistoryLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchScopes();
    fetchHistory();
  }, [fetchScopes, fetchHistory]);

  // ---------- Search ----------

  const handleSearch = async () => {
    if (!query.trim()) {
      addToast("Please enter a search query", "error");
      return;
    }
    if (!selectedScopeId) {
      addToast("Please select a search scope", "error");
      return;
    }

    setSearching(true);
    setHasSearched(true);
    setChunkResults([]);
    setChatResult(null);

    try {
      if (searchType === "chatbot" || searchType === "qa") {
        const endpoint = searchType === "qa" ? "/search/qa" : "/search/chatbot";
        const result = await apiClient.post<ChatResult>(endpoint, {
          search_scope_id: selectedScopeId,
          query: query.trim(),
        });
        setChatResult(result);
      } else {
        const endpoint = searchType === "keyword" ? "/search/keyword" : "/search/test";
        const result = await apiClient.post<ChunkResult[]>(endpoint, {
          search_scope_id: selectedScopeId,
          query: query.trim(),
        });
        setChunkResults(result);
      }
      fetchHistory();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Search failed", "error");
    } finally {
      setSearching(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSearch();
  };

  const loadFromHistory = (entry: SearchHistoryEntry) => {
    setQuery(entry.query);
    setSearchType(entry.search_type as SearchType);
  };

  // ---------- Render ----------

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Main content */}
      <div className="flex-1 overflow-auto">
        <div className="space-y-6 p-6">
          <h1 className="text-3xl font-bold">Search Test</h1>

          {/* Scope selector */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Search Scope</label>
            {scopesLoading ? (
              <Skeleton className="h-10 w-full max-w-md" />
            ) : (
              <Select value={selectedScopeId} onValueChange={setSelectedScopeId}>
                <SelectTrigger className="max-w-md">
                  <SelectValue placeholder="Select a scope" />
                </SelectTrigger>
                <SelectContent>
                  {scopes.map((scope) => (
                    <SelectItem key={scope.id} value={scope.id}>
                      {scope.name} - {scope.location_path}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>

          {/* Search type tabs */}
          <Tabs value={searchType} onValueChange={(val) => setSearchType(val as SearchType)}>
            <TabsList>
              <TabsTrigger value="hybrid">Hybrid</TabsTrigger>
              <TabsTrigger value="chatbot">Chatbot</TabsTrigger>
              <TabsTrigger value="qa">Q&A</TabsTrigger>
              <TabsTrigger value="keyword">Keyword</TabsTrigger>
            </TabsList>
          </Tabs>

          {/* Query input */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
              <Input
                placeholder={
                  searchType === "chatbot" || searchType === "qa"
                    ? "Ask a question..."
                    : "Enter search keywords..."
                }
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                className="pl-9"
              />
            </div>
            <Button onClick={handleSearch} disabled={searching}>
              {searching ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Search
                </>
              )}
            </Button>
          </div>

          {/* Results */}
          {searching ? (
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-32 w-full rounded-lg" />
              ))}
            </div>
          ) : hasSearched ? (
            <div className="space-y-4">
              {/* Chunk results (hybrid / keyword) */}
              {(searchType === "hybrid" || searchType === "keyword") && (
                <>
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold">Results ({chunkResults.length})</h2>
                  </div>

                  {chunkResults.length === 0 ? (
                    <div className="text-muted-foreground py-8 text-center">
                      No results found for your query.
                    </div>
                  ) : (
                    chunkResults.map((chunk) => (
                      <Card key={chunk.id}>
                        <CardContent className="p-4">
                          <div className="mb-2 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <FileText className="text-muted-foreground h-4 w-4" />
                              <span className="font-medium">{chunk.document_name}</span>
                            </div>
                            <Badge variant="outline">
                              Score: {(chunk.score * 100).toFixed(1)}%
                            </Badge>
                          </div>
                          <p className="text-muted-foreground text-sm whitespace-pre-wrap">
                            {chunk.content}
                          </p>
                          {chunk.highlights.length > 0 && (
                            <div className="mt-3 space-y-1">
                              <span className="text-muted-foreground text-xs font-medium">
                                Highlights:
                              </span>
                              {chunk.highlights.map((hl, idx) => (
                                <div
                                  key={idx}
                                  className="rounded bg-yellow-50 px-2 py-1 text-xs dark:bg-yellow-900/20"
                                  dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(hl) }}
                                />
                              ))}
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))
                  )}
                </>
              )}

              {/* Chat results (chatbot / QA) */}
              {(searchType === "chatbot" || searchType === "qa") && chatResult && (
                <>
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="flex items-center gap-2 text-base">
                        <MessageSquare className="h-4 w-4" />
                        Answer
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm whitespace-pre-wrap">{chatResult.answer}</p>
                    </CardContent>
                  </Card>

                  {chatResult.citations.length > 0 && (
                    <div>
                      <h3 className="text-muted-foreground mb-3 text-sm font-semibold">
                        Citations ({chatResult.citations.length})
                      </h3>
                      <div className="grid gap-3 sm:grid-cols-2">
                        {chatResult.citations.map((citation, idx) => (
                          <Card key={idx}>
                            <CardContent className="p-4">
                              <div className="mb-2 flex items-center gap-2">
                                <FileText className="text-muted-foreground h-4 w-4" />
                                <span className="text-sm font-medium">
                                  {citation.document_name}
                                </span>
                                {citation.page && (
                                  <Badge variant="outline" className="text-xs">
                                    p.{citation.page}
                                  </Badge>
                                )}
                              </div>
                              <p className="text-muted-foreground line-clamp-4 text-xs">
                                {citation.content}
                              </p>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}

                  {!chatResult && (
                    <div className="text-muted-foreground py-8 text-center">
                      No answer could be generated for your query.
                    </div>
                  )}
                </>
              )}
            </div>
          ) : (
            <div className="text-muted-foreground py-16 text-center">
              Select a scope, choose a search type, and enter a query to begin.
            </div>
          )}
        </div>
      </div>

      {/* Right sidebar -- search history */}
      {showHistory && (
        <div className="w-72 flex-shrink-0 border-l">
          <div className="flex items-center justify-between p-4">
            <h2 className="text-muted-foreground text-sm font-semibold tracking-wider uppercase">
              Recent Queries
            </h2>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={() => setShowHistory(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          <Separator />
          <ScrollArea className="h-[calc(100vh-8rem)]">
            <div className="p-2">
              {historyLoading ? (
                <div className="space-y-2">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : history.length === 0 ? (
                <p className="text-muted-foreground p-4 text-center text-sm">
                  No search history yet.
                </p>
              ) : (
                history.map((entry) => (
                  <button
                    key={entry.id}
                    className="hover:bg-muted w-full rounded-md p-3 text-left transition-colors"
                    onClick={() => loadFromHistory(entry)}
                  >
                    <p className="truncate text-sm font-medium">{entry.query}</p>
                    <div className="text-muted-foreground mt-1 flex items-center gap-2 text-xs">
                      <Badge variant="outline" className="px-1.5 py-0 text-xs">
                        {entry.search_type}
                      </Badge>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {format(new Date(entry.timestamp), "MM/dd HH:mm")}
                      </span>
                    </div>
                    <p className="text-muted-foreground mt-0.5 text-xs">
                      {entry.result_count} result(s) - {entry.scope_name}
                    </p>
                  </button>
                ))
              )}
            </div>
          </ScrollArea>
        </div>
      )}

      {/* History toggle (when hidden) */}
      {!showHistory && (
        <Button
          variant="outline"
          size="icon"
          className="fixed top-20 right-4 z-10"
          onClick={() => setShowHistory(true)}
        >
          <Clock className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
