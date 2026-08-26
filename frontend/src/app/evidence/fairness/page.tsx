import { getSubgroupAudit } from "@/lib/api";
import { SubgroupTable } from "@/components/SubgroupTable";
import type { SubgroupAuditRow } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function FairnessPage() {
  let rows: SubgroupAuditRow[];
  let error: string | null = null;
  try {
    rows = await getSubgroupAudit("v1_burden");
  } catch (err) {
    rows = [];
    error = err instanceof Error ? err.message : String(err);
  }

  return (
    <main className="mx-auto max-w-4xl p-8 font-sans">
      <h1 className="text-2xl font-bold">Subgroup fairness audit</h1>
      <p className="mt-2 text-sm text-neutral-500 dark:text-neutral-400">
        Computed on the held-out validation set only — never on data the
        model was trained on. A stratum below 30 patients is shown, not
        dropped, with every rate reported as insufficient rather than a
        misleadingly precise number. See{" "}
        <a
          className="underline"
          href="https://github.com/zarreh/cohort_risk_lab/blob/main/docs/architecture/decisions/D-A12-5-min-n-confidence-intervals.md"
        >
          D-A12-5
        </a>
        .
      </p>

      {error && (
        <p className="mt-6 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
          Could not reach the backend ({error}). Run{" "}
          <code>make data &amp;&amp; make train</code> first.
        </p>
      )}

      {rows.length > 0 && <SubgroupTable rows={rows} />}

      <p className="mt-6 text-xs text-neutral-400">
        Model <code>v1_burden</code> is calibrated, not equalised-odds-matched
        — the two cannot both hold once base rates differ across strata. See{" "}
        <a
          className="underline"
          href="https://github.com/zarreh/cohort_risk_lab/blob/main/docs/architecture/decisions/D-A12-3-calibration-over-equalised-odds.md"
        >
          D-A12-3
        </a>
        .
      </p>
    </main>
  );
}
