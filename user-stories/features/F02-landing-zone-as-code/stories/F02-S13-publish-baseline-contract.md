---
id: F02-S13
feature: F2
title: Publish the baseline contract for the Code repository
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Infrastructure
status: ready
sow: D2
due: 2026-11-24
blocked_by: []
depends_on_stories: [F02-S03, F03-S02, F03-S04]
params: [aws_home_region]
human_gates: [Soma approves any change to the contract table in ADR 0002]
---

## Story

As Venkat (DevOps), I want the baseline to publish the values the project needs as SSM parameters under `/mep/baseline/`, so that `project-mep-AWS-Code` can deploy on top of it without knowing or changing how the baseline is built.

## Context

ADR `user-stories/docs/0002-repo-structure-and-roles.md`, "The baseline contract". The parameters are plain `String`/`StringList` SSM parameters in the POC account, home Region. They hold IDs and ARNs only, never secrets. The Identity Center values (`/mep/baseline/identity/*`) are published once F06-S03 and F06-S05 have run; until then those two parameters hold the value `pending`, and Code stacks that need them fail at deploy with a clear message.

Out of scope: consuming the parameters (F02-S12 and later Code stories).

## Acceptance criteria

1. Given the baseline stacks, when synthesized, then there is one SSM parameter for every row of the ADR 0002 contract table, with exactly that name, and each value references the resource that creates it (no literals except `pending`).
   - verify: CDK assertion test compares the synthesized parameter names with the ADR 0002 table and fails on any difference.
2. Given the parameters, when their types are checked, then subnet lists are `StringList` and all others are `String`, and none is a `SecureString`.
   - verify: the same assertion test checks the types.
3. Given a change to a parameter name or meaning, when the PR is opened, then the ADR 0002 table is updated in the parent repository in the same change set.
   - gate: Soma approves the contract change in the PR.

## Dependencies

None beyond the stories it depends on.

## Evidence

The PR in `project-mep-AWS-Infrastructure` and its passing assertion test.

## Status log

- 2026-11-19: created (ADR 0002 purpose split: baseline contract)
