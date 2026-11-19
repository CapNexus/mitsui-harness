---
id: F08-S04
feature: F8
title: Enforce SELECT-only, row limits and timeouts with AgentCore Policy
tier: build
executor: agent
owner: Soma
repo: project-mep-AWS-Code
status: ready
sow: D5
due: 2026-12-03
blocked_by: []
depends_on_stories: [F08-S03]
params: [limit_list_tables_rows, limit_describe_columns_rows, limit_sample_rows_max, limit_run_select_rows, timeout_list_describe_sample_s, timeout_run_select_s, timeout_question_s]
human_gates: [Soma reviews the policy rules]
---

## Story

As Soma (solution architect), I want AgentCore Policy to allow only the four approved tools, only single SELECT statements, and only within the agreed limits, so that write attempts are refused at the first layer and logged.

## Context

Task list Week 3, Thu Dec 3. Workflow step Q7. This is the first of two refusal layers. Lake Formation is the second (F07-S07). Limits come from `config/parameters.md` (Feature List Section 6). If AgentCore Policy cannot express a rule (for example parsing SQL), the rule is enforced in the tool (F08-S02) and the gap is recorded.

## Acceptance criteria

1. Given the policy as code, when synthesized, then only `list_tables`, `describe_columns`, `sample_rows` and `run_select` are allowed, and limit and timeout values come from the parameters.
   - verify: `make test-policy` passes. Target created by this story.
2. Given INSERT, UPDATE, DELETE, DROP, CREATE, MERGE and a multi-statement SQL with a write, when sent to `run_select` through the Gateway, then each is refused by the Policy and a refusal log entry exists with user, tool, SQL and time.
   - verify: `scripts/test-gateway.sh --env sandbox --case write-refusal` exits 0 and finds a log entry per case.
3. Given a call to a tool name that is not one of the four, when sent through the Gateway, then it is refused.
   - verify: the same script includes this case.
4. Given the rules, when reviewed, then any rule the Policy cannot express is listed in `docs/policy-gaps.md` with where it is enforced instead.
   - gate: Soma reviews.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-06 | A+D | AgentCore Policy available in us-east-1 | Sandbox in us-east-1 |

## Evidence

Test output and refusal log samples.

## Status log

- 2026-11-19: created
