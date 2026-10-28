# Project enhancement guide: deployment-readiness and "explain it to a stranger" UI

A reusable playbook distilled from the Cohort Risk & Review Lab work. Use it on
another project (FastAPI + Next.js + Tailwind here, but the ideas are stack-agnostic)
to (1) find what blocks deployment and (2) make the UI understandable to someone who
has never seen the project, and visually polished.

---

## 0. How to run this as an agent-assisted workflow

The order that worked well:

1. **Reproduce a real failure first.** Paste the actual log or error. Diagnose from
   evidence (check the data, the code path, timestamps), not guesses.
2. **Ask for a readiness review.** Run lint, types, tests, then read the Docker/compose
   files and the API surface. Report findings ranked by severity.
3. **Plan before building.** Ask for a plan, answer the clarifying questions (style,
   auth approach, depth of explanation, icon dependency), then approve.
4. **Implement in small verified slices.** After each slice run the full checks.
5. **Verify visually.** Run the real backend and frontend, screenshot every page and
   state (light and dark), and fix what looks off.
6. **Update docs and the docs screenshot** so they match the app.

Prompts that worked (adapt the nouns):

```text
Why is `make run` failing on this: <paste log>
```
```text
Do you think this project is ready for deployment?
```
```text
Plan for these fixes: <list>. Ask me about anything ambiguous.
```
```text
Someone who doesn't know the project would understand nothing from the UI. It should
explain what is happening, and it looks pale and plain. Improve it, and link the docs.
```

---

## Part A: Deployment-readiness review

### A1. Checklist to audit

| Area | What to check |
|---|---|
| Quality gates | Lint, format, type check, import/layer contracts, full test suite |
| Container | Lockfile install, non-root user, healthcheck, `.dockerignore` excludes data/secrets, no secrets baked in |
| Network | No host ports published in prod; reverse proxy is the only entry; proxy **overwrites** `X-Forwarded-For` |
| Auth | Who can call write endpoints? At minimum put basic auth at the proxy |
| Config | Production `.env` values (CORS origins, public API URL, API keys, log format) |
| Data | How do generated data/model artifacts reach the server? Is derived state (queues, caches) rebuilt from them? |
| Concurrency | Can a double click or two clients start the same job twice? |
| Failure visibility | Do background-task failures reach the user, or only the server log? |
| Repo hygiene | Uncommitted changes, `.gitignore` covers data/secrets |

### A2. Findings from the original project and the fix pattern used

1. **Stale derived state.** A queue table kept rows from an earlier data generation
   (`INSERT OR IGNORE`, never cleared), so starting a review crashed on patients that
   no longer existed. It was also slow because it committed per row.
   - Fix: a destructive, documented rebuild step: clear tables, then insert everything
     in **one transaction** with `executemany`. Also clear any resumable-job state
     (LangGraph checkpoints) keyed by the same ids.
   - Result: minutes down to about 13 s, most of which was building the feature table.

2. **Fail early with a clear message.** The route returned 202 and the error happened
   later in a background task the client never sees.
   - Fix: validate cheaply in the route (is the id in the cached set of valid ids?) and
     return 404 with an actionable `detail`. Surface `detail` in the frontend's errors.

3. **Check-then-set races.** Two quick requests both passed `status == "pending"`.
   - Fix: an atomic claim, one conditional UPDATE, success = `rowcount == 1`:

   ```python
   def claim(self, id: str, from_status: str, to_status: str) -> bool:
       with self._conn:
           cur = self._conn.execute(
               "UPDATE cases SET status = ?, updated_at = ? WHERE id = ? AND status = ?",
               (to_status, _now(), id, from_status),
           )
       return cur.rowcount == 1
   ```
   Route: `if not store.claim(id, "pending", "in_review"): raise HTTPException(409, ...)`.
   Add an intermediate status (`deciding`) and **roll it back on failure** so users can retry.

4. **Auth.** Decide explicitly. For a public demo with no user accounts, basic auth at
   the reverse proxy covers both the site and the browser's direct API calls. Do not put
   an API key in browser code; it protects nothing. Document Caddy and nginx examples.

