import { AgentTrace } from "./components/AgentTrace";
import { AnswerPanel } from "./components/AnswerPanel";
import { QuestionForm } from "./components/QuestionForm";
import { useAgent } from "./hooks/useAgent";

export function App() {
  const { status, steps, answer, error, ask } = useAgent();
  const running = status === "running";

  return (
    <div className="layout">
      <header className="header">
        <h1>InsightQL</h1>
        <p className="muted">Perguntas em linguagem natural, respostas com SQL auditável.</p>
      </header>

      <QuestionForm disabled={running} onAsk={ask} />

      <main className="content">
        <AgentTrace steps={steps} running={running} />
        <div className="results">
          {error && <div className="card alert">{error}</div>}
          {answer && <AnswerPanel answer={answer} />}
          {!answer && !error && (
            <div className="card empty">
              <p className="muted">
                {running
                  ? "O agente está explorando o banco..."
                  : "Faça uma pergunta ou escolha uma sugestão acima."}
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
