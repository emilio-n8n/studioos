"use client";

interface Props {
  generating: boolean;
  generatedUrl: string | null;
  genError: string | null;
  onGenerate: () => void;
}

export default function GenerationPanel({
  generating,
  generatedUrl,
  genError,
  onGenerate,
}: Props) {
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  let previewUrl: string | null = null;
  if (generatedUrl) {
    try {
      previewUrl = new URL(generatedUrl, apiBase).href;
    } catch {
      previewUrl = `${apiBase}${generatedUrl.startsWith("/") ? "" : "/"}${generatedUrl}`;
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h2 className="mb-2 text-lg font-semibold text-zinc-900">Génération du site web</h2>
        <p className="mb-6 text-sm text-zinc-500">
          StudioOS va orchestrer les agents pour produire le livrable final : un site web complet.
        </p>

        <button
          onClick={onGenerate}
          disabled={generating}
          className="rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {generating ? (
            <span className="flex items-center gap-2">
              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" aria-hidden="true">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Génération en cours...
            </span>
          ) : (
            "Générer le site web"
          )}
        </button>

        {generating && (
          <div className="mt-6 rounded-lg border border-blue-200 bg-blue-50 p-4">
            <div className="mb-2 text-sm font-medium text-blue-800">Les agents travaillent</div>
            <div className="h-2 w-full rounded-full bg-blue-200" role="progressbar" aria-valuenow={66} aria-valuemin={0} aria-valuemax={100}>
              <div className="h-2 w-2/3 animate-pulse rounded-full bg-blue-600" />
            </div>
            <ul className="mt-3 space-y-1 text-xs text-blue-700">
              <li>✓ Analyse stratégique du projet</li>
              <li>✓ Conception de l'organisation</li>
              <li>✓ Création des rôles et agents</li>
              <li className="animate-pulse text-blue-500">→ Génération du code par les agents...</li>
            </ul>
          </div>
        )}

        {genError && (
          <div className="mt-6 rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-700">
            {genError}
          </div>
        )}

        {previewUrl && (
          <div className="mt-6 space-y-4">
            <div className="rounded-lg border border-green-200 bg-green-50 p-4">
              <div className="text-sm font-medium text-green-800">
                Site généré avec succès !
              </div>
              <a
                href={previewUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-green-700 underline"
              >
                Ouvrir le site →
              </a>
            </div>
            <iframe
              src={previewUrl}
              className="h-[600px] w-full rounded-lg border border-zinc-200"
              title="Website Preview"
              sandbox="allow-scripts"
            />
          </div>
        )}
      </div>
    </div>
  );
}
