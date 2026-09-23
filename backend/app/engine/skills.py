"""Skill state, promotion-target and readiness calculations."""

from __future__ import annotations

from datetime import date
from typing import Iterable

from app.models import Readiness, Target

from .dataset import Dataset, Json


GRADE_ORDER = ("Junior", "Middle", "Senior", "Lead")


class SkillSnapshot(dict[str, int]):
    """Effective levels plus activity IDs awaiting formal review."""

    pending_from: dict[str, list[str]]

    def __init__(self, levels: dict[str, int], pending_from: dict[str, list[str]]):
        super().__init__(levels)
        self.pending_from = pending_from


def _date(value: str | date) -> date:
    return value if isinstance(value, date) else date.fromisoformat(value)


def resolve_target(ds: Dataset, employee: Json) -> Target:
    """Use a distinct career goal, otherwise the next grade in the same role."""

    goal = employee.get("career_goal")
    if goal and (goal.get("target_role"), goal.get("target_grade")) != (employee["role"], employee["grade"]):
        return Target(role=goal["target_role"], grade=goal["target_grade"], source="career_goal")
    try:
        current_index = GRADE_ORDER.index(employee["grade"])
    except ValueError:
        return Target(role=None, grade=None, source="none")
    if current_index == len(GRADE_ORDER) - 1:
        return Target(role=None, grade=None, source="none")
    return Target(role=employee["role"], grade=GRADE_ORDER[current_index + 1], source="next_grade")


def effective_skills(ds: Dataset, employee: Json) -> SkillSnapshot:
    """Apply only post-review completions, in date order, with event caps."""

    levels = {skill_id: int(level) for skill_id, level in employee.get("skills", {}).items()}
    pending: dict[str, list[str]] = {}
    reviewed_on = _date(employee["last_review_date"])
    rows = sorted(ds.employee_history(employee["employee_id"]), key=lambda row: str(row["date"]))
    for row in rows:
        if row.get("status") != "completed" or _date(row["date"]) <= reviewed_on:
            continue
        event = ds.events.get(str(row["event_id"]))
        if not event:
            continue
        for gain in event.get("develops_skills", []):
            skill_id = gain["skill_id"]
            current = levels.get(skill_id, 0)
            levels[skill_id] = max(current, min(current + int(gain["gain"]), int(gain["max_level"])))
            pending.setdefault(skill_id, []).append(event["event_id"])
    return SkillSnapshot(levels, pending)


def target_profile(ds: Dataset, target: Target) -> Json | None:
    if target.source == "none" or target.role is None or target.grade is None:
        return None
    return ds.role_profiles.get((target.role, target.grade))


def gaps(ds: Dataset, employee: Json, levels: dict[str, int] | None = None, target: Target | None = None) -> dict[str, int]:
    """Return non-negative gaps to every skill required by the promotion target."""

    target = target or resolve_target(ds, employee)
    required = (target_profile(ds, target) or {}).get("required_skills", {})
    levels = levels or effective_skills(ds, employee)
    return {skill_id: max(0, int(required_level) - int(levels.get(skill_id, 0))) for skill_id, required_level in required.items()}


def readiness(ds: Dataset, levels: dict[str, int], target: Target) -> Readiness:
    requirements = (target_profile(ds, target) or {})
    required = requirements.get("required_skills", {})
    if not required:
        return Readiness(pct=0.0, critical_met=0, critical_total=0)
    critical = set(requirements.get("critical_skills", []))
    denominator = sum((3 if skill_id in critical else 1) * int(required_level) for skill_id, required_level in required.items())
    numerator = sum(
        (3 if skill_id in critical else 1) * min(int(levels.get(skill_id, 0)), int(required_level))
        for skill_id, required_level in required.items()
    )
    critical_met = sum(int(levels.get(skill_id, 0)) >= int(required[skill_id]) for skill_id in critical)
    return Readiness(pct=round(100 * numerator / denominator, 2) if denominator else 0.0, critical_met=critical_met, critical_total=len(critical))


def apply_event_gains(levels: dict[str, int], event: Json) -> tuple[dict[str, int], list[tuple[str, int, int]]]:
    """Return a copied skill state and the observable capped gains."""

    updated = dict(levels)
    changed: list[tuple[str, int, int]] = []
    for gain in event.get("develops_skills", []):
        skill_id = gain["skill_id"]
        before = int(updated.get(skill_id, 0))
        after = max(before, min(before + int(gain["gain"]), int(gain["max_level"])))
        updated[skill_id] = after
        if after != before:
            changed.append((skill_id, before, after))
    return updated, changed


def trajectory(ds: Dataset, levels: dict[str, int], target: Target, events: Iterable[Json]) -> list[float]:
    """Readiness after each cumulative selected activity."""

    projected = dict(levels)
    values: list[float] = []
    for event in events:
        projected, _ = apply_event_gains(projected, event)
        values.append(readiness(ds, projected, target).pct)
    return values
