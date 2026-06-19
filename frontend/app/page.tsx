"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import ProjectForm from "@/components/project/ProjectForm";
import { listProjects, createProject } from "@/lib/api";
import type { Project } from "@/lib/types";

export default function Home() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadProjects = useCallback(async () => {
    try {
      const data = await listProjects();
      setProjects(data);
    } catch {
      // server might not be running
    }
  }, []);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const handleSubmit = async (description: string, apiKey: string, provider?: string, model?: string) => {
    setLoading(true);
    setError(null);
    try {
      const project = await createProject(description, apiKey, provider, model);
      router.push(`/projects/${project.id}`);
    } catch (err: any) {
      setError(err.message || "Erreur lors de l'analyse");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-1 flex-col">
      <header className="border-b border-zinc-200 bg-white px-6 py-4">
        <h1 className="text-xl font-bold text-zinc-900">StudioOS</h1>
        <p className="text-sm text-zinc-500">Operating System for Autonomous Organizations</p>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-4 py-8">
        <ProjectForm onSubmit={handleSubmit} loading={loading} />

        {error && (
          <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        <section>
          <h2 className="mb-4 text-lg font-semibold text-zinc-900">Projets existants</h2>
          {projects.length === 0 ? (
            <p className="text-sm text-zinc-400">Aucun projet pour le moment.</p>
          ) : (
            <div className="space-y-3">
              {projects.map((p) => (
                <button
                  key={p.id}
                  onClick={() => router.push(`/projects/${p.id}`)}
                  className="w-full rounded-xl border border-zinc-200 bg-white p-4 text-left shadow-sm transition-colors hover:border-blue-300"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-zinc-900">{p.name}</span>
                    <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600">
                      {p.status}
                    </span>
                  </div>
                  <div className="mt-1 text-xs text-zinc-400">
                    Complexité: {p.complexity || "N/A"} | Créé le {new Date(p.created_at).toLocaleDateString()}
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
