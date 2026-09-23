"""Dataset loading, runtime persistence, and safe import upserts."""

from __future__ import annotations

import csv
import importlib
import io
import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable

from pydantic import ValidationError

from app.models import ActivityHistoryRecord, Employee


HISTORY_COLUMNS = [
    "record_id",
    "employee_id",
    "event_id",
    "date",
    "due_date",
    "status",
    "completion_pct",
    "score",
    "feedback_rating",
    "assigned_by",
]
IMPORT_FILES = {"employees.json", "activity_history.csv", "events.json", "skills.json"}


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _optional_int(value: str | None) -> int | None:
    return int(value) if value not in (None, "") else None


def _history_row(raw: dict[str, Any]) -> dict[str, Any]:
    row = dict(raw)
    for key in ("due_date", "score", "feedback_rating"):
        if row.get(key) == "":
            row[key] = None
    for key in ("completion_pct", "score", "feedback_rating"):
        if key in row:
            row[key] = _optional_int(row[key]) if isinstance(row[key], str) else row[key]
    return row


def _engine_dataset(data_root: Path) -> Any | None:
    """Use A's dataset loader when it has landed, without coupling to its internals."""

    try:
        module = importlib.import_module("app.engine.dataset")
    except ModuleNotFoundError:
        return None
    loader = getattr(module, "load_dataset", None)
    if not callable(loader):
        return None
    try:
        return loader(data_root)
    except TypeError:
        return loader(str(data_root))


