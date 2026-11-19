# 0002. Repository structure and team roles

Status: accepted (Nov 17, 2026)

## Repository structure

This repository is the main (parent) repository. It holds planning only: features, stories, dependencies, config parameters, evidence and scripts for tracking.

The implementation lives in separate repositories on Mitsui's GitHub Enterprise (`MEPUSA.ghe.com`), added here as git submodules at the repository root. Each submodule is versioned and can be handed over on its own. Planning stays with CapNexus.

Updated Nov 19, 2026: the five proposed `code/` submodules were replaced by the two repositories Mitsui created, split by **purpose**, not by resource type.

| Path (`repo:` value) | Purpose | Content | Features |
|---|---|---|---|
| `project-mep-AWS-Infrastructure` | The **AWS baseline** the project runs on. It exists before the project and would stay if the project were replaced. | CDK: Control Tower landing zone and accounts, Region-deny exceptions, IAM Identity Center and the trusted token issuer, the workload VPC, subnets and their security groups, site-to-site VPN, PrivateLink endpoints, the shared customer-managed KMS key and log encryption, budget alert, Bedrock model access check, baseline pipeline, baseline teardown, and the published baseline contract (below) | F2, F3, F6 (Identity Center, trusted token issuer) |
| `project-mep-AWS-Code` | The **project**: all application code **and the AWS resources that exist only for it**. | CDK and runtime code: DMS replication, endpoints, staging bucket and source secrets, Glue/Athena load jobs and row-count checks, load alarms, S3 Tables and the Glue catalog, Lake Formation grants and masking, the identity-aware Athena workgroup, MCP tool Lambdas, AgentCore Gateway and Policy, the assistant, the Teams bot, audit and monitoring, the eval harness, the project pipeline and project teardown | F4, F5, F6 (Athena workgroup), F7, F8, F9, F10, F11, F12, F13 (code) |
| `planning` (this repo) | Planning and evidence | Stories, evidence, tracking scripts | F1, F13 (evidence), F14 |

The test: *if Mitsui replaced the Well Data Assistant with another project tomorrow, would this resource stay?* Yes → Infrastructure. No → Code.

A story that would touch both submodules is split so each story names one repository.

### The baseline contract

`project-mep-AWS-Code` never creates or changes baseline resources. It reads them from SSM Parameter Store, which `project-mep-AWS-Infrastructure` publishes (F02-S13). Code reads the parameters by name at synth or deploy time, and its unit tests use stub values with the same names.

F02-S13 publishes every parameter. The last column names the story that creates the resource.

| SSM parameter | Value | Resource created by |
|---|---|---|
| `/mep/baseline/vpc-id` | Workload VPC ID | F03-S02 |
| `/mep/baseline/subnets/dms` | DMS subnet IDs (two AZs, the only route to the VPN) | F03-S02 |
| `/mep/baseline/subnets/tools` | Tool and assistant subnet IDs (no route to the VPN) | F03-S02 |
| `/mep/baseline/sg/dms` | DMS security group ID (outbound only to the SQL Server ports and the endpoints) | F03-S02 |
| `/mep/baseline/sg/endpoints` | Security group of the PrivateLink endpoints | F03-S04 |
| `/mep/baseline/kms/key-arn` | Customer-managed KMS key for secrets and logs | F02-S03 |
| `/mep/baseline/identity/instance-arn` | IAM Identity Center instance ARN | F06-S03 |
| `/mep/baseline/identity/tti-arn` | Trusted token issuer ARN | F06-S04 |

Changing a name or meaning in this table is a breaking change: it needs a PR in both submodules and an update here.

### Order

- **Deploy:** Infrastructure first, then Code. A Code stack fails at deploy time if a parameter it needs is missing.
- **Tear down:** Code first, then Infrastructure. The baseline teardown (F02-S05) refuses to run while Code stacks still exist.
- **Network isolation stays in the baseline.** Code places DMS only in the DMS subnets with the DMS security group, and tools only in the tool subnets. It never adds routes, subnets or security-group rules to the baseline.

Rules:
1. A story names the submodule it changes in a `repo:` front-matter field, chosen by the purpose test above.
2. A story is `done` when its PR in the submodule is merged and the parent repo records the new submodule commit and the story status in one commit.
3. Planning files never go into a submodule.

## Roles

| Person | Role | Owns |
|---|---|---|
| Mike | Project manager | F1 stories, status report, RAID log, Mitsui follow-ups, human gates for approvals |
| Soma | Solution architect | Design decisions (type E dependencies), DEP-06 and DEP-27 tests, story review for F8, F9 and F13 |
| Venkat | DevOps | AWS landing zone, IaC, pipeline, network, load pipeline, submodule CI |

Stories use `owner:` for the accountable person. The harness does the work, and the owner reviews and approves.
