#!/usr/bin/env bash
# Story: F01-S01 - tests for the RAID log checker
set -uo pipefail
export LC_ALL=C

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS="$(cd "$HERE/.." && pwd)"
STORIES="$(cd "$SCRIPTS/.." && pwd)"
CHECK="$SCRIPTS/check-raid-log.sh"
VALID="$HERE/fixtures/raid-valid.md"
REAL="$STORIES/raid-log.md"

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

expect_pass() {
  local name="$1"; shift
  run_check "$@"
  if [ "$RC" -eq 0 ] && printf '%s' "$OUT" | grep -q '^PASS '; then pass "$name"; else fail "$name (rc=$RC out=$OUT err=$ERR)"; fi
}

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

mutant() {
  cp "$VALID" "$WORK/$1.md"
  echo "$WORK/$1.md"
}

# AC7: valid log
expect_pass "F01-S01 AC7: valid RAID log passes" "$VALID"
grep -q '^## Risks' "$VALID" && grep -q '^## Decisions' "$VALID" && pass "F01-S01 AC7: fixture has the four sections" || fail "F01-S01 AC7: fixture sections"
f="$(mutant empty-risks)"
expect_pass "F01-S01 AC7: Risks and Assumptions may be header-only" "$f"

# AC8: sections and columns
for sec in Risks Assumptions Issues Decisions; do
  f="$(mutant "section-$sec")"; sed -i "/^## $sec\$/d" "$f"
  expect_fail "F01-S01 AC8: missing section $sec" "$f" "section \"## $sec\" is missing"
done
f="$(mutant column-missing)"
awk '/^## Issues/{s=1} /^## Decisions/{s=0} s && /^\| ID \|/{sub(/ Owner \|/,"")} {print}' "$VALID" >"$f"
expect_fail "F01-S01 AC8: Issues table without Owner column" "$f" 'section Issues lacks column "Owner"'
: >"$WORK/empty.md"
expect_fail "F01-S01 AC8: empty file reports every section" "$WORK/empty.md" 'section "## Risks" is missing' 'section "## Decisions" is missing'

# AC9: seeds
f="$(mutant issue-seed-missing)"; sed -i '/gap 5 |$/d' "$f"
expect_fail "F01-S01 AC9: gap 5 seed missing" "$f" "Issues lacks seed for Feature List s5 gap 5"
f="$(mutant issue-seed-gap9)"; sed -i '/gap 9 |$/d' "$f"
expect_fail "F01-S01 AC9: gap 9 seed missing" "$f" "Issues lacks seed for Feature List s5 gap 9"
f="$(mutant decision-seed-missing)"; sed -i '/s7 q7 |$/d' "$f"
expect_fail "F01-S01 AC9: question 7 seed missing" "$f" "Decisions lacks seed for Feature List s7 q7"
f="$(mutant decision-seed-q1)"; sed -i '/s7 q1 |$/d' "$f"
expect_fail "F01-S01 AC9: question 1 seed missing" "$f" "Decisions lacks seed for Feature List s7 q1"

# AC10: row fields
f="$(mutant owner-empty)"; sed -i '/^| I-02 /s/| Mike |/|  |/' "$f"
expect_fail "F01-S01 AC10: empty owner names I-02" "$f" "I-02: owner is empty"
f="$(mutant date-bad)"; sed -i '/^| I-03 /s/2026-11-20/17\/11\/2026/' "$f"
expect_fail "F01-S01 AC10: date 17/11/2026 names I-03" "$f" 'I-03: date "17/11/2026" is not YYYY-MM-DD'
f="$(mutant date-empty)"; sed -i '/^| I-03 /s/| 2026-11-20 |/|  |/' "$f"
expect_fail "F01-S01 AC10: empty date names I-03" "$f" "I-03: date"
f="$(mutant id-prefix-wrong)"; sed -i 's/^| I-04 /| R-04 /' "$f"
expect_fail "F01-S01 AC10: R- row inside Issues" "$f" "R-04 has wrong prefix for section Issues"
f="$(mutant id-duplicate)"; sed -i 's/^| I-04 /| I-03 /' "$f"
expect_fail "F01-S01 AC10: duplicate I-03" "$f" "I-03 is duplicated"
f="$(mutant risk-row-ok)"
awk '{print} /^## Risks/{r=1} r && /^\|---/{print "| R-01 | Example risk | Mike | 2026-11-20 | open | test |"; r=0}' "$VALID" >"$f"
expect_pass "F01-S01 AC10: a well-formed R- row in Risks passes" "$f"
f="$(mutant date-risk-bad)"
awk '{print} /^## Risks/{r=1} r && /^\|---/{print "| R-01 | Example risk | Mike | tomorrow | open | test |"; r=0}' "$VALID" >"$f"
expect_fail "F01-S01 AC10: bad date in Risks names R-01" "$f" 'R-01: date "tomorrow" is not YYYY-MM-DD'

# AC11: seeded decisions must be open
f="$(mutant decision-not-open)"; sed -i '/^| D-03 /s/| open |/| closed |/' "$f"
expect_fail "F01-S01 AC11: D-03 closed is rejected" "$f" "D-03: seeded question must have status open"

# AC13: all findings listed
f="$(mutant two-findings)"; sed -i '/gap 5 |$/d' "$f"; sed -i '/^| D-03 /s/| open |/| closed |/' "$f"
run_check "$f"
n="$(printf '%s\n' "$ERR" | grep -c '^FAIL ')"
if [ "$RC" -eq 1 ] && [ "$n" -ge 2 ]; then pass "F01-S01 AC13: lists every finding ($n)"; else fail "F01-S01 AC13: rc=$RC n=$n"; fi
if printf '%s' "$ERR" | grep -qE '^FAIL .*:[0-9]*: '; then pass "F01-S01 AC13: finding uses FAIL <file>:<line>: format"; else fail "F01-S01 AC13: format (err=$ERR)"; fi

# Robustness
sed 's/$/\r/' "$VALID" >"$WORK/crlf.md"
expect_pass "F01-S01 AC7: CRLF input passes" "$WORK/crlf.md"
printf '%s' "$(cat "$VALID")" >"$WORK/nonl.md"
expect_pass "F01-S01 AC7: last line without newline passes" "$WORK/nonl.md"
f="$(mutant utf8)"; sed -i '/^| I-01 /s/Gap 1/Gap 1 — dash/' "$f"
expect_pass "F01-S01 AC7: UTF-8 em dash in a cell passes" "$f"

# AC12
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

# AC14: real log, default path, other working directory
expect_pass "F01-S01 AC14: real RAID log passes when named" "$REAL"
(cd "$WORK" && bash "$CHECK" >"$WORK/out" 2>"$WORK/err"); RC=$?
if [ "$RC" -eq 0 ] && grep -q '^PASS ' "$WORK/out"; then pass "F01-S01 AC14: no arguments from another directory checks the real RAID log"; else fail "F01-S01 AC14: rc=$RC err=$(cat "$WORK/err")"; fi

# AC16
[ -f "$SCRIPTS/check-raid-log.sh" ] && pass "F01-S01 AC16: checker exists where validate.sh looks" || fail "F01-S01 AC16: checker missing"

echo
if [ "$FAILS" -ne 0 ]; then echo "check-raid-log tests: $FAILS failed"; exit 1; fi
echo "check-raid-log tests: all passed"
