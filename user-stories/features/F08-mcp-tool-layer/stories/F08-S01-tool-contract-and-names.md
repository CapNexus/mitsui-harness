---
id: F08-S01
feature: F8
title: Define the tool contract, limits and names
tier: build
executor: agent
owner: Soma
repo: project-mep-AWS-Code
status: ready
sow: D5
due: 2026-11-30
blocked_by: []
depends_on_stories: []
params: [limit_list_tables_rows, limit_describe_columns_rows, limit_sample_rows_default, limit_sample_rows_max, limit_run_select_rows, timeout_list_describe_sample_s, timeout_run_select_s, timeout_question_s, athena_scan_cutoff_gb, identity_mode]   # identity_mode is proposed
human_gates: [Soma approves the tool contract and the compute decision]
---

## Story

As Soma (solution architect), I want one written contract for the four tools (names, inputs, outputs, limits and errors), so that the Lambdas, the Gateway, the Policy, the assistant prompt and the runbook all use the same names and numbers.

## Context

Feature List Section 5, gap 2 (`run_select` vs `run_select_query`) and Section 6 (one Lambda per tool as a Gateway target, starting limits). The limits live in `config/parameters.md` and are read at deploy time, not hard-coded.

The contract also states how each tool behaves under `identity_mode` (DEP-27): `propagated` uses the caller's token through the trusted token issuer, `group_fallback` uses a group role and logs the user.

## Acceptance criteria

1. Given the contract, when it is written, then `docs/tool-contract.md` and `schemas/tools/*.json` define `list_tables`, `describe_columns`, `sample_rows` and `run_select` with input schema, output schema, limit, timeout and error codes.
   - verify: `make test-tool-schemas` validates every schema file. Target created by this story.
2. Given the code, policy and docs, when the name check runs, then no file uses `run_select_query` and all four tool names match the contract.
   - verify: `scripts/check-tool-names.sh` exits 0. Script created by this story.
3. Given the limits, when the contract is generated, then each limit and timeout value comes from the parameter names in `config/parameters.md`, and a limits table is produced for the runbook.
   - verify: `scripts/render-limits.sh` writes `docs/limits.md` and the test checks it matches the parameters.
4. Given the compute proposal (Lambda per tool, Gateway Lambda targets), when it is reviewed, then it is recorded as a decision.
   - gate: Soma approves. Decision added to the RAID log.

## Dependencies

None. Limits are proposed defaults and can be changed by Mitsui later.

## Evidence

Contract, schemas, name check output.

## Status log

- 2026-11-19: created
