import { useEffect, useState } from "react";
import { api, apiUpload } from "@/lib/api";
import { useAuth } from "@/auth/AuthProvider";
import { PageHeader } from "@/components/Layout";
import { Button, Card, EmptyState, Input, Label, Textarea } from "@/components/ui";

interface Policy {
  id: string;
  title: string;
  source: string;
  chunks: number;
  created_at: string;
}
interface PolicyDetail {
  id: string;
  title: string;
  content: string;
}

export default function Policies() {
  const { me } = useAuth();
  const isAdmin = me?.role === "admin";
  const [list, setList] = useState<Policy[]>([]);
  const [open, setOpen] = useState<PolicyDetail | null>(null);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ title: "", content: "" });
  const [msg, setMsg] = useState<string | null>(null);

  async function load() {
    setList(await api<Policy[]>("/policies"));
  }
  useEffect(() => {
    load();
  }, []);

  async function view(id: string) {
    setOpen(await api<PolicyDetail>(`/policies/${id}`));
  }

  async function createText(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      await api("/policies", { method: "POST", body: JSON.stringify(form) });
      setForm({ title: "", content: "" });
      setMsg("Policy added and indexed for the assistant.");
      await load();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "error");
    } finally {
      setBusy(false);
    }
  }

  async function upload(file: File) {
    setBusy(true);
    setMsg(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      await apiUpload("/policies/upload", fd);
      setMsg(`Uploaded ${file.name}.`);
      await load();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "error");
    } finally {
      setBusy(false);
    }
  }

  async function seed() {
    setBusy(true);
    try {
      await api("/policies/seed-samples", { method: "POST" });
      await load();
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: string) {
    await api(`/policies/${id}`, { method: "DELETE" });
    await load();
  }

  return (
    <div>
      <PageHeader
        title="Policies"
        subtitle={isAdmin ? "Upload policies your team & their agents will follow" : "Company policies"}
      />
      <div className="p-8 max-w-3xl space-y-6">
        {isAdmin && (
          <Card className="p-6">
            <h3 className="font-semibold mb-4">Add a policy</h3>
            <form onSubmit={createText} className="space-y-3">
              <div className="space-y-1">
                <Label>Title</Label>
                <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Leave Policy" />
              </div>
              <div className="space-y-1">
                <Label>Content</Label>
                <Textarea
                  rows={6}
                  value={form.content}
                  onChange={(e) => setForm({ ...form, content: e.target.value })}
                  placeholder="Paste your policy text here…"
                />
              </div>
              <div className="flex flex-wrap gap-2 items-center">
                <Button type="submit" disabled={busy || !form.content.trim()}>Add policy</Button>
                <label className="btn-ghost cursor-pointer">
                  Upload file (.txt/.md/.pdf)
                  <input
                    type="file"
                    accept=".txt,.md,.pdf"
                    className="hidden"
                    onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])}
                  />
                </label>
                <Button type="button" variant="ghost" onClick={seed} disabled={busy}>
                  Load sample policies
                </Button>
              </div>
              {msg && <p className="text-sm text-brand-800 bg-brand-50 rounded-lg p-2">{msg}</p>}
            </form>
          </Card>
        )}

        <div>
          <h3 className="font-semibold mb-3">
            {isAdmin ? `Policies (${list.length})` : "Company policies"}
          </h3>
          {list.length === 0 ? (
            <EmptyState text={isAdmin ? "No policies yet. Add one or load samples." : "No policies published yet."} />
          ) : (
            <div className="space-y-2">
              {list.map((p) => (
                <Card key={p.id} className="p-4 flex items-center justify-between">
                  <button className="text-left" onClick={() => view(p.id)}>
                    <p className="font-medium text-sm">{p.title}</p>
                    <p className="text-xs text-muted">{p.chunks} sections · {p.source}</p>
                  </button>
                  <div className="flex gap-2">
                    <Button variant="ghost" onClick={() => view(p.id)}>View</Button>
                    {isAdmin && (
                      <button
                        onClick={() => remove(p.id)}
                        className="text-xs text-red-600 hover:underline px-2"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {open && (
        <div
          className="fixed inset-0 bg-black/30 flex items-center justify-center p-6 z-50"
          onClick={() => setOpen(null)}
        >
          <div className="max-w-2xl w-full" onClick={(e) => e.stopPropagation()}>
            <Card className="max-h-[80vh] overflow-y-auto p-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold">{open.title}</h3>
                <button onClick={() => setOpen(null)} className="text-muted">✕</button>
              </div>
              <pre className="whitespace-pre-wrap text-sm text-foreground font-sans">{open.content}</pre>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
