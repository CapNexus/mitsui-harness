# Checker: Overdue dependency checker

## Description
One deterministic Bash checker for the planning repository. Story id: F01-S06 (Log slipped dependencies and shift plan dates, SOW D1). Classification token: `checker-script`.

`check-overdue.sh` reads `user-stories/dependencies/README.md` and, given a date with `--today`, lists every dependency whose needed-by date is on or before that date and whose status is not `resolved`, with the number of days late. This is the evidence for SOW Assumption 8 (plan dates shift by the days a Mitsui dependency is late).

Scope after RAID D-13 (Soma Muniyappa, 2026-11-20): only `check-overdue.sh` is built. `shift-plan.sh` and a stored days-late field are dropped. Days late are computed by this checker, and plan shifts are made by Mike Charow in the project plan (RAID D-08).

The story changes the parent planning repository only (`repo: planning`). Per `project-context.md` context-5 the CDK/npm rules do not apply: the checker is Bash under `user-stories/scripts/`, its test is Bash under `user-stories/scripts/tests/`, and `scripts/validate.sh` planning mode runs them.

## User Story
As Mike (CapNexus project manager)
I want every late Mitsui dependency listed with its date and days late
So that the SOW schedule protection (Assumption 8) is documented when a dependency slips.

## Relevant Files
- `user-stories/features/F01-mobilization-governance/stories/F01-S06-slipped-dependency-handling.md`: the story; criteria 1 and 2 are in scope, 3 and 4 are gates after D-13.
- `user-stories/dependencies/README.md`: the register. Columns `ID | Dependency | Owner (Mitsui) | Needed by | Type | Status | Used by features | Notes`. Needed-by values are free text: `Nov 16`, `Dec 4`, `Week 1`, `Week 1 and ongoing`, `Weeks 1 to 3`, `Week 6`.
- `user-stories/raid-log.md`: D-08 (project plan is the source of truth), D-13 (scope cut).
- `task-list/week-1/README.md` ("Dates: Nov 16 to Nov 20") and the project plan rows P10 to P13 (2026-11-16 to 2026-11-20): Week 1 runs Mon 2026-11-16 to Fri 2026-11-20.
- `user-stories/scripts/check-dependency-register.sh`: existing checker. Already fails a `slipped` row without slip date or cause (F01-S06 criterion 2, F01-S01 criterion 3). Not changed. Its structure (header-driven awk parse, guarded `main`, exit 0/1/2) is reused.
- `user-stories/scripts/tests/fixtures/register-valid.md`: existing valid fixture (DEP-01 `Nov 16` open, DEP-02 `Nov 17` open, DEP-03 `Nov 18` slipped). Reused read-only, not changed.
- `scripts/validate.sh`: planning mode runs every `user-stories/scripts/check-*.sh` with no arguments and every `user-stories/scripts/tests/*.sh`. Frozen, not edited.

### New Files
- `user-stories/scripts/check-overdue.sh`: the checker.
- `user-stories/scripts/tests/check-overdue.test.sh`: its tests. Invalid inputs are one-change mutations of the valid fixture in a `mktemp -d` directory, as in the F01-S01 tests.

## Checker Design
- Usage: `check-overdue.sh [--today YYYY-MM-DD] [FILE]`. `-h` prints usage and exits 0. FILE defaults to the repository's `user-stories/dependencies/README.md`, resolved from the script's location.
- Parsing: the register table is the first table whose header has `ID` and `Status`. Columns `ID`, `Needed by` and `Status` are found by header name. CRLF is stripped. Rows start with `| DEP-`.
- Needed-by to date (the due date):
  - `Mon D` or `Mon DD` with a three-letter English month (`Jan` to `Dec`): `Nov` and `Dec` are 2026, `Jan` to `Oct` are 2027 (the POC runs Nov 2026 to Dec 2026, so a January date can only be the following year).
  - `Week N`, optionally followed by more text (`Week 1 and ongoing`): Friday of week N, where week 1 is Mon 2026-11-16 to Fri 2026-11-20. Week N ends 2026-11-20 plus 7 x (N - 1) days.
  - `Weeks A to B`: Friday of week B.
  - Anything else is a finding: `FAIL <file>:<line>: <DEP-nn>: needed-by "<text>" is not a date`.
- Without `--today`: no clock is read. The checker only confirms that every needed-by value converts to a date. All convert: exit 0 with `PASS <file>: <n> needed-by dates parse`. Any does not: exit 1 with the FAIL lines on stderr. This keeps `scripts/validate.sh` (which passes no arguments) deterministic.
- With `--today D`: `D` must be a real calendar date in `YYYY-MM-DD` form, else exit 2. A row is overdue when its due date is on or before `D` and its status is not `resolved`. For each overdue row, stdout gets `OVERDUE <file>:<line>: <DEP-nn>: needed by <text> (<YYYY-MM-DD>), status <status>, days late <n>`, where `n` is `D` minus the due date in days (0 when due today). Any overdue row or FAIL: exit 1. None: exit 0 with `PASS <file>: no dependency overdue on <D>`.
- Missing `ID`, `Needed by` or `Status` column, or no register table: FAIL line naming it, exit 1.
- Exit codes: 0 pass, 1 findings (overdue rows or FAIL lines, all listed), 2 usage error, bad `--today`, unreadable file.
- Determinism: no network, no AWS, no system clock, no randomness. `bash`, `awk`, `sed`, `grep`, `tr` only, `LC_ALL=C`. Works under Git Bash on Windows. Date arithmetic uses a days-from-civil formula in awk, not `date`.
- Read-only: writes no file.

