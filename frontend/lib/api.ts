const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit, timeoutMs = 120000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
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

export function createProject(description: string, openai_api_key: string, name?: string) {
  return request<import("./types").Project>("/api/projects", {
    method: "POST",
    body: JSON.stringify({ description, openai_api_key, name }),
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
