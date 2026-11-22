# Checker: Appendix B pre-flight answers checker

## Description
One deterministic Bash checker plus the pre-flight evidence files for the planning repository. Story id: F02-S01 (Run the pre-flight checks and confirm services in us-east-1, SOW D2). Classification token: `checker-script`.

`check-appendix-b.sh` reads `user-stories/evidence/F02/preflight/appendix-b.md` and confirms that all 13 questions of the Appendix B pre-flight questionnaire are present once and have a real answer. It is the verify step of F02-S01 criterion 2.

The story changes the parent planning repository only (`repo: planning`). Per `project-context.md` context-5 the CDK/npm rules do not apply: the checker is Bash under `user-stories/scripts/`, its test is Bash under `user-stories/scripts/tests/`, and `scripts/validate.sh` planning mode runs them.

Scope after RAID D-14 (Soma Muniyappa, 2026-11-22): Control Tower already exists in management account `463768556578`. CapNexus works through `CapNexusDeploymentRole` in `166390307071`. Mitsui supplies the management-account answers in writing.

## User Story
As Soma (CapNexus solution architect)
I want the 13 Appendix B questions checked for an answer each
So that a design gap in the Mitsui organization shows up in Week 1.

## Relevant Files
- `user-stories/features/F02-landing-zone-as-code/stories/F02-S01-preflight-and-service-availability.md`: the story. Criterion 1 and the Mitsui part of 2 and the review in 3 are gates.
- `knowledge/Mitsui-WDA-POC-Client-Dependencies-and-Sharing-Strategy.md`, "Appendix B: AWS organization pre-flight questionnaire": the 13 questions and the answers recorded so far (kickoff). Question 1 to 13 are copied into `appendix-b.md` unchanged.
- `user-stories/raid-log.md`: D-14 (account map, role accepted), I-09.
- `user-stories/dependencies/README.md`: DEP-02, DEP-06.
- `user-stories/scripts/check-overdue.sh` and its test: the structure reused (header-driven awk parse, guarded `main`, exit 0/1/2, no clock).
- `scripts/validate.sh`: planning mode runs every `user-stories/scripts/check-*.sh` with no arguments and every `user-stories/scripts/tests/*.sh`. Frozen, not edited.
- Task list Tue 2026-11-17 and `knowledge/...Sharing-Strategy.md` risk 17: the service list for criterion 3.

### New Files
- `user-stories/scripts/check-appendix-b.sh`: the checker.
- `user-stories/scripts/tests/check-appendix-b.test.sh`: its tests.
- `user-stories/scripts/tests/fixtures/appendix-b-valid.md`: 13 answered questions.
- `user-stories/evidence/F02/preflight/appendix-b.md`: the 13 questions with the answers known on 2026-11-22. Unanswered rows stay empty for Mitsui.
- `user-stories/evidence/F02/preflight/caller-identity.txt`: account ID and role name only.
- `user-stories/evidence/F02/preflight/service-availability.md`: eight services with a result and a source link.

## Acceptance Criteria
1. `check-appendix-b.sh FILE` shall exit 0 and print `PASS` when FILE has 13 rows numbered 1 to 13, each with a non-empty answer that is not a placeholder.
2. The checker shall exit 1 and print `FAIL <file>:<line>: question <n>: no answer` for a row with an empty answer.
3. The checker shall treat the answers `TBD`, `Pending`, `To confirm` and `To be confirmed` (any case, with or without a full stop) as no answer.
4. The checker shall exit 1 and name each question number from 1 to 13 that has no row, and each number that appears more than once.
5. The checker shall list every finding in one run, not stop at the first.
6. The checker shall exit 1 when no table with the columns `#`, `Question` and `Mitsui answer` is found, and name the missing column.
7. When run with no argument, the checker shall check only the structure (13 numbered rows, no duplicates) of the default file `user-stories/evidence/F02/preflight/appendix-b.md`, shall exit 0 when the structure is right even if answers are missing, and shall print how many questions have an answer. This keeps `scripts/validate.sh`, which passes no arguments, passing while Mitsui answers are open.
8. The checker shall exit 2 for an unreadable file or an unknown option, and exit 0 with usage text for `-h`.
9. The checker shall give the same result for a file with CRLF line endings.
10. The checker shall write no file and make no network, AWS or clock call.
11. The file `service-availability.md` shall list eight services, each with a result of `available`, `limited` or `missing` and an `https://` source link. The eight are AgentCore Gateway, AgentCore Identity, AgentCore Runtime, AgentCore Policy, S3 Tables, Lake Formation with S3 Tables, identity-aware Athena workgroups and Claude model access in Bedrock. (The task list names seven items. S3 Tables with Lake Formation is split in two to reach the story's eight.)
12. `caller-identity.txt` shall contain the account ID and role name only, and no key, token or external ID.
13. Each gap in `service-availability.md` shall have a RAID log row of type risk or issue. The design response is recorded by Soma (gate).

## Checker Design
- Usage: `check-appendix-b.sh [FILE]`. `-h` prints usage. FILE defaults to `user-stories/evidence/F02/preflight/appendix-b.md`, resolved from the script's location. A given FILE gets the full check. No FILE gets the structure-only check (criterion 7).
- Parsing: the table is the first table whose header has `#`, `Question` and `Mitsui answer`, found by header name. CRLF is stripped. Rows are lines starting with `|` after the separator row. Cell text is trimmed.
- An answer is missing when the cell is empty or matches, ignoring case, spaces and a trailing full stop, one of `tbd`, `pending`, `to confirm`, `to be confirmed`.
- Output: `PASS <file>: 13 of 13 questions answered`, or `FAIL <file>:<line>: <message>` on stderr for each finding.
- Exit codes: 0 pass, 1 findings, 2 usage or unreadable file.
- Tools: `bash`, `awk`, `sed`, `grep`, `tr` only, `LC_ALL=C`. Works under Git Bash on Windows.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Tests (written first, red)
- Create `user-stories/scripts/tests/check-appendix-b.test.sh` and the fixture. Test names start with `F02-S01 AC<n>` and cover criteria 1 to 10 and the real `appendix-b.md` structure. It must fail because the checker does not exist yet.

### 2. Checker (green)
- Create `user-stories/scripts/check-appendix-b.sh` with the header `# Story: F02-S01 - Appendix B answers checker`. Make step 1 pass without changing the test file.

### 3. Evidence files
- Create `appendix-b.md`, `caller-identity.txt` and `service-availability.md` as described under New Files. Record each gap in `raid-log.md`.

### 4. Docs
- Add `check-appendix-b.sh` to the checker line in `user-stories/README.md` Conventions.

### 5. Validation
- Run the Validation Commands below.

## Validation Commands
- `bash user-stories/scripts/tests/check-appendix-b.test.sh` exits 0.
- `bash user-stories/scripts/check-appendix-b.sh` exits 0 (structure only).
- `bash user-stories/scripts/check-appendix-b.sh user-stories/evidence/F02/preflight/appendix-b.md` exits 0 only after Mitsui has answered all 13 questions. Until then it exits 1 and lists the open questions.
- The other `check-*.sh` and their tests still pass.

## Open points
- Story criterion 2 cannot be met until Mitsui answers the management-account questions (Config trusted access, STS, CloudTrail, SCPs, tags, quotas, on-prem network). The story stays `in-progress` until then.
