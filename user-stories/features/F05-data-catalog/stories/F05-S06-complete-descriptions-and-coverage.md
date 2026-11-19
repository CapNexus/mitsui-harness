---
id: F05-S06
feature: F5
title: Complete the descriptions and prove coverage
tier: integrate
executor: mixed
owner: Mike
repo: project-mep-AWS-Code
status: ready
sow: D3
due: 2026-12-10
blocked_by: [DEP-17, DEP-21]
depends_on_stories: [F05-S05]
params: [sme_descriptions_file, question_set_file]
human_gates: [SMEs confirm the descriptions, Noah Jackson approves any missing description as an exception]
---

## Story

As Noah Jackson (Mitsui), I want every table and column used by the question set described by our SMEs, so that the assistant's SQL is based on what our data actually means.

## Context

Week 4 Thu Dec 10: collect the remaining descriptions and load them as table and column comments. The question set is frozen the same day (DEP-21). Coverage is measured against the tables and columns the question set uses (`question_set_file`, Appendix E4 `Tables` column). Mike chases the SMEs weekly (Dec 3) and escalates to Noah if any are missing.

Criterion 4 needs the `describe_columns` tool from F8. If F8 is not deployed, the check runs against the Glue API and is repeated once F8 is live.

## Acceptance criteria

1. Given the frozen question set, when the coverage script runs, then every table and column it uses has an SME description (no `DRAFT:` text), or is on an exception list.
   - verify: `scripts/description-coverage.sh --env poc --questions config/questions.yaml` exits 0. It fails on any uncovered item not on the exception list.
2. Given an exception list, when it is sent, then Noah Jackson approves each exception in writing.
   - gate: Noah Jackson's approval, saved as evidence.
3. Given 10 tables picked at random from the approved list, when `describe_columns` is called for each, then the response contains the catalog description text.
   - verify: `make test-describe-columns SAMPLE=10` exits 0. Before F8 is live, the same script reads the Glue API.
4. Given the final descriptions, when the SMEs review them, then their confirmation is recorded and DEP-17 is set to `resolved`.
   - gate: SME confirmation.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-17 | A | All SME descriptions | Draft text, listed as missing |
| DEP-21 | A | Question set (frozen Dec 10) | Latest draft of `config/questions.yaml` |

## Evidence

`evidence/F05/coverage/`: coverage output, exception approvals, `describe_columns` sample output.

## Status log

- 2026-11-19: created
