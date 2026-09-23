# AGENTS.md — Career Quest (HackAlem AI · Halyk Bank · Case 1)

Three coding agents build this repo, each driven by a different teammate (A, B, C).
Agents coordinate through THIS file, the API contract in §7, and directory ownership in §3.
Read the whole file before every task. If something here conflicts with a prompt, this file wins; say so in your final message.

## 1. What we build and how it is judged

A web app with an AI layer that, for one employee:
1. shows profile + career trajectory (role, grade, skills, completed activities, available next steps);
2. recommends 1–3 next development activities with a rationale built on ≥3 factors (grade, skill gaps, participation history, next-level requirements);
3. updates skill progress and trajectory when an activity is marked completed;
4. gives HR a view of lagging skills, employees with no recommended step, and participation by activity.

- The core is recommendation QUALITY and EXPLAINABILITY, not UI chrome. Gamification is optional.
- The jury uploads 3 extra test profiles (same file format) built so that single-factor rules ("pick the lowest skill") fail. Every rule in §4 exists to survive them.
- Limits: UI responses < 2 s. AI recommendation < 10 s (target p95 < 6 s). Start with ONE command.

## 2. Stack (do not change without team agreement)

- `backend/`: Python 3.11, FastAPI, Pydantic v2, uvicorn, `openai` SDK (any OpenAI-compatible endpoint), pytest.
  In-memory store loaded from `data/`; runtime writes go to `data/runtime/` (git-ignored).
- `frontend/`: React 18 + Vite + TypeScript, Tailwind CSS, Recharts, react-router. No UI kits, no templates.
  Dev server proxies `/api` to `http://localhost:8000` (no CORS needed).
- One container: multi-stage `Dockerfile` (node builds SPA → python runtime; FastAPI serves `/api/*` and the built SPA).
  `docker compose up --build` → http://localhost:8000
- LLM config via env only: `LLM_API_KEY`, `LLM_BASE_URL` (empty = OpenAI), `LLM_MODEL`, `LLM_TIMEOUT_S=8`.
  The app MUST fully work with no key (rules mode + template rationale).

## 3. Layout and ownership (edit only what you own)

| Path | Owner |
|---|---|
| `backend/app/engine/**`, `backend/app/llm/**`, `backend/tests/engine/**`, `backend/scripts/**`, `eval/**`, `data/test_profiles/**` | A — Engine & AI |
| `backend/app/main.py`, `backend/app/api/**`, `backend/app/store/**`, `backend/app/auth.py`, `backend/app/hr/**`, `backend/tests/api/**`, `Dockerfile`, `docker-compose.yml`, `Makefile`, `README.md`, `docs/**` | B — Platform & HR |
| `frontend/**` | C — Experience |
| `backend/app/models.py` (shared Pydantic models = the contract), `AGENTS.md` | Shared. Change only in a dedicated commit `contract: ...` and tell the team |
| `data/*.json`, `data/*.csv` (starter kit) | Read-only |

## 4. Domain rules (from the starter-kit README — these are the traps)

1. **"Today" = `meta.as_of_date` = 2026-10-01.** Never use the system clock for business logic. New history rows use this date.
2. **Effective skills.** Profile skills are as of `last_review_date`. Apply every `completed` event dated after `last_review_date`, in date order:
   `new = max(cur, min(cur + gain, max_level))`. Missing skill = 0. Mark these as "pending review" with the source event. (114 of 200 employees are affected.)
3. **Target.** `career_goal {target_role, target_grade}` if set (28 employees target a DIFFERENT role, 66 have no goal).
   Else the next grade in the same role (Junior → Middle → Senior → Lead). Lead with no goal → no promotion target.
   Goal equal to current role+grade → treat as no goal.
4. **Gap** per skill = `max(0, required[target] − effective)`. Target `critical_skills` weigh 3, others 1.
5. **Candidate eligibility** (all must hold; keep an explicit rejection reason per event):
   - `mandatory == false` (mandatory = assigned by HR, never recommended; show separately as "assigned");
   - role fits: employee role ∈ `target_roles`, or goal role ∈ `target_roles` when the goal role differs;
   - grade fits: current grade ∈ `target_grades`, or target grade ∈ `target_grades`;
   - `prerequisites` met on EFFECTIVE levels (else blocked; an event that raises the missing prerequisite gets factor `prerequisites: unlocks EV_x`);
   - not already `completed` (exception: `EV_036`, recurring club) and not `in_progress` (show as "continue");
   - available: `format == self_paced`, or an `upcoming_sessions` date after as_of;
   - develops ≥1 skill with gap > 0 AND `effective < max_level` for that skill (the cap makes some events useless).
