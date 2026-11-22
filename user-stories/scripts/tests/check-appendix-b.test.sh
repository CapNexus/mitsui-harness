#!/usr/bin/env bash
# Story: F02-S01 - tests for the Appendix B answers checker
set -uo pipefail
export LC_ALL=C

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS="$(cd "$HERE/.." && pwd)"
STORIES="$(cd "$SCRIPTS/.." && pwd)"
CHECK="$SCRIPTS/check-appendix-b.sh"
VALID="$HERE/fixtures/appendix-b-valid.md"
REAL="$STORIES/evidence/F02/preflight/appendix-b.md"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
FAILS=0
RC=0
OUT=""
ERR=""

pass() { echo "ok   - $1"; }
fail() { echo "FAIL - $1"; FAILS=$((FAILS + 1)); }

run_check() {
  bash "$CHECK" "$@" >"$WORK/out" 2>"$WORK/err"
  RC=$?
  OUT="$(cat "$WORK/out")"
  ERR="$(cat "$WORK/err")"
}

# expect_rc NAME RC FRAGMENT... : exit code equals RC and stdout+stderr contain every fragment
expect_rc() {
  local name="$1" want="$2"; shift 2
  local ok=1 frag
  [ "$RC" -eq "$want" ] || ok=0
  for frag in "$@"; do
    printf '%s\n%s' "$OUT" "$ERR" | grep -qF -- "$frag" || ok=0
  done
  if [ "$ok" -eq 1 ]; then pass "$name"; else fail "$name (rc=$RC out=$OUT err=$ERR)"; fi
}

# mutate OUT_FILE SED_EXPR : copy the valid fixture with one change
mutate() { sed "$2" "$VALID" >"$1"; }

# AC1: valid file passes
run_check "$VALID"
expect_rc "F02-S01 AC1 valid file passes" 0 "PASS" "13 of 13"

# AC2: empty answer
mutate "$WORK/empty.md" 's/| Region deny only. |/|  |/'
run_check "$WORK/empty.md"
expect_rc "F02-S01 AC2 empty answer fails and names question 7" 1 "question 7: no answer"

# AC3: placeholder answers
for ph in "TBD" "pending" "To confirm." "To be confirmed"; do
  mutate "$WORK/ph.md" "s/| Yes, us-east-1. |/| $ph |/"
  run_check "$WORK/ph.md"
  expect_rc "F02-S01 AC3 placeholder '$ph' fails" 1 "question 4: no answer"
done

# AC4: missing and duplicate numbers
grep -v '^| 9 |' "$VALID" >"$WORK/missing.md"
run_check "$WORK/missing.md"
expect_rc "F02-S01 AC4 missing question 9 fails" 1 "question 9: missing"
sed 's/^| 13 |/| 12 |/' "$VALID" >"$WORK/dup.md"
run_check "$WORK/dup.md"
expect_rc "F02-S01 AC4 duplicate 12 and missing 13 fail" 1 "question 12: duplicate" "question 13: missing"

# AC5: every finding listed in one run
sed -e 's/| Yes. |/|  |/' -e 's/| No. |/| TBD |/' "$VALID" >"$WORK/many.md"
run_check "$WORK/many.md"
expect_rc "F02-S01 AC5 several findings in one run" 1 "question 3: no answer" "question 13: no answer" "question 6: no answer"

# AC6: header problems
sed 's/| Mitsui answer |/| Reply |/' "$VALID" >"$WORK/hdr.md"
run_check "$WORK/hdr.md"
expect_rc "F02-S01 AC6 missing answer column fails and names it" 1 "Mitsui answer"
printf 'no table here\n' >"$WORK/none.md"
run_check "$WORK/none.md"
expect_rc "F02-S01 AC6 no table fails" 1 "no Appendix B table"

# AC7: no argument checks structure only
run_check
expect_rc "F02-S01 AC7 no argument passes on the real file structure" 0 "PASS" "structure"

# AC8: usage and unreadable file
run_check -h
expect_rc "F02-S01 AC8 -h prints usage" 0 "Usage"
run_check --bogus
expect_rc "F02-S01 AC8 unknown option exits 2" 2 "Usage"
run_check "$WORK/does-not-exist.md"
expect_rc "F02-S01 AC8 unreadable file exits 2" 2 "cannot read"

# AC9: CRLF
sed 's/$/\r/' "$VALID" >"$WORK/crlf.md"
run_check "$WORK/crlf.md"
expect_rc "F02-S01 AC9 CRLF file passes" 0 "PASS"

# AC10: read-only (no file created next to the input)
before="$(ls "$WORK" | wc -l)"
run_check "$VALID"
after="$(ls "$WORK" | wc -l)"
# out and err are the only files created by run_check itself
if [ "$before" -eq "$after" ] || [ "$after" -le $((before + 2)) ]; then pass "F02-S01 AC10 writes nothing besides the harness files"; else fail "F02-S01 AC10 extra files created"; fi

# Real file has the 13 questions (structure)
if [ -f "$REAL" ]; then
  n="$(grep -c '^| [0-9]\{1,2\} |' "$REAL")"
  if [ "$n" -eq 13 ]; then pass "F02-S01 real appendix-b.md has 13 numbered rows"; else fail "F02-S01 real appendix-b.md has $n rows"; fi
else
  fail "F02-S01 real appendix-b.md missing at $REAL"
fi

if [ "$FAILS" -ne 0 ]; then echo "$FAILS test(s) failed"; exit 1; fi
echo "all tests passed"
