export type ChartKind = "bar" | "line" | "pie" | "table";

export interface ChartSpec {
  kind: ChartKind;
  x: string | null;
  y: string[];
  title: string | null;
}

export type Row = Record<string, string | number | boolean | null>;

export interface QuerySnapshot {
  sql: string;
  columns: string[];
  rows: Row[];
  truncated: boolean;
}

export interface ToolStartedEvent {
  type: "tool_started";
  call_id: string;
  tool: string;
  arguments: Record<string, unknown>;
}

export interface ToolFinishedEvent {
  type: "tool_finished";
  call_id: string;
  tool: string;
  ok: boolean;
  summary: string;
}

export interface AnswerEvent {
  type: "answer";
  summary: string;
  chart: ChartSpec;
  query: QuerySnapshot | null;
}

export interface ErrorEvent {
  type: "error";
  message: string;
}

export type AgentEvent = ToolStartedEvent | ToolFinishedEvent | AnswerEvent | ErrorEvent;

export interface TraceStep {
  callId: string;
  tool: string;
  arguments: Record<string, unknown>;
  status: "running" | "ok" | "failed";
  summary?: string;
}
