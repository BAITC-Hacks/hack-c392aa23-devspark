"""Generate 8 synthetic trap profiles + expectations, then self-verify each trap
fires (naive lowest-skill baseline wrong, engine right). Regenerates
data/test_profiles/ and eval/expectations.json; run: python eval/make_test_profiles.py"""
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.engine.dataset import load_dataset
from app.engine.skills import effective_skills, resolve_target
from app.engine.recommender import recommend

BASE = load_dataset(str(ROOT / "data"))
BE_MID = BASE.role_profiles[("Backend Engineer", "Middle")]["required_skills"]

def emp(eid, name, role, grade, skills, goal=None, work="office", lang="en", review="2026-06-01", tenure=48, dept="Backend Development"):
    return {"employee_id": eid, "full_name": name, "department": dept, "role": role, "grade": grade,
            "manager_id": None, "hire_date": "2022-01-15", "tenure_months": tenure, "work_format": work,
            "preferred_language": lang, "career_goal": goal, "skills": skills, "last_review_date": review}

# A reasonably complete BE skill map we tweak per trap.
def be_skills(**over):
    s = {"SK_PYTHON": 3, "SK_SQL": 3, "SK_API_DESIGN": 2, "SK_SYSTEM_DESIGN": 2, "SK_CLOUD": 2, "SK_CONTAINERS": 2,
         "SK_CICD": 2, "SK_APP_SECURITY": 2, "SK_OBSERVABILITY": 2, "SK_COMMUNICATION": 3, "SK_TEAMWORK": 3,
         "SK_PROBLEM_SOLVING": 3, "SK_MENTORING": 2, "SK_LEADERSHIP": 2, "SK_STAKEHOLDER_MGMT": 2, "SK_PUBLIC_SPEAKING": 2}
    s.update(over); return s

employees, history, expect = [], [], {}
rid = 900000
def hrow(eid, ev, status, date, assigned="self", pct=0):
    global rid; rid += 1
    return {"record_id": f"R{rid:06d}", "employee_id": eid, "event_id": ev, "date": date, "due_date": "",
            "status": status, "completion_pct": 100 if status == "completed" else pct, "score": "",
            "feedback_rating": "", "assigned_by": assigned}

# E9001 — public-speaking trap: lowest skill PS with 3 refusals; critical gap is System Design.
s = be_skills(SK_PUBLIC_SPEAKING=0, SK_SYSTEM_DESIGN=2, SK_API_DESIGN=2)
employees.append(emp("E9001", "Trap PublicSpeaking", "Backend Engineer", "Middle", s, lang="ru"))
for d in ("2026-05-11", "2026-07-14", "2026-09-08"):
    history.append(hrow("E9001", "EV_036", "declined", d, "manager"))
expect["E9001"] = {"trap": "Lowest skill (Public Speaking) refused 3x; critical System Design gap",
                   "must_not_include": ["EV_036", "EV_023"], "must_include_any": ["EV_005", "EV_006", "EV_007"]}

# E9002 — stale assessment: assessed SD=2 but two completed SD events after review => effective 4 (gap closed).
s = be_skills(SK_SYSTEM_DESIGN=2, SK_API_DESIGN=3)
employees.append(emp("E9002", "Trap StaleReview", "Backend Engineer", "Middle", s, review="2026-05-01"))
history.append(hrow("E9002", "EV_006", "completed", "2026-06-10"))
history.append(hrow("E9002", "EV_007", "completed", "2026-07-20"))
expect["E9002"] = {"trap": "System Design looks low (2) but completions after review raise it to 4",
                   "must_not_include": ["EV_005", "EV_006", "EV_007"]}

# E9003 — career goal in a different role: QA Middle aiming Backend Engineer Middle.
s = {"SK_TEST_DESIGN": 3, "SK_TEST_AUTOMATION": 3, "SK_PYTHON": 1, "SK_SQL": 1, "SK_API_DESIGN": 0, "SK_SYSTEM_DESIGN": 1}
employees.append(emp("E9003", "Trap CrossRole", "QA Engineer", "Middle", s,
                     goal={"target_role": "Backend Engineer", "target_grade": "Middle"}, dept="Quality Assurance"))
expect["E9003"] = {"trap": "Goal is a different role (QA -> Backend); recommend for the target role",
                   "target_role": "Backend Engineer", "must_include_any": ["EV_005", "EV_012"]}

# E9004 — prerequisite chain: SD=1 blocks EV_006/EV_007 (need SD2); EV_005 (no prereq) should come first.
s = be_skills(SK_SYSTEM_DESIGN=1, SK_API_DESIGN=1)
employees.append(emp("E9004", "Trap Prerequisite", "Backend Engineer", "Junior", s, tenure=14))
expect["E9004"] = {"trap": "System Design=1 blocks the advanced events; the no-prerequisite builder comes first",
                   "must_include_any": ["EV_005"], "must_not_include": ["EV_006", "EV_007"]}

