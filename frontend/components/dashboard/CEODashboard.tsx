"use client";

import StatsCard from "./StatsCard";

interface Props {
  dashboard: {
    total_tasks: number;
    tasks_by_status: Record<string, number>;
    total_agents: number;
    total_roles: number;
    total_departments: number;
    complexity: string | null;
    risks: { risk: string; severity: string }[] | null;
  };
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
  low: "text-green-600",
  medium: "text-amber-600",
  high: "text-orange-600",
  critical: "text-red-600",
};

export default function CEODashboard({ dashboard }: Props) {
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

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatsCard
          label="Complexité"
          value={dashboard.complexity || "N/A"}
          color={COMPLEXITY_COLORS[dashboard.complexity || ""]}
        />
        <StatsCard label="Départements" value={dashboard.total_departments} />
        <StatsCard label="Rôles" value={dashboard.total_roles} />
        <StatsCard label="Agents" value={dashboard.total_agents} color="text-blue-600" />
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
        <div className="mb-2 text-sm font-medium text-zinc-500">Progression globale</div>
        <div className="h-3 w-full rounded-full bg-zinc-100">
          <div
            className="h-3 rounded-full bg-blue-600 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="mt-1 text-right text-xs text-zinc-400">{progress}%</div>
      </div>

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
