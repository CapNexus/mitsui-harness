#!/usr/bin/env bash
# Story: F01-S01 - tests for the dependency register checker
set -uo pipefail
export LC_ALL=C

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS="$(cd "$HERE/.." && pwd)"
STORIES="$(cd "$SCRIPTS/.." && pwd)"
CHECK="$SCRIPTS/check-dependency-register.sh"
VALID="$HERE/fixtures/register-valid.md"
REAL="$STORIES/dependencies/README.md"

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

expect_pass() {
  local name="$1"; shift
  run_check "$@"
  if [ "$RC" -eq 0 ] && printf '%s' "$OUT" | grep -q '^PASS '; then pass "$name"; else fail "$name (rc=$RC out=$OUT err=$ERR)"; fi
}

# expect_fail NAME FILE FRAGMENT...: exit 1, no PASS line, every fragment on stderr
expect_fail() {
  local name="$1" file="$2"; shift 2
  run_check "$file"
  local ok=1 frag
  [ "$RC" -eq 1 ] || ok=0
  printf '%s' "$OUT" | grep -q 'PASS' && ok=0
  for frag in "$@"; do
    printf '%s' "$ERR" | grep -qF -- "$frag" || { ok=0; echo "     missing fragment: $frag"; }
  done
  if [ "$ok" -eq 1 ]; then pass "$name"; else fail "$name (rc=$RC err=$ERR)"; fi
}

expect_absent() {
  local name="$1" fragment="$2"
  if printf '%s' "$ERR" | grep -qF -- "$fragment"; then fail "$name (unexpected: $fragment)"; else pass "$name"; fi
}

# set_cell FILE ID COLUMN_NUMBER VALUE: replace one cell of the row (column 2 = ID ... 9 = Notes)
set_cell() {
  awk -F'|' -v id="$2" -v col="$3" -v val="$4" 'BEGIN{OFS="|"}
    { c=$2; gsub(/^ +| +$/, "", c); if (c == id) $col = " " val " "; print }' "$1" >"$1.tmp" && mv "$1.tmp" "$1"
}

mutant() { # mutant NAME -> path of fresh copy of the valid fixture
  cp "$VALID" "$WORK/$1.md"
  echo "$WORK/$1.md"
}

# AC1, AC6: valid register, including a valid slipped row (DEP-03)
expect_pass "F01-S01 AC1: valid register with 29 rows passes" "$VALID"
expect_pass "F01-S01 AC6: slipped row with slip-date and cause is accepted" "$VALID"
grep -q 'slipped' "$VALID" && pass "F01-S01 AC6: fixture really contains a slipped row" || fail "F01-S01 AC6: fixture has no slipped row"

# AC2: IDs
f="$(mutant dep-missing)"; sed -i '/^| DEP-17 /d' "$f"
expect_fail "F01-S01 AC2: missing DEP-17 is reported" "$f" "DEP-17 is missing"

f="$(mutant dep-duplicate)"; grep '^| DEP-05 ' "$VALID" >>"$f"
expect_fail "F01-S01 AC2: duplicate DEP-05 is reported with its lines" "$f" "DEP-05 appears more than once" "lines"

f="$(mutant dep-unexpected)"; sed -i 's/^| DEP-29 /| DEP-30 /' "$f"
expect_fail "F01-S01 AC2: DEP-30 replacing DEP-29 gives two findings" "$f" "DEP-29 is missing" "unexpected ID DEP-30"

f="$(mutant dep-lowercase)"; sed -i 's/^| DEP-01 /| dep-01 /' "$f"
expect_fail "F01-S01 AC2: lowercase dep-01 does not count as DEP-01" "$f" "DEP-01 is missing"

f="$(mutant dep-missing-line)"; sed -i '/^| DEP-17 /d' "$f"
run_check "$f"
if printf '%s' "$ERR" | grep -qE '^FAIL .*:[0-9]*: .*DEP-17'; then pass "F01-S01 AC2: finding uses FAIL <file>:<line>: format"; else fail "F01-S01 AC2: finding format (err=$ERR)"; fi

