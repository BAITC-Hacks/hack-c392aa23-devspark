import type { AuthSession, DemoPerson, Grade, HrOverview, ImportReport, Profile, ProgressUpdate, RecommendationResult, Role } from './types'
import { aiRecommendations, people, profile, progress, rulesRecommendations } from '../mocks/fixtures'

const mock = import.meta.env.VITE_MOCK === '1'
const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))
let session: AuthSession | null = null
export const auth = { get: () => session, set: (value: AuthSession | null) => { session = value; localStorage.setItem('career-quest-session', JSON.stringify(value)) }, restore: () => { try { session = JSON.parse(localStorage.getItem('career-quest-session') || 'null') } catch { session = null }; return session } }

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = auth.get()?.token
  const response = await fetch(path, { ...init, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...init.headers } })
  if (!response.ok) throw new Error((await response.text()) || `Request failed (${response.status})`)
  return response.json() as Promise<T>
}
export const api = {
  async login(role: Role, employee_id?: string) { if (mock) { await wait(180); return { token: 'mock-token', role, employee_id: role === 'employee' ? employee_id : null } as AuthSession } return request<AuthSession>('/api/auth/login', { method: 'POST', body: JSON.stringify({ role, employee_id }) }) },
  people: () => mock ? Promise.resolve(people) : request<DemoPerson[]>('/api/demo/people'),
  profile: (id: string) => mock ? Promise.resolve({ ...profile, employee: { ...profile.employee, employee_id: id } }) : request<Profile>(`/api/employees/${id}`),
  recommendations: async (id: string, mode: 'rules' | 'ai', lang?: string) => { if (mock) { await wait(mode === 'ai' ? 800 : 90); return mode === 'ai' ? aiRecommendations : rulesRecommendations } return request<RecommendationResult>(`/api/employees/${id}/recommendations?mode=${mode}${lang ? `&lang=${lang}` : ''}`) },
  hrOverview: (department?: string) => request<HrOverview>(`/api/hr/overview${department ? `?department=${encodeURIComponent(department)}` : ''}`),
  hrEmployees: (q?: string) => request<{ employee_id: string; full_name: string; role: string; grade: Grade; empty_reason?: string }[]>(`/api/hr/employees${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  importFiles: async (files: File[]) => {
    const body = new FormData()
    for (const file of files) body.append(file.name, file, file.name)
    const token = auth.get()?.token
    const response = await fetch('/api/hr/import', { method: 'POST', headers: token ? { Authorization: `Bearer ${token}` } : {}, body })
    if (!response.ok) throw new Error((await response.text()) || `Import failed (${response.status})`)
    return response.json() as Promise<ImportReport>
  },
  action: async (id: string, event_id: string, action: 'complete' | 'enroll' | 'not_now') => { if (mock) { await wait(350); if (action === 'complete') { profile.skills = profile.skills.map((skill) => skill.skill_id === 'SK_SYSTEM_DESIGN' ? { ...skill, effective: 3, pending_from: ['EV_024'] } : skill); profile.readiness = { ...profile.readiness, pct: 70, critical_met: 2 } } return progress } return request<ProgressUpdate>(`/api/employees/${id}/activities`, { method: 'POST', body: JSON.stringify({ event_id, action }) }) },
}
