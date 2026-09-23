# Career Quest — team plan (14:00 → 18:00)

## 0. Decisions (made — don't re-debate them)

1. **Architecture:** deterministic engine (hard rules + scoring, every number explainable) → LLM decision layer (picks 1–3 of the top-8, writes a ≥3-factor rationale in kk/ru/en) → validator → rules fallback.
2. **The dataset traps are the product.** Stale skills after `last_review_date`, `career_goal` in another role, critical skills, prerequisites, `max_level` caps, repeated declines/no-shows, mandatory ≠ recommendable. All listed in `AGENTS.md §4`.
3. **Proof beats claims:** our own 8 trap profiles + an eval table "lowest-skill baseline vs ours" goes in the README.
4. **One container, one command, works with no API key.**
5. **One human = one stream = one Codex = one git identity.** No shared credentials.

Where the points come from:

| Criterion | Pts | What earns it | Owner |
|---|---|---|---|
| Task fit & functionality | 25 | E2E scenario + jury import working by 15:30 | all |
| Technical implementation | 25 | engine + LLM + validator + tests + eval | A |
| README & reproducibility | 25 | fresh-clone test, verified commands, eval table | B |
| Value | 15 | actionable HR hints, voluntariness, "why not X" | B + C |
| Originality & potential | 10 | trap eval, on-prem-ready LLM, same decision-layer pattern as the Voice Router case | A |

## 1. Roles

- **A — Engine & AI** (strongest in Python / LLMs): engine, LLM layer, trap profiles, eval.
- **B — Platform & HR** (backend / devops): API, auth, import, HR analytics, Docker, README, submission.
- **C — Experience** (frontend): all screens, HR dashboard, import UI, i18n, demo video.

## 2. Timeline

| Time | A — Engine & AI | B — Platform & HR | C — Experience |
|---|---|---|---|
| 14:00–14:15 setup | Put key in local `.env`; measure latency of 2–3 fast models with structured output; pick `LLM_MODEL` | First commit: `AGENTS.md`, `PLAN.md`, `.gitignore`, `.env.example`, `data/` (starter kit). Then Codex: "generate backend/app/models.py (Pydantic v2) exactly from AGENTS.md §7" → commit `contract: models` by 14:15. Ask mentor about data (§6) | Pull; start **C1** in mock mode |
| 14:15–15:20 build 1 | **A1** engine v1. At 14:30 fire **A2** as a parallel Codex cloud task | **B1** platform + stub API + Docker | **C1** employee journey on mocks |
| **15:20–15:30 CP1** | Integrate: UI → real API → engine. See CP1 checklist (§5) | | |
| 15:30–16:40 build 2 | **A3** LLM layer, then run eval | **B2** HR analytics + import tested with `data/test_profiles/` | **C2** HR dashboard + import UI + i18n |
| **16:40–16:50 CP2** | Feature freeze. Full demo dry-run on the Docker build | | |
| 16:50–17:30 harden | Max 1 stretch (§7) + `eval/RESULTS.md` | **B3** README (RU) + fresh-clone test | **C3** polish + 2-min backup demo video |
| **17:30 code freeze** | Only README fixes after this | Submit on the platform (§8) | |
| 17:45–18:00 | Buffer. Do not touch code. | | |

## 3. Git and Codex workflow

1. Each person works in their own clone, with their own git identity and their own Codex session.
2. Work on `main`, only in your own directories (`AGENTS.md §3`). `git pull --rebase` before every push; push every 20–30 min.
3. Contract changes (`backend/app/models.py`, `AGENTS.md §7`) = one `contract:` commit + say it out loud.
4. Local ports: backend :8000, Vite dev server :5173 (proxies `/api` → :8000).

## 4. Codex prompts (copy-paste)

