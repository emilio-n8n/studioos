"use client";

interface Props {
  label: string;
  value: string | number;
  color?: string;
}

export default function StatsCard({ label, value, color }: Props) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
      <div className="text-sm font-medium text-zinc-500">{label}</div>
      <div className={`mt-1 text-2xl font-bold ${color || "text-zinc-900"}`}>{value}</div>
    </div>
  );
}
