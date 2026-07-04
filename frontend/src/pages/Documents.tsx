import { useState } from "react";
import { api, apiUpload } from "@/lib/api";
import { useToast } from "@/components/Toast";
import { PageHeader } from "@/components/Layout";
import { Button, Card, EmptyState, Input, Label, Textarea } from "@/components/ui";

const DOC_TYPES = [
  { value: "offer_letter", label: "Offer letter" },
  { value: "policy", label: "Policy" },
  { value: "email", label: "HR email" },
  { value: "warning_letter", label: "Warning letter" },
  { value: "job_description", label: "Job description" },
  { value: "custom", label: "Custom" },
];

export default function Documents() {
  const [tab, setTab] = useState<"generate" | "understand">("generate");
  return (
    <div>
      <PageHeader title="Document Studio" subtitle="Generate and understand HR documents with AI" />
      <div className="p-8 max-w-3xl space-y-6">
        <div className="flex gap-2">
          <button onClick={() => setTab("generate")} className={`px-4 py-2 rounded-xl text-sm font-medium ${tab === "generate" ? "bg-brand text-black" : "bg-surface border border-border"}`}>
            ✍️ Generate
          </button>
          <button onClick={() => setTab("understand")} className={`px-4 py-2 rounded-xl text-sm font-medium ${tab === "understand" ? "bg-brand text-black" : "bg-surface border border-border"}`}>
            🔍 Understand
          </button>
        </div>
        {tab === "generate" ? <Generate /> : <Understand />}
      </div>
    </div>
  );
}

function Generate() {
  const toast = useToast();
  const [docType, setDocType] = useState("offer_letter");
  const [details, setDetails] = useState("");
  const [content, setContent] = useState("");
  const [busy, setBusy] = useState(false);

  async function gen(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const r = await api<{ content: string }>("/documents/generate", {
        method: "POST",
        body: JSON.stringify({ doc_type: docType, details }),
      });
      setContent(r.content);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <Card className="p-6">
        <form onSubmit={gen} className="space-y-3">
          <div className="space-y-1">
            <Label>Document type</Label>
            <select className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm" value={docType} onChange={(e) => setDocType(e.target.value)}>
              {DOC_TYPES.map((d) => <option key={d.value} value={d.value}>{d.label}</option>)}
            </select>
          </div>
          <div className="space-y-1">
            <Label>Details</Label>
            <Textarea rows={4} value={details} onChange={(e) => setDetails(e.target.value)} placeholder="e.g. Offer for Priya Sharma, Backend Engineer, ₹18L/yr, start Aug 1, at Acme." />
          </div>
          <Button type="submit" disabled={busy || !details.trim()}>{busy ? "Writing…" : "🤖 Generate"}</Button>
        </form>
      </Card>

      {content && (
        <Card className="p-6 animate-in">
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-semibold text-sm">Draft (editable)</h3>
            <button onClick={() => { navigator.clipboard.writeText(content); toast("Copied.", "success"); }} className="text-xs text-brand-700 hover:underline">Copy</button>
          </div>
          <Textarea rows={16} value={content} onChange={(e) => setContent(e.target.value)} />
          <p className="text-[11px] text-muted mt-2">AI-drafted — review and edit before sending.</p>
        </Card>
      )}
    </div>
  );
}

interface Analysis {
  summary: string;
  key_terms: string[];
  red_flags: string[];
  text?: string;
}

function Understand() {
  const toast = useToast();
  const [text, setText] = useState("");
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [busy, setBusy] = useState(false);
  const [q, setQ] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [qBusy, setQBusy] = useState(false);

  async function analyze() {
    setBusy(true);
    setAnalysis(null);
    setAnswer(null);
    try {
      const r = await api<Analysis>("/documents/analyze", { method: "POST", body: JSON.stringify({ text }) });
      setAnalysis({ ...r, text });
    } finally {
      setBusy(false);
    }
  }

  async function upload(file: File) {
    setBusy(true);
    setAnalysis(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await apiUpload<Analysis>("/documents/analyze-upload", fd);
      setAnalysis(r);
      setText(r.text ?? "");
      toast("Analyzed.", "success");
    } finally {
      setBusy(false);
    }
  }

  async function ask() {
    if (!analysis?.text) return;
    setQBusy(true);
    try {
      const r = await api<{ answer: string }>("/documents/qa", { method: "POST", body: JSON.stringify({ text: analysis.text, question: q }) });
      setAnswer(r.answer);
    } finally {
      setQBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <Card className="p-6">
        <Label>Paste document text or upload a file</Label>
        <Textarea rows={6} value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste a contract, offer letter, policy…" className="mt-1" />
        <div className="flex gap-2 items-center mt-3">
          <Button onClick={analyze} disabled={busy || !text.trim()}>{busy ? "Analyzing…" : "🔍 Analyze"}</Button>
          <label className="btn-ghost cursor-pointer">
            Upload (.pdf/.txt)
            <input type="file" accept=".pdf,.txt,.md" className="hidden" onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
          </label>
        </div>
      </Card>

      {analysis && (
        <Card className="p-6 animate-in space-y-3">
          <div>
            <h3 className="font-semibold text-sm mb-1">Summary</h3>
            <p className="text-sm">{analysis.summary}</p>
          </div>
          {analysis.key_terms.length > 0 && (
            <div>
              <h3 className="font-semibold text-sm mb-1">Key terms</h3>
              <ul className="list-disc pl-5 text-sm text-muted">{analysis.key_terms.map((t, i) => <li key={i}>{t}</li>)}</ul>
            </div>
          )}
          {analysis.red_flags.length > 0 && (
            <div>
              <h3 className="font-semibold text-sm mb-1 text-red-700">⚠️ Red flags</h3>
              <ul className="list-disc pl-5 text-sm text-red-700">{analysis.red_flags.map((t, i) => <li key={i}>{t}</li>)}</ul>
            </div>
          )}
          <div className="border-t border-border pt-3">
            <Label>Ask about this document</Label>
            <div className="flex gap-2 mt-1">
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. What is the notice period?" />
              <Button onClick={ask} disabled={qBusy || !q.trim()}>{qBusy ? "…" : "Ask"}</Button>
            </div>
            {answer && <p className="text-sm mt-2 bg-brand-50 rounded-lg p-3 whitespace-pre-wrap animate-in">{answer}</p>}
          </div>
        </Card>
      )}

      {!analysis && !busy && <EmptyState text="Paste or upload a document to analyze it." />}
    </div>
  );
}
