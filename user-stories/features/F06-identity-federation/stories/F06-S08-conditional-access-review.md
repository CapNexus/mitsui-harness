---
id: F06-S08
feature: F6
title: Review Conditional Access for pilot, test and IT/PMO users
tier: integrate
executor: mixed
owner: Soma
repo: planning
status: blocked
sow: D4
due: 2026-12-03
blocked_by: [DEP-15]
depends_on_stories: [F06-S02]
params: [entra_groups]
human_gates: [Matt Schiefelbein supplies the policy list, a sign-in test on a Mitsui-managed laptop]
---

## Story

As Soma (solution architect), I want the Conditional Access policies that apply to pilot, test and IT/PMO users reviewed early, so that Claude Code, Claude Desktop and Teams sign-in are not blocked silently in Week 4.

## Context

Task list Week 3, Thu Dec 3 (item 5.5). Mitsui assigns Conditional Access by group. Policies that block loopback or device-code sign-in, require a compliant device, or apply to "All cloud apps" can break the WDA-Clients sign-in and the Teams single sign-on token exchange. The full sign-in test from a managed laptop is Dec 9 (F11); this story finds problems a week earlier.

## Acceptance criteria

1. Given Matt Schiefelbein's policy list, when it is reviewed, then `user-stories/evidence/F06/conditional-access-review.md` lists each policy that applies to the WDA groups and apps, and marks it OK, risk or blocking.
   - verify: the file exists and every row has one of the three marks (`scripts/check-ca-review.sh`, created by this story).
2. Given a blocking or risk policy, when it is listed, then it has a proposed resolution (exclusion, app exception or alternative sign-in flow), an owner and a date.
   - verify: the same script fails if any blocking or risk row lacks a resolution, owner or date.
3. Given a Mitsui-managed laptop and a test user, when WDA-Clients sign-in is tried, then it works, or the failed sign-in log is sent to Matt Schiefelbein.
   - gate: result recorded in the review file.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-15 | D | Policy list and a test sign-in | none |

## Evidence

`user-stories/evidence/F06/conditional-access-review.md`.

## Status log

- 2026-11-19: created
