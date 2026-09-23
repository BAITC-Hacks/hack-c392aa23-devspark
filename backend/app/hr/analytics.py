"""Small, dependency-free HR overview used until the engine analytics lands."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.api.service import profile, recommend
from app.models import HrOverview
from app.store import CareerStore


def overview(store: CareerStore, department: str | None = None) -> HrOverview:
    employees = [employee for employee in store.employees.values() if not department or employee["department"] == department]
    lagging: dict[str, dict[str, Any]] = {}
    no_step = []
    for employee in employees:
        employee_profile = profile(store, employee["employee_id"])
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
            no_step.append({"employee_id": employee["employee_id"], "full_name": employee["full_name"], "role": employee["role"], "grade": employee["grade"], "reason_code": result.empty_reason, "hint": "Review available voluntary development options with the employee."})
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
    return HrOverview.model_validate({"lagging_skills": sorted(lagging_skills, key=lambda item: item["employees_below"], reverse=True)[:15], "no_step": no_step, "participation": participation, "disengaged": []})
