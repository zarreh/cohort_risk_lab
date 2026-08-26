"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { getCase, reviewEventsUrl, startReview, submitDecision } from "@/lib/api";
import type { CaseBrief, CaseDetail, ReviewEventPayload } from "@/lib/types";

const ACTIVE_STATUSES = new Set(["in_review"]);

function extractBrief(events: ReviewEventPayload[]): CaseBrief | null {
  for (let i = events.length - 1; i >= 0; i -= 1) {
    const output = events[i].output;
    if (
      output !== null &&
      typeof output === "object" &&
      "draft_brief" in output &&
      output.draft_brief !== null
    ) {
      return (output as { draft_brief: CaseBrief }).draft_brief;
    }
  }
  return null;
}

export function CaseReviewClient({
  patientId,
  initialCase,
}: {
  patientId: string;
  initialCase: CaseDetail;
}) {
  const [caseDetail, setCaseDetail] = useState(initialCase);
  const [events, setEvents] = useState<ReviewEventPayload[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const eventSourceRef = useRef<EventSource | null>(null);

  const refreshCase = useCallback(async () => {
    try {
      setCaseDetail(await getCase(patientId));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [patientId]);

  useEffect(() => {
    if (!ACTIVE_STATUSES.has(caseDetail.status)) return undefined;

    const source = new EventSource(reviewEventsUrl(patientId));
    eventSourceRef.current = source;
    source.onmessage = (message) => {
      const payload = JSON.parse(message.data) as ReviewEventPayload;
      if (payload.node === "__end__") {
        source.close();
        void refreshCase();
        return;
      }
      setEvents((prev) => [...prev, payload]);
    };
    source.onerror = () => {
      source.close();
    };
    return () => source.close();
  }, [caseDetail.status, patientId, refreshCase]);

  const handleStart = async () => {
    setError(null);
    try {
      await startReview(patientId);
      setCaseDetail((prev) => ({ ...prev, status: "in_review" }));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleDecision = async (decision: "enrol" | "decline" | "defer") => {
    setError(null);
    try {
      await submitDecision(patientId, decision, notes || undefined);
      await refreshCase();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const brief = extractBrief(events);

  return (
    <div>
      <h1 className="text-xl font-bold">Case {patientId.slice(0, 8)}…</h1>
      <dl className="mt-4 grid grid-cols-2 gap-2 text-sm">
        <dt className="text-neutral-500">Risk score</dt>
        <dd>{caseDetail.risk_score.toFixed(3)}</dd>
        <dt className="text-neutral-500">Risk tier</dt>
        <dd>{caseDetail.risk_tier}</dd>
        <dt className="text-neutral-500">Status</dt>
        <dd>{caseDetail.status}</dd>
      </dl>

      {error && (
        <p className="mt-4 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
          {error}
          {error.includes("500") && (
            <span className="mt-1 block text-xs">
              This is expected without an OpenAI API key configured — see README.
            </span>
          )}
        </p>
      )}

      {caseDetail.status === "pending" && (
        <button
          onClick={handleStart}
          className="mt-6 rounded-lg bg-neutral-900 px-4 py-2 text-sm text-white dark:bg-neutral-100 dark:text-neutral-900"
        >
          Start review
        </button>
      )}

      {events.length > 0 && (
        <div className="mt-6">
          <h2 className="font-semibold">Trace</h2>
          <ol className="mt-2 space-y-1 text-sm">
            {events.map((event, i) => (
              <li key={i} className="font-mono text-xs text-neutral-500">
                {event.node}
              </li>
            ))}
          </ol>
        </div>
      )}

      {brief && (
        <div className="mt-6 rounded-lg border border-neutral-200 p-4 dark:border-neutral-800">
          <h2 className="font-semibold">Case brief</h2>
          <p className="mt-2 text-sm">{brief.narrative}</p>
          {brief.drivers.length > 0 && (
            <>
              <h3 className="mt-3 text-sm font-medium">Drivers</h3>
              <ul className="mt-1 text-sm text-neutral-600 dark:text-neutral-400">
                {brief.drivers.map((d) => (
                  <li key={d.feature_name}>
                    {d.feature_name}: {d.direction} ({d.contribution.toFixed(3)})
                  </li>
                ))}
              </ul>
            </>
          )}
          <h3 className="mt-3 text-sm font-medium">What would change this</h3>
          <p className="mt-1 text-sm text-neutral-600 dark:text-neutral-400">
            {brief.what_would_change_this}
          </p>
          <p className="mt-3 text-xs text-neutral-400">
            Note: no risk tier or enrolment recommendation appears above —
            the schema has no field for one. See D-A12-1.
          </p>
        </div>
      )}

      {caseDetail.status === "awaiting_decision" && (
        <div className="mt-6">
          <h2 className="font-semibold">Clinician decision</h2>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Optional notes"
            className="mt-2 w-full rounded-lg border border-neutral-200 p-2 text-sm dark:border-neutral-800 dark:bg-neutral-900"
            rows={2}
          />
          <div className="mt-2 flex gap-2">
            <button
              onClick={() => handleDecision("enrol")}
              className="rounded-lg bg-green-700 px-3 py-1.5 text-sm text-white"
            >
              Enrol
            </button>
            <button
              onClick={() => handleDecision("decline")}
              className="rounded-lg bg-neutral-700 px-3 py-1.5 text-sm text-white"
            >
              Decline
            </button>
            <button
              onClick={() => handleDecision("defer")}
              className="rounded-lg bg-amber-700 px-3 py-1.5 text-sm text-white"
            >
              Defer
            </button>
          </div>
        </div>
      )}

      {caseDetail.status === "decided" && (
        <div className="mt-6 rounded-lg border border-neutral-200 p-4 dark:border-neutral-800">
          <h2 className="font-semibold">Decision recorded</h2>
          <p className="mt-1 text-sm">
            {caseDetail.decision} — {caseDetail.override_notes ?? "no notes"}
          </p>
        </div>
      )}
    </div>
  );
}
