import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/Layout";
import { Badge, Card, EmptyState } from "@/components/ui";

interface Action {
  id: string;
  tool_name: string;
  summary: string;
  args: Record<string, unknown>;
  status: string;
  result: Record<string, unknown> | null;
  created_at: string;
  decided_at: string | null;
}

export default function AgentConsole() {
  const [actions, setActions] = useState<Action[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<Action[]>("/agent/actions")
      .then(setActions)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader title="Agent Console" subtitle="Every action agents proposed or performed" />
      <div className="p-8 max-w-3xl">
        {loading ? (
          <EmptyState text="Loading…" />
        ) : actions.length === 0 ? (
          <EmptyState text="No agent actions yet." />
        ) : (
          <div className="space-y-2">
            {actions.map((a) => (
              <Card key={a.id} className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm">{a.summary}</p>
                    <p className="text-xs text-muted">
                      {a.tool_name} · {new Date(a.created_at).toLocaleString()}
                    </p>
                  </div>
                  <Badge status={a.status} />
                </div>
                {a.result && (
                  <pre className="mt-2 text-xs bg-background rounded-lg p-2 overflow-x-auto">
                    {JSON.stringify(a.result, null, 2)}
                  </pre>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
