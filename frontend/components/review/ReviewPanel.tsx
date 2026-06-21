"use client";

import { useEffect, useState } from "react";
import { API_BASE } from "@/lib/config";

interface Review {
  id: number;
  task_id: number;
  project_id: number;
  reviewer_id: number | null;
  worker_id: number | null;
  status: string;
  output_ref: Record<string, unknown>;
  comments: { type: string; text: string; by?: string }[];
  attempt: number;
  created_at: string;
  updated_at: string;
}

interface Props {
  projectId: number;
}

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-amber-100 text-amber-700 border-amber-200",
  approved: "bg-green-100 text-green-700 border-green-200",
  changes_requested: "bg-red-100 text-red-700 border-red-200",
};



export default function ReviewPanel({ projectId }: Props) {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<number | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/projects/${projectId}/reviews`);
      if (res.ok) setReviews(await res.json());
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [projectId]);

  const handleApprove = async (reviewId: number) => {
    try {
      await fetch(`${API_BASE}/api/projects/${projectId}/reviews/${reviewId}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ approved_by: "Lead", comment: "Approved" }),
      });
      load();
    } catch {
      // ignore
    }
  };

  const handleRequestChanges = async (reviewId: number, comment: string) => {
    if (!comment) return;
    try {
      await fetch(`${API_BASE}/api/projects/${projectId}/reviews/${reviewId}/request-changes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ comment }),
      });
      load();
    } catch {
      // ignore
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-zinc-900">Reviews</h2>
          <span className="rounded bg-zinc-100 px-2 py-0.5 text-xs text-zinc-500">
            {reviews.length} revues
          </span>
        </div>
        <button
          onClick={load}
          className="rounded border border-zinc-300 px-2 py-1 text-xs hover:bg-zinc-100"
        >
          Actualiser
        </button>
      </div>

      {loading && <p className="text-sm text-zinc-400">Chargement...</p>}

      {!loading && reviews.length === 0 && (
        <p className="text-sm text-zinc-400 italic">Aucune revue en cours</p>
      )}

      <div className="space-y-2">
        {reviews.map((r) => {
          const badge = STATUS_STYLES[r.status] || "bg-zinc-100 text-zinc-600 border-zinc-200";
          const isExpanded = expanded === r.id;

          return (
            <div key={r.id} className="rounded-xl border border-zinc-200 bg-white shadow-sm">
              <button
                onClick={() => setExpanded(isExpanded ? null : r.id)}
                className="flex w-full items-center justify-between px-4 py-3 text-left"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-zinc-900">
                    Review #{r.id} — Tâche #{r.task_id}
                  </span>
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${badge}`}>
                    {r.status === "changes_requested" ? "Modifications" : r.status}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs text-zinc-400">
                  <span>Tentative {r.attempt}</span>
                  <svg className={`h-4 w-4 transition-transform ${isExpanded ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>

              {isExpanded && (
                <div className="border-t border-zinc-100 px-4 py-3 text-sm">
                  <div className="grid grid-cols-2 gap-2 text-xs text-zinc-600">
                    <div><span className="font-medium">Worker:</span> #{r.worker_id ?? "—"}</div>
                    <div><span className="font-medium">Reviewer:</span> #{r.reviewer_id ?? "—"}</div>
                    <div><span className="font-medium">Créée:</span> {new Date(r.created_at).toLocaleString()}</div>
                    <div><span className="font-medium">Mise à jour:</span> {new Date(r.updated_at).toLocaleString()}</div>
                  </div>

                  {/* Output */}
                  {Object.keys(r.output_ref).length > 0 && (
                    <div className="mt-3">
                      <div className="mb-1 text-xs font-medium text-zinc-500">Output soumis</div>
                      <pre className="max-h-24 overflow-auto rounded bg-zinc-50 p-2 text-[10px] text-zinc-600">
                        {JSON.stringify(r.output_ref, null, 2)}
                      </pre>
                    </div>
                  )}

                  {/* Comments */}
                  {r.comments.length > 0 && (
                    <div className="mt-3">
                      <div className="mb-1 text-xs font-medium text-zinc-500">Commentaires</div>
                      <div className="space-y-1">
                        {r.comments.map((c, i) => (
                          <div key={i} className="rounded-lg bg-zinc-50 p-2 text-xs">
                            <span className="font-medium text-zinc-500">
                              {c.type === "approve" ? "✓ Approuvé" : "✗ Modifications demandées"}
                              {c.by ? ` par ${c.by}` : ""}:
                            </span>{" "}
                            <span className="text-zinc-700">{c.text}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  {r.status === "pending" && (
                    <div className="mt-3 flex gap-2">
                      <button
                        onClick={() => handleApprove(r.id)}
                        className="rounded bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700"
                      >
                        Approuver
                      </button>
                      <button
                        onClick={() => {
                          const comment = prompt("Commentaire pour modifications:");
                          if (comment) handleRequestChanges(r.id, comment);
                        }}
                        className="rounded border border-red-300 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50"
                      >
                        Demander modifications
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
