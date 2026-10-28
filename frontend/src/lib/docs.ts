// The MkDocs site (docs/). Overridable so a fork or staging deploy can point at its own copy.
export const DOCS_URL = (
  process.env.NEXT_PUBLIC_DOCS_URL ?? "https://zarreh.ai/clinical_care_navigator/"
).replace(/\/?$/, "/");

export const REPO_URL = "https://github.com/zarreh/cohort_risk_lab";

export const DOC_PAGES = {
  home: "",
  plainLanguage: "how-it-works/in-plain-language/",
  architecture: "architecture/overview/",
  fairnessAudit: "evidence/fairness-audit/",
  labelChoice: "evidence/label-choice-experiment/",
  regulatoryBasis: "regulatory-basis/",
  runItYourself: "run-it-yourself/",
  llmIsNotTheRiskModel: "architecture/decisions/D-A12-1-llm-is-not-the-risk-model/",
  injectedAccessGap: "architecture/decisions/D-A12-2-injected-access-gap/",
  calibrationOverEqualisedOdds:
    "architecture/decisions/D-A12-3-calibration-over-equalised-odds/",
  minNConfidenceIntervals: "architecture/decisions/D-A12-5-min-n-confidence-intervals/",
} as const;

export function docsLink(page: keyof typeof DOC_PAGES): string {
  return `${DOCS_URL}${DOC_PAGES[page]}`;
}
