"use client";

interface Props {
  tasksByStatus: Record<string, number>;
}

const STAGES = ["TODO", "ASSIGNED", "IN_PROGRESS", "REVIEW", "APPROVED", "MERGED"];

const STAGE_LABELS: Record<string, string> = {
  TODO: "À faire",
  ASSIGNED: "Assignées",
  IN_PROGRESS: "En cours",
  REVIEW: "Revue",
  APPROVED: "Approuvées",
  MERGED: "Fusionnées",
};

export default function ProductionFlow({ tasksByStatus }: Props) {
  const maxCount = Math.max(...Object.values(tasksByStatus), 1);

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-zinc-900">Production Flow</h3>
      <div className="flex items-end gap-2">
        {STAGES.map((stage) => {
          const count = tasksByStatus[stage] || 0;
          const height = Math.max((count / maxCount) * 120, count > 0 ? 24 : 8);
          return (
            <div key={stage} className="flex flex-1 flex-col items-center gap-1">
              <span className="text-xs font-medium text-zinc-500">{count}</span>
              <div
                className="w-full rounded-t-md bg-blue-500 transition-all"
                style={{ height: `${height}px` }}
              />
              <span className="text-center text-[10px] text-zinc-400">{STAGE_LABELS[stage]}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
