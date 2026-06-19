"use client";

import type { ProjectAnalysis } from "@/lib/types";

interface Props {
  analysis: ProjectAnalysis;
}

export default function AnalysisReport({ analysis }: Props) {
  const risks = analysis.risks ?? [];
  const assumptions = analysis.assumptions ?? [];
  const objectives = analysis.objectives ?? [];
  const constraints = analysis.constraints ?? [];

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-zinc-900">Rapport Stratégique</h3>

        <div className="mb-4">
          <div className="text-xs font-medium uppercase text-zinc-400">Résumé</div>
          <p className="mt-1 text-sm text-zinc-700">{analysis.summary}</p>
        </div>

        <div className="mb-4">
          <div className="text-xs font-medium uppercase text-zinc-400">Complexité estimée</div>
          <div className="mt-1 text-sm font-semibold text-zinc-900">
            {analysis.complexity?.toUpperCase() || "N/A"}
          </div>
          {analysis.complexity_rationale && (
            <p className="text-xs text-zinc-500">{analysis.complexity_rationale}</p>
          )}
        </div>

        <div className="mb-4">
          <div className="text-xs font-medium uppercase text-zinc-400">Durée estimée</div>
          <div className="mt-1 text-sm text-zinc-700">{analysis.estimated_duration || "N/A"}</div>
        </div>

        {objectives.length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-medium uppercase text-zinc-400">Objectifs</div>
            <ul className="mt-1 list-inside list-disc space-y-1">
              {objectives.map((o: string, i: number) => (
                <li key={i} className="text-sm text-zinc-700">{o}</li>
              ))}
            </ul>
          </div>
        )}

        {constraints.length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-medium uppercase text-zinc-400">Contraintes</div>
            <ul className="mt-1 list-inside list-disc space-y-1">
              {constraints.map((c: string, i: number) => (
                <li key={i} className="text-sm text-zinc-700">{c}</li>
              ))}
            </ul>
          </div>
        )}

        {risks.length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-medium uppercase text-zinc-400">Risques</div>
            <div className="mt-1 space-y-2">
              {risks.map((r: { risk: string; severity: string; mitigation: string }, i: number) => (
                <div key={i} className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
                  <div className="text-sm font-medium text-amber-800">
                    [{r.severity}] {r.risk}
                  </div>
                  <div className="text-xs text-amber-600">Mitigation: {r.mitigation}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {assumptions.length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-medium uppercase text-zinc-400">Hypothèses</div>
            <ul className="mt-1 list-inside list-disc space-y-1">
              {assumptions.map((a: string, i: number) => (
                <li key={i} className="text-sm text-zinc-700">{a}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
