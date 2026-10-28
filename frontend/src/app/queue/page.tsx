import { ArrowRight, ClipboardList, Users } from "lucide-react";
import Link from "next/link";

import { Callout } from "@/components/ui/Callout";
import { Card } from "@/components/ui/Card";
import { InfoTip } from "@/components/ui/InfoTip";
import { PageHeader } from "@/components/ui/PageHeader";
import { RiskBar } from "@/components/ui/RiskBar";
import { StatusBadge, TierBadge } from "@/components/ui/Badge";
import { getQueue } from "@/lib/api";
import { docsLink } from "@/lib/docs";
import { GLOSSARY } from "@/lib/glossary";
import type { QueueEntry } from "@/lib/types";

export const dynamic = "force-dynamic";

const SHOWN = 50;

export default async function QueuePage() {
  let entries: QueueEntry[];
  let error: string | null = null;
  try {
    entries = await getQueue("pending");
  } catch (err) {
    entries = [];
    error = err instanceof Error ? err.message : String(err);
  }

  return (
    <main>
      <PageHeader
        icon={ClipboardList}
        eyebrow="Step 3 & 4 · Review"
        title="Review queue"
        docsHref={docsLink("llmIsNotTheRiskModel")}
        docsLabel="Why the AI agent never sets the risk score"
      >
        <p>
          These are the synthetic patients the risk model flagged as likely to have a high illness
          burden in the next six months — candidates for a care-management programme. They are
          ranked by the model&apos;s risk score, highest first.
        </p>
        <p>
          <strong className="text-slate-900 dark:text-white">Open any patient</strong> to have the
          AI agent gather evidence into a case brief, then decide whether to enrol them.
        </p>
      </PageHeader>

      {error && (
        <Callout variant="warning" title="Could not reach the backend">
          {error}. Start the API with <code>make dev</code> (or <code>make run</code>), and build
          the data with <code>make data &amp;&amp; make train</code> first.
        </Callout>
      )}

      {!error && entries.length === 0 && (
        <Callout title="The queue is empty">
          No patients are waiting for review. Run <code>make train</code> (which calls{" "}
          <code>data.populate_queue</code>) to score the cohort and fill the queue.
        </Callout>
      )}

      {entries.length > 0 && (
        <>
          <div className="mb-6 grid gap-4 sm:grid-cols-3">
            <Card>
              <div className="flex items-center gap-3">
                <span className="rounded-lg bg-teal-50 p-2 text-teal-700 dark:bg-teal-950 dark:text-teal-300">
                  <Users className="h-5 w-5" aria-hidden />
                </span>
                <div>
                  <p className="text-2xl font-bold text-slate-900 dark:text-white">
                    {entries.length.toLocaleString()}
                  </p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">patients awaiting review</p>
                </div>
              </div>
            </Card>
            <Card className="sm:col-span-2">
              <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-300">
                <strong className="text-slate-900 dark:text-white">Who decided they belong here?</strong>{" "}
                A statistical model, not the AI agent. Everyone scoring at or above the model&apos;s
                threshold is queued
                <InfoTip text={GLOSSARY.threshold} />. Patients with a recorded death are excluded.
              </p>
            </Card>
          </div>

          <Card padded={false} className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-800/60 dark:text-slate-400">
                  <tr>
                    <th className="px-5 py-3 font-semibold">#</th>
                    <th className="px-5 py-3 font-semibold">Patient</th>
                    <th className="px-5 py-3 font-semibold">
                      Risk score
                      <InfoTip text={GLOSSARY.riskScore} />
                    </th>
                    <th className="px-5 py-3 font-semibold">
                      Tier
                      <InfoTip text={GLOSSARY.tier} />
                    </th>
                    <th className="px-5 py-3 font-semibold">
                      Status
                      <InfoTip text={GLOSSARY.status} />
                    </th>
                    <th className="px-5 py-3" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {entries.slice(0, SHOWN).map((entry, i) => (
                    <tr key={entry.patient_id} className="group relative hover:bg-teal-50/50 dark:hover:bg-teal-950/30">
                      <td className="px-5 py-3 text-slate-400">{i + 1}</td>
                      <td className="px-5 py-3 font-mono text-xs text-slate-700 dark:text-slate-300">
                        <Link
                          href={`/queue/${entry.patient_id}`}
                          className="after:absolute after:inset-0 focus:outline-none focus-visible:underline"
                          aria-label={`Review patient ${entry.patient_id.slice(0, 8)}`}
                        >
                          {entry.patient_id.slice(0, 8)}…
                        </Link>
                      </td>
                      <td className="px-5 py-3">
                        <RiskBar score={entry.risk_score} />
                      </td>
                      <td className="px-5 py-3">
                        <TierBadge tier={entry.risk_tier} />
                      </td>
                      <td className="px-5 py-3">
                        <StatusBadge status={entry.status} />
                      </td>
                      <td className="px-5 py-3 text-right">
                        <span className="inline-flex items-center gap-1 text-sm font-medium text-teal-700 group-hover:gap-2 dark:text-teal-400">
                          Review <ArrowRight className="h-4 w-4 transition-all" aria-hidden />
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
          {entries.length > SHOWN && (
            <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
              Showing the {SHOWN} highest-risk of {entries.length.toLocaleString()} pending patients.
            </p>
          )}
        </>
      )}
    </main>
  );
}
