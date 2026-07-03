import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/auth/AuthProvider";
import { PageHeader } from "@/components/Layout";
import { Button, Card } from "@/components/ui";

interface GoogleStatus {
  connected: boolean;
  email: string;
}

export default function Settings() {
  const { me } = useAuth();
  const [status, setStatus] = useState<GoogleStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const justConnected = new URLSearchParams(window.location.search).get("google") === "connected";

  async function load() {
    setStatus(await api<GoogleStatus>("/google/status"));
  }
  useEffect(() => {
    load();
  }, []);

  async function connect() {
    setBusy(true);
    try {
      const { auth_url } = await api<{ auth_url: string }>("/google/connect");
      window.location.href = auth_url;
    } finally {
      setBusy(false);
    }
  }

  async function disconnect() {
    setBusy(true);
    try {
      await api("/google/disconnect", { method: "DELETE" });
      await load();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader title="Settings" subtitle="Account & integrations" />
      <div className="p-8 max-w-2xl space-y-6">
        <Card className="p-6">
          <h3 className="font-semibold mb-1">Profile</h3>
          <p className="text-sm text-muted">{me?.full_name || "—"} · {me?.email}</p>
          <p className="text-sm text-muted capitalize">Role: {me?.role}</p>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold flex items-center gap-2">
                <span>📧</span> Gmail
              </h3>
              <p className="text-sm text-muted">
                Connect your Google account so the assistant can send email as you.
              </p>
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
