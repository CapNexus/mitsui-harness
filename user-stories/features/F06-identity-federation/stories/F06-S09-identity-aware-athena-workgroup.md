---
id: F06-S09
feature: F6
title: Build the identity-aware Athena workgroup as code
tier: build
executor: agent
owner: Soma
repo: project-mep-AWS-Code
status: ready
sow: D4
due: 2026-11-25
blocked_by: []
depends_on_stories: [F02-S12]
params: [aws_home_region, athena_scan_cutoff_gb]
human_gates: []
---

## Story

As Soma (solution architect), I want the project's Athena workgroup defined as CDK code with IAM Identity Center authentication and a scan cutoff, so that every query the tools run is attributed to the signed-in user and a bad query cannot scan the whole lake.

## Context

Workflow step I3 and Feature List Section 6 (10 GB per-query cutoff). Split from F06-S04 under ADR 0002: the workgroup exists only for this project, so it lives in `project-mep-AWS-Code`. The trusted token issuer and Identity Center stay in the baseline (F06-S04, F06-S05). The workgroup reads the Identity Center instance ARN from `/mep/baseline/identity/instance-arn` through the F02-S12 lookup module; unit tests stub it.

Out of scope: Lake Formation grants (F7), the propagation test (F06-S06, F06-S07).

## Acceptance criteria

1. Given the stack, when synthesized, then it creates an Athena workgroup with IAM Identity Center authentication enabled, using the instance ARN from the baseline contract.
   - verify: CDK assertion test on the workgroup properties passes.
2. Given the workgroup, when synthesized, then its per-query scan cutoff equals `athena_scan_cutoff_gb`, results are encrypted with `/mep/baseline/kms/key-arn`, and the workgroup configuration is enforced.
   - verify: the same test checks the cutoff, encryption and enforcement.
3. Given the source, when scanned, then no Identity Center instance ARN, account ID or key ARN is hard-coded.
   - verify: the F02-S12 baseline-literal check passes.

## Dependencies

None. Identity Center values come from the baseline contract; stubs are used until F06-S03 runs.

## Evidence

Test output in the PR.

## Status log

- 2026-11-19: created (split from F06-S04 under ADR 0002)
