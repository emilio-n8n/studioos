"use client";

import type { Task } from "@/lib/types";
import { transitionTask } from "@/lib/api";

const STATUS_ORDER = ["TODO", "ASSIGNED", "IN_PROGRESS", "REVIEW", "APPROVED", "MERGED", "ARCHIVED"];

interface Props {
  tasks: Task[];
  projectId: number;
  onRefresh: () => void;
}

function nextStatuses(current: string): string[] {
  const idx = STATUS_ORDER.indexOf(current);
  if (idx === -1 || idx >= STATUS_ORDER.length - 1) return [];
  const next = STATUS_ORDER[idx + 1];
  const prev = idx > 0 ? STATUS_ORDER[idx - 1] : null;
  const result = [next];
  if (prev && current !== "TODO") result.unshift(prev);
  return result;
}

export default function TaskBoard({ tasks, projectId, onRefresh }: Props) {
  const handleTransition = async (taskId: number, status: string) => {
    try {
      await transitionTask(projectId, taskId, status);
      onRefresh();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-2">
      {tasks.map((task) => (
        <div key={task.id} className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white px-4 py-3 shadow-sm">
          <div className="flex-1">
            <div className="text-sm font-medium text-zinc-900">{task.title}</div>
            <div className="text-xs text-zinc-500">
              Priorité: {task.priority} | Coût: {task.estimated_cost}
              {task.assigned_agent_id && ` | Agent #${task.assigned_agent_id}`}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
              task.status === "TODO" ? "bg-zinc-100 text-zinc-600" :
              task.status === "IN_PROGRESS" ? "bg-amber-100 text-amber-700" :
              task.status === "APPROVED" ? "bg-green-100 text-green-700" :
              task.status === "MERGED" ? "bg-emerald-100 text-emerald-700" :
              task.status === "ARCHIVED" ? "bg-zinc-100 text-zinc-400" :
              "bg-blue-100 text-blue-700"
            }`}>
              {task.status}
            </span>
            <div className="flex gap-1">
              {nextStatuses(task.status).map((ns) => (
                <button
                  key={ns}
                  onClick={() => handleTransition(task.id, ns)}
                  className="rounded bg-zinc-100 px-2 py-1 text-xs text-zinc-600 hover:bg-zinc-200"
                >
                  {ns === STATUS_ORDER[STATUS_ORDER.indexOf(task.status) + 1] ? "→" : "←"}
                </button>
              ))}
            </div>
          </div>
        </div>
      ))}
      {tasks.length === 0 && (
        <p className="py-8 text-center text-sm text-zinc-400">Aucune tâche</p>
      )}
    </div>
  );
}
