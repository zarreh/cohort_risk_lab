const REGULATORY_BASIS_URL =
  "https://github.com/zarreh/cohort_risk_lab/blob/main/docs/regulatory-basis.md";

export function PrototypeBanner() {
  return (
    <div className="border-b border-amber-300 bg-amber-50 px-4 py-2 text-center text-xs text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
      Architectural demonstration, fully synthetic Synthea data — not a
      medical device, does not diagnose or screen for disease. See{" "}
      <a className="underline" href={REGULATORY_BASIS_URL}>
        regulatory basis
      </a>
      .
    </div>
  );
}
