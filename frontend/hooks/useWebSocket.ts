"use client";
import { useEffect, useRef, useCallback } from "react";

const WS_BASE =
  process.env.NEXT_PUBLIC_WS_URL ||
  (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/^http/, "ws");

export function useWebSocket(
  projectId: number | null,
  onMessage: (data: any) => void
) {
  const wsRef = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  const connect = useCallback(() => {
    if (!projectId) return;
    const url = `${WS_BASE}/ws/projects/${projectId}`;
    const ws = new WebSocket(url);
    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        onMessageRef.current(parsed);
      } catch {
        // ignore non-json messages
      }
    };
    ws.onclose = () => {
      setTimeout(connect, 3000);
    };
    wsRef.current = ws;
  }, [projectId]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);
}
