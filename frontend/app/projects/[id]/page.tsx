"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import CeoChat from "@/components/chat/CeoChat";
import MiniOrgChart from "@/components/chat/MiniOrgChart";
import AgentCodexPanel from "@/components/chat/AgentCodexPanel";
import CEODashboard from "@/components/dashboard/CEODashboard";
import AlertCenter from "@/components/dashboard/AlertCenter";
import OrgChart from "@/components/organization/OrgChart";
import TaskBoard from "@/components/project/TaskBoard";
import AnalysisReport from "@/components/project/AnalysisReport";
import GenerationPanel from "@/components/generation/GenerationPanel";
import LogPanel from "@/components/logs/LogPanel";
import MemoryGraph from "@/components/memory/MemoryGraph";
import ReviewPanel from "@/components/review/ReviewPanel";
import GitPanel from "@/components/git/GitPanel";
import DAGView from "@/components/pipeline/DAGView";
import AgentRegistryPanel from "@/components/integration/AgentRegistryPanel";
import {
  getProject,
  getOrgTree,
  getOrganization,
  getDashboard,
  listTasks,
  generateWebsite,
  getDecisions,
  runPipeline,
  getPipelineDag,
} from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";
import type { Project, Dashboard, OrgTree, Task, StrategicDecision, Organization, AgentDetail } from "@/lib/types";

type Tab = "dashboard" | "organization" | "tasks" | "analysis" | "memory" | "reviews" | "git" | "pipeline" | "agents" | "generation" | "logs";

const LEGACY_LABELS: Record<Tab, string> = {
  dashboard: "CEO Dashboard",
  organization: "Organigramme",
  tasks: "Tâches",
  analysis: "Rapport Stratégique",
  memory: "Mémoire",
  reviews: "Reviews",
  git: "Git",
  pipeline: "Pipeline",
  agents: "Agents",
  generation: "Génération",
  logs: "Logs",
};

