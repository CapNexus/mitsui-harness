---
name: plan_cdk_infrastructure
description: "Plan CDK resources, synth assertion tests, cdk-nag handling and IAM scope with EARS criteria."
mode: on-demand
---

# Plan a CDK infrastructure change

Write an implementation plan for one story that defines AWS resources in CDK (TypeScript). You are the **builder** agent. Your only deliverable is the plan file and the envelope described at the end. Do NOT write CDK code, tests, or scripts, and do NOT run `cdk deploy`, `cdk bootstrap`, or any command that changes a live AWS account. The plan will be executed later by the `write_tests` and `implement` steps.

## Variables

issue: $1
classification: $2

## Instructions

- The issue text is `$1`. It contains the story id (for example `F04-S02`), the story text and its acceptance criteria. The classification is `$2`. If it is not `cdk-infrastructure`, say so in `## Notes` and plan only the CDK part of the issue.
- Cite the story id from the issue in the plan title and in a `Story:` line near the top. The `plan_exists` check fails without it.
- Research before planning. Read `README.md`, `package.json` and `ENGINEERING-STANDARDS.md` if they exist. Then read whatever exists under `bin/`, `lib/` and `test/`, plus the steering files that apply: `core` (`architecture-1`, `architecture-2`, `types-1`, `types-2`, `standard_output-1`, `standard_output-2`, `plans-1`), `infra` (`plans-2`, `commands_scripts-2`, `architecture-3`) and `testing` (`tests-1`, `tests-2`, `tests-3`). The codebase may be nearly empty. Where `lib/` has no precedent, name the construct and stack layout you propose and the reason.
- Do not guess at resources. Every resource, property and IAM action in the plan must trace to a sentence in the issue or to a constraint below. Put anything the issue leaves undecided in `## Open Questions` and do not invent a value for it.
- Replace every angle-bracket slot in the Plan Format with real content. Leave no template slot text in the file.
- Write the plan file in the plans location defined by the `plans` steering files. If they name none, use `specs/<story-id>-<short-slug>.md`.

### Constraints the plan must respect

- **Entry points and layout.** Stacks and constructs go under `lib/`, the app entry is `bin/app.ts`, tests go under `test/`. Prefer one construct per concern over a large stack.
- **Types.** TypeScript strict. Props are typed interfaces. No `any`, no untyped context lookups. Configuration comes from typed props or a typed config object, so that promotion between environments is a config-only change.
- **Region.** Home Region is `us-east-1`. Only `us-east-2` and `us-west-2` are permitted exceptions. State the Region of every resource that is not in the home Region and why.
- **IAM.** Least privilege. List each role with its principal, its actions and its resource ARNs. No `*` in actions or resources unless the AWS API requires it. If one is required, record the reason in the plan. Tool Lambdas behind the gateway and anything touching source data get read-only permissions and no write path.
- **Secrets and keys.** Secrets live in Secrets Manager under a customer-managed KMS key. No secret value, account id, or credential appears in code, tests, plan, or logs. Use references and parameters.
- **Storage and transport.** S3 buckets block all public access, enforce TLS, and are KMS-encrypted. Network resources keep egress to the narrowest CIDRs, ports and endpoints the story names.
- **Naming.** Lowercase schema, table and column names for S3 Tables, Glue and Lake Formation resources.
- **Reliability.** Loads and jobs are idempotent (replace, not append). Failure alarms exist for any pipeline stage the story adds.
- **No console changes.** Everything must deploy from an empty account through the pipeline. If a step needs a person in a console, an admin portal, or an approval, do not plan it as CDK. List it under `## Human Steps` as a handoff and plan only the part CDK can do.
- **Promotion.** Moving between environments is a config-only change, and a second `cdk diff` after deploy shows no changes. Plan for that where the story mentions promotion or environments.

### cdk-nag handling

- Plan to run `AwsSolutionsChecks` (from `cdk-nag`) on the app or on the stacks the story adds.
- For each finding you expect, choose between fixing the resource and suppressing the rule. Prefer the fix.
- A suppression must be scoped to the specific resource path (`NagSuppressions.addResourceSuppressionsByPath` or on the construct), must name the rule id, and must carry a one-sentence reason tied to the story. Blanket stack-level or `appliesTo`-less wildcard suppressions are not allowed.
- Add a test that fails if any unsuppressed cdk-nag error annotation exists on the stack.

