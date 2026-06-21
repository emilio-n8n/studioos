"use client";

function detectApiBase(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== "undefined") {
    const m = window.location.hostname.match(
      /^(.+?)-3000\.preview\.app\.github\.dev$/
    );
    if (m) {
      return `https://${m[1]}-8000.preview.app.github.dev`;
    }
  }
  return "http://localhost:8000";
}

function detectWsBase(apiBase: string): string {
  if (apiBase.startsWith("https://")) return apiBase.replace(/^https/, "wss");
  return apiBase.replace(/^http/, "ws");
}

export const API_BASE = detectApiBase();
export const WS_BASE = detectWsBase(API_BASE);
