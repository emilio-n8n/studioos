"use client";

import { useState, useCallback } from "react";
import type { AgentDetail } from "@/lib/types";
import { getApiBase } from "@/lib/config";

interface AgentCodexPanelProps {
  agent: AgentDetail | null;
  projectId: number;
  onClose: () => void;
}

export default function AgentCodexPanel({ agent, projectId, onClose }: AgentCodexPanelProps) {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<{ sender: string; text: string }[]>([]);
  const [sending, setSending] = useState(false);

  const handleSendMessage = useCallback(async () => {
    if (!message.trim() || !agent || sending) return;
    setSending(true);
    try {
      const res = await fetch(`${getApiBase()}/api/projects/${projectId}/agents/${agent.id}/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, sender: "Moi" }),
      });
      if (res.ok) {
        setChatHistory((prev) => [...prev, { sender: "Moi", text: message }, { sender: agent.name, text: "Message reçu ✅" }]);
        setMessage("");
      }
    } catch (e) {
      console.error("Failed to send message", e);
    } finally {
      setSending(false);
    }
  }, [message, agent, projectId, sending]);

  if (!agent) return null;

  return (
    <div style={{
      position: "fixed", top: 0, right: 0, width: "480px", height: "100vh",
      background: "#1e1e2e", borderLeft: "1px solid #313244",
      display: "flex", flexDirection: "column", zIndex: 100,
      boxShadow: "-4px 0 20px rgba(0,0,0,0.3)",
    }}>
      {/* Header */}
      <div style={{
        display: "flex", alignItems: "center", gap: "10px",
        padding: "14px 16px", borderBottom: "1px solid #313244",
        background: "#181825",
      }}>
        <span style={{
          width: 10, height: 10, borderRadius: "50%",
          background: agent.is_active ? "#22c55e" : "#6c7086",
          flexShrink: 0,
        }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, fontSize: "14px", color: "#cdd6f4" }}>{agent.name}</div>
          <div style={{ fontSize: "11px", color: "#6c7086" }}>
            {agent.role} · {agent.provider}
          </div>
        </div>
        <button onClick={onClose} style={{
          background: "none", border: "none", color: "#6c7086",
          cursor: "pointer", fontSize: "20px", padding: "4px 8px",
        }}>×</button>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: "auto", padding: "12px 16px", display: "flex", flexDirection: "column", gap: "16px" }}>

        {/* Status */}
        <div>
          <div style={{ fontSize: "11px", fontWeight: 600, color: "#89b4fa", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.5px" }}>Statut</div>
          <div style={{ fontSize: "13px", color: "#cdd6f4" }}>
            {agent.current_task ? (
              <>En train de travailler sur : <strong>{agent.current_task}</strong></>
            ) : agent.is_active ? (
              "En attente de tâche"
            ) : (
              "Inactif"
            )}
          </div>
        </div>

        {/* Capabilities */}
        {agent.capabilities && agent.capabilities.length > 0 && (
          <div>
            <div style={{ fontSize: "11px", fontWeight: 600, color: "#89b4fa", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.5px" }}>Capacités</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
              {agent.capabilities.map((cap, i) => (
                <span key={i} style={{
                  fontSize: "11px", padding: "2px 8px", borderRadius: "10px",
                  background: "#313244", color: "#a6e3a1",
                }}>{cap}</span>
              ))}
            </div>
          </div>
        )}

        {/* Recent Files */}
        <div>
          <div style={{ fontSize: "11px", fontWeight: 600, color: "#89b4fa", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.5px" }}>Fichiers modifiés</div>
          {agent.recent_files && agent.recent_files.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              {agent.recent_files.map((f, i) => (
                <div key={i} style={{
                  padding: "8px 10px", borderRadius: "6px", background: "#181825",
                  fontSize: "12px",
                }}>
                  <div style={{ color: "#89dceb", fontFamily: "monospace", marginBottom: "2px" }}>
                    {f.sha}
                  </div>
                  <div style={{ color: "#cdd6f4", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {f.message.slice(0, 100)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ fontSize: "12px", color: "#6c7086" }}>Aucun commit récent</div>
          )}
        </div>

        {/* Direct Chat */}
        <div>
          <div style={{ fontSize: "11px", fontWeight: 600, color: "#89b4fa", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
            Message direct à {agent.name}
          </div>
          <div style={{
            maxHeight: "200px", overflowY: "auto", marginBottom: "8px",
            display: "flex", flexDirection: "column", gap: "6px",
          }}>
            {chatHistory.map((msg, i) => (
              <div key={i} style={{
                alignSelf: msg.sender === "Moi" ? "flex-end" : "flex-start",
                background: msg.sender === "Moi" ? "#2563eb" : "#313244",
                color: "#fff", padding: "6px 10px", borderRadius: "8px",
                fontSize: "12px", maxWidth: "80%",
              }}>
                <div style={{ fontSize: "10px", opacity: 0.7, marginBottom: "2px" }}>{msg.sender}</div>
                {msg.text}
              </div>
            ))}
          </div>
          <div style={{ display: "flex", gap: "6px" }}>
            <input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleSendMessage(); }}
              placeholder="Message direct..."
              style={{
                flex: 1, padding: "8px 10px", borderRadius: "6px",
                border: "1px solid #313244", background: "#11111b",
                color: "#cdd6f4", fontSize: "12px", outline: "none",
              }}
            />
            <button onClick={handleSendMessage} disabled={!message.trim() || sending} style={{
              padding: "8px 12px", borderRadius: "6px", border: "none",
              background: message.trim() && !sending ? "#2563eb" : "#313244",
              color: message.trim() && !sending ? "#fff" : "#6c7086",
              cursor: message.trim() && !sending ? "pointer" : "default",
              fontSize: "12px", fontWeight: 600,
            }}>Envoyer</button>
          </div>
        </div>
      </div>
    </div>
  );
}
