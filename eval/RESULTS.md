# Trap-profile evaluation

Profiles: **8**  ·  engine correct: **8/8**  ·  naive lowest-skill baseline diverges: **4/8**

Each profile is built so a single-factor rule ("recommend for the lowest skill") fails. The engine combines grade, effective skills, gaps, participation history, prerequisites and availability; the AI column is the LLM decision layer over the same shortlist. Where the baseline matches, the lowest-skill activity is coincidentally the correct builder; where it diverges it recommends a refused, blocked, capped or already-satisfied activity.

| Profile | Trap | Naive baseline | Engine (rules) | AI | ms | Result |
|---|---|---|---|---|---|---|
| E9001 | Lowest skill (Public Speaking) refused 3x; critical System Design gap | EV_023 | EV_005, EV_010, EV_009 | EV_005, EV_007, EV_012 | 2.0 | ✅ |
| E9002 | System Design looks low (2) but completions after review raise it to 4 | EV_011 | EV_010, EV_009, EV_040 | EV_010, EV_040, EV_037 | 5.5 | ✅ |
| E9003 | Goal is a different role (QA -> Backend); recommend for the target role | EV_005 | EV_005, EV_012, EV_040 | EV_005, EV_012, EV_040 | 7.1 | ✅ |
| E9004 | System Design=1 blocks the advanced events; the no-prerequisite builder comes first | EV_005 | EV_005 | EV_005 | 5.3 | ✅ |
| E9005 | Cloud/CICD already at the event's max level; that event cannot help | EV_010 | EV_006, EV_005, EV_007 | EV_006, EV_005 | 8.1 | ✅ |
| E9006 | Lead with no career goal; nothing to recommend | — | ∅ AT_TOP_NO_GOAL | — | 7.0 | ✅ |
| E9007 | Remote employee avoids offline (no-shows) but finishes self-paced work | EV_010 | EV_005, EV_007, EV_010 | EV_005, EV_010 | 4.8 | ✅ |
| E9008 | Already meets every Senior requirement; no gap remains | EV_038 | ∅ TARGET_REACHED | — | 7.3 | ✅ |
