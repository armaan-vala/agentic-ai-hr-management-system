import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

type ToastKind = "success" | "error" | "info";
interface Toast {
  id: number;
  message: string;
  kind: ToastKind;
}

const ToastCtx = createContext<(message: string, kind?: ToastKind) => void>(() => {});

let counter = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((message: string, kind: ToastKind = "info") => {
    const id = ++counter;
    setToasts((t) => [...t, { id, message, kind }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3500);
  }, []);

  return (
    <ToastCtx.Provider value={toast}>
      {children}
      <div className="fixed top-4 right-4 z-[100] space-y-2 w-80">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`animate-in rounded-xl border px-4 py-3 text-sm shadow-lg bg-surface ${
              t.kind === "success"
                ? "border-green-200"
                : t.kind === "error"
                ? "border-red-200"
                : "border-border"
            }`}
          >
            <span className="mr-2">
              {t.kind === "success" ? "✅" : t.kind === "error" ? "⚠️" : "ℹ️"}
            </span>
            {t.message}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

export const useToast = () => useContext(ToastCtx);
