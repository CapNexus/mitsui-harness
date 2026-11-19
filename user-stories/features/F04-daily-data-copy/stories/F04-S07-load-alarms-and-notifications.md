---
id: F04-S07
feature: F4
title: Add load alarms and the email topic
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Infrastructure
status: ready
sow: D3
due: 2026-11-25
blocked_by: []
depends_on_stories: [F04-S02]
params: [alarm_distribution_list]
human_gates: []
---

## Story

As a Mitsui DBA on the distribution list, I want an email when the daily load fails, is partial, or skips SDEDBPROD, so that someone acts the same day.

## Context

Load run diagram in `adr/WDA-POC-Data-Workflow.md`. Alarms:
- DMS task failed or stopped (DMS event subscription).
- Partial load: `LoadSucceeded = 0` or `TablesMismatched > 0` (from F04-S06).
- Missed load: no `LoadSucceeded` data point within 2 hours after the window end.
- SDEDBPROD skipped (from F04-S08).

All alarms publish to one SNS topic, encrypted with the customer-managed KMS key, with an email subscription to `alarm_distribution_list`. Until DEP-24 gives the real address, the subscription uses the CapNexus on-call address. The F12 dashboard and other alarms are out of scope.

## Acceptance criteria

1. Given the CDK app, when it is synthesized, then it contains the four alarms above, each with the SNS topic as its alarm action.
   - verify: CDK assertion tests pass.
2. Given the SNS topic, when it is synthesized, then it is encrypted with the customer-managed KMS key and has one email subscription whose address comes from `alarm_distribution_list`.
   - verify: CDK assertion test.
3. Given the stack deployed in the sandbox, when `LoadSucceeded = 0` is published, then the partial-load alarm goes to ALARM and an email reaches the on-call address.
   - verify: `make test-alarm` publishes the metric and checks the alarm state. Email receipt is confirmed by the PR author.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-24 | A | Mitsui distribution list address | CapNexus on-call address in `alarm_distribution_list` |

## Evidence

PR with passing tests and a screenshot of the test alarm email.

## Status log

- 2026-11-19: created
