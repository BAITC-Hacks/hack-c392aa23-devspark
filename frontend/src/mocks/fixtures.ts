import type { DemoPerson, Profile, ProgressUpdate, Recommendation, RecommendationResult } from '../api/types'

export const people: DemoPerson[] = [
  { employee_id: 'E0028', full_name: 'Aigerim Sarsenova', role: 'Backend Engineer', grade: 'Middle' },
  { employee_id: 'E0002', full_name: 'Arman Zhaksylykov', role: 'Backend Engineer', grade: 'Middle' },
  { employee_id: 'E0003', full_name: 'Symbat Omarova', role: 'Customer Support Specialist', grade: 'Senior' },
]

export const profile: Profile = {
  employee: { employee_id: 'E0028', full_name: 'Aigerim Sarsenova', department: 'Backend Development', role: 'Backend Engineer', grade: 'Middle', manager_id: 'E0034', hire_date: '2023-06-12', tenure_months: 40, work_format: 'remote', preferred_language: 'en', career_goal: { target_role: 'Backend Engineer', target_grade: 'Senior' }, last_review_date: '2026-07-15' },
  target: { role: 'Backend Engineer', grade: 'Senior', source: 'career_goal' },
  readiness: { pct: 61, critical_met: 1, critical_total: 3 },
  skills: [
    { skill_id: 'SK_SYSTEM_DESIGN', name: 'System Design', type: 'hard', category: 'engineering', assessed: 2, effective: 2, pending_from: [], required_current: 2, required_target: 4, critical: true },
    { skill_id: 'SK_CLOUD', name: 'Cloud Platforms', type: 'hard', category: 'engineering', assessed: 2, effective: 3, pending_from: ['EV_031'], required_current: 2, required_target: 4, critical: true },
    { skill_id: 'SK_API_DESIGN', name: 'API Design', type: 'hard', category: 'engineering', assessed: 2, effective: 2, pending_from: [], required_current: 2, required_target: 3, critical: true },
    { skill_id: 'SK_PYTHON', name: 'Python', type: 'hard', category: 'engineering', assessed: 4, effective: 4, pending_from: [], required_current: 3, required_target: 4, critical: false },
    { skill_id: 'SK_OBSERVABILITY', name: 'Observability', type: 'hard', category: 'engineering', assessed: 1, effective: 1, pending_from: [], required_current: 1, required_target: 3, critical: false },
  ],
  history: [
    { record_id: 'R002899', event_id: 'EV_031', title: 'Cloud Fundamentals Lab', date: '2026-08-08', due_date: null, status: 'completed', completion_pct: 100, feedback_rating: 5, assigned_by: 'self' },
    { record_id: 'R002477', event_id: 'EV_019', title: 'API Design in Practice', date: '2026-06-12', due_date: null, status: 'completed', completion_pct: 100, feedback_rating: 4, assigned_by: 'self' },
    { record_id: 'R002122', event_id: 'EV_067', title: 'Secure Coding Essentials', date: '2026-03-19', due_date: null, status: 'declined', completion_pct: 0, assigned_by: 'self' },
  ],
  stats: { completed: 8, no_show: 0, declined: 1, dropped: 0, overdue: 1, in_progress: 0 },
  assigned: [{ event_id: 'EV_001', title: 'Information Security Awareness', due_date: '2026-10-20', status: 'overdue' }],
  available_events: [
    { event_id: 'EV_024', title: 'System Design: Reliable Services', eligible: true, blocked_by: null, score: 0.39 },
    { event_id: 'EV_036', title: 'Architecture Practice Club', eligible: true, blocked_by: null, score: 0.23 },
    { event_id: 'EV_043', title: 'Observability Foundations', eligible: true, blocked_by: null, score: 0.16 },
  ],
}

const recs: Recommendation[] = [
  { rank: 1, event_id: 'EV_024', title: 'System Design: Reliable Services', type: 'workshop', format: 'online', duration_hours: 6, next_session: '2026-10-15', score: 0.39, factors: [{ kind: 'critical_gap', label: 'System Design 2 → 4 required for Senior (critical)', impact: 0.5 }, { kind: 'expected_gain', label: 'Expected gain: System Design 2 → 3', impact: 0.5 }, { kind: 'participation_history', label: '2 positive outcomes on similar learning', impact: 0.75 }, { kind: 'availability', label: 'Next session is in 14 days', impact: 1 }], expected_gains: [{ skill_id: 'SK_SYSTEM_DESIGN', from: 2, to: 3 }], readiness_after_pct: 70, rationale: 'Strengthen your most important Senior-level gap with a focused online workshop. It advances System Design by one level, fits your strong learning history, and has a session available soon.' },
  { rank: 2, event_id: 'EV_036', title: 'Architecture Practice Club', type: 'club', format: 'mentoring', duration_hours: 4, next_session: '2026-10-22', score: 0.23, factors: [{ kind: 'critical_gap', label: 'System Design remains 2 levels below the Senior target', impact: 0.5 }, { kind: 'participation_history', label: 'Mentoring offers a different format after one decline', impact: 0.67 }, { kind: 'format_fit', label: 'Remote-friendly mentoring fit: 0.80', impact: 0.8 }, { kind: 'availability', label: 'Next session is in 21 days', impact: 1 }], expected_gains: [{ skill_id: 'SK_SYSTEM_DESIGN', from: 3, to: 4 }], readiness_after_pct: 79, rationale: 'Continue building System Design through hands-on peer practice. This remote-friendly mentoring format complements the workshop and helps close the remaining critical gap for Senior.' },
  { rank: 3, event_id: 'EV_043', title: 'Observability Foundations', type: 'course', format: 'self_paced', duration_hours: 5, next_session: null, score: 0.16, factors: [{ kind: 'target_gap', label: 'Observability 1 → 3 required for Senior', impact: 0.33 }, { kind: 'expected_gain', label: 'Expected gain: Observability 1 → 2', impact: 0.33 }, { kind: 'format_fit', label: 'Self-paced completion fit: 0.80', impact: 0.8 }, { kind: 'availability', label: 'Self-paced learning is available now', impact: 1 }], expected_gains: [{ skill_id: 'SK_OBSERVABILITY', from: 1, to: 2 }], readiness_after_pct: 85, rationale: 'Add a flexible self-paced course when your schedule allows. It builds the observability foundation expected at Senior level without adding a fixed-session commitment.' },
]

export const rulesRecommendations: RecommendationResult = { employee_id: 'E0028', target: profile.target, generated_by: 'rules', model: null, latency_ms: 18, recommendations: [...recs], trajectory: { now_pct: 61, after_pct: [70, 79, 85] }, not_recommended: [{ skill_id: 'SK_OBSERVABILITY', event_id: 'EV_043', reason: 'Observability is the lowest effective skill, but System Design is critical for Senior and this first step closes a larger weighted target gap.' }], empty_reason: null }
export const aiRecommendations: RecommendationResult = { ...rulesRecommendations, generated_by: 'llm', model: 'career-quest-ai', latency_ms: 536, recommendations: recs.map((r) => ({ ...r, rationale: `${r.rationale} You can choose the pace that works for you.` })) }

export const progress: ProgressUpdate = { record: { event_id: 'EV_024', title: 'System Design: Reliable Services', date: '2026-10-01', status: 'completed', completion_pct: 100, assigned_by: 'self' }, skills_changed: [{ skill_id: 'SK_SYSTEM_DESIGN', from: 2, to: 3 }], readiness_before: 61, readiness_after: 70, recommendations: rulesRecommendations }
