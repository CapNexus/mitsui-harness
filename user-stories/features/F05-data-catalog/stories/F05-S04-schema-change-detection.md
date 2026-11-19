---
id: F05-S04
feature: F5
title: Detect schema changes after each load
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Code
status: ready
sow: D3
due: 2026-12-04
blocked_by: []
depends_on_stories: [F05-S03]
params: [sme_descriptions_file, alarm_distribution_list]
human_gates: []
---

## Story

As Venkat (DevOps), I want the catalog checked against the loaded tables after every load, so that a source schema change either updates the catalog or raises an alarm, and the assistant never reads stale column information.

## Context

Feature criterion 5. After the row-count check, the daily load (F04-S08) calls this step through its catalog update hook. It compares the loaded table schemas with the catalog:
- New column: register it, with the comment `DRAFT: no SME description yet`, and add it to a `missing_descriptions` list.
- Removed or retyped column: update the catalog and keep the old description in a change log.
- Any change: publish a `SchemaChanged` metric with the table name.

The alarm on `SchemaChanged` uses the SNS topic from F04-S07. Adding the alarm resource there is a small change to F04-S07's stack, noted in the PR.

## Acceptance criteria

1. Given a sandbox table with a new column, when the step runs after a load, then the column is registered with the draft comment and listed in `missing_descriptions`.
   - verify: integration test adds a column to the sandbox source, runs a load, and checks the catalog.
2. Given a removed column, when the step runs, then the catalog no longer lists it and the change log has the old description.
   - verify: integration test drops a column and checks the catalog and the change log.
3. Given any schema change, when the step runs, then `SchemaChanged` is published with the table name, and the alarm sends an email to the on-call address.
   - verify: integration test checks the metric. `make test-alarm` covers the email route.
4. Given no change, when the step runs, then nothing in the catalog changes and no metric above 0 is published.
   - verify: integration test.

## Dependencies

None beyond F05-S03 and the F04-S08 hook.

## Evidence

PR with passing tests.

## Status log

- 2026-11-19: created
