import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/auth/AuthProvider";
import { useToast } from "@/components/Toast";
import { PageHeader } from "@/components/Layout";
import { Button, Card, CardSkeleton, EmptyState, Input, Label, Textarea } from "@/components/ui";

interface Announcement {
  id: string;
  title: string;
  body: string;
  created_at: string;
}

export default function Announcements() {
  const { me } = useAuth();
  const toast = useToast();
  const isAdmin = me?.role === "admin";
  const [list, setList] = useState<Announcement[] | null>(null);
  const [form, setForm] = useState({ title: "", body: "", email_everyone: false });
  const [busy, setBusy] = useState(false);

  async function load() {
    setList(await api<Announcement[]>("/announcements"));
  }
  useEffect(() => {
    load();
  }, []);

  async function post(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const res = await api<{ email_result?: { emailed: number } }>("/announcements", {
        method: "POST",
        body: JSON.stringify(form),
      });
      const emailed = res.email_result?.emailed;
      toast(
        emailed !== undefined ? `Posted and emailed ${emailed} people.` : "Announcement posted.",
        "success",
      );
      setForm({ title: "", body: "", email_everyone: false });
      await load();
    } catch (e) {
      toast(e instanceof Error ? e.message : "Failed to post", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader title="Announcements" subtitle={isAdmin ? "Post company-wide notices" : "Company news"} />
      <div className="p-8 max-w-3xl space-y-6">
        {isAdmin && (
          <Card className="p-6">
            <h3 className="font-semibold mb-4">New announcement</h3>
            <form onSubmit={post} className="space-y-3">
              <div className="space-y-1">
                <Label>Title</Label>
                <Input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Office closed on Friday" />
              </div>
              <div className="space-y-1">
                <Label>Message</Label>
                <Textarea rows={4} required value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} placeholder="Write your announcement…" />
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.email_everyone}
                  onChange={(e) => setForm({ ...form, email_everyone: e.target.checked })}
                  className="accent-brand"
                />
                Also email everyone (from your connected Gmail)
              </label>
              <Button type="submit" disabled={busy || !form.title.trim() || !form.body.trim()}>
                {busy ? "Posting…" : "Post announcement"}
              </Button>
            </form>
          </Card>
        )}

        <div>
          <h3 className="font-semibold mb-3">Feed</h3>
          {!list ? (
            <div className="space-y-2">
              <CardSkeleton />
              <CardSkeleton />
            </div>
          ) : list.length === 0 ? (
            <EmptyState text="No announcements yet." />
          ) : (
            <div className="space-y-2">
              {list.map((a) => (
                <Card key={a.id} className="p-4 animate-in">
                  <div className="flex items-center justify-between">
                    <p className="font-semibold text-sm">{a.title}</p>
                    <span className="text-xs text-muted">{new Date(a.created_at).toLocaleString()}</span>
                  </div>
                  <p className="text-sm text-foreground mt-1 whitespace-pre-wrap">{a.body}</p>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
