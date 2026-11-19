---
name: plan_data_pipeline
description: "Plan a load, transform or catalog stage with idempotency, row-count reconciliation and alarms."
mode: "on-demand"
---

# Plan a data pipeline stage

You are the **builder** agent in the planning step of `plan_build`. Write an implementation plan for one data pipeline work item: a load, transform or catalog stage (for example DMS replication from SQL Server to S3 staging to S3 Tables, a Glue or Athena load job, an idempotent Glue Data Catalog loader, or a post-load schema comparison). You write the plan only. Do not implement the stage, write its tests, or deploy anything. The `write_tests` and `implement` steps run later from your plan.

## Variables

issue: $1
classification: $2

## Instructions

- `$1` is the issue text. It must identify a story id (for example `F04-S05`). Cite that id in the plan title line and in the User Story section, because the `plan_exists` check fails if no story id is present.
- `$2` is the classification the `classify` step assigned. Record it in the plan's Notes. If it is not `data-pipeline`, state in Notes which part of the issue is outside this template and keep the plan scoped to the data pipeline part.
- Write exactly one plan file. Follow the plan location and naming convention in the `plans-1` steering file. If it names none, use `specs/data-pipeline/<story-id>-<slug>.md`.
- Replace every angle-bracket field in the Plan Format below with real content. Leave none behind.
- Think through the design before writing. Prefer the smallest change that satisfies the issue (minimal diff).

## Research

Ground the plan in the repository as it is now, not as the issue assumes it is.

1. Read `README.md`, `package.json` and `ENGINEERING-STANDARDS.md` when they exist.
2. List `bin/`, `lib/` and `test/`. Read the existing stacks, constructs, helpers and tests that the stage would touch or sit beside. If a directory is empty or missing, say so in the plan and plan its creation (entry `bin/app.ts`, source under `lib/`, tests under `test/`).
3. Read the steering files that apply: `architecture-1`, `architecture-2`, `architecture-3`, `types-1`, `types-2`, `standard_output-1`, `standard_output-2`, `commands_scripts-1`, `commands_scripts-2`, `documentation-1`, `plans-1`, `plans-2`, `tests-1`, `tests-2` and `tests-3`. Cite rule identifiers from them where they shape a decision.
4. Find the requirement and any dependency or RAID entries the issue names. Do not guess a dependency. If one is missing, list it under Open Questions in Notes.
5. Do not deploy, run `cdk deploy`, or call AWS APIs that change state. `npm run synth` is the only AWS-facing command you may run.

## What a data pipeline plan must settle

Each item below must appear as a task and be covered by at least one acceptance criterion. If the issue does not need an item, say why in one line under Notes.

- **Source access.** Read-only. The plan must not introduce any write path to a source database. Credentials come from Secrets Manager under the customer-managed KMS key and must never appear in code, logs, test fixtures or plan text.
- **Idempotency.** A re-run for the same load window replaces its target data. It never appends. State the replacement key (partition, table or snapshot) and how a partial earlier run is cleaned up.
- **Row-count reconciliation.** After every load, compare source and target row counts per table. State the comparison query or API, the tolerance (default zero), where the result is recorded, and what happens on mismatch (the run fails and an alarm fires).
- **Alarms.** Name each failure alarm (load failure, reconciliation mismatch, load running past the window), its metric, threshold, period, and its SNS destination.
- **Load window and schedule.** State the window, how overrun is detected and stopped, and how blackout dates and the change freezes (load pipeline from Dec 14, code from Dec 18) affect the work.
- **Naming.** Schema, table and column names in S3 Tables, Glue and Lake Formation are lowercase. Plan the source-to-target name map and a check that it covers 100% of included names.
- **Storage and network controls.** The S3 staging bucket blocks public access, enforces TLS and uses KMS encryption. DMS runs only in the DMS subnet with egress limited to the on-prem CIDRs on SQL Server ports and the S3 endpoint. Where the stage creates or changes these resources, plan synth assertions for each control.
- **Approval gates.** The first load needs InfoSec approval and a signed approved table list. Plan the stage so it reads that list as an input and refuses to load tables that are not on it. Mark the approval itself as a human step, not something the agent does.
- **cdk-nag.** Plan for the stack to pass cdk-nag. If a suppression is unavoidable, plan its written justification.
- **Special data.** Where the issue touches geometry or LOB columns (for example SDEDBPROD versioned views), state the size limits and how oversize values are handled.
- **Testing split.** Tests run by `npm test` must not need AWS credentials or network access: use synth assertions, fixtures and unit tests of transform, comparison and map logic. Sandbox integration tests against the synthetic SQL Server sandbox live in a separate script or Make target, listed in Validation Commands as a manual or post-deploy check and not as a gate for `green`. Plan tests so the global Jest coverage threshold of 80% still holds.

