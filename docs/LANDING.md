# Career Quest — Landing page design (SaaS)

> Planning document. Nothing here is built yet. It describes what the landing page
> should be, why, and how it would be built — precisely enough to hand to an agent.

---

## 1. Positioning

**One line.** Career Quest is the AI decision layer for employee growth.

**The pitch.** Companies spend their full development budget and still get
formality-driven completions and empty voluntary events — not because the training is
bad, but because nobody tells the employee *why this step, why now, and where it leads.*
Career Quest turns scattered HR events into a clear, explainable path to the next
grade, and gives HR a live map of where the catalog fails its people.

**Who it is for.** Mid-to-large organisations with graded career ladders — banks,
telcos, public sector, big tech. Buyer: Head of L&D / HRD. User: every employee.

**Why it wins.** Explainability is the product. Every recommendation shows its factors;
every empty result has a reason; a naive rule is shown side by side and beaten.
It works without a cloud LLM, so it can run inside a bank's perimeter.

---

## 2. What the page must achieve

| In | The visitor should… |
|---|---|
| 5 seconds | understand what it is: *a clear path to your next role, explained.* |
| 30 seconds | **see it work** — not a screenshot; the real component, animating. |
| 60 seconds | trust it — explainable, private, sovereign, tested on trap profiles. |
| 2 minutes | know how it works, and click *Open a demo profile.* |

Two conversions: **Open a demo profile** (self-serve, into the live app on E0028) and
**Talk to us** (enterprise). No sign-up wall on the demo.

---

## 3. Visual identity

Inherits the app so the landing and product feel like one thing.

- **Palette.** Ink `#17352d` (dark surfaces), Pine `#1f6b57` (primary), Mint `#b9e5b4`
  (accent / "the path"), Mist `#f3f7f5` (light surfaces), Sand `#f7f2e9` (warm cards),
  Line `#dce8e2`. Amber `#c98a1b` only for "critical" and warnings.
- **Type.** Inter (UI) with a slightly tighter display cut for headlines; large,
  confident, few words. Numbers in tabular figures.
- **Mood.** Calm, premium, bank-grade. No confetti, no rocket emojis. Motion is slow
  and purposeful. Dark hero → light body → dark close.
- **Signature motif — the Path.** A single mint SVG line that *draws itself* as you
  scroll, running down the page and passing through four nodes — **Junior → Middle →
  Senior → Lead** — which anchor the main sections. It is the grade ladder from the
  product, turned into the page's spine. Every section "sits on the path."
- **Dark / light.** Both, following system; the hero is always dark.

---

## 4. Page map

Sections in order. Each lists copy (draft), visual, and interaction.

### 4.1 Navigation (sticky, translucent)
Logo ↗ CAREER QUEST · Product · How it works · For HR · Trust · Docs ·
**[Open a demo profile]** (primary). Collapses to a sheet on mobile.

### 4.2 Hero — *the product is the hero*
- **Headline:** Every employee deserves to know where they're going.
- **Sub:** Career Quest turns scattered HR events into a clear, explainable path to the
  next grade — and shows HR where the catalog fails its people.
- **CTAs:** Open a demo profile → · Read the method
- **Visual (right, 55% width):** the **real** Trajectory + Recommendation components
  with fixture data (E0028), running a 12-second scripted loop:
  1. readiness ring fills 0 → 76 %, grade ladder lights *Middle → Senior*;
  2. a recommendation card slides in; factor chips appear one by one
     (*Leadership 1 → 2 required for Senior*, *2/2 similar completed*, *online fits*);
  3. the **✦ AI** badge pops and the rationale types out;
  4. the language flips KK → RU → EN and the rationale morphs;
  5. loop. A "Live" dot pulses; hovering pauses it.
- **Background:** ink, with a slow, cursor-aware mint gradient — subtle.
- **Below the fold hint:** the Path line begins at the ring and heads down.