6. **History = voluntariness signal.** For each candidate, count outcomes on "similar" events (same developed skill, or same `type`+`format`):
   positive = `completed` (self-assigned and `feedback_rating ≥ 4` count extra), negative = `declined`, `no_show`, `dropped`.
   Weight last 12 months ×1.0, older ×0.5. **≥3 negatives on similar events ⇒ do not push that format again**;
   prefer another format (self_paced, mentoring, the `EV_036` club) and SAY so in the rationale.
   Open `overdue` mandatory items and `in_progress` items = workload signal.
7. `work_format == remote` → offline events get a fit penalty.
8. `preferred_language` (`kk` | `ru` | `en`) = language of the rationale and default UI language.

## 5. Scoring (deterministic, explainable — every number is shown in the UI)

```
gap_value    = Σ_s w_s · min(effective_gain_s, gap_s) / Σ_s w_s · gap_s     # share of the weighted target gap closed
propensity   = (1 + pos_similar) / (2 + pos_similar + neg_similar)
fit          = employee completion rate for this format (default 0.8); × 0.7 if remote and offline
availability = 1.0 if self_paced or next session ≤ 45 days; 0.8 if ≤ 90 days; else 0.5
score        = gap_value · (0.5 + 0.5 · propensity) · fit · availability
```

- Diversify: pick greedily; a candidate whose main skill is already covered by a pick gets × 0.5. Return up to 3 with score ≥ 0.05.
- `readiness = Σ_s w_s · min(eff_s, req_s) / Σ_s w_s · req_s` over target required skills (0–100 %), plus "critical met x/y".
- Trajectory projection: readiness after applying the gains of pick #1, #1+#2, #1+#2+#3.
- Empty result → `empty_reason` ∈ `AT_TOP_NO_GOAL`, `TARGET_REACHED`, `NO_ELIGIBLE_EVENTS`, `PREREQUISITES_BLOCKED`, `LOW_ENGAGEMENT`.
- Always compute the naive baseline (lowest effective skill). If it differs from pick #1, add a `not_recommended` entry explaining why.
- Every factor gets a human label with real numbers, e.g. `System Design 2 → 4 required for Senior (critical)`.
- Performance: < 50 ms per employee in rules mode.

## 6. LLM layer (`backend/app/llm/`)

- Role: the decision + explanation layer ON TOP of the engine. It picks 1–3 of the engine's top-8 candidates and explains them.
- Input: compact JSON — employee summary, target, top gaps (critical flagged), history stats, top-8 candidates with factor breakdowns and projections, naive baseline, language.
- Output: strict JSON schema — `picks[1..3] {event_id, rationale, factors_used[]}`, `not_recommended[]`, `summary`.
- Factor kinds (enum): `critical_gap`, `target_gap`, `expected_gain`, `max_level_cap`, `participation_history`, `format_fit`, `availability`, `prerequisites`, `stale_assessment`, `goal_alignment`, `workload`.
- Guardrails: `event_id` ∈ candidates; each pick cites ≥3 distinct factor kinds; rationale ≤ 60 words, second person, encouraging, no pressure, numbers only from the provided facts, written in `preferred_language` unless `?lang=` overrides.
  Invalid → one retry with the validation error → fallback to rules picks + template rationale (templates in en/ru/kk).
- Response carries `generated_by: "llm" | "rules"`, `model`, `latency_ms`.
- Latency: timeout `LLM_TIMEOUT_S`; cache by `(employee_id, state_hash, lang)`. The UI renders rules results at once and swaps in AI text when ready.

## 7. API contract (JSON, all under `/api`; Bearer token from login)

