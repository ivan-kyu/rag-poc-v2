"use client";

import { Switch } from "@/components/ui/switch";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Info } from "lucide-react";
import { PipelineConfig } from "@/lib/types";

interface Props {
  config: PipelineConfig;
  onChange: (config: PipelineConfig) => void;
  disabled?: boolean;
}

const TOGGLES: { key: keyof PipelineConfig; label: string; description: string }[] = [
  {
    key: "hybrid",
    label: "Hybrid Search",
    description: "Combines BM25 keyword search with vector similarity (EnsembleRetriever)",
  },
  {
    key: "multi_query",
    label: "Multi-Query",
    description: "Generates query variants and merges retrieved results (MultiQueryRetriever)",
  },
  {
    key: "hyde",
    label: "HyDE",
    description: "Generates a hypothetical answer, embeds it, and retrieves by that embedding",
  },
  {
    key: "rerank",
    label: "Reranking",
    description: "Re-scores retrieved chunks with a cross-encoder model (bge-reranker-base)",
  },
  {
    key: "route",
    label: "Query Routing",
    description: "Classifies query type (factual/definition/procedural) and picks best retriever",
  },
];

export function TechniqueToggles({ config, onChange, disabled }: Props) {
  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">
        Retrieval Techniques
      </p>
      {TOGGLES.map(({ key, label, description }) => (
        <div key={key} className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5">
            <span className="text-sm">{label}</span>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent side="right" className="max-w-xs text-xs">
                {description}
              </TooltipContent>
            </Tooltip>
          </div>
          <Switch
            checked={config[key]}
            onCheckedChange={(val) => onChange({ ...config, [key]: val })}
            disabled={disabled}
          />
        </div>
      ))}
    </div>
  );
}