### 4.3 Proof strip
Small, quiet: *Built for Halyk Bank at HackAlem AI* · **200** profiles · **40**
activities · **60** skills · **8 / 8** trap profiles handled · **< 10 ms** rules,
**~3 s** AI. Counters animate once on view.

### 4.4 The problem — "The bottleneck isn't the training. It's the decision."
Three cards on Sand, node **Junior** on the Path:
1. **A stream of notifications.** Onboarding, courses, reviews, mentoring — arriving as
   deadlines, not as a trajectory.
2. **Formality by design.** Done on the due date, forgotten the day after.
3. **Empty rooms.** Voluntary events with no turnout, while the budget is fully spent.

Closing line, large: *Every one of these is a decision nobody explained.*

### 4.5 How it works — "The decision layer" (node **Middle**)
A horizontal, scroll-driven pipeline. Three stages, each a card that activates as it
enters view; data "flows" along the Path between them.

1. **Facts, not guesses.** Effective skills (post-review completions applied, caps
   respected), target grade or career goal, weighted gaps, prerequisites, availability,
   participation history. *Rules you can read.*
2. **AI decides — from a shortlist.** The model picks 1–3 of the engine's top-8 and
   writes the rationale in the employee's language. It may only cite factors that
   exist. *Judgement where judgement helps.*
3. **Validated, or it falls back.** Every answer is checked (ids in shortlist, ≥ 3 real
   factors); one retry; otherwise the rules result ships. *Never a blank screen,
   never an invented number.*

**"For engineers" toggle** reveals the scoring formula in monospace:
`score = gap_value · (0.5 + 0.5·propensity) · fit · availability`, with a one-line
gloss for each term. Hovering a term highlights the matching factor chip in the
hero card above (which is still visible on wide screens — the two are linked).

### 4.6 Why this, why not that — the trap
Node **Senior**. Split panel, one profile: *lowest skill is Public Speaking, refused
three times; the critical gap is System Design.*

- Left, greyed: **"Recommend for the lowest skill."** → Public Speaking Club. A small
  red note: *already declined ×3.*
- Right, alive: **Career Quest** → System Design Fundamentals, factors listed, and the
  line *Public Speaking is your lowest skill, but you declined it three times — we'll
  suggest a lighter format later.*

A toggle **[Naive rule | Career Quest]** flips the panels. Caption: *Single-factor rules
fail on real people. We built 8 profiles designed to break them — and pass all 8.*
Link → eval results.

### 4.7 Progress you can see
Interactive: a card with **Mark completed**. Clicking it animates the skill bar
1 → 2, the readiness counter 75.76 → 78.79, the Path advances one notch, and the next
recommendation slides in. Reset after 6 s. Copy: *Finish something, and the map moves.*

### 4.8 For HR — "Where the catalog fails your people"
Node **Lead**. A dashboard preview (real components, fixture data), four tiles:
lagging competencies (with *critical ×N*), no recommended step (reason + hint),
participation with drop-off flags, attrition risk with **plain-language reasons**.

Sidebar principle, set in Sand: *No rankings. No leaderboards. Engagement data is
never shown to other employees. Signals prompt a conversation, not a decision.*

### 4.9 Principles
Five short blocks, icon-free, typographic:
**Explainable** — every number on screen has a source. **Voluntary** — invitations,
not orders; "Not now" is a real answer. **Private** — internal loop, role-separated.
**Sovereign** — any OpenAI-compatible endpoint; runs on-prem in one container.
**Multilingual** — Kazakh, Russian, English, live.

### 4.10 Multilingual moment
One recommendation card, three language chips. Clicking morphs the rationale
(cross-fade, not reload). Copy: *The same reasoning, in the employee's language.*

### 4.11 Architecture (compact)
A single clean diagram (SVG, themed): SPA → API → Store / Rules engine / AI layer →
OpenAI-compatible endpoint. Under it: *FastAPI · React · one container ·
`docker compose up`.* Link → README.

### 4.12 What's next (roadmap)
Four cards, honest: calendar & messenger nudges · HR event builder from lagging
skills · grade-transition simulation ("what if I complete these three?") · mentoring
matches from the same engine. Tag each *planned*, not *coming soon*.

