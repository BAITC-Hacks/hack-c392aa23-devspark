"""Loading and in-memory representation of the starter-kit data."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


Json = dict[str, Any]


@dataclass
class Dataset:
    """Mutable data store used by the pure recommendation engine.

    Records deliberately remain dictionaries so imported starter-kit rows retain
    their original schema.  The API boundary is responsible for Pydantic parsing.
    """

    meta: Json
    proficiency_scale: dict[str, str]
    skills: dict[str, Json]
    role_profiles: dict[tuple[str, str], Json]
    employees: dict[str, Json]
    events: dict[str, Json]
    history: list[Json] = field(default_factory=list)

    def employee_history(self, employee_id: str) -> list[Json]:
        return [row for row in self.history if row["employee_id"] == employee_id]

    @property
    def as_of_date(self) -> str:
        return str(self.meta["as_of_date"])


def _read_json(path: Path) -> Json | None:
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def _read_history(path: Path) -> list[Json]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as source:
        rows: list[Json] = []
        for row in csv.DictReader(source):
            for field_name in ("completion_pct", "score", "feedback_rating"):
                if row.get(field_name) not in (None, ""):
                    row[field_name] = int(row[field_name])
                elif field_name in row:
                    row[field_name] = None
            row["due_date"] = row.get("due_date") or None
            rows.append(dict(row))
        return rows


def _upsert(records: dict[str, Json], items: Iterable[Json], id_field: str) -> None:
    for item in items:
        if id_value := item.get(id_field):
            records[str(id_value)] = dict(item)


def load_dataset(data_dir: str | Path, extra_dirs: Iterable[str | Path] | None = None) -> Dataset:
    """Load starter data and upsert optional data/extra and data/test_profiles.

    An explicitly supplied ``extra_dirs`` supplements (rather than replaces) the
    conventional folders, so the evaluator can point at an isolated profile set.
    """

    root = Path(data_dir)
    directories = [root]
    for candidate in (root / "extra", root / "test_profiles"):
        if candidate.is_dir():
            directories.append(candidate)
    for directory in extra_dirs or ():
        candidate = Path(directory)
        if candidate.is_dir() and candidate not in directories:
            directories.append(candidate)

    first_skills = _read_json(root / "skills.json") or {}
    first_employees = _read_json(root / "employees.json") or {}
    first_events = _read_json(root / "events.json") or {}
    dataset = Dataset(
        meta=dict(first_skills.get("meta") or first_employees.get("meta") or first_events.get("meta") or {}),
        proficiency_scale=dict(first_skills.get("proficiency_scale") or {}),
        skills={},
        role_profiles={},
        employees={},
        events={},
    )
    history_by_id: dict[str, Json] = {}
    for directory in directories:
        skills_doc = _read_json(directory / "skills.json") or {}
        employees_doc = _read_json(directory / "employees.json") or {}
        events_doc = _read_json(directory / "events.json") or {}
        if skills_doc.get("meta") and not dataset.meta:
            dataset.meta = dict(skills_doc["meta"])
        if skills_doc.get("proficiency_scale"):
            dataset.proficiency_scale.update(skills_doc["proficiency_scale"])
        _upsert(dataset.skills, skills_doc.get("skills", []), "skill_id")
        for item in skills_doc.get("role_profiles", []):
            if item.get("role") and item.get("grade"):
                dataset.role_profiles[(item["role"], item["grade"])] = dict(item)
        _upsert(dataset.employees, employees_doc.get("employees", []), "employee_id")
        _upsert(dataset.events, events_doc.get("events", []), "event_id")
        _upsert(history_by_id, _read_history(directory / "activity_history.csv"), "record_id")
    dataset.history = sorted(history_by_id.values(), key=lambda row: (str(row["date"]), str(row["employee_id"]), str(row["event_id"])))
    if not dataset.meta.get("as_of_date"):
        raise ValueError("Dataset meta.as_of_date is required")
    return dataset
