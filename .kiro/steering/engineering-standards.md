---
name: engineering-standards
description: "Stack, AWS Well-Architected, SOLID and test-coverage standards for every code change. Loaded every turn."
inclusion: always
---

# Engineering standards — Well Data Assistant POC

Decided by the solution architect (Soma), Nov 19, 2026. These apply to every change the
harness makes in `project-mep-AWS-Infrastructure` and `project-mep-AWS-Code`. Paths below
(lib/, bin/, test/, package.json) are relative to the submodule the story names. Both
repositories start empty; the harness writes the starter code (F02-S02 is the first code
story) and must set up the toolchain below exactly, because `scripts/validate.sh` runs these
commands as its stages.

## Repositories

| Repo (`repo:` in a story) | Content | Stack |
|---|---|---|
| `project-mep-AWS-Infrastructure` | Landing zone baseline, VPC, VPN, PrivateLink, DMS, S3, KMS, pipeline, monitoring, teardown | AWS CDK v2, TypeScript, Node.js 20 LTS |
| `project-mep-AWS-Code` | Glue/Athena load jobs, catalog, Lake Formation, MCP tools, AgentCore Gateway/Policy, assistant, Teams bot, eval harness | AWS CDK v2 TypeScript for all infrastructure; runtime language per component is decided in the story that creates it |
| parent (`planning`) | Stories, evidence, tracking — never code | — |

A story changes exactly one repository. Planning files never go into a submodule.

## Toolchain and commands (TypeScript CDK repositories)

`package.json` scripts every TypeScript repository must define, and the validator runs, in order:

| Purpose | Command |
|---|---|
| install | `npm ci` (npm only; `package-lock.json` is committed) |
| format check | `npm run format:check` (Prettier) |
| lint | `npm run lint` (ESLint with `@typescript-eslint`, strict type-checked config) |
| type check / build | `npm run build` (`tsc --noEmit` with `"strict": true`) |
| unit tests + coverage | `npm test` (Jest + ts-jest, `--coverage`, `coverageThreshold.global` 80 for lines, branches, functions, statements) |
| synth + compliance | `npm run synth` = `cdk synth --quiet` (cdk-nag `AwsSolutionsChecks` applied to the app; any unsuppressed error fails synth) |

**Synth is local, for unit tests only.** The validator runs synth with every AWS credential
removed, so the app MUST synthesize offline: account and Region come from the typed config
(placeholders allowed), no `fromLookup`/context lookups, no SDK calls at synth time. Agents
never run `cdk deploy`, `cdk diff`, `cdk bootstrap` or any mutating AWS CLI call; deploying
is a human step (Venkat) through the pipeline. cdk-nag rule pack: AwsSolutions only.

## AWS Well-Architected Framework

Every stack and construct is reviewed against the six pillars. Mechanical checks:

- **Security** — cdk-nag `AwsSolutionsChecks` on the whole app; suppressions only with a written
  reason in code (`NagSuppressions.addResourceSuppressions(..., [{ id, reason }])`). Customer-managed
  KMS keys for data at rest and logs; TLS enforced on buckets; least-privilege IAM (no `*` actions
  or resources without a nag suppression reason); no secrets in code or config — only Secrets
  Manager secret names (see `config/parameters.md`, type B).
- **Reliability** — infrastructure only through the pipeline; no console changes; stacks are
  idempotent and deploy from an empty account.
- **Operational excellence** — every stack tagged (`project`, `owner`, `environment`,
  `cost-center`); logging and alarms defined in code; teardown script kept working.
- **Performance efficiency** — managed/serverless services preferred; sizes come from config.
- **Cost optimization** — budget alert in code; log retention set explicitly; no idle resources
  outside the load window.
- **Sustainability** — right-size from config; lifecycle rules on S3 buckets.

## Design: SOLID for CDK and application code

- **Single responsibility** — one construct per concern (e.g. `KmsBaseline`, `BudgetAlert`); a
  stack composes constructs and holds no resource logic of its own.
- **Open/closed** — extend by adding a construct or stack, not by editing unrelated ones.
- **Liskov** — construct props interfaces are honoured by every implementation; no runtime
  type checks on props.
- **Interface segregation** — small, typed props interfaces per construct; no catch-all props bag.
- **Dependency inversion** — constructs receive collaborators (keys, buckets, VPC) through props;
  every Mitsui value comes from the typed config module by its `config/parameters.md` name,
  and a missing value fails synth naming the parameter.

## Code quality and tests

- Tests are written before the implementation (red, then green).
- Every construct has CDK assertion tests (`Template.fromStack`, `hasResourceProperties`,
  `resourceCountIs`); every non-trivial function has unit tests, including failure cases.
- Coverage of at least 80% (lines, branches, functions, statements) is enforced by Jest;
  lowering the threshold is a harness-change, not a story change.
- No `any`, no non-null assertions without a comment, no disabled lint rules without a reason.
- Each story's `verify:` lines are run as written; a story is done only when all pass.
