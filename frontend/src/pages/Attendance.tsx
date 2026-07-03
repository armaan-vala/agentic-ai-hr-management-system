import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/auth/AuthProvider";
import { useToast } from "@/components/Toast";
import { PageHeader } from "@/components/Layout";
import { Button, Card, CardSkeleton, EmptyState, Input } from "@/components/ui";

interface Today {
  status: string;
  clock_in: string | null;
  clock_out: string | null;
  hours: number;
}
interface DayRow {
  date: string;
  clock_in: string | null;
  clock_out: string | null;
  hours: number;
  status: string;
}
interface TeamRow {
  user_id: string;
  name: string;
  status: string;
  clock_in: string | null;
  hours: number;
}

const fmtTime = (s: string | null) => (s ? new Date(s).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—");

export default function Attendance() {
  const { me } = useAuth();
  return me?.role === "admin" ? <AdminAttendance /> : <EmployeeAttendance />;
}

function EmployeeAttendance() {
  const toast = useToast();
  const [today, setToday] = useState<Today | null>(null);
  const [rows, setRows] = useState<DayRow[] | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    setToday(await api<Today>("/attendance/today"));
    setRows(await api<DayRow[]>("/attendance/mine"));
  }
  useEffect(() => {
    load();
  }, []);

  async function act(kind: "clock-in" | "clock-out") {
    setBusy(true);
    try {
      const r = await api<{ ok: boolean; message: string }>(`/attendance/${kind}`, { method: "POST" });
      toast(r.message, r.ok ? "success" : "error");
      await load();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader title="Attendance" subtitle="Clock in and track your hours" />
      <div className="p-8 max-w-2xl space-y-6">
        <Card className="p-6 animate-in">
          {!today ? (
            <CardSkeleton />
          ) : (
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted">Today</p>
                <p className="text-lg font-semibold capitalize">{today.status.replace("_", " ")}</p>
                <p className="text-xs text-muted mt-1">
                  In {fmtTime(today.clock_in)} · Out {fmtTime(today.clock_out)} · {today.hours}h
                </p>
              </div>
              {today.status === "not_started" && (
                <Button onClick={() => act("clock-in")} disabled={busy}>Clock in</Button>
              )}
              {today.status === "clocked_in" && (
                <Button onClick={() => act("clock-out")} disabled={busy}>Clock out</Button>
              )}
              {today.status === "clocked_out" && (
                <span className="text-sm text-green-700 font-medium">✓ Done for today</span>
              )}
            </div>
          )}
        </Card>

        <div>
          <h3 className="font-semibold mb-3">Timesheet</h3>
          {!rows ? (
            <div className="space-y-2"><CardSkeleton /><CardSkeleton /></div>
          ) : rows.length === 0 ? (
            <EmptyState text="No attendance yet." />
          ) : (
            <div className="space-y-2">
              {rows.map((r) => (
                <Card key={r.date} className="p-3 flex items-center justify-between text-sm">
                  <span className="font-medium">{new Date(r.date).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" })}</span>
                  <span className="text-muted">{fmtTime(r.clock_in)} → {fmtTime(r.clock_out)}</span>
                  <span className="font-medium">{r.hours}h</span>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function AdminAttendance() {
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [team, setTeam] = useState<TeamRow[] | null>(null);

  useEffect(() => {
    setTeam(null);
    api<TeamRow[]>(`/attendance/team?date=${date}`).then(setTeam);
  }, [date]);

  const present = team?.filter((t) => t.status !== "not_started").length ?? 0;

  return (
    <div>
      <PageHeader title="Attendance" subtitle="Team attendance" />
      <div className="p-8 max-w-3xl space-y-6">
        <div className="flex items-center gap-3">
          <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="w-44" />
          {team && <span className="text-sm text-muted">{present}/{team.length} present</span>}
        </div>
        {!team ? (
          <div className="space-y-2"><CardSkeleton /><CardSkeleton /></div>
        ) : (
          <div className="space-y-2">
            {team.map((t) => (
              <Card key={t.user_id} className="p-4 flex items-center justify-between">
                <div>
                  <p className="font-medium text-sm">{t.name}</p>
                  <p className="text-xs text-muted">In {fmtTime(t.clock_in)} · {t.hours}h</p>
                </div>
                <span
                  className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                    t.status === "not_started" ? "bg-gray-100 text-gray-600" : "bg-green-100 text-green-800"
                  }`}
                >
                  {t.status === "not_started" ? "Absent" : t.status === "clocked_in" ? "Working" : "Present"}
                </span>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
