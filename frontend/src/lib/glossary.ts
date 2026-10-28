// Plain-language definitions shown in ⓘ tooltips, kept in one place so
// every page explains a term the same way.
export const GLOSSARY = {
  riskScore:
    "The statistical model's estimated probability (0–1) that this patient will have a high illness burden in the next six months. Produced by the model, never by the AI agent.",
  threshold:
    "Patients scoring at or above the model's threshold are flagged for review. It is chosen to balance missing someone who needs help against spending clinician time on someone who doesn't.",
  tier: "High = at or above the review threshold. The tier comes from the model's score, not from the AI agent.",
  status:
    "Pending → the AI agent is gathering evidence → awaiting a clinician's decision → decided.",
  drivers:
    "Which of the patient's features pushed the model's score up or down (SHAP contributions). Red bars increase risk, teal bars decrease it.",
  stratum: "A demographic group (by age, sex, race or insurance) the audit reports on separately.",
  n: "Number of patients in this group in the held-out validation set.",
  tpr: "True-positive rate: of the patients in this group who really went on to have a high illness burden, the share the model flagged. Higher is better; big differences between groups mean the model misses some groups more often.",
  enrolmentRate: "Share of this group the model would flag for care-management review.",
  ci: "95% confidence interval: the range the true value plausibly lies in. Wide ranges mean small groups, so read the point estimate with care.",
  insufficientN:
    "Fewer than 30 patients: too few to say anything reliable, so no number is shown rather than a misleadingly precise one.",
  labelChoice:
    "The 'label' is what a model is trained to predict. The burden model predicts illness; the cost model predicts healthcare spending — which also reflects how much care someone could access.",
  gap: "Cost-model enrolment rate minus burden-model enrolment rate, in percentage points. Negative means the cost-trained model selects that group less often.",
} as const;
