---
name: plan_customer_approval
description: "Plan the sign-off request, the decision recorded and where it is logged."
mode: "on-demand"
---

# Plan a customer-approval item

Write an implementation plan for one issue classified as `customer-approval`: obtaining written confirmation or sign-off from the customer, preparing a document or config for sign-off, or collecting SME input into version-controlled config behind a human review gate. You write the plan only. Do not implement it, send anything to the customer, or record a decision.

## Variables

issue: $1
classification: $2

## Instructions

- The issue is `$1`. The classification chosen for it is `$2`. If `$2` is not `customer-approval`, still plan the issue, and state the mismatch under `Notes`.
- The agent never obtains or grants approval. Every step that needs the customer, InfoSec, an SME or any other person is marked `[HUMAN]` in the plan. The agent's own steps are limited to preparing the request, the evidence template and the log entry, and checking that a recorded outcome is well-formed.
- Plan three things explicitly, each as its own section:
  1. The sign-off request: what is being approved, who approves, what they receive, the response deadline and what happens if there is no response. Apply the 8-business-day deliverable review clock when the item is a deliverable. Name any gate that depends on the approval (for example InfoSec approval and a signed approved table list before the first load) and any change freeze it must land before (load pipeline from Dec 14, code from Dec 18).
  2. The decision to record: the allowed outcomes (approved, approved with changes, rejected, no response), the approver name and role, the date, the version or hash of what was approved, and a reference to the written confirmation.
  3. Where it is logged: the RAID log entry or evidence folder path, and any version-controlled config that changes as a result. Evidence files are dated and live in the repo. Reference the approval artifact. Never copy secrets, credentials, personal data or raw customer data into the plan or the evidence.
- Whenever the outcome should be machine-checkable, plan a checker (a script or Make target that exits non-zero when a required approval record is missing or malformed) with valid and invalid fixture cases, so the plan has a real `npm test` path. When nothing can be checked mechanically, say so and make the review gate explicit.
- If the approval changes config, plan the change as a version-controlled file edit with a human review gate. If it unlocks CDK changes, point to the `cdk-infrastructure` or `human-gated-step` item that follows and do not plan that work here.
- Research before planning:
  1. Read the issue and find its story id (for example `F02-S08`). The plan must cite it.
  2. Read `README.md` and `ENGINEERING-STANDARDS.md` if they exist, and look for the existing RAID log, evidence folder, dependency register and similar Markdown trackers. Use their formats and paths. Do not invent new locations when one exists.
  3. Read the steering files `plans-1`, `plans-2`, `documentation-1`, `commands_scripts-1`, `commands_scripts-2`, `architecture-1` and `types-1`. Apply what they say about plan location, naming, scripts and typed data.
  4. Look under `lib/`, `bin/`, `test/` and any scripts directory for existing patterns. The code base may be nearly empty, so state what you found and what is missing.
- Write the plan file where the `plans` steering files say plans belong, with a name derived from the story id and a short slug. Replace every angle-bracket slot in the Plan Format with real content.
- Write each acceptance criterion in EARS notation (When/While/If-then/Where ... shall). Number the criteria, keep each singular and testable, and map each to a validation command. Include the unwanted-behavior cases: no response before the deadline, rejection, approval of the wrong version, and a missing or malformed record.
- Use only these validation commands, taken from the profile, and add item-specific checker commands only if the plan creates them:
  - `npm run format:check`
  - `npm run lint`
  - `npm run build`
  - `npm test`
  - `npm run synth`
- Follow the repo's conventions: TypeScript with typed data (no bare `any`), Node 20 or later, lint with zero warnings, 80% coverage threshold. Do not plan deploys.
- Keep the diff minimal. Do not plan unrelated refactors.

## Plan Format

```md
# Customer Approval: <short title> (<story id>)

## Description
<what is being approved or signed off, by whom, and why it matters to the engagement>

## User Story
As a <role>
I want <goal>
So that <benefit>

## Sign-off Request
- Approver: <name or role>
- Subject and version: <document, config or table list, with version or hash>
- Package sent: <what the approver receives>
- Response deadline: <date or review-clock rule>
- No-response handling: <escalation or assumption, stated as a decision for a person>
- Blocks: <downstream gate or freeze date that depends on this>

## Decision Record
- Allowed outcomes: <approved | approved with changes | rejected | no response>
- Fields recorded: <approver, role, date, version approved, reference to written confirmation>
- Confirmation reference: <where the written confirmation is stored, without copying sensitive content>

## Log Location
- Log: <RAID log entry or evidence folder path>
- Config changed by the outcome: <version-controlled file, or none>

## Relevant Files
<existing files to read or edit, with a reason for each>

### New Files
<files to create, such as the request document, evidence template or checker with its fixtures>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom. Mark person-owned steps `[HUMAN]`.

<h3 headers with bullets. Start with the tests or fixtures for any checker. Then the request document, the decision record template and the log entry. Put each `[HUMAN]` step in sequence: send request, obtain decision, record outcome. The last step runs the Validation Commands.>

## Acceptance Criteria
1. <EARS statement>
2. <EARS statement>
<numbered, each singular and testable, each mapped to a validation command>

## Validation Commands
<npm run format:check, npm run lint, npm run build, npm test, npm run synth, plus any checker command this plan creates>

## Notes
<mismatched classification if any, assumptions, open questions for a person, follow-up items>
```

## Output contract (STRICT)

Write the plan to its file first. Your entire reply must then be one block delimited by the markers below and nothing else: no preamble, no narration, no closing remarks, no code fences. The block contains only the repo-relative path of the plan file you wrote, on one line.

```
<<<SPEC>>>
<repo-relative path to the plan file>
<<<END SPEC>>>
```

The `<<<SPEC>>>` line must be the first line of your reply and the `<<<END SPEC>>>` line must be the last. Write nothing before or after them.
