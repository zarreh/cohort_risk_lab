import { Scale } from "lucide-react";

import { SubgroupTable } from "@/components/SubgroupTable";
import { Callout } from "@/components/ui/Callout";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { getSubgroupAudit } from "@/lib/api";
import { docsLink } from "@/lib/docs";
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
    <main>
      <PageHeader
        icon={Scale}
        eyebrow="Step 2 · Fairness"
        title="Subgroup fairness audit"
        docsHref={docsLink("fairnessAudit")}
        docsLabel="Read the full fairness audit"
      >
        <p>
          A model can look accurate overall while quietly failing one group of patients. So
          instead of one overall score, this audit reports how the risk model performs for
          <strong className="text-slate-900 dark:text-white"> each demographic group separately</strong>.
        </p>
        <p>
          The key column is the <strong className="text-slate-900 dark:text-white">true-positive rate</strong>:
          of the patients who really did go on to have a high illness burden, what share the
          model caught. Similar rates across groups mean the model misses people at similar rates
          regardless of who they are.
        </p>
      </PageHeader>

      <div className="mb-6 grid gap-4 md:grid-cols-3">
        <Card>
          <p className="text-sm font-semibold text-slate-900 dark:text-white">Held-out data only</p>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Computed on patients the model never saw during training.
          </p>
        </Card>
        <Card>
          <p className="text-sm font-semibold text-slate-900 dark:text-white">Uncertainty shown</p>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            The shaded bar is the 95% confidence interval; the dark tick is the estimate.{" "}
            <a className="text-teal-700 underline dark:text-teal-400" href={docsLink("minNConfidenceIntervals")} target="_blank" rel="noreferrer">
              Why
            </a>
          </p>
        </Card>
        <Card>
          <p className="text-sm font-semibold text-slate-900 dark:text-white">Small groups not hidden</p>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Groups under 30 patients are listed but get no number, rather than a misleadingly precise one.
          </p>
        </Card>
      </div>

      {error && (
        <Callout variant="warning" title="Could not reach the backend">
          {error}. Run <code>make data &amp;&amp; make train</code> first.
        </Callout>
      )}

      {rows.length > 0 && (
        <Card padded={false} className="overflow-hidden">
          <SubgroupTable rows={rows} />
        </Card>
      )}

      <Callout className="mt-6" title="Why not make every rate exactly equal?">
        The deployed model is <em>calibrated</em> — a score of 0.4 means roughly a 40% chance for
        every group. Once groups have different underlying rates of illness, a model cannot be
        both calibrated and have identical error rates everywhere; this project chose
        calibration.{" "}
        <a className="font-medium underline" href={docsLink("calibrationOverEqualisedOdds")} target="_blank" rel="noreferrer">
          Read the decision
        </a>
        .
      </Callout>
    </main>
  );
}
