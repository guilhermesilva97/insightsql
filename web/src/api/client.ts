import type { AgentEvent } from "../types";
import { createSseParser } from "./sse";

export async function askQuestion(
  question: string,
  onEvent: (event: AgentEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch("/api/questions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`A API respondeu com status ${response.status}`);
  }

  const feed = createSseParser((message) => onEvent(JSON.parse(message.data) as AgentEvent));
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    feed(value);
  }
}