5. **Proxy header trust.** If the app trusts `X-Forwarded-For` from any peer, the proxy
   must replace the header, otherwise clients can spoof their IP and dodge rate limits.

### A3. Verification for Part A

- Unit tests for each new store method (bulk insert, reset, claim true/false).
- Route tests: stale id gives 404 and status unchanged; second start gives 409.
- Live check against a **throwaway database** (env vars to point the app at temp
  files): fire two parallel POSTs and confirm exactly one 202 and one 409.
- Time the slow script before and after.

---

## Part B: UI that explains itself, and looks good

### B1. Principles

1. **Every page answers three questions:** what am I looking at, why does it matter,
   what can I do next. Put the answer in a plain-language intro under the title.
2. **Jargon gets a tooltip, not a paragraph.** Keep explanations one or two sentences.
3. **Say who owns each decision** (model, AI, human). It is the single most
   clarifying thing for AI-assisted workflows.
4. **Show state visually:** a status stepper, coloured badges, meters, timelines.
   Raw status strings and node names are secondary (small monospace beneath).
5. **Surface data you already have.** The API sent evidence, care gaps and missing
   data that the old page never rendered. Check the response schema against the UI.
6. **One source of truth for wording and links** (glossary file, docs-link helper).
7. **Do not state facts the data can't back up.** A hard-coded "largest gap of any
   group" was wrong for the current data; compute the claim or drop it.
8. **Light and dark mode both work** (`prefers-color-scheme`, `dark:` variants).

### B2. Design foundation (Tailwind v4)

- Page background soft slate (`#f5f7fa`), cards white with `border-slate-200` and
  `shadow-sm`, accent teal-600/700, secondary indigo, status colours red/amber/emerald.
- Dark: background `#0b1120`, cards `slate-900`, borders `slate-800`.
- Remove any global `font-family` override (the template's `Arial` was defeating the
  loaded font). Let `font-sans` use the font variable.
- Add one icon library (here `lucide-react`). Verify icon names exist in the installed
  version before using them: names change between versions (e.g. no `Github` icon).

### B3. Shared components (put in `src/components/ui/`)

| Component | Purpose |
|---|---|
| `AppHeader` | Sticky bar: name, nav with active state (`usePathname`), external **Docs** button |
| `AppFooter` | Disclaimer plus Docs / policy / source links |
| `PageHeader` | Icon, eyebrow ("Step 2 · Fairness"), title, plain-language intro, "Learn more in the docs →" |
| `Card` (`tone`, `padded`) | Surface; tones for default/teal/red/emerald; `padded={false}` for tables |
| `Badge`, `StatusBadge`, `TierBadge` | Map raw values to labels and colours in one place |
| `Callout` (`info`/`warning`/`error`) | Notices, disclosures, empty and error states |
| `InfoTip` | Accessible ⓘ tooltip |
| `RiskBar` / meter | Number plus bar, `role="meter"` with aria values |

`InfoTip` is CSS-only (works in server components, hover and keyboard focus):

```tsx
<span className="group relative inline-flex align-middle">
  <button type="button" aria-label={`${label} ${text}`} className="ml-1 ...">
    <Info className="h-3.5 w-3.5" aria-hidden />
  </button>
  <span role="tooltip"
    className="pointer-events-none invisible absolute bottom-full left-1/2 z-20 mb-2 w-64
               -translate-x-1/2 rounded-lg bg-slate-900 px-3 py-2 text-xs opacity-0
               group-hover:visible group-hover:opacity-100
               group-focus-within:visible group-focus-within:opacity-100">
    {text}
  </span>
</span>
```

Docs links in one place (`lib/docs.ts`), overridable at build time:

```ts
export const DOCS_URL = (process.env.NEXT_PUBLIC_DOCS_URL ?? "https://your.site/docs/")
  .replace(/\/?$/, "/");
export const DOC_PAGES = { plainLanguage: "how-it-works/in-plain-language/", /* ... */ } as const;
export const docsLink = (page: keyof typeof DOC_PAGES) => `${DOCS_URL}${DOC_PAGES[page]}`;
```

