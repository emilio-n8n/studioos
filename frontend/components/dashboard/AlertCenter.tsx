"use client";

interface Alert {
  type: "risk" | "delay";
  message: string;
}

interface Props {
  alerts: Alert[];
}

const ALERT_STYLES: Record<string, string> = {
  risk: "border-amber-300 bg-amber-50 text-amber-800",
  delay: "border-yellow-300 bg-yellow-50 text-yellow-800",
};

export default function AlertCenter({ alerts }: Props) {
  if (alerts.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-4 text-center text-sm text-zinc-400 shadow-sm">
        Aucune alerte
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {alerts.map((alert, i) => (
        <div
          key={`alert-${i}`}
          className={`rounded-lg border px-3 py-2 text-sm ${ALERT_STYLES[alert.type] || ALERT_STYLES.risk}`}
        >
          <span className="mr-1.5 font-semibold uppercase">{alert.type}:</span>
          {alert.message}
        </div>
      ))}
    </div>
  );
}
