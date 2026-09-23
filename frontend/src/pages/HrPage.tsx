import { useEffect, useRef, useState } from 'react'
import { api, auth } from '../api/client'
import type { HrOverview, ImportReport } from '../api/types'

const REASON_LABEL: Record<string, string> = {
  AT_TOP_NO_GOAL: 'At top grade, no goal',
  TARGET_REACHED: 'Target already met',
  NO_ELIGIBLE_EVENTS: 'No matching activity',
  PREREQUISITES_BLOCKED: 'Blocked by prerequisites',
  LOW_ENGAGEMENT: 'Low engagement',
}

function Bar({ value, max, tone = 'pine' }: { value: number; max: number; tone?: string }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0
  return (
    <div className="h-2 flex-1 rounded-full bg-line">
      <div className="h-2 rounded-full" style={{ width: `${pct}%`, background: tone === 'amber' ? '#c98a1b' : '#1f6b57' }} />
    </div>
  )
}

export function HrPage({ onSignOut }: { onSignOut: () => void }) {
  const [data, setData] = useState<HrOverview | null>(null)
  const [error, setError] = useState('')
  const [report, setReport] = useState<ImportReport | null>(null)
  const [importing, setImporting] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  function load() {
    api.hrOverview().then(setData).catch(() => setError('Could not load the HR overview.'))
  }
  useEffect(load, [])

  async function onImport(list: FileList | null) {
    if (!list || list.length === 0) return
    setImporting(true); setError(''); setReport(null)
    try {
      const result = await api.importFiles(Array.from(list))
      setReport(result)
      load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Import failed.')
    } finally {
      setImporting(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  if (error && !data) return <main className="min-h-screen bg-mist p-8"><p className="text-red-600">{error}</p></main>
  if (!data) return <main className="min-h-screen bg-mist p-8"><div className="loader">Loading the organization view…</div></main>

  const maxLag = Math.max(1, ...data.lagging_skills.map((s) => s.employees_below))

  return (
    <main className="min-h-screen bg-mist px-5 py-8">
      <div className="mx-auto max-w-6xl">
        <header className="topbar">
          <span className="brand"><span className="grid h-9 w-9 place-items-center rounded-xl bg-ink text-[#b9e5b4]">↗</span> CAREER QUEST · HR</span>
          <button onClick={onSignOut} className="signout">Sign out</button>
        </header>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          {/* Lagging skills */}
          <section className="card">
            <p className="eyebrow">Where skills lag most</p>
            <h2 className="section-title">Lagging competencies</h2>
            <div className="mt-5 space-y-3">
              {data.lagging_skills.slice(0, 10).map((skill) => (
                <div key={skill.skill_id} className="flex items-center gap-3 text-sm">
                  <span className="w-40 shrink-0 text-ink">{skill.name}{skill.critical_count > 0 && <span className="pill pill-amber ml-2">critical ×{skill.critical_count}</span>}</span>
                  <Bar value={skill.employees_below} max={maxLag} tone={skill.critical_count > 0 ? 'amber' : 'pine'} />
                  <span className="w-28 shrink-0 text-right text-slate-500">{skill.employees_below} below · gap {skill.avg_gap.toFixed(1)}</span>
                </div>
              ))}
            </div>
          </section>

          {/* No recommended step */}
          <section className="card">
            <p className="eyebrow">Needs attention</p>
            <h2 className="section-title">No recommended step ({data.no_step.length})</h2>
            <div className="mt-4 max-h-[22rem] overflow-auto">
              <table className="w-full text-sm">
                <tbody>
                  {data.no_step.map((person) => (
                    <tr key={person.employee_id} className="border-b border-line/70 align-top">
                      <td className="py-2 pr-3"><b className="text-ink">{person.full_name}</b><br /><small className="text-slate-500">{person.role} · {person.grade}</small></td>
                      <td className="py-2 pr-3"><span className="pill pill-slate">{REASON_LABEL[person.reason_code] ?? person.reason_code}</span></td>
                      <td className="py-2 text-slate-600">{person.hint}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Participation */}
          <section className="card lg:col-span-2">
            <p className="eyebrow">How activities perform</p>
            <h2 className="section-title">Participation by activity</h2>
            <div className="mt-4 overflow-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-slate-500">
                  <tr className="border-b border-line">
                    <th className="py-2 pr-3 font-medium">Activity</th>
                    <th className="py-2 pr-3 font-medium">Completed</th>
                    <th className="py-2 pr-3 font-medium">No-show</th>
                    <th className="py-2 pr-3 font-medium">Declined</th>
                    <th className="py-2 pr-3 font-medium">Dropped</th>
                    <th className="py-2 pr-3 font-medium">Completion</th>
                    <th className="py-2 pr-3 font-medium">Rating</th>
                  </tr>
                </thead>
                <tbody>
                  {data.participation.map((event) => (
                    <tr key={event.event_id} className="border-b border-line/70">
                      <td className="py-2 pr-3 text-ink">{event.title}{event.flagged && <span className="pill pill-amber ml-2">⚑ drop-off</span>}</td>
                      <td className="py-2 pr-3">{event.completed}</td>
                      <td className="py-2 pr-3">{event.no_show}</td>
                      <td className="py-2 pr-3">{event.declined}</td>
                      <td className="py-2 pr-3">{event.dropped}</td>
                      <td className="py-2 pr-3"><div className="flex items-center gap-2"><Bar value={event.completion_rate} max={1} tone={event.flagged ? 'amber' : 'pine'} /><span className="w-10 text-right text-slate-500">{Math.round(event.completion_rate * 100)}%</span></div></td>
                      <td className="py-2 pr-3 text-slate-500">{event.avg_rating != null ? event.avg_rating.toFixed(1) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Disengaged */}
          <section className="card">
            <p className="eyebrow">Quiet signals</p>
            <h2 className="section-title">Disengaging ({data.disengaged.length})</h2>
            {data.disengaged.length === 0 ? <p className="mt-4 text-sm text-slate-500">No one is flagged as disengaging right now.</p> : (
              <ul className="mt-4 space-y-2 text-sm">
                {data.disengaged.map((person) => (
                  <li key={person.employee_id} className="flex items-center justify-between border-b border-line/70 py-2">
                    <span className="text-ink">{person.full_name}</span>
                    <span className="text-slate-500">{person.negatives_6m} refusals · {person.completions_6m} completed · 6&nbsp;mo</span>
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-4 text-xs text-slate-400">Private HR signal. Talk first — this is not a ranking, and it is never shown to employees.</p>
          </section>

          {/* Import */}
          <section className="card">
            <p className="eyebrow">Evaluation</p>
            <h2 className="section-title">Import profiles &amp; history</h2>
            <p className="mt-2 text-sm text-slate-600">Upload any of <code>employees.json</code>, <code>activity_history.csv</code>, <code>events.json</code>, <code>skills.json</code>. Records are upserted by id; bad rows are reported, never fatal.</p>
            <input ref={fileRef} type="file" multiple accept=".json,.csv" onChange={(e) => onImport(e.target.files)} className="mt-4 block w-full text-sm" />
            {importing && <p className="mt-3 text-sm text-pine">Importing…</p>}
            {report && (
              <div className="mt-4 rounded-xl bg-mist p-4 text-sm">
                <p className="text-ink">Added {report.added.employees} employees, {report.added.history} history rows, {report.added.events} events, {report.added.skills} skills.</p>
                <p className="text-slate-600">Updated {report.updated.employees} employees, {report.updated.history} history rows.</p>
                {report.errors.length > 0 && <p className="mt-2 text-amber-700">{report.errors.length} row(s) skipped: {report.errors.slice(0, 3).map((x) => `${x.file}${x.row ? ` r${x.row}` : ''}`).join(', ')}{report.errors.length > 3 ? '…' : ''}</p>}
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  )
}
