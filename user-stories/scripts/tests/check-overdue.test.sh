#!/usr/bin/env bash
# Story: F01-S06 - tests for the overdue dependency checker
set -uo pipefail
export LC_ALL=C

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS="$(cd "$HERE/.." && pwd)"
STORIES="$(cd "$SCRIPTS/.." && pwd)"
CHECK="$SCRIPTS/check-overdue.sh"
VALID="$HERE/fixtures/register-valid.md"
REAL="$STORIES/dependencies/README.md"
SNAPSHOT="$HERE/fixtures/register-2026-11-20.md"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
FAILS=0
RC=0
OUT=""
ERR=""

pass() { echo "ok   - $1"; }
fail() { echo "FAIL - $1"; FAILS=$((FAILS + 1)); }

# run_check [args...]: sets RC, OUT (stdout), ERR (stderr)
run_check() {
  bash "$CHECK" "$@" >"$WORK/out" 2>"$WORK/err"
  RC=$?
  OUT="$(cat "$WORK/out")"
  ERR="$(cat "$WORK/err")"
}

# check NAME CONDITION...: pass when the shell condition is true
check() {
  local name="$1"; shift
  if "$@"; then pass "$name"; else fail "$name (rc=$RC out=$OUT err=$ERR)"; fi
}

rc_is() { [ "$RC" -eq "$1" ]; }
out_has() { printf '%s\n' "$OUT" | grep -qF -- "$1"; }
err_has() { printf '%s\n' "$ERR" | grep -qF -- "$1"; }
# overdue_line ID: the OVERDUE line for ID, empty when not listed
overdue_line() { printf '%s\n' "$OUT" | grep "^OVERDUE .*: $1: " || true; }
listed() { [ -n "$(overdue_line "$1")" ]; }
not_listed() { [ -z "$(overdue_line "$1")" ]; }
line_has() { overdue_line "$1" | grep -qF -- "$2"; }

# set_cell FILE ID COLUMN_NUMBER VALUE: replace one cell (column 2 = ID, 5 = Needed by, 7 = Status)
set_cell() {
  awk -F'|' -v id="$2" -v col="$3" -v val="$4" 'BEGIN{OFS="|"}
    { c=$2; gsub(/^ +| +$/, "", c); if (c == id) $col = " " val " "; print }' "$1" >"$1.tmp" && mv "$1.tmp" "$1"
}

mutant() { # mutant NAME -> path of a fresh copy of the valid fixture
  cp "$VALID" "$WORK/$1.md"
  echo "$WORK/$1.md"
}

# AC1, AC2, AC4: fixture on 2026-11-17
run_check --today 2026-11-17 "$VALID"
check "F01-S06 AC1: overdue rows give exit 1" rc_is 1
check "F01-S06 AC2: DEP-01 (Nov 16, open) is listed" listed DEP-01
check "F01-S06 AC2: DEP-02 (Nov 17, due today) is listed" listed DEP-02
check "F01-S06 AC2: DEP-03 (Nov 18) is not listed" not_listed DEP-03
check "F01-S06 AC4: DEP-01 shows needed-by text and due date" line_has DEP-01 "needed by Nov 16 (2026-11-16)"
check "F01-S06 AC4: DEP-01 shows status" line_has DEP-01 "status open"
check "F01-S06 AC4: DEP-01 is 1 day late" line_has DEP-01 "days late 1"
check "F01-S06 AC4: DEP-02 due today is 0 days late" line_has DEP-02 "days late 0"
n="$(printf '%s\n' "$OUT" | grep -c '^OVERDUE ')"
check "F01-S06 AC2: exactly two rows listed on 2026-11-17 ($n)" [ "$n" -eq 2 ]
check "F01-S06 AC4: line uses OVERDUE <file>:<line>: format" bash -c "printf '%s\n' \"\$1\" | grep -qE '^OVERDUE .+:5: DEP-01: '" _ "$OUT"
check "F01-S06 AC1: no PASS line when rows are overdue" bash -c "! printf '%s' \"\$1\" | grep -q '^PASS'" _ "$OUT"

# AC7: nothing overdue
run_check --today 2026-11-15 "$VALID"
check "F01-S06 AC7: nothing due by 2026-11-15 exits 0" rc_is 0
check "F01-S06 AC7: PASS line names the date" out_has "no dependency overdue on 2026-11-15"
check "F01-S06 AC7: no OVERDUE line" not_listed DEP-01

