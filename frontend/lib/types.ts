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
  responsibilities: string[];
  authority: string[];
  reports_to: string | null;
  required_skills: string[];
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
