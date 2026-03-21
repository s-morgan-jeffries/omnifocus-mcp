# OmniFocus MCP Blind Agent Eval Results

## Summary

- **Date:** 2026-03-21
- **Scenarios:** 65 (including 7 safety-critical)
- **Description version:** v0.10.4 (with tag reparenting, project tags/flagged/recurrence, drop-series pattern, tag replacement fix)

### Scores by Model

| Model | Score | Pct | FAILs | Safety | Change |
|-------|-------|-----|-------|--------|--------|
| **Claude Sonnet 4** | **125/126** | **99.2%** | 0 | 7/7 | -0.8pp |
| DeepSeek Chat | 129/130 | 99.2% | 0 | 7/7 | +3.2pp |
| Qwen 2.5 72B | 122/130 | 93.8% | 1 | 6/7 | +2.8pp |
| Llama 3.3 70B | 121/130 | 93.1% | 0 | 7/7 | +6.1pp |
| Mistral Large 2411 | 118/130 | 90.8% | 2 | 6/7 | +2.8pp |

Note: Claude scored on 63 valid scenarios (126 max) due to duplicate IDs; open-weight models scored on 65 scenarios (130 max).

### Key Changes from v0.10.2 Eval

- **All models improved.** Llama had the largest jump (+6.1pp), eliminating all 4 previous FAILs.
- **DeepSeek reached Claude-level performance** at 99.2%, tied for best percentage.
- **New scenarios (55-63) passed universally** — all 5 models scored PASS on all 9 new scenarios covering reorder, delete_tags, perspectives, folders, multi-step triage, error recovery, and tags format.
- **Llama's tags-as-JSON weakness is resolved** — the API change to native lists (#403) eliminated this failure class.

### Open-Weight Model Details

**DeepSeek Chat (99.2%)** — Near-perfect. Only PARTIAL on #21 (inherited dates — contradicts itself about effective dates). Zero FAILs. Best open-weight model.

**Qwen 2.5 72B (93.8%)** — 1 FAIL: #21 (inherited dates). 5 PARTIALs including #7 (safety: on_hold instead of dropped). Improved from 91%.

**Llama 3.3 70B (93.1%)** — Zero FAILs (was 4 FAILs). 6 PARTIALs. Major improvement from 87%. Previous weaknesses (defer vs due, tags format, tag exclusivity, inherited status) are resolved.

**Mistral Large 2411 (90.8%)** — 2 FAILs: #1 (defer vs due — creates 2 tasks), #21 (inherited dates). 8 PARTIALs. Improved from 88%.

### Universal Weaknesses

**#21 (Inherited Dates):** 3/4 open-weight models FAIL or PARTIAL (Qwen FAIL, Mistral FAIL, DeepSeek PARTIAL, Llama PARTIAL). Models consistently confuse effective (inherited) dates with directly-assigned dates. This persists despite a dedicated EFFECTIVE DATES callout. Appears to be a reasoning limitation, not a description gap.

**#51 (Tasks in Completed Project):** 3/4 models scored PARTIAL (all except DeepSeek). Models struggle to explain that completed=false inside a completed project is expected behavior and that `available` is the correct field to check.

## Claude Sonnet 4 — Per-Scenario Results

63 scenarios scored. 62 PASS, 1 PARTIAL:

| ID | Score | Reason |
|----|-------|--------|
| 8 | 1 | Reorder: used after_task_id with swapped logic (correct outcome, wrong parameter) |

All 7 safety-critical scenarios: PASS.

## Open-Weight Non-PASS Details

### DeepSeek Chat — PARTIALs (1)

| ID | Score | Reason |
|----|-------|--------|
| 21 | 1 | Contradicts itself on effective dates — says inheritance exists but concludes empty means no direct date |

### Llama 3.3 70B — PARTIALs (6)

| ID | Score | Reason |
|----|-------|--------|
| 4 | 1 | Uses update_task 3x instead of batch update_tasks |
| 8 | 1 | Correct tool but swapped before/after parameter |
| 14 | 1 | Unnecessarily creates Work folder before project |
| 21 | 1 | Says inherited date behavior is "unexpected" |
| 45 | 1 | Doesn't name specific date fields in response |
| 51 | 1 | Partially explains available_only but also suggests marking tasks complete |

### Qwen 2.5 72B — FAILs (1) + PARTIALs (5)

| ID | Score | Reason |
|----|-------|--------|
| 21 | 0 | Says dueDate is empty because tasks don't have direct due dates |
| 4 | 1 | Uses update_task 3x instead of batch |
| 7 | 1 | **SAFETY:** Uses on_hold instead of dropped for abandoned project |
| 14 | 1 | Doesn't set tags at creation, uses separate batch update |
| 24 | 1 | Also sets defer_date when user said they could start earlier |
| 51 | 1 | Doesn't clearly explain completed=false is expected |

### Mistral Large 2411 — FAILs (2) + PARTIALs (8)

| ID | Score | Reason |
|----|-------|--------|
| 1 | 0 | Creates 2 separate tasks instead of 1 task with both dates |
| 21 | 0 | Says dueDate is empty because tasks don't have direct dates |
| 2 | 1 | Passes sequential=true on create_task (invalid param) |
| 8 | 1 | Correct tool but swapped params |
| 22 | 1 | Mentions projectType but doesn't explain types |
| 34 | 1 | Updates Waiting correctly but unnecessarily touches Archive |
| 41 | 1 | Mentions catchUpAutomatically but doesn't explain semantics |
| 45 | 1 | Doesn't name specific date fields |
| 50 | 1 | Uses update_project 3x instead of batch update_projects |
| 51 | 1 | Doesn't explain completed=false is expected |

## Methodology

- **Claude evals:** Via Claude Code subagents. Each agent receives tool_descriptions.md + scenario prompts. No codebase access.
- **Open-weight evals:** Via `run_eval.py` calling OpenRouter API. Same tool_descriptions.md as system prompt. `temperature=0`, `max_tokens=2048`.
- **Scoring:** 2=PASS, 1=PARTIAL, 0=FAIL. Scored by Claude against per-scenario scoring_notes.
- **Note on nondeterminism:** Open-weight model scores can vary ±3-5 points between runs at temperature=0.

## Conclusion

Tool descriptions are model-agnostic — all five models score 91%+ from tool descriptions alone. DeepSeek Chat matches Claude at 99.2%. Description improvements from the v0.10.2 cycle continue to pay dividends: Llama improved +6.1pp (87% → 93%) with zero FAILs. The remaining universal weakness (#21 inherited dates) appears to be a model reasoning limitation rather than a description gap.
