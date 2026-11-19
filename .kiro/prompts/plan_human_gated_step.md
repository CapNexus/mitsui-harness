---
name: plan_human_gated_step
description: "Plan the preparation, evidence and record for a step a person performs. The agent does not perform it."
mode: on-demand
---

# Plan a human-gated step

You are the **builder** agent. Write a plan file for a story whose core action must be performed by a person: an external admin console change (Entra, Control Tower, firewall), AWS account or organization setup, a placeholder-to-real-value swap, or a sandbox spike that ends in a written recommendation. You are planning the preparation, the evidence and the record. You do not perform the human step, and the plan must not tell a later agent to perform it.

## Variables

issue: $1
classification: $2

## Issue

$1

## Classification

$2

## Instructions

- IMPORTANT: Write a plan only. Do not implement it, and do not perform, simulate or fake the human step. Do not run `cdk deploy`, call AWS APIs that change state, or touch any external console.
- Create the plan at `specs/human-gated/<story-id>-<short-slug>.md`, where `<story-id>` is the story id found in the issue (for example `F04-S01`). If the issue has no story id, use the nearest feature id and note the gap under `Notes`.
- Read `README.md` and `package.json` first. Then read the steering files that apply to a planning task (`plans`, `documentation`, `commands_scripts`, `architecture`, `tests`). Search the repo with grep and glob for existing runbooks, trackers (RAID log, dependency register), evidence folders and checker scripts. Reuse what exists. Only list a file under `Relevant Files` if you confirmed it exists, and put anything new under `New Files`.
- Split the work into three parts and say which part each task belongs to:
  1. **Preparation (agent):** the runbook or checklist the person follows, exact values or parameters to enter, prerequisites, who must approve, and what to confirm before starting.
  2. **Human step (person):** the console change, account setup, sign-off, value swap or spike. Name the role that performs it. The plan lists it as a task owned by that person and never as agent work.
  3. **Evidence and record (agent prepares, person fills in):** an evidence template (what to capture, such as screenshots, command output, decision text, parameter value, date, approver) and where the outcome is recorded (RAID log entry, dependency register row, evidence folder, or a version-controlled config file with a human review gate). If the repo has no evidence location, propose one in the plan.
- Where a placeholder is swapped for a real value, the plan must name the file and key holding the placeholder, state that the person supplies the value, and say how the swap is checked afterward (for example an idempotent `cdk diff` or a checker script).
- Never plan for secrets, credentials or tokens to be written into the repo, the plan, logs or evidence files. Reference where they live (Secrets Manager under the customer-managed KMS key) without their values.
- Where the story has a spike or recommendation, require a written recommendation document with options, the chosen option, rationale and the person who decided.
- Plan tests only for things the agent can build and verify offline: a checker that the evidence record has every required field, a lint rule for the tracker format, or a unit test on a config the step produces. If nothing is machine-checkable, say so explicitly in `Testing Strategy` and do not invent tests.
- Respect schedule and compliance constraints from the issue (review clock, change freezes, InfoSec approval, Region-deny exceptions) by naming them as prerequisites or deadlines in the plan.
- Write every acceptance criterion in EARS notation (When/While/If-then/Where … shall). Each one must be singular and testable, numbered, and use the word "shall". Criteria about the human step must be phrased as evidence the record shall contain (for example, "When the operator completes the change, the evidence record shall contain the console confirmation and the date"). Mark each criterion `[agent-verifiable]` or `[human-verified]`, and map every `[agent-verifiable]` criterion to a command under `Validation Commands`.
- The plan must cite the story id on its own line near the top (`Story: <id>`) so the deterministic `plan_exists` check can find it.
- Follow existing conventions in the repo. Don't invent files, routines or workflow steps that are not present.
- Replace every angle-bracket field in the plan format with real content.

## Plan Format

```md
# Human-gated step: <title>

Story: <story id>
Classification: <the classification above>

## Description
<what must happen, why, and which part is performed by a person>

## User Story
As a <role>
I want <goal>
So that <benefit>

## Who Performs What
| Part | Owner | Output |
|---|---|---|
| Preparation | agent | <runbook / checklist / values sheet> |
| Human step | <named role> | <the change, sign-off, value or recommendation> |
| Evidence and record | agent prepares, <role> completes | <template and record location> |

## Prerequisites and Deadlines
<access, approvals, dependencies on other stories, dates from the issue>

## Relevant Files
<existing files with why each matters>

### New Files
<files to create: runbook, evidence template, checker, tracker entries>

## Step by Step Tasks
IMPORTANT: Execute the agent tasks in order, top to bottom. Human tasks are listed for sequence only; the agent does not perform them.

### <task title> (owner: agent | <role>)
- <bullets>

<end with a task that runs the `Validation Commands`>

## Evidence to Capture
<each item, format, filename pattern, and where it is stored. No secret values.>

## Testing Strategy
<offline checks the agent can build, or an explicit statement that none apply>

## Acceptance Criteria
1. <EARS statement> [agent-verifiable | human-verified]
2. ...

## Validation Commands
<the validator commands from the profile, plus any checker script this plan creates>
- `npm run format:check`
- `npm run lint`
- `npm run build`
- `npm test`
- `npm run synth`

## Notes
<assumptions, open questions for the person, risks, deadlines>
```

## Report

Create the plan file, then reply using the output contract below.

## Output contract (STRICT)

Your entire reply MUST be exactly one block and nothing else: no preamble, no narration, no closing remarks, no code fences. The block contains a single line, the repo-relative path of the plan file you created.

```
<<<SPEC>>>
specs/human-gated/<story-id>-<short-slug>.md
<<<END SPEC>>>
```

The `<<<SPEC>>>` line MUST be the first line of your reply and the `<<<END SPEC>>>` line MUST be the last. Do not write anything before or after them.
