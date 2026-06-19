"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Header from "@/components/layout/Header";
import CEODashboard from "@/components/dashboard/CEODashboard";
import ProductionFlow from "@/components/dashboard/ProductionFlow";
import AlertCenter from "@/components/dashboard/AlertCenter";
import OrgChart from "@/components/organization/OrgChart";
import TaskBoard from "@/components/project/TaskBoard";
import AnalysisReport from "@/components/project/AnalysisReport";
import GenerationPanel from "@/components/generation/GenerationPanel";
import LogPanel from "@/components/logs/LogPanel";
import {
  getProject,
  getOrgTree,
  getDashboard,
  listTasks,
  generateWebsite,
} from "@/lib/api";
import type { Project, Dashboard, OrgTree, Task } from "@/lib/types";

type Tab = "dashboard" | "organization" | "tasks" | "analysis" | "alerts" | "generation" | "logs";

export default function ProjectPage() {
  const params = useParams();
  const rawId = params.id;
  const projectId = Array.isArray(rawId) ? parseInt(rawId[0], 10) : parseInt(rawId ?? "", 10);

  const [project, setProject] = useState<Project | null>(null);
  const [orgTree, setOrgTree] = useState<OrgTree | null>(null);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [generatedUrl, setGeneratedUrl] = useState<string | null>(null);
  const [genError, setGenError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (isNaN(projectId)) return;
    setError(null);
    try {
      const [proj, dt, ot, tk] = await Promise.all([
        getProject(projectId),
        getDashboard(projectId),
        getOrgTree(projectId),
        listTasks(projectId),
      ]);
      setProject(proj);
      setDashboard(dt);
      setOrgTree(ot);
      setTasks(tk);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Failed to load project");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleGenerate = async () => {
    if (isNaN(projectId)) return;
    setGenerating(true);
    setGenError(null);
    setGeneratedUrl(null);
    try {
      const result = await generateWebsite(projectId);
      setGeneratedUrl(result.output_url);
    } catch (err: unknown) {
      setGenError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: "dashboard", label: "CEO Dashboard" },
    { key: "organization", label: "Organigramme" },
    { key: "tasks", label: "Tâches" },
    { key: "analysis", label: "Rapport Stratégique" },
    { key: "generation", label: "Génération" },
    { key: "alerts", label: "Alertes" },
    { key: "logs", label: "Logs" },
  ];

  if (isNaN(projectId)) {
    return (
      <div className="flex flex-1 flex-col">
        <Header title="Projet invalide" />
        <div className="flex flex-1 items-center justify-center">
          <p className="text-zinc-400">ID de projet invalide</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex flex-1 flex-col">
        <Header title="Chargement..." />
        <div className="flex flex-1 items-center justify-center">
          <p className="text-zinc-400">Analyse du projet en cours...</p>
        </div>
      </div>
    );
  }

  if (!project || !dashboard) {
    return (
      <div className="flex flex-1 flex-col">
        <Header title="Erreur" />
        <div className="flex flex-1 flex-col items-center justify-center gap-4">
          <p className="text-zinc-400">{error || "Projet introuvable"}</p>
          <button onClick={loadData} className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col">
      <Header title={project.name} />

      <nav className="flex gap-1 border-b border-zinc-200 bg-white px-6" role="tablist" aria-label="Project tabs">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            role="tab"
            aria-selected={activeTab === tab.key}
            aria-controls={`panel-${tab.key}`}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-zinc-500 hover:text-zinc-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="flex-1 overflow-y-auto px-6 py-6">
        {activeTab === "dashboard" && <CEODashboard dashboard={dashboard} />}

        {activeTab === "organization" && <OrgChart nodes={orgTree?.nodes ?? []} edges={orgTree?.edges ?? []} />}
        {activeTab === "organization" && !orgTree && (
          <p className="text-sm text-zinc-400">Organisation non disponible</p>
        )}

        {activeTab === "tasks" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-zinc-900">Tâches ({tasks.length})</h2>
              <button
                onClick={loadData}
                className="rounded-lg bg-zinc-100 px-3 py-1.5 text-sm text-zinc-600 hover:bg-zinc-200"
              >
                Actualiser
              </button>
            </div>
            <TaskBoard tasks={tasks} projectId={projectId} onRefresh={loadData} />
            <ProductionFlow tasksByStatus={dashboard.tasks_by_status} />
          </div>
        )}

        {activeTab === "analysis" && project.analysis && (
          <AnalysisReport analysis={project.analysis} />
        )}
        {activeTab === "analysis" && !project.analysis && (
          <p className="text-sm text-zinc-400">Analyse non disponible</p>
        )}

        {activeTab === "generation" && (
          <GenerationPanel
            generating={generating}
            generatedUrl={generatedUrl}
            genError={genError}
            onGenerate={handleGenerate}
          />
        )}

        {activeTab === "logs" && (
          <LogPanel projectId={projectId} />
        )}

        {activeTab === "alerts" && (
          <AlertCenter
            alerts={(project.analysis?.risks || []).map((r) => {
              const type = r.severity === "high" ? "risk" : "delay" as const;
              return {
                type,
                message: r.risk + (r.mitigation ? ` — ${r.mitigation}` : ""),
              };
            })}
          />
        )}
      </main>
    </div>
  );
}
