---
id: F02-S05
feature: F2
title: Write and test the teardown script
tier: build
executor: agent
owner: Venkat
repo: project-mep-AWS-Infrastructure
status: ready
sow: D2
due: 2026-12-17
blocked_by: []
depends_on_stories: [F02-S02]
params: []
human_gates: [Venkat approves each real teardown run]
---

## Story

As Venkat (DevOps), I want a script that removes the POC baseline resources and leaves the Control Tower landing zone alone, so that Mitsui can stop paying for the POC after the readout and redeploy it later from the repository.

## Context

F2 criterion 8, end-to-end scenario E2E-8, and the runbook (F14). The task list finishes the script on Thu Dec 17. It is built now in the sandbox and extended as each new stack is added. The landing zone, Log Archive and Audit accounts and the retained KMS key are not removed.

Under ADR 0002 the project's own stacks are torn down first by the `project-mep-AWS-Code` teardown script (F02-S12). This script removes the baseline only, after that.

## Acceptance criteria

1. Given the deployed POC stacks, when the script runs with `--dry-run`, then it lists every stack it would delete in dependency order and changes nothing.
   - verify: `scripts/teardown.sh --dry-run --stage sandbox` exits 0 and lists the same stacks as `cdk list`.
2. Given the sandbox account, when the script runs for real, then all POC stacks are deleted, S3 buckets are emptied first, and Control Tower resources are untouched.
   - verify: after the run, `aws cloudformation list-stacks` shows no active POC stacks, and no stack named `AWSControlTower*` or `StackSet-AWSControlTower*` changed.
3. Given a torn-down sandbox, when the pipeline redeploys, then the environment returns to the same state.
   - verify: `cdk diff` after redeploy shows no difference.
4. Given the script, when it starts, then it requires the operator to type the account ID, and it refuses to run in the management account.
   - verify: unit tests for both refusal cases pass.

5. Given stacks from `project-mep-AWS-Code` still exist in the POC account, when the script runs, then it stops before deleting anything and names those stacks.
   - verify: script test with a stubbed stack list that includes a Code stack exits non-zero and deletes nothing.

## Dependencies

None.

## Evidence

Dry-run and real-run logs from the sandbox in `evidence/F02/teardown/`.

## Status log

- 2026-11-19: created
- 2026-11-19: baseline-only teardown; refuses while Code stacks exist (ADR 0002 order)
