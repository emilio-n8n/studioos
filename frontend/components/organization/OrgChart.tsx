"use client";

import { useCallback, useMemo, useState } from "react";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeProps,
  Handle,
  Position,
} from "reactflow";
import "reactflow/dist/style.css";
import RoleCard from "./RoleCard";

const NODE_STYLES: Record<string, string> = {
  department: "border-blue-400 bg-blue-50 text-blue-900",
  role: "border-amber-400 bg-amber-50 text-amber-900",
  agent: "border-green-400 bg-green-50 text-green-900",
};

function CustomNode({ data }: NodeProps) {
  const style = NODE_STYLES[data.type] || NODE_STYLES.agent;
  return (
    <div className={`rounded-lg border-2 px-3 py-2 text-center shadow-sm ${style}`}>
      <Handle type="target" position={Position.Top} />
      <div className="text-xs font-semibold">{data.label}</div>
      {data.status && (
        <div className="text-[10px] opacity-70">{data.status}</div>
      )}
      {data.summary && (
        <div className="mt-0.5 text-[9px] text-zinc-500 line-clamp-1">{data.summary}</div>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

const nodeTypes = {
  department: CustomNode,
  role: CustomNode,
  agent: CustomNode,
};

interface Role {
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

interface Props {
  nodes: Node[];
  edges: Edge[];
  roles?: Role[];
}

function layoutTree(nodes: Node[], edges: Edge[]): { nodes: Node[]; edges: Edge[] } {
  const childrenMap = new Map<string, string[]>();
  const parentMap = new Map<string, string | null>();
  const roots: string[] = [];

  for (const edge of edges) {
    if (!childrenMap.has(edge.source)) childrenMap.set(edge.source, []);
    childrenMap.get(edge.source)!.push(edge.target);
    parentMap.set(edge.target, edge.source);
  }

  for (const node of nodes) {
    if (!parentMap.has(node.id)) {
      roots.push(node.id);
    }
  }

  const positions = new Map<string, { x: number; y: number }>();
  const nodeWidth = 200;
  const nodeHeight = 90;
  const horizontalSpacing = 40;
  const verticalSpacing = 80;

  function layoutSubtree(nodeId: string, depth: number, startX: number): number {
    const children = childrenMap.get(nodeId) || [];
    if (children.length === 0) {
      positions.set(nodeId, { x: startX, y: depth * (nodeHeight + verticalSpacing) });
      return startX + nodeWidth + horizontalSpacing;
    }

    let currentX = startX;
    for (const child of children) {
      currentX = layoutSubtree(child, depth + 1, currentX);
    }

    const childPositions = children.map((c) => positions.get(c)!);
    const minX = Math.min(...childPositions.map((p) => p.x));
    const maxX = Math.max(...childPositions.map((p) => p.x + nodeWidth));
    const centerX = (minX + maxX) / 2 - nodeWidth / 2;

    positions.set(nodeId, { x: centerX, y: depth * (nodeHeight + verticalSpacing) });
    return Math.max(currentX, maxX + horizontalSpacing);
  }

  let globalStartX = 0;
  for (const root of roots) {
    globalStartX = layoutSubtree(root, 0, globalStartX);
  }

  const laidOutNodes = nodes.map((n) => {
    const pos = positions.get(n.id) || { x: 0, y: 0 };
    return { ...n, position: pos };
  });

  return { nodes: laidOutNodes, edges };
}

export default function OrgChart({ nodes: rawNodes, edges: rawEdges, roles = [] }: Props) {
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const { nodes: laidOutNodes, edges: laidOutEdges } = useMemo(
    () => layoutTree(rawNodes, rawEdges),
    [rawNodes, rawEdges]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(laidOutNodes);
  const [flowEdges, setEdges, onEdgesChange] = useEdgesState(laidOutEdges);

  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    if (node.type === "role") {
      const role = roles.find((r) => r.title === node.data.label);
      if (role) setSelectedRole(role);
    }
  }, [roles]);

  const onLayout = useCallback(() => {
    const { nodes: relaid, edges: relied } = layoutTree(nodes, flowEdges);
    setNodes(relaid);
    setEdges(relied);
  }, [nodes, flowEdges, setNodes, setEdges]);

  if (nodes.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-zinc-200 bg-white text-sm text-zinc-400">
        Aucune organisation à afficher
      </div>
    );
  }

  return (
    <>
      <div className="h-[500px] rounded-xl border border-zinc-200 bg-white shadow-sm">
        <ReactFlow
          nodes={nodes}
          edges={flowEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          onNodeClick={onNodeClick}
          fitView
          attributionPosition="bottom-left"
        >
          <Controls />
          <MiniMap />
          <Background color="#e5e5e5" gap={16} />
        </ReactFlow>
      </div>
      {selectedRole && (
        <RoleCard role={selectedRole} onClose={() => setSelectedRole(null)} />
      )}
    </>
  );
}
