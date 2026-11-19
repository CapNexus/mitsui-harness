---
id: F05-S03
feature: F5
title: Register tables in the catalog and load descriptions
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Code
status: ready
sow: D3
due: 2026-11-30
blocked_by: []
depends_on_stories: [F04-S05]
params: [approved_table_list, sme_descriptions_file, crosswalk_rules]
human_gates: []
---

## Story

As Venkat (DevOps), I want a loader that registers every approved table in the Glue Data Catalog and writes the table and column descriptions and join hints from the repo files, so that the catalog is rebuilt the same way every time.

## Context

Data flow step D7. Inputs: the S3 Tables from F04-S05, `wda_meta.name_map` (source names to lowercase target names), `config/descriptions.yaml` and `config/crosswalk.yaml` (copied from the planning repo at deploy time).

The loader writes table comments and column comments. Join hints from the crosswalk are written to the key columns, and each hint names the crosswalk table. Decide whether hints go in the comment text or in Glue column parameters, write it in the README, and tell the F8 team (`describe_columns` must read the same place). Soma reviews the choice.

Descriptions with `source: draft` are loaded with the prefix `DRAFT:` so testers can see they are not SME text. The loader is idempotent.

## Acceptance criteria

1. Given the sandbox S3 Tables, when the loader runs, then every approved table and every column in it is present in the Glue Data Catalog.
   - verify: `make test-catalog` compares `glue get-tables` with the approved list and the name map, and exits 0 only when nothing is missing.
2. Given a descriptions file with SME and draft entries, when the loader runs, then each table and column comment matches the file, and draft entries start with `DRAFT:`.
   - verify: integration test reads the comments back and compares them with the fixture.
3. Given the crosswalk file, when the loader runs, then each key column named in it carries a join hint that names the crosswalk table.
   - verify: integration test checks one join hint per database pair.
4. Given the loader runs twice with the same inputs, when the second run ends, then the catalog is unchanged.
   - verify: integration test compares the catalog before and after the second run.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-17 | A | SME descriptions | Draft text from F05-S01 |
| DEP-13 | A | Crosswalk rules | Sandbox crosswalk |

## Evidence

PR with passing tests and a sample `glue get-table` output.

## Status log

- 2026-11-19: created
