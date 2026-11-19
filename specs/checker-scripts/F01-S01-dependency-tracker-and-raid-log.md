# Checker: Dependency register and RAID log checkers

## Description
Two deterministic Bash checkers for the planning repository, plus the RAID log they validate.
Story id: F01-S01 (Set up the dependency tracker and RAID log, SOW D1). Classification token: `checker-script`.

- `check-dependency-register.sh` validates `user-stories/dependencies/README.md`: all 29 DEP IDs exist once, each with a non-empty owner, needed-by, type and status, and every `slipped` row carries a slip date and a cause (SOW Assumption 8).
- `check-raid-log.sh` validates the new `user-stories/raid-log.md`: it has the four RAID sections and is seeded with Feature List Section 5 gaps 1 to 9 as issues and Section 7 questions 1 to 7 as open decisions, each with an owner and a date.

It matters because every later F01 story (S02 owners, S06 slips and overdue check) and the Deliverable 1 submission rely on one tracker that cannot silently lose an item.

The story changes the parent planning repository only (`repo: planning`). Per `project-context.md` context-5, the CDK/npm rules (TypeScript script, Jest, `npm run` targets, `lib/`, `bin/`, `test/`) do not apply. The checkers are Bash under `user-stories/scripts/`, their tests are Bash under `user-stories/scripts/tests/`, and `scripts/validate.sh` planning mode runs every `check-*.sh` and every `tests/*.sh`. No `package.json` or `Makefile` exists at the root, so no Make target or npm script is added.

## User Story
As Mike (CapNexus project manager)
I want one tracker holding every client dependency and every risk, assumption, issue and decision, with a script that fails when an item is missing or incomplete
So that nobody has to ask who owns an item or when it is due.

## Relevant Files
- `user-stories/features/F01-mobilization-governance/stories/F01-S01-dependency-tracker-and-raid-log.md`: the story and its three acceptance criteria.
- `user-stories/dependencies/README.md`: the register under test. Has 29 rows with columns `ID | Dependency | Owner (Mitsui) | Needed by | Type | Status | Used by features`. It has no notes column yet, so a `slipped` row has nowhere to hold a slip date and cause.
- `user-stories/WDA-POC-Feature-List.md`: Section 5 "Still open" items 1 to 9 (gaps) and Section 7 questions 1 to 7 are the RAID seed. Section 3 is the DEP source.
- `user-stories/features/F01-mobilization-governance/feature.md`: feature criterion 2 (RAID log and tracker hold every Dependencies-doc item with owner, due date and status) and the open points on DEP-04, DEP-26 and Section 5 gaps 5 and 6.
- `user-stories/features/F01-mobilization-governance/stories/F01-S06-slipped-dependency-handling.md`: later story that extends the slipped-row rule (days late) and adds `check-overdue.sh`. S01 must not preempt it.
- `user-stories/README.md`: layout already lists `raid-log.md` and `scripts/` as created by F01-S01.
- `scripts/validate.sh`: planning mode runs `user-stories/scripts/check-*.sh` and `user-stories/scripts/tests/*.sh` with no arguments, so both checkers must default to the real files. It is frozen and must not be edited.
- `.kiro/steering/project-context.md` (context-5, context-2, context-3), `core.md` (plans-1, documentation-1 intent), `testing.md` (tests-1 intent: assert specific values and reasons).

Not present: `specs/`, `user-stories/scripts/`, `user-stories/raid-log.md`, `package.json`, `Makefile`. This story creates the first three.

### New Files
- `user-stories/scripts/check-dependency-register.sh`: checker. Verdict logic lives in functions, with a guarded `main` so tests can source it without running it.
- `user-stories/scripts/check-raid-log.sh`: checker, same structure.
- `user-stories/raid-log.md`: the RAID log, seeded.
- `user-stories/scripts/tests/check-dependency-register.test.sh`: tests for the register checker.
- `user-stories/scripts/tests/check-raid-log.test.sh`: tests for the RAID checker.
- `user-stories/scripts/tests/fixtures/register-valid.md`: 29 rows, one valid `slipped` row.
- `user-stories/scripts/tests/fixtures/raid-valid.md`: minimal valid RAID log with the four sections and all 9 gaps and 7 questions.
- Invalid fixtures are derived by each test from the valid fixture with one documented `sed`/`grep -v` mutation into a `mktemp -d` directory. This keeps each invalid case to exactly one change and avoids ten near-copies of a 29-row table. The test names each mutation after the failure it expects.

