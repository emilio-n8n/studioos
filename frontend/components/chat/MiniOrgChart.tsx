"use client";

import { useEffect, useState, useCallback } from "react";
import { listAgents, getAgentDetail } from "@/lib/api";
import type { Agent, AgentDetail } from "@/lib/types";

interface MiniOrgChartProps {
  projectId: number;
  onAgentSelect: (agent: AgentDetail) => void;
}

export default function MiniOrgChart({ projectId, onAgentSelect }: MiniOrgChartProps) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  const loadAgents = useCallback(async () => {
    try {
      const data = await listAgents(projectId);
      setAgents(data.agents || []);
    } catch (e) {
      console.error("Failed to load agents", e);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadAgents();
    const interval = setInterval(loadAgents, 5000);
    return () => clearInterval(interval);
  }, [loadAgents]);

  const handleClick = async (agent: Agent) => {
    try {
      const detail = await getAgentDetail(projectId, agent.id);
      onAgentSelect(detail);
    } catch (e) {
      console.error("Failed to load agent detail", e);
    }
  };

  const statusDot = (agent: Agent) => {
    if (agent.current_task_id) return { color: "#fbbf24", label: "busy" };
    if (agent.is_active) return { color: "#22c55e", label: "actif" };
    return { color: "#6c7086", label: "inactif" };
  };

  return (
    <div style={{ padding: "12px", height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ fontSize: "13px", fontWeight: 600, color: "#89b4fa", marginBottom: "12px" }}>
        Équipe
      </div>
      {loading ? (
        <div style={{ color: "#6c7086", fontSize: "12px" }}>Chargement...</div>
      ) : agents.length === 0 ? (
        <div style={{ color: "#6c7086", fontSize: "12px" }}>Aucun agent</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "4px", flex: 1, overflowY: "auto" }}>
          {agents.map((agent) => {
            const dot = statusDot(agent);
            return (
              <div
                key={agent.id}
                onClick={() => handleClick(agent)}
                style={{
                  display: "flex", alignItems: "center", gap: "8px",
                  padding: "6px 8px", borderRadius: "6px", cursor: "pointer",
                  fontSize: "12px", transition: "background 0.1s",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "#313244")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
              >
                <span style={{
                  width: 8, height: 8, borderRadius: "50%",
                  background: dot.color, flexShrink: 0,
                }} />
                <span style={{ flex: 1, color: "#cdd6f4", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {agent.name}
                </span>
                {agent.current_task && (
                  <span style={{
                    fontSize: "10px", color: "#6c7086",
                    whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: "80px",
                  }}>
                    {agent.current_task.slice(0, 20)}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
