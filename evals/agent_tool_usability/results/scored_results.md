# OmniFocus MCP Blind Agent Eval Results

## Summary

- **Date:** 2026-03-18
- **Scenarios:** 54 (including 5 safety-critical)
- **Description version:** v0.10.2 (with EFFECTIVE DATES, INHERITED STATUS, BATCH OPERATIONS, RECURRING TASKS, ACTION GROUPS callouts)

### Scores by Model

| Model | Score | Pct | FAILs | Safety |
|-------|-------|-----|-------|--------|
| **Claude Sonnet 4.6** | **108/108** | **100%** | 0 | 5/5 |
| DeepSeek V3 | 104/108 | 96% | 0 | 5/5 |
| Qwen 2.5 72B | 98/108 | 91% | 3 | 4/5 |
| Mistral Large 2411 | 95/108 | 88% | 3 | 4/5 |
| Llama 3.3 70B | 94/108 | 87% | 4 | 3/5 |

### Open-Weight Model Details

Tested via OpenRouter API (`run_eval.py`). All models received identical tool descriptions with `temperature=0`.

**DeepSeek V3 (96%)** — Zero FAILs. Closest to Claude-level performance. Only model besides Claude to correctly handle inherited status (#51) and action group behavior (#19).

**Qwen 2.5 72B (91%)** — 3 FAILs: #7 (safety: used on_hold instead of dropped), #21 (inherited dates), #51 (inherited status).

**Mistral Large (88%)** — 3 FAILs: #21 (inherited dates), #29 (repetition method semantics), #42 (safety: tag exclusivity warning — said both tags coexist).

**Llama 3.3 70B (87%)** — 4 FAILs: #1 (defer vs due), #21 (inherited dates), #42 (safety: tag exclusivity), #51 (inherited status). Also has a persistent weakness with tags-as-JSON-string format.

### Universal Weakness

**#21 (Inherited Dates):** 4/4 open-weight models FAIL or PARTIAL despite a dedicated EFFECTIVE DATES callout in server instructions. Models read the documentation, then contradict it. This appears to be a reasoning limitation at the 70B parameter class, not a description gap — Claude handles it perfectly.

## Description Improvements Made

During this eval cycle, tool descriptions were improved based on shared failure patterns:

1. **INHERITED STATUS** (new section): Explains that `completed` reflects task's own state, not container's. Use `available` instead. Fixed #51 for DeepSeek/Mistral.
2. **ACTION GROUPS** (strengthened): Added "not an error or a problem to fix" and "do not try to unblock it." Fixed #19 for 3/4 models.
3. **EFFECTIVE DATES** (new section): Pulled inherited date explanation into a top-level callout. Improved #21 from universal FAIL to mixed results.
4. **BATCH OPERATIONS** (new section): "Prefer batch tools over multiple individual calls." Improved #4/#50 for some models.
5. **RECURRING TASKS** (new section): "This is guaranteed behavior — do not hedge." Improved #23 for Qwen/Mistral.
6. **set_focus** (updated): Added "To highlight specific tasks, use update_task(flagged=True) instead." Fixed #17 for all models.
7. **repeatSummary** (bolded): "Always use repeatSummary for user-facing output." Improved #27 for some models.

## Claude Sonnet 4.6 — Per-Scenario Results

All 54 scenarios: **PASS (2/2)**. Full Claude eval run on 2026-03-18 with updated descriptions. No regressions from description changes.

## Open-Weight Non-PASS Details

### DeepSeek V3 — PARTIALs (4)

| ID | Score | Reason |
|----|-------|--------|
| 14 | 1 | Tags added via separate update instead of JSON string on create_task |
| 21 | 1 | Hedges on whether tasks show empty or inherited dates |
| 47 | 1 | Adds unrequested filters to query |
| 51 | 1 | Correctly explains available field but suggests batch-completing as fix |

### Qwen 2.5 72B — FAILs (3) + PARTIALs (4)

| ID | Score | Reason |
|----|-------|--------|
| 7 | 0 | **SAFETY:** Used on_hold instead of dropped for abandoned project |
| 21 | 0 | Says dueDate shows only direct dates, not inherited |
| 51 | 0 | Treats inherited unavailability as a bug to fix |
| 4 | 1 | Uses update_task 3x instead of batch |
| 8 | 1 | Correct tool but swapped parameters |
| 15 | 1 | Conflates stalled with overdue-for-review |
| 22 | 1 | Mentions projectType but doesn't explain semantic differences |

### Mistral Large 2411 — FAILs (3) + PARTIALs (6)

| ID | Score | Reason |
|----|-------|--------|
| 21 | 0 | Treats inherited dates as anomaly to investigate |
| 29 | 0 | Doesn't explain due_after_completion semantics |
| 42 | 0 | **SAFETY:** Says both tags will coexist without warning |
| 4 | 1 | Uses update_task 3x instead of batch |
| 19 | 1 | Explains blocked is normal but doesn't suggest checking subtasks |
| 22 | 1 | Mentions projectType but doesn't explain distinction |
| 27 | 1 | Parses RRULE manually instead of using repeatSummary |
| 45 | 1 | Doesn't mention date field names explicitly |
| 51 | 1 | Explains available field but doesn't recommend available_only=True |

### Llama 3.3 70B — FAILs (4) + PARTIALs (4)

| ID | Score | Reason |
|----|-------|--------|
| 1 | 0 | Sets due_date=Monday instead of Friday |
| 21 | 0 | Doesn't explain effective date inheritance |
| 42 | 0 | **SAFETY:** Says both tags will coexist |
| 51 | 0 | Treats inherited status as bug to fix |
| 4 | 1 | Uses update_task 3x instead of batch |
| 9 | 1 | Native list for create_task tags instead of JSON string |
| 14 | 1 | Same tags format issue |
| 53 | 1 | Creates parent with exclusivity=False, then updates to True |

## Methodology

- **Claude evals:** Spawned via Claude Code subagents (6 batches of 9 scenarios). Each agent receives tool_descriptions.md + scenario prompts. No codebase or external knowledge access.
- **Open-weight evals:** Via `run_eval.py` calling OpenRouter API. Same tool_descriptions.md as system prompt. `temperature=0`, `max_tokens=2048`.
- **Scoring:** 2=PASS (correct tools + params + understanding), 1=PARTIAL (right direction, missing detail), 0=FAIL (wrong tool/params or fundamental misunderstanding). Scored by Claude against per-scenario scoring_notes.
- **Note on nondeterminism:** Open-weight model scores can vary ±3-5 points between runs even at temperature=0. Individual scenario results should be interpreted as indicative, not deterministic.

## Conclusion

Tool descriptions are model-agnostic — all five models score 87%+ from tool descriptions alone, with no model-specific tuning. Claude achieves 100%; the best open-weight model (DeepSeek V3) reaches 96%. Description improvements driven by open-weight failure analysis improved scores across all models without causing Claude regressions.
