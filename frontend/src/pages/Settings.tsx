import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/auth/AuthProvider";
import { useToast } from "@/components/Toast";
import { PageHeader } from "@/components/Layout";
import { Button, Card, Input, Label } from "@/components/ui";

interface GoogleStatus {
  connected: boolean;
  email: string;
}
interface CompanyInfo {
  name: string;
  annual_leave_limit: number;
}

export default function Settings() {
  const { me, refreshMe } = useAuth();
  const toast = useToast();
  const [status, setStatus] = useState<GoogleStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [name, setName] = useState(me?.full_name ?? "");
  const [company, setCompany] = useState<CompanyInfo | null>(null);
  const justConnected = new URLSearchParams(window.location.search).get("google") === "connected";

  async function load() {
    setStatus(await api<GoogleStatus>("/google/status"));
    if (me?.role === "admin") setCompany(await api<CompanyInfo>("/company"));
  }
  useEffect(() => {
    load();
    setName(me?.full_name ?? "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me?.id]);

  async function saveProfile() {
    setBusy(true);
    try {
      await api("/me/profile", { method: "PATCH", body: JSON.stringify({ full_name: name }) });
      await refreshMe();
      toast("Profile updated.", "success");
    } finally {
      setBusy(false);
    }
  }

  async function saveCompany() {
    if (!company) return;
    setBusy(true);
    try {
      await api("/company", { method: "PUT", body: JSON.stringify(company) });
      toast("Company settings saved.", "success");
    } finally {
      setBusy(false);
    }
  }

  async function connect() {
    const { auth_url } = await api<{ auth_url: string }>("/google/connect");
    window.location.href = auth_url;
  }
  async function disconnect() {
    await api("/google/disconnect", { method: "DELETE" });
    await load();
    toast("Google disconnected.", "info");
  }

  return (
    <div>
      <PageHeader title="Settings" subtitle="Profile, company & integrations" />
      <div className="p-8 max-w-2xl space-y-6">
        {/* Profile */}
        <Card className="p-6">
          <h3 className="font-semibold mb-4">Profile</h3>
          <div className="space-y-3">
            <div className="space-y-1">
              <Label>Full name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="text-sm text-muted">
              {me?.email} · <span className="capitalize">{me?.role}</span>
            </div>
            <Button onClick={saveProfile} disabled={busy || !name.trim()}>Save profile</Button>
          </div>
        </Card>

        {/* Company (admin) */}
        {me?.role === "admin" && company && (
          <Card className="p-6">
            <h3 className="font-semibold mb-4">Company settings</h3>
            <div className="grid sm:grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Company name</Label>
                <Input value={company.name} onChange={(e) => setCompany({ ...company, name: e.target.value })} />
              </div>
              <div className="space-y-1">
                <Label>Annual leave limit (days)</Label>
                <Input
                  type="number"
                  value={company.annual_leave_limit}
                  onChange={(e) => setCompany({ ...company, annual_leave_limit: Number(e.target.value) })}
                />
              </div>
            </div>
            <div className="mt-4">
              <Button onClick={saveCompany} disabled={busy}>Save company</Button>
            </div>
          </Card>
        )}

        {/* Gmail */}
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold flex items-center gap-2"><span>📧</span> Gmail</h3>
              <p className="text-sm text-muted">Let the assistant send email as you.</p>
            </div>
            {status?.connected ? (
              <Button variant="ghost" onClick={disconnect} disabled={busy}>Disconnect</Button>
            ) : (
              <Button onClick={connect} disabled={busy}>Connect Google</Button>
            )}
          </div>
          {(status?.connected || justConnected) && (
            <p className="mt-3 text-sm text-green-700 bg-green-50 rounded-lg p-2">
              ✓ Connected{status?.email ? ` as ${status.email}` : ""}
            </p>
          )}
        </Card>
      </div>
    </div>
  );
}
