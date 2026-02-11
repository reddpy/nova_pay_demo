import { fetchEventSource } from "@microsoft/fetch-event-source";
import type { Source } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function streamChat(
  question: string,
  onToken: (token: string) => void,
  onSources: (sources: Source[]) => void,
  onDone: () => void,
  onError: (error: Error) => void,
  signal?: AbortSignal
) {
  await fetchEventSource(`${API_URL}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      metadata: {
        user_type: "engineer",
        feature_area: "general",
        session_id: crypto.randomUUID(),
      },
    }),
    signal,
    openWhenHidden: true,
    onmessage(event) {
      if (!event.data) return;
      try {
        const data = JSON.parse(event.data);
        if (data.type === "token") onToken(data.content);
        if (data.type === "sources") onSources(data.content);
        if (data.type === "done") onDone();
        if (data.type === "error") onError(new Error(data.content));
      } catch {
        // ignore parse errors
      }
    },
    onerror(err) {
      onError(err instanceof Error ? err : new Error("Stream error"));
      throw err; // stop retrying
    },
  });
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/api/health`, { signal: AbortSignal.timeout(3000) });
    const data = await res.json();
    return data.status === "ok";
  } catch {
    return false;
  }
}
