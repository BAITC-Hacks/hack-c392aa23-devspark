from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client(tmp_path: Path):
    root = tmp_path / "project"
    shutil.copytree(Path(__file__).resolve().parents[3] / "data", root / "data")
    with TestClient(create_app(root)) as test_client:
        yield test_client


def employee_headers(client: TestClient, employee_id: str = "E0001") -> dict[str, str]:
    response = client.post("/api/auth/login", json={"role": "employee", "employee_id": employee_id})
    return {"Authorization": f"Bearer {response.json()['token']}"}


def hr_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"role": "hr"})
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_employee_cannot_access_someone_else_or_hr(client: TestClient):
    headers = employee_headers(client)

    assert client.get("/api/employees/E0002", headers=headers).status_code == 403
    assert client.get("/api/hr/overview", headers=headers).status_code == 403


def test_import_upserts_valid_rows_and_reports_invalid_rows(client: TestClient):
    person = client.get("/api/demo/people").json()[0]
    source = Path(__file__).resolve().parents[3] / "data" / "employees.json"
    employee = next(item for item in json.loads(source.read_text())["employees"] if item["employee_id"] == person["employee_id"])
    employee["employee_id"] = "E9000"
    payload = {"meta": {"as_of_date": "2026-10-01"}, "employees": [employee, {"employee_id": "broken"}]}

    response = client.post(
        "/api/hr/import",
        headers=hr_headers(client),
        files={"employees.json": ("employees.json", json.dumps(payload), "application/json")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["added"]["employees"] == 1
    assert body["errors"][0]["file"] == "employees.json"
    assert client.get("/api/employees/E9000", headers=hr_headers(client)).status_code == 200


def test_complete_writes_history_and_reports_skill_change(client: TestClient):
    headers = employee_headers(client)
    recommendations = client.get("/api/employees/E0001/recommendations", headers=headers).json()["recommendations"]
    assert recommendations

    response = client.post(
        "/api/employees/E0001/activities",
        headers=headers,
        json={"event_id": recommendations[0]["event_id"], "action": "complete"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["record"]["status"] == "completed"
    assert body["skills_changed"]
