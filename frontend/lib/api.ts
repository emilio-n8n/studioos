import { getApiBase } from "./config";

async function request<T>(path: string, options?: RequestInit, timeoutMs = 120000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${getApiBase()}${path}`, {
      signal: controller.signal,
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!res.ok) {
      let err: string;
      try {
        const body = await res.json();
        err = body.detail || JSON.stringify(body);
      } catch {
        err = await res.text();
      }
      throw new Error(err || `HTTP ${res.status}`);
    }
    return res.json();
  } finally {
    clearTimeout(timer);
  }
}

export function listProjects() {
  return request<import("./types").Project[]>("/api/projects");
}

export function getProject(id: number) {
  return request<import("./types").Project>(`/api/projects/${id}`);
}

export function createProject(description: string, openai_api_key: string, provider?: string, model?: string, name?: string, outputPath?: string) {
  return request<import("./types").Project>("/api/projects", {
    method: "POST",
    body: JSON.stringify({ description, openai_api_key, provider, model, name, output_path: outputPath }),
  }, 180000);
}

export function getOrganization(projectId: number) {
  return request<import("./types").Organization>(`/api/projects/${projectId}/organization`);
}

export function getOrgTree(projectId: number) {
  return request<import("./types").OrgTree>(`/api/projects/${projectId}/organization/tree`);
}

export function getDashboard(projectId: number) {
  return request<import("./types").Dashboard>(`/api/projects/${projectId}/tasks/dashboard`);
}

export function listTasks(projectId: number) {
  return request<import("./types").Task[]>(`/api/projects/${projectId}/tasks`);
}

export function transitionTask(projectId: number, taskId: number, status: string) {
  return request<import("./types").Task>(`/api/projects/${projectId}/tasks/${taskId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function generateWebsite(projectId: number) {
  return request<{ output_url: string; files: { path: string }[] }>(
    `/api/projects/${projectId}/generate`,
    { method: "POST" },
    300000
  );
}

export function getDecisions(projectId: number) {
  return request<import("./types").StrategicDecision[]>(`/api/projects/${projectId}/decisions`);
}

export function getMemoryGraph(projectId: number) {
  return request<import("./types").MemoryGraphData>(`/api/projects/${projectId}/memory/graph`);
}

export function getMemorySnapshot(projectId: number, timestamp?: string) {
  const qs = timestamp ? `?timestamp=${encodeURIComponent(timestamp)}` : "";
  return request<Record<string, unknown>>(`/api/projects/${projectId}/memory/snapshot${qs}`);
}

export function getMemoryReplay(projectId: number) {
  return request<Record<string, unknown>[]>(`/api/projects/${projectId}/memory/replay`);
}

export function runPipeline(projectId: number) {
  return request<{ status: string; tasks_completed: number; tasks_total: number }>(
    `/api/projects/${projectId}/pipeline/run`,
    { method: "POST" },
    300000
  );
}

export function getPipelineDag(projectId: number) {
  return request<{ nodes: unknown[]; edges: unknown[] }>(
    `/api/projects/${projectId}/pipeline/dag`
  );
}

// Agent Registry
export function listRegistryAgents(status?: string, provider?: string) {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (provider) params.set("provider", provider);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return request<import("./types").AgentRegistryEntry[]>(`/api/integration/agents${qs}`);
}

export function registerAgent(data: {
  provider: string;
  name: string;
  description?: string;
  capabilities?: string[];
  endpoint_url?: string;
  cost?: number;
  speed?: number;
  quality?: number;
}) {
  return request<{ id: number; provider: string; name: string; status: string }>(
    "/api/integration/agents/register",
    { method: "POST", body: JSON.stringify(data) }
  );
}

export function approveAgent(entryId: number) {
  return request<{ id: number; name: string; status: string }>(
    `/api/integration/agents/${entryId}/approve`,
    { method: "POST" }
  );
}

export function rejectAgent(entryId: number) {
  return request<{ id: number; name: string; status: string }>(
    `/api/integration/agents/${entryId}/reject`,
    { method: "POST" }
  );
}

export function discoverProviders() {
  return request<{ discovered: number; total: number }>(
    "/api/integration/providers/discover",
    { method: "POST" }
  );
}

export function listProviders() {
  return request<{ providers: { name: string; class: string }[] }>(
    "/api/integration/providers"
  );
}

export function searchAgentsByCapability(q: string, minQuality = 1) {
  return request<import("./types").AgentSearchResult[]>(
    `/api/integration/agents/search?q=${encodeURIComponent(q)}&min_quality=${minQuality}`
  );
}

// Chat CEO
export function chatWithCEO(
  projectId: number,
  message: string,
  history: { role: string; content: string }[],
  onEvent: (event: import("./types").ChatStreamEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  return new Promise((resolve, reject) => {
    fetch(`${getApiBase()}/api/projects/${projectId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
      signal,
    }).then(async (res) => {
      if (!res.ok) {
        const err = await res.text();
        reject(new Error(err));
        return;
      }
      const reader = res.body?.getReader();
      if (!reader) { resolve(); return; }
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const event = JSON.parse(line.slice(6));
              onEvent(event);
              if (event.type === "done") { resolve(); return; }
            } catch { /* skip malformed */ }
          }
        }
      }
      resolve();
    }).catch(reject);
  });
}

// Agent API
export function listAgents(projectId: number) {
  return request<{ agents: import("./types").Agent[] }>(
    `/api/projects/${projectId}/agents`
  );
}

export function getAgentDetail(projectId: number, agentId: number) {
  return request<import("./types").AgentDetail>(
    `/api/projects/${projectId}/agents/${agentId}`
  );
}

export function sendAgentMessage(projectId: number, agentId: number, message: string) {
  return request<{ status: string; agent_name: string }>(
    `/api/projects/${projectId}/agents/${agentId}/message`,
    { method: "POST", body: JSON.stringify({ message, sender: "CEO" }) }
  );
}
