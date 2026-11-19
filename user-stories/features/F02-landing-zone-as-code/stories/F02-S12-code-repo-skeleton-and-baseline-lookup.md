---
id: F02-S12
feature: F2
title: Create the project CDK app, pipeline and baseline lookup in the Code repository
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Code
status: ready
sow: D2
due: 2026-11-23
blocked_by: []
depends_on_stories: [F02-S02]
params: [aws_home_region, repo_home_url, codeconnections_connection_arn]
human_gates: []
---

## Story

As Venkat (DevOps), I want `project-mep-AWS-Code` to have its own CDK app, pipeline, baseline lookup module and teardown script, so that every project stack (DMS, load jobs, catalog, Lake Formation, tools, assistant, bot) is added in one place and reads the AWS baseline instead of creating it.

## Context

ADR `user-stories/docs/0002-repo-structure-and-roles.md` ("The baseline contract", "Order") and steering `project-context.md` context-6. This is the first story in `project-mep-AWS-Code`, so it runs with the scaffold unlock and sets up the same toolchain as F02-S02 (TypeScript, Jest with 80% coverage, ESLint, Prettier, cdk-nag AwsSolutions, `package-lock.json` committed).

The baseline (VPC, subnets, security groups, KMS key, Identity Center) is deployed by `project-mep-AWS-Infrastructure` and published under SSM `/mep/baseline/*` by F02-S13. This repository never defines those resources. In unit tests the lookup module returns stub values for the same parameter names, so nothing here needs AWS credentials.

Out of scope: any project stack (later F4 to F13 stories), wiring the pipeline to Mitsui's repository (done alongside F02-S09 once DEP-25 is confirmed).

## Acceptance criteria

1. Given a clean checkout, when the validator runs, then install, format, lint, typecheck, test (80% coverage) and `cdk synth` all pass with placeholder values.
   - verify: `scripts/validate.sh` with `HARNESS_TARGET_REPO=project-mep-AWS-Code` exits 0.
2. Given the baseline lookup module, when a stack asks for a baseline value, then it is read from the SSM parameter named in the ADR 0002 contract table, and every name in that table has a typed accessor.
   - verify: unit test compares the module's parameter names with the ADR 0002 table and fails on any difference.
3. Given the source tree, when it is scanned, then no construct creates a VPC, subnet, route, VPN, VPC endpoint or KMS key, and no baseline ID (`vpc-`, `subnet-`, `sg-`, a KMS key ARN) is hard-coded.
   - verify: `npm run lint` includes a custom check (or a Jest test) that fails on these constructs and patterns.
4. Given the pipeline stack, when synthesized, then it has a CodeConnections source (ARN from config), a synth step and a deploy stage for the POC account in us-east-1 that runs after the baseline pipeline.
   - verify: CDK assertion test on the pipeline template passes.
5. Given the teardown script, when run with `--dry-run`, then it lists only this repository's stacks and touches no baseline resource.
   - verify: script test with a stubbed stack list passes; the script refuses to run without `--dry-run` unless `--confirm` is given.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-25 | A+D | Repository and pipeline home | `repo_home_url`, `codeconnections_connection_arn` placeholders |

## Evidence

The PR in `project-mep-AWS-Code` and its passing validator run.

## Status log

- 2026-11-19: created (ADR 0002 purpose split: project infrastructure lives in Code)
