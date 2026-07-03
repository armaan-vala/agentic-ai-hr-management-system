import { useState } from "react";
import { supabase } from "@/lib/supabase";
import { Button, Card, Input, Label } from "@/components/ui";

export default function Login() {
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      if (mode === "signin") {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
      } else {
        const { data, error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        if (!data.session) {
          setMsg("Account created. If email confirmation is on, check your inbox, then sign in.");
          setMode("signin");
        }
      }
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <Card className="w-full max-w-md p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="h-10 w-10 rounded-xl bg-brand flex items-center justify-center font-bold text-black">
            T
          </div>
          <div>
            <h1 className="text-xl font-bold">TalentOS</h1>
            <p className="text-sm text-muted">Agentic HRMS</p>
          </div>
        </div>

        <h2 className="text-lg font-semibold mb-4">
          {mode === "signin" ? "Sign in" : "Create your workspace"}
        </h2>

        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-1">
            <Label>Email</Label>
            <Input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
            />
          </div>
          <div className="space-y-1">
            <Label>Password</Label>
            <Input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>

          {msg && <p className="text-sm text-brand-800 bg-brand-50 rounded-lg p-2">{msg}</p>}

          <Button type="submit" disabled={busy} className="w-full">
            {busy ? "Please wait…" : mode === "signin" ? "Sign in" : "Sign up"}
          </Button>
        </form>

        <p className="text-sm text-muted mt-4 text-center">
          {mode === "signin" ? "New here?" : "Already have an account?"}{" "}
          <button
            className="font-semibold text-brand-700 hover:underline"
            onClick={() => {
              setMode(mode === "signin" ? "signup" : "signin");
              setMsg(null);
            }}
          >
            {mode === "signin" ? "Create a workspace" : "Sign in"}
          </button>
        </p>
      </Card>
    </div>
  );
}
