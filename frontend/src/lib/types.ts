// Mirrors src/cohort/api/schemas.py exactly. Regenerate via
// `make frontend-types` (openapi-typescript against the live backend)
// once the schema stabilises; hand-typed for now so the frontend can be
// built without a running backend.

export interface QueueEntry {
  patient_id: string;
  risk_score: number;
  risk_tier: string;
  status: "pending" | "in_review" | "awaiting_decision" | "decided";
  created_at: string;
  updated_at: string;
}

export interface CaseDetail {
  patient_id: string;
  risk_score: number;
  risk_tier: string;
  status: string;
  decision: string | null;
  override_notes: string | null;
  decided_at: string | null;
}

export interface Driver {
  feature_name: string;
  contribution: number;
  direction: "increases_risk" | "decreases_risk";
}

export interface CorroboratingEvidence {
  source: string;
  description: string;
}

export interface CaseBrief {
  patient_id: string;
  narrative: string;
  drivers: Driver[];
  corroborating_evidence: CorroboratingEvidence[];
  care_gaps: string[];
  missing_data: string[];
  what_would_change_this: string;
}

export interface ReviewEventPayload {
  node: string;
  output: unknown;
}

export interface SubgroupAuditRow {
  stratum: string;
  n: number;
  sufficient_n: boolean;
  calibration_in_the_large: number | null;
  expected_calibration_error: number | null;
  tpr: number | null;
  tpr_ci_lower: number | null;
  tpr_ci_upper: number | null;
  enrolment_rate: number | null;
  enrolment_rate_ci_lower: number | null;
  enrolment_rate_ci_upper: number | null;
}

export interface LabelChoiceRow {
  race: string;
  n: number;
  burden_enrolment_rate: number;
  cost_enrolment_rate: number;
  gap_percentage_points: number;
}