### A1 — Engine v1 (14:15)
```
Read AGENTS.md fully; sections 4–7 are your spec. Implement the engine as a pure Python package backend/app/engine/ (no FastAPI imports):
- dataset.py: load skills.json, employees.json, events.json, activity_history.csv from a directory; merge extra directories (data/extra, data/test_profiles) by id (upsert).
- skills.py: effective_skills() (§4.2), resolve_target() (§4.3), gaps(), readiness() and trajectory projection (§5).
- candidates.py: eligibility with an explicit rejection reason per event (§4.5); history/propensity/format features (§4.6–4.7).
- recommender.py: scoring, diversification, empty_reason codes, naive lowest-skill baseline and not_recommended (§5).
  Public API: profile(ds, employee_id) -> Profile; recommend(ds, employee_id, k=3, mode="rules") -> RecommendationResult; apply_activity(ds, employee_id, event_id, action) -> ProgressUpdate.
- Use the Pydantic models in backend/app/models.py (B commits them at 14:15). Missing field? Add it in a separate "contract: ..." commit and tell the team.
- Factor labels in English with real numbers, e.g. "System Design 2 → 4 required for Senior (critical)".
Tests in backend/tests/engine/: one test per rule in §4 with tiny in-memory fixtures (stale assessment, career_goal in another role, critical weighting, prerequisites, max_level cap, completed + EV_036, mandatory excluded, no upcoming session, repeated declines switch format, remote vs offline).
Script backend/scripts/compare_baseline.py: run all employees, print how often our top-1 differs from the lowest-skill baseline, 5 example explanations, and p95 runtime (< 50 ms).
Make pytest green. Commit in small steps ("engine: ...").
```

### A2 — Trap profiles + eval (Codex cloud task, 14:30)
```
Read AGENTS.md. Create data/test_profiles/ in EXACTLY the starter-kit format: employees.json as {"meta": ..., "employees": [...]} and activity_history.csv with the same columns. Add 8 synthetic employees E9001–E9008 (record_ids from R900001), each built so that a single-factor rule fails, using real event and skill ids from data/:
1) lowest skill is Public Speaking with 3 declines/no-shows on public-speaking events, while a critical skill for the next grade has a gap;
2) a skill looks low, but an event completed after last_review_date already closed the gap;
3) career_goal in a different role;
4) the best-gap event has unmet prerequisites, so the prerequisite-building event should come first;
5) skill already at the event's max_level, so that event gives no gain;
6) Lead with no goal → empty_reason AT_TOP_NO_GOAL;
7) remote employee with no-shows on offline events and strong self-paced completions;
8) everything relevant completed → TARGET_REACHED or NO_ELIGIBLE_EVENTS.
Write eval/expectations.json (per employee: must_include / must_not_include event ids, or expected empty_reason) and eval/run_eval.py: load data/ + data/test_profiles/, run (a) lowest-skill baseline, (b) rules engine, (c) AI mode if LLM_API_KEY is set; print a Markdown table (profile, trap, baseline pick, our pick, pass/fail, latency) and write it to eval/RESULTS.md. Commit as "eval: ...".
```

### A3 — LLM layer (15:30)
```
Read AGENTS.md §6. Implement backend/app/llm/:
- client.py: OpenAI SDK client from env (LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT_S); cleanly disabled when no key.
- prompt.py: compact JSON context from the engine output (top-8 candidates with factors and projections, history stats, naive baseline, target, language) + the system prompt from §6.
- decide.py: structured output with a strict JSON schema; validate (ids ⊆ candidates, ≥3 distinct factor kinds per pick, 1–3 picks); one retry with the validation error; otherwise fall back to rules picks + template rationale (en/ru/kk templates). Cache by (employee_id, state_hash, lang). Fill generated_by, model, latency_ms.
- Wire into recommend(..., mode="ai").
- Tests with a fake client: unknown event id → fallback; only 2 factor kinds → retry → fallback; timeout → fallback.
Measure 10 real employees, print p50/p95, and tune (fewer candidates, shorter context, lower reasoning effort) until p95 < 6 s. Commit as "llm: ...".
```