Edited file:
- `user-stories/dependencies/README.md`: add a trailing `Notes` column to the register table (empty for all `open` rows), and one sentence in the prose defining the slipped-row note format: `slip-date: YYYY-MM-DD; cause: <text>`. No other row content changes.

## Checker Design
- Input: a Markdown file path as the first argument. Default is the repo file, resolved from the script's own location (not the working directory): `user-stories/dependencies/README.md` and `user-stories/raid-log.md`. Usage: `check-dependency-register.sh [FILE]`, `check-raid-log.sh [FILE]`. `-h` prints usage.
- Parsing: header-driven. The register table is the first table whose header row contains `ID` and `Status`. Columns are found by header name (`Owner`, `Needed by`, `Type`, `Status`, `Notes`), so column order may change. Cells are trimmed. Table rows start with `| DEP-`.
- Register checks, each reported as `FAIL <file>:<line>: <DEP-nn>: <message>` on stderr:
  1. Register table not found, or a required column is missing: `register table lacks column "<name>"`.
  2. Missing ID: `DEP-<nn> is missing` for each of DEP-01 to DEP-29 not present.
  3. Duplicate ID: `DEP-<nn> appears more than once (lines a, b)`.
  4. Unexpected ID outside DEP-01 to DEP-29: `unexpected ID <id>`.
  5. Empty required cell: `owner is empty`, `needed-by is empty`, `type is empty`, `status is empty`.
  6. Type does not match `^[A-E](\+[A-E])*$`: `type "<x>" is not A to E`.
  7. Status not one of `open`, `requested`, `in-progress`, `resolved`, `slipped`: `status "<x>" is not allowed`.
  8. Status `slipped` and Notes lack `slip-date: YYYY-MM-DD`: `slipped row has no slip date`.
  9. Status `slipped` and Notes lack a non-empty `cause: ...`: `slipped row has no cause`. A row missing both prints both lines.
- RAID checks:
  1. Missing section: `section "## Risks" is missing` (likewise Assumptions, Issues, Decisions). Sections are found by exact `## <Name>` heading.
  2. Each section holds a table with columns `ID | Item | Owner | Date | Status | Source`. Missing column: `section <Name> lacks column "<c>"`.
  3. Row ID prefix matches the section (`R-`, `A-`, `I-`, `D-`) and is unique: `<id> has wrong prefix for section <Name>` / `<id> is duplicated`.
  4. Every row has non-empty Owner and a Date matching `^[0-9]{4}-[0-9]{2}-[0-9]{2}$` (format only, no calendar or clock check): `<id>: owner is empty`, `<id>: date "<x>" is not YYYY-MM-DD`.
  5. Issues seed: for each n in 1 to 9 the Issues table has a row whose Source cell contains `Feature List s5 gap <n>`: `Issues lacks seed for Feature List s5 gap <n>`.
  6. Decisions seed: for each n in 1 to 7 the Decisions table has a row whose Source cell contains `Feature List s7 q<n>`, with Status `open`: `Decisions lacks seed for Feature List s7 q<n>` / `<id>: seeded question must have status open`.
  The Risks and Assumptions sections must exist and be well-formed but may hold no rows. An empty table (header only) is allowed there.
- Exit codes: `0` all checks pass (prints one line `PASS <file>: <summary>` on stdout). `1` one or more checks failed (all failures are listed, not just the first). `2` usage error, file not found or not readable.
- Determinism: no network, no AWS, no clock, no randomness. Uses `bash`, `grep`, `awk`, `sed` only, with `LC_ALL=C`. Works under Git Bash on Windows (CRLF in the input is stripped before parsing) and macOS `/bin/bash` 3.2 (no associative arrays, no `mapfile`).
- Guards: none, read-only check. Neither script writes any file.
- Logging: `standard_output-1` and `-2` apply to `lib/ bin/ scripts/` in CDK repositories. Here the output is plain one-line-per-finding text, which the stdout/stderr and exit-code contract above makes machine-checkable. No evidence JSON file is written, because the story's evidence is "the commit and the passing script output" (story Evidence section).