export default function ProjectPage() {
  const params = useParams();
  const rawId = params.id;
  const projectId = Array.isArray(rawId) ? parseInt(rawId[0], 10) : parseInt(rawId ?? "", 10);

  const [project, setProject] = useState<Project | null>(null);
  const [orgTree, setOrgTree] = useState<OrgTree | null>(null);
  const [org, setOrg] = useState<Organization | null>(null);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [decisions, setDecisions] = useState<StrategicDecision[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [generatedUrl, setGeneratedUrl] = useState<string | null>(null);
  const [genError, setGenError] = useState<string | null>(null);
  const [runningPipeline, setRunningPipeline] = useState(false);
  const [pipelineStatus, setPipelineStatus] = useState<string | null>(null);
  const [dagData, setDagData] = useState<{ nodes: unknown[]; edges: unknown[] } | null>(null);
  const [showMenu, setShowMenu] = useState(false);
  const [legacyTab, setLegacyTab] = useState<Tab | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<AgentDetail | null>(null);

  const loadData = useCallback(async () => {
    if (isNaN(projectId)) return;
    setError(null);
    try {
      const [proj, dt, ot, tk, og, dec, dag] = await Promise.all([
        getProject(projectId),
        getDashboard(projectId),
        getOrgTree(projectId),
        listTasks(projectId),
        getOrganization(projectId),
        getDecisions(projectId),
        getPipelineDag(projectId).catch(() => null),
      ]);
      setProject(proj);
      setDashboard(dt);
      setOrgTree(ot);
      setTasks(tk);
      setOrg(og);
      setDecisions(dec);
      if (dag) setDagData(dag);
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

  const handleWsEvent = useCallback((event: { type: string; data?: unknown }) => {
    const refreshTypes = [
      "TASK_STARTED", "TASK_COMPLETED",
      "REVIEW_REQUESTED", "REVIEW_APPROVED", "REVIEW_CHANGES_REQUESTED",
      "GIT_COMMIT_CREATED", "PR_CREATED", "PR_MERGED",
      "MEMORY_CREATED", "PIPELINE_COMPLETED",
    ];
    if (refreshTypes.includes(event.type)) {
      loadData();
    }
  }, [loadData]);

  useWebSocket(projectId, handleWsEvent);

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

  const handleRunPipeline = async () => {
    if (isNaN(projectId)) return;
    setRunningPipeline(true);
    setPipelineStatus(null);
    try {
      const result = await runPipeline(projectId);
      setPipelineStatus(`Terminé : ${result.tasks_completed}/${result.tasks_total} tâches`);
      loadData();
    } catch (err: unknown) {
      setPipelineStatus(err instanceof Error ? err.message : "Pipeline failed");
    } finally {
      setRunningPipeline(false);
    }
  };

  const allRoles = org?.departments?.flatMap((d) => d.roles) ?? [];

  const handleAgentSelect = (agent: AgentDetail) => {
    setSelectedAgent(agent);
  };

  const handleAgentClickFromChat = (agentId: number) => {
    import("@/lib/api").then((api) => {
      api.getAgentDetail(projectId, agentId).then(setSelectedAgent).catch(() => {});
    });
  };

  const tabs: Tab[] = ["dashboard", "organization", "tasks", "analysis", "memory", "reviews", "git", "pipeline", "agents", "generation", "logs"];

  if (isNaN(projectId)) {
    return (
      <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#1e1e2e", color: "#cdd6f4" }}>
        <div style={{ height: 40, display: "flex", alignItems: "center", padding: "0 14px", background: "#181825", borderBottom: "1px solid #313244" }}>
          <span style={{ fontWeight: 600 }}>StudioOS</span>
        </div>
        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#6c7086" }}>
          ID de projet invalide
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#1e1e2e", color: "#cdd6f4" }}>
      {/* Header */}
      <div style={{
        height: 40, display: "flex", alignItems: "center", gap: "8px",
        padding: "0 12px", background: "#181825", borderBottom: "1px solid #313244",
        flexShrink: 0,
      }}>
        <button onClick={() => { setShowMenu(!showMenu); setLegacyTab(null); }}
          style={{ background: "none", border: "none", color: "#6c7086", cursor: "pointer", fontSize: "18px", padding: "4px" }}>
          ☰
        </button>
        <span style={{ fontWeight: 600, fontSize: "13px", color: "#89b4fa" }}>
          {project?.name || "StudioOS"}
        </span>
        {pipelineStatus && (
          <span style={{ fontSize: "11px", color: "#a6e3a1", marginLeft: "8px" }}>
            {pipelineStatus}
          </span>
        )}
        {runningPipeline && (
          <span style={{ fontSize: "11px", color: "#fbbf24", marginLeft: "8px" }}>
            Pipeline en cours...
          </span>
        )}
      </div>

      {/* Main layout */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Legacy Sidebar Menu */}
        {showMenu && (
          <div style={{
            width: 220, background: "#181825", borderRight: "1px solid #313244",
            display: "flex", flexDirection: "column", flexShrink: 0,
          }}>
            <div style={{ padding: "12px 14px", fontSize: "11px", fontWeight: 600, color: "#6c7086", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              Vues détaillées
            </div>
            {tabs.map((tab) => (
              <button key={tab}
                onClick={() => { setLegacyTab(legacyTab === tab ? null : tab); setShowMenu(false); }}
                style={{
                  textAlign: "left", padding: "8px 14px", fontSize: "13px",
                  background: legacyTab === tab ? "#313244" : "transparent",
                  border: "none", color: legacyTab === tab ? "#89b4fa" : "#cdd6f4",
                  cursor: "pointer",
                }}>
                {LEGACY_LABELS[tab]}
              </button>
            ))}
            <div style={{ marginTop: "auto", padding: "12px 14px" }}>
              <button onClick={handleRunPipeline} disabled={runningPipeline} style={{
                width: "100%", padding: "8px", borderRadius: "6px",
                border: "none", background: runningPipeline ? "#313244" : "#2563eb",
                color: runningPipeline ? "#6c7086" : "#fff",
                cursor: runningPipeline ? "default" : "pointer",
                fontSize: "12px", fontWeight: 600,
              }}>
                {runningPipeline ? "Pipeline..." : "▶ Lancer le pipeline"}
              </button>
            </div>
          </div>
        )}

        {/* Main: Chat or Legacy View */}
        <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
          {legacyTab ? (
            <div style={{ flex: 1, overflowY: "auto", padding: "24px" }}>
              <div style={{ marginBottom: "16px" }}>
                <button onClick={() => { setLegacyTab(null); setShowMenu(true); }}
                  style={{ background: "none", border: "none", color: "#89b4fa", cursor: "pointer", fontSize: "13px" }}>
                  ← Retour au chat
                </button>
              </div>
              {legacyTab === "dashboard" && dashboard && (
                <>
                  <CEODashboard dashboard={dashboard} decisions={decisions} />
                  <AlertCenter tasks={tasks} />
                </>
              )}
              {legacyTab === "organization" && orgTree && (
                <OrgChart nodes={orgTree.nodes} edges={orgTree.edges} roles={allRoles} />
              )}
              {legacyTab === "tasks" && (
                <TaskBoard tasks={tasks} projectId={projectId} onRefresh={loadData} />
              )}
              {legacyTab === "analysis" && project?.analysis && (
                <AnalysisReport analysis={project.analysis} />
              )}
              {legacyTab === "memory" && (
                <MemoryGraph projectId={projectId} />
              )}
              {legacyTab === "reviews" && (
                <ReviewPanel projectId={projectId} />
              )}
              {legacyTab === "git" && (
                <GitPanel projectId={projectId} />
              )}
              {legacyTab === "pipeline" && (
                <div>
                  <h2 style={{ fontSize: "16px", fontWeight: 600, marginBottom: "12px", color: "#cdd6f4" }}>DAG d'exécution</h2>
                  {dagData ? (
                    <DAGView nodes={dagData.nodes as any} edges={dagData.edges as any} />
                  ) : (
                    <div style={{ color: "#6c7086", fontSize: "13px" }}>Aucune tâche</div>
                  )}
                  <div style={{ marginTop: "12px" }}>
                    <button onClick={handleRunPipeline} disabled={runningPipeline} style={{
                      padding: "8px 16px", borderRadius: "6px", border: "none",
                      background: runningPipeline ? "#313244" : "#2563eb",
                      color: runningPipeline ? "#6c7086" : "#fff",
                      cursor: runningPipeline ? "default" : "pointer", fontSize: "13px", fontWeight: 600,
                    }}>
                      {runningPipeline ? "Exécution..." : "Lancer le pipeline"}
                    </button>
                    {pipelineStatus && <span style={{ marginLeft: "12px", fontSize: "12px", color: "#a6e3a1" }}>{pipelineStatus}</span>}
                  </div>
                </div>
              )}
              {legacyTab === "agents" && <AgentRegistryPanel />}
              {legacyTab === "generation" && (
                <GenerationPanel generating={generating} generatedUrl={generatedUrl} genError={genError} onGenerate={handleGenerate} />
              )}
              {legacyTab === "logs" && <LogPanel projectId={projectId} />}
            </div>
          ) : (
            /* Chat view */
            <CeoChat projectId={projectId} onAgentClick={handleAgentClickFromChat} />
          )}
        </div>

        {/* Right sidebar: Mini Org Chart */}
        {!legacyTab && (
          <div style={{
            width: 220, borderLeft: "1px solid #313244",
            background: "#181825", flexShrink: 0,
            display: "flex", flexDirection: "column",
          }}>
            <MiniOrgChart projectId={projectId} onAgentSelect={handleAgentSelect} />
            <div style={{ padding: "8px 12px", borderTop: "1px solid #313244" }}>
              <button onClick={handleRunPipeline} disabled={runningPipeline} style={{
                width: "100%", padding: "6px", borderRadius: "6px",
                border: "none", background: runningPipeline ? "#313244" : "#2563eb",
                color: runningPipeline ? "#6c7086" : "#fff",
                cursor: runningPipeline ? "default" : "pointer",
                fontSize: "11px", fontWeight: 600,
              }}>
                {runningPipeline ? "Pipeline..." : "▶ Lancer le pipeline"}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Agent CodeXplorer Panel */}
      {selectedAgent && (
        <AgentCodexPanel
          agent={selectedAgent}
          projectId={projectId}
          onClose={() => setSelectedAgent(null)}
        />
      )}
    </div>
  );
}
