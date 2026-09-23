import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { Link, Navigate, Route, Routes, useNavigate, useSearchParams } from 'react-router-dom'
import { api, auth } from './api/client'
import type { AuthSession, DemoPerson } from './api/types'
import { LandingPage } from './landing/LandingPage'

// The workspace pages carry charts; load them on demand so the landing stays light.
const EmployeePage = lazy(() => import('./pages/EmployeePage').then((m) => ({ default: m.EmployeePage })))
const HrPage = lazy(() => import('./pages/HrPage').then((m) => ({ default: m.HrPage })))

function workspacePath(session: AuthSession) { return session.role === 'hr' ? '/hr' : `/me/${session.employee_id}` }

function Login({ onLogin }: { onLogin: (session: AuthSession) => void }) {
  const navigate = useNavigate(); const [params] = useSearchParams(); const [role, setRole] = useState<'employee' | 'hr'>('employee'); const [people, setPeople] = useState<DemoPerson[]>([]); const [query, setQuery] = useState(''); const [person, setPerson] = useState<DemoPerson | null>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState(''); const deepLinked = useRef(false)
  useEffect(() => { api.people().then(setPeople).catch(() => setError('Could not load the people directory.')) }, [])
  // Deep links from the landing page: /app?demo=E0028 or /app?role=hr open the workspace directly.
  useEffect(() => { const demo = params.get('demo'); const asHr = params.get('role') === 'hr'; if (deepLinked.current || (!demo && !asHr)) return; deepLinked.current = true; void signIn(asHr ? 'hr' : 'employee', demo ?? undefined) }, [params])
  const filtered = people.filter((p) => `${p.full_name} ${p.role} ${p.employee_id}`.toLowerCase().includes(query.toLowerCase()))
  async function signIn(nextRole: 'employee' | 'hr', employeeId?: string) { setError(''); setLoading(true); try { const next = await api.login(nextRole, employeeId); auth.set(next); onLogin(next); navigate(workspacePath(next)) } catch (e) { setError(e instanceof Error ? e.message : 'Sign in failed.') } finally { setLoading(false) } }
  function enter() { if (role === 'employee' && !person) return setError('Choose an employee profile to continue.'); void signIn(role, person?.employee_id) }
  return <main className="min-h-screen bg-mist px-5 py-10 md:grid md:place-items-center"><section className="mx-auto grid w-full max-w-5xl overflow-hidden rounded-3xl bg-white shadow-card md:grid-cols-[.9fr_1.1fr]"><div className="bg-ink p-8 text-white md:p-12"><div className="flex items-center justify-between gap-3 text-sm font-semibold"><span className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-[#b9e5b4] text-ink">↗</span> CAREER QUEST</span><Link to="/" className="text-xs font-medium text-white/60 hover:text-white">← Overview</Link></div><div className="mt-20"><p className="text-[#b9e5b4]">Halyk Bank · growth, in context</p><h1 className="mt-4 text-4xl font-semibold leading-tight">A clearer path to your next role.</h1><p className="mt-5 max-w-sm text-white/70">Explore skills, thoughtful recommendations, and the progress that matters to you.</p></div></div><div className="p-8 md:p-12"><p className="text-sm font-medium text-pine">WELCOME</p><h2 className="mt-2 text-2xl font-semibold text-ink">Choose your workspace</h2><div className="mt-7 grid grid-cols-2 rounded-xl bg-mist p-1"><button className={`tab ${role === 'employee' ? 'tab-active' : ''}`} onClick={() => setRole('employee')}>Employee</button><button className={`tab ${role === 'hr' ? 'tab-active' : ''}`} onClick={() => setRole('hr')}>HR partner</button></div>{role === 'employee' ? <div className="mt-7"><label className="label">Find your profile</label><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search by name or role" className="input" />{query && <div className="picker">{filtered.map((p) => <button key={p.employee_id} onClick={() => { setPerson(p); setQuery('') }} className="picker-row"><span className="avatar">{p.full_name.split(' ').map((x) => x[0]).join('')}</span><span><b>{p.full_name}</b><small>{p.role} · {p.grade}</small></span></button>)}</div>}{person ? <button className="selected-person" onClick={() => setPerson(null)}><span className="avatar">{person.full_name.split(' ').map((x) => x[0]).join('')}</span><span><b>{person.full_name}</b><small>{person.role} · {person.grade}</small></span><span>×</span></button> : <p className="mt-3 text-sm text-slate-500">Search and select a profile.</p>}</div> : <p className="mt-8 rounded-xl bg-sand p-4 text-sm leading-6 text-slate-600">You’ll see organization-level development signals. Individual employee recommendations remain private.</p>}{error && <p className="mt-5 text-sm text-red-600">{error}</p>}<button disabled={loading} onClick={enter} className="primary-button mt-8 w-full">{loading ? 'Opening workspace…' : 'Continue'} <span>→</span></button><p className="mt-5 text-center text-xs text-slate-400">Demo access · no password required</p></div></section></main>
}

// An explicit deep link (?demo= / ?role=hr) always switches profile; otherwise reuse the session.
function AppEntry({ session, onLogin }: { session: AuthSession | null; onLogin: (session: AuthSession) => void }) {
  const [params] = useSearchParams()
  const deepLink = params.has('demo') || params.get('role') === 'hr'
  return session && !deepLink ? <Navigate to={workspacePath(session)} /> : <Login onLogin={onLogin} />
}

export default function App() {
  const [session, setSession] = useState<AuthSession | null>(() => auth.restore())
  const signOut = () => { auth.set(null); setSession(null) }
  return <Suspense fallback={<main className="loading"><div className="loader" /><p>Preparing your path…</p></main>}>
    <Routes>
      <Route path="/" element={<LandingPage session={session} />} />
      <Route path="/app" element={<AppEntry session={session} onLogin={setSession} />} />
      <Route path="/me/:id" element={session?.role === 'employee' ? <EmployeePage onSignOut={signOut} /> : <Navigate to="/app" />} />
      <Route path="/hr" element={session?.role === 'hr' ? <HrPage onSignOut={signOut} /> : <Navigate to="/app" />} />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  </Suspense>
}
