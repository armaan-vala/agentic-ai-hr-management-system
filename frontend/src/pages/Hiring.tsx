import { useEffect, useState } from "react";
import { api, apiUpload } from "@/lib/api";
import { useToast } from "@/components/Toast";
import { PageHeader } from "@/components/Layout";
import { Button, Card, CardSkeleton, EmptyState, Input, Label, Textarea } from "@/components/ui";

interface Job {
  id: string;
  title: string;
  department: string;
  location: string;
  description: string;
  status: string;
  candidate_count: number;
}
interface Candidate {
  id: string;
  name: string;
  email: string;
  score: number | null;
  summary: string;
  strengths: string[];
  gaps: string[];
  status: string;
}

export default function Hiring() {
  const [job, setJob] = useState<Job | null>(null);
  return (
    <div>
      <PageHeader title="Hiring" subtitle="AI-powered applicant tracking" />
      <div className="p-8 max-w-3xl">
        {job ? <JobDetail job={job} onBack={() => setJob(null)} /> : <JobsList onOpen={setJob} />}
      </div>
    </div>
  );
}

function JobsList({ onOpen }: { onOpen: (j: Job) => void }) {
  const toast = useToast();
  const [jobs, setJobs] = useState<Job[] | null>(null);
  const [form, setForm] = useState({ title: "", department: "", location: "", description: "" });
  const [brief, setBrief] = useState("");
  const [genBusy, setGenBusy] = useState(false);
  const [busy, setBusy] = useState(false);
  const [showForm, setShowForm] = useState(false);

  async function load() {
    setJobs(await api<Job[]>("/hiring/jobs"));
  }
  useEffect(() => {
    load();
  }, []);

  async function generateJd() {
    setGenBusy(true);
    try {
      const r = await api<{ description: string }>("/hiring/jobs/generate-jd", {
        method: "POST",
        body: JSON.stringify({ title: form.title, brief, department: form.department, location: form.location }),
      });
      setForm({ ...form, description: r.description });
      toast("JD drafted by AI — edit as needed.", "success");
    } finally {
      setGenBusy(false);
    }
  }

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await api("/hiring/jobs", { method: "POST", body: JSON.stringify(form) });
      setForm({ title: "", department: "", location: "", description: "" });
      setBrief("");
      setShowForm(false);
      await load();
      toast("Job posted.", "success");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold">Open roles</h3>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? "Close" : "New job"}</Button>
      </div>

      {showForm && (
        <Card className="p-6 animate-in">
          <form onSubmit={create} className="space-y-3">
            <div className="grid sm:grid-cols-3 gap-3">
              <div className="space-y-1 sm:col-span-1">
                <Label>Title</Label>
                <Input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Backend Engineer" />
              </div>
              <div className="space-y-1">
                <Label>Department</Label>
                <Input value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} placeholder="Engineering" />
              </div>
              <div className="space-y-1">
                <Label>Location</Label>
                <Input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} placeholder="Remote" />
              </div>
            </div>
            <div className="space-y-1">
              <Label>Brief (for AI to draft the JD)</Label>
              <div className="flex gap-2">
                <Input value={brief} onChange={(e) => setBrief(e.target.value)} placeholder="3+ yrs Python, FastAPI, Postgres…" />
                <Button type="button" variant="ghost" onClick={generateJd} disabled={genBusy || !form.title}>
                  {genBusy ? "Drafting…" : "🤖 Generate JD"}
                </Button>
              </div>
            </div>
            <div className="space-y-1">
              <Label>Description</Label>
              <Textarea rows={6} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Job description…" />
            </div>
            <Button type="submit" disabled={busy || !form.title}>Post job</Button>
          </form>
        </Card>
      )}

      {!jobs ? (
        <div className="space-y-2"><CardSkeleton /><CardSkeleton /></div>
      ) : jobs.length === 0 ? (
        <EmptyState text="No jobs yet. Post one to start hiring." />
      ) : (
        <div className="space-y-2">
          {jobs.map((j) => (
            <Card key={j.id} className="p-4 flex items-center justify-between hover:shadow-sm transition cursor-pointer" >
              <button className="text-left flex-1" onClick={() => onOpen(j)}>
                <p className="font-medium text-sm">{j.title}</p>
                <p className="text-xs text-muted">
                  {[j.department, j.location].filter(Boolean).join(" · ")} · {j.candidate_count} candidate(s)
                </p>
              </button>
              <Button variant="ghost" onClick={() => onOpen(j)}>Open</Button>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function scoreColor(s: number | null) {
  if (s === null) return "bg-gray-100 text-gray-600";
  if (s >= 75) return "bg-green-100 text-green-800";
  if (s >= 50) return "bg-brand-100 text-brand-800";
  return "bg-red-100 text-red-800";
}

function JobDetail({ job, onBack }: { job: Job; onBack: () => void }) {
  const toast = useToast();
  const [cands, setCands] = useState<Candidate[] | null>(null);
  const [form, setForm] = useState({ name: "", email: "", resume_text: "" });
  const [busy, setBusy] = useState(false);

  async function load() {
    setCands(await api<Candidate[]>(`/hiring/jobs/${job.id}/candidates`));
  }
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [job.id]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await api(`/hiring/jobs/${job.id}/candidates`, { method: "POST", body: JSON.stringify(form) });
      setForm({ name: "", email: "", resume_text: "" });
      toast("Candidate added & AI-scored.", "success");
      await load();
    } finally {
      setBusy(false);
    }
  }

  async function upload(file: File) {
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      await apiUpload(`/hiring/jobs/${job.id}/candidates/upload?name=${encodeURIComponent(file.name)}`, fd);
      toast("Resume uploaded & scored.", "success");
      await load();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <button onClick={onBack} className="text-sm text-brand-700 hover:underline">← All jobs</button>
      <div>
        <h2 className="text-xl font-bold">{job.title}</h2>
        <p className="text-xs text-muted">{[job.department, job.location].filter(Boolean).join(" · ")}</p>
      </div>

      <Card className="p-6">
        <h3 className="font-semibold mb-3">Add candidate</h3>
        <form onSubmit={add} className="space-y-3">
          <div className="grid sm:grid-cols-2 gap-3">
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Candidate name" required />
            <Input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="email (optional)" />
          </div>
          <Textarea rows={4} value={form.resume_text} onChange={(e) => setForm({ ...form, resume_text: e.target.value })} placeholder="Paste resume text…" />
          <div className="flex gap-2 items-center">
            <Button type="submit" disabled={busy || !form.name}>Add & score</Button>
            <label className="btn-ghost cursor-pointer">
              Upload resume (.pdf/.txt)
              <input type="file" accept=".pdf,.txt,.md" className="hidden"
                onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
            </label>
          </div>
        </form>
      </Card>

      <div>
        <h3 className="font-semibold mb-3">Candidates (ranked)</h3>
        {!cands ? (
          <div className="space-y-2"><CardSkeleton /><CardSkeleton /></div>
        ) : cands.length === 0 ? (
          <EmptyState text="No candidates yet." />
        ) : (
          <div className="space-y-2">
            {cands.map((c) => (
              <CandidateCard key={c.id} c={c} onChange={load} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function CandidateCard({ c, onChange }: { c: Candidate; onChange: () => void }) {
  const [questions, setQuestions] = useState<string[] | null>(null);
  const [qBusy, setQBusy] = useState(false);

  async function setStatus(status: string) {
    await api(`/hiring/candidates/${c.id}`, { method: "PATCH", body: JSON.stringify({ status }) });
    onChange();
  }
  async function genQuestions() {
    setQBusy(true);
    try {
      const r = await api<{ questions: string[] }>(`/hiring/candidates/${c.id}/interview-questions`, { method: "POST" });
      setQuestions(r.questions);
    } finally {
      setQBusy(false);
    }
  }

  return (
    <Card className="p-4 animate-in">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <span className={`text-sm font-bold px-2.5 py-1 rounded-lg ${scoreColor(c.score)}`}>
            {c.score === null ? "—" : c.score}
          </span>
          <div>
            <p className="font-medium text-sm">{c.name} <span className="text-xs text-muted capitalize">· {c.status}</span></p>
            {c.email && <p className="text-xs text-muted">{c.email}</p>}
          </div>
        </div>
      </div>
      {c.summary && <p className="text-sm mt-2">{c.summary}</p>}
      {(c.strengths.length > 0 || c.gaps.length > 0) && (
        <div className="grid sm:grid-cols-2 gap-3 mt-2 text-xs">
          <div>
            <p className="font-semibold text-green-700 mb-1">Strengths</p>
            <ul className="list-disc pl-4 text-muted">{c.strengths.map((s, i) => <li key={i}>{s}</li>)}</ul>
          </div>
          <div>
            <p className="font-semibold text-red-700 mb-1">Gaps</p>
            <ul className="list-disc pl-4 text-muted">{c.gaps.map((g, i) => <li key={i}>{g}</li>)}</ul>
          </div>
        </div>
      )}
      <div className="flex flex-wrap gap-2 mt-3">
        <Button onClick={() => setStatus("shortlisted")}>Shortlist</Button>
        <Button variant="ghost" onClick={() => setStatus("rejected")}>Reject</Button>
        <button onClick={genQuestions} disabled={qBusy} className="text-xs font-semibold text-brand-700 hover:underline">
          🤖 {qBusy ? "Generating…" : "Interview questions"}
        </button>
      </div>
      {questions && (
        <ol className="list-decimal pl-5 mt-3 text-sm space-y-1 animate-in">
          {questions.map((q, i) => <li key={i}>{q}</li>)}
        </ol>
      )}
    </Card>
  );
}
