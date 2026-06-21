"use client";

import { useEffect, useState } from "react";

interface GitCommit {
  hexsha: string;
  author: string;
  message: string;
  datetime: string;
  branches: string[];
}

interface PR {
  id: number;
  agent_id: number | null;
  source_branch: string;
  target_branch: string;
  status: string;
  title: string;
  description: string | null;
  created_at: string;
  merged_at: string | null;
}

interface Props {
  projectId: number;
}

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function GitPanel({ projectId }: Props) {
  const [commits, setCommits] = useState<GitCommit[]>([]);
  const [prs, setPrs] = useState<PR[]>([]);
  const [branches, setBranches] = useState<{ name: string; commit: string; is_active: boolean }[]>([]);
  const [activeTab, setActiveTab] = useState<"commits" | "prs" | "branches">("commits");
  const [loading, setLoading] = useState(true);

  const loadAll = async () => {
    setLoading(true);
    try {
      const base = `${API}/api/projects/${projectId}/git`;
      const [logRes, prRes, branchRes] = await Promise.all([
        fetch(`${base}/log`),
        fetch(`${base}/prs`),
        fetch(`${base}/branches`),
      ]);
      if (logRes.ok) {
        const d = await logRes.json();
        setCommits(d.commits ?? []);
      }
      if (prRes.ok) setPrs(await prRes.json());
      if (branchRes.ok) {
        const d = await branchRes.json();
        setBranches(d.branches ?? []);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, [projectId]);

  const handleMerge = async (prId: number) => {
    try {
      const res = await fetch(`${API}/api/projects/${projectId}/git/pr/${prId}/merge`, { method: "POST" });
      if (res.ok) loadAll();
    } catch {
      // ignore
    }
  };

  const tabs = [
    { key: "commits" as const, label: "Commits", count: commits.length },
    { key: "prs" as const, label: "Pull Requests", count: prs.length },
    { key: "branches" as const, label: "Branches", count: branches.length },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-zinc-900">Git</h2>
        <button
          onClick={loadAll}
          className="rounded border border-zinc-300 px-2 py-1 text-xs hover:bg-zinc-100"
        >
          Actualiser
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-zinc-200">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`px-3 py-2 text-xs font-medium ${
              activeTab === t.key
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-zinc-500 hover:text-zinc-700"
            }`}
          >
            {t.label} ({t.count})
          </button>
        ))}
      </div>

      {loading && <p className="text-sm text-zinc-400">Chargement...</p>}

      {/* Commits */}
      {!loading && activeTab === "commits" && (
        <div className="space-y-1">
          {commits.length === 0 && (
            <p className="text-sm text-zinc-400 italic">Aucun commit</p>
          )}
          {commits.map((c) => (
            <div key={c.hexsha} className="flex items-start gap-3 rounded-lg border border-zinc-200 bg-white p-3 text-sm">
              <div className="mt-0.5 h-2 w-2 rounded-full bg-blue-500" />
              <div className="min-w-0 flex-1">
                <div className="font-medium text-zinc-900">{c.message}</div>
                <div className="mt-0.5 flex items-center gap-2 text-xs text-zinc-400">
                  <span>{c.author}</span>
                  <span>•</span>
                  <span>{new Date(c.datetime).toLocaleString()}</span>
                  <span>•</span>
                  <span className="font-mono text-[10px]">{c.hexsha.slice(0, 8)}</span>
                </div>
                {c.branches.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {c.branches.map((b) => (
                      <span key={b} className="rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] text-zinc-600">
                        {b}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* PRs */}
      {!loading && activeTab === "prs" && (
        <div className="space-y-2">
          {prs.length === 0 && (
            <p className="text-sm text-zinc-400 italic">Aucune pull request</p>
          )}
          {prs.map((pr) => (
            <div key={pr.id} className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`h-2 w-2 rounded-full ${
                      pr.status === "open" ? "bg-green-500" : "bg-zinc-400"
                    }`} />
                    <span className="font-medium text-zinc-900">{pr.title}</span>
                  </div>
                  <div className="mt-1 text-xs text-zinc-500">
                    {pr.source_branch} → {pr.target_branch}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    pr.status === "open"
                      ? "bg-green-100 text-green-700"
                      : "bg-zinc-100 text-zinc-500"
                  }`}>
                    {pr.status}
                  </span>
                  {pr.status === "open" && (
                    <button
                      onClick={() => handleMerge(pr.id)}
                      className="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700"
                    >
                      Merge
                    </button>
                  )}
                </div>
              </div>
              {pr.description && (
                <div className="mt-2 text-xs text-zinc-600">{pr.description}</div>
              )}
              <div className="mt-2 text-[10px] text-zinc-400">
                Créée le {new Date(pr.created_at).toLocaleString()}
                {pr.merged_at && ` | Mergée le ${new Date(pr.merged_at).toLocaleString()}`}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Branches */}
      {!loading && activeTab === "branches" && (
        <div className="space-y-1">
          {branches.length === 0 && (
            <p className="text-sm text-zinc-400 italic">Aucune branche</p>
          )}
          {branches.map((b) => (
            <div key={b.name} className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white p-3 text-sm">
              <div className="flex items-center gap-2">
                <span className={`h-2 w-2 rounded-full ${b.is_active ? "bg-blue-500" : "bg-zinc-300"}`} />
                <span className="font-medium text-zinc-900">{b.name}</span>
              </div>
              <div className="text-xs text-zinc-400">
                {b.is_active && <span className="text-blue-600">active</span>}
                {" "}{b.commit.slice(0, 8)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