`NEXT_PUBLIC_*` values are inlined at **build time**: add `ARG`/`ENV` to the frontend
Dockerfile and pass it as a compose build arg, or the override silently does nothing.

Glossary in one file (`lib/glossary.ts`): a `const GLOSSARY = { term: "plain sentence" }`
used by every `InfoTip`, so a term is explained identically everywhere.

### B4. Page recipes

- **Homepage:** hero (one-sentence purpose, two buttons), a numbered **"How it works"**
  strip (3 to 4 steps with icons and an owner for each), feature cards that link to
  pages, a docs call-to-action. Remove stale "Phase N" footers.
- **List/queue page:** intro explaining why items are here and who decided; a count card;
  table with meter, badges, header `InfoTip`s; whole row clickable (stretch the link
  with `after:absolute after:inset-0`); empty and error states as `Callout`s.
- **Detail/workflow page:**
  - header with id, badges, key number as a big meter;
  - **status stepper** (pending → working → needs human → done);
  - a "what happens when you start" box *before* the action button;
  - live progress as a **vertical timeline** with human labels and the raw node name
    beneath;
  - results in cards (narrative, driver bars with +/− colours, evidence, gaps, missing
    data, "what would change this");
  - a clear decision panel: each button gets a one-line consequence; final state is a
    summary card with a deterministic timestamp.
- **Evidence/analytics pages:** plain-language intro, a "key finding" stat card above
  the chart, a themed chart (highlight one series, neutral grey for the rest), an
  explicit **disclosure callout** for any synthetic or injected data, and docs links
  for the design decisions.
- **Tables with uncertainty:** draw CI as a shaded range with a tick for the estimate,
  and use a badge instead of a number where the sample is too small.

### B5. Gotchas that actually happened

- `.toLocaleString()` on a server-rendered date risks a hydration mismatch: format
  deterministically (e.g. `iso.slice(0,16).replace("T"," ") + " UTC"`).
- A flex row with mixed text and an inline link adds odd gaps: wrap the text in a
  single `<span>`.
- State that lived only in the SSE stream disappeared on refresh: replay stored events
  for finished states too (connect on load for every non-pending status).
- With a header added, a nav label can match two links; scope e2e selectors to
  `getByRole("navigation", { name: "Main" })`.
- Layout with `sticky` header and full-page screenshots shows the header mid-page;
  harmless, but screenshot viewport sections when judging layout.
- Generated files (`.venv`, data, `node_modules`) and files blocked by content policy
  can't be inspected; ask the user rather than working around it.

### B6. Verification for Part B

1. `npx tsc --noEmit` and `npm run build`.
2. Update the e2e smoke test for the new structure, then run Playwright.
3. Start the real API and `next dev`; use a Playwright script to screenshot **every**
   page and state: home, list, detail (pending, running, awaiting decision, decided),
   evidence pages, in light **and** dark. Check the browser console for errors.
4. Run one real end-to-end workflow, then reload the page and confirm the results
   persist.
5. Regenerate the docs screenshot from a production build.
6. Update the run/deploy docs (new env vars, proxy auth, rebuild steps).

---

## Part C: Copy-paste checklist for the next project

- [ ] Reproduce and diagnose any current failure from logs
- [ ] Run lint, types, tests; read Docker/compose; list API write endpoints
- [ ] Fix stale derived state; batch inserts; atomic claims; early validation errors
- [ ] Decide auth (proxy basic auth is the cheap default) and document proxy headers
- [ ] Theme tokens, icon library, remove font override
- [ ] `ui/` primitives: header, footer, page header, card, badge, callout, info tip, meter
- [ ] `lib/docs.ts` and `lib/glossary.ts`; pass docs URL through Docker build
- [ ] Homepage "How it works" strip; per-page plain-language intros; tooltips on jargon
- [ ] Render every field the API returns; status stepper; progress timeline
- [ ] Disclosure callouts for synthetic or injected data; no hard-coded claims
- [ ] Light and dark verified with screenshots; zero console errors
- [ ] e2e test updated; docs and docs screenshot updated