### Tests the plan must specify (the `write_tests` step writes them before any CDK code)

- Synth assertion tests with `Template.fromStack` and Jest (`ts-jest`) under `test/`. Cover, per resource the story names: existence and count (`resourceCountIs`), key properties (`hasResourceProperties`), encryption and public-access settings, IAM statements (exact actions and resources, plus a negative assertion that no `*` action or resource appears), and alarms or log retention where required.
- Each test must fail before implementation, because the resource is not yet defined. State which tests those are, since the `red` step requires the new tests to fail.
- A cdk-nag test as described above.
- Negative cases where the story has a refusal or isolation requirement, such as no write permission, no public ingress, no egress outside the allowed CIDRs.
- Tests live alongside existing `test/` conventions. The global 80% coverage threshold (lines, branches, functions, statements) must still hold, so list any new code paths that need their own tests.

### Verification beyond synth

Synth tests cannot prove deployed behavior. If the story requires evidence from a live account (tunnel status, reachability, row counts), do not put that in this plan's CDK scope. Name it as a follow-up of type `deployed-state-verification` in `## Notes`.

## Plan Format

```md
# CDK Infrastructure: <story id> <short title>

Story: <story id from the issue>
Classification: <$2>

## Description
<what the stack/constructs add or change and why, in terms of the story>

## User Story
As a <role from the story>
I want <goal>
So that <benefit>

## Relevant Files
<existing files to read or modify, each with a one-line reason>

### New Files
<files to create under lib/, bin/ and test/, each with a one-line reason>

## Resources
<table: logical resource | construct/L2 or L1 | key properties | Region | story sentence it traces to>

## IAM Scope
<table: role | principal | actions | resource ARNs | reason. State "no wildcards" or list each wildcard with its reason>

## cdk-nag
<expected findings, and for each: fix or suppression, resource path, rule id, reason>

## Human Steps
<steps a person must do outside CDK, or "None">

## Open Questions
<undecided values or choices that block implementation, or "None">

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<h3 headers with bullets. Order: typed config/props, tests (listed first and failing), constructs, stack wiring in bin/app.ts, cdk-nag handling, make target if the story requires one. The last step runs the Validation Commands.>

## Testing Strategy
### Synth Assertion Tests
<test cases by name, the resource or statement each asserts, and which must fail before implementation>

### cdk-nag Test
<what is asserted>

### Negative Cases
<refusal, isolation and no-wildcard assertions>

### Edge Cases
<empty config, missing optional props, environment differences>

## Acceptance Criteria
Number each criterion. Use EARS, keep each singular and testable, and use "shall" in every one:
1. Ubiquitous: The <system> shall <response>.
2. Event-driven: When <trigger>, the <system> shall <response>.
3. State-driven: While <state>, the <system> shall <response>.
4. Unwanted behavior: If <condition>, then the <system> shall <response>.
5. Optional feature: Where <feature>, the <system> shall <response>.

<the real criteria go here, replacing the five templates above. Include the story's own criteria, plus criteria for encryption, IAM scope, cdk-nag and idempotent `cdk diff` where they apply. Each maps to at least one test or validation command.>

## Validation Commands
Execute every command. Each must exit zero.

- `npm run format:check`
- `npm run lint`
- `npm run build`
- `npm test`
- `npm run synth`

<add story-specific commands only if they exist in package.json or the Makefile>

## Notes
<new dependencies (with reason), follow-up stories, deployed-state checks to schedule, anything out of scope>
```

## Report

After writing the plan file, confirm to yourself that: it cites the story id, the acceptance criteria are numbered and each contains "shall", no template slot text remains, and the Validation Commands match `package.json`.

## Output contract (STRICT)

Your entire reply MUST be one block and nothing else: no preamble, no narration, no closing remarks, no code fences. The block contains only the repo-relative path of the plan file you wrote.

```
<<<SPEC>>>
<repo-relative path to the plan file>
<<<END SPEC>>>
```

The `<<<SPEC>>>` line MUST be the first line of your reply and `<<<END SPEC>>>` MUST be the last. Write nothing before or after them.
