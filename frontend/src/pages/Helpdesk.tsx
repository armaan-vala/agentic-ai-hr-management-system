import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/auth/AuthProvider";
import { useToast } from "@/components/Toast";
import { PageHeader } from "@/components/Layout";
import { Badge, Button, Card, CardSkeleton, EmptyState, Input, Label, Textarea } from "@/components/ui";

interface Ticket {
  id: string;
  raised_by: string;
  subject: string;
  message: string;
  status: string;
  admin_response: string;
  created_at: string;
}

export default function Helpdesk() {
  const { me } = useAuth();
  const isAdmin = me?.role === "admin";
  const toast = useToast();
  const [tickets, setTickets] = useState<Ticket[] | null>(null);
  const [form, setForm] = useState({ subject: "", message: "" });
  const [busy, setBusy] = useState(false);

  async function load() {
    setTickets(await api<Ticket[]>(isAdmin ? "/tickets" : "/tickets/mine"));
  }
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin]);

  async function raise(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await api("/tickets", { method: "POST", body: JSON.stringify(form) });
      toast("Ticket raised. HR will get back to you.", "success");
      setForm({ subject: "", message: "" });
      await load();
    } finally {
      setBusy(false);
    }
  }

  async function resolve(id: string) {
    const response = window.prompt("Response to the employee (optional):") ?? "";
    await api(`/tickets/${id}/resolve`, { method: "POST", body: JSON.stringify({ response }) });
    toast("Ticket resolved.", "success");
    await load();
  }

  return (
    <div>
      <PageHeader title="Helpdesk" subtitle={isAdmin ? "Employee queries" : "Raise a query to HR"} />
      <div className="p-8 max-w-3xl space-y-6">
        {!isAdmin && (
          <Card className="p-6">
            <h3 className="font-semibold mb-4">New ticket</h3>
            <form onSubmit={raise} className="space-y-3">
              <div className="space-y-1">
                <Label>Subject</Label>
                <Input required value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} placeholder="Issue with my payslip" />
              </div>
              <div className="space-y-1">
                <Label>Message</Label>
                <Textarea rows={3} required value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} placeholder="Describe your query…" />
              </div>
              <Button type="submit" disabled={busy || !form.subject.trim() || !form.message.trim()}>
                {busy ? "Raising…" : "Raise ticket"}
              </Button>
            </form>
          </Card>
        )}

        <div>
          <h3 className="font-semibold mb-3">{isAdmin ? "All tickets" : "My tickets"}</h3>
          {!tickets ? (
            <div className="space-y-2"><CardSkeleton /><CardSkeleton /></div>
          ) : tickets.length === 0 ? (
            <EmptyState text="No tickets." />
          ) : (
            <div className="space-y-2">
              {tickets.map((t) => (
                <Card key={t.id} className="p-4 animate-in">
                  <div className="flex items-center justify-between">
                    <p className="font-semibold text-sm">{t.subject}</p>
                    <Badge status={t.status} />
                  </div>
                  {isAdmin && <p className="text-xs text-muted">from {t.raised_by}</p>}
                  <p className="text-sm mt-1 whitespace-pre-wrap">{t.message}</p>
                  {t.admin_response && (
                    <p className="text-sm mt-2 bg-brand-50 rounded-lg p-2">
                      <b>HR:</b> {t.admin_response}
                    </p>
                  )}
                  {isAdmin && t.status === "open" && (
                    <div className="mt-3">
                      <Button variant="ghost" onClick={() => resolve(t.id)}>Resolve</Button>
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
