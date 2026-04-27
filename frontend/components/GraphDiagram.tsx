"use client";

import { useMemo } from "react";
import { ReactFlow, Background, Node, Edge, MarkerType } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { NodeStates, NodeStatus, PipelineConfig } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Props {
  nodeStates: NodeStates;
  config: PipelineConfig;
}

const STATUS_COLORS: Record<NodeStatus, string> = {
  idle: "bg-muted text-muted-foreground border-border",
  running: "bg-blue-500/20 text-blue-700 dark:text-blue-300 border-blue-500 animate-pulse",
  done: "bg-green-500/20 text-green-700 dark:text-green-300 border-green-600",
};

const NODE_LABELS: Record<string, string> = {
  classify: "Classify Query",
  retrieve_naive: "Naive Retrieval",
  retrieve_hybrid: "Hybrid Search",
  retrieve_multiquery: "Multi-Query",
  retrieve_hyde: "HyDE",
  rerank: "Rerank",
  generate: "Generate",
};

function buildNodes(nodeStates: NodeStates, config: PipelineConfig): Node[] {
  const nodes: Node[] = [];
  const x = (col: number) => col * 190 + 20;
  const y = (row: number) => row * 80 + 20;

  if (config.route) {
    nodes.push({ id: "classify", position: { x: x(0), y: y(1) }, data: { label: "Classify" }, type: "default" });
  }

  nodes.push({ id: "retrieve_naive", position: { x: x(1), y: y(0) }, data: { label: "Naive" }, type: "default" });
  if (config.hybrid) nodes.push({ id: "retrieve_hybrid", position: { x: x(1), y: y(1) }, data: { label: "Hybrid" }, type: "default" });
  if (config.multi_query) nodes.push({ id: "retrieve_multiquery", position: { x: x(1), y: y(2) }, data: { label: "Multi-Query" }, type: "default" });
  if (config.hyde) nodes.push({ id: "retrieve_hyde", position: { x: x(1), y: y(3) }, data: { label: "HyDE" }, type: "default" });

  if (config.rerank) nodes.push({ id: "rerank", position: { x: x(2), y: y(1.5) }, data: { label: "Rerank" }, type: "default" });
  nodes.push({ id: "generate", position: { x: config.rerank ? x(3) : x(2), y: y(1.5) }, data: { label: "Generate" }, type: "default" });

  return nodes.map((n) => {
    const status: NodeStatus = (nodeStates as Record<string, { status: NodeStatus }>)[n.id]?.status ?? "idle";
    return {
      ...n,
      data: {
        label: (
          <span className={cn("px-2 py-1 rounded text-xs font-medium border", STATUS_COLORS[status])}>
            {NODE_LABELS[n.id] ?? n.id}
          </span>
        ),
      },
      style: { background: "transparent", border: "none", padding: 0 },
    };
  });
}

function buildEdges(config: PipelineConfig): Edge[] {
  const edges: Edge[] = [];
  const marker = { type: MarkerType.ArrowClosed };
  const retrievers = ["retrieve_naive",
    ...(config.hybrid ? ["retrieve_hybrid"] : []),
    ...(config.multi_query ? ["retrieve_multiquery"] : []),
    ...(config.hyde ? ["retrieve_hyde"] : []),
  ];
  const source = config.route ? "classify" : undefined;
  const next = config.rerank ? "rerank" : "generate";

  retrievers.forEach((r, i) => {
    if (source) edges.push({ id: `classify-${r}`, source: "classify", target: r, markerEnd: marker });
    edges.push({ id: `${r}-${next}-${i}`, source: r, target: next, markerEnd: marker });
  });

  if (config.rerank) edges.push({ id: "rerank-generate", source: "rerank", target: "generate", markerEnd: marker });
  return edges;
}

export function GraphDiagram({ nodeStates, config }: Props) {
  const nodes = useMemo(() => buildNodes(nodeStates, config), [nodeStates, config]);
  const edges = useMemo(() => buildEdges(config), [config]);

  return (
    <div className="h-64 w-full rounded-lg border bg-card">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        nodesDraggable={false}
        nodesConnectable={false}
        zoomOnScroll={false}
        panOnScroll={false}
        panOnDrag={false}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={20} size={1} />
      </ReactFlow>
    </div>
  );
}