### B1 — Platform (14:15)
```
Read AGENTS.md §2, §3, §7, §8. Build the backend platform:
- backend/requirements.txt; backend/app/main.py: FastAPI app, /api routes, serves frontend/dist at / when it exists (SPA fallback to index.html).
- backend/app/store/: load data/ (+ data/extra/, data/runtime/) through app.engine.dataset (teammate A is building it; until it lands, write a minimal loader behind the same function names). Persist runtime history rows to data/runtime/activity_history.csv (same columns) and not_now events to data/runtime/feedback.jsonl.
- backend/app/auth.py: demo login without password, HMAC-signed token {role, employee_id}; dependencies require_self_or_hr(employee_id) and require_hr(). Employees get 403 for other employees and for /api/hr/*.
- backend/app/api/: every endpoint in AGENTS.md §7 with the exact shapes from backend/app/models.py. Until the engine exists, return realistic stub data so the frontend can integrate.
- POST /api/hr/import: multipart with any subset of the 4 starter-kit files; validate, upsert by id, skip and report bad rows, never crash; return ImportReport. Also auto-load data/extra/* at startup.
- Dockerfile (multi-stage: node:20 builds frontend → python:3.11-slim runs uvicorn on 8000), docker-compose.yml (one service, port 8000, volume for data/runtime, LLM_* env passed through with empty defaults — it must start with NO .env file), Makefile (up, dev, test), .env.example.
- backend/tests/api/: 403 cases, import of a small fixture, complete → skills change.
Make pytest green and build the Docker image once. Commit in small steps ("api: ...", "infra: ...").
```

### B2 — HR analytics + import hardening (15:30)
```
Read AGENTS.md. Implement backend/app/hr/analytics.py and wire /api/hr/overview and /api/hr/employees:
- lagging_skills: gaps vs each employee's TARGET requirements using the engine's effective skills; per skill: employees_below, avg_gap, critical_count; top 15; optional ?department= filter.
- no_step: employees whose recommend() is empty, with reason_code and an HR-actionable hint (e.g. NO_ELIGIBLE_EVENTS → "no event develops SK_X for Senior QA — consider creating one"; LOW_ENGAGEMENT → "talk first, don't assign more").
- participation: per event from history: counts per status, completion_rate, avg feedback_rating; flagged when no_show + dropped > 25 %.
- disengaged: ≥2 negative outcomes and 0 completions in the 6 months before as_of_date.
- Cache the overview; recompute on import/completion; < 1 s for 200+ employees.
Tests per aggregate on a small fixture. Then import data/test_profiles/ via curl, check their recommendations, and write the exact curl commands to docs/demo.md. Commit as "hr: ...".
```

### B3 — README (16:50)
Paste the organizers' README prompt into Codex, then add:
```
Additionally include: a Mermaid architecture diagram; the recommendation algorithm (factors, formula, guardrails, fallback) exactly as implemented in backend/app/engine and backend/app/llm; the table from eval/RESULTS.md; the demo scenario with employees E0028 and E0112 and the import of test profiles; an env variables table; a note that the app works without an LLM key; privacy and roles; known limitations. Run every command you put in the README and fix anything that fails.
```

### C1 — Frontend + employee journey (14:00)
```
Read AGENTS.md §2, §3, §7, §8. Create frontend/ from scratch: Vite + React + TypeScript + Tailwind + Recharts + react-router. No UI kits or templates. Vite dev server proxies /api to http://localhost:8000.
- src/api/types.ts mirrors AGENTS.md §7 exactly; src/api/client.ts adds the Bearer token; mock mode (VITE_MOCK=1) serves realistic fixtures from src/mocks/ (employee E0028: Backend Engineer, Middle → Senior, System Design 2 of 4, critical) so you are not blocked by the backend.
- Login: choose Employee (searchable picker from /api/demo/people) or HR.
- Employee page "My path":
  header (name, role, grade, tenure, goal);
  trajectory (grade ladder Junior→Middle→Senior→Lead with current and target, readiness %, critical skills met x/y, projected readiness after each recommended step);
  skills vs target chart (effective vs required, critical highlighted, "pending review" markers);
  1–3 recommendation cards (title, type/format/duration/next session, rationale, factor chips, expandable "How this was calculated" with each factor, its numbers and the score, expected gains like "System Design 2→3", actions Join / Not now / Mark completed);
  "Why not X" note from not_recommended; assigned mandatory items listed separately; history timeline with statuses.
- Mark completed → before/after view (skill bars animate, readiness delta), then refetch recommendations.
- Render mode=rules at once, then fetch mode=ai and swap the text with a small "AI" badge. The spinner never blocks the page.
Clean, calm corporate look. Run npm run build. Commit in small steps ("ui: ...").
```

