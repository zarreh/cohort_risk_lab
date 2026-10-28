import { ChartBar } from "lucide-react";

import { LabelChoiceChart } from "@/components/LabelChoiceChart";
import { Callout } from "@/components/ui/Callout";
import { Card, CardTitle } from "@/components/ui/Card";
import { InfoTip } from "@/components/ui/InfoTip";
import { PageHeader } from "@/components/ui/PageHeader";
import { getLabelChoice } from "@/lib/api";
import { docsLink } from "@/lib/docs";
import { GLOSSARY } from "@/lib/glossary";
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
  const blackHasLargestDrop =
    blackRow !== undefined && rows.every((r) => r.gap_percentage_points >= blackRow.gap_percentage_points);

  return (
    <main>
      <PageHeader
        icon={ChartBar}
        eyebrow="Evidence · Why the label matters"
        title="The label-choice experiment"
        docsHref={docsLink("labelChoice")}
        docsLabel="Read the full experiment write-up"
      >
        <p>
          Every model is trained to predict <em>something</em> — its <strong className="text-slate-900 dark:text-white">label</strong>
          <InfoTip text={GLOSSARY.labelChoice} />. Here, two otherwise identical models are trained:
          one to predict <strong className="text-slate-900 dark:text-white">illness burden</strong>, one to
          predict <strong className="text-slate-900 dark:text-white">healthcare cost</strong>.
        </p>
        <p>
          Cost sounds like a reasonable stand-in for need, but people with less access to care
          spend less even when equally sick. A cost-trained model therefore under-selects them —
          the exact flaw Obermeyer et al. (2019) found in a widely used US hospital algorithm.
        </p>
      </PageHeader>

      <blockquote className="mb-6 border-l-4 border-teal-500 pl-4 text-slate-600 italic dark:text-slate-300">
        &ldquo;The most consequential bug in the most widely deployed clinical algorithm in America
        was not in the model. It was in the label — it predicted cost and everyone read it as
        illness.&rdquo;
      </blockquote>

      {error && (
        <Callout variant="warning" title="Could not reach the backend">
          {error}. Run <code>make data &amp;&amp; make train</code> first.
        </Callout>
      )}

      {rows.length > 0 && (
        <div className="grid gap-6 lg:grid-cols-3">
          {blackRow && (
            <Card tone="red" className="self-start">
              <CardTitle>Key finding</CardTitle>
              <p className="mt-3 text-4xl font-bold tabular-nums text-red-600 dark:text-red-400">
                {blackRow.gap_percentage_points > 0 ? "+" : "−"}
                {Math.abs(blackRow.gap_percentage_points).toFixed(1)} pp
              </p>
              <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
                <strong className="text-slate-900 dark:text-white">Black patients</strong> are
                selected {(blackRow.burden_enrolment_rate * 100).toFixed(1)}% of the time by the
                illness-trained model, but only {(blackRow.cost_enrolment_rate * 100).toFixed(1)}%
                by the cost-trained one
                {blackHasLargestDrop ? " — the largest drop of any group" : ""} (
                {blackRow.n.toLocaleString()} patients in the validation set).
              </p>
              <p className="mt-3 text-sm font-semibold text-slate-900 dark:text-white">
                Neither model was given race as a feature.
              </p>
            </Card>
          )}
          <Card className={blackRow ? "lg:col-span-2" : "lg:col-span-3"}>
            <CardTitle>
              Change in selection rate, cost model vs illness model
              <InfoTip text={GLOSSARY.gap} />
            </CardTitle>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
              Both models pick the top 20% of the same validation patients using the same features
              (race and ethnicity excluded). Bars left of zero: the cost model picks that group
              less often.
            </p>
            <LabelChoiceChart rows={rows} />
          </Card>
        </div>
      )}

      <Callout variant="warning" className="mt-6" title="Disclosure: the access gap is injected">
        Synthea&apos;s synthetic data has no built-in disparity in access to care, so one was added
        deliberately, with a published, seeded parameter. The claim here is that{" "}
        <em>the audit catches an access gap of this shape</em> — not that this app discovered a
        real-world disparity.{" "}
        <a className="font-medium underline" href={docsLink("injectedAccessGap")} target="_blank" rel="noreferrer">
          Read the decision
        </a>
        .
      </Callout>
    </main>
  );
}
