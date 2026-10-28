import type { AnswerEvent } from "../types";
import { ResultChart } from "./ResultChart";
import { ResultTable } from "./ResultTable";

export function AnswerPanel({ answer }: { answer: AnswerEvent }) {
  const { query, chart } = answer;

  return (
    <section className="card answer">
      {chart.title && <h2 className="card__title">{chart.title}</h2>}
      <p className="answer__summary">{answer.summary}</p>
      {query && (
        <>
          <ResultChart chart={chart} rows={query.rows} />
          <details className="answer__sql">
            <summary>SQL executado</summary>
            <pre>
              <code>{query.sql}</code>
            </pre>
          </details>
          <ResultTable query={query} />
        </>
      )}
    </section>
  );
}
