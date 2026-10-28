import { useState, type FormEvent } from "react";

const SUGGESTIONS = [
  "Qual a receita por categoria, sem pedidos cancelados?",
  "Quantos pedidos foram feitos por mês em 2025?",
  "Quais os 5 produtos com maior receita?",
  "Como os clientes se distribuem por estado?",
];

interface Props {
  disabled: boolean;
  onAsk: (question: string) => void;
}

export function QuestionForm({ disabled, onAsk }: Props) {
  const [question, setQuestion] = useState("");

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const trimmed = question.trim();
    if (trimmed.length >= 3) onAsk(trimmed);
  };

  return (
    <section className="question">
      <form onSubmit={submit} className="question__form">
        <input
          className="question__input"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Pergunte algo sobre as vendas..."
          maxLength={500}
          aria-label="Pergunta"
        />
        <button className="button" type="submit" disabled={disabled || question.trim().length < 3}>
          {disabled ? "Analisando..." : "Perguntar"}
        </button>
      </form>
      <div className="question__suggestions">
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            className="chip"
            disabled={disabled}
            onClick={() => {
              setQuestion(suggestion);
              onAsk(suggestion);
            }}
          >
            {suggestion}
          </button>
        ))}
      </div>
    </section>
  );
}
