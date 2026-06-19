"use client";

import { useState } from "react";

interface Props {
  onSubmit: (description: string, apiKey: string) => Promise<void>;
  loading: boolean;
}

export default function ProjectForm({ onSubmit, loading }: Props) {
  const [description, setDescription] = useState("");
  const [apiKey, setApiKey] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim() || !apiKey.trim()) return;
    await onSubmit(description.trim(), apiKey.trim());
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
            placeholder='Ex: "Créer un RPG tactique en 2D avec Godot proposant un système de combat au tour par tour et une arbre de compétences."'
            rows={5}
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-zinc-700">
            Clé API OpenAI
          </label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="sk-..."
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
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
