"use client";

import { useCallback, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Upload, RefreshCw, FileText, Loader2 } from "lucide-react";
import { DocumentSource } from "@/lib/types";
import { fetchDocuments, triggerIngest, uploadFile } from "@/lib/sseClient";

interface Props {
  sources: DocumentSource[];
  totalChunks: number;
  onRefresh: () => void;
}

export function KnowledgeBasePanel({ sources, totalChunks, onRefresh }: Props) {
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleIngest = async () => {
    setLoading(true);
    try {
      await triggerIngest();
      onRefresh();
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file: File) => {
    setLoading(true);
    try {
      await uploadFile(file);
      onRefresh();
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  }, []);

  return (
    <div className="flex flex-col h-full p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium">Knowledge Base</p>
          <p className="text-xs text-muted-foreground">{totalChunks} chunks across {sources.length} sources</p>
        </div>
        <Button variant="outline" size="sm" onClick={handleIngest} disabled={loading}>
          {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
        </Button>
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
          dragOver ? "border-primary bg-primary/5" : "border-muted-foreground/30 hover:border-primary/50"
        }`}
      >
        <Upload className="h-5 w-5 mx-auto mb-2 text-muted-foreground" />
        <p className="text-xs text-muted-foreground">Drop a .md or .pdf file here</p>
        <input
          ref={inputRef}
          type="file"
          accept=".md,.pdf"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
        />
      </div>

      <Separator />

      <ScrollArea className="flex-1">
        <div className="space-y-2">
          {sources.map((src) => (
            <div key={src.name} className="flex items-center gap-2 py-1">
              <FileText className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
              <span className="text-xs flex-1 truncate">{src.name}</span>
              <Badge variant="secondary" className="text-xs shrink-0">{src.chunks}</Badge>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
