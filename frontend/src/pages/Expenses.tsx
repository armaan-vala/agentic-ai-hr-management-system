import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/auth/AuthProvider";
import { useToast } from "@/components/Toast";
import { PageHeader } from "@/components/Layout";
import { Badge, Button, Card, CardSkeleton, EmptyState, Input, Label } from "@/components/ui";
import { AiRecommendation } from "@/components/AiRecommendation";

interface Expense {
  id: string;
  employee: string;
  amount: number;
  currency: string;
  category: string;
  description: string;
  status: string;
  created_at: string;
}

export default function Expenses() {
  const { me } = useAuth();
  return me?.role === "admin" ? <AdminExpenses /> : <EmployeeExpenses />;
}

function EmployeeExpenses() {
  const toast = useToast();
  const [mine, setMine] = useState<Expense[] | null>(null);
  const [form, setForm] = useState({ amount: "", category: "travel", description: "" });
  const [busy, setBusy] = useState(false);

  async function load() {
    setMine(await api<Expense[]>("/expenses/mine"));
  }
  useEffect(() => {
    load();
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await api("/expenses", {
        method: "POST",
        body: JSON.stringify({ ...form, amount: Number(form.amount) }),
      });
      toast("Expense submitted for approval.", "success");
      setForm({ amount: "", category: "travel", description: "" });
      await load();
    } catch (e) {
      toast(e instanceof Error ? e.message : "error", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader title="Expenses" subtitle="Submit reimbursement claims" />
      <div className="p-8 max-w-3xl space-y-6">
        <Card className="p-6">
          <h3 className="font-semibold mb-4">New claim</h3>
          <form onSubmit={submit} className="grid sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label>Amount</Label>
              <Input type="number" required value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} placeholder="1500" />
            </div>
            <div className="space-y-1">
              <Label>Category</Label>
              <select
                className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm"
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
              >
                <option value="travel">Travel</option>
                <option value="food">Food</option>
                <option value="supplies">Supplies</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div className="space-y-1 sm:col-span-2">
              <Label>Description</Label>
              <Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Cab to client meeting" />
            </div>
            <div className="sm:col-span-2">
              <Button type="submit" disabled={busy || !form.amount}>Submit claim</Button>
            </div>
          </form>
        </Card>

        <div>
          <h3 className="font-semibold mb-3">My claims</h3>
          {!mine ? (
            <div className="space-y-2"><CardSkeleton /><CardSkeleton /></div>
          ) : mine.length === 0 ? (
            <EmptyState text="No claims yet." />
          ) : (
            <div className="space-y-2">
              {mine.map((x) => (
                <Card key={x.id} className="p-4 flex items-center justify-between animate-in">
                  <div>
                    <p className="font-medium text-sm capitalize">
                      {x.currency} {x.amount.toLocaleString()} · {x.category}
                    </p>
                    <p className="text-xs text-muted">{x.description || "—"}</p>
                  </div>
                  <Badge status={x.status} />
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function AdminExpenses() {
  const toast = useToast();
  const [pending, setPending] = useState<Expense[] | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    setPending(await api<Expense[]>("/expenses/pending"));
  }
  useEffect(() => {
    load();
  }, []);

  async function decide(id: string, decision: "approve" | "reject") {
    setBusy(true);
    try {
      await api(`/expenses/${id}/decision`, { method: "POST", body: JSON.stringify({ decision }) });
      toast(`Expense ${decision}d.`, "success");
      await load();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader title="Expenses" subtitle="Reimbursement approvals" />
      <div className="p-8 max-w-3xl">
        <h3 className="font-semibold mb-3">Pending claims</h3>
        {!pending ? (
          <div className="space-y-2"><CardSkeleton /><CardSkeleton /></div>
        ) : pending.length === 0 ? (
          <EmptyState text="Nothing pending. 🎉" />
        ) : (
          <div className="space-y-2">
            {pending.map((x) => (
              <Card key={x.id} className="p-4 animate-in">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm capitalize">
                      {x.employee} · {x.currency} {x.amount.toLocaleString()} · {x.category}
                    </p>
                    <p className="text-xs text-muted">{x.description || "—"}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button disabled={busy} onClick={() => decide(x.id, "approve")}>Approve</Button>
                    <Button variant="ghost" disabled={busy} onClick={() => decide(x.id, "reject")}>Reject</Button>
                  </div>
                </div>
                <AiRecommendation path={`/advisor/expense/${x.id}`} />
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
