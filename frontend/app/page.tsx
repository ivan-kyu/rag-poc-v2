"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ChatPanel } from "@/components/ChatPanel";
import { PipelinePanel } from "@/components/PipelinePanel";
import { KnowledgeBasePanel } from "@/components/KnowledgeBasePanel";
import { EvalPanel } from "@/components/EvalPanel";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ChatMessage,
  DocumentSource,
  NodeName,
  NodeStates,
  PipelineConfig,
  RetrievedChunk,
} from "@/lib/types";
import { fetchDocuments, streamChat } from "@/lib/sseClient";

const DEFAULT_CONFIG: PipelineConfig = {
  hybrid: false,
  multi_query: false,
  hyde: false,
  rerank: false,
  route: false,
};

const DEFAULT_NODE_STATES: NodeStates = {
  classify: { status: "idle" },
  retrieve_naive: { status: "idle" },
  retrieve_hybrid: { status: "idle" },
  retrieve_multiquery: { status: "idle" },
  retrieve_hyde: { status: "idle" },
  rerank: { status: "idle" },
  generate: { status: "idle" },
};

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingToken, setStreamingToken] = useState("");
  const [config, setConfig] = useState<PipelineConfig>(DEFAULT_CONFIG);
  const [nodeStates, setNodeStates] = useState<NodeStates>(DEFAULT_NODE_STATES);
  const [retrievedChunks, setRetrievedChunks] = useState<RetrievedChunk[]>([]);
  const [rerankedChunks, setRerankedChunks] = useState<RetrievedChunk[]>([]);
  const [route, setRoute] = useState("");
  const [sources, setSources] = useState<DocumentSource[]>([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const abortRef = useRef<AbortController | null>(null);

  const loadDocuments = useCallback(async () => {
    try {
      const data = await fetchDocuments();
      setSources(data.sources || []);
      setTotalChunks(data.total_chunks || 0);
    } catch {
      // backend may not be up yet
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const resetPipelineState = () => {
    setNodeStates(DEFAULT_NODE_STATES);
    setRetrievedChunks([]);
    setRerankedChunks([]);
    setRoute("");
    setStreamingToken("");
  };

  const handleSubmit = async () => {
    if (!input.trim() || isStreaming) return;

    const question = input.trim();
    setInput("");
    setIsStreaming(true);
    resetPipelineState();

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
    };
    setMessages((prev) => [...prev, userMsg]);

    abortRef.current = new AbortController();

    try {
      let fullAnswer = "";
      let citations: ChatMessage["citations"] = [];
      let confidence = 0.8;
      let langsmithUrl = "";
      const currentNodeStates = { ...DEFAULT_NODE_STATES };

      for await (const event of streamChat(question, config, abortRef.current.signal)) {
        switch (event.type) {
          case "node_start": {
            const nodeName = event.data.node as NodeName;
            currentNodeStates[nodeName] = { ...currentNodeStates[nodeName], status: "running" };
            setNodeStates({ ...currentNodeStates });
            break;
          }
          case "node_end": {
            const nodeName = event.data.node as NodeName;
            currentNodeStates[nodeName] = {
              status: "done",
              chunks: event.data.chunks as RetrievedChunk[] | undefined,
            };
            setNodeStates({ ...currentNodeStates });

            if (event.data.chunks) {
              const chunks = event.data.chunks as RetrievedChunk[];
              if (nodeName === "rerank") {
                setRerankedChunks(chunks);
              } else if (nodeName.startsWith("retrieve_")) {
                setRetrievedChunks(chunks);
              }
            }
            if (event.data.route) setRoute(event.data.route as string);
            break;
          }
          case "token":
            fullAnswer += event.data.token as string;
            setStreamingToken(fullAnswer);
            break;
          case "done":
            fullAnswer = (event.data.answer as string) || fullAnswer;
            citations = (event.data.citations as ChatMessage["citations"]) || [];
            confidence = (event.data.confidence as number) || 0.8;
            langsmithUrl = (event.data.langsmith_url as string) || "";
            break;
        }
      }

      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: fullAnswer,
        citations,
        confidence,
        langsmithUrl,
        config,
        nodeStates: { ...currentNodeStates },
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setStreamingToken("");
    } catch (err: unknown) {
      if ((err as Error)?.name !== "AbortError") {
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: "Something went wrong. Is the backend running?",
          },
        ]);
      }
    } finally {
      setIsStreaming(false);
      setStreamingToken("");
    }
  };

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Left: Chat */}
      <div className="flex flex-col w-[420px] min-w-[320px] border-r">
        <div className="px-4 py-3 border-b flex items-center gap-2">
          <span className="font-semibold text-sm">RAG Explorer v2</span>
          <span className="text-xs text-muted-foreground">Python + LangGraph</span>
        </div>
        <div className="flex-1 overflow-hidden">
          <ChatPanel
            messages={messages}
            input={input}
            onInputChange={setInput}
            onSubmit={handleSubmit}
            isStreaming={isStreaming}
            streamingToken={streamingToken}
          />
        </div>
      </div>

      {/* Middle: Pipeline */}
      <div className="flex-1 flex flex-col border-r overflow-hidden">
        <div className="px-4 py-3 border-b">
          <span className="font-semibold text-sm">Pipeline</span>
        </div>
        <div className="flex-1 overflow-auto">
          <PipelinePanel
            nodeStates={nodeStates}
            config={config}
            onConfigChange={setConfig}
            retrievedChunks={retrievedChunks}
            rerankedChunks={rerankedChunks}
            route={route}
            isStreaming={isStreaming}
          />
        </div>
      </div>

      {/* Right: KB + Evals */}
      <div className="w-72 min-w-[260px] flex flex-col overflow-hidden">
        <div className="px-4 py-3 border-b">
          <span className="font-semibold text-sm">Knowledge Base</span>
        </div>
        <Tabs defaultValue="kb" className="flex-1 flex flex-col overflow-hidden">
          <TabsList className="mx-4 mt-3 self-start">
            <TabsTrigger value="kb">Files</TabsTrigger>
            <TabsTrigger value="evals">Evals</TabsTrigger>
          </TabsList>
          <TabsContent value="kb" className="flex-1 overflow-auto">
            <KnowledgeBasePanel
              sources={sources}
              totalChunks={totalChunks}
              onRefresh={loadDocuments}
            />
          </TabsContent>
          <TabsContent value="evals" className="flex-1 overflow-auto">
            <EvalPanel config={config} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