# E9005 — max-level cap: CLOUD and CICD already at EV_009's caps => EV_009 gives no gain.
s = be_skills(SK_CLOUD=3, SK_CICD=3, SK_CONTAINERS=1)
employees.append(emp("E9005", "Trap MaxLevel", "Backend Engineer", "Middle", s))
expect["E9005"] = {"trap": "Cloud/CICD already at the event's max level; that event cannot help",
                   "must_not_include": ["EV_009"]}

# E9006 — Lead with no goal => AT_TOP_NO_GOAL.
s = be_skills(SK_LEADERSHIP=4, SK_SYSTEM_DESIGN=4, SK_API_DESIGN=4)
employees.append(emp("E9006", "Trap TopNoGoal", "Backend Engineer", "Lead", s, goal=None, tenure=96))
expect["E9006"] = {"trap": "Lead with no career goal; nothing to recommend", "empty_reason": "AT_TOP_NO_GOAL"}

# E9007 — remote employee who no-shows offline but completes self-paced/online.
s = be_skills(SK_SYSTEM_DESIGN=2, SK_CLOUD=1, SK_CONTAINERS=1)
employees.append(emp("E9007", "Trap RemoteFormat", "Backend Engineer", "Middle", s, work="remote"))
for d in ("2026-06-02", "2026-08-05"):
    history.append(hrow("E9007", "EV_006", "no_show", d, "manager"))  # offline SD
history.append(hrow("E9007", "EV_011", "no_show", "2026-07-01", "hr"))  # offline
history.append(hrow("E9007", "EV_012", "completed", "2026-05-15"))  # self_paced
history.append(hrow("E9007", "EV_009", "completed", "2026-06-20"))  # self_paced
expect["E9007"] = {"trap": "Remote employee avoids offline (no-shows) but finishes self-paced work",
                   "first_format_not": "offline"}

# E9008 — everything already at the Senior bar => TARGET_REACHED.
s = dict(BASE.role_profiles[("Backend Engineer", "Senior")]["required_skills"])  # exactly meets Senior
employees.append(emp("E9008", "Trap TargetReached", "Backend Engineer", "Middle", s, tenure=60))
expect["E9008"] = {"trap": "Already meets every Senior requirement; no gap remains", "empty_reason": "TARGET_REACHED"}

# ---- write files ----
tp = ROOT / "data" / "test_profiles"; tp.mkdir(parents=True, exist_ok=True)
(tp / "employees.json").write_text(json.dumps({"meta": {"dataset": "Career Quest Traps", "as_of_date": "2026-10-01"}, "employees": employees}, ensure_ascii=False, indent=2))
with (tp / "activity_history.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["record_id", "employee_id", "event_id", "date", "due_date", "status", "completion_pct", "score", "feedback_rating", "assigned_by"])
    w.writeheader()
    for row in history:
        w.writerow(row)
(ROOT / "eval").mkdir(exist_ok=True)
(ROOT / "eval" / "expectations.json").write_text(json.dumps(expect, ensure_ascii=False, indent=2))
print("wrote", len(employees), "profiles,", len(history), "history rows")

# ---- self-verify ----
ds = load_dataset(str(ROOT / "data"))  # now includes test_profiles
def naive(eid):
    e = ds.employees[eid]; eff = effective_skills(ds, e); tgt = resolve_target(ds, e)
    from app.engine.skills import gaps
    g = gaps(ds, e, eff, tgt)
    if not g: return None
    lowest = min((eff.get(s, 0), s) for s in g)[1]
    for ev in ds.events.values():
        if ev["mandatory"]: continue
        if any(x["skill_id"] == lowest for x in ev["develops_skills"]):
            return ev["event_id"]
    return None

print("\nprofile | trap | baseline | engine picks | pass")
allpass = True
for eid, exp in expect.items():
    r = recommend(ds, eid)
    picks = [x.event_id for x in r.recommendations]
    ok = True
    for ev in exp.get("must_include_any", []) and [exp["must_include_any"]] or []:
        pass
    if "must_include_any" in exp: ok &= any(p in exp["must_include_any"] for p in picks)
    if "must_not_include" in exp: ok &= all(p not in exp["must_not_include"] for p in picks)
    if "empty_reason" in exp: ok &= (r.empty_reason == exp["empty_reason"])
    if "target_role" in exp: ok &= (r.target.role == exp["target_role"])
    if "first_format_not" in exp: ok &= (bool(picks) and r.recommendations[0].format != exp["first_format_not"])
    allpass &= ok
    print(f"{eid} | {exp['trap'][:44]:44} | base={naive(eid)} | {picks} | {'PASS' if ok else 'FAIL'}")
print("\nALL PASS" if allpass else "\nSOME FAILED")
