import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { useToast } from "@/components/Toast";
import { PageHeader } from "@/components/Layout";
import { Button, Card, CardSkeleton, EmptyState, Input, Label, Textarea } from "@/components/ui";

interface Upcoming {
  summary: string;
  start: string | null;
  meet_link: string | null;
  html_link: string | null;
}

export default function Meetings() {
  const toast = useToast();
  const [connected, setConnected] = useState<boolean | null>(null);
  const [items, setItems] = useState<Upcoming[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ title: "", description: "", start: "", end: "", attendees: "" });
  const [busy, setBusy] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const status = await api<{ connected: boolean }>("/google/status");
      setConnected(status.connected);
      if (status.connected) setItems(await api<Upcoming[]>("/meetings/upcoming"));
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    load();
  }, []);

  const toIso = (v: string) => (v.length === 16 ? `${v}:00` : v);

  async function schedule(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const attendees = form.attendees.split(",").map((s) => s.trim()).filter(Boolean);
      const res = await api<{ meet_link: string | null }>("/meetings", {
        method: "POST",
        body: JSON.stringify({
          title: form.title,
          description: form.description,
          start: toIso(form.start),
          end: toIso(form.end),
          attendees,
        }),
      });
      toast(res.meet_link ? "Meeting scheduled with Meet link!" : "Meeting scheduled.", "success");
      setForm({ title: "", description: "", start: "", end: "", attendees: "" });
      await load();
    } catch (e) {
      toast(e instanceof Error ? e.message : "error", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader title="Meetings" subtitle="Schedule Google Calendar meetings" />
      <div className="p-8 max-w-3xl space-y-6">
        {loading ? (
          <CardSkeleton />
        ) : !connected ? (
          <Card className="p-6 text-center">
            <p className="text-3xl mb-2">📅</p>
            <p className="font-medium mb-1">Connect Google to schedule meetings</p>
            <p className="text-sm text-muted mb-4">
              Meetings are created on your Google Calendar with a Meet link.
            </p>
            <Link to="/settings" className="btn-brand inline-flex">Go to Settings</Link>
          </Card>
        ) : (
          <>
            <Card className="p-6">
              <h3 className="font-semibold mb-4">Schedule a meeting</h3>
              <form onSubmit={schedule} className="grid sm:grid-cols-2 gap-3">
                <div className="space-y-1 sm:col-span-2">
                  <Label>Title</Label>
                  <Input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Sprint planning" />
                </div>
                <div className="space-y-1">
                  <Label>Start</Label>
                  <Input type="datetime-local" required value={form.start} onChange={(e) => setForm({ ...form, start: e.target.value })} />
                </div>
                <div className="space-y-1">
                  <Label>End</Label>
                  <Input type="datetime-local" required value={form.end} onChange={(e) => setForm({ ...form, end: e.target.value })} />
                </div>
                <div className="space-y-1 sm:col-span-2">
                  <Label>Attendees (comma-separated emails)</Label>
                  <Input value={form.attendees} onChange={(e) => setForm({ ...form, attendees: e.target.value })} placeholder="a@x.com, b@x.com" />
                </div>
                <div className="space-y-1 sm:col-span-2">
                  <Label>Description</Label>
                  <Textarea rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
                </div>
                <div className="sm:col-span-2">
                  <Button type="submit" disabled={busy || !form.title || !form.start || !form.end}>
                    {busy ? "Scheduling…" : "Schedule meeting"}
                  </Button>
                </div>
              </form>
            </Card>

            <div>
              <h3 className="font-semibold mb-3">Upcoming</h3>
              {items.length === 0 ? (
                <EmptyState text="No upcoming meetings." />
              ) : (
                <div className="space-y-2">
                  {items.map((m, i) => (
                    <Card key={i} className="p-4 flex items-center justify-between animate-in">
                      <div>
                        <p className="font-medium text-sm">{m.summary}</p>
                        <p className="text-xs text-muted">
                          {m.start ? new Date(m.start).toLocaleString() : ""}
                        </p>
                      </div>
                      {m.meet_link ? (
                        <a href={m.meet_link} target="_blank" rel="noreferrer" className="btn-brand text-sm">Join Meet</a>
                      ) : m.html_link ? (
                        <a href={m.html_link} target="_blank" rel="noreferrer" className="btn-ghost text-sm">Open</a>
                      ) : null}
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
