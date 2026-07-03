import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/auth/AuthProvider";
import { useToast } from "@/components/Toast";
import { PageHeader } from "@/components/Layout";
import { Badge, Button, Card, CardSkeleton, EmptyState, Input, Label } from "@/components/ui";

interface Structure {
  user_id: string;
  name: string;
  email: string;
  basic: number;
  hra: number;
  allowances: number;
  deductions: number;
  gross: number;
  net: number;
  currency: string;
  has_structure: boolean;
}
interface Slip {
  id: string;
  month?: string;
  name?: string;
  employee_name?: string;
  basic: number;
  hra: number;
  allowances: number;
  deductions: number;
  gross: number;
  net: number;
  currency: string;
  status: string;
}

function thisMonth() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export default function Payroll() {
  const { me } = useAuth();
  return me?.role === "admin" ? <AdminPayroll /> : <EmployeePayslips />;
}

/* ---------------- Admin ---------------- */
function AdminPayroll() {
  const toast = useToast();
  const [structures, setStructures] = useState<Structure[] | null>(null);
  const [month, setMonth] = useState(thisMonth());
  const [slips, setSlips] = useState<Slip[]>([]);
  const [edit, setEdit] = useState<Structure | null>(null);

  async function loadStructures() {
    setStructures(await api<Structure[]>("/payroll/structures"));
  }
  async function loadSlips() {
    setSlips(await api<Slip[]>(`/payroll/payslips?month=${month}`));
  }
  useEffect(() => {
    loadStructures();
  }, []);
  useEffect(() => {
    loadSlips();
  }, [month]);

  async function generate() {
    const r = await api<{ created: number; updated: number }>("/payroll/generate", {
      method: "POST",
      body: JSON.stringify({ month }),
    });
    toast(`Generated ${r.created + r.updated} payslips (draft).`, "success");
    loadSlips();
  }
  async function release() {
    const r = await api<{ released: number }>("/payroll/release", {
      method: "POST",
      body: JSON.stringify({ month }),
    });
    toast(`Released ${r.released} payslips.`, "success");
    loadSlips();
  }

  return (
    <div>
      <PageHeader title="Payroll" subtitle="Salary structures & payslips" />
      <div className="p-8 max-w-4xl space-y-6">
        <Card className="p-6">
          <h3 className="font-semibold mb-4">Run payroll</h3>
          <div className="flex flex-wrap items-end gap-3">
            <div className="space-y-1">
              <Label>Month</Label>
              <Input type="month" value={month} onChange={(e) => setMonth(e.target.value)} className="w-44" />
            </div>
            <Button onClick={generate}>Generate payslips</Button>
            <Button variant="ghost" onClick={release}>Release all</Button>
          </div>
          {slips.length > 0 && (
            <div className="mt-4 space-y-1">
              {slips.map((s) => (
                <div key={s.id} className="flex items-center justify-between text-sm border-b border-border py-1.5">
                  <span>{s.name}</span>
                  <span className="flex items-center gap-3">
                    <span className="text-muted">{s.currency} {s.net.toLocaleString()}</span>
                    <Badge status={s.status} />
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>

        <div>
          <h3 className="font-semibold mb-3">Salary structures</h3>
          {!structures ? (
            <div className="space-y-2"><CardSkeleton /><CardSkeleton /></div>
          ) : (
            <div className="space-y-2">
              {structures.map((s) => (
                <Card key={s.user_id} className="p-4 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm">{s.name}</p>
                    <p className="text-xs text-muted">
                      {s.has_structure ? `Net ${s.currency} ${s.net.toLocaleString()}/mo` : "No salary set"}
                    </p>
                  </div>
                  <Button variant="ghost" onClick={() => setEdit(s)}>
                    {s.has_structure ? "Edit" : "Set salary"}
                  </Button>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {edit && (
        <StructureEditor
          row={edit}
          onClose={() => setEdit(null)}
          onSaved={() => {
            setEdit(null);
            loadStructures();
            toast("Salary updated.", "success");
          }}
        />
      )}
    </div>
  );
}

function StructureEditor({ row, onClose, onSaved }: { row: Structure; onClose: () => void; onSaved: () => void }) {
  const [f, setF] = useState({ basic: row.basic, hra: row.hra, allowances: row.allowances, deductions: row.deductions, currency: row.currency });
  const [busy, setBusy] = useState(false);
  const gross = f.basic + f.hra + f.allowances;
  const net = gross - f.deductions;

  async function save() {
    setBusy(true);
    try {
      await api(`/payroll/structure/${row.user_id}`, { method: "PUT", body: JSON.stringify(f) });
      onSaved();
    } finally {
      setBusy(false);
    }
  }

  const field = (k: keyof typeof f, label: string) => (
    <div className="space-y-1">
      <Label>{label}</Label>
      <Input type="number" value={f[k] as number} onChange={(e) => setF({ ...f, [k]: Number(e.target.value) })} />
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center p-6 z-50" onClick={onClose}>
      <div className="w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <Card className="p-6">
          <h3 className="font-semibold mb-4">{row.name} — salary</h3>
          <div className="grid grid-cols-2 gap-3">
            {field("basic", "Basic")}
            {field("hra", "HRA")}
            {field("allowances", "Allowances")}
            {field("deductions", "Deductions")}
          </div>
          <div className="mt-4 text-sm bg-brand-50 rounded-lg p-3">
            Gross <b>{gross.toLocaleString()}</b> · Net take-home <b>{net.toLocaleString()}</b> {f.currency}
          </div>
          <div className="flex gap-2 mt-4">
            <Button onClick={save} disabled={busy}>{busy ? "Saving…" : "Save"}</Button>
            <Button variant="ghost" onClick={onClose}>Cancel</Button>
          </div>
        </Card>
      </div>
    </div>
  );
}

/* ---------------- Employee ---------------- */
function EmployeePayslips() {
  const [slips, setSlips] = useState<Slip[] | null>(null);
  const [open, setOpen] = useState<Slip | null>(null);

  useEffect(() => {
    api<Slip[]>("/payslips/mine").then(setSlips);
  }, []);

  return (
    <div>
      <PageHeader title="Payslips" subtitle="Your monthly payslips" />
      <div className="p-8 max-w-2xl space-y-4">
        {!slips ? (
          <div className="space-y-2"><CardSkeleton /><CardSkeleton /></div>
        ) : slips.length === 0 ? (
          <EmptyState text="No payslips released yet." />
        ) : (
          slips.map((s) => (
            <Card key={s.id} className="p-4 flex items-center justify-between">
              <div>
                <p className="font-medium text-sm">{s.month}</p>
                <p className="text-xs text-muted">Net {s.currency} {s.net.toLocaleString()}</p>
              </div>
              <Button variant="ghost" onClick={() => setOpen(s)}>View</Button>
            </Card>
          ))
        )}
      </div>

      {open && <PayslipModal slip={open} onClose={() => setOpen(null)} />}
    </div>
  );
}

function PayslipModal({ slip, onClose }: { slip: Slip; onClose: () => void }) {
  const rows: [string, number][] = [
    ["Basic", slip.basic],
    ["HRA", slip.hra],
    ["Allowances", slip.allowances],
  ];
  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center p-6 z-50" onClick={onClose}>
      <div className="w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <Card className="p-6 print-area">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold">Payslip · {slip.month}</h3>
              <p className="text-xs text-muted">{slip.employee_name}</p>
            </div>
            <div className="h-8 w-8 rounded-lg bg-brand flex items-center justify-center font-bold text-black">T</div>
          </div>
          <div className="space-y-1 text-sm">
            {rows.map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <span className="text-muted">{k}</span>
                <span>{slip.currency} {v.toLocaleString()}</span>
              </div>
            ))}
            <div className="flex justify-between border-t border-border pt-1 mt-1">
              <span>Gross</span>
              <span className="font-medium">{slip.currency} {slip.gross.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-red-600">
              <span>Deductions</span>
              <span>- {slip.currency} {slip.deductions.toLocaleString()}</span>
            </div>
            <div className="flex justify-between border-t border-border pt-2 mt-1 text-base">
              <span className="font-semibold">Net pay</span>
              <span className="font-bold text-brand-700">{slip.currency} {slip.net.toLocaleString()}</span>
            </div>
          </div>
          <div className="flex gap-2 mt-5 no-print">
            <Button onClick={() => window.print()}>Print / Save PDF</Button>
            <Button variant="ghost" onClick={onClose}>Close</Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
