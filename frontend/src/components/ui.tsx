import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  TextareaHTMLAttributes,
} from "react";

export function Button({
  variant = "brand",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "brand" | "ghost" }) {
  const base = variant === "brand" ? "btn-brand" : "btn-ghost";
  return <button className={`${base} ${className}`} {...props} />;
}

export function Card({
  className = "",
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return <div className={`card ${className}`}>{children}</div>;
}

export function Input({ className = "", ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={`w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm
        outline-none focus:border-brand focus:ring-2 focus:ring-brand-100 ${className}`}
      {...props}
    />
  );
}

export function Textarea({
  className = "",
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={`w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm
        outline-none focus:border-brand focus:ring-2 focus:ring-brand-100 ${className}`}
      {...props}
    />
  );
}

export function Label({ children }: { children: ReactNode }) {
  return <label className="text-sm font-medium text-foreground">{children}</label>;
}

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-brand-100 text-brand-800",
  open: "bg-brand-100 text-brand-800",
  approved: "bg-green-100 text-green-800",
  resolved: "bg-green-100 text-green-800",
  executed: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  failed: "bg-red-100 text-red-800",
};

export function Badge({ status, label }: { status: string; label?: string }) {
  const cls = STATUS_STYLES[status] ?? "bg-gray-100 text-gray-700";
  return (
    <span className={`inline-block text-xs font-semibold px-2.5 py-1 rounded-full ${cls}`}>
      {label ?? status}
    </span>
  );
}

export function Spinner() {
  return (
    <div className="h-5 w-5 animate-spin rounded-full border-2 border-brand-200 border-t-brand" />
  );
}

export function EmptyState({ text }: { text: string }) {
  return <div className="text-center text-muted py-12 text-sm">{text}</div>;
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton h-4 ${className}`} />;
}

export function CardSkeleton() {
  return (
    <Card className="p-4 space-y-2">
      <Skeleton className="w-1/3" />
      <Skeleton className="w-2/3" />
    </Card>
  );
}
