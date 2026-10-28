"use client";

import {
  Bot,
  Check,
  CircleCheckBig,
  ClipboardList,
  FileText,
  ListChecks,
  LoaderCircle,
  Play,
  Search,
  TriangleAlert,
  UserCheck,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { StatusBadge, TierBadge } from "@/components/ui/Badge";
import { Callout } from "@/components/ui/Callout";
import { Card, CardTitle } from "@/components/ui/Card";
import { InfoTip } from "@/components/ui/InfoTip";
import { RiskBar } from "@/components/ui/RiskBar";
import { getCase, reviewEventsUrl, startReview, submitDecision } from "@/lib/api";
import { docsLink } from "@/lib/docs";
import { GLOSSARY } from "@/lib/glossary";
import type { CaseBrief, CaseDetail, Driver, ReviewEventPayload } from "@/lib/types";

const ACTIVE_STATUSES = new Set(["in_review"]);
// Statuses whose stored trace is replayed on load, so the brief survives a page refresh.
const REPLAY_STATUSES = new Set(["in_review", "awaiting_decision", "deciding", "decided"]);

const STEP_LABELS: Record<string, string> = {
  load_case: "Scoring the patient with the risk model",
  assemble_evidence: "Agent is deciding what evidence to gather",
  tools: "Fetching patient encounters, labs and care gaps",
  draft_brief: "Drafting the case brief",
  verify_brief: "Checking the brief against the evidence",
  await_decision: "Ready for the clinician",
  record_decision: "Recording the clinician's decision",
};

const STAGES = [
  { key: "pending", label: "Flagged by model", icon: ClipboardList },
  { key: "in_review", label: "AI gathers evidence", icon: Bot },
  { key: "awaiting_decision", label: "Clinician reviews", icon: FileText },
  { key: "decided", label: "Decision recorded", icon: UserCheck },
] as const;

const STAGE_INDEX: Record<string, number> = {
  pending: 0,
  in_review: 1,
  awaiting_decision: 2,
  deciding: 3,
  decided: 3,
};

const DECISIONS = [
  {
    value: "enrol",
    label: "Enrol",
    hint: "Offer this patient the care-management programme.",
    className: "bg-teal-600 hover:bg-teal-700 text-white",
  },
  {
    value: "decline",
    label: "Decline",
    hint: "Not a fit for the programme right now.",
    className: "bg-slate-700 hover:bg-slate-800 text-white dark:bg-slate-600 dark:hover:bg-slate-500",
  },
  {
    value: "defer",
    label: "Defer",
    hint: "Need more information before deciding.",
    className: "bg-amber-500 hover:bg-amber-600 text-white",
  },
] as const;

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

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

function humanise(feature: string): string {
  const words = feature.toLowerCase().replace(/_/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function StatusStepper({ status }: { status: string }) {
  const current = STAGE_INDEX[status] ?? 0;
  const inProgress = status === "in_review" || status === "deciding";
  return (
    <ol className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {STAGES.map((stage, i) => {
        const done = i < current || (i === current && status === "decided");
        const active = i === current && !done;
        const Icon = stage.icon;
        return (
          <li
            key={stage.key}
            className={`flex items-center gap-3 rounded-lg border px-3 py-2.5 text-sm ${
              active
                ? "border-teal-500 bg-teal-50 text-teal-900 dark:border-teal-500 dark:bg-teal-950 dark:text-teal-100"
                : done
                  ? "border-slate-200 bg-white text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
                  : "border-dashed border-slate-300 text-slate-400 dark:border-slate-700 dark:text-slate-500"
            }`}
          >
            <span
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
                done
                  ? "bg-teal-600 text-white"
                  : active
                    ? "bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-200"
                    : "bg-slate-100 dark:bg-slate-800"
              }`}
            >
              {done ? (
                <Check className="h-4 w-4" aria-hidden />
              ) : active && inProgress ? (
                <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden />
              ) : (
                <Icon className="h-4 w-4" aria-hidden />
              )}
            </span>
            <span className="font-medium leading-tight">{stage.label}</span>
          </li>
        );
      })}
    </ol>
  );
}

function DriverBars({ drivers }: { drivers: Driver[] }) {
  const max = Math.max(...drivers.map((d) => Math.abs(d.contribution)), 1e-9);
  return (
    <ul className="mt-3 space-y-2">
      {drivers.map((d) => {
        const width = (Math.abs(d.contribution) / max) * 50;
        const up = d.direction === "increases_risk";
        return (
          <li key={d.feature_name} className="grid grid-cols-[minmax(0,13rem)_1fr_3.5rem] items-center gap-3 text-sm">
            <span className="leading-snug text-slate-700 dark:text-slate-300" title={d.feature_name}>
              {humanise(d.feature_name)}
            </span>
            <div className="relative h-3 rounded bg-slate-100 dark:bg-slate-800">
              <span className="absolute inset-y-0 left-1/2 w-px bg-slate-300 dark:bg-slate-600" />
              <span
                className={`absolute inset-y-0 rounded ${up ? "left-1/2 bg-red-500" : "right-1/2 bg-teal-500"}`}
                style={{ width: `${width}%` }}
              />
            </div>
            <span className={`text-right tabular-nums text-xs ${up ? "text-red-600 dark:text-red-400" : "text-teal-700 dark:text-teal-400"}`}>
              {d.contribution > 0 ? "+" : ""}
              {d.contribution.toFixed(3)}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

function BulletList({ items, empty }: { items: string[]; empty: string }) {
  if (items.length === 0) return <p className="mt-2 text-sm text-slate-400">{empty}</p>;
  return (
    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700 dark:text-slate-300">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
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
  const [starting, setStarting] = useState(false);
  const [deciding, setDeciding] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const eventSourceRef = useRef<EventSource | null>(null);

  const refreshCase = useCallback(async () => {
    try {
      setCaseDetail(await getCase(patientId));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [patientId]);

  // The stream replays every stored event and then, for a finished case,
  // closes — so connecting on load also restores the trace and brief.
  useEffect(() => {
    if (!REPLAY_STATUSES.has(caseDetail.status)) return undefined;

    setEvents([]);
    const source = new EventSource(reviewEventsUrl(patientId));
    eventSourceRef.current = source;
    source.onmessage = (message) => {
      const payload = JSON.parse(message.data) as ReviewEventPayload;
      if (payload.node === "__end__") {
        source.close();
        if (ACTIVE_STATUSES.has(caseDetail.status)) void refreshCase();
        return;
      }
      setEvents((prev) => [...prev, payload]);
    };
    source.onerror = () => {
      source.close();
    };
    return () => source.close();
  }, [caseDetail.status, patientId, refreshCase]);

  // The event stream can drop silently; polling guarantees the page never
  // stays stuck on "in_review". A reset to "pending" means the run failed.
  useEffect(() => {
    if (!ACTIVE_STATUSES.has(caseDetail.status)) return undefined;
    const timer = setInterval(async () => {
      try {
        const latest = await getCase(patientId);
        if (latest.status === "in_review") return;
        setCaseDetail(latest);
        if (latest.status === "pending") {
          setError("The review failed on the server. Check the API log, then start it again.");
        }
      } catch {
        // transient; the next tick retries
      }
    }, 3000);
    return () => clearInterval(timer);
  }, [caseDetail.status, patientId]);

  const busy = ACTIVE_STATUSES.has(caseDetail.status) || deciding !== null;
  useEffect(() => {
    if (!busy) return undefined;
    setElapsed(0);
    const timer = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, [busy]);

  const handleStart = async () => {
    setError(null);
    setStarting(true);
    setEvents([]);
    try {
      await startReview(patientId);
      setCaseDetail((prev) => ({ ...prev, status: "in_review" }));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setStarting(false);
    }
  };

  // The API resumes the graph in the background, so the decision is only
  // "recorded" once the case flips to `decided`; poll until it does.
  const handleDecision = async (decision: "enrol" | "decline" | "defer") => {
    setError(null);
    setDeciding(decision);
    try {
      await submitDecision(patientId, decision, notes || undefined);
      for (let attempt = 0; attempt < 40; attempt += 1) {
        const latest = await getCase(patientId);
        if (latest.status === "decided") {
          setCaseDetail(latest);
          return;
        }
        await sleep(1500);
      }
      setError("The decision was accepted but not recorded after 60s. Check the API log.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setDeciding(null);
    }
  };

  const running = caseDetail.status === "in_review";
  const brief = extractBrief(events);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-teal-700 dark:text-teal-400">
            Case review
          </p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl dark:text-white">
            Patient <span className="font-mono">{patientId.slice(0, 8)}</span>
          </h1>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <TierBadge tier={caseDetail.risk_tier} />
            <StatusBadge status={caseDetail.status} />
          </div>
        </div>
        <Card className="w-full lg:w-80">
          <p className="flex items-center text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Model risk score
            <InfoTip text={GLOSSARY.riskScore} />
          </p>
          <div className="mt-2">
            <RiskBar score={caseDetail.risk_score} size="lg" />
          </div>
          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
            ≈ {Math.round(caseDetail.risk_score * 100)}% estimated chance of high illness burden in
            the next 6 months.
          </p>
        </Card>
      </div>

      <StatusStepper status={caseDetail.status} />

      {caseDetail.status === "pending" && (
        <Card>
          <h2 className="font-semibold text-slate-900 dark:text-white">What happens when you start a review</h2>
          <ul className="mt-3 space-y-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
            <li className="flex gap-2">
              <Check className="mt-0.5 h-4 w-4 shrink-0 text-teal-600" aria-hidden />
              <span>The risk score above is already fixed — it came from the statistical model.</span>
            </li>
            <li className="flex gap-2">
              <Check className="mt-0.5 h-4 w-4 shrink-0 text-teal-600" aria-hidden />
              <span>
                An AI agent looks up this patient&apos;s encounters, labs and care gaps and drafts a
                short case brief. You can watch each step live (usually 20–60 seconds).
              </span>
            </li>
            <li className="flex gap-2">
              <Check className="mt-0.5 h-4 w-4 shrink-0 text-teal-600" aria-hidden />
              <span>
                The agent cannot change the score or recommend enrolment —{" "}
                <a className="font-medium text-teal-700 underline dark:text-teal-400" href={docsLink("llmIsNotTheRiskModel")} target="_blank" rel="noreferrer">
                  by design
                </a>
                . You make the decision.
              </span>
            </li>
          </ul>
          <button
            onClick={handleStart}
            disabled={starting}
            className="mt-5 inline-flex items-center gap-2 rounded-lg bg-teal-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-teal-700 disabled:opacity-50"
          >
            {starting ? (
              <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden />
            ) : (
              <Play className="h-4 w-4" aria-hidden />
            )}
            {starting ? "Starting…" : "Start AI review"}
          </button>
        </Card>
      )}

      {error && (
        <Callout variant="error" title="Something went wrong">
          {error}
          {error.includes("500") && (
            <span className="mt-1 block text-xs opacity-80">
              This is expected without an OpenAI API key configured — see the{" "}
              <a className="underline" href={docsLink("runItYourself")} target="_blank" rel="noreferrer">
                setup guide
              </a>
              .
            </span>
          )}
        </Callout>
      )}

      {(running || events.length > 0) && (
        <Card>
          <CardTitle icon={<Search className="h-4 w-4" aria-hidden />}>What the AI agent did</CardTitle>
          {running && (
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              Working… {elapsed}s (a review usually takes 20–60s)
            </p>
          )}
          <ol className="relative mt-4 space-y-3 border-l-2 border-slate-200 pl-6 dark:border-slate-700">
            {events.map((event, i) => (
              <li key={i} className="relative">
                <span className="absolute -left-[31px] top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-teal-600 text-white">
                  <Check className="h-2.5 w-2.5" aria-hidden />
                </span>
                <p className="text-sm text-slate-800 dark:text-slate-200">{STEP_LABELS[event.node] ?? event.node}</p>
                <p className="font-mono text-[11px] text-slate-400">{event.node}</p>
              </li>
            ))}
            {running && (
              <li className="relative">
                <span className="absolute -left-[31px] top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-white ring-2 ring-teal-500 dark:bg-slate-900">
                  <LoaderCircle className="h-3 w-3 animate-spin text-teal-600" aria-hidden />
                </span>
                <p className="text-sm text-slate-500">Next step in progress…</p>
              </li>
            )}
          </ol>
        </Card>
      )}

      {brief && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="lg:col-span-2">
            <CardTitle icon={<FileText className="h-4 w-4" aria-hidden />}>Case brief</CardTitle>
            <p className="mt-3 leading-relaxed text-slate-800 dark:text-slate-200">{brief.narrative}</p>
            <p className="mt-4 text-xs text-slate-400">
              Drafted by the AI agent and checked against the evidence it gathered. It deliberately
              contains no risk tier or enrolment recommendation — the schema has no field for one.
            </p>
          </Card>

          {brief.drivers.length > 0 && (
            <Card>
              <CardTitle>
                Why the model scored this patient high
                <InfoTip text={GLOSSARY.drivers} />
              </CardTitle>
              <DriverBars drivers={brief.drivers} />
              <div className="mt-3 flex gap-4 text-xs text-slate-500">
                <span className="flex items-center gap-1"><span className="h-2 w-3 rounded bg-red-500" /> increases risk</span>
                <span className="flex items-center gap-1"><span className="h-2 w-3 rounded bg-teal-500" /> decreases risk</span>
              </div>
            </Card>
          )}

          <Card>
            <CardTitle icon={<ListChecks className="h-4 w-4" aria-hidden />}>Supporting evidence</CardTitle>
            {brief.corroborating_evidence.length === 0 ? (
              <p className="mt-2 text-sm text-slate-400">None recorded.</p>
            ) : (
              <ul className="mt-3 space-y-2">
                {brief.corroborating_evidence.map((e, i) => (
                  <li key={i} className="flex gap-2 text-sm text-slate-700 dark:text-slate-300">
                    <span className="mt-0.5 shrink-0 rounded bg-indigo-50 px-1.5 py-0.5 text-[11px] font-medium uppercase text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                      {e.source}
                    </span>
                    {e.description}
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card>
            <CardTitle icon={<ClipboardList className="h-4 w-4" aria-hidden />}>Care gaps</CardTitle>
            <BulletList items={brief.care_gaps} empty="No care gaps found." />
          </Card>

          <Card>
            <CardTitle icon={<TriangleAlert className="h-4 w-4" aria-hidden />}>Missing data</CardTitle>
            <BulletList items={brief.missing_data} empty="Nothing flagged as missing." />
          </Card>

          <Card className="lg:col-span-2">
            <CardTitle>What would change this assessment</CardTitle>
            <p className="mt-2 text-sm leading-relaxed text-slate-700 dark:text-slate-300">{brief.what_would_change_this}</p>
          </Card>
        </div>
      )}

      {caseDetail.status === "awaiting_decision" && (
        <Card tone="teal">
          <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
            <UserCheck className="h-5 w-5 text-teal-600" aria-hidden />
            Your decision
          </h2>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            You are the clinician. Read the brief above, then choose. Nothing happens to the
            patient until you do.
          </p>
          <label className="mt-4 block text-sm font-medium text-slate-700 dark:text-slate-300" htmlFor="decision-notes">
            Notes (optional)
          </label>
          <textarea
            id="decision-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. Discussed with care coordinator; patient prefers phone contact."
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white p-2.5 text-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/30 dark:border-slate-700 dark:bg-slate-950"
            rows={2}
          />
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {DECISIONS.map((d) => (
              <button
                key={d.value}
                onClick={() => handleDecision(d.value)}
                disabled={deciding !== null}
                className={`rounded-lg px-4 py-3 text-left shadow-sm transition disabled:opacity-50 ${d.className}`}
              >
                <span className="flex items-center gap-2 font-semibold">
                  {deciding === d.value && <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden />}
                  {d.label}
                </span>
                <span className="mt-0.5 block text-xs opacity-90">{d.hint}</span>
              </button>
            ))}
          </div>
          {deciding && (
            <p className="mt-3 text-sm text-slate-500">
              Recording “{deciding}”… ({elapsed}s)
            </p>
          )}
        </Card>
      )}

      {caseDetail.status === "deciding" && deciding === null && (
        <Callout title="A decision is being recorded">Refresh in a few seconds.</Callout>
      )}

      {caseDetail.status === "decided" && (
        <Card tone="emerald">
          <h2 className="flex items-center gap-2 font-semibold text-emerald-900 dark:text-emerald-100">
            <CircleCheckBig className="h-5 w-5" aria-hidden />
            Decision recorded: <span className="capitalize">{caseDetail.decision}</span>
          </h2>
          <p className="mt-2 text-sm text-emerald-900/80 dark:text-emerald-200/80">
            {caseDetail.override_notes ?? "No notes."}
          </p>
          {caseDetail.decided_at && (
            <p className="mt-2 text-xs text-emerald-800/70 dark:text-emerald-300/70">
              {caseDetail.decided_at.slice(0, 16).replace("T", " ")} UTC
            </p>
          )}
        </Card>
      )}
    </div>
  );
}
