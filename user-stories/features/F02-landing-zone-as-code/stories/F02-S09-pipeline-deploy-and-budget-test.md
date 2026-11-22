---
id: F02-S09
feature: F2
title: Deploy the baseline through the pipeline and test the budget alert
tier: integrate
executor: mixed
owner: Venkat
repo: project-mep-AWS-Infrastructure
status: blocked
sow: D2
due: 2026-11-20
blocked_by: [DEP-25, DEP-26]
depends_on_stories: [F02-S02, F02-S03, F02-S04, F02-S07]
params: [repo_home_url, billing_contact_email, budget_monthly_usd]
human_gates: [Mitsui authorizes the CodeConnections app on its Git host, billing contact confirms the test alert]
---

## Story

As Venkat (DevOps), I want the pipeline connected to Mitsui's repository and deploying the baseline into the POC account, so that every POC resource comes from code and nothing is clicked in the console.

## Context

F2 criteria 3, 4 and 5. Task list Thu Nov 19 (pipeline skeleton, Budgets alert). The repository is likely `project-mep-AWS-Infrastructure` on `MEPUSA.ghe.com`, which may resolve DEP-25. Check that AWS CodeConnections supports this GitHub Enterprise host before relying on it. The POC account is `Blank Canvas` `108953016877` (RAID I-11, pending Mitsui confirmation in F02-S07). `166390307071` is the Identity Center delegated admin account, not a deployment target for the baseline.

## Acceptance criteria

1. Given Mitsui's repository, when the CodeConnections connection is created and authorized, then its status is AVAILABLE and a push to the main branch starts the pipeline.
   - verify: `aws codeconnections get-connection` shows `AVAILABLE`, and the pipeline execution history shows a run for the pushed commit.
   - gate: a Mitsui Git administrator authorizes the connection app.
2. Given an empty POC account, when the pipeline runs, then the baseline stacks (KMS, logging, budget) deploy with no manual step, and a second run makes no changes.
   - verify: `cdk diff` against the POC account shows no difference after the run.
3. Given the deployed key, when Secrets Manager and log groups in the account are listed, then each uses the customer-managed key.
   - verify: `scripts/check-kms-usage.sh` exits 0. Script is created by this story.
4. Given the deployed budget, when a test notification is sent, then the billing contact receives it.
   - gate: the billing contact confirms receipt. Screenshot or reply saved as evidence.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-25 | A+D | Repository home and connection approval | `repo_home_url` |
| DEP-26 | C+A | Budget approval, amount and billing contact | `budget_monthly_usd`, `billing_contact_email` |

## Evidence

Pipeline run link, `cdk diff` output, KMS check output and the budget alert confirmation, in `evidence/F02/pipeline/`.

## Status log

- 2026-11-19: created
