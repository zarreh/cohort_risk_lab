import { CircleAlert, Info, TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";

const STYLES = {
  info: {
    box: "border-teal-200 bg-teal-50 text-teal-900 dark:border-teal-900 dark:bg-teal-950/60 dark:text-teal-100",
    icon: Info,
  },
  warning: {
    box: "border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-900 dark:bg-amber-950/60 dark:text-amber-100",
    icon: TriangleAlert,
  },
  error: {
    box: "border-red-200 bg-red-50 text-red-900 dark:border-red-900 dark:bg-red-950/60 dark:text-red-100",
    icon: CircleAlert,
  },
} as const;

export function Callout({
  variant = "info",
  title,
  children,
  className = "",
}: {
  variant?: keyof typeof STYLES;
  title?: string;
  children: ReactNode;
  className?: string;
}) {
  const { box, icon: Icon } = STYLES[variant];
  return (
    <div className={`flex gap-3 rounded-xl border p-4 text-sm ${box} ${className}`}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <div className="space-y-1">
        {title && <p className="font-semibold">{title}</p>}
        <div className="leading-relaxed">{children}</div>
      </div>
    </div>
  );
}
