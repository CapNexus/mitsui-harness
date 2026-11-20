#!/usr/bin/env bash
# Story: F01-S01 - RAID log checker
#
# Usage: check-raid-log.sh [FILE]
# Checks that FILE (default: user-stories/raid-log.md) has the sections Risks, Assumptions,
# Issues and Decisions, each with a table ID | Item | Owner | Date | Status | Source, that
# every row has an owner, an ISO date, a matching ID prefix and a unique ID, and that the
# Issues table is seeded with Feature List Section 5 gaps 1 to 9 and the Decisions table
# with Section 7 questions 1 to 7 (status open). Lists every finding on stderr as
# "FAIL <file>:<line>: <message>". Exit 0 pass, 1 findings, 2 usage or unreadable file.
# Read-only: no network, no clock, no file written.

set -uo pipefail
export LC_ALL=C

usage() {
  echo "Usage: check-raid-log.sh [FILE]"
  echo "  FILE defaults to user-stories/raid-log.md of this repository."
}

check_raid() {
  tr -d '\r' <"$1" | awk -v file="$1" '
    function trim(s) { gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
    function fail(line, msg) { printf "FAIL %s:%d: %s\n", file, line, msg; nfail++ }
    function seeded(sec, label, n,    pat) {
      pat = label n "([^0-9]|$)"
      for (r = 1; r <= nrows[sec]; r++)
        if (rsource[sec, r] ~ pat) return r
      return 0
    }
    BEGIN {
      nfail = 0; cur = ""
      nsec = split("Risks Assumptions Issues Decisions", secs, " ")
      prefix["Risks"] = "R-"; prefix["Assumptions"] = "A-"
      prefix["Issues"] = "I-"; prefix["Decisions"] = "D-"
      ncn = split("ID Item Owner Date Status Source", need, " ")
    }
    {
      line = $0
      if (line ~ /^##[ \t]/) {
        name = line; sub(/^##[ \t]+/, "", name); name = trim(name)
        if (line == "## " name && (name in prefix)) { cur = name; present[name] = NR }
        else cur = ""
        next
      }
      if (cur == "" || line !~ /^\|/) next
      if (line ~ /^\|[ \t]*:?-+/) next
      n = split(line, f, "|")
      if (!(cur in hdr)) {
        hdr[cur] = NR; ncols[cur] = n - 2
        for (i = 2; i < n; i++) pos[cur, trim(f[i])] = i - 1
        for (k = 1; k <= ncn; k++)
          if (!((cur, need[k]) in pos)) {
            fail(NR, "section " cur " lacks column \"" need[k] "\"")
            badcols[cur] = 1
          }
        next
      }
      if (trim(f[2]) == "ID") next          # repeated header row
      if (badcols[cur]) next
      id = trim(f[2])
      if (n - 2 != ncols[cur]) {
        fail(NR, (id == "" ? "row" : id) ": malformed row (" n - 2 " cells, expected " ncols[cur] ")")
        next
      }
      owner = trim(f[pos[cur, "Owner"] + 1]); date = trim(f[pos[cur, "Date"] + 1])
      status = trim(f[pos[cur, "Status"] + 1]); source = trim(f[pos[cur, "Source"] + 1])
      if (index(id, prefix[cur]) != 1) fail(NR, id " has wrong prefix for section " cur)
      if (id in seen) fail(NR, id " is duplicated (first at line " seen[id] ")")
      else seen[id] = NR
      if (owner == "") fail(NR, id ": owner is empty")
      if (date !~ /^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]$/)
        fail(NR, id ": date \"" date "\" is not YYYY-MM-DD")
      nrows[cur]++
      rsource[cur, nrows[cur]] = source
      rstatus[cur, nrows[cur]] = status
      rid[cur, nrows[cur]] = id
      rline[cur, nrows[cur]] = NR
    }
    END {
      for (s = 1; s <= nsec; s++) {
        sec = secs[s]
        if (!(sec in present)) fail(1, "section \"## " sec "\" is missing")
        else if (!(sec in hdr)) {
          for (k = 1; k <= ncn; k++) fail(present[sec], "section " sec " lacks column \"" need[k] "\"")
        }
      }
      if (("Issues" in hdr) && !badcols["Issues"])
        for (g = 1; g <= 9; g++)
          if (!seeded("Issues", "Feature List s5 gap ", g))
            fail(hdr["Issues"], "Issues lacks seed for Feature List s5 gap " g)
      if (("Decisions" in hdr) && !badcols["Decisions"])
        for (q = 1; q <= 7; q++) {
          r = seeded("Decisions", "Feature List s7 q", q)
          if (!r) fail(hdr["Decisions"], "Decisions lacks seed for Feature List s7 q" q)
          else if (rstatus["Decisions", r] != "open")
            fail(rline["Decisions", r], rid["Decisions", r] ": seeded question must have status open")
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
    file="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/raid-log.md"
  fi
  if [ ! -f "$file" ] || [ ! -r "$file" ]; then
    echo "error: cannot read $file" >&2
    usage >&2
    return 2
  fi

  local result summary
  result="$(check_raid "$file")"
  summary="$(printf '%s\n' "$result" | sed -n 's/^SUMMARY //p')"
  printf '%s\n' "$result" | grep '^FAIL ' >&2
  if [ "${summary:-1}" -eq 0 ]; then
    echo "PASS $file: four RAID sections, seeds for gaps 1-9 and questions 1-7"
    return 0
  fi
  return 1
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
  exit $?
fi
