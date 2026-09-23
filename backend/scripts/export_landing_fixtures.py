"""Export real product output for the landing page.

Runs the engine and the API in-process against a clean copy of data/ (nothing is
written to data/runtime) and saves frontend/src/landing/fixtures.json, so every number
on the landing page comes from the actual product, not from copywriting.

With LLM_API_KEY set, the hero and trap rationales come from the AI layer and are
translated to kk/ru/en so all three languages describe the same pick. Without a key
the rules-mode templates (also kk/ru/en) are used.

Run from the repo root:  python backend/scripts/export_landing_fixtures.py
"""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

LANGS = ("en", "ru", "kk")
LANG_NAMES = {"en": "English", "ru": "Russian", "kk": "Kazakh"}
HERO_ID, TRAP_ID = "E0028", "E9001"
PEOPLE = [("E0028", "case_example"), ("E0112", "speaking_trap"), ("E9003", "cross_role")]
NEGATIVE = {"declined", "no_show", "dropped"}


def load_env_file() -> None:
    """Pick up LLM_* settings from a local .env if the shell did not export them."""
    env = ROOT / ".env"
    if not env.is_file():
        return
    for line in env.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            if key.startswith("LLM_") and value and not os.environ.get(key):
                os.environ[key] = value.strip()


def initials(name: str) -> str:
    return " ".join(part[0] + "." for part in name.split() if part)


def translate(client, model: str, texts: list[str], lang: str) -> list[str]:
    """Translate a list of UI strings, keeping names, numbers and arrows intact."""
    if lang == "en" or client is None or not texts:
        return texts
    response = client.chat.completions.create(
        model=model, temperature=0,
        response_format={"type": "json_schema", "json_schema": {"name": "t", "strict": True, "schema": {
            "type": "object", "additionalProperties": False, "required": ["items"],
            "properties": {"items": {"type": "array", "items": {"type": "string"}}}}}},
        messages=[
            {"role": "system", "content": f"Translate each string to {LANG_NAMES[lang]} for a bank's HR product UI. "
             "Keep event titles, numbers and arrows (→) exactly as they are. Return the same number of items in order."},
            {"role": "user", "content": json.dumps({"items": texts}, ensure_ascii=False)},
        ],
    )
    items = json.loads(response.choices[0].message.content)["items"]
    return items if len(items) == len(texts) else texts


def card(rec: dict, skills: dict) -> dict:
    return {
        "event_id": rec["event_id"], "title": rec["title"], "type": rec["type"], "format": rec["format"],
        "duration_hours": rec["duration_hours"], "next_session": rec["next_session"], "score": rec["score"],
        "factors": [{"kind": f["kind"], "label": f["label"]} for f in rec["factors"]],
        "gains": [{"skill": skills.get(g["skill_id"], g["skill_id"]), "from": g["from"], "to": g["to"]} for g in rec["expected_gains"]],
        "readiness_after": rec["readiness_after_pct"],
    }


def localized_card(client, model, api_get, employee_id: str, skills: dict) -> tuple[dict, list[int]]:
    """Top recommendation with rationale and factor labels in every language."""
    latencies: list[int] = []
    primary = api_get(f"/api/employees/{employee_id}/recommendations?mode=ai&lang=en")
    if primary["generated_by"] == "llm":
        latencies.append(primary["latency_ms"])
    top = card(primary["recommendations"][0], skills)
    base_rationale = primary["recommendations"][0]["rationale"]
    labels = [f["label"] for f in top["factors"]]
    top["generated_by"] = primary["generated_by"]
    top["rationale"], top["factor_labels"] = {}, {}
    for lang in LANGS:
        if client is not None and primary["generated_by"] == "llm":
            text, *translated = translate(client, model, [base_rationale, *labels], lang)
        else:  # rules templates exist for every language
            rules = api_get(f"/api/employees/{employee_id}/recommendations?mode=rules&lang={lang}")
            text, translated = rules["recommendations"][0]["rationale"], labels
        top["rationale"][lang], top["factor_labels"][lang] = text, translated
    return top, latencies


