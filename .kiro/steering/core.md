---
name: core
description: "Core code-level engineering rules for the AWS CDK (TypeScript) infrastructure harness. Loaded every turn."
inclusion: always
---

# Core Engineering Rules

These rules apply to every agent turn in this repository (AWS CDK in TypeScript, Jest, ESLint, Prettier). Each rule states what an agent MUST do, why, and how it is checked. Checks run independently of the agent's own report.

## standard_output-1

**Rule.** Lambdas, scripts and CDK code under `lib/`, `bin/` and `scripts/` MUST log through one structured JSON logger (one JSON object per line with `level`, `event` and context fields). Do not call `console.log` with free text.

**Why.** Structured output lets an agent read a failure from a log line instead of guessing.

**Check (grep).** `console\.log\(` in `lib/ bin/ scripts/` must return no matches.

## standard_output-2

**Rule.** Every verification or acceptance script MUST set a non-zero exit code on failure and write a dated JSON evidence file under `evidence/`.

**Why.** A script that cannot fail, or leaves no record, proves nothing about deployed state.

**Check (grep).** `process\.exitCode|process\.exit\(` in `scripts/` must match in every verification script.

## types-1

**Rule.** All TypeScript MUST pass the strict type check (`npm run build` is `tsc --noEmit`). Stack props, config and parameter shapes MUST be declared as interfaces or types, not inline objects.

**Why.** Typed props and config shapes are what an agent can trust across stack and script boundaries.

**Check (command).** `npm run build`

## types-2

**Rule.** Do not use `any` or `as any` in `lib/`, `bin/` or `scripts/`. Use `unknown` and narrow it at the boundary.

**Why.** Untyped values hide mistakes in IAM, parameter and API payloads until deploy time.

**Check (grep).** `:\s*any\b|as any` in `lib/ bin/ scripts/` must return no matches.

## architecture-1

**Rule.** Stacks MUST be instantiated in only two places: `bin/app.ts`, and the CDK Pipelines application Stage classes under `lib/pipeline/`. The Stage files are the only place besides `bin/app.ts` where `new <Name>Stack(` may appear, because the pipeline deploys the stacks through a Stage. Each construct or stack lives in its own file under `lib/`, and its test mirrors the path under `test/`.

**Why.** The infrastructure must deploy from an empty account through the pipeline, and a pipeline Stage has to instantiate the stacks it deploys. Limiting instantiation to these paths keeps one place to read the deployment composition, and keeps changes small and easy to locate.

**Check (grep).** `new \w+Stack\(` outside `bin/`, `lib/pipeline/` and `test/` must return no matches.

## architecture-2

**Rule.** Code under `lib/` MUST NOT import from `test/` or `scripts/`.

**Why.** Keeps deployable code independent of test and operator tooling.

**Check (grep).** `from '.*(test|scripts)/` in `lib/` must return no matches.

## documentation-1

**Rule.** Every new file in `lib/` and `scripts/` MUST start with a header comment naming its story id and a one-line purpose, for example `// Story: F04-S02 - PrivateLink endpoints`.

**Why.** The requirements are the only record of why the code exists, and there is no README or ADR yet.

**Check (grep).** `^// Story: F[0-9]{2}-S[0-9]{2}` must match on line 1 of every file in `lib/` and `scripts/`.

## commands_scripts-1

**Rule.** Agents MUST run only the npm scripts `format:check`, `lint`, `build`, `test` and `synth`. Any new repeatable action MUST be added as an npm script in `package.json` before it is used.

**Why.** One trigger per multi-step action keeps agent behavior predictable and auditable.

**Check (grep).** `"(format:check|lint|build|test|synth)"` must appear in the `scripts` block of `package.json`.

## plans-1

**Rule.** Every issue MUST have a plan file that cites its story id and lists numbered acceptance criteria written with "shall" before any test or code is written.

**Why.** The plan is what lets a later session build and check the work without the earlier conversation.

**Check (grep).** `\bshall\b` in each plan file under `plans/`.

## aews-1

**Rule.** Work MUST run through the `plan_build` workflow with a `commit_tests` step before `implement`, so the driver can diff implementation against the committed tests. The validator MUST be re-run by the driver, not trusted from the agent's report.

**Why.** Committed tests and a driver-owned validator are what stop an agent from editing tests to pass.

**Check (grep).** `commit_tests` in the `plan_build` workflow definition under `harness/workflows/`.