## Fixtures
- Valid:
  - `register-valid.md`: 29 well-formed rows DEP-01 to DEP-29, including one row with status `slipped` and Notes `slip-date: 2026-11-17; cause: Mitsui has not sent the account emails`. Passes with exit 0.
  - `raid-valid.md`: four sections; Issues rows I-01 to I-09 with Source `Feature List s5 gap 1..9`; Decisions rows D-01 to D-07 with Source `Feature List s7 q1..q7`, status `open`; each with owner and ISO date. Passes with exit 0.
- Invalid register (one mutation each):
  - `dep-missing`: delete the DEP-17 row. Fails: `DEP-17 is missing`.
  - `dep-duplicate`: repeat the DEP-05 row. Fails: `DEP-05 appears more than once`.
  - `dep-unexpected`: rename DEP-29 to DEP-30. Fails: `DEP-29 is missing` and `unexpected ID DEP-30` (this case asserts both, as one mutation).
  - `owner-empty`, `needed-by-empty`, `type-empty`, `status-empty`: blank that cell in DEP-03. Each fails with its own message.
  - `type-bad`: type `Z` in DEP-03. Fails: type not A to E.
  - `status-bad`: status `done` in DEP-03. Fails: status not allowed.
  - `slipped-no-date`: slipped row with Notes `cause: text` only. Fails: `slipped row has no slip date` and no cause message.
  - `slipped-no-cause`: slipped row with Notes `slip-date: 2026-11-17` only. Fails: `slipped row has no cause` and no date message.
  - `no-notes-column`: remove the Notes header cell. Fails: missing column "Notes".
  - `empty-file`: zero bytes. Fails: register table not found.
- Invalid RAID (one mutation each):
  - `section-missing`: delete the `## Assumptions` heading. Fails: section missing.
  - `issue-seed-missing`: delete the gap 5 row. Fails: `Issues lacks seed for Feature List s5 gap 5`.
  - `decision-seed-missing`: delete the q7 row. Fails: `Decisions lacks seed for Feature List s7 q7`.
  - `decision-not-open`: set D-03 status to `closed`. Fails: seeded question must have status open.
  - `owner-empty`, `date-bad` (`17/11/2026`), `id-prefix-wrong` (an `R-` row inside Issues), `id-duplicate`.
  - `column-missing`: drop `Owner` from the Issues header. Fails: lacks column "Owner".
- Missing file and usage cases are tested without fixtures: a path that does not exist gives exit 2, and `-h` gives exit 0.

No fixture holds a secret, a real account id or real customer data. Owners use the names already in the register (Noah Jackson, Mike) and generic text.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Register format and fixtures
- Edit `user-stories/dependencies/README.md`: add the `Notes` column (empty cells) and the slipped-note format sentence. Do not change any other cell.
- Create `user-stories/scripts/tests/fixtures/register-valid.md` from the edited register, with DEP-03 changed to `slipped` plus the valid note, so the valid fixture exercises the slipped branch.
- Create `user-stories/scripts/tests/fixtures/raid-valid.md`.

### 2. Register checker tests (written first, red)
- Create `user-stories/scripts/tests/check-dependency-register.test.sh` with a small inline helper (`expect_pass`, `expect_fail <message-fragment>`, exit code and stderr assertions) and a `mktemp -d` working directory removed by `trap`. The test file exits non-zero if any assertion fails and prints one line per assertion.
- One case per fixture listed above, asserting the exit code and that stderr contains the expected message and, for the slipped cases, does not contain the other message.
- Case: all findings are listed in one run (the DEP-17 delete plus a bad status gives two FAIL lines).
- Case: CRLF copy of the valid fixture passes.
- Case: the real `user-stories/dependencies/README.md` passes (this proves the actual register, not only fixtures).

### 3. Register checker
- Create `user-stories/scripts/check-dependency-register.sh` (`#!/usr/bin/env bash`, `set -uo pipefail`, header comment `# Story: F01-S01 - dependency register checker`). Pure functions parse the table into a temporary TSV in memory (variables, no temp files) and emit findings. A `main` runs only when the script is executed, not sourced. Make it executable (`git update-index --chmod=+x`).
- Make step 2 pass.

