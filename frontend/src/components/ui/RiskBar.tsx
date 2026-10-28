function riskColour(score: number): string {
  if (score >= 0.6) return "bg-red-500";
  if (score >= 0.35) return "bg-orange-500";
  return "bg-amber-400";
}

export function RiskBar({ score, size = "sm" }: { score: number; size?: "sm" | "lg" }) {
  const pct = Math.max(0, Math.min(1, score)) * 100;
  return (
    <div className={`flex items-center gap-3 ${size === "lg" ? "w-full" : "w-40"}`}>
      <span
        className={`tabular-nums font-semibold text-slate-900 dark:text-white ${size === "lg" ? "text-3xl" : "w-12 text-sm"}`}
      >
        {score.toFixed(size === "lg" ? 2 : 3)}
      </span>
      <div
        className={`flex-1 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700 ${size === "lg" ? "h-2.5" : "h-1.5"}`}
        role="meter"
        aria-valuemin={0}
        aria-valuemax={1}
        aria-valuenow={Number(score.toFixed(3))}
        aria-label="Risk score"
      >
        <div className={`h-full rounded-full ${riskColour(score)}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
