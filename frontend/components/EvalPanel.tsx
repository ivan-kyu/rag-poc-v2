"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ExternalLink, Play, Loader2 } from "lucide-react";
import { EvalResult, PipelineConfig } from "@/lib/types";
import { runEvals } from "@/lib/sseClient";

interface Props {
  config: PipelineConfig;
}

const METRIC_LABELS: Record<string, string> = {
  faithfulness: "Faithfulness",
  answer_relevancy: "Answer Relevancy",
  context_precision: "Context Precision",
  context_recall: "Context Recall",
};

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = pct >= 80 ? "bg-green-500" : pct >= 60 ? "bg-yellow-500" : "bg-red-400";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs w-8 text-right">{pct}%</span>
    </div>
  );
}

export function EvalPanel({ config }: Props) {
  const [result, setResult] = useState<EvalResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleRun = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await runEvals(config);
      if (data.error) {
        setError(data.error);
      } else {
        setResult(data as EvalResult);
      }
    } catch (e) {
      setError("Failed to run evals");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium">RAGAS Evaluation</p>
          <p className="text-xs text-muted-foreground">
            Run offline evals on current pipeline config
          </p>
        </div>
        <Button size="sm" onClick={handleRun} disabled={loading}>
          {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" /> : <Play className="h-3.5 w-3.5 mr-1.5" />}
          Run
        </Button>
      </div>

      {error && (
        <p className="text-xs text-destructive bg-destructive/10 rounded p-2">{error}</p>
      )}

      {result && (
        <div className="space-y-3">
          <Separator />
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              {result.sample_size} samples evaluated
            </p>
            <div className="flex gap-1 flex-wrap justify-end">
              {Object.entries(result.config)
                .filter(([, v]) => v)
                .map(([k]) => (
                  <Badge key={k} variant="secondary" className="text-xs">{k}</Badge>
                ))}
            </div>
          </div>
          {Object.entries(result.scores).map(([metric, score]) => (
            <div key={metric} className="space-y-1">
              <p className="text-xs font-medium">{METRIC_LABELS[metric] ?? metric}</p>
              <ScoreBar score={score as number} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
