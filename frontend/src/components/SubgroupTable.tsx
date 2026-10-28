import { Badge } from "@/components/ui/Badge";
import { InfoTip } from "@/components/ui/InfoTip";
import { GLOSSARY } from "@/lib/glossary";
import type { SubgroupAuditRow } from "@/lib/types";

function fmtPct(value: number | null): string {
  return value === null ? "—" : `${(value * 100).toFixed(1)}%`;
}

function RateWithCi({
  value,
  lower,
  upper,
  colour,
}: {
  value: number | null;
  lower: number | null;
  upper: number | null;
  colour: string;
}) {
  if (value === null) return <span className="text-slate-400">—</span>;
  return (
    <div className="min-w-[11rem]">
      <div className="flex items-baseline justify-between gap-2">
        <span className="font-semibold tabular-nums text-slate-900 dark:text-white">{fmtPct(value)}</span>
        {lower !== null && upper !== null && (
          <span className="text-xs tabular-nums text-slate-400">
            {fmtPct(lower)} – {fmtPct(upper)}
          </span>
        )}
      </div>
      <div className="relative mt-1 h-2 rounded-full bg-slate-100 dark:bg-slate-800">
        {lower !== null && upper !== null && (
          <span
            className={`absolute inset-y-0 rounded-full opacity-30 ${colour}`}
            style={{ left: `${lower * 100}%`, width: `${Math.max((upper - lower) * 100, 0.5)}%` }}
          />
        )}
        <span
          className={`absolute -top-0.5 h-3 w-1 -translate-x-1/2 rounded ${colour}`}
          style={{ left: `${value * 100}%` }}
        />
      </div>
    </div>
  );
}

export function SubgroupTable({ rows }: { rows: SubgroupAuditRow[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-800/60 dark:text-slate-400">
          <tr>
            <th className="px-5 py-3 font-semibold">
              Group
              <InfoTip text={GLOSSARY.stratum} />
            </th>
            <th className="px-5 py-3 text-right font-semibold">
              Patients
              <InfoTip text={GLOSSARY.n} />
            </th>
            <th className="px-5 py-3 font-semibold">
              True-positive rate · 95% CI
              <InfoTip text={`${GLOSSARY.tpr} ${GLOSSARY.ci}`} />
            </th>
            <th className="px-5 py-3 font-semibold">
              Flagged for review · 95% CI
              <InfoTip text={GLOSSARY.enrolmentRate} />
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
          {rows.map((row) => (
            <tr key={row.stratum} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
              <td className="px-5 py-3 font-medium capitalize text-slate-800 dark:text-slate-200">
                {row.stratum.replace(/_/g, " ")}
              </td>
              <td className="px-5 py-3 text-right tabular-nums text-slate-600 dark:text-slate-400">
                {row.n.toLocaleString()}
              </td>
              {row.sufficient_n ? (
                <>
                  <td className="px-5 py-3">
                    <RateWithCi value={row.tpr} lower={row.tpr_ci_lower} upper={row.tpr_ci_upper} colour="bg-teal-600" />
                  </td>
                  <td className="px-5 py-3">
                    <RateWithCi
                      value={row.enrolment_rate}
                      lower={row.enrolment_rate_ci_lower}
                      upper={row.enrolment_rate_ci_upper}
                      colour="bg-indigo-600"
                    />
                  </td>
                </>
              ) : (
                <td colSpan={2} className="px-5 py-3">
                  <span className="inline-flex items-center gap-1">
                    <Badge variant="amber">Too few patients (&lt; 30)</Badge>
                    <InfoTip text={GLOSSARY.insufficientN} />
                  </span>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