# AC3: empty cells (DEP-04: owner=4 needed-by=5 type=6 status=7)
f="$(mutant owner-empty)"; set_cell "$f" DEP-04 4 ""
expect_fail "F01-S01 AC3: empty owner names DEP-04" "$f" "DEP-04: owner is empty"
f="$(mutant needed-by-empty)"; set_cell "$f" DEP-04 5 ""
expect_fail "F01-S01 AC3: empty needed-by names DEP-04" "$f" "DEP-04: needed-by is empty"
f="$(mutant type-empty)"; set_cell "$f" DEP-04 6 ""
expect_fail "F01-S01 AC3: empty type names DEP-04" "$f" "DEP-04: type is empty"
f="$(mutant status-empty)"; set_cell "$f" DEP-04 7 ""
expect_fail "F01-S01 AC3: empty status names DEP-04" "$f" "DEP-04: status is empty"

# Owner "to be named" (DEP-18) counts as non-empty
expect_pass "F01-S01 AC3: owner 'to be named' (DEP-18) is accepted" "$VALID"

# AC4: type and status values
f="$(mutant type-bad)"; set_cell "$f" DEP-04 6 "Z"
expect_fail "F01-S01 AC4: type Z is rejected" "$f" "DEP-04" 'type "Z" is not A to E'
f="$(mutant type-secondary)"; set_cell "$f" DEP-04 6 "C+E"
expect_pass "F01-S01 AC4: secondary type C+E is accepted" "$f"
f="$(mutant status-bad)"; set_cell "$f" DEP-04 7 "done"
expect_fail "F01-S01 AC4: status done is rejected" "$f" "DEP-04" 'status "done" is not allowed'
for s in open requested in-progress resolved; do
  f="$(mutant "status-$s")"; set_cell "$f" DEP-04 7 "$s"
  expect_pass "F01-S01 AC4: status $s is accepted" "$f"
done

# AC5: slipped rows
f="$(mutant slipped-no-date)"; set_cell "$f" DEP-03 9 "cause: text"
expect_fail "F01-S01 AC5: slipped without slip date" "$f" "DEP-03" "slipped row has no slip date"
expect_absent "F01-S01 AC5: slipped-no-date does not also report a missing cause" "slipped row has no cause"

f="$(mutant slipped-no-cause)"; set_cell "$f" DEP-03 9 "slip-date: 2026-11-17"
expect_fail "F01-S01 AC5: slipped without cause" "$f" "DEP-03" "slipped row has no cause"
expect_absent "F01-S01 AC5: slipped-no-cause does not also report a missing date" "slipped row has no slip date"

f="$(mutant slipped-none)"; set_cell "$f" DEP-03 9 ""
expect_fail "F01-S01 AC5: slipped with empty notes prints both findings" "$f" "slipped row has no slip date" "slipped row has no cause"

f="$(mutant slipped-empty-cause)"; set_cell "$f" DEP-03 9 "slip-date: 2026-11-17; cause:"
expect_fail "F01-S01 AC5: empty cause text counts as missing" "$f" "slipped row has no cause"

f="$(mutant slipped-bad-date)"; set_cell "$f" DEP-03 9 "slip-date: 17/11/2026; cause: text"
expect_fail "F01-S01 AC5: slip date must be YYYY-MM-DD" "$f" "slipped row has no slip date"

f="$(mutant slipped-case)"; set_cell "$f" DEP-03 9 "Slip-Date: 2026-11-17; Cause: text"
expect_fail "F01-S01 AC5: match is case-sensitive" "$f" "slipped row has no slip date"

f="$(mutant not-slipped-no-notes)"; set_cell "$f" DEP-03 7 "open"; set_cell "$f" DEP-03 9 ""
expect_pass "F01-S01 AC6: non-slipped row needs no notes" "$f"

# Table structure
f="$(mutant no-notes-column)"; sed -i 's/ | Notes |$/ |/' "$f"
expect_fail "F01-S01 AC3: missing Notes column" "$f" 'register table lacks column "Notes"'
: >"$WORK/empty.md"
expect_fail "F01-S01 AC2: empty file has no register table" "$WORK/empty.md" "register table"
printf '# Title\n\nno table here\n' >"$WORK/notable.md"
expect_fail "F01-S01 AC2: file without table" "$WORK/notable.md" "register table"