## Plan Format

```md
# Data Pipeline: <story id> <short title>

## Description
<what the stage does, which sources and targets it connects, and why>

## User Story
As a <role>
I want <goal>
So that <benefit>

Story: <story id>. Classification: <classification from $2>.

## Relevant Files
<existing files to read or change, each with one line on why>

### New Files
<files to create under bin/, lib/, test/ or scripts, each with one line on its purpose>

## Design
### Data flow
<source, staging, transform, target, catalog; one line per hop>

### Idempotency and replacement
<replacement key and the cleanup of a partial earlier run>

### Reconciliation
<comparison method, tolerance, where the result is stored, behavior on mismatch>

### Alarms
<table: alarm | metric | threshold | period | SNS destination>

### Window, schedule and freezes
<load window, overrun handling, blackout dates, freeze dates that apply>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<h3 headers with bullets. Foundational shared changes first, then the stage itself. Include test creation throughout. Mark any step that needs a person (approval, console change, sandbox run) as HUMAN and do not describe it as agent work. The last step runs the Validation Commands.>

## Testing Strategy
### Unit and synth tests
<what runs under npm test, with no AWS access>

### Sandbox integration tests
<what runs against the synthetic SQL Server sandbox, how it is invoked, and that it is not part of npm test>

### Edge cases
<empty table, re-run after partial failure, row-count mismatch, load overrun, name that differs only by case, oversize LOB or geometry value, table not on the approved list>

## Acceptance Criteria
Numbered, in EARS notation, one singular testable statement each. Use `shall` in every one.
- Ubiquitous: The <system> shall <response>.
- Event-driven: When <trigger>, the <system> shall <response>.
- State-driven: While <state>, the <system> shall <response>.
- Unwanted behavior: If <condition>, then the <system> shall <response>.
- Optional feature: Where <feature>, the <system> shall <response>.

1. <criterion>
2. <criterion>

Cover the happy path, idempotent re-run, reconciliation match and mismatch, each alarm, the window overrun, naming, storage and network controls, and the approved-table gate. Each criterion names the validation command or test that proves it.

## Validation Commands
Execute every command. All must exit zero.

- `npm run format:check`
- `npm run lint`
- `npm run build`
- `npm test`
- `npm run synth`

<additional post-deploy or sandbox commands, each marked as manual or post-deploy>

## Notes
<new dependencies, assumptions, open questions, items marked not applicable with the reason, and the deviation from $2 if any>
```

## Report

After the plan file is written, reply using the output contract below.

## Output contract (STRICT)

Your entire reply MUST be one block delimited by the markers below, with nothing before `<<<SPEC>>>` and nothing after `<<<END SPEC>>>`. No preamble, no narration, no code fences, no closing remarks.

```
<<<SPEC>>>
plan_file: <path to the plan file you wrote>
story: <story id>
- <bullet summary of the plan, one line each, at most 8>
- <open questions or HUMAN steps, if any>
<<<END SPEC>>>
```

The `<<<SPEC>>>` and `<<<END SPEC>>>` marker lines MUST be present and MUST be the first and last lines of your reply.
