---
name: testing
description: "Testing rules for the CDK TypeScript infrastructure: coverage gate, synth-time stack assertions, and cdk-nag. Detailed rules loaded on demand."
inclusion: on-demand
---

# Testing Rules

Tests are the only automated check on infrastructure before a person deploys it. Each rule below says what an agent MUST do, why, and how it is checked. Tests live under `test/`, source under `lib/` and `bin/`, and the test runner is Jest 29 with ts-jest.

Agents must not run `cdk deploy`. `npm run synth` is the only AWS-facing script, and the stack tests below run at synth time without touching an account.

## tests-1

**Rule.** Changes MUST keep global Jest coverage at or above 80% for lines, branches, functions and statements. Tests assert specific values (a property, a count, a returned string), not only that code ran. A correct but failing test is a specification: fix the code, never weaken or delete the test, unless the test is provably wrong and you say so explicitly.

**Why.** The coverage threshold is the configured quality gate, and value assertions catch wrong output.

**Check.** command: `npm test`

- Do not lower `coverageThreshold` in the Jest config to make a change pass.
- New behavior and bug fixes ship with a test in `test/` that mirrors the path of the file under `lib/`.
- Prefer `toEqual`, `toBe`, `toHaveLength` and `Match.objectLike` with concrete values over `toBeDefined` or `toBeTruthy`.

## tests-2

**Rule.** Every CDK stack test MUST use `Template.fromStack` and assert the specific resource properties the story requires (encryption, ports, CIDRs, IAM actions). Include a negative assertion where the story forbids something.

**Why.** Synth-time assertions are the only automated check on infrastructure before a person deploys it.

**Check.** grep: `Template\.fromStack must appear in every test under test/ that covers a stack`

- Use `template.hasResourceProperties(type, Match.objectLike({...}))` with the exact value the story states, for example `KmsMasterKeyId` on the S3 staging bucket, the SQL Server port and on-prem CIDR on the DMS security group, or the allowed actions in an IAM policy statement.
- Use `template.resourceCountIs` to pin how many resources of a type exist, and `Match.not` or `Match.absent` for forbidden things. Examples from this project's constraints:
  - no public access on the S3 staging bucket (all four `PublicAccessBlockConfiguration` flags true), and a bucket policy denying non-TLS requests;
  - no write actions (`Put*`, `Delete*`, `Update*`) in read-only tool Lambda roles or Lake Formation grants;
  - no egress from the DMS subnet security group except on-prem CIDRs on SQL Server ports and the S3 endpoint.
- Name each test after the story it covers (for example `F02-S02`) so the requirement can be traced.
- Promotion between environments is a config-only change, so assert that synthesizing with different config values changes only the intended properties.

## tests-3

**Rule.** The CDK app MUST run cdk-nag and the test suite MUST fail on unsuppressed findings. Every suppression MUST carry a written reason.

**Why.** cdk-nag is a declared dependency and the security constraints depend on it.

**Check.** grep: `AwsSolutionsChecks in bin/app.ts or test/; NagSuppressions entries must contain a non-empty reason`

- Apply `Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }))` in `bin/app.ts`, and apply the same aspect to each stack under test in `test/`.
- In tests, collect annotations with `Annotations.fromStack(stack)` and assert `findError('*', Match.stringLikeRegexp('AwsSolutions-.*'))` returns an empty array. Do the same for warnings if the project treats them as blocking.
- Add suppressions with `NagSuppressions.addResourceSuppressions` or `addStackSuppressions`. Each entry needs `id` and a non-empty `reason` that names the specific resource and why the finding is acceptable. Use `appliesTo` to scope wildcard IAM suppressions to the exact pattern, not the whole rule.
- Never suppress a finding to make a test pass without a reason a reviewer could challenge.
