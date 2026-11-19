---
id: F04-S06
feature: F4
title: Compare row counts after each load
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Code
status: ready
sow: D3
due: 2026-11-25
blocked_by: []
depends_on_stories: [F04-S05]
params: [approved_table_list]
human_gates: []
---

## Story

As Venkat (DevOps), I want every load checked against the source row counts, so that a load that DMS marks complete after a dropped connection is caught instead of served to users.

## Context

Risk 9: DMS can mark a full load complete after a connection loss even when data is missing. After each load, the check reads the DMS table statistics (rows loaded per table) and compares them with the S3 Tables row counts. If the DMS statistics are not enough, it also runs a `COUNT(*)` on the source through the read-only login.

The check publishes a CloudWatch metric per run: `LoadSucceeded` (1 or 0) and `TablesMismatched` (count). The alarm on these metrics is F04-S07. Each run writes a result row to `wda_meta.load_runs` (run date, table, source count, target count, status). This table is the evidence for the clean-load criteria.

## Acceptance criteria

1. Given a load where all counts match, when the check runs, then it publishes `LoadSucceeded = 1` and `TablesMismatched = 0`, and writes one `ok` row per table to `wda_meta.load_runs`.
   - verify: unit test with matching fixture counts, and integration test in the sandbox.
2. Given a load where one table has fewer target rows than the source, when the check runs, then it publishes `LoadSucceeded = 0` and `TablesMismatched = 1`, and the table's row has status `mismatch`.
   - verify: unit test with a mismatched fixture.
3. Given a DMS task that ended with status `failed` or `stopped`, when the check runs, then it publishes `LoadSucceeded = 0` without loading or comparing.
   - verify: unit test with a failed task status.
4. Given several runs, when `scripts/clean-load-streak` runs, then it prints the number of consecutive clean daily runs up to today.
   - verify: unit test with a fixture of 5 runs where the third failed, expecting a streak of 2.

## Dependencies

None beyond F04-S05.

## Evidence

PR with tests. In production, `wda_meta.load_runs` is the evidence for F04-S11 to F04-S13.

## Status log

- 2026-11-19: created
