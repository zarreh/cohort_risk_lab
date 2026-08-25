export default function Home() {
  return (
    <main className="mx-auto max-w-2xl p-8 font-sans">
      <h1 className="text-2xl font-bold">Cohort Risk & Review Lab</h1>
      <p className="mt-2 text-sm text-neutral-500">
        A calibrated risk model stratifies a synthetic patient population for
        care-management enrolment. A subgroup audit reports fairness per
        stratum, and a review agent assembles the evidence for each flagged
        case — it never assigns the tier and never enrols anyone.
      </p>
      <p className="mt-6 text-sm text-neutral-400">
        Phase 0 — template shakedown. The review queue and case brief land in
        later phases; see{" "}
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
