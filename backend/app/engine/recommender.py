"""Public profile, recommendation and progress operations for rules mode."""

from __future__ import annotations

from time import perf_counter
from typing import Literal

from app.models import (
    ActivityHistoryRecord,
    ActivityStats,
    AssignedActivity,
    AvailableEvent,
    ExpectedGain,
    HistoryItem,
    NotRecommended,
    Profile,
    ProfileSkill,
    ProgressUpdate,
    Recommendation,
    RecommendationFactor,
    RecommendationResult,
    SkillChange,
    Target,
    Trajectory,
)

from .candidates import Candidate, evaluate_candidates
from .dataset import Dataset, Json
from .skills import apply_event_gains, effective_skills, gaps, readiness, resolve_target, target_profile, trajectory


def _history_item(ds: Dataset, row: Json) -> HistoryItem:
    return HistoryItem.model_validate({**row, "title": ds.events.get(row["event_id"], {}).get("title", row["event_id"])})


def _stats(rows: list[Json]) -> ActivityStats:
    return ActivityStats(**{status: sum(row.get("status") == status for row in rows) for status in ActivityStats.model_fields})


def _main_skill(candidate: Candidate, gap_values: dict[str, int], critical: set[str]) -> str | None:
    if not candidate.gains:
        return None
    return max(
        candidate.gains,
        key=lambda gain: ((3 if gain[0] in critical else 1) * min(gain[2] - gain[1], gap_values.get(gain[0], 0)), gain[0]),
    )[0]


def _select(candidates: list[Candidate], gap_values: dict[str, int], critical: set[str], k: int) -> list[tuple[Candidate, float]]:
    """Greedily select with a 50% overlap penalty after a main skill is covered."""

    remaining = list(candidates)
    selected: list[tuple[Candidate, float]] = []
    covered: set[str] = set()
    while remaining and len(selected) < k:
        scored = []
        for candidate in remaining:
            main_skill = _main_skill(candidate, gap_values, critical)
            score = candidate.base_score * (0.5 if main_skill in covered else 1.0)
            scored.append((score, candidate.event["event_id"], candidate, main_skill))
        score, _, candidate, main_skill = max(scored, key=lambda value: (value[0], value[1]))
        remaining.remove(candidate)
        # Every candidate reaching selection is eligible and closes a real weighted
        # target gap, so the only worthless score is a non-positive one. An absolute
        # floor would starve high-gap employees, whose per-event gap_value is small
        # because it is normalised by their (large) total remaining gap.
        if score <= 0.0:
            break
        selected.append((candidate, score))
        if main_skill:
            covered.add(main_skill)
    return selected


def _plural(n: int | float, one: str, many: str) -> str:
    return one if n == 1 else many


FORMAT_NAMES = {"online": "Online", "offline": "Offline", "self_paced": "Self-paced"}


