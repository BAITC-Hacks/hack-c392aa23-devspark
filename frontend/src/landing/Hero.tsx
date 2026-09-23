import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { track } from './analytics'
import fixtures from './fixtures.json'
import { clamp01, ease, useCountUp, useInView, useLoop, useReducedMotion } from './hooks'
import { fmt, LANG_CHIP, LANGS, LOCALE, type Lang, useLang } from './i18n'

const GRADES = ['Junior', 'Middle', 'Senior', 'Lead']
const LOOP_MS = 12000
const FINAL_FRAME = 10800

type Factor = { kind: string; label: string }

export function pickFactors(factors: Factor[]) {
  const find = (kinds: string[]) => factors.findIndex((factor) => kinds.includes(factor.kind))
  return [find(['critical_gap', 'target_gap']), find(['participation_history']), find(['format_fit', 'availability'])].filter((index) => index >= 0)
}

export function shortDate(value: string | null, lang: Lang) {
  if (!value) return ''
  return new Intl.DateTimeFormat(LOCALE[lang], { day: 'numeric', month: 'short' }).format(new Date(value))
}

function Ring({ value }: { value: number }) {
  return (
    <div className="lp-ring" role="img" aria-label={`${Math.round(value)}%`}>
      <svg viewBox="0 0 36 36"><path className="bg" d="M18 2.5a15.5 15.5 0 1 1 0 31a15.5 15.5 0 1 1 0-31" /><path className="fg" pathLength={100} strokeDasharray={`${value} 100`} d="M18 2.5a15.5 15.5 0 1 1 0 31a15.5 15.5 0 1 1 0-31" /></svg>
      <b className="lp-num">{Math.round(value)}%</b>
    </div>
  )
}

function HeroCard() {
  const { lang, t } = useLang()
  const reduced = useReducedMotion()
  const [hover, setHover] = useState(false)
  const [ref, visible] = useVisible<HTMLDivElement>()
  const running = !reduced && !hover && visible
  const clock = useLoop(LOOP_MS, running)
  const e = reduced ? FINAL_FRAME : clock

  const hero = fixtures.hero
  const card = hero.card
  const sequence: Lang[] = [lang, ...LANGS.filter((code) => code !== lang), lang]
  const phase = e < 6400 ? 0 : e < 7700 ? 1 : e < 9000 ? 2 : 3
  const shown = sequence[phase]
  const fullText = card.rationale[shown]
  const typed = phase === 0 ? clamp01((e - 3900) / 2300) : 1
  const text = fullText.slice(0, Math.round(fullText.length * typed))
  const readiness = hero.readiness.pct * ease(e / 1800)
  const current = GRADES.indexOf(hero.employee.grade)
  const target = GRADES.indexOf(hero.target.grade ?? '')
  const chips = pickFactors(card.factors)
  const gain = card.gains[0]

  return (
    <div ref={ref} className="relative" onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)} onFocus={() => setHover(true)} onBlur={() => setHover(false)}>
      <div className="mb-3 flex items-center justify-between">
        <span className={`lp-live ${running ? '' : 'is-paused'}`}><i />{running ? t.hero.live : t.hero.paused}</span>
        <span className="flex gap-1" aria-hidden="true">{LANGS.map((code) => <span key={code} className={`rounded-md px-2 py-0.5 text-[10px] font-bold tracking-wider transition ${code === shown && e > 3900 ? 'bg-[#b9e5b4] text-[#10261f]' : 'text-white/45'}`}>{LANG_CHIP[code]}</span>)}</span>
      </div>
      <div className="lp-hero-card p-5 sm:p-7" aria-label={`${hero.employee.name}: ${card.title}`}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[.16em] text-[#1f6b57]">{t.hero.myPath}</p>
            <p className="mt-1 text-xl font-semibold">{hero.employee.name}</p>
            <p className="text-sm text-slate-500">{hero.employee.role} · {hero.employee.grade} · {fmt(t.hero.monthsAt, { n: hero.employee.tenure_months })}</p>
          </div>
          <div className="rounded-xl bg-[#f7f2e9] px-3 py-2 text-right"><p className="text-[10px] font-bold uppercase tracking-wider text-[#8b7047]">{t.hero.goal}</p><p className="text-sm font-semibold">{hero.target.role} · {hero.target.grade}</p></div>
        </div>

        <div className="mt-5 grid items-center gap-5 sm:grid-cols-[auto_1fr]">
          <div className="flex items-center gap-3"><Ring value={readiness} /><p className="max-w-[9rem] text-xs leading-5 text-slate-500">{fmt(t.hero.readiness, { grade: hero.target.grade ?? '' })}</p></div>
          <div className="lp-ladder">{GRADES.map((grade, index) => <div key={grade} className={`${index === current && e > 500 ? 'is-current' : ''} ${index === target && e > 1300 ? 'is-target' : ''}`}><span>{index + 1}</span>{grade}</div>)}</div>
        </div>

        <div className={`mt-5 rounded-2xl border border-[#dce8e2] p-4 transition-all duration-500 sm:p-5 ${e > 1900 ? 'translate-y-0 opacity-100' : 'translate-y-3 opacity-0'}`}>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-[#eef4f1] px-2.5 py-1 text-[10px] font-bold tracking-wider text-[#1f6b57]">{t.hero.step}</span>
            {e > 3700 && <span className="lp-tag lp-tag-ai lp-pop">✦ AI</span>}
          </div>
          <p className="mt-3 text-lg font-semibold">{card.title}</p>
          <p className="text-xs text-slate-500">{t.types[card.type] ?? card.type} · {t.formats[card.format] ?? card.format} · {fmt(t.hero.hours, { n: card.duration_hours })} · {shortDate(card.next_session, shown)}</p>
          <div className="mt-3 flex min-h-[4.5rem] flex-wrap content-start gap-1.5">
            {chips.map((index, order) => <span key={index} className={`lp-chip ${card.factors[index].kind === 'critical_gap' ? 'lp-chip-critical' : ''} ${e > 2400 + order * 380 ? 'opacity-100' : 'translate-y-1 opacity-0'}`}>{card.factor_labels[shown][index]}</span>)}
          </div>
          <p className="mt-3 min-h-[6.2rem] text-sm leading-6 text-slate-700" aria-live="off">
            {e > 3900 && <span key={shown} className={phase === 0 ? '' : 'lp-fade'}>{text}</span>}
            {phase === 0 && typed > 0 && typed < 1 && <span className="lp-caret" />}
          </p>
          <div className={`mt-3 flex flex-wrap gap-2 text-xs transition-opacity duration-500 ${e > 3400 ? 'opacity-100' : 'opacity-0'}`}>
            {gain && <span className="rounded-lg bg-[#f3f7f5] px-2.5 py-1.5">{t.hero.expectedGain} <b>{gain.skill} {gain.from} → {gain.to}</b></span>}
            <span className="rounded-lg bg-[#f3f7f5] px-2.5 py-1.5">{t.hero.readinessAfter} <b>{card.readiness_after}%</b></span>
          </div>
        </div>
      </div>
    </div>
  )
}

