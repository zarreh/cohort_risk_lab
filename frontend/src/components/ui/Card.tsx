import type { ReactNode } from "react";

const TONES = {
  default: "border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900",
  teal: "border-teal-300 bg-white ring-1 ring-teal-200 dark:border-teal-800 dark:bg-slate-900 dark:ring-teal-900",
  red: "border-red-200 bg-white dark:border-red-900 dark:bg-slate-900",
  emerald: "border-emerald-300 bg-emerald-50 dark:border-emerald-900 dark:bg-emerald-950/40",
} as const;

export function Card({
  children,
  className = "",
  padded = true,
  tone = "default",
}: {
  children: ReactNode;
  className?: string;
  padded?: boolean;
  tone?: keyof typeof TONES;
}) {
  return (
    <div
      className={`rounded-xl border shadow-sm ${TONES[tone]} ${padded ? "p-5" : ""} ${className}`}
    >
      {children}
    </div>
  );
}

export function CardTitle({ children, icon }: { children: ReactNode; icon?: ReactNode }) {
  return (
    <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
      {icon}
      {children}
    </h2>
  );
}
