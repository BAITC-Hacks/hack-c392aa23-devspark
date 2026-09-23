from __future__ import annotations

from app.engine.candidates import evaluate_candidates
from app.engine.dataset import Dataset
from app.engine.recommender import recommend
from app.engine.skills import effective_skills, resolve_target

AS_OF = "2026-10-01"


def event(event_id: str, *, skill: str = "SK_A", gain: int = 1, cap: int = 5, format: str = "online", **extra):
    value = {"event_id": event_id, "title": event_id, "type": "course", "format": format, "duration_hours": 1, "mandatory": False, "target_roles": ["Engineer"], "target_grades": ["Junior", "Middle"], "develops_skills": [{"skill_id": skill, "gain": gain, "max_level": cap}], "prerequisites": {}, "upcoming_sessions": [] if format == "self_paced" else ["2026-10-10"]}
    value.update(extra)
    return value


def history(record_id: str, event_id: str, status: str, date: str = "2026-09-20", **extra):
    value = {"record_id": record_id, "employee_id": "E1", "event_id": event_id, "date": date, "due_date": None, "status": status, "completion_pct": 100 if status == "completed" else 0, "score": None, "feedback_rating": None, "assigned_by": "self"}
    value.update(extra)
    return value


def dataset(*events, employee=None, history_rows=(), critical=()):
    employee = employee or {"employee_id": "E1", "full_name": "Test", "department": "D", "role": "Engineer", "grade": "Junior", "manager_id": None, "hire_date": "2025-01-01", "tenure_months": 21, "work_format": "office", "preferred_language": "en", "career_goal": None, "skills": {"SK_A": 1, "SK_B": 1}, "last_review_date": "2026-09-01"}
    profiles = {("Engineer", "Junior"): {"role": "Engineer", "grade": "Junior", "required_skills": {"SK_A": 1, "SK_B": 1}, "critical_skills": []}, ("Engineer", "Middle"): {"role": "Engineer", "grade": "Middle", "required_skills": {"SK_A": 3, "SK_B": 3}, "critical_skills": list(critical)}, ("Other", "Middle"): {"role": "Other", "grade": "Middle", "required_skills": {"SK_A": 3, "SK_B": 3}, "critical_skills": []}}
    skills = {key: {"skill_id": key, "name": key, "type": "hard", "category": "test"} for key in ("SK_A", "SK_B")}
    return Dataset(meta={"as_of_date": AS_OF}, proficiency_scale={}, skills=skills, role_profiles=profiles, employees={"E1": employee}, events={item["event_id"]: item for item in events}, history=list(history_rows))


def candidate(ds, event_id):
    return next(item for item in evaluate_candidates(ds, ds.employees["E1"]) if item.event["event_id"] == event_id)


def test_effective_skills_apply_post_review_completion_and_mark_pending():
    ds = dataset(event("EV_POST", gain=2, cap=2), history_rows=[history("R1", "EV_POST", "completed", "2026-09-10")])
    actual = effective_skills(ds, ds.employees["E1"])
    assert actual["SK_A"] == 2
    assert actual.pending_from["SK_A"] == ["EV_POST"]


def test_distinct_career_goal_uses_other_role_target():
    employee = {**dataset().employees["E1"], "career_goal": {"target_role": "Other", "target_grade": "Middle"}}
    target = resolve_target(dataset(employee=employee), employee)
    assert (target.role, target.grade, target.source) == ("Other", "Middle", "career_goal")


def test_critical_gap_weighting_beats_same_size_noncritical_gap():
    ds = dataset(event("EV_A", skill="SK_A"), event("EV_B", skill="SK_B"), critical=("SK_A",))
    assert recommend(ds, "E1").recommendations[0].event_id == "EV_A"


def test_unmet_prerequisite_has_explicit_rejection_reason():
    ds = dataset(event("EV_LOCKED", prerequisites={"SK_A": 2}))
    assert candidate(ds, "EV_LOCKED").blocked_by == "PREREQUISITES: SK_A"


def test_max_level_cap_makes_event_ineligible_when_it_cannot_close_gap():
    ds = dataset(event("EV_CAPPED", skill="SK_A", cap=1))
    assert candidate(ds, "EV_CAPPED").blocked_by == "NO_TARGET_GAP_OR_MAX_LEVEL_CAP"


def test_completed_event_is_excluded_except_recurring_ev_036():
    ds = dataset(event("EV_DONE"), event("EV_036"), history_rows=[history("R1", "EV_DONE", "completed", "2026-08-20"), history("R2", "EV_036", "completed", "2026-08-20")])
    assert candidate(ds, "EV_DONE").blocked_by == "ALREADY_COMPLETED"
    assert candidate(ds, "EV_036").eligible


def test_mandatory_event_is_assigned_not_recommended():
    ds = dataset(event("EV_MANDATORY", mandatory=True))
    assert candidate(ds, "EV_MANDATORY").blocked_by == "MANDATORY_ASSIGNED"


def test_scheduled_event_without_future_session_is_ineligible():
    ds = dataset(event("EV_PAST", upcoming_sessions=["2026-10-01"]))
    assert candidate(ds, "EV_PAST").blocked_by == "NO_UPCOMING_SESSION"


def test_repeated_declines_suppress_that_format_but_allow_another():
    online, self_paced, prior = event("EV_ONLINE", format="online"), event("EV_SELF", format="self_paced"), event("EV_PRIOR", format="online")
    rows = [history(f"R{i}", "EV_PRIOR", "declined") for i in range(1, 4)]
    ds = dataset(online, self_paced, prior, history_rows=rows)
    assert candidate(ds, "EV_ONLINE").blocked_by == "LOW_ENGAGEMENT_FORMAT"
    assert candidate(ds, "EV_SELF").eligible


def test_remote_employee_gets_offline_fit_penalty():
    employee = {**dataset().employees["E1"], "work_format": "remote"}
    ds = dataset(event("EV_OFFLINE", format="offline"), employee=employee)
    assert candidate(ds, "EV_OFFLINE").fit == 0.56
