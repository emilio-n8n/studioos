"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { chatWithCEO } from "@/lib/api";
import type { ChatMessage, ChatStreamEvent } from "@/lib/types";

interface CeoChatProps {
  projectId: number;
  onAgentClick?: (agentId: number) => void;
}

export default function CeoChat({ projectId, onAgentClick }: CeoChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Bonjour, je suis votre CEO. Comment puis-je vous aider ?" },
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [abortController, setAbortController] = useState<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || streaming) return;
    setInput("");

    const updatedMessages = [...messages, { role: "user" as const, content: text }];
    setMessages([...updatedMessages, { role: "assistant", content: "" }]);
    setStreaming(true);

    const controller = new AbortController();
    setAbortController(controller);

    let assistantIdx = updatedMessages.length;

    try {
      await chatWithCEO(projectId, text, updatedMessages.slice(0, -1), (event: ChatStreamEvent) => {
        if (event.type === "token" && event.content) {
          setMessages((prev) => {
            const copy = [...prev];
            const last = { ...copy[copy.length - 1] };
            last.content += event.content!;
            copy[copy.length - 1] = last;
            return copy;
          });
        } else if (event.type === "tool_start") {
          setMessages((prev) => {
            const copy = [...prev];
            const last = { ...copy[copy.length - 1] };
            const toolMsg = `⚙️ Exécution de ${event.tool}...`;
            last.content += `\n${toolMsg}`;
            copy[copy.length - 1] = last;
            return copy;
          });
        } else if (event.type === "tool_result" && event.tool === "get_agent_detail") {
          try {
            const data = JSON.parse(event.result || "{}");
            if (data.id && onAgentClick) {
              onAgentClick(data.id);
            }
          } catch { /* ignore */ }
        }
      }, controller.signal);
    } catch (err: any) {
      if (err.name !== "AbortError") {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `❌ Erreur: ${err.message}` },
        ]);
      }
    } finally {
      setStreaming(false);
      setAbortController(null);
      inputRef.current?.focus();
    }
  }, [input, messages, streaming, projectId, onAgentClick]);

  const handleStop = useCallback(() => {
    abortController?.abort();
    setStreaming(false);
  }, [abortController]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ flex: 1, overflowY: "auto", padding: "16px", display: "flex", flexDirection: "column", gap: "12px" }}>
        {messages.map((msg, i) => (
          <div key={i} style={{
            alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
            maxWidth: "80%",
            background: msg.role === "user" ? "#2563eb" : "#1e293b",
            color: "#fff",
            padding: "10px 14px",
            borderRadius: msg.role === "user" ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
            fontSize: "14px",
            lineHeight: 1.5,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}>
            {msg.content || (i === messages.length - 1 && streaming ? (
              <span style={{ display: "inline-flex", gap: 4 }}>
                <span style={{ animation: "dotPulse 1.4s infinite", animationDelay: "0s" }}>.</span>
                <span style={{ animation: "dotPulse 1.4s infinite", animationDelay: "0.2s" }}>.</span>
                <span style={{ animation: "dotPulse 1.4s infinite", animationDelay: "0.4s" }}>.</span>
              </span>
            ) : null)}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <div style={{
        display: "flex", gap: "8px", padding: "12px 16px",
        borderTop: "1px solid #313244", background: "#181825",
      }}>
        <input
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Parle à ton CEO..."
          disabled={streaming}
          style={{
            flex: 1, padding: "10px 14px", borderRadius: "8px",
            border: "1px solid #313244", background: "#1e1e2e",
            color: "#cdd6f4", fontSize: "14px", outline: "none",
          }}
        />
        {streaming ? (
          <button onClick={handleStop} style={{
            padding: "10px 16px", borderRadius: "8px", border: "none",
            background: "#ef4444", color: "#fff", cursor: "pointer", fontWeight: 600,
          }}>Stop</button>
        ) : (
          <button onClick={handleSend} disabled={!input.trim()} style={{
            padding: "10px 16px", borderRadius: "8px", border: "none",
            background: input.trim() ? "#2563eb" : "#313244",
            color: input.trim() ? "#fff" : "#6c7086",
            cursor: input.trim() ? "pointer" : "default", fontWeight: 600,
          }}>Envoyer</button>
        )}
      </div>
      <style>{`
        @keyframes dotPulse {
          0%, 80%, 100% { opacity: 0; }
          40% { opacity: 1; }
        }
      `}</style>
    </div>
  );
}
