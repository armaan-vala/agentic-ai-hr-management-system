import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/Layout";
import { Button, Card, CardSkeleton, EmptyState, Input } from "@/components/ui";

interface Bucket {
  label: string;
  value: number;
}
interface Analytics {
  headcount: number;
  present_today: number;
  pending_leaves: number;
  headcount_by_role: Bucket[];
  leaves_by_status: Bucket[];
  leaves_by_type: Bucket[];
  leaves_by_month: Bucket[];
}

export default function Analytics() {
  const [a, setA] = useState<Analytics | null>(null);

  useEffect(() => {
    api<Analytics>("/analytics").then(setA);
  }, []);

  return (
    <div>
      <PageHeader title="People Analytics" subtitle="Your company at a glance" />
      <div className="p-8 max-w-4xl space-y-6">
        <AskBox />
        <div className="grid sm:grid-cols-3 gap-4">
          {!a ? (
            <>
              <CardSkeleton /><CardSkeleton /><CardSkeleton />
            </>
          ) : (
            <>
              <Stat label="Headcount" value={a.headcount} icon="👥" />
              <Stat label="Present today" value={a.present_today} icon="🟢" />
              <Stat label="Pending leaves" value={a.pending_leaves} icon="⏳" />
            </>
          )}
        </div>

        {!a ? (
          <CardSkeleton />
        ) : (
          <div className="grid md:grid-cols-2 gap-4">
            <ChartCard title="Headcount by role" data={a.headcount_by_role} />
            <ChartCard title="Leaves by status" data={a.leaves_by_status} />
            <ChartCard title="Leaves by type" data={a.leaves_by_type} />
            <ChartCard title="Leaves by month" data={a.leaves_by_month} vertical />
          </div>
        )}
      </div>
    </div>
  );
}

const SUGGESTED = [
  "How many people are absent today?",
  "What's our hiring pipeline looking like?",
  "How many leave requests are pending?",
];

function AskBox() {
  const [q, setQ] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function ask(question: string) {
    if (!question.trim()) return;
    setBusy(true);
    setAnswer(null);
    try {
      const r = await api<{ answer: string }>("/analytics/ask", {
        method: "POST",
        body: JSON.stringify({ question }),
      });
      setAnswer(r.answer);
    } catch (e) {
      setAnswer(e instanceof Error ? e.message : "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="p-6 bg-brand-50 border-brand-200">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">📊</span>
        <h3 className="font-semibold">Ask your data</h3>
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(q);
        }}
        className="flex gap-2"
      >
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. How many people are on leave this month?" />
        <Button type="submit" disabled={busy || !q.trim()}>{busy ? "Thinking…" : "Ask"}</Button>
      </form>
      <div className="flex flex-wrap gap-2 mt-2">
        {SUGGESTED.map((s) => (
          <button key={s} onClick={() => { setQ(s); ask(s); }} className="text-xs text-brand-700 hover:underline">
            {s}
          </button>
        ))}
      </div>
      {answer && (
        <div className="mt-3 bg-surface border border-border rounded-xl p-3 text-sm whitespace-pre-wrap animate-in">
          {answer}
          <p className="text-[10px] text-muted mt-2">Grounded in your live data — no invented numbers.</p>
        </div>
      )}
    </Card>
  );
}

function Stat({ label, value, icon }: { label: string; value: number; icon: string }) {
  return (
    <Card className="p-5 animate-in">
      <div className="text-xl mb-1">{icon}</div>
      <p className="text-3xl font-bold text-brand-700">{value}</p>
      <p className="text-xs text-muted">{label}</p>
    </Card>
  );
}

function ChartCard({ title, data, vertical }: { title: string; data: Bucket[]; vertical?: boolean }) {
  const max = Math.max(1, ...data.map((d) => d.value));
  return (
    <Card className="p-5 animate-in">
      <h3 className="font-semibold text-sm mb-4">{title}</h3>
      {data.length === 0 ? (
        <EmptyState text="No data yet." />
      ) : vertical ? (
        <div className="flex items-end gap-2 h-36">
          {data.map((d) => (
            <div key={d.label} className="flex-1 flex flex-col items-center justify-end gap-1">
              <div
                className="w-full rounded-t-lg bg-brand transition-all"
                style={{ height: `${(d.value / max) * 100}%`, minHeight: d.value ? "6px" : "0" }}
                title={`${d.value}`}
              />
              <span className="text-[10px] text-muted">{d.label.slice(5)}</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {data.map((d) => (
            <div key={d.label}>
              <div className="flex justify-between text-xs mb-1">
                <span className="capitalize">{d.label}</span>
                <span className="text-muted">{d.value}</span>
              </div>
              <div className="h-2 rounded-full bg-brand-50 overflow-hidden">
                <div
                  className="h-full rounded-full bg-brand transition-all"
                  style={{ width: `${(d.value / max) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