### C2 — HR area + import + i18n (15:30)
```
Read AGENTS.md. Add the HR area (role hr only):
- Dashboard: lagging skills (horizontal bars + department filter); "No recommended step" table with reason and hint (click → read-only profile); participation by activity (completion-rate bar, flag icon); disengaged list. No employee rankings anywhere.
- Import page: drag-and-drop for employees.json / activity_history.csv / events.json / skills.json → POST /api/hr/import → show the ImportReport, then links to the imported employees.
- i18n: EN / RU / KK toggle for UI strings (src/i18n/*.json); default from employee.preferred_language; pass ?lang= to recommendations.
Run npm run build. Commit as "ui: ...".
```

### C3 — Polish (16:50)
```
Read AGENTS.md. Polish without changing the API: friendly empty states for every empty_reason, loading and error states, 375 px mobile width, consistent spacing and typography. Walk through docs/demo.md end to end and fix anything that breaks. Run npm run build. Commit as "ui: polish".
```

## 5. Checkpoint checklists

**CP1 (15:20)** — all must be true:
1. `make dev` runs backend + frontend locally.
2. Log in as E0028 → profile, trajectory, 1–3 recommendations, each with ≥3 factors.
3. Mark completed → a skill and readiness change on screen.
4. HR page shows lagging skills (even if other widgets are stubs).
5. Each of the three has ≥2 commits on `main`.

**CP2 (16:40)** — feature freeze:
1. Every must-have from the case table works in the Docker build.
2. AI rationale arrives in < 10 s, or the rules fallback shows.
3. Importing `data/test_profiles/` through the UI works; the new people get recommendations.
4. `eval/run_eval.py`: ours passes ≥ 7/8, the baseline fails most.
5. `docker compose up --build` works from a fresh clone with no `.env`.

## 6. Risks and answers

| Risk | Answer |
|---|---|
| Jury files differ slightly (extra fields, only 2 of 4 files, id clashes) | Import accepts any subset, ignores unknown fields, reports bad rows, never crashes |
| LLM slow or down at the defense | Rules result renders instantly; AI text swaps in; fallback after 8 s |
| Data rule: "may not be taken outside the hackathon" | Ask a mentor at 14:00 whether the team repo is private. Private → commit `data/`. Public → keep `data/` git-ignored and document where to put the files |
| API key leaks | `.env` in `.gitignore` from the first commit; check before submitting (§8) |
| Behind schedule at CP1 | Cut in this order: i18n strings → animations → disengaged list and HR filters → LLM reranking (keep LLM rationale only). Never cut: import, progress update, ≥3-factor rationale, 3 HR widgets, one-command start, README |

## 7. Stretch (only after CP2, max 1 per person)

- A: point `LLM_BASE_URL` at NVIDIA's OpenAI-compatible endpoint (`https://integrate.api.nvidia.com/v1`) with an open model → "on-prem-ready" story for a bank (~15 min).
- A: "Ask why" box: the employee asks "why not X?", the LLM answers from the same facts.
- C: gamification lite: personal XP for voluntary activities only, milestone badges ("critical skill met"). No leaderboard.
- B: consent toggle "share my plan with my manager".

## 8. Defense demo (3 min) and submission

Demo:
1. HR → Import → upload the jury's files → report shows the new employees.
2. Open a jury profile (backup: E0028 or E0112) → trajectory, readiness, critical skills.
3. Read one rationale aloud: ≥3 factors + "why not <lowest skill>".
4. Mark completed → skill 2→3, readiness +X %, new recommendations.
5. HR dashboard: lagging skills, no-step list with hints, participation.
6. Show `eval/RESULTS.md` and toggle rules vs AI mode.

Submission (B, 17:30):
1. `git grep -nE "sk-[A-Za-z0-9_-]{20,}|nvapi-"` prints nothing, and `git ls-files | grep .env` shows only `.env.example`.
2. Fresh clone into a new folder → `docker compose up --build` → full demo works.
3. README renders on GitHub: all 11 organizer sections + eval table + screenshots.
4. GitHub → Insights → Contributors shows all three people.
5. Platform → track page → "Сдать решение" → title + description.
