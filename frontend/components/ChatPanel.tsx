"use client";

import { useRef, useEffect, KeyboardEvent } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, Send, Loader2 } from "lucide-react";
import { ChatMessage } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Props {
  messages: ChatMessage[];
  input: string;
  onInputChange: (val: string) => void;
  onSubmit: () => void;
  isStreaming: boolean;
  streamingToken: string;
}

const SUGGESTED = [
  "What is RAG and how does it work?",
  "What is the difference between pgvector and ChromaDB?",
  "How does chunking affect retrieval quality?",
  "What is hybrid search and when should I use it?",
];

export function ChatPanel({ messages, input, onInputChange, onSubmit, isStreaming, streamingToken }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingToken]);

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1 p-4">
        {messages.length === 0 && (
          <div className="space-y-3 pt-8">
            <p className="text-center text-muted-foreground text-sm">Ask a question about the knowledge base</p>
            <div className="grid grid-cols-1 gap-2">
              {SUGGESTED.map((q) => (
                <button
                  key={q}
                  onClick={() => { onInputChange(q); }}
                  className="text-left text-sm px-3 py-2 rounded-lg border bg-muted/30 hover:bg-muted transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={cn("mb-4", msg.role === "user" ? "flex justify-end" : "")}>
            {msg.role === "user" ? (
              <div className="max-w-[80%] bg-primary text-primary-foreground rounded-2xl rounded-tr-sm px-4 py-2 text-sm">
                {msg.content}
              </div>
            ) : (
              <div className="max-w-[95%] space-y-2">
                <div className="bg-muted/50 rounded-2xl rounded-tl-sm px-4 py-3 text-sm whitespace-pre-wrap">
                  {msg.content}
                </div>
                {msg.citations && msg.citations.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 px-1">
                    {msg.citations.map((c, i) => (
                      <Badge key={i} variant="secondary" className="text-xs">
                        {c.source}
                      </Badge>
                    ))}
                    {msg.confidence != null && (
                      <Badge variant="outline" className="text-xs">
                        {(msg.confidence * 100).toFixed(0)}% confidence
                      </Badge>
                    )}
                  </div>
                )}
                {msg.langsmithUrl && (
                  <a
                    href={msg.langsmithUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors px-1"
                  >
                    <ExternalLink className="h-3 w-3" />
                    View LangSmith trace
                  </a>
                )}
              </div>
            )}
          </div>
        ))}
        {isStreaming && streamingToken && (
          <div className="mb-4">
            <div className="bg-muted/50 rounded-2xl rounded-tl-sm px-4 py-3 text-sm max-w-[95%] whitespace-pre-wrap">
              {streamingToken}
              <span className="inline-block w-1 h-4 bg-current ml-0.5 animate-pulse" />
            </div>
          </div>
        )}
        <div ref={endRef} />
      </ScrollArea>

      <div className="p-4 border-t">
        <div className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask a question... (Enter to send)"
            className="min-h-[44px] max-h-32 resize-none"
            rows={1}
            disabled={isStreaming}
          />
          <Button onClick={onSubmit} disabled={isStreaming || !input.trim()} size="icon">
            {isStreaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </div>
  );
}
