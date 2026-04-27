export interface PipelineConfig {
  hybrid: boolean;
  multi_query: boolean;
  hyde: boolean;
  rerank: boolean;
  route: boolean;
}

export interface Citation {
  source: string;
  chunk_index: number;
  relevance_score: number;
  snippet: string;
}

export interface RetrievedChunk {
  content: string;
  source: string;
  score: number;
}

export type NodeName =
  | "classify"
  | "retrieve_naive"
  | "retrieve_hybrid"
  | "retrieve_multiquery"
  | "retrieve_hyde"
  | "rerank"
  | "generate";

export type NodeStatus = "idle" | "running" | "done";

export interface NodeState {
  status: NodeStatus;
  chunks?: RetrievedChunk[];
  route?: string;
}

export type NodeStates = Record<NodeName, NodeState>;

export interface SSEEvent {
  type:
    | "node_start"
    | "node_end"
    | "token"
    | "done"
    | "error"
    | "status";
  data: Record<string, unknown>;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  confidence?: number;
  langsmithUrl?: string;
  config?: PipelineConfig;
  nodeStates?: NodeStates;
}

export interface DocumentSource {
  name: string;
  chunks: number;
}

export interface DocumentsResponse {
  total_chunks: number;
  sources: DocumentSource[];
}

export interface EvalScore {
  faithfulness: number;
  answer_relevancy: number;
  context_precision: number;
  context_recall: number;
}

export interface EvalResult {
  config: PipelineConfig;
  sample_size: number;
  scores: EvalScore;
  error?: string;
}