| Method & path | Who | Returns |
|---|---|---|
| `POST /api/auth/login` `{role: "employee"\|"hr", employee_id?}` | anyone (demo, no password) | `{token, role, employee_id}` |
| `GET /api/demo/people` | anyone | `[{employee_id, full_name, role, grade}]` (login picker only) |
| `GET /api/employees/{id}` | self or hr | `Profile` |
| `GET /api/employees/{id}/recommendations?mode=ai\|rules&lang=` | self or hr | `RecommendationResult` |
| `POST /api/employees/{id}/activities` `{event_id, action: "complete"\|"enroll"\|"not_now"}` | self | `ProgressUpdate` |
| `GET /api/catalog` | any logged in | `{skills[], proficiency_scale, events[]}` |
| `GET /api/hr/overview?department=` | hr | `HrOverview` |
| `GET /api/hr/employees?q=` | hr | `[{employee_id, full_name, role, grade, empty_reason?}]` |
| `POST /api/hr/import` multipart: any of `employees.json`, `activity_history.csv`, `events.json`, `skills.json` | hr | `ImportReport` (upsert by id) |
| `GET /api/health` | anyone | `{status, llm_enabled, model}` |

Shapes (field names are binding; mirror them in `backend/app/models.py` and `frontend/src/api/types.ts`):

```
Profile = {
  employee: {...raw employees.json fields},
  target: {role, grade, source: "career_goal"|"next_grade"|"none"},
  skills: [{skill_id, name, type, category, assessed, effective, pending_from: [event_id],
            required_current, required_target, critical}],
  readiness: {pct, critical_met, critical_total},
  history: [{...activity_history.csv columns, title}],
  stats: {completed, no_show, declined, dropped, overdue, in_progress},
  assigned: [{event_id, title, due_date, status}],
  available_events: [{event_id, title, eligible, blocked_by: string|null, score: number|null}]
}
RecommendationResult = {
  employee_id, target, generated_by: "llm"|"rules", model: string|null, latency_ms,
  recommendations: [{rank, event_id, title, type, format, duration_hours, next_session: date|null, score,
                     factors: [{kind, label, impact}], expected_gains: [{skill_id, from, to}],
                     readiness_after_pct, rationale}],
  trajectory: {now_pct, after_pct: [number]},
  not_recommended: [{skill_id: string|null, event_id: string|null, reason}],
  empty_reason: string|null
}
ProgressUpdate = {record: {...activity_history.csv row}, skills_changed: [{skill_id, from, to}],
                  readiness_before, readiness_after, recommendations: RecommendationResult /* rules mode */}
HrOverview = {
  lagging_skills: [{skill_id, name, employees_below, avg_gap, critical_count}],
  no_step: [{employee_id, full_name, role, grade, reason_code, hint}],
  participation: [{event_id, title, type, completed, no_show, declined, dropped, overdue, completion_rate, avg_rating, flagged}],
  disengaged: [{employee_id, full_name, negatives_6m, completions_6m}]
}
ImportReport = {added: {employees, history, events, skills}, updated: {...same keys}, errors: [{file, row, message}]}
```

Activity actions: `complete` → history row `status=completed, completion_pct=100, assigned_by=self, date=as_of`;
`enroll` → row `status=in_progress, completion_pct=0`; `not_now` → `data/runtime/feedback.jsonl` (soft negative 0.5 for 90 days; keeps the CSV schema clean).

## 8. Non-negotiables

- Roles enforced server-side: an employee gets 403 for anyone else's data and for `/api/hr/*`.
- No rankings or leaderboards of employees anywhere. No points or rewards for mandatory processes.
- Voluntariness: recommendations are invitations (Join / Not now / Mark completed). Never auto-assign.
- Never commit `.env` or keys (only `.env.example`). Never print keys in logs.
- Runtime writes and imports keep the starter-kit schema exactly.
- Imports never crash the app: bad rows are reported in `errors` and skipped.

## 9. How agents work here

- Small commits (≤ 30 min of work), message `area: what` (`engine: cap gains by max_level`). `git pull --rebase` before push. Never force-push `main`.
- Before committing: backend `cd backend && pytest -q`; frontend `cd frontend && npm run build`.
- No heavy dependencies, no boilerplate repos, no reformatting files you don't own.
- Never bypass git hooks (`--no-verify`); fix what the hook reports instead.
- Need a contract change or something from another owner? Don't edit their files. Put the request in your final message.
- End every task with: what now works (one line), how to check it (one command), open issues.