# AC1: resolved rows are not overdue
f="$(mutant resolved)"; set_cell "$f" DEP-01 7 "resolved"
run_check --today 2026-11-17 "$f"
check "F01-S06 AC1: resolved DEP-01 is not listed" not_listed DEP-01
check "F01-S06 AC1: open DEP-02 is still listed" listed DEP-02
check "F01-S06 AC1: still exit 1" rc_is 1

# AC1: slipped rows are overdue
run_check --today 2026-11-18 "$VALID"
check "F01-S06 AC1: slipped DEP-03 is listed on its due date" listed DEP-03
check "F01-S06 AC4: DEP-03 shows status slipped" line_has DEP-03 "status slipped"

# AC5: week parsing
run_check --today 2026-11-19 "$VALID"
check "F01-S06 AC5: Week 1 (DEP-04) is not due on Thu 2026-11-19" not_listed DEP-04
run_check --today 2026-11-20 "$VALID"
check "F01-S06 AC5: Week 1 (DEP-04) is due Fri 2026-11-20" line_has DEP-04 "(2026-11-20)"
check "F01-S06 AC5: 'Week 1 and ongoing' (DEP-05) is due 2026-11-20" line_has DEP-05 "(2026-11-20)"
run_check --today 2026-12-03 "$VALID"
check "F01-S06 AC5: 'Weeks 1 to 3' (DEP-14) is not due on 2026-12-03" not_listed DEP-14
run_check --today 2026-12-04 "$VALID"
check "F01-S06 AC5: 'Weeks 1 to 3' (DEP-14) is due Fri 2026-12-04" line_has DEP-14 "(2026-12-04)"
check "F01-S06 AC5: 'Dec 4' (DEP-16) is 2026-12-04" line_has DEP-16 "(2026-12-04)"

# AC5: other months
f="$(mutant january)"; set_cell "$f" DEP-01 5 "Jan 5"
run_check --today 2026-12-31 "$f"
check "F01-S06 AC5: 'Jan 5' is 2027, so not due on 2026-12-31" not_listed DEP-01
run_check --today 2027-01-05 "$f"
check "F01-S06 AC5: 'Jan 5' is 2027-01-05" line_has DEP-01 "(2027-01-05)"
f="$(mutant week6)"; set_cell "$f" DEP-01 5 "Week 6"
run_check --today 2026-12-25 "$f"
check "F01-S06 AC5: 'Week 6' is Fri 2026-12-25" line_has DEP-01 "(2026-12-25)"

# AC4: days late across a month boundary
run_check --today 2026-12-01 "$VALID"
check "F01-S06 AC4: DEP-01 is 15 days late on 2026-12-01" line_has DEP-01 "days late 15"

# AC6: unparseable needed-by
f="$(mutant bad-needed)"; set_cell "$f" DEP-01 5 "soon"
run_check --today 2026-11-17 "$f"
check "F01-S06 AC6: unparseable needed-by exits 1 with --today" rc_is 1
check "F01-S06 AC6: finding names the row and the value" err_has 'DEP-01: needed-by "soon" is not a date'
run_check "$f"
check "F01-S06 AC6: unparseable needed-by exits 1 without --today" rc_is 1
check "F01-S06 AC6: finding is reported without --today" err_has 'DEP-01: needed-by "soon" is not a date'

# AC8: no --today reads no clock and passes when every date parses
run_check "$VALID"
check "F01-S06 AC8: no --today on the fixture exits 0" rc_is 0
check "F01-S06 AC8: PASS line reports the parsed dates" out_has "needed-by dates parse"
check "F01-S06 AC8: no OVERDUE line without --today" not_listed DEP-01

# Missing column
f="$(mutant no-needed-column)"; sed -i 's/| Needed by |/| Due |/' "$f"
run_check --today 2026-11-17 "$f"
check "F01-S06 AC6: missing Needed by column exits 1" rc_is 1
check "F01-S06 AC6: finding names the column" err_has 'lacks column "Needed by"'

# AC9: usage errors
run_check --today 17/11/2026 "$VALID"
check "F01-S06 AC9: --today 17/11/2026 exits 2" rc_is 2
run_check --today 2026-02-30 "$VALID"
check "F01-S06 AC9: --today 2026-02-30 is not a real date, exits 2" rc_is 2
run_check --today
check "F01-S06 AC9: --today without a value exits 2" rc_is 2
check "F01-S06 AC9: usage error prints to stderr" [ -n "$ERR" ]
run_check --today 2026-11-17 "$WORK/does-not-exist.md"
check "F01-S06 AC9: nonexistent file exits 2" rc_is 2
run_check -h
check "F01-S06 AC9: -h exits 0" rc_is 0
check "F01-S06 AC9: -h prints usage" bash -c "printf '%s%s' \"\$1\" \"\$2\" | grep -qi usage" _ "$OUT" "$ERR"

