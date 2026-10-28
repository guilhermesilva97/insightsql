import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartSpec, Row } from "../types";

const SERIES = ["var(--series-1)", "var(--series-2)", "var(--series-3)", "var(--series-4)"];

interface Props {
  chart: ChartSpec;
  rows: Row[];
}

export function ResultChart({ chart, rows }: Props) {
  if (chart.kind === "table" || !chart.x || chart.y.length === 0) return null;
  const x = chart.x;

  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height={320}>
        {chart.kind === "pie" ? (
          <PieChart>
            <Tooltip />
            <Legend />
            <Pie data={rows} dataKey={chart.y[0]} nameKey={x} outerRadius={120}>
              {rows.map((_, index) => (
                <Cell key={index} fill={SERIES[index % SERIES.length]} />
              ))}
            </Pie>
          </PieChart>
        ) : chart.kind === "line" ? (
          <LineChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey={x} stroke="var(--muted)" />
            <YAxis stroke="var(--muted)" />
            <Tooltip />
            <Legend />
            {chart.y.map((key, index) => (
              <Line key={key} dataKey={key} stroke={SERIES[index % SERIES.length]} strokeWidth={2} />
            ))}
          </LineChart>
        ) : (
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey={x} stroke="var(--muted)" />
            <YAxis stroke="var(--muted)" />
            <Tooltip />
            <Legend />
            {chart.y.map((key, index) => (
              <Bar key={key} dataKey={key} fill={SERIES[index % SERIES.length]} radius={[4, 4, 0, 0]} />
            ))}
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
