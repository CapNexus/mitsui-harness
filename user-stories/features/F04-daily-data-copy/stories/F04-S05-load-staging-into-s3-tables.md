---
id: F04-S05
feature: F4
title: Load staged files into S3 Tables with a name map
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Code
status: ready
sow: D3
due: 2026-11-25
blocked_by: []
depends_on_stories: [F04-S04]
params: [approved_table_list, athena_scan_cutoff_gb]
human_gates: []
---

## Story

As Venkat (DevOps), I want a job that loads the staged DMS files into S3 Tables and keeps a source-to-target name map, so that the assistant queries current, lowercase, Parquet-backed tables.

## Context

Data flow steps D5 and D6. DMS writes CSV or Parquet to the staging bucket. This job replaces each approved table in S3 Tables (full load, not incremental) and writes a name mapping table, `wda_meta.name_map` (database, source schema, source table, source column, target table, target column).

Glue or Athena is the engineer's choice (workflow assumption 2). Record the choice and the reason in the repo README. The Athena workgroup has the per-query scan cutoff from `athena_scan_cutoff_gb`.

Tables not on the approved list must never be created. If a staged file has no approved row, the job skips it and logs a warning.

## Acceptance criteria

1. Given staged files for the sandbox tables, when the job runs, then each approved table exists in S3 Tables with lowercase table and column names and the same row count as the staged files.
   - verify: integration test against the sandbox account (`make test-load`).
2. Given a staged file for a table that is not approved, when the job runs, then no S3 table is created for it and a warning is logged.
   - verify: integration test with one extra staged file.
3. Given a completed load, when `wda_meta.name_map` is queried, then every target table and column in S3 Tables has exactly one row (100% coverage), and every target name is lowercase.
   - verify: `make test-name-map` runs the coverage query and expects zero missing and zero uppercase names.
4. Given the job runs twice on the same staged files, when the second run ends, then row counts are unchanged (the load replaces, it does not append).
   - verify: integration test runs the job twice.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-10 | A+C | Approved table list | `fixtures/approved-tables.sandbox.yaml` from F04-S04 |

Needs an S3 table bucket and namespace (proposed parameter `s3_tables_namespace`, default `wda`).

## Evidence

PR with passing integration tests and a sample of `wda_meta.name_map`.

## Status log

- 2026-11-19: created