def _factor_list(ds: Dataset, candidate: Candidate, levels: dict[str, int], target: Target, gap_values: dict[str, int]) -> list[RecommendationFactor]:
    """Human-readable factors. Labels state facts plainly; the numbers behind the
    score live in `impact` and in the 'How this was calculated' view."""

    profile_data = target_profile(ds, target) or {}
    critical = set(profile_data.get("critical_skills", []))
    factors: list[RecommendationFactor] = []
    for skill_id, before, after in candidate.gains:
        skill = ds.skills.get(skill_id, {"name": skill_id})
        required = int(profile_data.get("required_skills", {}).get(skill_id, 0))
        is_critical = skill_id in critical
        factors.append(RecommendationFactor(
            kind="critical_gap" if is_critical else "target_gap",
            label=f"{target.grade} needs {skill['name']} {required} (you have {before})" + (" · critical" if is_critical else ""),
            impact=round((3 if is_critical else 1) * gap_values.get(skill_id, 0), 3),
        ))
        factors.append(RecommendationFactor(kind="expected_gain", label=f"Raises {skill['name']} {before} → {after}", impact=after - before))
        pending = len(levels.pending_from.get(skill_id, []))
        if pending:
            factors.append(RecommendationFactor(
                kind="stale_assessment", label=f"{skill['name']}: {pending} {_plural(pending, 'completion', 'completions')} awaiting review", impact=float(pending),
            ))
    history = candidate.history
    if history.completed_similar or history.refused_similar:
        participation = f"Similar activities: {history.completed_similar} completed, {history.refused_similar} declined or missed"
    else:
        participation = "No history with similar activities yet"
    factors.append(RecommendationFactor(kind="participation_history", label=participation, impact=round(history.propensity, 3)))
    format_name = FORMAT_NAMES.get(candidate.event["format"], candidate.event["format"])
    if history.format_total:
        format_label = f"{format_name}: you completed {history.format_completion_rate:.0%} of past ones"
    else:
        format_label = f"{format_name}: no history with this format yet"
    if candidate.fit < history.format_completion_rate:
        format_label += " · remote, offline"
    factors.append(RecommendationFactor(kind="format_fit", label=format_label, impact=round(candidate.fit, 3)))
    if candidate.event["format"] == "self_paced":
        availability_label = "Self-paced — start any time"
    elif candidate.next_session:
        availability_label = f"Next session {candidate.next_session.isoformat()}"
    else:
        availability_label = "No session scheduled yet"
    factors.append(RecommendationFactor(kind="availability", label=availability_label, impact=candidate.availability))
    if candidate.unlocks:
        factors.append(RecommendationFactor(kind="prerequisites", label=f"Unlocks {', '.join(candidate.unlocks[:3])}", impact=float(len(candidate.unlocks))))
    if history.workload:
        factors.append(RecommendationFactor(kind="workload", label=f"{history.workload} {_plural(history.workload, 'activity', 'activities')} already open", impact=-float(history.workload)))
    return factors


def _rationale(employee: Json, candidate: Candidate, target: Target, lang: str | None = None) -> str:
    # Rules-mode text remains an invitation and honors the employee's UI language.
    templates = {
        "en": f"You can build progress toward {target.grade} with {candidate.event['title']}; it directly closes a current skill gap.",
        "ru": f"Вы можете продвинуться к уровню {target.grade} с {candidate.event['title']}; активность закрывает текущий дефицит навыка.",
        "kk": f"{candidate.event['title']} арқылы {target.grade} деңгейіне жақындай аласыз; ол қазіргі дағды алшақтығын жабады.",
    }
    return templates.get(lang or employee.get("preferred_language"), templates["en"])


def _empty_reason(ds: Dataset, employee: Json, candidates: list[Candidate], target: Target, gap_values: dict[str, int]) -> str:
    if target.source == "none":
        return "AT_TOP_NO_GOAL"
    if not any(gap_values.values()):
        return "TARGET_REACHED"
    non_mandatory = [item for item in candidates if item.blocked_by != "MANDATORY_ASSIGNED"]
    if non_mandatory and all(item.blocked_by == "LOW_ENGAGEMENT_FORMAT" for item in non_mandatory):
        return "LOW_ENGAGEMENT"
    if non_mandatory and all((item.blocked_by or "").startswith("PREREQUISITES:") for item in non_mandatory):
        return "PREREQUISITES_BLOCKED"
    return "NO_ELIGIBLE_EVENTS"


