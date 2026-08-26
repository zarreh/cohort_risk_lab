import Link from "next/link";

import { getQueue } from "@/lib/api";
import type { QueueEntry } from "@/lib/types";

export const dynamic = "force-dynamic";

function tierBadgeClass(tier: string): string {
  return tier === "high"
    ? "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200"
    : "bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300";
}

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
    <main className="mx-auto max-w-4xl p-8 font-sans">
      <h1 className="text-2xl font-bold">Review queue</h1>
      <p className="mt-2 text-sm text-neutral-500 dark:text-neutral-400">
        Every patient here was flagged by the deployed model
        (<code>v1_burden</code>), not by an LLM — see{" "}
        <Link className="underline" href="/">
          how this app is built
        </Link>
        .
      </p>

      {error && (
        <p className="mt-6 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
          Could not reach the backend ({error}). Run <code>make dev</code> and{" "}
          <code>make data &amp;&amp; make train</code> first.
        </p>
      )}

      {!error && entries.length === 0 && (
        <p className="mt-6 text-sm text-neutral-500">
          No pending cases. Run <code>make train</code> (which calls{" "}
          <code>data.populate_queue</code>) to enqueue flagged patients.
        </p>
      )}

      {entries.length > 0 && (
        <>
          <p className="mt-4 text-xs text-neutral-400">
            {entries.length.toLocaleString()} pending cases, highest risk first.
          </p>
          <table className="mt-4 w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-neutral-200 text-left dark:border-neutral-800">
                <th className="py-2 pr-4 font-medium">Patient</th>
                <th className="py-2 pr-4 font-medium">Risk score</th>
                <th className="py-2 pr-4 font-medium">Tier</th>
                <th className="py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {entries.slice(0, 50).map((entry) => (
                <tr
                  key={entry.patient_id}
                  className="border-b border-neutral-100 dark:border-neutral-900"
                >
                  <td className="py-2 pr-4 font-mono text-xs">
                    <Link className="underline" href={`/queue/${entry.patient_id}`}>
                      {entry.patient_id.slice(0, 8)}…
                    </Link>
                  </td>
                  <td className="py-2 pr-4">{entry.risk_score.toFixed(3)}</td>
                  <td className="py-2 pr-4">
                    <span className={`rounded px-2 py-0.5 text-xs ${tierBadgeClass(entry.risk_tier)}`}>
                      {entry.risk_tier}
                    </span>
                  </td>
                  <td className="py-2 text-neutral-500">{entry.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {entries.length > 50 && (
            <p className="mt-2 text-xs text-neutral-400">
              Showing the top 50 of {entries.length.toLocaleString()}.
            </p>
          )}
        </>
      )}
    </main>
  );
}
