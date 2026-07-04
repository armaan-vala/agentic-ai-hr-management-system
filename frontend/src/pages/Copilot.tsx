import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/Layout";
import { Button, Card, CardSkeleton, EmptyState } from "@/components/ui";

interface Insight {
  type: string;
  severity: string;
  title: string;
  detail: string;
  action_path: string;
}
interface CopilotData {
  summary: string;
  grounded: boolean;
  generated_at: string | null;
  insights: Insight[];
}

const SEV: Record<string, string> = {
  critical: "border-red-200 bg-red-50",
  warning: "border-brand-200 bg-brand-50",
  info: "border-border bg-surface",
};
const SEV_ICON: Record<string, string> = { critical: "🔴", warning: "🟡", info: "🔵" };

export default function Copilot() {
  const [data, setData] = useState<CopilotData | null>(null);
  const [running, setRunning] = useState(false);
  const nav = useNavigate();

  async function load() {
    setData(await api<CopilotData>("/copilot"));
  }
  useEffect(() => {
    load();
  }, []);

  async function runNow() {
    setRunning(true);
    try {
      setData(await api<CopilotData>("/copilot/run", { method: "POST" }));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div>
      <PageHeader title="HR Copilot" subtitle="Proactive insights, grounded in your real data" />
      <div className="p-8 max-w-3xl space-y-6">
        {/* Digest hero */}
        {!data ? (
          <CardSkeleton />
        ) : (
          <Card className="p-6 bg-brand-50 border-brand-200 animate-in">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">🤖</span>
                  <h3 className="font-semibold">Your briefing</h3>
                  {!data.grounded && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-200 text-gray-600">
                      offline mode
                    </span>
                  )}
                </div>
                <p className="text-sm whitespace-pre-wrap">{data.summary}</p>
                {data.generated_at && (
                  <p className="text-xs text-muted mt-2">
                    Updated {new Date(data.generated_at).toLocaleString()}
                  </p>
                )}
              </div>
              <Button onClick={runNow} disabled={running}>
                {running ? "Running…" : "Run now"}
              </Button>
            </div>
          </Card>
        )}

        {/* Insight feed */}
        <div>
          <h3 className="font-semibold mb-3">Needs attention</h3>
          {!data ? (
            <div className="space-y-2"><CardSkeleton /><CardSkeleton /></div>
          ) : data.insights.length === 0 ? (
            <EmptyState text="Nothing needs your attention. 🎉" />
          ) : (
            <div className="space-y-2">
              {data.insights.map((i, idx) => (
                <button
                  key={idx}
                  onClick={() => i.action_path && nav(i.action_path)}
                  className="w-full text-left animate-in"
                  style={{ animationDelay: `${idx * 40}ms` }}
                >
                  <div className={`rounded-xl border p-4 transition hover:shadow-sm ${SEV[i.severity] ?? SEV.info}`}>
                    <p className="font-medium text-sm">
                      <span className="mr-2">{SEV_ICON[i.severity] ?? "🔵"}</span>
                      {i.title}
                    </p>
                    <p className="text-xs text-muted mt-1">{i.detail}</p>
                  </div>
                </button>
              ))}
            </div>
          )}
          <p className="text-xs text-muted mt-4">
            ℹ️ Numbers come straight from your data — the AI only writes the summary, it never invents figures.
          </p>
        </div>
      </div>
    </div>
  );
}