def main() -> int:
    load_env_file()
    from fastapi.testclient import TestClient

    from app.engine.dataset import load_dataset
    from app.engine.recommender import apply_activity, recommend
    from app.llm.client import get_client, model_name
    from app.main import create_app

    spec = importlib.util.spec_from_file_location("run_eval", ROOT / "eval" / "run_eval.py")
    run_eval = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run_eval)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        shutil.copytree(ROOT / "data", root / "data", ignore=shutil.ignore_patterns("runtime", "extra"))
        ds = load_dataset(root / "data")
        skills = {sid: item.get("name", sid) for sid, item in ds.skills.items()}
        client, model = get_client(), model_name()

        with TestClient(create_app(root)) as api:
            def token(role: str, employee_id: str | None = None) -> dict:
                body = {"role": role, **({"employee_id": employee_id} if employee_id else {})}
                return {"Authorization": f"Bearer {api.post('/api/auth/login', json=body).json()['token']}"}

            hr = token("hr")

            def get(path: str) -> dict:
                response = api.get(path, headers=hr)
                response.raise_for_status()
                return response.json()

            # ---- hero: the case's own example profile -------------------------------
            profile = get(f"/api/employees/{HERO_ID}")
            hero_card, ai_ms = localized_card(client, model, get, HERO_ID, skills)
            rules = get(f"/api/employees/{HERO_ID}/recommendations?mode=rules")
            hero = {
                "employee": {"name": profile["employee"]["full_name"], "role": profile["employee"]["role"],
                             "grade": profile["employee"]["grade"], "tenure_months": profile["employee"]["tenure_months"]},
                "target": profile["target"], "readiness": profile["readiness"],
                "trajectory": rules["trajectory"], "card": hero_card,
                "others": [r["title"] for r in rules["recommendations"][1:]],
                "why_not": rules["not_recommended"][0]["reason"] if rules["not_recommended"] else None,
            }

            # ---- trap: lowest skill refused 3x, critical gap elsewhere ---------------
            trap_profile = get(f"/api/employees/{TRAP_ID}")
            trap_card, trap_ms = localized_card(client, model, get, TRAP_ID, skills)
            ai_ms += trap_ms
            naive_id = run_eval.naive_baseline(ds, TRAP_ID)
            employee = ds.employees[TRAP_ID]
            effective = {s["skill_id"]: s["effective"] for s in trap_profile["skills"]}
            gaps = [s for s in trap_profile["skills"] if s["required_target"] > s["effective"]]
            lowest = min(gaps, key=lambda s: (s["effective"], s["skill_id"]))
            refused = sum(1 for row in ds.employee_history(TRAP_ID) if row["status"] in NEGATIVE and any(
                d["skill_id"] == lowest["skill_id"] for d in ds.events[row["event_id"]]["develops_skills"]))
            critical = [s for s in gaps if s["critical"]]
            trap = {
                "persona": {"role": employee["role"], "grade": employee["grade"], "target": trap_profile["target"]},
                "lowest": {"skill": lowest["name"], "level": lowest["effective"], "refused": refused},
                "critical_gap": {"skill": critical[0]["name"], "have": critical[0]["effective"], "need": critical[0]["required_target"]} if critical else None,
                "naive": {"event_id": naive_id, "title": ds.events[naive_id]["title"] if naive_id else None},
                "quest": trap_card,
            }

            # ---- progress: what 'Mark completed' does (in memory only) ---------------
            first = hero_card["event_id"]
            update = apply_activity(ds, HERO_ID, first, "complete")
            progress = {
                "event_title": hero_card["title"],
                "changes": [{"skill": skills.get(c.skill_id, c.skill_id), "from": c.model_dump(by_alias=True)["from"], "to": c.to} for c in update.skills_changed],
                "readiness_before": update.readiness_before, "readiness_after": update.readiness_after,
                "next": [r.title for r in update.recommendations.recommendations[:2]],
            }

            # ---- HR preview (initials only: the landing practises what it preaches) --
            overview = get("/api/hr/overview")
            # Voluntary activities only (mandatory training is not a recommendation target),
            # drop-off first: that is the signal HR can act on.
            voluntary = [p for p in overview["participation"] if not ds.events.get(p["event_id"], {}).get("mandatory")]
            participation = sorted(voluntary, key=lambda p: (not p["flagged"], -(p["completed"] + p["no_show"] + p["declined"] + p["dropped"])))
            hr_preview = {
                "lagging": [{k: s[k] for k in ("name", "employees_below", "avg_gap", "critical_count")} for s in overview["lagging_skills"][:5]],
                "no_step": [{"who": initials(p["full_name"]), "role": p["role"], "grade": p["grade"], "reason": p["reason_code"], "hint": p["hint"]} for p in overview["no_step"][:3]],
                "participation": [{"title": p["title"], "rate": p["completion_rate"], "flagged": p["flagged"], "rating": p["avg_rating"]} for p in participation[:6]],
                "attrition": [{"who": initials(p["full_name"]), "role": p["role"], "grade": p["grade"], "risk": p["risk"], "level": p["level"], "reasons": p["reasons"],
                               "reasons_i18n": {lang: translate(client, model, p["reasons"], lang) for lang in LANGS}} for p in overview["attrition_risk"][:3]],
                "no_step_total": len(overview["no_step"]),
            }

            people_by_id = {p["employee_id"]: p for p in api.get("/api/demo/people").json()}
            people = [{**people_by_id[pid], "tag": tag} for pid, tag in PEOPLE if pid in people_by_id]

        # ---- proof numbers ----------------------------------------------------------
        base = json.loads((ROOT / "data" / "employees.json").read_text())["employees"]
        events = json.loads((ROOT / "data" / "events.json").read_text())["events"]
        catalog = json.loads((ROOT / "data" / "skills.json").read_text())["skills"]
        with (ROOT / "data" / "activity_history.csv").open() as handle:
            history_rows = sum(1 for _ in csv.DictReader(handle))
        expectations = json.loads((ROOT / "eval" / "expectations.json").read_text())
        passed = sum(run_eval.check(exp, recommend(ds, eid), run_eval.naive_baseline(ds, eid))[0] for eid, exp in expectations.items())
        timings = []
        for item in base[:60]:
            started = time.perf_counter()
            recommend(ds, item["employee_id"])
            timings.append((time.perf_counter() - started) * 1000)
        stats = {
            "profiles": len(base), "activities": len(events), "skills": len(catalog), "history": history_rows,
            "traps_passed": passed, "traps_total": len(expectations),
            "rules_ms": round(statistics.median(timings), 1),
            "ai_ms": round(statistics.median(ai_ms)) if ai_ms else None, "model": model if ai_ms else None,
        }

    out = ROOT / "frontend" / "src" / "landing" / "fixtures.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"hero": hero, "trap": trap, "progress": progress, "hr": hr_preview,
                               "people": people, "stats": stats}, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {out.relative_to(ROOT)} — hero {hero_card['event_id']} ({hero_card['generated_by']}), "
          f"trap {trap_card['event_id']} vs naive {naive_id}, traps {passed}/{len(expectations)}, "
          f"rules {stats['rules_ms']} ms, ai {stats['ai_ms']} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
