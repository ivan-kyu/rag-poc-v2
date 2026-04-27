"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { GraphDiagram } from "./GraphDiagram";
import { TechniqueToggles } from "./TechniqueToggles";
import { NodeStates, PipelineConfig, RetrievedChunk } from "@/lib/types";

interface Props {
  nodeStates: NodeStates;
  config: PipelineConfig;
  onConfigChange: (c: PipelineConfig) => void;
  retrievedChunks: RetrievedChunk[];
  rerankedChunks: RetrievedChunk[];
  route: string;
  isStreaming: boolean;
}

export function PipelinePanel({
  nodeStates,
  config,
  onConfigChange,
  retrievedChunks,
  rerankedChunks,
  route,
  isStreaming,
}: Props) {
  const chunks = rerankedChunks.length > 0 ? rerankedChunks : retrievedChunks;

  return (
    <div className="flex flex-col h-full">
      <Tabs defaultValue="graph" className="flex-1 flex flex-col">
        <TabsList className="mx-4 mt-4 w-auto self-start">
          <TabsTrigger value="graph">Graph</TabsTrigger>
          <TabsTrigger value="config">Config</TabsTrigger>
          <TabsTrigger value="chunks">
            Chunks {chunks.length > 0 && <Badge variant="secondary" className="ml-1 text-xs">{chunks.length}</Badge>}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="graph" className="flex-1 px-4 pb-4">
          <div className="space-y-3">
            {route && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-muted-foreground">Route:</span>
                <Badge variant="outline">{route}</Badge>
              </div>
            )}
            <GraphDiagram nodeStates={nodeStates} config={config} />
            <div className="grid grid-cols-3 gap-2 text-center text-xs text-muted-foreground">
              {Object.entries(nodeStates).map(([name, state]) => (
                <div key={name} className="space-y-0.5">
                  <div className={
                    state.status === "running" ? "text-blue-500 font-medium" :
                    state.status === "done" ? "text-green-600 font-medium" : ""
                  }>
                    {name.replace("retrieve_", "").replace("_", "-")}
                  </div>
                  <div>{state.status}</div>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="config" className="px-4 pb-4">
          <TechniqueToggles config={config} onChange={onConfigChange} disabled={isStreaming} />
        </TabsContent>

        <TabsContent value="chunks" className="flex-1 px-4 pb-4">
          {chunks.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center pt-8">
              No chunks retrieved yet. Ask a question first.
            </p>
          ) : (
            <ScrollArea className="h-96">
              <div className="space-y-3">
                {chunks.map((chunk, i) => (
                  <div key={i} className="rounded-lg border bg-muted/30 p-3 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <Badge variant="outline" className="text-xs">{chunk.source}</Badge>
                      {chunk.score > 0 && (
                        <span className="text-xs text-muted-foreground">
                          score: {chunk.score.toFixed(3)}
                        </span>
                      )}
                    </div>
                    <p className="text-xs leading-relaxed line-clamp-4">{chunk.content}</p>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
