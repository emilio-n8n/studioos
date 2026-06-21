export function getApiBase(): string {
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

export function getWsBase(): string {
  const api = getApiBase();
  if (api.startsWith("https://")) return api.replace(/^https/, "wss");
  return api.replace(/^http/, "ws");
}
