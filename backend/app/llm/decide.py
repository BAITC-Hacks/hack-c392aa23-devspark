"""AI decision layer: the model picks 1-3 of the engine's shortlist and explains them.
Strictly validated, retried once, and it falls back to rules on any failure."""

from __future__ import annotations

import hashlib
import json
import logging
from time import perf_counter
from typing import Any

from app.engine.dataset import Dataset
from app.engine.recommender import recommend_for_events
from app.models import RecommendationResult

from .client import get_client, model_name
from .prompt import RESPONSE_SCHEMA, SYSTEM_PROMPT, build_context

logger = logging.getLogger("careerquest.llm")
_CACHE: dict[str, RecommendationResult] = {}


def _state_hash(ds: Dataset, employee_id: str, candidate_ids: list[str], language: str) -> str:
    employee = ds.employees[employee_id]
    payload = json.dumps({
        "skills": employee.get("skills"), "review": employee.get("last_review_date"),
        "history": len(ds.employee_history(employee_id)), "candidates": candidate_ids, "lang": language,
    }, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _validate(data: dict[str, Any], candidate_ids: list[str], factor_kinds: dict[str, set[str]]) -> str | None:
    picks = data.get("picks") or []
    if not 1 <= len(picks) <= 3:
        return "Return between 1 and 3 picks."
    seen: set[str] = set()
    for pick in picks:
        event_id = pick.get("event_id")
        if event_id not in candidate_ids:
            return f"event_id {event_id!r} is not one of the candidates {candidate_ids}."
        if event_id in seen:
            return f"event_id {event_id!r} is duplicated."
        seen.add(event_id)
        used = set(pick.get("factors_used") or [])
        if len(used) < 3:
            return f"{event_id} must cite at least three distinct factor kinds."
        unknown = used - factor_kinds.get(event_id, set())
        if unknown:
            return f"{event_id} cites factors {sorted(unknown)} that are not present on it; allowed: {sorted(factor_kinds.get(event_id, set()))}."
    return None


def _call(client, messages: list[dict[str, str]]) -> dict[str, Any]:
    response = client.chat.completions.create(
        model=model_name(), messages=messages, temperature=0,
        response_format={"type": "json_schema", "json_schema": {"name": "recommendations", "schema": RESPONSE_SCHEMA, "strict": True}},
    )
    return json.loads(response.choices[0].message.content)


def ai_recommendation(ds: Dataset, employee_id: str, lang: str | None = None) -> RecommendationResult | None:
    """Return an LLM-decided result, or None to signal the caller should use rules."""

    client = get_client()
    if client is None:
        return None
    built = build_context(ds, employee_id, lang)
    candidate_ids = built["candidate_ids"]
    if not candidate_ids:
        return None
    language = built["language"]
    cache_key = _state_hash(ds, employee_id, candidate_ids, language)
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    started = perf_counter()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(built["context"], ensure_ascii=False)},
    ]
    data: dict[str, Any] | None = None
    try:
        data = _call(client, messages)
        error = _validate(data, candidate_ids, built["factor_kinds_by_event"])
        if error:
            messages.append({"role": "user", "content": f"Your previous answer was invalid: {error} Fix it and return valid JSON."})
            data = _call(client, messages)
            error = _validate(data, candidate_ids, built["factor_kinds_by_event"])
            if error:
                logger.warning("LLM output invalid after retry for %s: %s", employee_id, error)
                return None
    except Exception as exc:  # network, timeout, parse — degrade to rules
        logger.warning("LLM call failed for %s: %s", employee_id, exc)
        return None

    picks = data["picks"]
    latency_ms = round((perf_counter() - started) * 1000)
    result = recommend_for_events(
        ds, employee_id, [pick["event_id"] for pick in picks], lang,
        generated_by="llm", model=model_name(), latency_ms=latency_ms,
    )
    if result is None:
        return None
    rationale_by_event = {pick["event_id"]: pick["rationale"].strip() for pick in picks}
    for recommendation in result.recommendations:
        if recommendation.event_id in rationale_by_event:
            recommendation.rationale = rationale_by_event[recommendation.event_id]
    _CACHE[cache_key] = result
    return result
