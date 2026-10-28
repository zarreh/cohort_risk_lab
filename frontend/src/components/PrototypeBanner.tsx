import { TriangleAlert } from "lucide-react";

import { docsLink } from "@/lib/docs";

export function PrototypeBanner() {
  return (
    <div className="flex items-center justify-center gap-2 bg-amber-100 px-4 py-1.5 text-center text-xs text-amber-900 dark:bg-amber-950 dark:text-amber-200">
      <TriangleAlert className="hidden h-3.5 w-3.5 shrink-0 sm:block" aria-hidden />
      <span>
        Architectural demonstration, fully synthetic Synthea data — not a medical device, does not
        diagnose or screen for disease.{" "}
        <a className="font-medium underline" href={docsLink("regulatoryBasis")} target="_blank" rel="noreferrer">
          Regulatory basis
        </a>
      </span>
    </div>
  );
}
