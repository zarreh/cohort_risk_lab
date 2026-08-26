import { getLabelChoice } from "@/lib/api";
import { LabelChoiceChart } from "@/components/LabelChoiceChart";
import type { LabelChoiceRow } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function LabelChoicePage() {
  let rows: LabelChoiceRow[];
  let error: string | null = null;
  try {
    rows = await getLabelChoice();
  } catch (err) {
    rows = [];
    error = err instanceof Error ? err.message : String(err);
  }

  const blackRow = rows.find((r) => r.race === "black");

  return (
    <main className="mx-auto max-w-4xl p-8 font-sans">
      <h1 className="text-2xl font-bold">The label-choice experiment ★</h1>
      <p className="mt-2 text-sm italic text-neutral-500 dark:text-neutral-400">
        &ldquo;The most consequential bug in the most widely deployed clinical
        algorithm in America was not in the model. It was in the label — it
        predicted cost and everyone read it as illness.&rdquo;
      </p>

      <div className="mt-4 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
        <strong>Disclosure:</strong> the divergence below depends on an
        access gap injected deliberately, with a published, seeded
        parameter — Synthea has no such disparity built in. The claim being
        made is &ldquo;the subgroup audit catches an access gap of this
        shape,&rdquo; not that this app discovered a real-world disparity.
        See{" "}
        <a
          className="underline"
          href="https://github.com/zarreh/cohort_risk_lab/blob/main/docs/architecture/decisions/D-A12-2-injected-access-gap.md"
        >
          D-A12-2
        </a>
        .
      </div>

      {error && (
        <p className="mt-6 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
          Could not reach the backend ({error}). Run{" "}
          <code>make data &amp;&amp; make train</code> first.
        </p>
      )}

      {rows.length > 0 && (
        <>
          <p className="mt-6 text-sm text-neutral-600 dark:text-neutral-400">
            Two models, trained on the identical validation population with
            the identical features — race and ethnicity excluded from both.
            Selecting the top 20% by each model&apos;s own predicted
            probability, who gets selected differs by race:
          </p>
          <LabelChoiceChart rows={rows} />
          {blackRow && (
            <p className="mt-4 text-sm">
              <strong>Black patients</strong> ({blackRow.n.toLocaleString()} in
              this validation split): enrolled at{" "}
              {(blackRow.burden_enrolment_rate * 100).toFixed(1)}% under the
              burden-trained model vs.{" "}
              {(blackRow.cost_enrolment_rate * 100).toFixed(1)}% under the
              cost-trained model — a{" "}
              {Math.abs(blackRow.gap_percentage_points).toFixed(1)} percentage
              point gap, larger than any other minority stratum.{" "}
              <strong>Neither model was given race as a feature.</strong>
            </p>
          )}
        </>
      )}
    </main>
  );
}
