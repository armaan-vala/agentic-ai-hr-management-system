import { useRef, useState, useEffect } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/Layout";
import { Button } from "@/components/ui";

interface PendingApproval {
  action_id: string;
  tool: string;
  summary: string;
}
interface ChatResponse {
  reply: string;
  trace: { tool: string }[];
  pending_approval: PendingApproval | null;
}
interface Msg {
  role: "user" | "assistant";
  content: string;
  tools?: string[];
  approval?: PendingApproval | null;
}

const SUGGESTIONS = [
  "What is my leave balance?",
  "Apply 2 days casual leave next Monday to Tuesday",
  "What's our work-from-home policy?",
  "Show my leave history",
];

export default function Chat() {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs, busy]);

  async function send(text: string) {
    if (!text.trim() || busy) return;
    const history = msgs.map((m) => ({ role: m.role, content: m.content }));
    setMsgs((m) => [...m, { role: "user", content: text }]);
    setInput("");
    setBusy(true);
    try {
      const res = await api<ChatResponse>("/chat/message", {
        method: "POST",
        body: JSON.stringify({ message: text, history }),
      });
      setMsgs((m) => [
        ...m,
        {
          role: "assistant",
          content: res.reply,
          tools: res.trace.map((t) => t.tool),
          approval: res.pending_approval,
        },
      ]);
    } catch (e) {
      setMsgs((m) => [
        ...m,
        { role: "assistant", content: `⚠️ ${e instanceof Error ? e.message : "error"}` },
      ]);
    } finally {
      setBusy(false);
    }
  }

  async function decide(idx: number, action_id: string, decision: "approve" | "reject") {
    setBusy(true);
    try {
      const res = await api<{ reply: string }>("/chat/approve", {
        method: "POST",
        body: JSON.stringify({ action_id, decision }),
      });
      setMsgs((m) => {
        const copy = [...m];
        copy[idx] = { ...copy[idx], approval: null }; // clear the buttons
        return [...copy, { role: "assistant", content: res.reply }];
      });
    } catch (e) {
      setMsgs((m) => [
        ...m,
        { role: "assistant", content: `⚠️ ${e instanceof Error ? e.message : "error"}` },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col h-screen">
      <PageHeader title="Assistant" subtitle="Ask about leave, policies, or ask me to do things" />

      <div className="flex-1 overflow-y-auto px-8 py-6">
        {msgs.length === 0 && (
          <div className="max-w-2xl mx-auto text-center mt-16">
            <div className="h-12 w-12 rounded-2xl bg-brand mx-auto mb-4 flex items-center justify-center text-xl">
              🤖
            </div>
            <h2 className="text-lg font-semibold mb-1">How can I help?</h2>
            <p className="text-muted text-sm mb-6">
              I use real company data and can take actions (with your approval).
            </p>
            <div className="grid sm:grid-cols-2 gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="text-left text-sm border border-border rounded-xl px-4 py-3 bg-surface hover:bg-brand-50"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="max-w-2xl mx-auto space-y-4">
          {msgs.map((m, i) => (
            <div key={i} className={m.role === "user" ? "flex justify-end" : ""}>
              <div
                className={`rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap max-w-[85%] ${
                  m.role === "user"
                    ? "bg-brand text-black"
                    : "bg-surface border border-border"
                }`}
              >
                {m.content}
                {m.tools && m.tools.length > 0 && (
                  <div className="mt-2 text-xs text-muted">
                    🔧 used: {m.tools.join(", ")}
                  </div>
                )}
                {m.approval && (
                  <div className="mt-3 border-t border-border pt-3">
                    <p className="text-xs text-muted mb-2">Approve this action?</p>
                    <div className="flex gap-2">
                      <Button
                        onClick={() => decide(i, m.approval!.action_id, "approve")}
                        disabled={busy}
                      >
                        Approve
                      </Button>
                      <Button
                        variant="ghost"
                        onClick={() => decide(i, m.approval!.action_id, "reject")}
                        disabled={busy}
                      >
                        Reject
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          {busy && <div className="text-sm text-muted">Thinking…</div>}
          <div ref={endRef} />
        </div>
      </div>

      <div className="border-t border-border bg-surface px-8 py-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="max-w-2xl mx-auto flex gap-2"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message…"
            className="flex-1 rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand-100"
          />
          <Button type="submit" disabled={busy || !input.trim()}>
            Send
          </Button>
        </form>
      </div>
    </div>
  );
}