### 4. RAID log and its checker
- Create `user-stories/raid-log.md`: short intro, four `##` sections (Risks, Assumptions, Issues, Decisions) with the column set above.
  - Risks and Assumptions: header only, plus a one-line note that they are filled as they arise. Do not invent risks or assumptions beyond what the sources state.
  - Issues I-01 to I-09: one per Section 5 "Still open" item 1 to 9, Item text as a short paraphrase, Source `Feature List s5 gap <n>`, status `open`.
  - Decisions D-01 to D-07: one per Section 7 question 1 to 7, Source `Feature List s7 q<n>`, status `open`.
  - Owner for each row comes from the sources where they name one (for example D-01 Noah Jackson, DEP-11 and D-02 Noah Jackson and the DBAs, I-05 and D-07 Noah Jackson to name the sponsor, D-05 Noah Jackson and Matt Schiefelbein per DEP-16). Where a source names none, the owner is `Mike` (CapNexus PM) as the person raising it. No new Mitsui name is invented, and `to be named` stays as is (story Dependencies section).
  - Date is the due date stated in the source (D-01: 2026-11-23; the register's needed-by date where the item maps to a DEP), otherwise 2026-11-20 (D1 due date). Dates are ISO.
- Create `user-stories/scripts/tests/check-raid-log.test.sh` (red first), then `user-stories/scripts/check-raid-log.sh` (green). Same style and cases as above, plus a case that the real `user-stories/raid-log.md` passes.

### 5. Docs
- `user-stories/README.md` already lists `raid-log.md` and `scripts/`. Add one line under Layout or Conventions naming the two checkers and how to run them. Do not touch other docs.
- Do not edit story status. `status: done` is set by the `record` step after human review.

### 6. Validation
- Run the Validation Commands below. Every one must exit zero (or the stated non-zero for invalid inputs).

## Testing Strategy
### Unit Tests
Bash tests that source each checker (guarded `main`) and call the verdict functions directly where useful, otherwise run the script as a process:
- Register: complete valid case; each failure condition above, one case each, asserting the specific message text and the DEP ID.
- RAID: complete valid case; each of the four sections missing; each seed missing; prefix, duplicate, owner, date and column failures.

### CLI Tests
- Exit 0 and a `PASS` line on stdout for each valid fixture and for the real files.
- Exit 1 for each invalid case, stdout empty of `PASS`, stderr with the expected `FAIL file:line: id: message` line.
- Exit 2 for a nonexistent path and for no readable file. `-h` exits 0 with usage.
- Run from a different working directory (`cd /tmp`) with no arguments to prove the defaults resolve from the script location.

### Edge Cases
- Empty file, header-only table, missing table, rows with fewer or more cells than the header (reported as a malformed row with the line number).
- CRLF line endings and a trailing line without a newline.
- Extra whitespace inside cells, and cell text containing `slip-date:` in different case (match is case-sensitive; the test records this).
- Lowercase or mixed-case IDs (`dep-01`) count as unexpected, not as DEP-01.
- Non-ASCII text in cells (UTF-8 em dash) does not break parsing.

Coverage: the 80% Jest threshold is not applicable (no TypeScript). The substitute is that every failure message in Checker Design is asserted by at least one test, which the review step checks against this plan.

## Acceptance Criteria
1. When `user-stories/scripts/check-dependency-register.sh` runs against a register containing DEP-01 to DEP-29 once each, each with a non-empty owner, needed-by, type and status, it shall exit 0 and print a `PASS` line (F01-S01 criterion 1).
2. If any ID from DEP-01 to DEP-29 is missing, duplicated or replaced by an ID outside that range, then the register checker shall exit 1 and name that ID and its line.
3. If a register row has an empty owner, needed-by, type or status, then the register checker shall exit 1 and name the row and the empty field.
4. If a register row has a type outside A to E (with optional `+` secondary types) or a status outside `open`, `requested`, `in-progress`, `resolved`, `slipped`, then the register checker shall exit 1 and name the row and the value.
5. If a register row has status `slipped` and its Notes lack `slip-date: YYYY-MM-DD` or a non-empty `cause:`, then the register checker shall exit 1 and name which of the two is missing (F01-S01 criterion 3).
6. While a register row has status `slipped` with both a slip date and a cause, the register checker shall accept the row (F01-S01 criterion 3, valid case).
7. When `user-stories/scripts/check-raid-log.sh` runs against a RAID log with sections Risks, Assumptions, Issues and Decisions, each with the required columns, it shall exit 0 and print a `PASS` line (F01-S01 criterion 2).
8. If a RAID section or a required column is missing, then the RAID checker shall exit 1 and name the section or column.
9. If the Issues table lacks a row for any of Feature List Section 5 gaps 1 to 9, or the Decisions table lacks a row for any of Section 7 questions 1 to 7, then the RAID checker shall exit 1 and name the missing seed.
10. If a RAID row has an empty owner, a date that is not `YYYY-MM-DD`, an ID prefix that does not match its section, or a duplicate ID, then the RAID checker shall exit 1 and name the row.
11. If a seeded Section 7 question in Decisions has a status other than `open`, then the RAID checker shall exit 1 and name the row.
12. When the input file does not exist or cannot be read, each checker shall exit 2 and print a usage or error message to stderr.
13. When either checker runs, it shall list every failure found, not only the first, and shall exit 1 if the list is not empty.
14. When either checker runs without arguments from any working directory, it shall check the repository's real `user-stories/dependencies/README.md` or `user-stories/raid-log.md` and exit 0 on the committed files.
15. The checkers shall be deterministic and read-only: no network access, no AWS call, no clock dependence and no file written.
16. When `scripts/validate.sh` runs in planning mode, it shall run both checkers and both test scripts and exit 0 (the repository's validator gate for F01-S01).

## Validation Commands
Execute every command; each must exit zero unless stated. `npm run format:check`, `lint`, `build`, `test` and `synth` do not exist for a `planning` story (no `package.json`); `scripts/validate.sh` planning mode is the gate.

- `bash user-stories/scripts/check-dependency-register.sh` (real register, expect exit 0)
- `bash user-stories/scripts/check-raid-log.sh` (real RAID log, expect exit 0)
- `bash user-stories/scripts/check-dependency-register.sh user-stories/scripts/tests/fixtures/register-valid.md` (expect exit 0)
- `bash user-stories/scripts/check-raid-log.sh user-stories/scripts/tests/fixtures/raid-valid.md` (expect exit 0)
- `bash user-stories/scripts/tests/check-dependency-register.test.sh` (expect exit 0; includes the invalid cases, which the test asserts exit non-zero)
- `bash user-stories/scripts/tests/check-raid-log.test.sh` (expect exit 0)
- Invalid spot check: `sed '/^| DEP-17 /d' user-stories/dependencies/README.md > /tmp/r.md; bash user-stories/scripts/check-dependency-register.sh /tmp/r.md` (expect exit 1 with `DEP-17 is missing`)
- `VALIDATE_BASE_REF=origin/main bash scripts/validate.sh` from the repository root (expect `validate: PASS`)

## Notes
- No new dependencies. Bash, grep, awk and sed only.
- Deviation from the prompt template: the template asks for a TypeScript script, Jest tests, a Make target and the `npm run` stage list. `project-context.md` context-5 overrides those for `repo: planning` stories, and `scripts/validate.sh` planning mode runs exactly the Bash layout used here. The "pure function so Jest can test it" requirement becomes shell functions with a guarded `main`, tested by Bash test scripts.
- Story path note: the story's `verify:` lines write `scripts/check-*.sh`, which context-5 maps to `user-stories/scripts/`.
- Plan location: `plans-1` says plan files live under `plans/` in its check text, but its rule text names no directory. The harness contract names `specs/checker-scripts/`, so this plan is there.
- The register has no place for the slip date and cause today. Adding a `Notes` column is the smallest change and matches the register prose ("a `slipped` row needs a slip date and cause in the notes"). F01-S06 later adds "days late" to the same note and extends the checker. The note format `slip-date: ...; cause: ...` is chosen so S06 can append `; days-late: n` without breaking S01.
- Needed-by values are free text (`Nov 16`, `Week 1`, `Weeks 1 to 3`), so the checker tests only that the cell is non-empty. Date parsing and overdue logic belong to F01-S06 (`check-overdue.sh`).
- Owner "to be named" (DEP-18) counts as non-empty, as the story states.
- Open questions for a human: (1) confirm Mike as owner where no source names one for a RAID seed row; (2) the RAID seed dates (source due date where present, otherwise 2026-11-20) are proposals for Mike to adjust. Neither blocks the story.
- Freezes (context-4) do not apply: planning-mode change, dated Nov 2026.
