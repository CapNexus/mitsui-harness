---
name: infra
description: "Infrastructure rules for the AWS CDK (TypeScript) project: human-gated work, no deploys, least-privilege IAM and secrets handling."
inclusion: on-demand
---

# Infrastructure Rules

These rules apply to any change under `lib/`, `bin/`, `scripts/` or `test/`, and to any plan that touches AWS resources or customer-owned inputs. Each rule states what an agent MUST do, why, and how it is checked.

## plans-2

**Rule.** For human-gated or customer-approval work, the plan MUST name the person who acts, the exact value or evidence to collect, and where it is recorded (RAID log or `evidence/`). The agent MUST NOT perform the console, account or approval action itself.

- Examples of work this covers: Entra, Control Tower or firewall console changes, AWS account or organization setup, placeholder-to-real-value swaps, and customer sign-offs such as the InfoSec approval and the signed approved table list.
- The agent's part is to prepare the request, record the outcome once a person supplies it, and leave the step open until then.

**Why.** Many stories depend on Mitsui-owned inputs, and the agent can only prepare and record them.

**Check (review).** Reviewer confirms the plan assigns the action to a named person and the diff contains no attempt to perform it.

## commands_scripts-2

**Rule.** Agents MUST NOT run `cdk deploy`, `cdk destroy`, `cdk bootstrap` or any AWS CLI command that creates, changes or deletes resources. Only `npm run synth` is allowed against AWS-facing tooling.

- Deployment goes through the CDK Pipelines pipeline with a person's approval.
- Do not add scripts to `package.json` or `scripts/` that wrap these commands.

**Why.** Deploys change real cloud resources and must go through the pipeline with a person's approval.

**Check (grep).** `cdk (deploy|destroy|bootstrap)` in `package.json` scripts and `scripts/` must return no matches.

## architecture-3

**Rule.** IAM policies MUST NOT use wildcard actions or wildcard resources unless a cdk-nag suppression with a written reason is present. Secrets MUST come from Secrets Manager under the customer-managed KMS key, and no secret value may appear in code, config or logs.

- Source access is read-only. Do not grant write actions to source databases or data stores.
- Reference secrets by name or ARN in CDK code. Never inline the value.
- A cdk-nag suppression must state why the wildcard is unavoidable.

**Why.** Least privilege and read-only access to the sources are the system's core security constraints.

**Check (grep).** `actions:\s*\[\s*['"]\*['"]|AKIA[0-9A-Z]{16}|password\s*[:=]\s*['"]` in `lib/`, `bin/`, `scripts/` and `test/` must return no matches.
