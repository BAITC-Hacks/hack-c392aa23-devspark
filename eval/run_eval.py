"""Trap-profile evaluation: naive lowest-skill baseline vs the rules engine vs the
AI layer. Run from anywhere: `python eval/run_eval.py`. Writes eval/RESULTS.md.

The AI column runs only when LLM_API_KEY is set; otherwise it is skipped.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.engine.dataset import load_dataset
from app.engine.recommender import recommend
from app.engine.skills import effective_skills, gaps, resolve_target


def naive_baseline(ds, employee_id: str) -> str | None:
    """The single-factor rule the task warns against: recommend for the lowest skill."""
    employee = ds.employees[employee_id]
    effective = effective_skills(ds, employee)
    gap = gaps(ds, employee, effective, resolve_target(ds, employee))
    if not gap:
        return None
    lowest = min((int(effective.get(skill, 0)), skill) for skill in gap)[1]
    for event in ds.events.values():
        if event["mandatory"]:
            continue
        if any(item["skill_id"] == lowest for item in event["develops_skills"]):
            return event["event_id"]
    return None


def check(expectation: dict, result, baseline: str | None) -> tuple[bool, bool]:
    picks = [rec.event_id for rec in result.recommendations]
    ok = True
    if "must_include_any" in expectation:
        ok &= any(pick in expectation["must_include_any"] for pick in picks)
    if "must_not_include" in expectation:
        ok &= all(pick not in expectation["must_not_include"] for pick in picks)
    if "empty_reason" in expectation:
        ok &= result.empty_reason == expectation["empty_reason"]
    if "target_role" in expectation:
        ok &= result.target.role == expectation["target_role"]
    if "first_format_not" in expectation:
        ok &= bool(picks) and result.recommendations[0].format != expectation["first_format_not"]
    # Did the naive baseline fall into the trap? (baseline pick is forbidden, or it
    # recommends where the engine correctly stays empty.)
    picks_set = set(picks)
    diverges = (
        baseline in expectation.get("must_not_include", [])
        or (baseline is not None and not picks_set)              # engine says stop, baseline pushes on
        or (baseline is not None and picks and baseline not in picks_set)
    )
    return ok, diverges


def main() -> int:
    ds = load_dataset(str(ROOT / "data"))
    expectations = json.loads((ROOT / "eval" / "expectations.json").read_text())

    use_ai = bool(__import__("os").environ.get("LLM_API_KEY"))
    ai_fn = None
    if use_ai:
        try:
            from app.llm.decide import ai_recommendation as ai_fn  # type: ignore
        except Exception:
            ai_fn = None

    rows, passed, diverge_count = [], 0, 0
    for employee_id, expectation in expectations.items():
        baseline = naive_baseline(ds, employee_id)
        started = time.perf_counter()
        result = recommend(ds, employee_id)
        rules_ms = round((time.perf_counter() - started) * 1000, 1)
        ok, diverges = check(expectation, result, baseline)
        passed += ok
        diverge_count += diverges

        ai_cell = "—"
        if ai_fn is not None:
            ai_result = ai_fn(ds, employee_id)
            if ai_result is not None:
                ai_cell = ", ".join(rec.event_id for rec in ai_result.recommendations) or "(none)"

        picks = ", ".join(rec.event_id for rec in result.recommendations) or f"∅ {result.empty_reason}"
        rows.append({
            "id": employee_id, "trap": expectation["trap"],
            "baseline": baseline or "—", "rules": picks, "ai": ai_cell,
            "ms": rules_ms, "pass": ok,
        })

    lines = [
        "# Trap-profile evaluation",
        "",
        f"Profiles: **{len(rows)}**  ·  engine correct: **{passed}/{len(rows)}**  ·  "
        f"naive lowest-skill baseline diverges: **{diverge_count}/{len(rows)}**",
        "",
        "Each profile is built so a single-factor rule (\"recommend for the lowest skill\") fails. "
        "The engine combines grade, effective skills, gaps, participation history, prerequisites and "
        "availability; the AI column is the LLM decision layer over the same shortlist. Where the baseline "
        "matches, the lowest-skill activity is coincidentally the correct builder; where it diverges it "
        "recommends a refused, blocked, capped or already-satisfied activity.",
        "",
        "| Profile | Trap | Naive baseline | Engine (rules) | AI | ms | Result |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['id']} | {row['trap']} | {row['baseline']} | {row['rules']} | {row['ai']} | {row['ms']} | {'✅' if row['pass'] else '❌'} |")
    lines.append("")
    (ROOT / "eval" / "RESULTS.md").write_text("\n".join(lines))

    print("\n".join(lines))
    print(f"\nengine {passed}/{len(rows)} correct; baseline diverges on {diverge_count}/{len(rows)}.")
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
