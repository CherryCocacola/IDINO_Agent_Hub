"use client";

import {
  Plus,
  Trash2,
  Send,
  Square,
  Loader2,
  MessageSquare,
  Wifi,
  WifiOff,
  AlertCircle,
  FileText,
  Settings2,
  Sparkles,
} from "lucide-react";
import { useState, useRef, useEffect, useCallback, KeyboardEvent } from "react";

import { ChatMessage, type Citation } from "@/components/chat/chat-message";
import { DocumentScopeModal } from "@/components/chat/document-scope-modal";
import apiClient from "@/lib/api/client";
import { useAuth } from "@/lib/hooks/use-auth";
import { useToast } from "@/lib/hooks/use-toast";
import { cn } from "@/lib/utils/cn";

// ── Types ──────────────────────────────────────────────────────────────────

interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  scopedDocumentIds: string[];
  searchScope?: string;
}

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations?: Citation[];
  modelUsed?: string;
  hallucinationScore?: number;
  timestamp: string;
}

type ConnectionState = "connecting" | "connected" | "disconnected" | "error";

// ── Constants ──────────────────────────────────────────────────────────────

// WebSocket 연결 주소: Nginx 리버스 프록시를 경유하여 연결한다.
// Nginx가 /api/v1/chat/ws/ 경로에 대해 WebSocket 업그레이드를 처리하므로
// 현재 접속 중인 호스트(IP/도메인)와 동일한 주소를 사용하면
// localhost가 아닌 외부 IP에서도 정상 동작한다.
// WebSocket은 Next.js rewrite를 통과하지 못하므로 Nginx(같은 host)를 직접 사용
const WS_BASE =
  typeof window !== "undefined"
    ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.hostname}:8041/api/v1`
    : "";

// ── 프로바이더 라벨 매핑 ─────────────────────────────────────────────────
const PROVIDER_SHORT_LABELS: Record<string, string> = {
  openai: "GPT",
  azure_openai: "Azure",
  anthropic: "Claude",
  gemini: "Gemini",
  vllm: "vLLM",
};

/** LLM 프로바이더 값을 짧은 라벨로 변환한다 (null이면 빈 문자열) */
function getProviderTag(provider: string | null | undefined): string {
  if (!provider) return "";
  return PROVIDER_SHORT_LABELS[provider] || provider;
}

// ── Component ──────────────────────────────────────────────────────────────

export default function ChatPage() {
  const { accessToken } = useAuth();
  const { addToast } = useToast();

  // Session state
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessionsLoading, setSessionsLoading] = useState(true);

  // Message state
  const [messages, setMessages] = useState<Message[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [inputText, setInputText] = useState("");

  // Streaming state
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const streamingRef = useRef<string>("");
  const wsMetaRef = useRef<{ citations?: unknown; metadata?: Record<string, unknown> }>({});

  // 로딩/상태 표시: 메시지 전송 후 응답이 올 때까지의 상태를 관리한다
  // isWaitingResponse: 사용자가 메시지를 보낸 후 ~ 응답 스트리밍 시작 전까지 true
  // statusText: 서버가 보내는 상태 메시지 (예: "문서 검색 중...")를 표시한다
  const [isWaitingResponse, setIsWaitingResponse] = useState(false);
  const [statusText, setStatusText] = useState("");

  // WebSocket state
  const [connectionState, setConnectionState] = useState<ConnectionState>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);

  // Document scope modal
  const [showScopeModal, setShowScopeModal] = useState(false);
  const [_pendingScopeIds, setPendingScopeIds] = useState<string[]>([]);

  // Deep Search (Agentic RAG) toggle
  const [deepSearch, setDeepSearch] = useState(false);

  // Agent selection
  const [chatAgents, setChatAgents] = useState<
    {
      id: string;
      name: string;
      description: string | null;
      llm_provider?: string | null;
      llm_model?: string | null;
    }[]
  >([]);
  const [selectedChatAgentId, setSelectedChatAgentId] = useState<string | null>(null);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // ── Load sessions ────────────────────────────────────────────────────────

  // 세션 목록을 API에서 가져온다
  // 백엔드 응답 형식: { items: [...], total, page, size }
  const loadSessions = useCallback(async () => {
    try {
      setSessionsLoading(true);
      const data = await apiClient.get<{ items: Record<string, unknown>[]; total: number }>(
        "/chat/sessions",
      );
      // 백엔드 snake_case → 프론트 camelCase 변환
      const mapped: ChatSession[] = (data.items ?? []).map((s) => ({
        id: s.id as string,
        title: (s.title as string) || "채팅",
        createdAt: (s.created_at as string) || "",
        updatedAt: (s.updated_at as string) || "",
        scopedDocumentIds: (s.scoped_document_ids as string[]) || [],
      }));
      setSessions(mapped);
    } catch {
      addToast("채팅 세션을 불러오지 못했습니다.", "error");
    } finally {
      setSessionsLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // Load chatbot agents
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const data = await apiClient.get<{ items: typeof chatAgents }>("/agents", {
          agent_type: "chatbot",
        });
        setChatAgents(data.items || []);
      } catch {
        /* ignore */
      }
    };
    loadAgents();
  }, []);

  // ── Load messages for active session ─────────────────────────────────────

  // 특정 세션의 메시지 목록을 API에서 가져온다
  // 백엔드 응답 형식: { items: [...], total, page, size }
  const loadMessages = useCallback(
    async (sessionId: string) => {
      try {
        setMessagesLoading(true);
        const data = await apiClient.get<{ items: Record<string, unknown>[]; total: number }>(
          `/chat/sessions/${sessionId}/messages`,
        );
        // 백엔드 snake_case → 프론트 camelCase 변환
        const mapped: Message[] = (data.items ?? []).map((m) => ({
          id: m.id as string,
          role: m.role as "user" | "assistant" | "system",
          content: (m.content as string) || "",
          citations: Array.isArray(m.citations)
            ? (m.citations as any[]).map((c: any) => ({
                id: c.document_id || c.id || "",
                documentName: c.document_name || c.documentName || "알 수 없는 문서",
                chunkText: c.snippet || c.chunkText || c.content || "",
                pageNumber: c.page_number ?? c.pageNumber ?? null,
                score: c.relevance_score ?? c.score ?? null,
              }))
            : undefined,
          modelUsed: m.model_used as string | undefined,
          hallucinationScore: m.hallucination_score as number | undefined,
          timestamp: (m.created_at as string) || "",
        }));
        setMessages(mapped);
      } catch {
        addToast("메시지를 불러오지 못했습니다.", "error");
      } finally {
        setMessagesLoading(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  useEffect(() => {
    if (activeSessionId) {
      loadMessages(activeSessionId);
    } else {
      setMessages([]);
    }
  }, [activeSessionId, loadMessages]);

  // ── Auto-scroll to bottom ───────────────────────────────────────────────

  // 메시지 목록, 스트리밍 내용, 상태 텍스트가 변경될 때 자동으로 스크롤을 하단으로 이동
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent, statusText]);

  // ── WebSocket connection ─────────────────────────────────────────────────

  const connectWebSocket = useCallback(
    (sessionId: string) => {
      if (wsRef.current) {
        wsRef.current.close();
      }

      setConnectionState("connecting");

      // Connect without token in URL — authenticate via first message
      const wsUrl = `${WS_BASE}/chat/ws/${sessionId}`;
      console.log("[WS] Connecting to:", wsUrl);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("[WS] Connected, sending auth");
        // Send auth message immediately after connection opens
        ws.send(JSON.stringify({ type: "auth", token: accessToken }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("[WS]", data.type, data);

          // 서버에서 보내는 인증 확인 메시지 처리
          if (data.type === "status" && data.data?.message === "Authenticated. Ready to chat.") {
            setConnectionState("connected");
            return;
          }

          // 서버에서 보내는 상태 메시지 처리 (예: "Searching documents...", "Generating response...")
          // 사용자에게 현재 서버가 어떤 작업을 하고 있는지 알려주는 역할
          if (data.type === "status") {
            const statusMap: Record<string, string> = {
              "Loading session context...": "세션 컨텍스트 로딩 중...",
              "Searching documents...": "문서 검색 중...",
              "Generating response...": "응답 생성 중...",
            };
            const serverMsg = data.data?.message || data.message || "";
            setStatusText(statusMap[serverMsg] || serverMsg);
            return;
          }

          if (data.type === "stream_start") {
            setIsWaitingResponse(false);
            setStatusText("");
            setIsStreaming(true);
            setStreamingContent("");
            streamingRef.current = "";
          } else if (data.type === "stream_chunk" || data.type === "chunk") {
            // 백엔드는 "chunk"로 보냄, 프론트 호환 "stream_chunk"도 처리
            const text = data.content || data.data?.text || "";
            if (text) {
              // 첫 chunk가 오면 스트리밍 시작
              if (!isStreaming) {
                setIsWaitingResponse(false);
                setStatusText("");
                setIsStreaming(true);
              }
              streamingRef.current += text;
              setStreamingContent(streamingRef.current);
            }
          } else if (data.type === "citations") {
            // 백엔드 snake_case → 프론트 camelCase 필드 매핑
            wsMetaRef.current.citations = (data.data?.citations || []).map((c: any) => ({
              id: c.document_id || c.id || "",
              documentName: c.document_name || c.documentName || "알 수 없는 문서",
              chunkText: c.snippet || c.chunkText || c.content || "",
              pageNumber: c.page_number ?? c.pageNumber ?? null,
              score: c.relevance_score ?? c.score ?? null,
            }));
          } else if (data.type === "metadata") {
            wsMetaRef.current.metadata = data.data;
          } else if (data.type === "stream_end" || data.type === "done") {
            // 백엔드는 "done"으로 보냄
            const finalMessage: Message = {
              id: data.data?.message_id || data.message_id || `msg-${Date.now()}`,
              role: "assistant",
              content: streamingRef.current,
              citations: wsMetaRef.current.citations as Message["citations"],
              modelUsed: wsMetaRef.current.metadata?.model_used as string,
              hallucinationScore: wsMetaRef.current.metadata?.hallucination_score as number,
              timestamp: new Date().toLocaleTimeString(),
            };
            setMessages((prev) => [...prev, finalMessage]);
            setIsStreaming(false);
            setIsWaitingResponse(false);
            setStatusText("");
            setStreamingContent("");
            streamingRef.current = "";
            wsMetaRef.current = {};
          } else if (data.type === "error") {
            addToast(data.message || "오류가 발생했습니다.", "error");
            setIsStreaming(false);
            setIsWaitingResponse(false);
            setStatusText("");
            setStreamingContent("");
            streamingRef.current = "";
          }
        } catch {
          // ignore parse errors
        }
      };

      ws.onclose = (e) => {
        console.log("[WS] Closed:", e.code, e.reason);
        setConnectionState("disconnected");
      };

      ws.onerror = (e) => {
        console.error("[WS] Error:", e);
        setConnectionState("error");
      };
    },
    [accessToken, addToast],
  );

  // Connect WebSocket when active session changes
  useEffect(() => {
    if (activeSessionId) {
      connectWebSocket(activeSessionId);
    }
    return () => {
      wsRef.current?.close();
    };
  }, [activeSessionId, connectWebSocket]);

  // ── Create new session ───────────────────────────────────────────────────

  const handleNewChat = () => {
    setShowScopeModal(true);
  };

  // 문서 선택 확인 후 새 세션을 생성한다
  // 백엔드 POST /chat/sessions는 ChatSessionResponse 객체를 직접 반환한다 (wrapper 없음)
  // 백엔드 필드명은 snake_case (created_at, updated_at, scoped_document_ids)
  // generatedTitle: 선택된 문서명으로 자동 생성된 세션 제목
  const handleScopeConfirm = async (selectedIds: string[], generatedTitle: string) => {
    setShowScopeModal(false);
    setPendingScopeIds(selectedIds);

    try {
      const raw = await apiClient.post<Record<string, unknown>>("/chat/sessions", {
        scoped_document_ids: selectedIds,
        title: generatedTitle,
        agent_id: selectedChatAgentId || undefined,
      });

      // 백엔드 snake_case → 프론트 camelCase 변환
      const newSession: ChatSession = {
        id: raw.id as string,
        title: (raw.title as string) || generatedTitle,
        createdAt: (raw.created_at as string) || new Date().toISOString(),
        updatedAt: (raw.updated_at as string) || new Date().toISOString(),
        scopedDocumentIds: (raw.scoped_document_ids as string[]) || selectedIds,
      };
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
    } catch {
      addToast("채팅 세션 생성에 실패했습니다.", "error");
    }
  };

  // ── Delete session ───────────────────────────────────────────────────────

  const handleDeleteSession = async (sessionId: string) => {
    if (!confirm("이 채팅 세션을 삭제하시겠습니까?")) return;

    try {
      await apiClient.delete(`/chat/sessions/${sessionId}`);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
      }
      addToast("세션이 삭제되었습니다.", "success");
    } catch {
      addToast("세션 삭제에 실패했습니다.", "error");
    }
  };

  // ── Send message ─────────────────────────────────────────────────────────

  const handleSendMessage = useCallback(() => {
    const text = inputText.trim();
    // 입력값이 없거나, 세션이 없거나, 스트리밍/응답 대기 중이면 전송하지 않는다
    if (!text || !activeSessionId || isStreaming || isWaitingResponse) return;

    // Add user message locally
    const userMessage: Message = {
      id: `msg-user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputText("");

    // Auto-resize textarea back
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    // 메시지 전송 후 응답 대기 상태로 전환 (로딩 표시 시작)
    setIsWaitingResponse(true);
    setStatusText("요청 전송 중...");

    // WebSocket으로 전송, 연결이 안 되어있으면 REST API로 대체
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "message",
          content: text,
          options: deepSearch ? { deep_search: true } : undefined,
        }),
      );
    } else {
      // REST API로 대체 전송
      sendViaRest(text);
    }
  }, [inputText, activeSessionId, isStreaming, isWaitingResponse, deepSearch]);

  // REST API를 통한 메시지 전송 (WebSocket 연결 실패 시 대체 수단)
  const sendViaRest = async (text: string) => {
    if (!activeSessionId) return;

    setIsStreaming(true);
    setStatusText("응답 생성 중...");
    console.log("[REST] Sending message:", text);
    try {
      const data = await apiClient.post<Record<string, unknown>>(
        `/chat/sessions/${activeSessionId}/messages`,
        { content: text },
      );
      console.log("[REST] Response:", data);

      // 응답 구조: { message: { id, content, role, ... } }
      const msg = (data.message || data) as Record<string, unknown>;
      if (msg && msg.content) {
        const assistantMsg: Message = {
          id: (msg.id as string) || `msg-${Date.now()}`,
          role: "assistant",
          content: (msg.content as string) || "",
          citations: Array.isArray(msg.citations)
            ? (msg.citations as any[]).map((c: any) => ({
                id: c.document_id || c.id || "",
                documentName: c.document_name || c.documentName || "알 수 없는 문서",
                chunkText: c.snippet || c.chunkText || c.content || "",
                pageNumber: c.page_number ?? c.pageNumber ?? null,
                score: c.relevance_score ?? c.score ?? null,
              }))
            : undefined,
          modelUsed: (msg.model_used as string) || undefined,
          hallucinationScore: (msg.hallucination_score as number) || undefined,
          timestamp: (msg.created_at as string) || new Date().toLocaleTimeString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } else {
        // 응답에서 메시지를 못 찾으면 세션 메시지 새로고침
        console.log("[REST] No message found, reloading messages");
        loadMessages(activeSessionId);
      }
    } catch (err) {
      console.error("[REST] Error:", err);
      // 에러 시에도 메시지 새로고침 시도 (서버는 저장했을 수 있음)
      loadMessages(activeSessionId);
    } finally {
      setIsStreaming(false);
      setIsWaitingResponse(false);
      setStatusText("");
    }
  };

  // ── Stop streaming ──────────────────────────────────────────────────────

  const handleStopStreaming = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "stop" }));
    }
    setIsStreaming(false);
    setIsWaitingResponse(false);
    setStatusText("");
    if (streamingRef.current) {
      const partialMessage: Message = {
        id: `msg-partial-${Date.now()}`,
        role: "assistant",
        content: streamingRef.current + " [stopped]",
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, partialMessage]);
      setStreamingContent("");
      streamingRef.current = "";
    }
  }, []);

  // ── Textarea auto-resize + keyboard handling ─────────────────────────────

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(e.target.value);
    // Auto-resize
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  };

  // ── Connection state indicator ───────────────────────────────────────────

  const connectionIndicator = () => {
    switch (connectionState) {
      case "connecting":
        return (
          <span className="flex items-center gap-1.5 text-xs text-yellow-600">
            <Loader2 className="h-3 w-3 animate-spin" />
            연결 중...
          </span>
        );
      case "connected":
        return (
          <span className="flex items-center gap-1.5 text-xs text-green-600">
            <Wifi className="h-3 w-3" />
            연결됨
          </span>
        );
      case "disconnected":
        return (
          <span className="flex items-center gap-1.5 text-xs text-gray-400">
            <WifiOff className="h-3 w-3" />
            연결 끊김
          </span>
        );
      case "error":
        return (
          <span className="flex items-center gap-1.5 text-xs text-red-600">
            <AlertCircle className="h-3 w-3" />
            연결 오류
          </span>
        );
    }
  };

  // Active session
  const activeSession = sessions.find((s) => s.id === activeSessionId);

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-0 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      {/* ── Left sidebar: Chat sessions ────────────────────────────────── */}
      <div className="flex w-72 shrink-0 flex-col border-r border-gray-200 bg-gray-50">
        {/* New Chat button */}
        <div className="border-b border-gray-200 p-3">
          <button
            onClick={handleNewChat}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />새 채팅
          </button>
          {chatAgents.length > 0 && (
            <select
              value={selectedChatAgentId || ""}
              onChange={(e) => setSelectedChatAgentId(e.target.value || null)}
              className="mt-2 w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-700 focus:border-blue-400 focus:outline-none"
            >
              <option value="">기본 에이전트</option>
              {chatAgents.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                  {getProviderTag(a.llm_provider) ? ` [${getProviderTag(a.llm_provider)}]` : ""}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Session list */}
        <div className="flex-1 overflow-y-auto">
          {sessionsLoading ? (
            <div className="flex items-center justify-center py-10">
              <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="px-4 py-10 text-center text-sm text-gray-400">채팅 세션이 없습니다</div>
          ) : (
            <div className="py-1">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => setActiveSessionId(session.id)}
                  className={cn(
                    "group flex cursor-pointer items-center gap-3 border-l-2 px-4 py-3 transition-colors",
                    activeSessionId === session.id
                      ? "border-l-blue-600 bg-white"
                      : "border-l-transparent hover:bg-gray-100",
                  )}
                >
                  <MessageSquare
                    className={cn(
                      "h-4 w-4 shrink-0",
                      activeSessionId === session.id ? "text-blue-600" : "text-gray-400",
                    )}
                  />
                  <div className="min-w-0 flex-1">
                    <p
                      className={cn(
                        "truncate text-sm font-medium",
                        activeSessionId === session.id ? "text-gray-900" : "text-gray-700",
                      )}
                    >
                      {session.title}
                    </p>
                    <p className="mt-0.5 text-[10px] text-gray-400">
                      {new Date(session.updatedAt).toLocaleDateString()}
                    </p>
                  </div>

                  {/* Active indicator */}
                  {activeSessionId === session.id && (
                    <span className="h-2 w-2 shrink-0 rounded-full bg-blue-600" />
                  )}

                  {/* Delete button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteSession(session.id);
                    }}
                    className="shrink-0 rounded p-1 text-gray-300 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-red-50 hover:text-red-500"
                    aria-label="세션 삭제"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Main chat area ──────────────────────────────────────────────── */}
      <div className="flex flex-1 flex-col">
        {activeSessionId ? (
          <>
            {/* Chat header */}
            <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
              <div className="flex items-center gap-3">
                <MessageSquare className="h-5 w-5 text-blue-600" />
                <div>
                  <h2 className="text-sm font-semibold text-gray-900">
                    {activeSession?.title ?? "Chat"}
                  </h2>
                  {activeSession?.scopedDocumentIds &&
                    activeSession.scopedDocumentIds.length > 0 && (
                      <p className="flex items-center gap-1 text-[10px] text-gray-400">
                        <FileText className="h-3 w-3" />
                        {activeSession.scopedDocumentIds.length}개 문서 범위 설정됨
                      </p>
                    )}
                </div>
              </div>
              <div className="flex items-center gap-3">
                {connectionIndicator()}
                <button
                  onClick={() => setShowScopeModal(true)}
                  className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                  aria-label="세션 설정"
                >
                  <Settings2 className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Messages area */}
            <div className="flex-1 overflow-y-auto px-4 py-4">
              {messagesLoading ? (
                <div className="flex items-center justify-center py-20">
                  <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                </div>
              ) : messages.length === 0 && !isStreaming ? (
                <div className="flex flex-col items-center justify-center py-20">
                  <MessageSquare className="h-12 w-12 text-gray-200" />
                  <p className="mt-4 text-sm font-medium text-gray-500">대화를 시작하세요</p>
                  <p className="mt-1 text-xs text-gray-400">선택한 문서에 대해 질문해보세요</p>
                </div>
              ) : (
                <div className="mx-auto max-w-3xl space-y-1">
                  {messages.map((msg) => (
                    <ChatMessage
                      key={msg.id}
                      role={msg.role}
                      content={msg.content}
                      citations={msg.citations}
                      modelUsed={msg.modelUsed}
                      hallucinationScore={msg.hallucinationScore}
                      timestamp={msg.timestamp}
                    />
                  ))}

                  {/* 스트리밍 중인 응답 표시 */}
                  {isStreaming && (
                    <ChatMessage role="assistant" content={streamingContent} isStreaming={true} />
                  )}

                  {/* 응답 대기 중 로딩 표시: 메시지 전송 후 ~ 스트리밍 시작 전까지 보여준다 */}
                  {isWaitingResponse && !isStreaming && (
                    <div className="flex items-start gap-3 py-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-100">
                        <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                      </div>
                      <div className="flex flex-col gap-1 pt-1">
                        <div className="flex items-center gap-2">
                          <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-blue-500" />
                          <span className="text-sm text-gray-500">
                            {statusText || "응답 대기 중..."}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>

            {/* Input area */}
            <div className="border-t border-gray-200 px-4 py-3">
              {/* Deep Search toggle */}
              <div className="mx-auto mb-2 flex max-w-3xl items-center gap-2">
                <button
                  type="button"
                  onClick={() => setDeepSearch((v) => !v)}
                  className={cn(
                    "flex items-center gap-1.5 rounded-lg border px-3 py-1 text-xs font-medium transition-colors",
                    deepSearch
                      ? "border-blue-300 bg-blue-50 text-blue-800"
                      : "border-gray-200 bg-white text-gray-500 hover:border-gray-300 hover:text-gray-700",
                  )}
                  title="심층 검색: AI가 쿼리를 분석하고 더 정확한 결과를 찾습니다"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  심층 검색
                  {deepSearch && (
                    <span className="ml-1 inline-block h-1.5 w-1.5 rounded-full bg-blue-500" />
                  )}
                </button>
                {deepSearch && (
                  <span className="text-xs text-gray-400">
                    AI가 더 정확한 검색 결과를 찾습니다
                  </span>
                )}
              </div>
              <div className="mx-auto flex max-w-3xl items-end gap-3">
                <div className="relative flex-1">
                  <textarea
                    ref={textareaRef}
                    value={inputText}
                    onChange={handleTextareaChange}
                    onKeyDown={handleKeyDown}
                    placeholder="메시지를 입력하세요... (Shift+Enter로 줄바꿈)"
                    rows={1}
                    className="w-full resize-none rounded-xl border border-gray-300 bg-gray-50 px-4 py-3 pr-4 text-sm text-gray-900 placeholder-gray-400 transition-colors focus:border-blue-400 focus:bg-white focus:ring-1 focus:ring-blue-100 focus:outline-none"
                    style={{ maxHeight: "200px" }}
                    disabled={isStreaming || isWaitingResponse}
                  />
                </div>

                {isStreaming || isWaitingResponse ? (
                  <button
                    onClick={handleStopStreaming}
                    className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-red-600 text-white transition-colors hover:bg-red-700"
                    aria-label="생성 중지"
                  >
                    <Square className="h-4 w-4" />
                  </button>
                ) : (
                  <button
                    onClick={handleSendMessage}
                    disabled={!inputText.trim() || isStreaming || isWaitingResponse}
                    className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                    aria-label="메시지 전송"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          </>
        ) : (
          /* No session selected */
          <div className="flex flex-1 flex-col items-center justify-center">
            <MessageSquare className="h-16 w-16 text-gray-200" />
            <h2 className="mt-4 text-lg font-medium text-gray-700">다중 문서 Q&A 채팅</h2>
            <p className="mt-2 max-w-sm text-center text-sm text-gray-400">
              기존 채팅 세션을 선택하거나 새로 생성하여 문서에 대해 질문하세요.
            </p>
            <button
              onClick={handleNewChat}
              className="mt-6 flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />새 채팅
            </button>
          </div>
        )}
      </div>

      {/* ── Document Scope Modal ────────────────────────────────────────── */}
      <DocumentScopeModal
        open={showScopeModal}
        onClose={() => setShowScopeModal(false)}
        onConfirm={handleScopeConfirm}
        initialSelectedIds={activeSession?.scopedDocumentIds ?? []}
        title={activeSessionId ? "문서 범위 수정" : "채팅할 문서 선택"}
        description={
          activeSessionId
            ? "이 채팅 세션의 문서 범위를 수정합니다."
            : "대화할 문서를 선택하세요. 여러 프로젝트의 문서를 선택할 수 있습니다."
        }
      />
    </div>
  );
}
