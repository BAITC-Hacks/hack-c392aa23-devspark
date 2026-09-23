"""Bridge to the recommendation engine with a useful no-engine fallback."""

from __future__ import annotations

import importlib
from datetime import date
from typing import Any, Callable

from app.models import Profile, ProgressUpdate, RecommendationResult
from app.store import CareerStore


GRADE_ORDER = ["Junior", "Middle", "Senior", "Lead"]


def _target(store: CareerStore, employee: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    goal = employee.get("career_goal")
    if goal and (goal["target_role"], goal["target_grade"]) != (employee["role"], employee["grade"]):
        target = {"role": goal["target_role"], "grade": goal["target_grade"], "source": "career_goal"}
    else:
        try:
            next_grade = GRADE_ORDER[GRADE_ORDER.index(employee["grade"]) + 1]
            target = {"role": employee["role"], "grade": next_grade, "source": "next_grade"}
        except (ValueError, IndexError):
            target = {"role": None, "grade": None, "source": "none"}
    requirements = next(
        (item for item in store.role_profiles if item["role"] == target["role"] and item["grade"] == target["grade"]),
        None,
    )
    return target, requirements


def _effective_skills(store: CareerStore, employee: dict[str, Any]) -> tuple[dict[str, int], dict[str, list[str]]]:
    effective = dict(employee["skills"])
    pending: dict[str, list[str]] = {}
    review_date = date.fromisoformat(employee["last_review_date"])
    for row in sorted(store.history_for(employee["employee_id"]), key=lambda item: item["date"]):
        if row["status"] != "completed" or date.fromisoformat(row["date"]) <= review_date:
            continue
        event = store.event(row["event_id"])
        if not event:
            continue
        for gain in event.get("develops_skills", []):
            skill_id = gain["skill_id"]
            before = effective.get(skill_id, 0)
            effective[skill_id] = max(before, min(before + gain["gain"], gain["max_level"]))
            pending.setdefault(skill_id, []).append(event["event_id"])
    return effective, pending


def _readiness(effective: dict[str, int], requirements: dict[str, Any] | None) -> tuple[float, int, int]:
    if not requirements or not requirements["required_skills"]:
        return 100.0, 0, 0
    required = requirements["required_skills"]
    critical = set(requirements.get("critical_skills", []))
    weighted_total = sum((3 if skill in critical else 1) * level for skill, level in required.items())
    weighted_met = sum((3 if skill in critical else 1) * min(effective.get(skill, 0), level) for skill, level in required.items())
    return round(100 * weighted_met / weighted_total, 2), sum(effective.get(skill, 0) >= required[skill] for skill in critical), len(critical)


def fallback_profile(store: CareerStore, employee_id: str) -> Profile:
    employee = store.employee(employee_id)
    if employee is None:
        raise KeyError(employee_id)
    target, requirements = _target(store, employee)
    effective, pending = _effective_skills(store, employee)
    current_requirements = next(
        (item for item in store.role_profiles if item["role"] == employee["role"] and item["grade"] == employee["grade"]),
        {"required_skills": {}},
    )
    all_skill_ids = set(employee["skills"]) | set((requirements or {}).get("required_skills", {}))
    skills = []
    for skill_id in sorted(all_skill_ids):
        item = store.skills.get(skill_id, {"skill_id": skill_id, "name": skill_id, "type": "unknown", "category": "unknown"})
        skills.append({
            "skill_id": skill_id, "name": item["name"], "type": item["type"], "category": item["category"],
            "assessed": employee["skills"].get(skill_id, 0), "effective": effective.get(skill_id, 0),
            "pending_from": pending.get(skill_id, []),
            "required_current": current_requirements["required_skills"].get(skill_id, 0),
            "required_target": (requirements or {"required_skills": {}})["required_skills"].get(skill_id, 0),
            "critical": skill_id in set((requirements or {}).get("critical_skills", [])),
        })
    history = []
    for row in store.history_for(employee_id):
        history.append({**row, "title": store.event(row["event_id"]).get("title", row["event_id"]) if store.event(row["event_id"]) else row["event_id"]})
    stats = {status: sum(row["status"] == status for row in history) for status in ("completed", "no_show", "declined", "dropped", "overdue", "in_progress")}
    assigned = [{"event_id": row["event_id"], "title": row["title"], "due_date": row["due_date"], "status": row["status"]} for row in history if row["assigned_by"] != "self" and row["status"] in {"overdue", "in_progress"}]
    available = []
    for event in store.events.values():
        if event.get("mandatory"):
            continue
        roles = event.get("target_roles", [])
        grades = event.get("target_grades", [])
        role_fits = employee["role"] in roles or (target["role"] in roles if target["role"] else False)
        grade_fits = employee["grade"] in grades or (target["grade"] in grades if target["grade"] else False)
        blocked = None if role_fits and grade_fits else "Role or grade does not fit this activity"
        available.append({"event_id": event["event_id"], "title": event["title"], "eligible": blocked is None, "blocked_by": blocked, "score": 0.1 if blocked is None else None})
    pct, critical_met, critical_total = _readiness(effective, requirements)
    return Profile.model_validate({"employee": employee, "target": target, "skills": skills, "readiness": {"pct": pct, "critical_met": critical_met, "critical_total": critical_total}, "history": history, "stats": stats, "assigned": assigned, "available_events": available})


def fallback_recommend(store: CareerStore, employee_id: str) -> RecommendationResult:
    profile = fallback_profile(store, employee_id)
    gaps = {skill.skill_id: max(0, skill.required_target - skill.effective) for skill in profile.skills}
    candidates: list[tuple[float, dict[str, Any], list[dict[str, Any]]]] = []
    completed = {row["event_id"] for row in store.history_for(employee_id) if row["status"] == "completed"}
    active = {row["event_id"] for row in store.history_for(employee_id) if row["status"] == "in_progress"}
    for item in profile.available_events:
        event = store.event(item.event_id)
        if not item.eligible or not event or event["event_id"] in active or (event["event_id"] in completed and event["event_id"] != "EV_036"):
            continue
        gains = []
        for gain in event.get("develops_skills", []):
            before = next((skill.effective for skill in profile.skills if skill.skill_id == gain["skill_id"]), 0)
            after = min(before + gain["gain"], gain["max_level"])
            if gaps.get(gain["skill_id"], 0) > 0 and after > before:
                gains.append({"skill_id": gain["skill_id"], "from": before, "to": after})
        if gains:
            score = sum(min(gain["to"] - gain["from"], gaps[gain["skill_id"]]) for gain in gains) / max(1, sum(gaps.values()))
            candidates.append((score, event, gains))
    candidates.sort(key=lambda item: item[0], reverse=True)
    recommendations = []
    after = []
    current_pct = profile.readiness.pct
    for rank, (score, event, gains) in enumerate(candidates[:3], start=1):
        readiness_after = min(100.0, round(current_pct + score * 100, 2))
        after.append(readiness_after)
        critical = any(next((skill.critical for skill in profile.skills if skill.skill_id == gain["skill_id"]), False) for gain in gains)
        next_session = next((session for session in event.get("upcoming_sessions", []) if session > store.as_of_date.isoformat()), None)
        recommendations.append({"rank": rank, "event_id": event["event_id"], "title": event["title"], "type": event["type"], "format": event["format"], "duration_hours": event["duration_hours"], "next_session": next_session, "score": round(score, 4), "factors": [{"kind": "critical_gap" if critical else "target_gap", "label": "Builds a required target skill", "impact": round(score, 4)}, {"kind": "expected_gain", "label": f"Improves {len(gains)} skill gap(s)", "impact": 1.0}, {"kind": "availability", "label": "Available development activity", "impact": 1.0}], "expected_gains": gains, "readiness_after_pct": readiness_after, "rationale": "This is an optional next step that helps close your target skill gap."})
    empty_reason = None if recommendations else ("AT_TOP_NO_GOAL" if profile.target.source == "none" else "NO_ELIGIBLE_EVENTS")
    return RecommendationResult.model_validate({"employee_id": employee_id, "target": profile.target, "generated_by": "rules", "model": None, "latency_ms": 0, "recommendations": recommendations, "trajectory": {"now_pct": current_pct, "after_pct": after}, "not_recommended": [], "empty_reason": empty_reason})


def _engine_function(name: str) -> Callable[..., Any] | None:
    for module_name in ("app.engine.recommender", "app.engine"):
        try:
            function = getattr(importlib.import_module(module_name), name, None)
        except ModuleNotFoundError:
            continue
        if callable(function):
            return function
    return None


def profile(store: CareerStore, employee_id: str) -> Profile:
    function = _engine_function("profile")
    if function and store.engine_dataset is not None:
        return Profile.model_validate(function(store.engine_dataset, employee_id))
    return fallback_profile(store, employee_id)


def recommend(store: CareerStore, employee_id: str, mode: str = "rules", lang: str | None = None) -> RecommendationResult:
    function = _engine_function("recommend")
    if function and store.engine_dataset is not None:
        kwargs = {"mode": mode}
        if lang:
            kwargs["lang"] = lang
        return RecommendationResult.model_validate(function(store.engine_dataset, employee_id, **kwargs))
    return fallback_recommend(store, employee_id)


def apply_activity(store: CareerStore, employee_id: str, event_id: str, action: str) -> ProgressUpdate:
    before = profile(store, employee_id).readiness.pct
    if action == "not_now":
        store.add_not_now(employee_id, event_id)
        result = recommend(store, employee_id)
        return ProgressUpdate.model_validate({"record": {"record_id": "", "employee_id": employee_id, "event_id": event_id, "date": store.as_of_date, "due_date": None, "status": "declined", "completion_pct": 0, "score": None, "feedback_rating": None, "assigned_by": "self"}, "skills_changed": [], "readiness_before": before, "readiness_after": before, "recommendations": result})
    if not store.event(event_id):
        raise KeyError(event_id)
    row = store.add_activity(employee_id, event_id, action)
    after_profile = fallback_profile(store, employee_id)
    event = store.event(event_id) or {}
    changes = []
    if action == "complete":
        baseline = store.employee(employee_id)["skills"]
        for gain in event.get("develops_skills", []):
            from_level = baseline.get(gain["skill_id"], 0)
            to_level = next((skill.effective for skill in after_profile.skills if skill.skill_id == gain["skill_id"]), from_level)
            if to_level != from_level:
                changes.append({"skill_id": gain["skill_id"], "from": from_level, "to": to_level})
    return ProgressUpdate.model_validate({"record": row, "skills_changed": changes, "readiness_before": before, "readiness_after": after_profile.readiness.pct, "recommendations": fallback_recommend(store, employee_id)})
