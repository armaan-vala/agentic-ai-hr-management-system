import { useState } from "react";
import { api } from "@/lib/api";

interface Rec {
  recommendation: string;
  reason: string;
  confidence: string;
  facts: string[];
}

const REC_STYLE: Record<string, string> = {
  approve: "bg-green-100 text-green-800",
  reject: "bg-red-100 text-red-800",
  review: "bg-brand-100 text-brand-800",
};

/** Fetches an advisory recommendation for a leave/expense and shows it inline. */
export function AiRecommendation({ path }: { path: string }) {
  const [rec, setRec] = useState<Rec | null>(null);
  const [busy, setBusy] = useState(false);

  async function ask() {
    setBusy(true);
    try {
      setRec(await api<Rec>(path));
    } finally {
      setBusy(false);
    }
  }

  if (!rec) {
    return (
      <button
        onClick={ask}
        disabled={busy}
        className="text-xs font-semibold text-brand-700 hover:underline disabled:opacity-50"
      >
        🤖 {busy ? "Thinking…" : "AI recommend"}
      </button>
    );
  }

  return (
    <div className="mt-2 rounded-lg border border-border bg-background p-3 text-xs animate-in">
      <div className="flex items-center gap-2 mb-1">
        <span className={`px-2 py-0.5 rounded-full font-semibold capitalize ${REC_STYLE[rec.recommendation] ?? "bg-gray-100 text-gray-700"}`}>
          {rec.recommendation}
        </span>
        <span className="text-muted">{rec.confidence} confidence</span>
      </div>
      <p className="text-foreground">{rec.reason}</p>
      {rec.facts.length > 0 && (
        <details className="mt-1">
          <summary className="cursor-pointer text-muted">Based on</summary>
          <ul className="mt-1 list-disc pl-4 text-muted">
            {rec.facts.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
