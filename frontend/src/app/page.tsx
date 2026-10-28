import {
  Activity,
  ArrowRight,
  BookOpen,
  Bot,
  ChartBar,
  ClipboardList,
  Scale,
  ShieldCheck,
  UserCheck,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import Link from "next/link";

import { DOCS_URL, docsLink } from "@/lib/docs";

const STEPS: { icon: LucideIcon; title: string; body: string; href: string }[] = [
  {
    icon: Activity,
    title: "A statistical model scores every patient",
    body: "A calibrated machine-learning model — not a chatbot — estimates each patient's chance of a high illness burden over the next six months. It never sees race.",
    href: "/queue",
  },
  {
    icon: ShieldCheck,
    title: "Fairness is checked per group",
    body: "Accuracy is reported separately for every age, sex, race and insurance group, with uncertainty ranges — so a model that fails one group can't hide behind a good average.",
    href: "/evidence/fairness",
  },
  {
    icon: Bot,
    title: "An AI agent gathers the evidence",
    body: "For each flagged patient, an AI assistant pulls encounters, labs and care gaps into a short case brief. It cannot change the score or recommend enrolment.",
    href: "/queue",
  },
  {
    icon: UserCheck,
    title: "A clinician decides",
    body: "A person reads the brief and chooses to enrol, decline or defer. Nothing happens to a patient without that decision.",
    href: "/queue",
  },
];

const FEATURES: { icon: LucideIcon; title: string; body: string; href: string; cta: string }[] = [
  {
    icon: ClipboardList,
    title: "Review queue",
    body: "Patients the model flagged for possible care-management enrolment, highest risk first. Open one to watch the AI agent build its case brief live, then record a decision.",
    href: "/queue",
    cta: "Open the queue",
  },
  {
    icon: Scale,
    title: "Subgroup fairness audit",
    body: "How well the model works for each demographic group, with 95% confidence intervals — and an honest \u201cnot enough data\u201d where groups are too small.",
    href: "/evidence/fairness",
    cta: "See the audit",
  },
  {
    icon: ChartBar,
    title: "The label-choice experiment",
    body: "Two identical models, one trained to predict illness and one to predict cost. Watch the cost model quietly select fewer Black patients — reproducing Obermeyer et al. (2019).",
    href: "/evidence/label-choice",
    cta: "See the experiment",
  },
];

export default function Home() {
  return (
    <main>
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-teal-700 via-teal-600 to-indigo-700 px-6 py-10 text-white shadow-lg sm:px-10 sm:py-14">
        <p className="text-xs font-semibold uppercase tracking-widest text-teal-100">
          Clinical decision support · demonstration
        </p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">Cohort Risk &amp; Review Lab</h1>
        <p className="mt-4 max-w-2xl text-base leading-relaxed text-teal-50 sm:text-lg">
          Which patients should a care-management team call first? This app shows a responsible
          way to answer that: <strong>the model decides who is flagged, an AI agent explains
          why, and a human makes the call</strong> — with fairness measured for every group, not
          just on average.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/queue"
            className="inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-semibold text-teal-800 shadow hover:bg-teal-50"
          >
            Try a case review <ArrowRight className="h-4 w-4" aria-hidden />
          </Link>
          <a
            href={docsLink("plainLanguage")}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-lg border border-white/40 px-4 py-2 text-sm font-semibold text-white hover:bg-white/10"
          >
            <BookOpen className="h-4 w-4" aria-hidden /> How it works, in plain language
          </a>
        </div>
      </section>

      <section className="mt-12">
        <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">How it works</h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          Four steps, each with a clear owner. The AI assistant only ever does step 3.
        </p>
        <ol className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, i) => (
            <li key={step.title}>
              <Link
                href={step.href}
                className="group flex h-full flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-teal-400 hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:hover:border-teal-600"
              >
                <div className="flex items-center gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-teal-600 text-sm font-bold text-white">
                    {i + 1}
                  </span>
                  <step.icon className="h-5 w-5 text-teal-600 dark:text-teal-400" aria-hidden />
                </div>
                <h3 className="mt-4 font-semibold text-slate-900 dark:text-white">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400">{step.body}</p>
              </Link>
            </li>
          ))}
        </ol>
      </section>

      <section className="mt-12">
        <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">Explore</h2>
        <nav className="mt-6 grid gap-4 md:grid-cols-3">
          {FEATURES.map((f) => (
            <Link
              key={f.href}
              href={f.href}
              className="group flex flex-col rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-teal-400 hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:hover:border-teal-600"
            >
              <span className="w-fit rounded-lg bg-teal-50 p-2.5 text-teal-700 dark:bg-teal-950 dark:text-teal-300">
                <f.icon className="h-5 w-5" aria-hidden />
              </span>
              <div className="mt-4 font-semibold text-slate-900 dark:text-white">{f.title}</div>
              <div className="mt-2 flex-1 text-sm leading-relaxed text-slate-600 dark:text-slate-400">{f.body}</div>
              <div className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-teal-700 group-hover:gap-2 dark:text-teal-400">
                {f.cta} <ArrowRight className="h-4 w-4 transition-all" aria-hidden />
              </div>
            </Link>
          ))}
        </nav>
      </section>

      <section className="mt-12 flex flex-col items-start gap-4 rounded-xl border border-indigo-200 bg-indigo-50 p-6 sm:flex-row sm:items-center sm:justify-between dark:border-indigo-900 dark:bg-indigo-950/50">
        <div>
          <h2 className="font-semibold text-indigo-950 dark:text-indigo-100">Want the full story?</h2>
          <p className="mt-1 text-sm text-indigo-900/80 dark:text-indigo-200/80">
            The documentation covers the architecture, every design decision, the evidence behind
            each claim, and how to run it yourself.
          </p>
        </div>
        <a
          href={DOCS_URL}
          target="_blank"
          rel="noreferrer"
          className="inline-flex shrink-0 items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          <BookOpen className="h-4 w-4" aria-hidden /> Read the docs
        </a>
      </section>
    </main>
  );
}
