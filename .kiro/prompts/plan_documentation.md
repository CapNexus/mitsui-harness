---
name: plan_documentation
description: "Plan a runbook, record or document, with a consistency check where one exists."
mode: "on-demand"
---

# Plan a documentation item

You are the **builder** agent. Write a plan file for one documentation issue. Do not write the document itself and do not change any other file. A later step turns the plan into tests and then into the document.

Typical items: a runbook, a governance record (RAID log, dependency register, deliverable acceptance record), a status report, a handover or readout, or a contract or decision document. The document is Markdown under version control. Where a checkable rule exists for it (required sections, register columns, story-id coverage, crosswalk completeness), the plan includes a consistency check.

## Variables

issue: $1
classification: $2

## Instructions

- The issue is `$1`. The classification is `$2` (`documentation` or `docs`). Read both fully before planning.
- Find the story id in the issue (for example `F01-S04`). Cite it in the plan's title area and in the User Story section. If the issue has no story id, state that in `Notes` and cite the nearest feature id instead.
- Research before planning:
  1. Read `README.md` and any `ENGINEERING-STANDARDS.md` if they exist.
  2. Read the steering files `documentation-1`, `plans-1`, `standard_output-1` and `commands_scripts-1`. They define document conventions, plan layout, output style and script and Make target conventions. Where they disagree with this template, they win.
  3. Search with grep and glob for existing documents of the same kind (registers, runbooks, evidence folders) and match their headings, tables and file naming.
  4. Search for an existing checker script or Make target that already validates this kind of document. If one exists, plan to extend or call it and do not plan a duplicate. If none exists and the document has structure that can be checked, plan a small checker.
- Save the plan at the path that `plans-1` prescribes. If it prescribes none, use `specs/documentation/<story-id>-<slug>.md`. Create the file with the write tool.
- Replace every angle-bracket field in the Plan Format with real content. Leave none behind.
- Facts in the planned document must come from the issue, the requirement files or the repository. Do not invent figures, dates, names or approvals. When a fact is not available, plan a clearly marked placeholder and record the gap under `Notes` as an open question for a person.
- Planned documents must never contain secrets, credentials, connection strings or key material. Refer to the Secrets Manager entry name only.
- If the document records a human or customer decision (sign-off, approval, InfoSec confirmation), plan the record so it holds the decision, who made it, the date and the evidence link. Do not plan any step where the agent states that a decision was made when the issue gives no evidence of it.
- Write every acceptance criterion in EARS notation. Use `shall`. Each criterion must be singular, testable and traceable to a command in `Validation Commands`.
- Respect the project's mechanics: Node 20 or later, Jest 29 with ts-jest (80% global coverage threshold, tests under `test/`), ESLint with zero warnings, Prettier. Any planned checker script is TypeScript under the layout the architecture steering files describe, exits non-zero on failure, and has at least one valid and one invalid fixture test. Do not plan a deploy. `npm run synth` is the only AWS-facing command.
- Keep the plan small. Plan only what the issue asks for.

## Plan Format

```md
# Documentation: <title> (<story id>)

## Description
<what the document is, who reads it, and what decision or action it supports>

## User Story
As a <role named in the issue>
I want <the document or record>
So that <benefit stated in or implied by the issue>

Story: <story id>

## Relevant Files
<existing files to read or update, each with one line on why>

### New Files
<files to create: the document, any checker script, any fixtures and tests>

## Document Outline
<ordered headings, tables and required fields of the document, with the source of each fact (issue, requirement file, repository path, or "open question")>

## Consistency Check
<the rule the document must satisfy and the command that checks it. If an existing checker covers it, name it. If a new one is needed, describe its inputs, what it fails on, and its valid and invalid fixture cases. If no mechanical check applies, write "None applicable" and give the reason.>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<h3 headers with bullets. Put the checker tests first, then the checker, then the document. End with running the Validation Commands.>

## Acceptance Criteria
<numbered EARS statements, each using "shall":
1. Ubiquitous: The <system> shall <response>.
2. Event-driven: When <trigger>, the <system> shall <response>.
3. State-driven: While <state>, the <system> shall <response>.
4. Unwanted behavior: If <condition>, then the <system> shall <response>.
5. Optional feature: Where <feature>, the <system> shall <response>.
Cover the required content of the document, the consistency check passing on the document, the check failing on an invalid fixture, and the absence of secrets.>

## Validation Commands
Execute every command. Each must exit zero.

- `npm run format:check`
- `npm run lint`
- `npm run build`
- `npm test`
- `npm run synth`
<add the checker or Make target command for this document if one is planned>

## Notes
<assumptions, open questions for a person, facts that could not be sourced, and anything a reviewer should look at first>
```

## Your reply

The plan file is written to disk by you. The reply carries only its path.

## Output contract (STRICT)

Your entire reply MUST be one block and nothing else. No preamble, no narration, no closing remarks, no code fences. The first line is `<<<SPEC>>>` and the last line is `<<<END SPEC>>>`. Between them, put the single line with the repository-relative path of the plan file you wrote.

<<<SPEC>>>
<repository-relative path of the plan file>
<<<END SPEC>>>
