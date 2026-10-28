import { useCallback, useRef, useState } from "react";
import { askQuestion } from "../api/client";
import type { AgentEvent, AnswerEvent, TraceStep } from "../types";

type Status = "idle" | "running" | "done" | "error";

export function useAgent() {
  const [status, setStatus] = useState<Status>("idle");
  const [steps, setSteps] = useState<TraceStep[]>([]);
  const [answer, setAnswer] = useState<AnswerEvent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const controller = useRef<AbortController | null>(null);
  const settled = useRef(false);

  const handle = useCallback((event: AgentEvent) => {
    if (event.type === "answer" || event.type === "error") settled.current = true;
    switch (event.type) {
      case "tool_started":
        setSteps((current) => [
          ...current,
          { callId: event.call_id, tool: event.tool, arguments: event.arguments, status: "running" },
        ]);
        break;
      case "tool_finished":
        setSteps((current) =>
          current.map((step) =>
            step.callId === event.call_id
              ? { ...step, status: event.ok ? "ok" : "failed", summary: event.summary }
              : step,
          ),
        );
        break;
      case "answer":
        setAnswer(event);
        setStatus("done");
        break;
      case "error":
        setError(event.message);
        setStatus("error");
        break;
    }
  }, []);

  const ask = useCallback(
    async (question: string) => {
      controller.current?.abort();
      controller.current = new AbortController();
      settled.current = false;
      setStatus("running");
      setSteps([]);
      setAnswer(null);
      setError(null);
      try {
        await askQuestion(question, handle, controller.current.signal);
        if (!settled.current) {
          setError("A conexão terminou antes de o agente responder.");
          setStatus("error");
        }
      } catch (cause) {
        if ((cause as Error).name === "AbortError") return;
        setError((cause as Error).message);
        setStatus("error");
      }
    },
    [handle],
  );

  return { status, steps, answer, error, ask };
}