f="$(mutant header-only)"; sed -i '/^| DEP-/d' "$f"
expect_fail "F01-S01 AC2: header-only table reports all IDs missing" "$f" "DEP-01 is missing" "DEP-29 is missing"

f="$(mutant short-row)"; sed -i '/^| DEP-04 /s/ | F1, F3 | |$/ |/' "$f"
expect_fail "F01-S01 AC3: row with fewer cells is malformed" "$f" "malformed"

# AC13: all findings in one run
f="$(mutant two-findings)"; sed -i '/^| DEP-17 /d' "$f"; set_cell "$f" DEP-04 7 "done"
run_check "$f"
n="$(printf '%s\n' "$ERR" | grep -c '^FAIL ')"
if [ "$RC" -eq 1 ] && [ "$n" -ge 2 ]; then pass "F01-S01 AC13: lists every finding, not only the first ($n)"; else fail "F01-S01 AC13: expected >=2 FAIL lines, got $n (rc=$RC)"; fi

# Input robustness
sed 's/$/\r/' "$VALID" >"$WORK/crlf.md"
expect_pass "F01-S01 AC1: CRLF input passes" "$WORK/crlf.md"
printf '%s' "$(cat "$VALID")" >"$WORK/nonl.md"
expect_pass "F01-S01 AC1: last line without newline passes" "$WORK/nonl.md"
f="$(mutant utf8)"; set_cell "$f" DEP-04 3 "Change freeze — CAB rules"
expect_pass "F01-S01 AC1: UTF-8 em dash in a cell passes" "$f"
f="$(mutant spaces)"; set_cell "$f" DEP-04 4 "     Noah Jackson     "
expect_pass "F01-S01 AC1: extra whitespace in cells passes" "$f"

# AC12: usage and errors
run_check "$WORK/does-not-exist.md"
if [ "$RC" -eq 2 ] && [ -n "$ERR" ]; then pass "F01-S01 AC12: nonexistent file exits 2 with a message"; else fail "F01-S01 AC12: rc=$RC err=$ERR"; fi
run_check -h
if [ "$RC" -eq 0 ] && printf '%s%s' "$OUT" "$ERR" | grep -qi 'usage'; then pass "F01-S01 AC12: -h prints usage and exits 0"; else fail "F01-S01 AC12: -h rc=$RC"; fi

# AC15: read-only
before="$(cksum <"$VALID")"
run_check "$VALID"
after="$(cksum <"$VALID")"
[ "$before" = "$after" ] && pass "F01-S01 AC15: input file is unchanged" || fail "F01-S01 AC15: input changed"
mkdir "$WORK/ro" && (cd "$WORK/ro" && bash "$CHECK" "$VALID" >/dev/null 2>&1)
[ -z "$(ls -A "$WORK/ro")" ] && pass "F01-S01 AC15: no file written to the working directory" || fail "F01-S01 AC15: files written"

# AC14: real register, default path, from another working directory
expect_pass "F01-S01 AC14: real register passes when named" "$REAL"
(cd "$WORK" && bash "$CHECK" >"$WORK/out" 2>"$WORK/err"); RC=$?
if [ "$RC" -eq 0 ] && grep -q '^PASS ' "$WORK/out"; then pass "F01-S01 AC14: no arguments from another directory checks the real register"; else fail "F01-S01 AC14: rc=$RC err=$(cat "$WORK/err")"; fi

# AC16: validator planning mode picks up both checkers and tests by pattern
[ -f "$SCRIPTS/check-dependency-register.sh" ] && [ -f "$SCRIPTS/check-raid-log.sh" ] \
  && pass "F01-S01 AC16: both checkers exist where validate.sh looks" || fail "F01-S01 AC16: checker missing under user-stories/scripts"

echo
if [ "$FAILS" -ne 0 ]; then echo "check-dependency-register tests: $FAILS failed"; exit 1; fi
echo "check-dependency-register tests: all passed"
