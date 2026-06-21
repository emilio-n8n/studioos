export interface Project {
  id: number;
  name: string;
  description: string;
  status: string;
  complexity: string | null;
  analysis: ProjectAnalysis | null;
  created_at: string;
}

export interface ProjectAnalysis {
  name: string;
  summary: string;
  objectives: string[];
  constraints: string[];
  complexity: string;
  complexity_rationale: string;
  risks: Risk[];
  assumptions: string[];
  estimated_duration: string;
  suggested_departments: DepartmentSuggestion[];
}

export interface Risk {
  risk: string;
  severity: "low" | "medium" | "high";
  mitigation: string;
}

export interface DepartmentSuggestion {
  name: string;
  description: string;
  priority: number;
}

export interface Organization {
  id: number;
  project_id: number;
  name: string;
  structure_type: string;
  hierarchy: any[];
  departments: Department[];
}

export interface Department {
  id: number;
  name: string;
  description: string | null;
  roles: Role[];
}

export interface Role {
  id: number;
  title: string;
  summary: string | null;
  responsibilities: string[];
  authority: string[];
  permissions: string[];
  reports_to: string | null;
  required_skills: string[];
  metrics: string[];
  status: string;
}

export interface Agent {
  id: number;
  role_id: number;
  name: string;
  status: string;
}

export interface Task {
  id: number;
  project_id: number;
  department_id: number | null;
  assigned_agent_id: number | null;
  title: string;
  description: string | null;
  priority: number;
  status: string;
  estimated_cost: number;
  depends_on: number[];
  created_at: string;
}

export interface Dashboard {
  project_id: number;
  total_tasks: number;
  tasks_by_status: Record<string, number>;
  total_agents: number;
  total_roles: number;
  total_departments: number;
  complexity: string | null;
  risks: Risk[] | null;
  total_decisions: number;
}

export interface StrategicDecision {
  id: number;
  project_id: number;
  category: string;
  title: string;
  description: string | null;
  impact: string | null;
  extra: Record<string, unknown> | null;
  created_at: string;
}

export interface OrgTree {
  nodes: OrgNode[];
  edges: OrgEdge[];
}

export interface OrgNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    label: string;
    description?: string;
    status?: string;
    type: string;
  };
}

export interface OrgEdge {
  id: string;
  source: string;
  target: string;
}

export interface MemoryNodeData {
  id: number;
  project_id: number;
  agent_id: number | null;
  parent_id: number | null;
  key: string;
  value: Record<string, unknown>;
  type: string;
  tags: string[];
  status: string;
  version: number;
  summary: string | null;
  created_by: string | null;
  approved_by: string | null;
  superseded_by: number | null;
  created_at: string;
}

export interface MemoryEdgeData {
  source: number;
  target: number;
  type: string;
}

export interface MemoryGraphData {
  nodes: MemoryNodeData[];
  edges: MemoryEdgeData[];
}
