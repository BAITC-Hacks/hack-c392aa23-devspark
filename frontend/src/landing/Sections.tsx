import { type ReactNode, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { DemoPerson } from '../api/types'
import { track } from './analytics'
import fixtures from './fixtures.json'
import { pickFactors } from './Hero'
import { useCountUp, useInView } from './hooks'
import { fmt, LANG_CHIP, LANGS, type Lang, useLang } from './i18n'

export const REPO_URL = 'https://github.com/BAITC-Hacks/hack-c392aa23-devspark'

function Reveal({ children, delay = 0, className = '' }: { children: ReactNode; delay?: number; className?: string }) {
  const [ref, inView] = useInView<HTMLDivElement>(0.15)
  return <div ref={ref} className={`lp-reveal ${inView ? 'is-in' : ''} ${className}`} style={{ transitionDelay: `${delay}ms` }}>{children}</div>
}

function Head({ eyebrow, title, lead, id }: { eyebrow: string; title: string; lead?: string; id: string }) {
  return (
    <Reveal>
      <p className="lp-eyebrow">{eyebrow}</p>
      <h2 id={id} className="lp-h2 mt-4">{title}</h2>
      {lead && <p className="lp-lead mt-5">{lead}</p>}
    </Reveal>
  )
}

/* ---------------------------------------------------------------- Problem */
export function Problem() {
  const { t } = useLang()
  const cards = [[t.problem.c1t, t.problem.c1b], [t.problem.c2t, t.problem.c2b], [t.problem.c3t, t.problem.c3b]]
  return (
    <section id="junior" className="lp-section" aria-labelledby="problem-title">
      <div className="lp-container">
        <Head id="problem-title" eyebrow={t.problem.eyebrow} title={t.problem.title} />
        <div className="mt-12 grid gap-5 md:grid-cols-3">
          {cards.map(([title, body], index) => (
            <Reveal key={title} delay={index * 120} className="lp-sand p-7">
              <span className="lp-num text-sm font-semibold lp-muted">0{index + 1}</span>
              <h3 className="mt-4 text-xl font-semibold tracking-tight">{title}</h3>
              <p className="mt-3 leading-7 lp-muted">{body}</p>
            </Reveal>
          ))}
        </div>
        <Reveal><p className="mt-14 max-w-3xl text-2xl font-semibold leading-snug tracking-tight md:text-[2rem]">{t.problem.closing}</p></Reveal>
      </div>
    </section>
  )
}

/* ---------------------------------------------------------------- Pipeline */
type TermKey = 'gap_value' | 'propensity' | 'fit' | 'availability'
const TERM_KINDS: Record<TermKey, string[]> = {
  gap_value: ['critical_gap', 'target_gap', 'expected_gain'],
  propensity: ['participation_history'],
  fit: ['format_fit'],
  availability: ['availability'],
}

export function Pipeline() {
  const { lang, t } = useLang()
  const [ref, inView] = useInView<HTMLDivElement>(0.3)
  const [open, setOpen] = useState(false)
  const [term, setTerm] = useState<TermKey | null>(null)
  const card = fixtures.hero.card
  const stages = [[t.pipeline.s1t, t.pipeline.s1tag, t.pipeline.s1b], [t.pipeline.s2t, t.pipeline.s2tag, t.pipeline.s2b], [t.pipeline.s3t, t.pipeline.s3tag, t.pipeline.s3b]]
  const glosses: Record<TermKey, string> = { gap_value: t.pipeline.gap, propensity: t.pipeline.propensity, fit: t.pipeline.fit, availability: t.pipeline.availability }
  const Term = ({ k }: { k: TermKey }) => (
    <button type="button" className="lp-term" aria-pressed={term === k} onMouseEnter={() => setTerm(k)} onMouseLeave={() => setTerm(null)} onFocus={() => setTerm(k)} onBlur={() => setTerm(null)} onClick={() => setTerm(term === k ? null : k)}>{k}</button>
  )
  return (
    <section id="middle" className="lp-section" aria-labelledby="pipeline-title">
      <div className="lp-container">
        <Head id="pipeline-title" eyebrow={t.pipeline.eyebrow} title={t.pipeline.title} lead={t.pipeline.sub} />
        <div ref={ref} className="mt-12 grid items-stretch gap-4 lg:grid-cols-[1fr_32px_1fr_32px_1fr]">
          {stages.map(([title, tag, body], index) => (
            <FragmentStage key={title} index={index} last={index === stages.length - 1} active={inView}>
              <span className="lp-num text-xs font-bold lp-muted">0{index + 1}</span>
              <h3 className="mt-3 text-xl font-semibold tracking-tight">{title}</h3>
              <p className="mt-1 text-sm font-semibold text-[var(--lp-pine)]">{tag}</p>
              <p className="mt-4 text-[15px] leading-7 lp-muted">{body}</p>
            </FragmentStage>
          ))}
        </div>

        <div className="mt-8">
          <button type="button" className="lp-btn lp-btn-outline" aria-expanded={open} onClick={() => setOpen(!open)}>{open ? t.pipeline.hide : t.pipeline.engineers} <span aria-hidden="true">{open ? '−' : '+'}</span></button>
          {open && (
            <div className="lp-card lp-fade mt-5 grid gap-8 p-6 lg:grid-cols-[1.25fr_1fr] lg:p-8">
              <div>
                <p className="lp-formula">score = <Term k="gap_value" /> · (0.5 + 0.5 · <Term k="propensity" />) · <Term k="fit" /> · <Term k="availability" /></p>
                <dl className="mt-5 space-y-3 text-sm leading-6">
                  {(Object.keys(glosses) as TermKey[]).map((key) => <div key={key} className={`transition-opacity ${term && term !== key ? 'opacity-40' : ''}`}><dt className="inline font-mono font-semibold">{key}</dt> <dd className="inline lp-muted">— {glosses[key]}</dd></div>)}
                </dl>
                <p className="mt-5 text-xs lp-muted">{t.pipeline.caption}</p>
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-[.14em] lp-muted">{t.pipeline.factors} · {card.title}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {card.factors.map((factor, index) => (
                    <span key={index} className={`lp-chip ${factor.kind === 'critical_gap' ? 'lp-chip-critical' : ''} ${term && TERM_KINDS[term].includes(factor.kind) ? 'lp-chip-lit' : ''}`}>{card.factor_labels[lang][index]}</span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}

function FragmentStage({ children, index, last, active }: { children: ReactNode; index: number; last: boolean; active: boolean }) {
  return (
    <>
      <div className={`lp-card lp-stage lp-reveal p-7 ${active ? 'is-in is-active' : ''}`} style={{ transitionDelay: `${index * 180}ms` }}>{children}</div>
      {!last && <div aria-hidden="true" className="hidden items-center lg:flex"><div className="lp-flow w-full" /></div>}
    </>
  )
}

/* ---------------------------------------------------------------- Trap */
export function Trap() {
  const { lang, t } = useLang()
  const [mode, setMode] = useState<'naive' | 'quest'>('quest')
  const trap = fixtures.trap
  const quest = trap.quest
  const chips = pickFactors(quest.factors)
  const total = fixtures.stats.traps_total
  return (
    <section id="senior" className="lp-section" aria-labelledby="trap-title">
      <div className="lp-container">
        <Head id="trap-title" eyebrow={t.trap.eyebrow} title={t.trap.title} />
        <Reveal className="mt-8 flex flex-wrap items-center justify-between gap-5">
          <div className="text-sm leading-7">
            <p className="font-semibold">{trap.persona.role} · {trap.persona.grade} → {trap.persona.target.grade}</p>
            <p className="lp-muted">{fmt(t.trap.lowest, { skill: trap.lowest.skill, level: trap.lowest.level, n: trap.lowest.refused })}</p>
            {trap.critical_gap && <p className="lp-muted">{fmt(t.trap.critical, { skill: trap.critical_gap.skill, have: trap.critical_gap.have, need: trap.critical_gap.need })}</p>}
          </div>
          <div className="lp-seg" role="group" aria-label={t.trap.eyebrow}>
            <button type="button" aria-pressed={mode === 'naive'} onClick={() => setMode('naive')}>{t.trap.toggleNaive}</button>
            <button type="button" aria-pressed={mode === 'quest'} onClick={() => setMode('quest')}>{t.trap.toggleQuest}</button>
          </div>
        </Reveal>
        <div className="mt-8 grid gap-5 md:grid-cols-2">
          <article className={`lp-card lp-panel p-7 ${mode === 'quest' ? 'is-dim' : ''}`} aria-current={mode === 'naive'}>
            <p className="text-xs font-bold uppercase tracking-[.14em] lp-muted">{t.trap.naiveLabel}</p>
            <h3 className="mt-4 text-2xl font-semibold tracking-tight">{trap.naive.title}</h3>
            <span className="lp-tag lp-tag-amber mt-4">{fmt(t.trap.naiveNote, { skill: trap.lowest.skill, n: trap.lowest.refused })}</span>
            <p className="mt-5 leading-7 lp-muted">{fmt(t.trap.naiveWhy, { skill: trap.lowest.skill })}</p>
          </article>
          <article className={`lp-card lp-panel p-7 ${mode === 'naive' ? 'is-dim' : ''}`} aria-current={mode === 'quest'} style={{ borderColor: mode === 'quest' ? 'var(--lp-pine)' : undefined }}>
            <div className="flex items-center gap-2"><p className="text-xs font-bold uppercase tracking-[.14em] text-[var(--lp-pine)]">{t.trap.questLabel}</p>{quest.generated_by === 'llm' && <span className="lp-tag lp-tag-ai">✦ AI</span>}</div>
            <h3 className="mt-4 text-2xl font-semibold tracking-tight">{quest.title}</h3>
            <div className="mt-4 flex flex-wrap gap-1.5">{chips.map((index) => <span key={index} className={`lp-chip ${quest.factors[index].kind === 'critical_gap' ? 'lp-chip-critical' : ''}`}>{quest.factor_labels[lang][index]}</span>)}</div>
            <p key={lang} className="lp-fade mt-5 leading-7">{quest.rationale[lang]}</p>
            <p className="lp-sand mt-5 rounded-2xl p-4 text-sm leading-6">{fmt(t.trap.questWhy, { skill: trap.lowest.skill, n: trap.lowest.refused })}</p>
          </article>
        </div>
        <Reveal className="mt-8 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
          <p className="lp-muted">{fmt(t.trap.caption, { total, passed: fixtures.stats.traps_passed })}</p>
          <a className="font-semibold text-[var(--lp-pine)] underline-offset-4 hover:underline" href={`${REPO_URL}/blob/main/eval/RESULTS.md`} target="_blank" rel="noreferrer">{t.trap.link} →</a>
        </Reveal>
      </div>
    </section>
  )
}

/* ---------------------------------------------------------------- Progress */
export function Progress() {
  const { t } = useLang()
  const progress = fixtures.progress
  const grade = fixtures.hero.target.grade ?? ''
  const [done, setDone] = useState(false)
  const readiness = useCountUp(progress.readiness_after, done, 1100, progress.readiness_before)
  useEffect(() => { if (!done) return; const timer = setTimeout(() => setDone(false), 7000); return () => clearTimeout(timer) }, [done])
  return (
    <section className="lp-section pt-0" aria-labelledby="progress-title">
      <div className="lp-container grid items-center gap-10 lg:grid-cols-[.9fr_1.1fr]">
        <Head id="progress-title" eyebrow={t.progress.eyebrow} title={t.progress.title} lead={t.progress.body} />
        <Reveal className="lp-card p-6 sm:p-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div><p className="text-xs font-bold uppercase tracking-[.14em] lp-muted">{t.hero.step}</p><p className="mt-1 text-xl font-semibold">{progress.event_title}</p></div>
            <button type="button" className={`lp-btn ${done ? 'lp-btn-outline' : 'lp-btn-solid'}`} onClick={() => setDone(!done)} aria-pressed={done}>{done ? `✓ ${t.progress.done}` : t.progress.button}</button>
          </div>
          <div className="mt-7 space-y-4">
            {progress.changes.map((change) => (
              <div key={change.skill}>
                <div className="flex justify-between text-sm"><span>{change.skill}</span><span className="lp-num font-semibold">{done ? `${change.from} → ${change.to}` : change.from}<span className="lp-muted"> / 5</span></span></div>
                <div className="lp-bar mt-2"><i className={done ? 'is-gain' : ''} style={{ width: `${((done ? change.to : change.from) / 5) * 100}%` }} /></div>
              </div>
            ))}
          </div>
          <div className="lp-divider my-7" />
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div><p className="text-sm lp-muted">{fmt(t.progress.readiness, { grade })}</p><p className="lp-num mt-1 text-4xl font-semibold tracking-tight">{readiness.toFixed(2)}%</p></div>
            <div className={`text-sm transition-all duration-500 ${done ? 'translate-y-0 opacity-100' : 'translate-y-2 opacity-0'}`} aria-live="polite">
              {done && <><p className="lp-muted">{t.progress.nextUp}</p><p className="font-semibold">{progress.next[0]}</p></>}
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  )
}

/* ---------------------------------------------------------------- HR preview */
type I18nList = { reasons_i18n?: Record<Lang, string[]> }

export function HrPreview() {
  const { lang, t } = useLang()
  const hr = fixtures.hr
  const maxLag = Math.max(1, ...hr.lagging.map((skill) => skill.employees_below))
  return (
    <section id="lead" className="lp-section" aria-labelledby="hr-title">
      <div className="lp-container">
        <Head id="hr-title" eyebrow={t.hr.eyebrow} title={t.hr.title} lead={t.hr.sub} />
        <div className="mt-12 grid gap-5 md:grid-cols-2 xl:grid-cols-[1fr_1fr_.85fr]">
          <Reveal className="lp-card p-6">
            <h3 className="font-semibold">{t.hr.lagging}</h3>
            <ul className="mt-5 space-y-4">
              {hr.lagging.map((skill) => (
                <li key={skill.name} className="text-sm">
                  <div className="flex items-center justify-between gap-3"><span>{skill.name}{skill.critical_count > 0 && <span className="lp-tag lp-tag-amber ml-2">{fmt(t.hr.critical, { n: skill.critical_count })}</span>}</span><span className="lp-num whitespace-nowrap lp-muted">{fmt(t.hr.below, { n: skill.employees_below })}</span></div>
                  <div className="lp-bar mt-2"><i style={{ width: `${(skill.employees_below / maxLag) * 100}%`, background: skill.critical_count ? 'var(--lp-amber)' : undefined }} /></div>
                </li>
              ))}
            </ul>
          </Reveal>
          <div className="grid gap-5">
            <Reveal delay={100} className="lp-card p-6">
              <div className="flex items-baseline justify-between"><h3 className="font-semibold">{t.hr.noStep}</h3><span className="text-xs lp-muted">{fmt(t.hr.people, { n: hr.no_step_total })}</span></div>
              <ul className="mt-4 space-y-3 text-sm">{hr.no_step.map((person) => <li key={person.who + person.role} className="flex items-center justify-between gap-3"><span><b>{person.who}</b> <span className="lp-muted">{person.role} · {person.grade}</span></span><span className="lp-tag lp-tag-soft whitespace-nowrap">{t.hr.reasons[person.reason] ?? person.reason}</span></li>)}</ul>
            </Reveal>
            <Reveal delay={180} className="lp-card p-6">
              <h3 className="font-semibold">{t.hr.attrition}</h3>
              <ul className="mt-4 space-y-3 text-sm">{hr.attrition.map((person) => {
                const reasons = (person as typeof person & I18nList).reasons_i18n?.[lang] ?? person.reasons
                return <li key={person.who + person.role}><div className="flex items-center justify-between gap-3"><span><b>{person.who}</b> <span className="lp-muted">{person.role} · {person.grade}</span></span><span className={`lp-tag whitespace-nowrap ${person.level === 'high' ? 'lp-tag-amber' : 'lp-tag-soft'}`}>{person.level === 'high' ? t.hr.high : t.hr.medium} · {person.risk}</span></div><p className="mt-1 text-xs lp-muted">{reasons[0]}</p></li>
              })}</ul>
            </Reveal>
          </div>
          <div className="grid gap-5 md:col-span-2 md:grid-cols-2 xl:col-span-1 xl:grid-cols-1">
            <Reveal delay={240} className="lp-card p-6">
              <h3 className="font-semibold">{t.hr.participation}</h3>
              <ul className="mt-4 space-y-3 text-sm">{hr.participation.map((event) => <li key={event.title}><div className="flex items-start justify-between gap-3"><span className="min-w-0">{event.title}</span><span className="lp-num shrink-0 lp-muted">{Math.round(event.rate * 100)}%</span></div><div className="lp-bar mt-1.5"><i style={{ width: `${event.rate * 100}%`, background: event.flagged ? 'var(--lp-amber)' : undefined }} /></div>{event.flagged && <span className="mt-1 inline-block text-[11px] text-[var(--lp-amber)]">⚑ {t.hr.dropOff}</span>}</li>)}</ul>
            </Reveal>
            <Reveal delay={300} className="lp-sand p-6"><p className="text-[15px] font-semibold leading-7">{t.hr.principle}</p></Reveal>
          </div>
        </div>
        <p className="mt-5 text-xs lp-muted">{t.hr.preview}</p>
      </div>
    </section>
  )
}

/* ---------------------------------------------------------------- Principles */
export function Principles() {
  const { t } = useLang()
  const p = t.principles
  const items = [[p.explainableT, p.explainableB], [p.voluntaryT, p.voluntaryB], [p.privateT, p.privateB], [p.sovereignT, p.sovereignB], [p.multilingualT, p.multilingualB]]
  return (
    <section id="trust" className="lp-section" aria-labelledby="principles-title">
      <div className="lp-container">
        <Head id="principles-title" eyebrow={p.eyebrow} title={p.title} />
        <div className="mt-12 grid gap-x-8 gap-y-10 sm:grid-cols-2 lg:grid-cols-5">
          {items.map(([title, body], index) => (
            <Reveal key={title} delay={index * 90} className="border-t-2 border-[var(--lp-pine)] pt-5">
              <h3 className="text-lg font-semibold tracking-tight">{title}</h3>
              <p className="mt-3 text-sm leading-6 lp-muted">{body}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ---------------------------------------------------------------- Multilingual */
export function Multilingual() {
  const { lang, t } = useLang()
  const [selected, setSelected] = useState<Lang>(lang)
  useEffect(() => setSelected(lang), [lang])
  const card = fixtures.hero.card
  return (
    <section className="lp-section pt-0" aria-labelledby="multi-title">
      <div className="lp-container grid items-center gap-10 lg:grid-cols-2">
        <Head id="multi-title" eyebrow={t.multi.eyebrow} title={t.multi.title} lead={t.multi.body} />
        <Reveal className="lp-card p-7">
          <div className="flex items-center justify-between gap-3">
            <p className="font-semibold">{card.title}</p>
            <div className="lp-lang lp-lang-light" role="group" aria-label={t.footer.language}>
              {LANGS.map((code) => <button key={code} type="button" aria-pressed={selected === code} onClick={() => setSelected(code)}>{LANG_CHIP[code]}</button>)}
            </div>
          </div>
          <p className="mt-5 grid leading-7">{LANGS.map((code) => <span key={code} aria-hidden="true" className="invisible col-start-1 row-start-1">{card.rationale[code]}</span>)}<span key={selected} lang={selected} className="lp-fade col-start-1 row-start-1">{card.rationale[selected]}</span></p>
        </Reveal>
      </div>
    </section>
  )
}

/* ---------------------------------------------------------------- Architecture */
export function Architecture() {
  const { t } = useLang()
  const a = t.arch
  const Box = ({ x, y, title, sub, ai = false }: { x: number; y: number; title: string; sub: string; ai?: boolean }) => (
    <g><rect className={`box ${ai ? 'is-ai' : ''}`} x={x} y={y} width={176} height={64} rx={14} /><text x={x + 16} y={y + 28}>{title}</text><text className="sub" x={x + 16} y={y + 47}>{sub}</text></g>
  )
  return (
    <section className="lp-section pt-0" aria-labelledby="arch-title">
      <div className="lp-container">
        <Head id="arch-title" eyebrow={a.eyebrow} title={a.title} />
        <Reveal className="lp-card mt-10 overflow-x-auto p-4 sm:p-8">
          <svg className="lp-arch min-w-[640px]" viewBox="0 0 900 330" role="img" aria-label={`${a.spa} → ${a.api} → ${a.store}, ${a.engine}, ${a.ai} → ${a.llm}`}>
            <defs><marker id="lp-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 10 5 0 10z" fill="var(--lp-muted)" stroke="none" /></marker></defs>
            <Box x={10} y={133} title={a.spa} sub={a.spaSub} />
            <Box x={240} y={133} title={a.api} sub={a.apiSub} />
            <Box x={480} y={20} title={a.store} sub={a.storeSub} />
            <Box x={480} y={133} title={a.engine} sub={a.engineSub} />
            <Box x={480} y={246} title={a.ai} sub={a.aiSub} ai />
            <Box x={714} y={246} title={a.llm} sub={a.llmSub} />
            <path d="M186 165 H236" markerEnd="url(#lp-arrow)" />
            <path d="M416 165 C 446 165, 446 52, 476 52" markerEnd="url(#lp-arrow)" />
            <path d="M416 165 H476" markerEnd="url(#lp-arrow)" />
            <path d="M416 165 C 446 165, 446 278, 476 278" markerEnd="url(#lp-arrow)" />
            <path className="mint" d="M604 199 V242" markerEnd="url(#lp-arrow)" />
            <path className="dash" d="M540 246 V203" markerEnd="url(#lp-arrow)" />
            <path d="M656 278 H710" markerEnd="url(#lp-arrow)" />
            <text className="edge" x={614} y={226}>{a.shortlist}</text>
            <text className="edge" x={530} y={226} textAnchor="end">{a.fallback}</text>
          </svg>
        </Reveal>
        <p className="mt-5 font-mono text-xs lp-muted">{a.caption}</p>
      </div>
    </section>
  )
}

/* ---------------------------------------------------------------- Roadmap */
export function Roadmap() {
  const { t } = useLang()
  const r = t.roadmap
  const items = [[r.r1t, r.r1b], [r.r2t, r.r2b], [r.r3t, r.r3b], [r.r4t, r.r4b]]
  return (
    <section className="lp-section pt-0" aria-labelledby="roadmap-title">
      <div className="lp-container">
        <Head id="roadmap-title" eyebrow={r.eyebrow} title={r.title} />
        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {items.map(([title, body], index) => (
            <Reveal key={title} delay={index * 90} className="lp-card p-6">
              <span className="lp-tag lp-tag-soft">{r.tag}</span>
              <h3 className="mt-4 font-semibold tracking-tight">{title}</h3>
              <p className="mt-2 text-sm leading-6 lp-muted">{body}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ---------------------------------------------------------------- Final CTA */
export function FinalCta() {
  const { lang, t } = useLang()
  const navigate = useNavigate()
  const [people, setPeople] = useState<DemoPerson[] | null>(null)
  const [query, setQuery] = useState('')
  const load = () => { if (!people) api.people().then(setPeople).catch(() => setPeople([])) }
  const matches = useMemo(() => {
    if (!people || !query.trim()) return []
    const needle = query.toLowerCase()
    return people.filter((person) => `${person.full_name} ${person.role} ${person.employee_id}`.toLowerCase().includes(needle)).slice(0, 6)
  }, [people, query])
  const open = (id: string) => { track('demo_opened', { profile: id, lang }); navigate(`/app?demo=${id}`) }
  return (
    <section id="demo" className="lp-hero" aria-labelledby="final-title">
      <div className="lp-container relative py-20 lg:py-28">
        <h2 id="final-title" className="lp-h1 max-w-[16ch]">{t.final.title}</h2>
        <p className="mt-5 max-w-xl text-lg text-white/70">{t.final.sub}</p>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {fixtures.people.map((person) => (
            <button key={person.employee_id} type="button" onClick={() => open(person.employee_id)} className="group rounded-3xl border border-white/10 bg-white/[.04] p-6 text-left transition hover:border-[#b9e5b4]/60 hover:bg-white/[.07]">
              <p className="text-xs font-bold uppercase tracking-[.14em] text-[#b9e5b4]">{t.final.tags[person.tag] ?? person.tag}</p>
              <p className="mt-3 text-lg font-semibold">{person.employee_id} · {person.role}</p>
              <p className="text-sm text-white/60">{person.grade}</p>
              <p className="mt-5 text-sm font-semibold text-white/80 group-hover:text-white">{t.final.open} →</p>
            </button>
          ))}
        </div>
        <div className="mt-8 grid gap-4 md:grid-cols-[1fr_auto] md:items-start">
          <div className="relative">
            <label htmlFor="lp-search" className="text-sm text-white/60">{fmt(t.final.search, { n: fixtures.stats.profiles })}</label>
            <input id="lp-search" value={query} onFocus={load} onChange={(e) => { load(); setQuery(e.target.value) }} placeholder={t.final.searchPlaceholder} autoComplete="off" className="mt-2 w-full rounded-2xl border border-white/15 bg-white/[.06] px-4 py-3 text-white outline-none placeholder:text-white/35 focus:border-[#b9e5b4]" />
            {matches.length > 0 && (
              <ul className="absolute z-10 mt-2 w-full overflow-hidden rounded-2xl bg-white text-[#17352d] shadow-2xl">
                {matches.map((person) => <li key={person.employee_id}><button type="button" onClick={() => open(person.employee_id)} className="flex w-full justify-between gap-3 px-4 py-3 text-left text-sm hover:bg-[#f3f7f5]"><span><b>{person.full_name}</b> <span className="text-slate-500">{person.role} · {person.grade}</span></span><span className="text-slate-400">{person.employee_id}</span></button></li>)}
              </ul>
            )}
          </div>
          <button type="button" onClick={() => { track('demo_opened', { profile: 'hr', lang }); navigate('/app?role=hr') }} className="lp-btn lp-btn-ghost md:mt-7">{t.final.hr} →</button>
        </div>
      </div>
    </section>
  )
}
