import type { QuerySnapshot } from "../types";

const numberFormat = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });

function format(value: unknown): string {
  if (typeof value === "number") return numberFormat.format(value);
  if (value === null || value === undefined) return "—";
  return String(value);
}

export function ResultTable({ query }: { query: QuerySnapshot }) {
  return (
    <div className="table-wrapper">
      <table className="table">
        <thead>
          <tr>
            {query.columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {query.rows.map((row, index) => (
            <tr key={index}>
              {query.columns.map((column) => (
                <td key={column} className={typeof row[column] === "number" ? "num" : undefined}>
                  {format(row[column])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {query.truncated && <p className="muted">Resultado truncado pelo limite de linhas.</p>}
    </div>
  );
}
