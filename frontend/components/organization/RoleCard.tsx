"use client";

interface Role {
  id: number;
  title: string;
  summary: string | null;
  responsibilities: string[];
  authority: string[];
  permissions: string[];
  reports_to: string | null;
  required_skills: string[];
  metrics: string[];
  status: string;
}

interface Props {
  role: Role;
  onClose: () => void;
}

export default function RoleCard({ role, onClose }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={onClose}>
      <div
        className="mx-4 max-h-[80vh] w-full max-w-lg overflow-y-auto rounded-xl border border-zinc-200 bg-white p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-zinc-900">{role.title}</h3>
            {role.summary && (
              <p className="text-sm text-zinc-500">{role.summary}</p>
            )}
          </div>
          <button onClick={onClose} className="rounded-lg p-1 hover:bg-zinc-100">
            <svg className="h-5 w-5 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {role.reports_to && (
          <div className="mb-3 text-xs text-zinc-500">
            Rapporte à: <span className="font-medium text-zinc-700">{role.reports_to}</span>
          </div>
        )}

        <div className="mb-3">
          <div className="mb-1 text-xs font-medium uppercase text-zinc-400">Responsabilités</div>
          <ul className="space-y-1">
            {role.responsibilities.map((r, i) => (
              <li key={i} className="text-sm text-zinc-700 flex items-start gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-500" />
                {r}
              </li>
            ))}
          </ul>
        </div>

        {(role.permissions ?? []).length > 0 && (
          <div className="mb-3">
            <div className="mb-1 text-xs font-medium uppercase text-zinc-400">Permissions</div>
            <div className="flex flex-wrap gap-1">
              {role.permissions.map((p, i) => (
                <span key={i} className="rounded bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600 font-mono">
                  {p}
                </span>
              ))}
            </div>
          </div>
        )}

        {(role.required_skills ?? []).length > 0 && (
          <div className="mb-3">
            <div className="mb-1 text-xs font-medium uppercase text-zinc-400">Compétences requises</div>
            <div className="flex flex-wrap gap-1">
              {role.required_skills.map((s, i) => (
                <span key={i} className="rounded bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}

        {(role.metrics ?? []).length > 0 && (
          <div className="mb-3">
            <div className="mb-1 text-xs font-medium uppercase text-zinc-400">Métriques</div>
            <div className="flex flex-wrap gap-1">
              {role.metrics.map((m, i) => (
                <span key={i} className="rounded bg-purple-50 px-2 py-0.5 text-xs text-purple-700">
                  {m}
                </span>
              ))}
            </div>
          </div>
        )}

        {role.authority && role.authority.length > 0 && (
          <div>
            <div className="mb-1 text-xs font-medium uppercase text-zinc-400">Autorité</div>
            <ul className="space-y-1">
              {role.authority.map((a, i) => (
                <li key={i} className="text-sm text-zinc-700 flex items-start gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                  {a}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
