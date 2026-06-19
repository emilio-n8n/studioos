"use client";

import StatsCard from "./StatsCard";

interface Risk {
  risk: string;
  severity: string;
  mitigation: string;
}

interface Decision {
  id: number;
  category: string;
  title: string;
  description: string | null;
  impact: string | null;
  created_at: string;
}

interface Props {
  dashboard: {
    total_tasks: number;
    tasks_by_status: Record<string, number>;
    total_agents: number;
    total_roles: number;
    total_departments: number;
    complexity: string | null;
    risks: Risk[] | null;
    total_decisions: number;
  };
  decisions?: Decision[];
}

const STATUS_COLORS: Record<string, string> = {
  TODO: "text-zinc-500",
  ASSIGNED: "text-blue-600",
  IN_PROGRESS: "text-amber-600",
  REVIEW: "text-purple-600",
  APPROVED: "text-green-600",
  MERGED: "text-emerald-600",
  ARCHIVED: "text-zinc-400",
};

const COMPLEXITY_COLORS: Record<string, string> = {
  low: "text-green-600 bg-green-50 border-green-200",
  medium: "text-amber-600 bg-amber-50 border-amber-200",
  high: "text-orange-600 bg-orange-50 border-orange-200",
  critical: "text-red-600 bg-red-50 border-red-200",
};

const CATEGORY_COLORS: Record<string, string> = {
  complexity: "border-l-purple-500 bg-purple-50",
  duration: "border-l-blue-500 bg-blue-50",
  risk: "border-l-red-500 bg-red-50",
  assumption: "border-l-amber-500 bg-amber-50",
  structure: "border-l-emerald-500 bg-emerald-50",
};

const CATEGORY_LABELS: Record<string, string> = {
  complexity: "Complexité",
  duration: "Durée",
  risk: "Risque",
  assumption: "Hypothèse",
  structure: "Structure",
};

export default function CEODashboard({ dashboard, decisions }: Props) {
  const progress =
    dashboard.total_tasks > 0
      ? Math.round(
          ((dashboard.tasks_by_status.MERGED || 0) +
            (dashboard.tasks_by_status.ARCHIVED || 0) +
            (dashboard.tasks_by_status.APPROVED || 0)) /
            dashboard.total_tasks *
            100
        )
      : 0;

  const dec = decisions ?? [];

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatsCard
          label="Complexité"
          value={dashboard.complexity || "N/A"}
          color={COMPLEXITY_COLORS[dashboard.complexity || ""]?.split(" ")[0]}
        />
        <StatsCard label="Départements" value={dashboard.total_departments} />
        <StatsCard label="Rôles" value={dashboard.total_roles} />
        <StatsCard label="Agents" value={dashboard.total_agents} color="text-blue-600" />
      </div>

      {/* Progress bar */}
      <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="text-sm font-medium text-zinc-500">Progression globale</div>
          <div className="text-xs text-zinc-400">{dashboard.total_tasks} tâches</div>
        </div>
        <div className="mt-2 h-3 w-full rounded-full bg-zinc-100">
          <div
            className="h-3 rounded-full bg-blue-600 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="mt-1 text-right text-xs text-zinc-400">{progress}%</div>
      </div>

      {/* Task status breakdown */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {Object.entries(dashboard.tasks_by_status).map(([status, count]) => (
          <StatsCard
            key={status}
            label={status}
            value={count}
            color={STATUS_COLORS[status]}
          />
        ))}
      </div>

      {/* Strategic Decisions Timeline */}
      {dec.length > 0 && (
        <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-zinc-900">
              Décisions Stratégiques
            </h3>
            <span className="text-xs text-zinc-400">{dec.length} décisions</span>
          </div>
          <div className="space-y-2">
            {dec.map((d) => (
              <div
                key={d.id}
                className={`rounded-lg border-l-4 px-3 py-2 text-sm ${
                  CATEGORY_COLORS[d.category] || "border-l-zinc-300 bg-zinc-50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">
                    {CATEGORY_LABELS[d.category] || d.category}
                  </span>
                  <span className="text-[10px] text-zinc-400">
                    {new Date(d.created_at).toLocaleTimeString()}
                  </span>
                </div>
                <div className="mt-0.5 font-medium text-zinc-900">{d.title}</div>
                {d.description && (
                  <div className="text-xs text-zinc-600">{d.description}</div>
                )}
                {d.impact && (
                  <div className="mt-0.5">
                    <span className="rounded bg-zinc-200 px-1.5 py-0.5 text-[10px] font-medium text-zinc-700">
                      {d.impact}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risks */}
      {(dashboard.risks ?? []).length > 0 && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4">
          <h3 className="mb-2 text-sm font-semibold text-red-800">
            Risques identifiés ({dashboard.risks!.length})
          </h3>
          <ul className="space-y-1">
            {dashboard.risks!.map((r, i) => (
              <li key={i} className="text-sm text-red-700">
                <span className="font-medium">{r.severity.toUpperCase()}:</span> {r.risk}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
