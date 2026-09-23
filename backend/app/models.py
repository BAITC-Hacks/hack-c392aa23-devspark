"""Pydantic v2 models for the public Career Quest API contract."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    """Base model for the JSON API contract."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


Language = Literal["kk", "ru", "en"]
UserRole = Literal["employee", "hr"]
TargetSource = Literal["career_goal", "next_grade", "none"]
RecommendationMode = Literal["ai", "rules"]
GeneratedBy = Literal["llm", "rules"]
ActivityAction = Literal["complete", "enroll", "not_now"]
ActivityStatus = Literal[
    "completed", "in_progress", "declined", "no_show", "dropped", "overdue"
]
AssignedBy = Literal["self", "manager", "hr"]
FactorKind = Literal[
    "critical_gap",
    "target_gap",
    "expected_gain",
    "max_level_cap",
    "participation_history",
    "format_fit",
    "availability",
    "prerequisites",
    "stale_assessment",
    "goal_alignment",
    "workload",
]


# Authentication and login picker
class LoginRequest(ApiModel):
    role: UserRole
    employee_id: str | None = None


class LoginResponse(ApiModel):
    token: str
    role: UserRole
    employee_id: str | None


class PersonSummary(ApiModel):
    employee_id: str
    full_name: str
    role: str
    grade: str


# Raw starter-kit records exposed by the API.
class CareerGoal(ApiModel):
    target_role: str
    target_grade: str


class Employee(ApiModel):
    employee_id: str
    full_name: str
    department: str
    role: str
    grade: str
    manager_id: str | None
    hire_date: date
    tenure_months: int
    work_format: Literal["office", "hybrid", "remote"]
    preferred_language: Language
    career_goal: CareerGoal | None
    skills: dict[str, int]
    last_review_date: date


class ActivityHistoryRecord(ApiModel):
    record_id: str
    employee_id: str
    event_id: str
    date: date
    due_date: date | None
    status: ActivityStatus
    completion_pct: int
    score: int | None
    feedback_rating: int | None
    assigned_by: AssignedBy


class HistoryItem(ActivityHistoryRecord):
    title: str


# Profile
class Target(ApiModel):
    role: str | None
    grade: str | None
    source: TargetSource


class ProfileSkill(ApiModel):
    skill_id: str
    name: str
    type: str
    category: str
    assessed: int
    effective: int
    pending_from: list[str]
    required_current: int
    required_target: int
    critical: bool


class Readiness(ApiModel):
    pct: float
    critical_met: int
    critical_total: int


class ActivityStats(ApiModel):
    completed: int
    no_show: int
    declined: int
    dropped: int
    overdue: int
    in_progress: int


class AssignedActivity(ApiModel):
    event_id: str
    title: str
    due_date: date | None
    status: ActivityStatus


class AvailableEvent(ApiModel):
    event_id: str
    title: str
    eligible: bool
    blocked_by: str | None
    score: float | None


class Profile(ApiModel):
    employee: Employee
    target: Target
    skills: list[ProfileSkill]
    readiness: Readiness
    history: list[HistoryItem]
    stats: ActivityStats
    assigned: list[AssignedActivity]
    available_events: list[AvailableEvent]


# Recommendations
class RecommendationFactor(ApiModel):
    kind: FactorKind
    label: str
    impact: float


class ExpectedGain(ApiModel):
    skill_id: str
    from_: int = Field(alias="from")
    to: int


class Recommendation(ApiModel):
    rank: int
    event_id: str
    title: str
    type: str
    format: str
    duration_hours: float
    next_session: date | None
    score: float
    factors: list[RecommendationFactor]
    expected_gains: list[ExpectedGain]
    readiness_after_pct: float
    rationale: str


class Trajectory(ApiModel):
    now_pct: float
    after_pct: list[float]


class NotRecommended(ApiModel):
    skill_id: str | None
    event_id: str | None
    reason: str


class RecommendationResult(ApiModel):
    employee_id: str
    target: Target
    generated_by: GeneratedBy
    model: str | None
    latency_ms: int
    recommendations: list[Recommendation]
    trajectory: Trajectory
    not_recommended: list[NotRecommended]
    empty_reason: str | None


class ActivityRequest(ApiModel):
    event_id: str
    action: ActivityAction


class SkillChange(ApiModel):
    skill_id: str
    from_: int = Field(alias="from")
    to: int


class ProgressUpdate(ApiModel):
    record: ActivityHistoryRecord
    skills_changed: list[SkillChange]
    readiness_before: float
    readiness_after: float
    recommendations: RecommendationResult


# Catalog and health
class Catalog(ApiModel):
    skills: list[dict[str, Any]]
    proficiency_scale: dict[str, str]
    events: list[dict[str, Any]]


class Health(ApiModel):
    status: str
    llm_enabled: bool
    model: str | None


# HR
class HrEmployeeSummary(PersonSummary):
    empty_reason: str | None = None


class LaggingSkill(ApiModel):
    skill_id: str
    name: str
    employees_below: int
    avg_gap: float
    critical_count: int


class NoStepEmployee(ApiModel):
    employee_id: str
    full_name: str
    role: str
    grade: str
    reason_code: str
    hint: str


class Participation(ApiModel):
    event_id: str
    title: str
    type: str
    completed: int
    no_show: int
    declined: int
    dropped: int
    overdue: int
    completion_rate: float
    avg_rating: float | None
    flagged: bool


class DisengagedEmployee(ApiModel):
    employee_id: str
    full_name: str
    negatives_6m: int
    completions_6m: int


class HrOverview(ApiModel):
    lagging_skills: list[LaggingSkill]
    no_step: list[NoStepEmployee]
    participation: list[Participation]
    disengaged: list[DisengagedEmployee]


# Imports
class ImportCounts(ApiModel):
    employees: int
    history: int
    events: int
    skills: int


class ImportError(ApiModel):
    file: str
    row: int | None
    message: str


class ImportReport(ApiModel):
    added: ImportCounts
    updated: ImportCounts
    errors: list[ImportError]
