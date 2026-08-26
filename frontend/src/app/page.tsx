import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto max-w-2xl p-8 font-sans">
      <h1 className="text-2xl font-bold">Cohort Risk & Review Lab</h1>
      <p className="mt-2 text-sm text-neutral-500 dark:text-neutral-400">
        A calibrated risk model — not a language model — stratifies a
        synthetic patient population for care-management enrolment. A
        subgroup audit reports fairness per stratum, and a review agent
        assembles the evidence for each flagged case. It never assigns the
        tier and never enrols anyone; a clinician always decides.
      </p>

      <nav className="mt-8 grid gap-3">
        <Link
          href="/queue"
          className="rounded-lg border border-neutral-200 p-4 hover:border-neutral-400 dark:border-neutral-800 dark:hover:border-neutral-600"
        >
          <div className="font-semibold">Review queue</div>
          <div className="text-sm text-neutral-500 dark:text-neutral-400">
            Patients the deployed model flagged, ranked by risk score.
          </div>
        </Link>
        <Link
          href="/evidence/fairness"
          className="rounded-lg border border-neutral-200 p-4 hover:border-neutral-400 dark:border-neutral-800 dark:hover:border-neutral-600"
        >
          <div className="font-semibold">Subgroup fairness audit</div>
          <div className="text-sm text-neutral-500 dark:text-neutral-400">
            Per-stratum calibration and true-positive rate, with confidence
            intervals — computed on the held-out validation set.
          </div>
        </Link>
        <Link
          href="/evidence/label-choice"
          className="rounded-lg border border-neutral-200 p-4 hover:border-neutral-400 dark:border-neutral-800 dark:hover:border-neutral-600"
        >
          <div className="font-semibold">The label-choice experiment ★</div>
          <div className="text-sm text-neutral-500 dark:text-neutral-400">
            Two models, one difference: which label they were trained to
            predict. Reproducing the Obermeyer et al. (2019) finding.
          </div>
        </Link>
      </nav>

      <p className="mt-8 text-sm text-neutral-400">
        Phase 8 — frontend.{" "}
        <a
          className="underline"
          href="https://github.com/zarreh/cohort_risk_lab/blob/main/docs/PLAN.md"
        >
          docs/PLAN.md
        </a>
        .
      </p>
    </main>
  );
}
