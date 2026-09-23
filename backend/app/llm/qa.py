"""Grounded Q&A: the employee asks about their own development plan and the model
answers strictly from engine-provided facts. Falls back to a templated answer."""

from __future__ import annotations

import json
import logging
from time import perf_counter
from typing import Any

from app.engine.dataset import Dataset
from app.engine.recommender import recommend
from app.engine.skills import effective_skills, gaps, resolve_target, target_profile

from .client import get_client, model_name

logger = logging.getLogger("careerquest.llm")

SYSTEM_PROMPT = (
    "You are a supportive career-development assistant for a bank employee. Answer the employee's "
    "question using ONLY the facts provided about their plan. If the facts do not contain the answer, "
    "say you don't have that information and suggest they ask their manager or HR. "
    "Never invent skills, levels, events or numbers. Be concise (<=80 words), second person, "
    "encouraging and free of pressure. Reply in the requested language."
)


def _facts(ds: Dataset, employee_id: str, lang: str | None) -> dict[str, Any]:
    employee = ds.employees[employee_id]
    target = resolve_target(ds, employee)
    levels = effective_skills(ds, employee)
    gap = gaps(ds, employee, levels, target)
    profile_data = target_profile(ds, target) or {}
    critical = set(profile_data.get("critical_skills", []))
    result = recommend(ds, employee_id, lang=lang)
    rows = ds.employee_history(employee_id)
    stats = {status: sum(row.get("status") == status for row in rows) for status in ("completed", "declined", "no_show", "dropped")}
    top_gaps = sorted(((g, s) for s, g in gap.items() if g > 0), reverse=True)[:6]
    return {
        "you": {"role": employee["role"], "grade": employee["grade"], "target": {"role": target.role, "grade": target.grade}},
        "gaps": [{"skill": ds.skills.get(s, {}).get("name", s), "have": int(levels.get(s, 0)),
                  "need": int(profile_data.get("required_skills", {}).get(s, 0)), "critical": s in critical} for _, s in top_gaps],
        "recommendations": [{"title": r.title, "why": [f.label for f in r.factors][:4],
                             "gains": [f"{g.skill_id} {g.model_dump(by_alias=True)['from']}->{g.to}" for g in r.expected_gains]} for r in result.recommendations],
        "not_recommended": [n.reason for n in result.not_recommended],
        "participation": stats,
        "language": lang or employee.get("preferred_language") or "en",
    }


def _template_answer(facts: dict[str, Any]) -> str:
    if facts["recommendations"]:
        first = facts["recommendations"][0]
        return f"Your suggested next step is {first['title']} because {', '.join(first['why'][:2])}. It is an invitation, not an obligation."
    return "You have no open recommended step right now. This is a good moment to agree a goal with your manager."


def answer_question(ds: Dataset, employee_id: str, question: str, lang: str | None = None) -> dict[str, Any]:
    """Return {answer, generated_by, model, latency_ms}. Never raises for LLM issues."""

    facts = _facts(ds, employee_id, lang)
    client = get_client()
    if client is None or not question.strip():
        return {"answer": _template_answer(facts), "generated_by": "rules", "model": None, "latency_ms": 0}
    started = perf_counter()
    try:
        response = client.chat.completions.create(
            model=model_name(), temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "Facts:\n" + json.dumps(facts, ensure_ascii=False) + f"\n\nQuestion: {question.strip()}"},
            ],
        )
        answer = (response.choices[0].message.content or "").strip()
        if not answer:
            raise ValueError("empty answer")
        return {"answer": answer, "generated_by": "llm", "model": model_name(), "latency_ms": round((perf_counter() - started) * 1000)}
    except Exception as exc:
        logger.warning("QA failed for %s: %s", employee_id, exc)
        return {"answer": _template_answer(facts), "generated_by": "rules", "model": None, "latency_ms": 0}