def profile(ds: Dataset, employee_id: str) -> Profile:
    employee = ds.employees[employee_id]
    target = resolve_target(ds, employee)
    levels = effective_skills(ds, employee)
    current_requirements = ds.role_profiles.get((employee["role"], employee["grade"]), {}).get("required_skills", {})
    target_data = target_profile(ds, target) or {}
    target_requirements = target_data.get("required_skills", {})
    critical = set(target_data.get("critical_skills", []))
    skill_ids = sorted(set(employee.get("skills", {})) | set(target_requirements) | set(levels.pending_from))
    skill_models = [ProfileSkill(
        skill_id=skill_id, name=ds.skills.get(skill_id, {}).get("name", skill_id), type=ds.skills.get(skill_id, {}).get("type", "unknown"),
        category=ds.skills.get(skill_id, {}).get("category", "unknown"), assessed=int(employee.get("skills", {}).get(skill_id, 0)),
        effective=int(levels.get(skill_id, 0)), pending_from=levels.pending_from.get(skill_id, []),
        required_current=int(current_requirements.get(skill_id, 0)), required_target=int(target_requirements.get(skill_id, 0)), critical=skill_id in critical,
    ) for skill_id in skill_ids]
    rows = ds.employee_history(employee_id)
    candidates = evaluate_candidates(ds, employee)
    assigned = [AssignedActivity(event_id=row["event_id"], title=ds.events.get(row["event_id"], {}).get("title", row["event_id"]), due_date=row.get("due_date"), status=row["status"])
                for row in rows if ds.events.get(row["event_id"], {}).get("mandatory") and row.get("status") != "completed"]
    return Profile(
        employee=employee, target=target, skills=skill_models, readiness=readiness(ds, levels, target),
        history=[_history_item(ds, row) for row in rows], stats=_stats(rows), assigned=assigned,
        available_events=[AvailableEvent(event_id=item.event["event_id"], title=item.event["title"], eligible=item.eligible, blocked_by=item.blocked_by, score=round(item.base_score, 6) if item.eligible else None) for item in candidates],
    )


def _build_recommendation(ds: Dataset, employee: Json, candidate: Candidate, rank: int, score: float, after_pct: float, levels, target: Target, gap_values: dict[str, int], lang: str | None) -> Recommendation:
    """Assemble one explained Recommendation. Shared by rules and AI selection so
    both paths carry identical factors, gains and readiness projections."""

    return Recommendation(
        rank=rank, event_id=candidate.event["event_id"], title=candidate.event["title"], type=candidate.event["type"],
        format=candidate.event["format"], duration_hours=float(candidate.event["duration_hours"]), next_session=candidate.next_session,
        score=round(score, 6), factors=_factor_list(ds, candidate, levels, target, gap_values),
        expected_gains=[ExpectedGain(skill_id=skill_id, **{"from": before}, to=after) for skill_id, before, after in candidate.gains],
        readiness_after_pct=after_pct, rationale=_rationale(employee, candidate, target, lang),
    )


def _baseline_not_recommended(ds: Dataset, recommendations: list[Recommendation], levels, gap_values: dict[str, int]) -> list[NotRecommended]:
    """Contrast the top pick with the naive 'lowest skill' rule for explainability."""

    if not (recommendations and gap_values):
        return []
    lowest = min((int(levels.get(skill_id, 0)), skill_id) for skill_id in gap_values)[1]
    if lowest in {gain.skill_id for gain in recommendations[0].expected_gains}:
        return []
    skill_name = ds.skills.get(lowest, {}).get("name", lowest)
    return [NotRecommended(skill_id=lowest, event_id=None, reason=f"Naive lowest skill is {skill_name} at {levels.get(lowest, 0)}, but {recommendations[0].title} closes a higher weighted target gap with fit and availability.")]


def _prepare(ds: Dataset, employee_id: str):
    employee = ds.employees[employee_id]
    target = resolve_target(ds, employee)
    levels = effective_skills(ds, employee)
    gap_values = gaps(ds, employee, levels, target)
    candidates = evaluate_candidates(ds, employee)
    critical = set((target_profile(ds, target) or {}).get("critical_skills", []))
    return employee, target, levels, gap_values, candidates, critical


def scored_pool(ds: Dataset, employee_id: str, limit: int = 8) -> list[Candidate]:
    """Top eligible candidates by base score — the shortlist the AI layer chooses from."""

    _, _, _, _, candidates, _ = _prepare(ds, employee_id)
    eligible = [item for item in candidates if item.eligible]
    eligible.sort(key=lambda item: (item.base_score, item.event["event_id"]), reverse=True)
    return eligible[:limit]