### 4.13 Final CTA (dark)
*See your path.* An inline demo picker — the app's own profile search — with three
suggested profiles: **E0028** (the case example), **E0112** (the public-speaking trap),
**E9003** (goal in another role). One click opens the live app.

### 4.14 Footer
Team · Repository · HackAlem AI 2026 · Halyk Bank track · Data is synthetic.
Language switch for the page itself (KK / RU / EN).

---

## 5. Signature interactions (the "cool")

1. **The Path.** The mint line draws on scroll, through four grade nodes that are the
   section anchors. Deep-link `#senior` scrolls to the trap section and lights the node.
2. **Live hero.** Real components, scripted loop, pauses on hover, resumes on leave.
3. **Linked explanation.** Hover a formula term → the matching factor chip glows in
   the card. Explainability, demonstrated.
4. **Naive vs Quest toggle.** The single best argument, made in one click.
5. **Mark completed.** The page itself makes progress.
6. **Language morph.** Rationale cross-fades between KK / RU / EN.
7. **Counters on view** for the proof strip; **reduced-motion** respected everywhere.

Rule of restraint: at most one moving thing per viewport at a time.

---

## 6. Copy deck (headlines)

- Every employee deserves to know where they're going.
- The bottleneck isn't the training. It's the decision.
- Facts, not guesses. · Judgement where judgement helps. · Validated, or it falls back.
- Why this, why not that.
- Finish something, and the map moves.
- Where the catalog fails your people.
- The same reasoning, in the employee's language.
- See your path.

Tone: calm, specific, second person where it's about the employee. No exclamation marks.

---

## 7. Technical plan

- **Where.** A `/` landing route in the existing Vite app (the workspace moves to
  `/app`), or `frontend-landing/` built to the same static bundle. Served by FastAPI
  like everything else — still one container, one command.
- **Components.** Reuse `Trajectory`, `RecommendationCard`, the HR tiles and the
  language chips with **fixture data** (no API calls on the landing). Fixtures = E0028,
  E0112, E9003 snapshots exported from the engine.
- **Motion.** Framer Motion for scroll-linked reveals and the Path draw
  (`pathLength` on an SVG), CSS for the rest. `prefers-reduced-motion` → static.
- **Performance budget.** < 200 KB JS on the landing, LCP < 1.5 s, no layout shift
  (reserve the hero card's box). Fonts self-hosted, two weights.
- **Accessibility.** Semantic sections, focus-visible, the toggles are real buttons,
  the animated card has a text equivalent, colour contrast AA on both themes.
- **i18n.** Page strings in `landing/i18n/{kk,ru,en}.json`; default from browser.
- **Analytics.** Two events only: `demo_opened`, `contact_clicked`. No trackers.
- **SEO / share.** Title *Career Quest — a clear path to your next role*; OG image is
  the hero card, rendered once.

---

## 8. Build plan (when it is time)

| Phase | Scope | Effort | Owner |
|---|---|---|---|
| 1 | Skeleton: nav, hero with static card, proof strip, problem, principles, footer | ~2 h | C |
| 2 | Live hero loop, the Path draw, section nodes | ~2 h | C |
| 3 | Decision-layer pipeline + formula toggle + linked highlight | ~1.5 h | A + C |
| 4 | Naive-vs-Quest trap toggle, Mark-completed demo, language morph | ~1.5 h | C |
| 5 | HR preview, architecture SVG, roadmap, final CTA picker | ~1.5 h | B + C |
| 6 | i18n, dark mode, perf + a11y pass, OG image | ~1 h | all |

Total ≈ 1.5 days for one person; an afternoon for three with agents. Phases 1–2 alone
already make a convincing page.

---

## 9. Success

The page is done when a stranger, in under a minute and without reading a paragraph,
can say what Career Quest does, has watched it recommend something *and explain it*,
and has clicked into a demo profile. Everything else is polish.
