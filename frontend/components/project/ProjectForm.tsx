"use client";

import { useState } from "react";

interface Props {
  onSubmit: (description: string, apiKey: string, provider: string, model?: string, outputPath?: string) => Promise<void>;
  loading: boolean;
}

const PROVIDERS = [
  { id: "openai", label: "OpenAI" },
  { id: "opencode-go", label: "OpenCode Go" },
];

const OPENCODE_GO_MODELS = [
  { id: "deepseek-v4-flash", label: "DeepSeek V4 Flash" },
  { id: "deepseek-v4-pro", label: "DeepSeek V4 Pro" },
  { id: "glm-5.2", label: "GLM-5.2" },
  { id: "glm-5.1", label: "GLM-5.1" },
  { id: "kimi-k2.7-code", label: "Kimi K2.7 Code" },
  { id: "kimi-k2.6", label: "Kimi K2.6" },
  { id: "mimo-v2.5", label: "MiMo-V2.5" },
  { id: "mimo-v2.5-pro", label: "MiMo-V2.5-Pro" },
];

export default function ProjectForm({ onSubmit, loading }: Props) {
  const [description, setDescription] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("");
  const [outputPath, setOutputPath] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim() || !apiKey.trim()) return;
    await onSubmit(description.trim(), apiKey.trim(), provider, model || undefined, outputPath || undefined);
  };

  return (
    <form onSubmit={handleSubmit} className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
      <h2 className="mb-1 text-lg font-semibold text-zinc-900">Nouveau projet</h2>
      <p className="mb-4 text-sm text-zinc-500">
        Décrivez le projet à réaliser. StudioOS va analyser la demande et concevoir une organisation adaptée.
      </p>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-zinc-700">
            Description du projet
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder='Ex: "Créer un site SaaS pour TaskFlow avec hero, features, pricing et contact."'
            rows={5}
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-zinc-700">
            Fournisseur IA
          </label>
          <select
            value={provider}
            onChange={(e) => {
              setProvider(e.target.value);
              if (e.target.value !== "opencode-go") setModel("");
            }}
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            {PROVIDERS.map((p) => (
              <option key={p.id} value={p.id}>{p.label}</option>
            ))}
          </select>
        </div>

        {provider === "opencode-go" && (
          <div>
            <label className="block text-sm font-medium text-zinc-700">
              Modèle OpenCode Go
            </label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value="">DeepSeek V4 Flash (défaut)</option>
              {OPENCODE_GO_MODELS.map((m) => (
                <option key={m.id} value={m.id}>{m.label}</option>
              ))}
            </select>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-zinc-700">
            Clé API
          </label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={provider === "opencode-go" ? "go-..." : "sk-..."}
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
          <p className="mt-1 text-xs text-zinc-400">
            {provider === "opencode-go"
              ? "Votre clé OpenCode Go (depuis OpenCode Zen)"
              : "Utilisez 'demo' pour un essai sans clé"
            }
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-zinc-700">
            Dossier de sortie (optionnel)
          </label>
          <input
            type="text"
            value={outputPath}
            onChange={(e) => setOutputPath(e.target.value)}
            placeholder="/Users/moi/studioos-output"
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
          <p className="mt-1 text-xs text-zinc-400">Chemin absolu sur votre machine. Laissez vide pour utiliser le dossier par défaut.</p>
        </div>

        <button
          type="submit"
          disabled={loading || !description.trim() || !apiKey.trim()}
          className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Analyse en cours..." : "Lancer l'analyse"}
        </button>
      </div>
    </form>
  );
}
