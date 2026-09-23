"""Turn engine output into a compact, factual context for the model and define the
strict response schema. The model decides and explains; it never invents numbers."""

from __future__ import annotations

from typing import Any

from app.engine.dataset import Dataset, Json
from app.engine.recommender import _factor_list, scored_pool
from app.engine.skills import effective_skills, gaps, resolve_target, target_profile

FACTOR_KINDS = [
    "critical_gap", "target_gap", "expected_gain", "max_level_cap", "participation_history",
    "format_fit", "availability", "prerequisites", "stale_assessment", "goal_alignment", "workload",
]

SYSTEM_PROMPT = (
    "You are the decision layer of an internal career-development navigator for bank employees. "
    "You receive an employee's promotion target, skill gaps, participation history and a shortlist of "
    "eligible development activities, each already scored with explicit factors. "
    "Choose the 1-3 activities that best help this specific person progress, and explain each choice.\n"
    "Rules:\n"
    "- Pick only from the provided candidate event_ids.\n"
    "- Each pick must cite at least three distinct factor kinds that are present on that candidate.\n"
    "- Respect participation history: if the person repeatedly declined or skipped a format, prefer another "
    "format and say so; recommendations are invitations, never pressure.\n"
    "- Use only numbers given in the context. Never invent skills, levels or events.\n"
    "- Write every rationale in the requested language, second person, encouraging, at most 60 words.\n"
    "- Prefer closing critical gaps, but account for what the person actually engages with."
)

RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["picks", "not_recommended", "summary"],
    "properties": {
        "picks": {
            "type": "array", "minItems": 1, "maxItems": 3,
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["event_id", "rationale", "factors_used"],
                "properties": {
                    "event_id": {"type": "string"},
                    "rationale": {"type": "string"},
                    "factors_used": {"type": "array", "minItems": 3, "items": {"type": "string", "enum": FACTOR_KINDS}},
                },
            },
        },
        "not_recommended": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["label", "reason"],
                "properties": {"label": {"type": "string"}, "reason": {"type": "string"}},
            },
        },
        "summary": {"type": "string"},
    },
}


def build_context(ds: Dataset, employee_id: str, lang: str | None, limit: int = 8) -> dict[str, Any]:
    """Assemble the model context and the per-candidate factor kinds used for validation."""

    employee = ds.employees[employee_id]
    target = resolve_target(ds, employee)
    levels = effective_skills(ds, employee)
    gap_values = gaps(ds, employee, levels, target)
    profile_data = target_profile(ds, target) or {}
    critical = set(profile_data.get("critical_skills", []))
    language = lang or employee.get("preferred_language") or "en"

    top_gaps = sorted(((gap, skill_id) for skill_id, gap in gap_values.items() if gap > 0), reverse=True)
    gaps_ctx = [
        {"skill_id": skill_id, "name": ds.skills.get(skill_id, {}).get("name", skill_id),
         "current": int(levels.get(skill_id, 0)), "required": int(profile_data.get("required_skills", {}).get(skill_id, 0)),
         "critical": skill_id in critical}
        for gap, skill_id in top_gaps[:8]
    ]

    rows = ds.employee_history(employee_id)
    stats = {status: sum(row.get("status") == status for row in rows) for status in
             ("completed", "no_show", "declined", "dropped", "overdue", "in_progress")}

    pool = scored_pool(ds, employee_id, limit)
    candidates_ctx: list[dict[str, Any]] = []
    factor_kinds_by_event: dict[str, set[str]] = {}
    for candidate in pool:
        factors = _factor_list(ds, candidate, levels, target, gap_values)
        factor_kinds_by_event[candidate.event["event_id"]] = {factor.kind for factor in factors}
        candidates_ctx.append({
            "event_id": candidate.event["event_id"], "title": candidate.event["title"],
            "type": candidate.event["type"], "format": candidate.event["format"],
            "score": round(candidate.base_score, 4),
            "expected_gains": [{"skill_id": s, "from": b, "to": a} for s, b, a in candidate.gains],
            "factors": [{"kind": factor.kind, "detail": factor.label} for factor in factors],
        })

    lowest = min(((int(levels.get(skill_id, 0)), skill_id) for skill_id in gap_values), default=(0, None))[1]
    context = {
        "employee": {"role": employee["role"], "grade": employee["grade"], "tenure_months": employee.get("tenure_months"),
                     "work_format": employee.get("work_format")},
        "target": {"role": target.role, "grade": target.grade, "source": target.source},
        "top_gaps": gaps_ctx,
        "participation": stats,
        "naive_baseline_skill": ds.skills.get(lowest, {}).get("name", lowest) if lowest else None,
        "candidates": candidates_ctx,
        "language": language,
    }
    return {"context": context, "factor_kinds_by_event": factor_kinds_by_event,
            "candidate_ids": [c["event_id"] for c in candidates_ctx], "language": language}
