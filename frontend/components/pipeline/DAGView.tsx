"use client";

import { useMemo } from "react";
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
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";

function TaskNode({ data }: NodeProps) {
  return (
    <div
      className="rounded-lg border-2 px-3 py-2 text-center shadow-sm"
      style={{ borderColor: data.color || "#94a3b8" }}
    >
      <Handle type="target" position={Position.Top} />
      <div className="text-xs font-semibold text-zinc-900">{data.label}</div>
      <div className="mt-1 flex items-center justify-center gap-2">
        <span
          className="inline-block h-2 w-2 rounded-full"
          style={{ backgroundColor: data.color || "#94a3b8" }}
        />
        <span className="text-[10px] font-medium uppercase text-zinc-500">
          {data.status}
        </span>
      </div>
      {data.agent && (
        <div className="text-[9px] text-zinc-400">{data.agent}</div>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

const nodeTypes = { taskNode: TaskNode };

interface DAGNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    label: string;
    status: string;
    priority: number;
    agent: string | null;
    color: string;
  };
}

interface DAGEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  animated: boolean;
}

interface Props {
  nodes: DAGNode[];
  edges: DAGEdge[];
}

function layoutDag(nodes: DAGNode[], edges: DAGEdge[]): { nodes: Node[]; edges: Edge[] } {
  const deps = new Map<string, string[]>();
  const dependents = new Map<string, string[]>();
  for (const e of edges) {
    if (!deps.has(e.target)) deps.set(e.target, []);
    deps.get(e.target)!.push(e.source);
    if (!dependents.has(e.source)) dependents.set(e.source, []);
    dependents.get(e.source)!.push(e.target);
  }

  const roots = nodes.filter((n) => !deps.has(n.id) || deps.get(n.id)!.length === 0);

  const positions = new Map<string, { x: number; y: number }>();
  const nodeWidth = 180;
  const nodeHeight = 80;
  const hSpacing = 60;
  const vSpacing = 100;

  function assignLayers(
    nodeId: string,
    visited: Set<string>
  ): number {
    if (visited.has(nodeId)) return 0;
    visited.add(nodeId);
    const children = dependents.get(nodeId) || [];
    if (children.length === 0) return 0;
    let maxDepth = 0;
    for (const c of children) {
      maxDepth = Math.max(maxDepth, assignLayers(c, visited) + 1);
    }
    return maxDepth;
  }

  const visited = new Set<string>();
  const nodeLayers = new Map<string, number>();
  for (const r of roots) {
    nodeLayers.set(r.id, 0);
    for (const n of nodes) {
      const depth = assignLayers(n.id, new Set());
      if (!nodeLayers.has(n.id) || depth > nodeLayers.get(n.id)!) {
        nodeLayers.set(n.id, depth);
      }
    }
  }

  const layers = new Map<number, string[]>();
  for (const n of nodes) {
    const l = nodeLayers.get(n.id) || 0;
    if (!layers.has(l)) layers.set(l, []);
    layers.get(l)!.push(n.id);
  }

  for (const [layer, nodeIds] of layers) {
    const totalWidth = nodeIds.length * nodeWidth + (nodeIds.length - 1) * hSpacing;
    let x = -totalWidth / 2 + nodeWidth / 2;
    for (const nid of nodeIds) {
      positions.set(nid, { x, y: layer * (nodeHeight + vSpacing) });
      x += nodeWidth + hSpacing;
    }
  }

  const laidOutNodes: Node[] = nodes.map((n) => ({
    id: n.id,
    type: n.type,
    position: positions.get(n.id) || { x: 0, y: 0 },
    data: n.data,
  }));

  const flowEdges: Edge[] = edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    type: "smoothstep",
    animated: e.animated,
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { stroke: "#94a3b8", strokeWidth: 2 },
  }));

  return { nodes: laidOutNodes, edges: flowEdges };
}

export default function DAGView({ nodes: rawNodes, edges: rawEdges }: Props) {
  const { nodes: laidOutNodes, edges: laidOutEdges } = useMemo(
    () => layoutDag(rawNodes, rawEdges),
    [rawNodes, rawEdges]
  );

  const [nodes, , onNodesChange] = useNodesState(laidOutNodes);
  const [flowEdges, , onEdgesChange] = useEdgesState(laidOutEdges);

  if (nodes.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-zinc-200 bg-white text-sm text-zinc-400">
        Aucune tâche à afficher dans le DAG
      </div>
    );
  }

  return (
    <div className="h-[500px] rounded-xl border border-zinc-200 bg-white shadow-sm">
      <ReactFlow
        nodes={nodes}
        edges={flowEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
      >
        <Controls />
        <MiniMap />
        <Background color="#e5e5e5" gap={16} />
      </ReactFlow>
    </div>
  );
}
