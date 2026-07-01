import { useEffect, useState } from "react";

const API_URL = (import.meta.env.VITE_API_URL as string) ?? "http://localhost:8000";

/**
 * v0.1.0 landing — confirms the theme renders and the backend is reachable.
 * Real routing (admin / employee / chat) lands in later versions.
 */
export default function App() {
  const [backend, setBackend] = useState<"checking" | "up" | "down">("checking");

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((r) => (r.ok ? setBackend("up") : setBackend("down")))
      .catch(() => setBackend("down"));
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="card max-w-lg w-full p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="h-10 w-10 rounded-xl bg-brand flex items-center justify-center font-bold text-black">
            T
          </div>
          <div>
            <h1 className="text-2xl font-bold">TalentOS</h1>
            <p className="text-sm text-muted">Agentic HRMS · v0.1.0</p>
          </div>
        </div>

        <p className="text-muted mb-6">
          Foundation is live. Theme, frontend, and backend wiring are in place —
          the agent core and features arrive in the next versions.
        </p>

        <div className="flex items-center gap-2 mb-6">
          <span className="text-sm font-medium">Backend:</span>
          <StatusPill state={backend} />
        </div>

        <div className="flex gap-3">
          <button className="btn-brand">Primary action</button>
          <button className="btn-ghost">Secondary</button>
        </div>
      </div>
    </div>
  );
}

function StatusPill({ state }: { state: "checking" | "up" | "down" }) {
  const map = {
    checking: { text: "checking…", cls: "bg-brand-100 text-brand-800" },
    up: { text: "connected", cls: "bg-green-100 text-green-800" },
    down: { text: "not reachable", cls: "bg-red-100 text-red-800" },
  } as const;
  const { text, cls } = map[state];
  return (
    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${cls}`}>
      {text}
    </span>
  );
}
