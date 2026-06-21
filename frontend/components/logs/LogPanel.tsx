"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { WS_BASE } from "@/lib/config";

interface LogEntry {
  id: number;
  level: string;
  message: string;
  logger: string;
  timestamp: number;
}

interface Props {
  projectId: number;
}

const LEVEL_COLORS: Record<string, string> = {
  DEBUG: "text-gray-400",
  INFO: "text-blue-600",
  WARNING: "text-amber-600",
  ERROR: "text-red-600",
  CRITICAL: "text-red-700 font-bold",
};



export default function LogPanel({ projectId }: Props) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filter, setFilter] = useState<string>("INFO");
  const [connected, setConnected] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const idRef = useRef(0);

  const addLog = useCallback((entry: LogEntry) => {
    setLogs((prev) => {
      const next = [...prev, entry];
      return next.length > 500 ? next.slice(-500) : next;
    });
  }, []);

  useEffect(() => {
    const url = `${WS_BASE}/ws/projects/${projectId}`;
    const ws = new WebSocket(url);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        if (parsed.type === "log" && parsed.data) {
          idRef.current += 1;
          addLog({
            id: idRef.current,
            level: parsed.data.level || "INFO",
            message: parsed.data.message,
            logger: parsed.data.logger || "",
            timestamp: parsed.data.timestamp || Date.now(),
          });
        }
      } catch {
        // skip non-json
      }
    };

    return () => ws.close();
  }, [projectId, addLog]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const filtered = filter === "ALL"
    ? logs
    : logs.filter((l) => {
        const levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"];
        return levels.indexOf(l.level) >= levels.indexOf(filter);
      });

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-zinc-900">Logs temps réel</h2>
          <span
            className={`h-2 w-2 rounded-full ${connected ? "bg-green-500" : "bg-red-500"}`}
            title={connected ? "Connecté" : "Déconnecté"}
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-400">{filtered.length} entrées</span>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="rounded border border-zinc-300 px-2 py-1 text-xs"
          >
            <option value="DEBUG">Debug +</option>
            <option value="INFO">Info +</option>
            <option value="WARNING">Warning +</option>
            <option value="ERROR">Error +</option>
            <option value="ALL">Tous</option>
          </select>
          <button
            onClick={() => setLogs([])}
            className="rounded border border-zinc-300 px-2 py-1 text-xs hover:bg-zinc-100"
          >
            Effacer
          </button>
        </div>
      </div>

      <div className="h-[400px] overflow-y-auto rounded-lg border border-zinc-200 bg-zinc-950 p-3 font-mono text-xs leading-relaxed">
        {filtered.length === 0 && (
          <p className="text-zinc-500 italic">En attente de logs...</p>
        )}
        {filtered.map((log) => (
          <div key={log.id} className="flex gap-2">
            <span className="shrink-0 text-zinc-500">
              {new Date(log.timestamp * 1000).toLocaleTimeString()}
            </span>
            <span className={`shrink-0 w-16 ${LEVEL_COLORS[log.level] || "text-zinc-400"}`}>
              {log.level}
            </span>
            <span className="text-zinc-400 shrink-0 max-w-[120px] truncate" title={log.logger}>
              {log.logger.split(".").pop()}
            </span>
            <span className="text-zinc-100 break-words">{log.message}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