def recommend(ds: Dataset, employee_id: str, k: int = 3, mode: Literal["rules", "ai"] = "rules", lang: str | None = None) -> RecommendationResult:
    """Generate explainable deterministic recommendations (AI is layered elsewhere)."""

    started = perf_counter()
    employee, target, levels, gap_values, candidates, critical = _prepare(ds, employee_id)
    chosen = _select([item for item in candidates if item.eligible], gap_values, critical, max(0, min(k, 3)))
    projected = trajectory(ds, levels, target, [candidate.event for candidate, _ in chosen])
    recommendations = [
        _build_recommendation(ds, employee, candidate, rank, score, after_pct, levels, target, gap_values, lang)
        for rank, ((candidate, score), after_pct) in enumerate(zip(chosen, projected), start=1)
    ]
    return RecommendationResult(
        employee_id=employee_id, target=target, generated_by="rules", model=None,
        latency_ms=round((perf_counter() - started) * 1000), recommendations=recommendations,
        trajectory=Trajectory(now_pct=readiness(ds, levels, target).pct, after_pct=projected),
        not_recommended=_baseline_not_recommended(ds, recommendations, levels, gap_values),
        empty_reason=None if recommendations else _empty_reason(ds, employee, candidates, target, gap_values),
    )


def recommend_for_events(ds: Dataset, employee_id: str, event_ids: list[str], lang: str | None = None, generated_by: str = "llm", model: str | None = None, latency_ms: int = 0) -> RecommendationResult | None:
    """Build a result for an explicit ordered set of event ids (the AI layer's picks).

    Returns None when none of the ids are eligible, so the caller can fall back to rules."""

    employee, target, levels, gap_values, candidates, _ = _prepare(ds, employee_id)
    by_id = {item.event["event_id"]: item for item in candidates if item.eligible}
    chosen = [by_id[event_id] for event_id in event_ids if event_id in by_id][:3]
    if not chosen:
        return None
    projected = trajectory(ds, levels, target, [candidate.event for candidate in chosen])
    recommendations = [
        _build_recommendation(ds, employee, candidate, rank, candidate.base_score, after_pct, levels, target, gap_values, lang)
        for rank, (candidate, after_pct) in enumerate(zip(chosen, projected), start=1)
    ]
    return RecommendationResult(
        employee_id=employee_id, target=target, generated_by=generated_by, model=model, latency_ms=latency_ms,
        recommendations=recommendations, trajectory=Trajectory(now_pct=readiness(ds, levels, target).pct, after_pct=projected),
        not_recommended=_baseline_not_recommended(ds, recommendations, levels, gap_values), empty_reason=None,
    )


def _next_record_id(ds: Dataset) -> str:
    numeric = [int(row["record_id"][1:]) for row in ds.history if str(row.get("record_id", "")).startswith("R") and str(row["record_id"])[1:].isdigit()]
    return f"R{max(numeric, default=0) + 1:06d}"


def apply_activity(ds: Dataset, employee_id: str, event_id: str, action: Literal["complete", "enroll", "not_now"]) -> ProgressUpdate:
    """Record a voluntary action in-memory and return its resulting rules recommendation."""

    if employee_id not in ds.employees:
        raise KeyError(employee_id)
    if event_id not in ds.events:
        raise KeyError(event_id)
    employee = ds.employees[employee_id]
    target = resolve_target(ds, employee)
    before = effective_skills(ds, employee)
    readiness_before = readiness(ds, before, target).pct
    status = "completed" if action == "complete" else "in_progress" if action == "enroll" else "declined"
    record: Json = {"record_id": _next_record_id(ds), "employee_id": employee_id, "event_id": event_id, "date": ds.as_of_date, "due_date": None, "status": status, "completion_pct": 100 if action == "complete" else 0, "score": None, "feedback_rating": None, "assigned_by": "self"}
    # not_now is represented as a non-persistent, soft negative record to the caller;
    # the platform store writes its feedback.jsonl instead of appending this row.
    if action != "not_now":
        ds.history.append(record)
        ds.history.sort(key=lambda row: (str(row["date"]), str(row["employee_id"]), str(row["event_id"])))
    after = effective_skills(ds, employee)
    changes = []
    if action == "complete":
        _, raw_changes = apply_event_gains(before, ds.events[event_id])
        changes = [SkillChange(skill_id=skill_id, **{"from": old}, to=new) for skill_id, old, new in raw_changes]
    return ProgressUpdate(
        record=ActivityHistoryRecord.model_validate(record), skills_changed=changes, readiness_before=readiness_before,
        readiness_after=readiness(ds, after, target).pct, recommendations=recommend(ds, employee_id, mode="rules"),
    )
