#!/usr/bin/env bash
# Story: F02-S01 - Appendix B answers checker
#
# Usage: check-appendix-b.sh [FILE]
# With FILE: checks that the table with columns "#", "Question" and "Mitsui answer" has the
# 13 questions numbered 1 to 13, each once, each with an answer that is not empty and not a
# placeholder (TBD, Pending, To confirm, To be confirmed).
# Without FILE: checks the structure only (13 numbered rows, no duplicates) of
# user-stories/evidence/F02/preflight/appendix-b.md and prints how many have an answer, so
# scripts/validate.sh (which passes no arguments) passes while Mitsui answers are open.
# Lists every finding on stderr as "FAIL <file>:<line>: <message>".
# Exit 0 pass, 1 findings, 2 usage or unreadable file.
# Read-only: no network, no clock, no file written.

set -uo pipefail
export LC_ALL=C

usage() {
  echo "Usage: check-appendix-b.sh [FILE]"
  echo "  FILE defaults to user-stories/evidence/F02/preflight/appendix-b.md (structure check only)."
}

check_appendix() {
  local file="$1" mode="$2"
  tr -d '\r' <"$file" | awk -v file="$file" -v mode="$mode" '
    function trim(s) { gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
    function fail(line, msg) { printf "FAIL %s:%d: %s\n", file, line, msg > "/dev/stderr"; nfail++ }
    function unanswered(a,    t) {
      t = tolower(a); gsub(/[ \t.]+$/, "", t); gsub(/^[ \t]+/, "", t)
      return (t == "" || t == "tbd" || t == "pending" || t == "to confirm" || t == "to be confirmed")
    }
    {
      line = $0
      if (!found && line ~ /^\|/) {
        n = split(line, h, "|")
        cn = 0; cq = 0; ca = 0
        for (i = 2; i < n; i++) {
          c = trim(h[i])
          if (c == "#") cn = i
          else if (c == "Question") cq = i
          else if (c == "Mitsui answer") ca = i
        }
        if (cn && cq && ca) { found = 1; headerline = NR; next }
        if (cn || cq) {
          if (!cn) fail(NR, "table header lacks column #")
          if (!cq) fail(NR, "table header lacks column Question")
          if (!ca) fail(NR, "table header lacks column Mitsui answer")
          bad = 1
        }
        next
      }
      if (found && line ~ /^\|/) {
        if (line ~ /^\|[ \t]*[-:]+/) next
        n = split(line, cells, "|")
        num = trim(cells[cn]); ans = trim(cells[ca])
        if (num !~ /^[0-9]+$/) next
        num += 0
        count[num]++
        if (count[num] > 1) dup[num] = 1
        if (!(num in rowline)) rowline[num] = NR
        if (!unanswered(ans)) answered[num] = 1
        next
      }
      if (found && line !~ /^\|/ && line !~ /^[ \t]*$/) { found = 2 }
    }
    END {
      if (!found) {
        if (!bad) fail(1, "no Appendix B table with columns #, Question and Mitsui answer")
        exit 1
      }
      for (q = 1; q <= 13; q++) {
        if (!(q in count)) fail(headerline, "question " q ": missing")
        else if (dup[q]) fail(rowline[q], "question " q ": duplicate")
        else if (mode == "full" && !(q in answered)) fail(rowline[q], "question " q ": no answer")
      }
      na = 0
      for (q = 1; q <= 13; q++) if (q in answered) na++
      if (nfail) exit 1
      if (mode == "full") printf "PASS %s: %d of 13 questions answered\n", file, na
      else printf "PASS %s: structure ok, %d of 13 questions answered\n", file, na
    }
  '
}

main() {
  local file="" mode="full" here root
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  root="$(cd "$here/.." && pwd)"
  case "${1:-}" in
    -h|--help) usage; return 0 ;;
    -*) usage >&2; return 2 ;;
  esac
  if [ "$#" -gt 1 ]; then usage >&2; return 2; fi
  if [ "$#" -eq 1 ]; then
    file="$1"
  else
    file="$root/evidence/F02/preflight/appendix-b.md"
    mode="structure"
  fi
  if [ ! -r "$file" ] || [ -d "$file" ]; then
    echo "cannot read $file" >&2
    return 2
  fi
  check_appendix "$file" "$mode"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
  exit $?
fi