## Fixtures
- Valid: the existing `register-valid.md`. As of 2026-11-17, DEP-01 (`Nov 16`, open, 1 day late) and DEP-02 (`Nov 17`, open, 0 days late) are overdue, and DEP-03 (`Nov 18`) is not.
- Mutations in the test: DEP-01 set to `resolved`; DEP-01 needed-by set to `soon`; the `Needed by` header cell renamed; CRLF copy.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Tests (written first, red)
- Create `user-stories/scripts/tests/check-overdue.test.sh` in the style of `check-dependency-register.test.sh`, with test names starting `F01-S06 AC<n>`, covering every case in Testing Strategy. Commit it alone. It must fail because the checker does not exist yet.

### 2. Checker (green)
- Create `user-stories/scripts/check-overdue.sh` with the header comment `# Story: F01-S06 - overdue dependency checker`, functions for parsing and a guarded `main`. Mark it executable in git. Make step 1 pass without changing the test file.

### 3. Docs
- Add `check-overdue.sh` to the checker line in `user-stories/README.md` Conventions.

### 4. Validation
- Run the Validation Commands below.

## Testing Strategy
### CLI Tests
- Fixture, `--today 2026-11-17`: exit 1; stdout lists DEP-01 with `(2026-11-16)` and `days late 1`, and DEP-02 with `days late 0`; does not list DEP-03.
- Fixture, `--today 2026-11-15`: exit 0, `PASS`, no `OVERDUE` line.
- Fixture with DEP-01 set to `resolved`, `--today 2026-11-17`: DEP-01 not listed, DEP-02 listed.
- Fixture, `--today 2026-11-18`: DEP-03 (`slipped`) listed with `status slipped`.
- Week parsing: `--today 2026-11-19` does not list DEP-04 (`Week 1`); `--today 2026-11-20` lists DEP-04 and DEP-05 (`Week 1 and ongoing`) with `(2026-11-20)`.
- Weeks range: DEP-14 (`Weeks 1 to 3`) is listed with `(2026-12-04)` on 2026-12-04 and not on 2026-12-03.
- Month boundary: `--today 2026-12-01` gives DEP-01 `days late 15`.
- `Dec` date: DEP-16 (`Dec 4`) listed with `(2026-12-04)` on 2026-12-04.
- Unparseable needed-by `soon`: exit 1 and stderr `DEP-01: needed-by "soon" is not a date`, with and without `--today`.
- No `--today` on the fixture: exit 0, `PASS`, no `OVERDUE` line.
- Missing `Needed by` column: exit 1, stderr names the column.
- Bad `--today` (`17/11/2026`, `2026-02-30`, `--today` with no value): exit 2.
- Nonexistent file: exit 2. `-h`: exit 0 and usage.
- CRLF copy of the fixture gives the same overdue list as the original.
- Read-only: fixture checksum unchanged and no file written in the working directory.
- Real register, `--today 2026-11-17`: exit 1, lists DEP-02, does not list DEP-01 (resolved 2026-11-20).
- Real register, no arguments, from another working directory: exit 0 and `PASS`.

Coverage: the Jest threshold does not apply (no TypeScript). Every output message and exit code in Checker Design is asserted by at least one test.

## Acceptance Criteria
1. When `check-overdue.sh --today D` runs, it shall list every register row whose needed-by date is on or before `D` and whose status is not `resolved`, and shall exit 1 if at least one row is listed (F01-S06 criterion 1).
2. When the checker runs with `--today 2026-11-17` against the test fixture, it shall list DEP-01 and DEP-02 and shall not list DEP-03.
3. When the checker runs with `--today 2026-11-17` against the real register, it shall list DEP-02 and shall not list DEP-01, because DEP-01 is `resolved`.
4. Each listed row shall show the dependency ID, its needed-by text, the resolved due date as `YYYY-MM-DD`, its status, and the days late as `D` minus the due date (F01-S06 criterion 2, days late).
5. The checker shall convert `Mon D` dates to 2026 for `Nov` and `Dec` and to 2027 for `Jan` to `Oct`, `Week N` to the Friday of week N, and `Weeks A to B` to the Friday of week B, with week 1 ending Fri 2026-11-20.
6. If a needed-by value cannot be converted to a date, then the checker shall exit 1 and name the row and the value.
7. When no row is overdue, the checker shall exit 0 and print a `PASS` line.
8. When the checker runs without `--today`, it shall not read the system clock and shall exit 0 if every needed-by value converts to a date.
9. If `--today` is missing its value or is not a real `YYYY-MM-DD` date, or the input file cannot be read, then the checker shall exit 2 with a message on stderr.
10. The checker shall be read-only and deterministic: no network, no AWS call, no file written.
11. When `scripts/validate.sh` runs in planning mode, the new checker and its test shall run and exit 0.
12. The existing `check-dependency-register.sh` shall continue to fail a `slipped` row without a slip date or cause (F01-S06 criterion 2), and its tests shall still pass.

## Validation Commands
Each must exit zero unless stated.

- `bash user-stories/scripts/tests/check-overdue.test.sh`
- `bash user-stories/scripts/check-overdue.sh` (real register, no clock, expect exit 0)
- `bash user-stories/scripts/check-overdue.sh --today 2026-11-17` (expect exit 1, lists DEP-02)
- `bash user-stories/scripts/tests/check-dependency-register.test.sh`
- `bash user-stories/scripts/tests/check-raid-log.test.sh`
- `bash scripts/validate.sh` from the repository root (expect `validate: PASS`)

## Notes
- The story's verify line says the real register lists DEP-01 on 2026-11-17. DEP-01 was resolved on 2026-11-20, so the story text was updated in the same branch to name DEP-02 for the register and DEP-01 for the fixture.
- Week 6 resolves to Fri 2026-12-25, a holiday. The checker uses the calendar Friday; holiday handling is not in scope.
- No new dependencies.
- Freezes (context-4) do not apply: planning change dated 2026-11-20.
