import type { TraceStep } from "../types";

const LABELS: Record<string, string> = {
  list_tables: "Listando tabelas",
  describe_table: "Lendo schema",
  run_query: "Executando SQL",
};

interface Props {
  steps: TraceStep[];
  running: boolean;
}

export function AgentTrace({ steps, running }: Props) {
  return (
    <aside className="card trace">
      <h2 className="card__title">Raciocínio do agente</h2>
      {steps.length === 0 && !running && (
        <p className="muted">As chamadas de ferramentas MCP aparecem aqui em tempo real.</p>
      )}
      <ol className="trace__list">
        {steps.map((step) => (
          <li key={step.callId} className={`trace__step trace__step--${step.status}`}>
            <span className="trace__dot" aria-hidden />
            <div>
              <strong>{LABELS[step.tool] ?? step.tool}</strong>
              {typeof step.arguments.table === "string" && (
                <code className="trace__arg">{step.arguments.table}</code>
              )}
              {step.summary && <p className="trace__summary">{step.summary}</p>}
            </div>
          </li>
        ))}
        {running && <li className="trace__step trace__step--thinking">Pensando...</li>}
      </ol>
    </aside>
  );
}
