"""The landing's numbers are product output: keep them complete, consistent and private."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "frontend" / "src" / "landing" / "fixtures.json"
LANGS = ("en", "ru", "kk")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def employees(*parts: str) -> list[dict]:
    return load(ROOT.joinpath("data", *parts, "employees.json"))["employees"]


def test_every_language_has_a_rationale_and_all_factor_labels():
    data = load(FIXTURES)
    for card in (data["hero"]["card"], data["trap"]["quest"]):
        for lang in LANGS:
            assert card["rationale"][lang].strip()
            assert len(card["factor_labels"][lang]) == len(card["factors"])


def test_hr_preview_shows_initials_never_names():
    data = load(FIXTURES)
    names = {person["full_name"] for person in employees()}
    blob = json.dumps(data["hr"], ensure_ascii=False)
    assert not [name for name in names if name in blob]
    for row in data["hr"]["no_step"] + data["hr"]["attrition"]:
        assert re.fullmatch(r"(\w\.\s?)+", row["who"])


def test_proof_numbers_match_the_dataset():
    stats = load(FIXTURES)["stats"]
    assert stats["profiles"] == len(employees())
    assert stats["traps_passed"] == stats["traps_total"] > 0


def test_demo_profiles_exist_and_trap_contrasts_the_naive_rule():
    data = load(FIXTURES)
    known = {person["employee_id"] for person in employees() + employees("test_profiles")}
    assert all(person["employee_id"] in known for person in data["people"])
    trap = data["trap"]
    assert trap["naive"]["event_id"] and trap["naive"]["event_id"] != trap["quest"]["event_id"]
    assert trap["lowest"]["refused"] >= 3
