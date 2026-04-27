import { createParser } from "eventsource-parser";
import { SSEEvent } from "./types";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function* streamChat(
  question: string,
  config: object,
  signal?: AbortSignal
): AsyncGenerator<SSEEvent> {
  const res = await fetch(`${BACKEND_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, config }),
    signal,
  });

  if (!res.ok || !res.body) {
    throw new Error(`Chat request failed: ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  const queue: SSEEvent[] = [];
  let resolve: (() => void) | null = null;

  const parser = createParser({
    onEvent(event) {
      try {
        const parsed = JSON.parse(event.data) as SSEEvent;
        queue.push(parsed);
        resolve?.();
        resolve = null;
      } catch {
        // skip malformed
      }
    },
  });

  const pump = async () => {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        resolve?.();
        break;
      }
      parser.feed(decoder.decode(value, { stream: true }));
      resolve?.();
    }
  };

  pump().catch(() => resolve?.());

  while (true) {
    if (queue.length > 0) {
      const evt = queue.shift()!;
      yield evt;
      if (evt.type === "done" || evt.type === "error") break;
    } else {
      await new Promise<void>((r) => (resolve = r));
    }
  }
}

export async function triggerIngest(): Promise<void> {
  await fetch(`${BACKEND_URL}/api/ingest`, { method: "POST" });
}

export async function fetchDocuments() {
  const res = await fetch(`${BACKEND_URL}/api/documents`);
  return res.json();
}

export async function uploadFile(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BACKEND_URL}/api/upload`, { method: "POST", body: form });
  return res.json();
}

export async function runEvals(config: object) {
  const res = await fetch(`${BACKEND_URL}/api/evals/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ config }),
  });
  return res.json();
}
