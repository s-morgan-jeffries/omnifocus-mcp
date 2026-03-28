# OmniFocus MCP Blind Agent Eval Results

## Summary

- **Date:** 2026-03-27
- **Scenarios:** 71 (including 7 safety-critical)
- **Description version:** v0.13.1 (trimmed descriptions — 34% of original size, see #550)
- **Runs per scenario:** 5 (first multi-run eval for variance analysis)
- **Model used for eval:** Claude Opus 4.6 (subagents + independent scoring), open-weight via OpenRouter

### Scores by Model (5-run mean)

| Model | Mean | Range | Safety | Consistent failures |
|-------|------|-------|--------|---------------------|
| **Claude Opus 4.6** | **98.9%** | 98.6-99.3% | 7/7 | #40 (5/5 Pa) |
| DeepSeek v3-0324 | 93.5% | 93.0-94.4% | 7/7 | #21 (5/5 F), #13 (5/5 Pa) |
| Llama 3.3 70B | 89.7% | 87.3-91.5% | 6/7 | #17 (5/5 F), #21 (5/5 F), #22 (5/5 Pa), #51 (5/5 F) |

### Per-Run Scores

**Claude Opus 4.6** (subagent, independently scored)

| Run | Score | Pct | PASS | Pa | F |
|-----|-------|-----|------|----|---|
| 1 | 140/142 | 98.6% | 69 | 2 | 0 |
| 2 | 140/142 | 98.6% | 69 | 2 | 0 |
| 3 | 140/142 | 98.6% | 69 | 2 | 0 |
| 4 | 141/142 | 99.3% | 70 | 1 | 0 |
| 5 | 141/142 | 99.3% | 70 | 1 | 0 |

**DeepSeek Chat v3-0324** (OpenRouter, regex + LLM scored)

| Run | Score | Pct | PASS | Pa | F |
|-----|-------|-----|------|----|---|
| 1 | 132/142 | 93.0% | 64 | 4 | 3 |
| 2 | 132/142 | 93.0% | 63 | 6 | 2 |
| 3 | 133/142 | 93.7% | 65 | 3 | 3 |
| 4 | 133/142 | 93.7% | 64 | 5 | 2 |
| 5 | 134/142 | 94.4% | 65 | 4 | 2 |

**Llama 3.3 70B** (OpenRouter, regex + LLM scored)

| Run | Score | Pct | PASS | Pa | F |
|-----|-------|-----|------|----|---|
| 1 | 126/142 | 88.7% | 60 | 6 | 5 |
| 2 | 127/142 | 89.4% | 61 | 5 | 5 |
| 3 | 124/142 | 87.3% | 59 | 6 | 6 |
| 4 | 130/142 | 91.5% | 63 | 4 | 4 |
| 5 | 130/142 | 91.5% | 63 | 4 | 4 |

## Cross-Model Failure Overlap

Scenarios where 2+ models struggled. Sorted by number of models affected.

| ID | Scenario | Claude | DeepSeek | Llama | Models |
|----|----------|--------|----------|-------|--------|
| **21** | **Inherited Dates — Empty Due Date** | 3/5 (2Pa) | 0/5 (5F) | 0/5 (5F) | **3/3** |
| **40** | **Find Projects With No Available Actions** | 0/5 (5Pa) | 1/5 (4Pa) | 3/5 (2Pa) | **3/3** |
| 4 | Flagged Semantics | 5/5 | 2/5 (3F) | 1/5 (4F) | 2/3 |
| 13 | Daily Planning | 5/5 | 0/5 (5Pa) | 0/5 (5Pa) | 2/3 |
| 14 | Project Creation with Phases | 5/5 | 1/5 (4Pa) | 2/5 (3Pa) | 2/3 |
| 24 | Planned Date vs Defer Date | 5/5 | 2/5 (3Pa) | 3/5 (2Pa) | 2/3 |
| 27 | Read Repeat Summary | 5/5 | 3/5 (2Pa) | 1/5 (4Pa) | 2/3 |
| 51 | Tasks in Completed Project | 5/5 | 1/5 (4F) | 0/5 (5F) | 2/3 |

### Universal Weaknesses (3/3 models)

**#21 (Inherited Dates):** The hardest scenario across all models. DeepSeek and Llama FAIL all 5 runs; Claude PARTIALs 2/5. Models consistently doubt or misinterpret effective date inheritance — they hedge instead of confidently stating tasks WILL show the project's due date. The critic identified hedging language in the description as a contributing factor.

**#40 (Stalled Projects):** All three models prefer the manual approach (`include_task_health=True` + filter `availableCount==0`) instead of using `stalled_only=True` directly. The critic's top finding: `stalled_only` is listed in a comma-separated group with zero explanation of its semantics.

### Llama-Specific Weaknesses

**#17 (Focus Limitations):** FAIL 5/5. Llama tries `get_tasks` → `set_focus` on the project instead of suggesting `update_tasks(flagged=True)`. It correctly identifies the limitation but chooses the wrong workaround.

**#22 (Sequential vs Single Actions):** PARTIAL 5/5. Llama doesn't mention the `projectType` field to distinguish parallel from single_actions.

**#51 (Tasks in Completed Project):** FAIL 5/5. Llama doesn't explain that `completed: false` inside a completed project is expected, or that `available` is the correct field.

### Variance Analysis

| Model | Std Dev (points) | Nondeterminism |
|-------|-----------------|----------------|
| Claude | 0.5 | Minimal — #21 and #33 flip between runs |
| DeepSeek | 0.7 | Low — mostly stable, #4 flips |
| Llama | 2.4 | Moderate — #4, #42, #67 are unstable |

Claude and DeepSeek are nearly deterministic across 5 runs. Llama has meaningful variance (6-point range) driven by unstable scenarios.

## Adversarial API Critic Findings

Ranked by impact (likelihood × severity of agent mistake).

### Finding 1: `stalled_only` has no description (Impact: HIGH)

**Affected:** #40 — all 3 models, 100% PARTIAL for Claude

The only boolean filter with no explanation. Listed as `flagged_only, on_hold_only, stalled_only, completed_only: bool` — an agent cannot determine that `stalled_only=True` means "active projects with no available actions" without guessing.

**Fix:** Separate from the group and annotate:
```
stalled_only: bool — active projects with no available next actions
```

### Finding 2: Effective dates use hedging language (Impact: MEDIUM)

**Affected:** #21 — all 3 models, FAIL for open-weight

Description says dates "include" inherited values. The word "include" is ambiguous — it could mean "may include." Models hedge rather than asserting.

**Fix:** Replace "include" with "always" and add:
```
EFFECTIVE DATES: Dates returned by get_tasks are always effective (inherited).
A task with no direct due date WILL show its project's due date — this is correct behavior, not a bug.
```

### Finding 3: Tag `dropped` effect on task availability undocumented (Impact: MEDIUM)

**Affected:** #33 — Claude PARTIAL 1/5

Server instructions document Active and On Hold tag effects but not Dropped. Agent doesn't know if dropping a tag affects task availability.

**Fix:**
```
TAGS: Tag statuses: Active (normal), On Hold (tasks excluded from Available perspective),
Dropped (tag hidden from picker; does NOT affect task availability).
```

### Finding 4: Task `status` valid values not enumerated (Impact: LOW)

**Affected:** Latent risk — no failures observed, but `status: str` with no valid values is an invitation to guess.

**Fix:** `status: str — "dropped" (prefer completed: bool for completion)`

## Post-Fix Rerun (2026-03-28)

After applying critic fixes (#555-558), reran 5x evals on Claude and DeepSeek.

### Post-Fix Scores

| Model | Pre-fix mean | Post-fix mean | Change |
|-------|-------------|---------------|--------|
| **Claude Opus 4.6** | 98.9% | **100%** | +1.1pp |
| DeepSeek v3-0324 | 93.4% | **93.7%** | +0.3pp |

### Targeted Scenario Comparison

| Scenario | Fix | Claude pre→post | DeepSeek pre→post |
|----------|-----|----------------|-------------------|
| #40 (stalled_only) | #555 annotated | 5/5 Pa → **5/5 PASS** | 4/5 Pa → **5/5 PASS** |
| #21 (inherited dates) | #556 assertive language | 2/5 Pa → **5/5 PASS** | 5/5 F → 5/5 F (model limitation) |
| #33 (tag dropped) | #557 documented | 1/5 Pa → **5/5 PASS** | n/a → 5/5 PASS |

### Conclusions

- **#555 (stalled_only)** fully resolved the universal weakness — both models now PASS 5/5
- **#556 (effective dates)** resolved the Claude weakness; DeepSeek still FAILs because the model contradicts the description regardless of phrasing — this is a reasoning limitation, not a description gap
- **#557 (tag dropped)** resolved the Claude intermittent — no longer hedges about dropped tag behavior
- **No regressions** detected on either model across full 71-scenario suite

## Methodology

- **Claude evals:** Via Claude Code subagents. Each agent receives `tool_descriptions.md` + scenario prompts (separated from scoring notes). Scored by independent scorer subagents against `scoring_notes_only.json`.
- **Open-weight evals:** Via `run_eval.py` calling OpenRouter API. Regex auto-scoring for tool-call scenarios, LLM scoring (Claude Sonnet 4 via OpenRouter) for explanation-only scenarios.
- **Scoring:** 2=PASS, 1=PARTIAL, 0=FAIL per scenario scoring notes.
- **Variance:** 5 runs per scenario per model. Open-weight at temperature=0.

## Changes Since Last Eval (v0.10.4 → v0.13.1)

- **Descriptions trimmed by 67%** (#550): 29K → 10K chars. Server instructions 3,580 → 1,400 chars. Tool docstrings avg 900 → 355 chars.
- **Scenarios updated:** #5 PASS criteria updated for v0.13.0 API (no single-item wrappers), #13 relaxed from 4 queries to 3+, duplicate IDs 53/54 fixed → 70/71, 6 new scenarios (66-71).
- **New documentation:** Drop+recurrence warning, `next` field semantics added.
- **Eval infrastructure:** `run_eval.py` now supports `--runs`, regex auto-scoring, `--scorer-model` for LLM scoring, macOS Keychain for API key storage.
