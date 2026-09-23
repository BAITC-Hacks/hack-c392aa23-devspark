"""Small, dependency-free HR overview used until the engine analytics lands."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from typing import Any

from app.api.service import profile, recommend
from app.models import HrOverview
from app.store import CareerStore

NEGATIVE = {"declined", "no_show", "dropped", "overdue"}

REASON_HINTS = {
    "AT_TOP_NO_GOAL": "At the top grade with no goal set — offer lateral or mentoring options, never pressure.",
    "TARGET_REACHED": "Already meets every target requirement — a good moment to agree the next goal.",
    "NO_ELIGIBLE_EVENTS": "No untaken activity develops their remaining gaps — consider creating or sourcing one.",
    "PREREQUISITES_BLOCKED": "Remaining steps are prerequisite-blocked — plan a foundational activity first.",
    "LOW_ENGAGEMENT": "Repeated refusals on relevant activities — talk first; assigning more tends to backfire.",
}


def overview(store: CareerStore, department: str | None = None) -> HrOverview:
    employees = [employee for employee in store.employees.values() if not department or employee["department"] == department]
    lagging: dict[str, dict[str, Any]] = {}
    no_step = []
    readiness_by_id: dict[str, float] = {}
    for employee in employees:
        employee_profile = profile(store, employee["employee_id"])
        readiness_by_id[employee["employee_id"]] = employee_profile.readiness.pct
        for skill in employee_profile.skills:
            gap = max(0, skill.required_target - skill.effective)
            if not gap:
                continue
            item = lagging.setdefault(skill.skill_id, {"skill_id": skill.skill_id, "name": skill.name, "employees_below": 0, "gaps": [], "critical_count": 0})
            item["employees_below"] += 1
            item["gaps"].append(gap)
            item["critical_count"] += int(skill.critical)
        result = recommend(store, employee["employee_id"])
        if result.empty_reason:
            no_step.append({"employee_id": employee["employee_id"], "full_name": employee["full_name"], "role": employee["role"], "grade": employee["grade"], "reason_code": result.empty_reason, "hint": REASON_HINTS.get(result.empty_reason, "Review available voluntary development options with the employee.")})
    lagging_skills = [{"skill_id": item["skill_id"], "name": item["name"], "employees_below": item["employees_below"], "avg_gap": round(sum(item["gaps"]) / len(item["gaps"]), 2), "critical_count": item["critical_count"]} for item in lagging.values()]
    counts: dict[str, dict[str, Any]] = defaultdict(lambda: {status: 0 for status in ("completed", "no_show", "declined", "dropped", "overdue")})
    ratings: dict[str, list[int]] = defaultdict(list)
    for row in store.history:
        event = store.event(row["event_id"])
        if not event:
            continue
        if row["status"] in counts[row["event_id"]]:
            counts[row["event_id"]][row["status"]] += 1
        if row.get("feedback_rating") is not None:
            ratings[row["event_id"]].append(row["feedback_rating"])
    participation = []
    for event_id, event in store.events.items():
        item = counts[event_id]
        total = sum(item.values())
        completion_rate = round(item["completed"] / total, 4) if total else 0.0
        participation.append({"event_id": event_id, "title": event["title"], "type": event["type"], **item, "completion_rate": completion_rate, "avg_rating": round(sum(ratings[event_id]) / len(ratings[event_id]), 2) if ratings[event_id] else None, "flagged": bool(total and (item["no_show"] + item["dropped"]) / total > 0.25)})
    disengaged = _disengaged(store, employees)
    attrition_risk = _attrition_risk(store, employees, readiness_by_id)
    return HrOverview.model_validate({"lagging_skills": sorted(lagging_skills, key=lambda item: item["employees_below"], reverse=True)[:15], "no_step": no_step, "participation": participation, "disengaged": disengaged, "attrition_risk": attrition_risk})


def _attrition_risk(store: CareerStore, employees: list[dict[str, Any]], readiness_by_id: dict[str, float]) -> list[dict[str, Any]]:
    """Transparent attrition-risk signal from disengagement, overdue work, stalled
    progress and missing goals. Every point is explained; it prompts a conversation."""

    cutoff = (store.as_of_date - timedelta(days=182)).isoformat()
    window: dict[str, dict[str, int]] = defaultdict(lambda: {"neg": 0, "overdue": 0, "pos": 0})
    for row in store.history:
        if str(row.get("date")) < cutoff:
            continue
        bucket = window[row["employee_id"]]
        if row["status"] == "overdue":
            bucket["overdue"] += 1
            bucket["neg"] += 1
        elif row["status"] in NEGATIVE:
            bucket["neg"] += 1
        elif row["status"] == "completed":
            bucket["pos"] += 1

    risks: list[dict[str, Any]] = []
    for employee in employees:
        eid = employee["employee_id"]
        counts = window.get(eid, {"neg": 0, "overdue": 0, "pos": 0})
        risk, reasons = 0, []
        if counts["neg"] >= 2:
            risk += 25
            reasons.append(f"{counts['neg']} refusals or no-shows in 6 months")
        if counts["overdue"] > 0:
            risk += 25
            reasons.append(f"{counts['overdue']} overdue mandatory item(s)")
        if counts["pos"] == 0:
            risk += 20
            reasons.append("no voluntary activity completed in 6 months")
        readiness = readiness_by_id.get(eid, 100.0)
        if readiness < 50 and employee.get("tenure_months", 0) >= 24:
            risk += 20
            reasons.append(f"low readiness ({readiness:.0f}%) after {employee['tenure_months'] // 12}+ years")
        if employee.get("career_goal") is None and employee.get("grade") != "Lead":
            risk += 10
            reasons.append("no career goal set")
        risk = min(100, risk)
        if risk >= 35 and reasons:
            risks.append({"employee_id": eid, "full_name": employee["full_name"], "role": employee["role"],
                          "grade": employee["grade"], "risk": risk, "level": "high" if risk >= 60 else "medium", "reasons": reasons})
    return sorted(risks, key=lambda item: item["risk"], reverse=True)[:12]


def _disengaged(store: CareerStore, employees: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Employees refusing more than they finish over the last 6 months. A private
    signal for a conversation — never a ranking, never shown to employees."""

    cutoff = (store.as_of_date - timedelta(days=182)).isoformat()
    tally: dict[str, dict[str, int]] = defaultdict(lambda: {"neg": 0, "pos": 0})
    for row in store.history:
        if str(row.get("date")) < cutoff:
            continue
        bucket = tally[row["employee_id"]]
        if row["status"] in NEGATIVE:
            bucket["neg"] += 1
        elif row["status"] == "completed":
            bucket["pos"] += 1
    names = {employee["employee_id"]: employee for employee in employees}
    flagged = [
        {"employee_id": eid, "full_name": names[eid]["full_name"], "negatives_6m": counts["neg"], "completions_6m": counts["pos"]}
        for eid, counts in tally.items()
        if eid in names and counts["neg"] >= 2 and counts["neg"] >= counts["pos"]
    ]
    return sorted(flagged, key=lambda item: (item["negatives_6m"] - item["completions_6m"], item["negatives_6m"]), reverse=True)[:15]
