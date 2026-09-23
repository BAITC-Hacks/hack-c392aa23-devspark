"""Eligibility and participation features for development activities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .dataset import Dataset, Json
from .skills import SkillSnapshot, effective_skills, gaps, resolve_target


NEGATIVE_STATUSES = {"declined", "no_show", "dropped"}


@dataclass
class HistoryFeatures:
    positive: float = 0.0
    negative: float = 0.0
    negative_for_format: float = 0.0
    format_completion_rate: float = 0.8
    workload: int = 0
    # Raw counts for human-readable explanations (the fields above are weighted).
    completed_similar: int = 0
    refused_similar: int = 0
    format_total: int = 0

    @property
    def propensity(self) -> float:
        return (1 + self.positive) / (2 + self.positive + self.negative)


@dataclass
class Candidate:
    event: Json
    eligible: bool
    blocked_by: str | None
    next_session: date | None = None
    history: HistoryFeatures = field(default_factory=HistoryFeatures)
    gains: list[tuple[str, int, int]] = field(default_factory=list)
    gap_value: float = 0.0
    fit: float = 0.8
    availability: float = 1.0
    unlocks: list[str] = field(default_factory=list)

    @property
    def base_score(self) -> float:
        return self.gap_value * (0.5 + 0.5 * self.history.propensity) * self.fit * self.availability


def _date(value: str | date) -> date:
    return value if isinstance(value, date) else date.fromisoformat(value)


def _next_session(ds: Dataset, event: Json) -> date | None:
    future = [_date(item) for item in event.get("upcoming_sessions", []) if _date(item) > _date(ds.as_of_date)]
    return min(future) if future else None


def _similar(candidate: Json, past_event: Json) -> bool:
    candidate_skills = {item["skill_id"] for item in candidate.get("develops_skills", [])}
    past_skills = {item["skill_id"] for item in past_event.get("develops_skills", [])}
    return bool(candidate_skills & past_skills) or (
        candidate.get("type") == past_event.get("type") and candidate.get("format") == past_event.get("format")
    )


def _history_features(ds: Dataset, employee: Json, event: Json) -> HistoryFeatures:
    as_of = _date(ds.as_of_date)
    twelve_months_ago = date(as_of.year - 1, as_of.month, as_of.day)
    positive = negative = negative_for_format = 0.0
    completed_for_format = total_for_format = 0
    completed_similar = refused_similar = 0
    workload = 0
    for row in ds.employee_history(employee["employee_id"]):
        status = row.get("status")
        past_event = ds.events.get(str(row.get("event_id")))
        if status == "in_progress" or (status == "overdue" and past_event and past_event.get("mandatory")):
            workload += 1
        if past_event and past_event.get("format") == event.get("format") and status in {"completed", *NEGATIVE_STATUSES}:
            total_for_format += 1
            completed_for_format += status == "completed"
        if not past_event or not _similar(event, past_event):
            continue
        weight = 1.0 if _date(row["date"]) >= twelve_months_ago else 0.5
        if status == "completed":
            completed_similar += 1
            positive += weight
            if row.get("assigned_by") == "self" and (row.get("feedback_rating") or 0) >= 4:
                positive += weight
        elif status in NEGATIVE_STATUSES:
            refused_similar += 1
            negative += weight
            if past_event.get("format") == event.get("format"):
                # History remains similar across skill/type, but the opt-out rule
                # suppresses only the format that repeatedly did not work.
                negative_for_format += weight
    rate = completed_for_format / total_for_format if total_for_format else 0.8
    return HistoryFeatures(positive=positive, negative=negative, negative_for_format=negative_for_format, format_completion_rate=rate, workload=workload,
                           completed_similar=completed_similar, refused_similar=refused_similar, format_total=total_for_format)


def _role_fits(employee: Json, event: Json) -> bool:
    if employee["role"] in event.get("target_roles", []):
        return True
    goal = employee.get("career_goal") or {}
    return bool(goal and goal.get("target_role") != employee["role"] and goal.get("target_role") in event.get("target_roles", []))


def _grade_fits(employee: Json, target_grade: str | None, event: Json) -> bool:
    return employee["grade"] in event.get("target_grades", []) or target_grade in event.get("target_grades", [])


def _unlocks(ds: Dataset, event: Json, levels: SkillSnapshot) -> list[str]:
    hypothetical = dict(levels)
    for gain in event.get("develops_skills", []):
        skill_id = gain["skill_id"]
        hypothetical[skill_id] = max(hypothetical.get(skill_id, 0), min(hypothetical.get(skill_id, 0) + gain["gain"], gain["max_level"]))
    unlocked: list[str] = []
    for other in ds.events.values():
        missing_before = any(levels.get(skill_id, 0) < needed for skill_id, needed in other.get("prerequisites", {}).items())
        met_after = all(hypothetical.get(skill_id, 0) >= needed for skill_id, needed in other.get("prerequisites", {}).items())
        if missing_before and met_after:
            unlocked.append(other["event_id"])
    return sorted(unlocked)


def evaluate_candidates(ds: Dataset, employee: Json) -> list[Candidate]:
    """Return one evaluation per catalog event, including its first rejection reason."""

    target = resolve_target(ds, employee)
    levels = effective_skills(ds, employee)
    employee_gaps = gaps(ds, employee, levels, target)
    target_profile = ds.role_profiles.get((target.role, target.grade)) if target.role and target.grade else None
    required = (target_profile or {}).get("required_skills", {})
    critical = set((target_profile or {}).get("critical_skills", []))
    history_rows = ds.employee_history(employee["employee_id"])
    result: list[Candidate] = []
    for event in ds.events.values():
        history = _history_features(ds, employee, event)
        next_session = _next_session(ds, event)
        blocked: str | None = None
        if target.source == "none":
            blocked = "NO_PROMOTION_TARGET"
        elif event.get("mandatory"):
            blocked = "MANDATORY_ASSIGNED"
        elif not _role_fits(employee, event):
            blocked = "ROLE_MISMATCH"
        elif not _grade_fits(employee, target.grade, event):
            blocked = "GRADE_MISMATCH"
        else:
            unmet = [skill_id for skill_id, required_level in event.get("prerequisites", {}).items() if levels.get(skill_id, 0) < required_level]
            if unmet:
                blocked = "PREREQUISITES: " + ", ".join(unmet)
            elif any(row.get("event_id") == event["event_id"] and row.get("status") == "in_progress" for row in history_rows):
                blocked = "IN_PROGRESS_CONTINUE"
            elif event["event_id"] != "EV_036" and any(row.get("event_id") == event["event_id"] and row.get("status") == "completed" for row in history_rows):
                blocked = "ALREADY_COMPLETED"
            elif event.get("format") != "self_paced" and next_session is None:
                blocked = "NO_UPCOMING_SESSION"
            elif history.negative_for_format >= 3:
                blocked = "LOW_ENGAGEMENT_FORMAT"
            elif not target_profile:
                blocked = "TARGET_PROFILE_MISSING"
        gains: list[tuple[str, int, int]] = []
        if blocked is None:
            for gain in event.get("develops_skills", []):
                skill_id = gain["skill_id"]
                before = int(levels.get(skill_id, 0))
                after = max(before, min(before + int(gain["gain"]), int(gain["max_level"])))
                if employee_gaps.get(skill_id, 0) > 0 and after > before:
                    gains.append((skill_id, before, after))
            if not gains:
                blocked = "NO_TARGET_GAP_OR_MAX_LEVEL_CAP"
        gap_value = 0.0
        if gains and required:
            denominator = sum((3 if skill_id in critical else 1) * gap for skill_id, gap in employee_gaps.items())
            gap_value = sum(
                (3 if skill_id in critical else 1) * min(after - before, employee_gaps[skill_id])
                for skill_id, before, after in gains
            ) / denominator if denominator else 0.0
        availability = 1.0
        if event.get("format") != "self_paced" and next_session:
            days = (next_session - _date(ds.as_of_date)).days
            availability = 1.0 if days <= 45 else 0.8 if days <= 90 else 0.5
        fit = history.format_completion_rate
        if employee.get("work_format") == "remote" and event.get("format") == "offline":
            fit *= 0.7
        fit = round(fit, 6)
        candidate = Candidate(
            event=event, eligible=blocked is None, blocked_by=blocked, next_session=next_session,
            history=history, gains=gains, gap_value=gap_value, fit=fit, availability=availability,
            unlocks=_unlocks(ds, event, levels) if blocked is None else [],
        )
        result.append(candidate)
    return result
