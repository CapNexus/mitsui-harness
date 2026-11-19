#!/usr/bin/env bash
# Story: F01-S01 - dependency register checker
#
# Usage: check-dependency-register.sh [FILE]
# Checks that FILE (default: user-stories/dependencies/README.md) lists DEP-01 to DEP-29
# once each, with owner, needed-by, type and status, and that every slipped row carries
# a slip date and a cause in Notes. Lists every finding on stderr as
# "FAIL <file>:<line>: <message>". Exit 0 pass, 1 findings, 2 usage or unreadable file.
# Read-only: no network, no clock, no file written.

set -uo pipefail
export LC_ALL=C

usage() {
  echo "Usage: check-dependency-register.sh [FILE]"
  echo "  FILE defaults to user-stories/dependencies/README.md of this repository."
}

# Print findings (FAIL ...) on stdout and a final line "SUMMARY <n>" for the caller.
check_register() {
  tr -d '\r' <"$1" | awk -v file="$1" '
    function trim(s) { gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
    function fail(line, msg) { printf "FAIL %s:%d: %s\n", file, line, msg; nfail++ }
    BEGIN { nfail = 0; in_table = 0; found = 0 }
    {
      line = $0
      if (!found) {
        if (line ~ /^\|/) {
          n = split(line, h, "|")
          hasid = 0; hasstatus = 0
          for (i = 2; i < n; i++) {
            c = trim(h[i])
            if (c == "ID") hasid = 1
            if (c == "Status") hasstatus = 1
          }
          if (hasid && hasstatus) {
            found = 1; in_table = 1; hdrline = NR; ncols = n - 2
            for (i = 2; i < n; i++) {
              c = trim(h[i])
              if (c == "ID") col["id"] = i - 1
              else if (c ~ /^Owner/) col["owner"] = i - 1
              else if (c == "Needed by") col["needed"] = i - 1
              else if (c == "Type") col["type"] = i - 1
              else if (c == "Status") col["status"] = i - 1
              else if (c == "Notes") col["notes"] = i - 1
            }
            split("id owner needed type status notes", keys, " ")
            names["id"] = "ID"; names["owner"] = "Owner"; names["needed"] = "Needed by"
            names["type"] = "Type"; names["status"] = "Status"; names["notes"] = "Notes"
            for (k = 1; k <= 6; k++)
              if (!(keys[k] in col)) {
                fail(hdrline, "register table lacks column \"" names[keys[k]] "\"")
                badcols = 1
              }
          }
        }
        next
      }
      if (!in_table) next
      if (line !~ /^\|/) { in_table = 0; next }
      if (line ~ /^\|[ \t]*:?-+/) next
      n = split(line, f, "|")
      cells = n - 2
      id = trim(f[2])
      if (id == "") next
      if (id !~ /^DEP-(0[1-9]|1[0-9]|2[0-9])$/) {
        fail(NR, "unexpected ID " id)
        next
      }
      if (id in seen) { seen[id] = seen[id] ", " NR; dup[id] = 1; next }
      seen[id] = NR
      if (badcols) next
      if (cells != ncols) {
        fail(NR, id ": malformed row (" cells " cells, expected " ncols ")")
        next
      }
      owner = trim(f[col["owner"] + 1]); needed = trim(f[col["needed"] + 1])
      type = trim(f[col["type"] + 1]); status = trim(f[col["status"] + 1])
      notes = trim(f[col["notes"] + 1])
      if (owner == "") fail(NR, id ": owner is empty")
      if (needed == "") fail(NR, id ": needed-by is empty")
      if (type == "") fail(NR, id ": type is empty")
      else if (type !~ /^[A-E]([+][A-E])*$/) fail(NR, id ": type \"" type "\" is not A to E")
      if (status == "") fail(NR, id ": status is empty")
      else if (status !~ /^(open|requested|in-progress|resolved|slipped)$/)
        fail(NR, id ": status \"" status "\" is not allowed")
      else if (status == "slipped") {
        if (notes !~ /slip-date: [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]/)
          fail(NR, id ": slipped row has no slip date")
        if (notes !~ /cause:[ ]*[^ ]/) fail(NR, id ": slipped row has no cause")
      }
    }
    END {
      if (!found) { fail(1, "register table not found (no table with ID and Status columns)") }
      else {
        for (d in dup) fail(hdrline, d " appears more than once (lines " seen[d] ")")
        for (i = 1; i <= 29; i++) {
          id = sprintf("DEP-%02d", i)
          if (!(id in seen)) fail(hdrline, id " is missing")
        }
      }
      printf "SUMMARY %d\n", nfail
    }'
}

main() {
  local file
  case "${1:-}" in
    -h | --help) usage; return 0 ;;
  esac
  if [ "$#" -gt 1 ]; then usage >&2; return 2; fi
  if [ "$#" -eq 1 ]; then
    file="$1"
  else
    file="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/user-stories/dependencies/README.md"
    [ -f "$file" ] || file="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/dependencies/README.md"
  fi
  if [ ! -f "$file" ] || [ ! -r "$file" ]; then
    echo "error: cannot read $file" >&2
    usage >&2
    return 2
  fi

  local result summary
  result="$(check_register "$file")"
  summary="$(printf '%s\n' "$result" | sed -n 's/^SUMMARY //p')"
  printf '%s\n' "$result" | grep '^FAIL ' >&2
  if [ "${summary:-1}" -eq 0 ]; then
    echo "PASS $file: DEP-01 to DEP-29 present with owner, needed-by, type and status"
    return 0
  fi
  return 1
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
  exit $?
fi