/** Visible-in-viewport flag that follows scrolling both ways (pauses the loop off-screen). */
function useVisible<T extends Element>() {
  const ref = useRef<T | null>(null)
  const [visible, setVisible] = useState(true)
  useEffect(() => {
    const element = ref.current
    if (!element) return
    const observer = new IntersectionObserver(([entry]) => setVisible(entry.isIntersecting), { threshold: 0.2 })
    observer.observe(element)
    return () => observer.disconnect()
  }, [])
  return [ref, visible] as const
}

export function Hero() {
  const { lang, t } = useLang()
  const reduced = useReducedMotion()
  const heroRef = useRef<HTMLElement>(null)
  const frame = useRef(0)
  const onMove = (event: React.MouseEvent) => {
    if (reduced || frame.current) return
    const { clientX, clientY } = event
    frame.current = requestAnimationFrame(() => {
      frame.current = 0
      const box = heroRef.current?.getBoundingClientRect()
      if (!box || !heroRef.current) return
      heroRef.current.style.setProperty('--mx', `${((clientX - box.left) / box.width) * 100}%`)
      heroRef.current.style.setProperty('--my', `${((clientY - box.top) / box.height) * 100}%`)
    })
  }
  return (
    <header id="top" ref={heroRef} className="lp-hero" onMouseMove={onMove}>
      <div className="lp-container relative grid gap-12 pb-20 pt-14 lg:grid-cols-[1fr_1.05fr] lg:items-center lg:pb-28 lg:pt-20">
        <div>
          <p className="lp-eyebrow">{t.hero.eyebrow}</p>
          <h1 className={`lp-h1 mt-5 ${lang === 'en' ? '' : 'lp-h1-long'}`}>{t.hero.title}</h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-white/70">{t.hero.sub}</p>
          <div className="mt-9 flex flex-wrap gap-3">
            <Link to="/app?demo=E0028" className="lp-btn lp-btn-primary" onClick={() => track('demo_opened', { profile: 'E0028', lang })}>{t.hero.ctaDemo} <span aria-hidden="true">→</span></Link>
            <a href="#middle" className="lp-btn lp-btn-ghost">{t.hero.ctaMethod}</a>
          </div>
        </div>
        <HeroCard />
      </div>
      <div aria-hidden="true" className="absolute bottom-0 left-1/2 hidden h-16 w-[3px] -translate-x-1/2 rounded-full bg-gradient-to-b from-transparent to-[#b9e5b4] lg:block" />
    </header>
  )
}

export function ProofStrip() {
  const { t } = useLang()
  const [ref, inView] = useInView<HTMLDivElement>(0.4)
  const stats = fixtures.stats
  const profiles = useCountUp(stats.profiles, inView)
  const activities = useCountUp(stats.activities, inView)
  const skills = useCountUp(stats.skills, inView)
  const traps = useCountUp(stats.traps_passed, inView)
  const items = [
    { value: Math.round(profiles), label: t.proof.profiles },
    { value: Math.round(activities), label: t.proof.activities },
    { value: Math.round(skills), label: t.proof.skills },
    { value: `${Math.round(traps)}/${stats.traps_total}`, label: t.proof.traps },
    { value: `${stats.rules_ms} ms`, label: t.proof.rules },
    ...(stats.ai_ms ? [{ value: `~${(stats.ai_ms / 1000).toFixed(1)} s`, label: t.proof.ai }] : []),
  ]
  return (
    <section aria-label={t.proof.builtFor} className="border-b border-[var(--lp-line)]">
      <div ref={ref} className="lp-container py-10">
        <p className="text-center text-xs font-semibold uppercase tracking-[.16em] lp-muted">{t.proof.builtFor}</p>
        <dl className="mt-7 grid grid-cols-2 gap-6 text-center sm:grid-cols-3 lg:grid-cols-6">
          {items.map((item) => <div key={item.label} className="flex flex-col-reverse"><dt className="mt-1 text-xs lp-muted">{item.label}</dt><dd className="lp-num text-2xl font-semibold tracking-tight">{item.value}</dd></div>)}
        </dl>
      </div>
    </section>
  )
}
