import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/Layout";
import { Button, Card, EmptyState, Input, Label } from "@/components/ui";

interface Employee {
  id: string;
  email: string;
  full_name: string;
  role: string;
}
interface Created extends Employee {
  temp_password: string;
  note: string;
}

export default function Employees() {
  const [list, setList] = useState<Employee[]>([]);
  const [form, setForm] = useState({ email: "", full_name: "" });
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState<Created | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setList(await api<Employee[]>("/employees"));
  }
  useEffect(() => {
    load();
  }, []);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    setCreated(null);
    try {
      const res = await api<Created>("/employees", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setCreated(res);
      setForm({ email: "", full_name: "" });
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader title="Employees" subtitle="Add and manage your team" />
      <div className="p-8 max-w-3xl space-y-6">
        <Card className="p-6">
          <h3 className="font-semibold mb-4">Add employee</h3>
          <form onSubmit={add} className="grid sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <Label>Full name</Label>
              <Input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} placeholder="Priya Sharma" />
            </div>
            <div className="space-y-1">
              <Label>Email</Label>
              <Input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="priya@company.com" />
            </div>
            {err && <p className="text-sm text-red-600 sm:col-span-2">{err}</p>}
            <div className="sm:col-span-2">
              <Button type="submit" disabled={busy}>{busy ? "Creating…" : "Create employee"}</Button>
            </div>
          </form>

          {created && (
            <div className="mt-4 rounded-xl bg-brand-50 border border-brand-200 p-4 text-sm">
              <p className="font-semibold mb-1">✅ {created.email} created</p>
              <p>
                Temporary password: <code className="bg-white px-2 py-0.5 rounded">{created.temp_password}</code>
              </p>
              <p className="text-muted text-xs mt-1">{created.note}</p>
            </div>
          )}
        </Card>

        <div>
          <h3 className="font-semibold mb-3">Team ({list.length})</h3>
          {list.length === 0 ? (
            <EmptyState text="No employees yet." />
          ) : (
            <div className="space-y-2">
              {list.map((u) => (
                <Card key={u.id} className="p-4 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm">{u.full_name || "—"}</p>
                    <p className="text-xs text-muted">{u.email}</p>
                  </div>
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-gray-100 text-gray-700 capitalize">
                    {u.role}
                  </span>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
