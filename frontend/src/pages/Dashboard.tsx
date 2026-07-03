import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/Layout";
import { Card, CardSkeleton, EmptyState } from "@/components/ui";

interface Recent {
  title: string;
  created_at: string;
}
interface Dash {
  role: string;
  greeting_name: string;
  leave_balance?: number;
  my_pending_leaves?: number;
  employee_count?: number;
  pending_leaves?: number;
  policy_count?: number;
  agent_actions?: number;
  recent_announcements: Recent[];
}

export default function Dashboard() {
  const [d, setD] = useState<Dash | null>(null);
  const nav = useNavigate();

  useEffect(() => {
    api<Dash>("/dashboard").then(setD);
  }, []);

  const isAdmin = d?.role === "admin";

  const stats = isAdmin
    ? [
        { label: "Employees", value: d?.employee_count, icon: "👥", to: "/employees" },
        { label: "Pending leaves", value: d?.pending_leaves, icon: "🌴", to: "/leaves" },
        { label: "Policies", value: d?.policy_count, icon: "📚", to: "/policies" },
        { label: "Agent actions", value: d?.agent_actions, icon: "🤖", to: "/console" },
      ]
    : [
        { label: "Leave balance", value: d?.leave_balance, icon: "🌴", to: "/leaves" },
        { label: "Pending requests", value: d?.my_pending_leaves, icon: "⏳", to: "/leaves" },
      ];

  return (
    <div>
      <PageHeader title="Home" />
      <div className="p-8 max-w-4xl space-y-8">
        <div className="animate-in">
          <h2 className="text-2xl font-bold">
            {greeting()}, {d?.greeting_name ?? "…"} 👋
          </h2>
          <p className="text-muted text-sm">
            {isAdmin ? "Here's what's happening in your company." : "Here's your snapshot."}
          </p>
        </div>

        <div className={`grid gap-4 ${isAdmin ? "sm:grid-cols-4" : "sm:grid-cols-2"}`}>
          {!d
            ? Array.from({ length: isAdmin ? 4 : 2 }).map((_, i) => <CardSkeleton key={i} />)
            : stats.map((s, i) => (
                <button
                  key={s.label}
                  onClick={() => nav(s.to)}
                  style={{ animationDelay: `${i * 40}ms` }}
                  className="animate-in text-left"
                >
                  <Card className="p-5 hover:shadow-md hover:-translate-y-0.5 transition">
                    <div className="text-xl mb-2">{s.icon}</div>
                    <p className="text-3xl font-bold text-brand-700">{s.value ?? 0}</p>
                    <p className="text-xs text-muted">{s.label}</p>
                  </Card>
                </button>
              ))}
        </div>

        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold">Recent announcements</h3>
            <button className="text-sm text-brand-700 hover:underline" onClick={() => nav("/announcements")}>
              View all
            </button>
          </div>
          {!d ? (
            <CardSkeleton />
          ) : d.recent_announcements.length === 0 ? (
            <EmptyState text="No announcements yet." />
          ) : (
            <div className="space-y-2">
              {d.recent_announcements.map((a, i) => (
                <Card key={i} className="p-4 animate-in">
                  <p className="font-medium text-sm">{a.title}</p>
                  <p className="text-xs text-muted">{new Date(a.created_at).toLocaleDateString()}</p>
                </Card>
              ))}
            </div>
          )}
        </div>

        <Card className="p-5 bg-brand-50 border-brand-200">
          <p className="font-medium text-sm mb-1">💬 Need something?</p>
          <p className="text-sm text-muted mb-3">
            Ask the assistant — it can check balances, apply leave, answer policy questions, and more.
          </p>
          <button className="btn-brand" onClick={() => nav("/chat")}>
            Open assistant
          </button>
        </Card>
      </div>
    </div>
  );
}

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}
