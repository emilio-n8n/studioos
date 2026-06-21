"use client";

import { useEffect, useState } from "react";

interface MemoryNode {
  id: number;
  project_id: number;
  agent_id: number | null;
  parent_id: number | null;
  key: string;
  value: Record<string, unknown>;
  type: string;
  tags: string[];
  status: string;
  version: number;
  summary: string | null;
  created_by: string | null;
  approved_by: string | null;
  superseded_by: number | null;
  created_at: string;
}

interface MemoryEdge {
  source: number;
  target: number;
  type: string;
}

interface MemoryGraphData {
  nodes: MemoryNode[];
  edges: MemoryEdge[];
}

interface Props {
  projectId: number;
}

const TYPE_COLORS: Record<string, string> = {
  decision: "border-l-purple-500 bg-purple-50",
  fact: "border-l-blue-500 bg-blue-50",
  constraint: "border-l-red-500 bg-red-50",
  output: "border-l-emerald-500 bg-emerald-50",
  artifact: "border-l-amber-500 bg-amber-50",
};

const STATUS_BADGES: Record<string, string> = {
  active: "bg-green-100 text-green-700",
  superseded: "bg-zinc-100 text-zinc-500",
  rejected: "bg-red-100 text-red-700",
  proposed: "bg-amber-100 text-amber-700",
};

export default function MemoryGraph({ projectId }: Props) {
  const [graph, setGraph] = useState<MemoryGraphData | null>(null);
  const [filter, setFilter] = useState<string>("ALL");
  const [selected, setSelected] = useState<MemoryNode | null>(null);
  const [loading, setLoading] = useState(true);

  const loadGraph = async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/projects/${projectId}/memory/graph`
      );
      if (res.ok) setGraph(await res.json());
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraph();
  }, [projectId]);

  const nodes = graph?.nodes ?? [];
  const edges = graph?.edges ?? [];

  const filtered = filter === "ALL"
    ? nodes
    : filter === "ACTIVE"
    ? nodes.filter((n) => n.status === "active")
    : nodes.filter((n) => n.type === filter);

  const childMap = new Map<number, MemoryNode[]>();
  for (const n of nodes) {
    if (n.parent_id) {
      if (!childMap.has(n.parent_id)) childMap.set(n.parent_id, []);
      childMap.get(n.parent_id)!.push(n);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-zinc-900">Mémoire partagée</h2>
          <span className="rounded bg-zinc-100 px-2 py-0.5 text-xs text-zinc-500">
            {nodes.length} entrées
          </span>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="rounded border border-zinc-300 px-2 py-1 text-xs"
          >
            <option value="ALL">Toutes</option>
            <option value="ACTIVE">Actives</option>
            <option value="decision">Décisions</option>
            <option value="fact">Faits</option>
            <option value="constraint">Contraintes</option>
            <option value="output">Outputs</option>
          </select>
          <button
            onClick={loadGraph}
            className="rounded border border-zinc-300 px-2 py-1 text-xs hover:bg-zinc-100"
          >
            Actualiser
          </button>
        </div>
      </div>

      {loading && <p className="text-sm text-zinc-400">Chargement...</p>}

      {!loading && filtered.length === 0 && (
        <p className="text-sm text-zinc-400 italic">Aucune entrée mémoire</p>
      )}

      {/* Timeline */}
      <div className="space-y-2">
        {filtered.map((node) => {
          const children = childMap.get(node.id) ?? [];
          const color = TYPE_COLORS[node.type] || "border-l-zinc-300 bg-zinc-50";
          const badge = STATUS_BADGES[node.status] || "bg-zinc-100 text-zinc-600";

          return (
            <div key={node.id}>
              <button
                onClick={() => setSelected(selected?.id === node.id ? null : node)}
                className={`w-full rounded-lg border-l-4 p-3 text-left text-sm transition-colors hover:opacity-80 ${color}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${badge}`}>
                      {node.status}
                    </span>
                    <span className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">
                      {node.type}
                    </span>
                    <span className="text-[10px] text-zinc-400">v{node.version}</span>
                  </div>
                  <span className="text-[10px] text-zinc-400">
                    {new Date(node.created_at).toLocaleString()}
                  </span>
                </div>
                <div className="mt-1 font-medium text-zinc-900">{node.key}</div>
                {node.summary && (
                  <div className="text-xs text-zinc-500">{node.summary}</div>
                )}
                {node.created_by && (
                  <div className="mt-0.5 text-[10px] text-zinc-400">par {node.created_by}</div>
                )}
              </button>

              {/* Children */}
              {selected?.id === node.id && children.length > 0 && (
                <div className="ml-4 mt-1 space-y-1 border-l-2 border-zinc-200 pl-4">
                  {children.map((child) => (
                    <div
                      key={child.id}
                      className="rounded border border-zinc-200 bg-white p-2 text-xs text-zinc-600"
                    >
                      <span className="font-medium">{child.key}</span> v{child.version}
                      {child.summary && <span> — {child.summary}</span>}
                    </div>
                  ))}
                </div>
              )}

              {/* Detail expand */}
              {selected?.id === node.id && (
                <div className="mt-2 rounded-lg border border-zinc-200 bg-white p-3 text-xs">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <span className="font-medium text-zinc-500">ID:</span> {node.id}
                    </div>
                    <div>
                      <span className="font-medium text-zinc-500">Version:</span> {node.version}
                    </div>
                    {node.parent_id && (
                      <div>
                        <span className="font-medium text-zinc-500">Parent:</span> #{node.parent_id}
                      </div>
                    )}
                    {node.superseded_by && (
                      <div>
                        <span className="font-medium text-zinc-500">Remplace:</span> #{node.superseded_by}
                      </div>
                    )}
                    {node.approved_by && (
                      <div>
                        <span className="font-medium text-zinc-500">Approuvé par:</span> {node.approved_by}
                      </div>
                    )}
                  </div>
                  <div className="mt-2">
                    <span className="font-medium text-zinc-500">Tags:</span>{" "}
                    {(node.tags ?? []).length > 0
                      ? node.tags.join(", ")
                      : "—"}
                  </div>
                  <div className="mt-1">
                    <span className="font-medium text-zinc-500">Valeur:</span>
                    <pre className="mt-1 max-h-32 overflow-auto rounded bg-zinc-50 p-2 text-[10px] text-zinc-700">
                      {JSON.stringify(node.value, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Relationship graph */}
      {edges.length > 0 && (
        <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
          <h3 className="mb-2 text-sm font-semibold text-zinc-900">Relations ({edges.length})</h3>
          <div className="space-y-1">
            {edges.map((e, i) => {
              const src = nodes.find((n) => n.id === e.source);
              const tgt = nodes.find((n) => n.id === e.target);
              return (
                <div key={i} className="flex items-center gap-2 text-xs text-zinc-600">
                  <span className="font-medium">{src?.key ?? `#${e.source}`}</span>
                  <span className="text-zinc-300">
                    {e.type === "derives_from" ? "← dérive de" : "← remplacé par"}
                  </span>
                  <span className="font-medium">{tgt?.key ?? `#${e.target}`}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