@dataclass
class CareerStore:
    """Mutable view of starter data plus safe runtime records."""

    data_root: Path = field(default_factory=project_root)
    employees: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: dict[str, dict[str, Any]] = field(default_factory=dict)
    skills: dict[str, dict[str, Any]] = field(default_factory=dict)
    role_profiles: list[dict[str, Any]] = field(default_factory=list)
    proficiency_scale: dict[str, str] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    as_of_date: date = date(2026, 10, 1)
    engine_dataset: Any | None = None

    @property
    def data_dir(self) -> Path:
        return self.data_root / "data"

    @property
    def runtime_dir(self) -> Path:
        return self.data_dir / "runtime"

    def load(self) -> None:
        """Load base data, then optional extra and runtime overlays."""

        self._load_directory(self.data_dir)
        self._load_directory(self.data_dir / "extra")
        self._load_directory(self.runtime_dir)
        self.engine_dataset = _engine_dataset(self.data_dir)

    def _load_directory(self, directory: Path) -> None:
        if not directory.exists():
            return
        employees_path = directory / "employees.json"
        if employees_path.exists():
            payload = _read_json(employees_path)
            self.as_of_date = date.fromisoformat(payload.get("meta", {}).get("as_of_date", str(self.as_of_date)))
            self.employees.update({item["employee_id"]: item for item in payload.get("employees", [])})

        events_path = directory / "events.json"
        if events_path.exists():
            self.events.update({item["event_id"]: item for item in _read_json(events_path).get("events", [])})

        skills_path = directory / "skills.json"
        if skills_path.exists():
            payload = _read_json(skills_path)
            self.skills.update({item["skill_id"]: item for item in payload.get("skills", [])})
            self.role_profiles = payload.get("role_profiles", self.role_profiles)
            self.proficiency_scale = payload.get("proficiency_scale", self.proficiency_scale)

        history_path = directory / "activity_history.csv"
        if history_path.exists():
            with history_path.open(newline="", encoding="utf-8") as handle:
                self._upsert_history(_history_row(row) for row in csv.DictReader(handle))

    def _upsert_history(self, rows: Iterable[dict[str, Any]]) -> None:
        by_id = {row["record_id"]: index for index, row in enumerate(self.history)}
        for row in rows:
            index = by_id.get(row["record_id"])
            if index is None:
                by_id[row["record_id"]] = len(self.history)
                self.history.append(row)
            else:
                self.history[index] = row

    def employee(self, employee_id: str) -> dict[str, Any] | None:
        return self.employees.get(employee_id)

    def history_for(self, employee_id: str) -> list[dict[str, Any]]:
        return [row for row in self.history if row["employee_id"] == employee_id]

    def event(self, event_id: str) -> dict[str, Any] | None:
        return self.events.get(event_id)

    def persist_history(self, row: dict[str, Any]) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        path = self.runtime_dir / "activity_history.csv"
        write_header = not path.exists() or path.stat().st_size == 0
        with path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=HISTORY_COLUMNS)
            if write_header:
                writer.writeheader()
            writer.writerow({key: row.get(key) or "" for key in HISTORY_COLUMNS})

    def add_activity(self, employee_id: str, event_id: str, action: str) -> dict[str, Any]:
        sequence = max(
            (int(row["record_id"][1:]) for row in self.history if row["record_id"].startswith("R") and row["record_id"][1:].isdigit()),
            default=0,
        ) + 1
        status = "completed" if action == "complete" else "in_progress"
        row = {
            "record_id": f"R{sequence:06d}",
            "employee_id": employee_id,
            "event_id": event_id,
            "date": self.as_of_date.isoformat(),
            "due_date": None,
            "status": status,
            "completion_pct": 100 if action == "complete" else 0,
            "score": None,
            "feedback_rating": None,
            "assigned_by": "self",
        }
        ActivityHistoryRecord.model_validate(row)
        self.history.append(row)
        self.persist_history(row)
        return row

    def add_not_now(self, employee_id: str, event_id: str) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        feedback = {
            "employee_id": employee_id,
            "event_id": event_id,
            "date": self.as_of_date.isoformat(),
            "expires_date": (self.as_of_date + timedelta(days=90)).isoformat(),
            "weight": 0.5,
        }
        with (self.runtime_dir / "feedback.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(feedback, ensure_ascii=False) + "\n")

    def import_files(self, uploads: list[tuple[str, bytes]]) -> dict[str, Any]:
        """Validate each row independently and upsert valid records only."""

        counts = {key: 0 for key in ("employees", "history", "events", "skills")}
        added = dict(counts)
        updated = dict(counts)
        errors: list[dict[str, Any]] = []
        for filename, content in uploads:
            if filename not in IMPORT_FILES:
                errors.append({"file": filename, "row": None, "message": "unsupported import file"})
                continue
            try:
                if filename == "activity_history.csv":
                    self._import_history(content, added, updated, errors)
                else:
                    self._import_json(filename, content, added, updated, errors)
            except (UnicodeDecodeError, csv.Error, json.JSONDecodeError) as exc:
                errors.append({"file": filename, "row": None, "message": f"invalid file: {exc}"})
        return {"added": added, "updated": updated, "errors": errors}

    def _import_json(
        self, filename: str, content: bytes, added: dict[str, int], updated: dict[str, int], errors: list[dict[str, Any]]
    ) -> None:
        payload = json.loads(content.decode("utf-8"))
        key, id_key, destination, validator = {
            "employees.json": ("employees", "employee_id", self.employees, Employee),
            "events.json": ("events", "event_id", self.events, None),
            "skills.json": ("skills", "skill_id", self.skills, None),
        }[filename]
        if not isinstance(payload, dict) or not isinstance(payload.get(key), list):
            raise json.JSONDecodeError(f"expected an object with a {key} list", "", 0)
        count_key = "history" if filename == "activity_history.csv" else key
        for row_number, item in enumerate(payload[key], start=1):
            try:
                if not isinstance(item, dict) or not item.get(id_key):
                    raise ValueError(f"missing {id_key}")
                if validator:
                    validator.model_validate(item)
                record_id = item[id_key]
                (updated if record_id in destination else added)[count_key] += 1
                destination[record_id] = item
            except (ValidationError, ValueError, TypeError) as exc:
                errors.append({"file": filename, "row": row_number, "message": str(exc)})
        if filename == "skills.json":
            self.role_profiles = payload.get("role_profiles", self.role_profiles)
            self.proficiency_scale = payload.get("proficiency_scale", self.proficiency_scale)

    def _import_history(
        self, content: bytes, added: dict[str, int], updated: dict[str, int], errors: list[dict[str, Any]]
    ) -> None:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
        if reader.fieldnames != HISTORY_COLUMNS:
            errors.append({"file": "activity_history.csv", "row": None, "message": "CSV columns must match starter-kit schema"})
            return
        existing = {row["record_id"] for row in self.history}
        valid_rows: list[dict[str, Any]] = []
        for row_number, raw in enumerate(reader, start=2):
            try:
                row = ActivityHistoryRecord.model_validate(_history_row(raw)).model_dump(mode="json")
                (updated if row["record_id"] in existing else added)["history"] += 1
                valid_rows.append(row)
            except ValidationError as exc:
                errors.append({"file": "activity_history.csv", "row": row_number, "message": str(exc)})
        self._upsert_history(valid_rows)
