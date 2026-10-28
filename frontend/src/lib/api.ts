// HTTP client only — no business logic here (PORTFOLIO_PLAN_V3.md §10).
// The FastAPI backend is the single source of truth for every decision
// this app makes; this file just calls it.

import type { CaseDetail, LabelChoiceRow, QueueEntry, SubgroupAuditRow } from "./types";

const PUBLIC_API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// Server components run inside the web container, where the browser-facing URL is not routable.
function serverSideBaseUrl(): string {
  return process.env.API_INTERNAL_URL ?? PUBLIC_API_BASE_URL;
}

async function get<T>(path: string): Promise<T> {
  const base = typeof window === "undefined" ? serverSideBaseUrl() : PUBLIC_API_BASE_URL;
  const response = await fetch(`${base}${path}`);
  if (!response.ok) {
    throw new Error(`${path} failed: ${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

// FastAPI puts the human-readable reason in `detail`; surface it rather than a bare status code.
async function failureMessage(action: string, response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") {
      return `${action} failed: ${response.status} — ${body.detail}`;
    }
  } catch {
    // non-JSON body; fall through
  }
  return `${action} failed: ${response.status}`;
}

export function getQueue(status?: string): Promise<QueueEntry[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return get<QueueEntry[]>(`/queue${query}`);
}

export function getCase(patientId: string): Promise<CaseDetail> {
  return get<CaseDetail>(`/queue/${encodeURIComponent(patientId)}`);
}

export async function startReview(patientId: string): Promise<void> {
  const response = await fetch(`${PUBLIC_API_BASE_URL}/queue/${encodeURIComponent(patientId)}/start`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(await failureMessage("start review", response));
  }
}

export async function submitDecision(
  patientId: string,
  decision: "enrol" | "decline" | "defer",
  notes?: string,
): Promise<void> {
  const response = await fetch(`${PUBLIC_API_BASE_URL}/queue/${encodeURIComponent(patientId)}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, notes: notes ?? null }),
  });
  if (!response.ok) {
    throw new Error(await failureMessage("submit decision", response));
  }
}

export function reviewEventsUrl(patientId: string): string {
  return `${PUBLIC_API_BASE_URL}/queue/${encodeURIComponent(patientId)}/events`;
}

export function getSubgroupAudit(version = "v1_burden"): Promise<SubgroupAuditRow[]> {
  return get<SubgroupAuditRow[]>(`/evidence/subgroup-audit?version=${encodeURIComponent(version)}`);
}

export function getLabelChoice(): Promise<LabelChoiceRow[]> {
  return get<LabelChoiceRow[]>("/evidence/label-choice");
}
