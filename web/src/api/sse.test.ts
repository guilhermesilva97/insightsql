import { describe, expect, it } from "vitest";
import { createSseParser, type SseMessage } from "./sse";

function collect(chunks: string[]): SseMessage[] {
  const messages: SseMessage[] = [];
  const feed = createSseParser((message) => messages.push(message));
  chunks.forEach(feed);
  return messages;
}

describe("createSseParser", () => {
  it("parses complete events", () => {
    const messages = collect(['event: answer\ndata: {"summary":"ok"}\n\n']);
    expect(messages).toEqual([{ event: "answer", data: '{"summary":"ok"}' }]);
  });

  it("joins events split across network chunks", () => {
    const messages = collect(["event: tool_started\nda", 'ta: {"tool":"list_tables"}\n', "\n"]);
    expect(messages).toHaveLength(1);
    expect(JSON.parse(messages[0].data)).toEqual({ tool: "list_tables" });
  });

  it("handles several events in one chunk and CRLF line endings", () => {
    const messages = collect(["event: a\r\ndata: 1\r\n\r\nevent: b\r\ndata: 2\r\n\r\n"]);
    expect(messages.map((m) => m.event)).toEqual(["a", "b"]);
  });

  it("ignores blocks without data", () => {
    expect(collect([": keep-alive\n\n"])).toEqual([]);
  });
});
