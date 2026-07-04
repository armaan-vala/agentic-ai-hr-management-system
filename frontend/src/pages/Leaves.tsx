import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/auth/AuthProvider";
import { PageHeader } from "@/components/Layout";
import { Badge, Button, Card, EmptyState, Input, Label } from "@/components/ui";
import { AiRecommendation } from "@/components/AiRecommendation";

interface Leave {
  id: string;
  employee: string;
  type: string;
  start_date: string;
  end_date: string;
  days: number;
  reason: string;
  status: string;
}
interface Balance {
  annual_limit: number;
  used: number;
  balance: number;
}

export default function Leaves() {
  const { me } = useAuth();
  const isAdmin = me?.role === "admin";
  return (
    <div>
      <PageHeader title="Leave" subtitle={isAdmin ? "Approvals & requests" : "Apply and track your leave"} />
      <div className="p-8 max-w-3xl space-y-6">
        {isAdmin ? <AdminLeaves /> : <EmployeeLeaves />}
      </div>
    </div>
  );
}

function EmployeeLeaves() {
  const [balance, setBalance] = useState<Balance | null>(null);
  const [mine, setMine] = useState<Leave[]>([]);
  const [form, setForm] = useState({ leave_type: "casual", start_date: "", end_date: "", reason: "" });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setBalance(await api<Balance>("/leaves/balance"));
    setMine(await api<Leave[]>("/leaves/mine"));
  }
  useEffect(() => {
    load();
  }, []);

  async function apply(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      await api("/leaves/", { method: "POST", body: JSON.stringify(form) });
      setForm({ leave_type: "casual", start_date: "", end_date: "", reason: "" });
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      {balance && (
        <div className="grid grid-cols-3 gap-4">
          <Stat label="Balance" value={balance.balance} />
          <Stat label="Used" value={balance.used} />
          <Stat label="Annual limit" value={balance.annual_limit} />
        </div>
      )}

      <Card className="p-6">
        <h3 className="font-semibold mb-4">Apply for leave</h3>
        <form onSubmit={apply} className="grid sm:grid-cols-2 gap-4">
          <div className="space-y-1">
            <Label>Type</Label>
            <select
              className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm"
              value={form.leave_type}
              onChange={(e) => setForm({ ...form, leave_type: e.target.value })}
            >
              <option value="casual">Casual</option>
              <option value="sick">Sick</option>
              <option value="earned">Earned</option>
            </select>
          </div>
          <div />
          <div className="space-y-1">
            <Label>From</Label>
            <Input type="date" required value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
          </div>
          <div className="space-y-1">
            <Label>To</Label>
            <Input type="date" required value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
          </div>
          <div className="space-y-1 sm:col-span-2">
            <Label>Reason</Label>
            <Input value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} placeholder="Optional" />
          </div>
          {err && <p className="text-sm text-red-600 sm:col-span-2">{err}</p>}
          <div className="sm:col-span-2">
            <Button type="submit" disabled={busy}>{busy ? "Applying…" : "Apply"}</Button>
          </div>
        </form>
      </Card>

      <div>
        <h3 className="font-semibold mb-3">My requests</h3>
        {mine.length === 0 ? (
          <EmptyState text="No leave requests yet." />
        ) : (
          <div className="space-y-2">
            {mine.map((l) => (
              <LeaveRow key={l.id} l={l} />
            ))}
          </div>
        )}
      </div>
    </>
  );
}

function AdminLeaves() {
  const [pending, setPending] = useState<Leave[]>([]);
  const [busy, setBusy] = useState(false);

  async function load() {
    setPending(await api<Leave[]>("/leaves/pending"));
  }
  useEffect(() => {
    load();
  }, []);

  async function decide(id: string, decision: "approve" | "reject") {
    setBusy(true);
    try {
      await api(`/leaves/${id}/decision`, { method: "POST", body: JSON.stringify({ decision }) });
      await load();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h3 className="font-semibold mb-3">Pending approvals</h3>
      {pending.length === 0 ? (
        <EmptyState text="Nothing pending. All caught up! 🎉" />
      ) : (
        <div className="space-y-2">
          {pending.map((l) => (
            <Card key={l.id} className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-sm">
                    {l.employee} · {l.type} · {l.days}d
                  </p>
                  <p className="text-xs text-muted">
                    {l.start_date} → {l.end_date}
                    {l.reason ? ` · ${l.reason}` : ""}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button disabled={busy} onClick={() => decide(l.id, "approve")}>Approve</Button>
                  <Button variant="ghost" disabled={busy} onClick={() => decide(l.id, "reject")}>Reject</Button>
                </div>
              </div>
              <AiRecommendation path={`/advisor/leave/${l.id}`} />
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <Card className="p-4">
      <p className="text-2xl font-bold text-brand-700">{value}</p>
      <p className="text-xs text-muted">{label}</p>
    </Card>
  );
}

function LeaveRow({ l }: { l: Leave }) {
  return (
    <Card className="p-4 flex items-center justify-between">
      <div>
        <p className="font-medium text-sm capitalize">
          {l.type} · {l.days}d
        </p>
        <p className="text-xs text-muted">
          {l.start_date} → {l.end_date}
          {l.reason ? ` · ${l.reason}` : ""}
        </p>
      </div>
      <Badge status={l.status} />
    </Card>
  );
}
