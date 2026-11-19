---
id: F07-S05
feature: F7
title: Build the A/B/C permission test harness
tier: build
executor: agent
owner: Soma
repo: project-mep-AWS-Code
status: ready
sow: D9
due: 2026-12-02
blocked_by: []
depends_on_stories: [F07-S01, F07-S02]
params: [access_matrix_file, masked_column, test_users, identity_mode]   # access_matrix_file, test_users and identity_mode are proposed
human_gates: []
---

## Story

As Soma (solution architect), I want one test harness that runs the same checks as users A, B and C and compares the results with the access matrix, so that the permission tests in Week 3, Week 5 and Week 6 give the same, repeatable evidence through every entry point.

## Context

The acceptance criterion requires identical results through the Gateway, Teams, Claude Code and Claude Desktop. This story builds the harness with two entry points now (direct Athena and Gateway). F10, F11 and F13 add the Teams, Claude Code and Claude Desktop runs using the same expected-results file.

Expected results are derived from `access_matrix_file`. Test user identities come from the proposed `test_users` parameter (A, B, C). Tokens are obtained interactively at run time and never stored.

Out of scope: running it in the POC account (F07-S06).

## Acceptance criteria

1. Given the access matrix, when the harness runs, then it generates expected results per user: tables visible, the masked column visible or not, and write refused.
   - verify: `make test-permission-harness` passes (unit tests on the expected-results generator). Target created by this story.
2. Given the sandbox and three sandbox users, when `scripts/permission-test.sh --env sandbox --entry athena` runs, then it reports pass or fail per user per check and exits 0 only if all pass.
   - verify: the script exits 0 in the sandbox. Script created by this story.
3. Given `--entry gateway`, when the Gateway from F8 exists in the sandbox, then the same checks run through `list_tables`, `sample_rows` and `run_select`.
   - verify: `scripts/permission-test.sh --env sandbox --entry gateway` exits 0 (may be completed after F08-S03).
4. Given a run, when it finishes, then the report is written as Markdown and JSON with the user, entry point, check, expected, actual and time.
   - verify: the report files exist and validate against `tests/permission-report.schema.json`.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-14 | A | Test user names | Sandbox users |
| DEP-16 | A+C | Matrix and masked column | Sandbox matrix |

## Evidence

Sandbox run report.

## Status log

- 2026-11-19: created
