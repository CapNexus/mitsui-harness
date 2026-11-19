---
id: F08-S02
feature: F8
title: Build the four read-only tool Lambdas
tier: build
executor: agent
owner: Soma
repo: project-mep-AWS-Code
status: ready
sow: D5
due: 2026-12-02
blocked_by: []
depends_on_stories: [F08-S01]
params: [sme_descriptions_file, limit_list_tables_rows, limit_describe_columns_rows, limit_sample_rows_default, limit_sample_rows_max, limit_run_select_rows, timeout_list_describe_sample_s, timeout_run_select_s, athena_scan_cutoff_gb, identity_mode]   # identity_mode is proposed
human_gates: []
---

## Story

As Soma (solution architect), I want four small Lambda functions that implement the tool contract against Athena, so that the assistant and the Claude clients can discover tables, read descriptions, sample values and run SELECT queries, and nothing else.

## Context

Task list Week 3, Wed Dec 2 (CapNexus AI Engineer). One Lambda per tool (F08-S01 decision). The tools read the Glue Data Catalog for descriptions. Until SME descriptions arrive (F5, due Dec 10), use the placeholder descriptions in `sme_descriptions_file`.

The tools check SQL themselves as well (single SELECT, no write keywords). This is a third layer behind AgentCore Policy (F08-S04) and Lake Formation (F07-S07), not a replacement.

In the sandbox, test against dummy tables in the three databases and the sandbox OIDC provider.

## Acceptance criteria

1. Given a sandbox user, when each tool is called with valid input, then `list_tables` returns only tables the user may see, `describe_columns` returns column names, types and descriptions, `sample_rows` returns up to `limit_sample_rows_default` rows (max `limit_sample_rows_max`), and `run_select` returns rows plus the SQL that ran.
   - verify: `make test-tools` passes (unit and sandbox integration tests). Target created by this story.
2. Given a SELECT returning more than `limit_run_select_rows` rows, when `run_select` runs, then the result is capped and flagged as truncated.
   - verify: the same test suite includes a cap test.
3. Given a query longer than `timeout_run_select_s`, when it runs, then the Athena query is cancelled and a timeout error is returned.
   - verify: the same test suite includes a timeout test.
4. Given non-SELECT or multi-statement SQL, when `run_select` is called, then it is rejected before reaching Athena.
   - verify: the same test suite includes a list of write and multi-statement cases.
5. Given `identity_mode`, when the tools call Athena, then `propagated` uses the caller's identity and `group_fallback` uses a group role and logs the user name, tool and SQL.
   - verify: tests run both modes with a stubbed identity layer.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-17 | A | SME descriptions | Placeholder descriptions |
| DEP-27 | E | Identity mode | Both modes built |

## Evidence

Test output.

## Status log

- 2026-11-19: created
