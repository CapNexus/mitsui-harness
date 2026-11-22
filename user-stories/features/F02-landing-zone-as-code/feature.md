---
id: F2
title: AWS landing zone and POC account as code
sow: D2
due: 2026-11-20
status: draft
depends_on_features: [F1]
blocked_by: [DEP-02, DEP-03, DEP-06, DEP-25, DEP-26]
---

## Description

Build an AWS Control Tower landing zone in Mitsui's new management account (home Region us-east-1) with Log Archive and Audit accounts, Security and Workloads OUs, one POC workload account, default controls, organization trail and AWS Config. Enable IAM Identity Center. Deliver the baseline as CDK infrastructure as code with a pipeline, KMS keys, logging, a budget alert, and teardown scripts. Allow Region-deny exceptions for us-east-2 and us-west-2 so Claude cross-region inference works.

Source: `WDA-POC-Feature-List.md`, F2. Drift and compliance exports run again on Dec 17 and Dec 23.

## Feature-level acceptance criteria

| # | Criterion | Covered by |
|---|---|---|
| 1 | Control Tower shows the landing zone as Active, with Log Archive, Audit and POC workload accounts enrolled and no drift. | F02-S06, F02-S07, F02-S11 |
| 2 | The Region-deny control allows us-east-1, us-east-2 and us-west-2, and a Bedrock Claude call from the POC account succeeds. | F02-S01, F02-S06, F02-S08 |
| 3 | All POC resources deploy from the IaC repository through the pipeline from an empty account. Manual console changes are not required. | F02-S02, F02-S09 (baseline), F02-S12 (project) |
| 4 | A customer-managed KMS key exists and is used for Secrets Manager and logs. | F02-S03, F02-S09 |
| 5 | An AWS Budgets alert reaches the billing contact (send a test). | F02-S04, F02-S09 |
| 6 | The temporary cross-account role is deleted by Mitsui after use, and Mitsui sends CloudTrail review confirmation. | F02-S10 |
| 7 | A Control Tower console export (no drift, controls compliant, account enrolled) is saved as acceptance evidence, once in Week 5 and once in Week 6. | F02-S11 |
| 8 | A teardown script removes the POC resources in a test run and leaves the landing zone intact. | F02-S12 (project stacks first), F02-S05 (baseline) |

## Stories

| ID | Title | Tier | Executor | Blocked by | Status |
|---|---|---|---|---|---|
| [F02-S01](stories/F02-S01-preflight-and-service-availability.md) | Run the pre-flight checks and confirm services in us-east-1 | integrate | mixed | DEP-06 | in-progress |
| [F02-S02](stories/F02-S02-cdk-app-and-pipeline-skeleton.md) | Create the CDK app and pipeline skeleton | build | agent | none | ready |
| [F02-S03](stories/F02-S03-kms-and-logging-baseline.md) | Build the KMS key and log encryption baseline | build | agent | none | ready |
| [F02-S04](stories/F02-S04-budget-alert-construct.md) | Build the AWS Budgets alert | build | agent | none | ready |
| [F02-S05](stories/F02-S05-teardown-script.md) | Write and test the teardown script | build | agent | none | ready |
| [F02-S06](stories/F02-S06-control-tower-landing-zone.md) | Verify the Control Tower landing zone and Region-deny exceptions | integrate | mixed | DEP-02 | blocked |
| [F02-S07](stories/F02-S07-poc-account-and-identity-center.md) | Verify the POC workload account and IAM Identity Center | integrate | mixed | DEP-02 | blocked |
| [F02-S08](stories/F02-S08-bedrock-claude-access.md) | Prove a Bedrock Claude call works from the POC account | integrate | mixed | DEP-06 | blocked |
| [F02-S09](stories/F02-S09-pipeline-deploy-and-budget-test.md) | Deploy the baseline through the pipeline and test the budget alert | integrate | mixed | DEP-25, DEP-26 | blocked |
| [F02-S10](stories/F02-S10-remove-cross-account-role.md) | Confirm the elevated cross-account access is removed or scoped | integrate | human | DEP-02 | blocked |
| [F02-S11](stories/F02-S11-control-tower-evidence-exports.md) | Export Control Tower drift and compliance evidence | integrate | mixed | DEP-02 | blocked |
| [F02-S12](stories/F02-S12-code-repo-skeleton-and-baseline-lookup.md) | Create the project CDK app, pipeline and baseline lookup in the Code repository | build | agent | none | ready |
| [F02-S13](stories/F02-S13-publish-baseline-contract.md) | Publish the baseline contract for the Code repository | build | agent | none | ready |

Order: S02 first (S03, S04 and S05 build on it). S12 creates the Code repository's own CDK app after S02 and is the first story in `project-mep-AWS-Code` (scaffold unlock). S13 publishes the baseline contract once S03 and the F3 network stacks exist. S01, then S06, then S07. S08 and S09 need S07. S10 follows S06 and S07. S11 runs on Dec 17 and Dec 23.

## Open points

- ADR 0002 splits by purpose: this repository (`project-mep-AWS-Infrastructure`) is the AWS baseline; the project's own resources live in `project-mep-AWS-Code` and read the baseline from SSM `/mep/baseline/*` (S13 publishes, S12 reads).

- DEP-25 may already be resolved: Mitsui created `project-mep-AWS-Infrastructure` on `MEPUSA.ghe.com`. Confirm with Mitsui and set `repo_home_url`. AWS CodeConnections must support GitHub Enterprise Cloud with a data-residency (`ghe.com`) host; check this in F02-S09.
- The cross-account role expires after 7 days and is deleted Fri Nov 20. Any management-account work after that (S11, Identity Center switch in F6) needs Identity Center access for CapNexus. Agree this with Noah before the role is deleted.
- The Bedrock model ID is not chosen ("Claude is default"). F02-S08 needs one to test. Proposed new parameter `bedrock_model_id`.
- Task list Thu Nov 19 says "TypeScript or Python with AWS CDK". F02-S02 needs one choice before it starts.
