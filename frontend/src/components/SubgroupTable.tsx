"use client";

import type { SubgroupAuditRow } from "@/lib/types";

function fmtPct(value: number | null): string {
  return value === null ? "—" : `${(value * 100).toFixed(1)}%`;
}

function fmtCi(lower: number | null, upper: number | null): string {
  return lower === null || upper === null
    ? "—"
    : `[${(lower * 100).toFixed(1)}%, ${(upper * 100).toFixed(1)}%]`;
}

export function SubgroupTable({ rows }: { rows: SubgroupAuditRow[] }) {
  return (
    <table className="mt-4 w-full border-collapse text-sm">
      <thead>
        <tr className="border-b border-neutral-200 text-left dark:border-neutral-800">
          <th className="py-2 pr-4 font-medium">Stratum</th>
          <th className="py-2 pr-4 font-medium">N</th>
          <th className="py-2 pr-4 font-medium">TPR</th>
          <th className="py-2 pr-4 font-medium">TPR 95% CI</th>
          <th className="py-2 pr-4 font-medium">Enrolment rate</th>
          <th className="py-2 font-medium">Enrolment 95% CI</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.stratum} className="border-b border-neutral-100 dark:border-neutral-900">
            <td className="py-2 pr-4 capitalize">{row.stratum}</td>
            <td className="py-2 pr-4">{row.n.toLocaleString()}</td>
            {row.sufficient_n ? (
              <>
                <td className="py-2 pr-4">{fmtPct(row.tpr)}</td>
                <td className="py-2 pr-4 text-neutral-500">{fmtCi(row.tpr_ci_lower, row.tpr_ci_upper)}</td>
                <td className="py-2 pr-4">{fmtPct(row.enrolment_rate)}</td>
                <td className="py-2 text-neutral-500">
                  {fmtCi(row.enrolment_rate_ci_lower, row.enrolment_rate_ci_upper)}
                </td>
              </>
            ) : (
              <td colSpan={4} className="py-2 text-amber-700 dark:text-amber-400">
                insufficient n (&lt; 30) — no point estimate reported
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