# Input robustness: CRLF gives the same list
run_check --today 2026-11-17 "$VALID"; base="$(printf '%s\n' "$OUT" | grep -o 'DEP-[0-9]*: needed by.*')"
sed 's/$/\r/' "$VALID" >"$WORK/crlf.md"
run_check --today 2026-11-17 "$WORK/crlf.md"; crlf="$(printf '%s\n' "$OUT" | grep -o 'DEP-[0-9]*: needed by.*')"
check "F01-S06 AC1: CRLF input gives the same overdue list" [ "$base" = "$crlf" ]

# AC10: read-only
before="$(cksum <"$VALID")"
mkdir "$WORK/ro" && (cd "$WORK/ro" && bash "$CHECK" --today 2026-11-17 "$VALID" >/dev/null 2>&1)
after="$(cksum <"$VALID")"
check "F01-S06 AC10: input file is unchanged" [ "$before" = "$after" ]
check "F01-S06 AC10: no file written to the working directory" [ -z "$(ls -A "$WORK/ro")" ]

# AC3: register as of 2026-11-20 (frozen snapshot, so later status changes do not break the test)
run_check --today 2026-11-17 "$SNAPSHOT"
check "F01-S06 AC3: 2026-11-20 register on 2026-11-17 exits 1" rc_is 1
check "F01-S06 AC3: 2026-11-20 register lists DEP-02" listed DEP-02
check "F01-S06 AC3: 2026-11-20 register does not list resolved DEP-01" not_listed DEP-01
n="$(printf '%s\n' "$OUT" | grep -c '^OVERDUE ')"
check "F01-S06 AC3: 2026-11-20 register lists only DEP-02 on 2026-11-17 ($n)" [ "$n" -eq 1 ]

# AC8: the real register's needed-by dates all parse (no status dependence)
run_check "$REAL"
check "F01-S06 AC8: real register dates parse, exit 0" rc_is 0

# Review fixes: more invalid needed-by values
for v in "Week 0" "Feb 29" "Feb 30" "Weeks 3 to 1" "Week 1 to 3"; do
  f="$(mutant "needed-$(printf '%s' "$v" | tr ' ' '-')")"; set_cell "$f" DEP-01 5 "$v"
  run_check "$f"
  check "F01-S06 AC6: needed-by '$v' is not a date" err_has "DEP-01: needed-by \"$v\" is not a date"
done

# Review fixes: rows that are not DEP-nn inside the table are reported
f="$(mutant bad-id)"; sed -i 's/^| DEP-01 /| DEP01 /' "$f"
run_check "$f"
check "F01-S06 AC6: malformed ID exits 1" rc_is 1
check "F01-S06 AC6: malformed ID is named" err_has 'unexpected ID DEP01'

# Review fixes: no register table
printf '# Title\n\nno table here\n' >"$WORK/notable.md"
run_check "$WORK/notable.md"
check "F01-S06 AC6: file without a register table exits 1" rc_is 1
check "F01-S06 AC6: missing table is named" err_has "register table not found"

# Review fixes: usage errors
run_check --today "" "$VALID"
check "F01-S06 AC9: --today with an empty value exits 2" rc_is 2
run_check "$VALID" "$VALID"
check "F01-S06 AC9: a second file argument exits 2" rc_is 2

# AC8, AC11: no arguments from another directory checks the real register
(cd "$WORK" && bash "$CHECK" >"$WORK/out" 2>"$WORK/err"); RC=$?; OUT="$(cat "$WORK/out")"; ERR="$(cat "$WORK/err")"
check "F01-S06 AC11: no arguments from another directory exits 0" rc_is 0
check "F01-S06 AC11: no arguments checks the real register" out_has "user-stories/dependencies/README.md"

# AC12: the register checker still enforces slip date and cause
f="$(mutant slipped-no-date)"; set_cell "$f" DEP-03 9 "cause: text"
bash "$SCRIPTS/check-dependency-register.sh" "$f" >/dev/null 2>"$WORK/err"; RC=$?; ERR="$(cat "$WORK/err")"
check "F01-S06 AC12: register checker fails a slipped row without slip date" rc_is 1
check "F01-S06 AC12: finding names the missing slip date" err_has "slipped row has no slip date"

echo
if [ "$FAILS" -ne 0 ]; then echo "check-overdue tests: $FAILS failed"; exit 1; fi
echo "check-overdue tests: all passed"
