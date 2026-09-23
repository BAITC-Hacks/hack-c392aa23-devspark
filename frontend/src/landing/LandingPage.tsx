import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import type { AuthSession } from '../api/types'
import { track } from './analytics'
import { Hero, ProofStrip } from './Hero'
import { DICTS, initialLang, LANG_CHIP, LANGS, type Lang, LangContext, useLang } from './i18n'
import './landing.css'
import { Path } from './Path'
import { Architecture, FinalCta, HrPreview, Multilingual, Pipeline, Principles, Problem, Progress, REPO_URL, Roadmap, Trap } from './Sections'

const TITLES: Record<Lang, string> = {
  en: 'Career Quest — a clear path to your next role',
  ru: 'Career Quest — понятный путь к следующей роли',
  kk: 'Career Quest — келесі рөлге түсінікті жол',
}

function LangSwitch({ light = false }: { light?: boolean }) {
  const { lang, setLang, t } = useLang()
  return (
    <div className={`lp-lang ${light ? 'lp-lang-light' : ''}`} role="group" aria-label={t.footer.language}>
      {LANGS.map((code) => <button key={code} type="button" lang={code} aria-pressed={lang === code} onClick={() => setLang(code)}>{LANG_CHIP[code]}</button>)}
    </div>
  )
}

function Nav({ session, onContact }: { session: AuthSession | null; onContact: () => void }) {
  const { lang, t } = useLang()
  const [open, setOpen] = useState(false)
  const workspace = session ? (session.role === 'hr' ? '/hr' : `/me/${session.employee_id}`) : null
  const links = [['#top', t.nav.product], ['#middle', t.nav.how], ['#lead', t.nav.hr], ['#trust', t.nav.trust]]
  const cta = workspace
    ? <Link to={workspace} className="lp-btn lp-btn-primary !py-2.5">{t.nav.workspace} →</Link>
    : <Link to="/app?demo=E0028" className="lp-btn lp-btn-primary !py-2.5" onClick={() => track('demo_opened', { profile: 'E0028', lang })}>{t.nav.demo} →</Link>
  return (
    <nav className="lp-nav" aria-label="Career Quest">
      <div className="lp-container flex h-16 items-center justify-between gap-4">
        <a href="#top" className="flex items-center gap-3 text-sm font-semibold tracking-wide text-white"><span className="grid h-9 w-9 place-items-center rounded-xl bg-[#b9e5b4] text-[#10261f]">↗</span>CAREER QUEST</a>
        <div className="hidden items-center gap-6 xl:flex">
          {links.map(([href, label]) => <a key={href} href={href} className="lp-nav-link">{label}</a>)}
          <a href={`${REPO_URL}#readme`} target="_blank" rel="noreferrer" className="lp-nav-link">{t.nav.docs}</a>
        </div>
        <div className="hidden items-center gap-3 md:flex">
          <LangSwitch />
          <button type="button" onClick={onContact} className="lp-nav-link hidden px-2 xl:inline">{t.nav.talk}</button>
          {cta}
        </div>
        <button type="button" className="rounded-lg px-3 py-2 text-sm text-white/80 xl:hidden" aria-expanded={open} aria-controls="lp-menu" onClick={() => setOpen(!open)}>{open ? '✕' : '☰'} <span className="sr-only">{t.nav.menu}</span></button>
      </div>
      {open && (
        <div id="lp-menu" className="lp-container grid gap-4 pb-6 xl:hidden">
          {links.map(([href, label]) => <a key={href} href={href} className="lp-nav-link text-base" onClick={() => setOpen(false)}>{label}</a>)}
          <a href={`${REPO_URL}#readme`} target="_blank" rel="noreferrer" className="lp-nav-link text-base">{t.nav.docs}</a>
          <div className="flex flex-wrap items-center gap-3"><LangSwitch /><button type="button" onClick={() => { setOpen(false); onContact() }} className="lp-nav-link">{t.nav.talk}</button></div>
          {cta}
        </div>
      )}
    </nav>
  )
}

function ContactDialog({ onClose }: { onClose: () => void }) {
  const { t } = useLang()
  const closeRef = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    closeRef.current?.focus()
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  return (
    <div className="lp-modal" onClick={onClose}>
      <div role="dialog" aria-modal="true" aria-labelledby="lp-contact-title" className="lp-card p-7" onClick={(event) => event.stopPropagation()}>
        <h2 id="lp-contact-title" className="text-2xl font-semibold tracking-tight">{t.contact.title}</h2>
        <p className="mt-4 leading-7 lp-muted">{t.contact.body}</p>
        <div className="mt-7 flex flex-wrap gap-3">
          <a href={REPO_URL} target="_blank" rel="noreferrer" className="lp-btn lp-btn-solid">{t.contact.repo} →</a>
          <button ref={closeRef} type="button" onClick={onClose} className="lp-btn lp-btn-outline">{t.contact.close}</button>
        </div>
      </div>
    </div>
  )
}

function Footer() {
  const { t } = useLang()
  return (
    <footer className="border-t border-[var(--lp-line)]">
      <div className="lp-container flex flex-wrap items-center justify-between gap-6 py-10 text-sm">
        <div className="space-y-1">
          <p className="flex items-center gap-2 font-semibold"><span className="grid h-7 w-7 place-items-center rounded-lg bg-[#b9e5b4] text-xs text-[#10261f]">↗</span>Career Quest · {t.footer.team}</p>
          <p className="lp-muted">{t.footer.event} · {t.footer.synthetic}</p>
        </div>
        <div className="flex flex-wrap items-center gap-5">
          <a href={REPO_URL} target="_blank" rel="noreferrer" className="font-semibold text-[var(--lp-pine)] underline-offset-4 hover:underline">{t.footer.repo}</a>
          <LangSwitch light />
        </div>
      </div>
    </footer>
  )
}

export function LandingPage({ session }: { session: AuthSession | null }) {
  const [lang, setLangState] = useState<Lang>(initialLang)
  const [contact, setContact] = useState(false)
  const railRef = useRef<HTMLDivElement>(null)
  const setLang = (next: Lang) => { setLangState(next); try { localStorage.setItem('cq-landing-lang', next) } catch { /* private mode */ } }
  useEffect(() => {
    const previous = document.title
    document.documentElement.lang = lang
    document.title = TITLES[lang]
    return () => { document.title = previous; document.documentElement.lang = 'en' }
  }, [lang])
  const openContact = () => { track('contact_clicked', { lang }); setContact(true) }
  return (
    <LangContext.Provider value={{ lang, t: DICTS[lang], setLang }}>
      <div className="lp">
        <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-[#10261f]">Skip to content</a>
        <Nav session={session} onContact={openContact} />
        <main id="main">
          <Hero />
          <ProofStrip />
          <div ref={railRef} className="lp-rail relative">
            <Path wrapperRef={railRef} deps={[lang]} />
            <div className="relative z-[1]">
              <Problem />
              <Pipeline />
              <Trap />
              <Progress />
              <HrPreview />
              <Principles />
              <Multilingual />
              <Architecture />
              <Roadmap />
            </div>
          </div>
          <FinalCta />
        </main>
        <Footer />
        {contact && <ContactDialog onClose={() => setContact(false)} />}
      </div>
    </LangContext.Provider>
  )
}
