"use client";

import { useState, useEffect, useCallback } from "react";
import {
  listRegistryAgents,
  approveAgent,
  rejectAgent,
  discoverProviders,
  registerAgent,
} from "@/lib/api";
import type { AgentRegistryEntry } from "@/lib/types";

const STATUS_COLORS: Record<string, string> = {
  discovered: "text-yellow-600 bg-yellow-50 border-yellow-200",
  pending: "text-blue-600 bg-blue-50 border-blue-200",
  approved: "text-green-600 bg-green-50 border-green-200",
  rejected: "text-red-600 bg-red-50 border-red-200",
};

const PROVIDER_BADGES: Record<string, string> = {
  native: "bg-zinc-100 text-zinc-700",
  mock: "bg-purple-100 text-purple-700",
  acp: "bg-blue-100 text-blue-700",
};

export default function AgentRegistryPanel() {
  const [agents, setAgents] = useState<AgentRegistryEntry[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [showRegister, setShowRegister] = useState(false);
  const [form, setForm] = useState({
    provider: "custom",
    name: "",
    description: "",
    capabilities: "",
    endpoint_url: "",
    cost: 5,
    speed: 5,
    quality: 5,
  });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const status = filter === "all" ? undefined : filter;
      const data = await listRegistryAgents(status);
      setAgents(data);
    } catch (err) {
      console.error("Failed to load agents", err);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    load();
  }, [load]);

  const handleDiscover = async () => {
    await discoverProviders();
    load();
  };

  const handleApprove = async (id: number) => {
    await approveAgent(id);
    load();
  };

  const handleReject = async (id: number) => {
    await rejectAgent(id);
    load();
  };

  const handleRegister = async () => {
    try {
      await registerAgent({
        provider: form.provider,
        name: form.name,
        description: form.description,
        capabilities: form.capabilities.split(",").map((c) => c.trim()).filter(Boolean),
        endpoint_url: form.endpoint_url || undefined,
        cost: form.cost,
        speed: form.speed,
        quality: form.quality,
      });
      setShowRegister(false);
      setForm({ provider: "custom", name: "", description: "", capabilities: "", endpoint_url: "", cost: 5, speed: 5, quality: 5 });
      load();
    } catch (err) {
      console.error("Registration failed", err);
    }
  };

  const filtered = filter === "all" ? agents : agents.filter((a) => a.status === filter);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-zinc-900">
          Registre des agents ({agents.length})
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDiscover}
            className="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700"
          >
            Découvrir
          </button>
          <button
            onClick={() => setShowRegister(!showRegister)}
            className="rounded-lg bg-zinc-100 px-3 py-1.5 text-xs font-medium text-zinc-600 hover:bg-zinc-200"
          >
            {showRegister ? "Annuler" : "Inscrire"}
          </button>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="rounded border border-zinc-300 px-2 py-1 text-xs"
          >
            <option value="all">Tous</option>
            <option value="discovered">Découverts</option>
            <option value="pending">En attente</option>
            <option value="approved">Approuvés</option>
            <option value="rejected">Rejetés</option>
          </select>
        </div>
      </div>

      {/* Register form */}
      {showRegister && (
        <div className="rounded-lg border border-zinc-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-semibold text-zinc-900">Nouvel agent</h3>
          <div className="grid grid-cols-2 gap-3">
            <input
              placeholder="Nom"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="rounded border border-zinc-300 px-2 py-1 text-sm"
            />
            <input
              placeholder="Provider (custom, acp...)"
              value={form.provider}
              onChange={(e) => setForm({ ...form, provider: e.target.value })}
              className="rounded border border-zinc-300 px-2 py-1 text-sm"
            />
            <input
              placeholder="Description"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="col-span-2 rounded border border-zinc-300 px-2 py-1 text-sm"
            />
            <input
              placeholder="Capacités (séparées par des virgules)"
              value={form.capabilities}
              onChange={(e) => setForm({ ...form, capabilities: e.target.value })}
              className="col-span-2 rounded border border-zinc-300 px-2 py-1 text-sm"
            />
            <input
              placeholder="Endpoint URL"
              value={form.endpoint_url}
              onChange={(e) => setForm({ ...form, endpoint_url: e.target.value })}
              className="col-span-2 rounded border border-zinc-300 px-2 py-1 text-sm"
            />
            <div className="flex items-center gap-2 text-xs text-zinc-500">
              <span>Coût:</span>
              <input
                type="range" min={1} max={10}
                value={form.cost}
                onChange={(e) => setForm({ ...form, cost: +e.target.value })}
                className="w-20"
              />
              <span>{form.cost}</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-zinc-500">
              <span>Vitesse:</span>
              <input
                type="range" min={1} max={10}
                value={form.speed}
                onChange={(e) => setForm({ ...form, speed: +e.target.value })}
                className="w-20"
              />
              <span>{form.speed}</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-zinc-500">
              <span>Qualité:</span>
              <input
                type="range" min={1} max={10}
                value={form.quality}
                onChange={(e) => setForm({ ...form, quality: +e.target.value })}
                className="w-20"
              />
              <span>{form.quality}</span>
            </div>
            <button
              onClick={handleRegister}
              disabled={!form.name}
              className="col-span-2 rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              Enregistrer
            </button>
          </div>
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="flex h-32 items-center justify-center text-sm text-zinc-400">Chargement...</div>
      ) : filtered.length === 0 ? (
        <div className="flex h-32 items-center justify-center rounded-lg border border-zinc-200 text-sm text-zinc-400">
          Aucun agent trouvé
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-zinc-200">
          <table className="w-full text-left text-sm">
            <thead className="bg-zinc-50 text-xs uppercase text-zinc-500">
              <tr>
                <th className="px-3 py-2">Agent</th>
                <th className="px-3 py-2">Provider</th>
                <th className="px-3 py-2">Capacités</th>
                <th className="px-3 py-2">C/S/Q</th>
                <th className="px-3 py-2">Statut</th>
                <th className="px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {filtered.map((a) => (
                <tr key={a.id} className="hover:bg-zinc-50">
                  <td className="px-3 py-2">
                    <div className="font-medium text-zinc-900">{a.name}</div>
                    <div className="text-[10px] text-zinc-400">{a.external_id}</div>
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                        PROVIDER_BADGES[a.provider] || "bg-zinc-100 text-zinc-700"
                      }`}
                    >
                      {a.provider}
                    </span>
                    {a.endpoint_url && (
                      <div className="mt-0.5 text-[9px] text-zinc-400 truncate max-w-[120px]">{a.endpoint_url}</div>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex flex-wrap gap-1">
                      {(a.capabilities || []).slice(0, 4).map((c) => (
                        <span key={c} className="rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] text-zinc-600">
                          {c}
                        </span>
                      ))}
                      {(a.capabilities || []).length > 4 && (
                        <span className="text-[10px] text-zinc-400">+{a.capabilities.length - 4}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-3 py-2 text-xs text-zinc-500">
                    {a.cost}/{a.speed}/{a.quality}
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                        STATUS_COLORS[a.status] || "text-zinc-500"
                      }`}
                    >
                      {a.status}
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex gap-1">
                      {a.status === "discovered" && (
                        <>
                          <button
                            onClick={() => handleApprove(a.id)}
                            className="rounded bg-green-100 px-2 py-0.5 text-[10px] font-medium text-green-700 hover:bg-green-200"
                          >
                            Approuver
                          </button>
                          <button
                            onClick={() => handleReject(a.id)}
                            className="rounded bg-red-100 px-2 py-0.5 text-[10px] font-medium text-red-700 hover:bg-red-200"
                          >
                            Rejeter
                          </button>
                        </>
                      )}
                      {a.status === "pending" && (
                        <>
                          <button
                            onClick={() => handleApprove(a.id)}
                            className="rounded bg-green-100 px-2 py-0.5 text-[10px] font-medium text-green-700 hover:bg-green-200"
                          >
                            Approuver
                          </button>
                          <button
                            onClick={() => handleReject(a.id)}
                            className="rounded bg-red-100 px-2 py-0.5 text-[10px] font-medium text-red-700 hover:bg-red-200"
                          >
                            Rejeter
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
