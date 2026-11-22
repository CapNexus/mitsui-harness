#!/usr/bin/env bash
# Story: F01-S06 - overdue dependency checker
#
# Usage: check-overdue.sh [--today YYYY-MM-DD] [FILE]
# Reads the dependency register (default: user-stories/dependencies/README.md) and converts
# every needed-by value to a date: "Nov 16" (Nov and Dec are 2026, Jan to Oct 2027),
# "Week N" (Friday of week N; week 1 ends Fri 2026-11-20) and "Weeks A to B" (Friday of
# week B). With --today, lists on stdout every row due on or before that date whose status
# is not resolved, as "OVERDUE <file>:<line>: <id>: needed by <text> (<date>), status <s>,
# days late <n>". Without --today no clock is read; the check only confirms every date
# parses. Findings go to stderr as "FAIL <file>:<line>: <message>".
# Exit 0 pass, 1 overdue rows or findings, 2 usage error, bad --today or unreadable file.
# Read-only: no network, no system clock, no file written.

set -uo pipefail
export LC_ALL=C

usage() {
  echo "Usage: check-overdue.sh [--today YYYY-MM-DD] [FILE]"
  echo "  FILE defaults to user-stories/dependencies/README.md of this repository."
  echo "  Without --today, only checks that every needed-by value is a date."
}

# Shared awk date functions: day numbers from and to civil dates (proleptic Gregorian).
DATE_AWK='
  function daynum(y, m, d,   era, yoe, mp, doy, doe) {
    y -= (m <= 2)
    era = int((y >= 0 ? y : y - 399) / 400)
    yoe = y - era * 400
    mp = (m + 9) % 12
    doy = int((153 * mp + 2) / 5) + d - 1
    doe = yoe * 365 + int(yoe / 4) - int(yoe / 100) + doy
    return era * 146097 + doe
  }
  function civil(z,   era, doe, yoe, y, doy, mp, d, m) {
    era = int((z >= 0 ? z : z - 146096) / 146097)
    doe = z - era * 146097
    yoe = int((doe - int(doe / 1460) + int(doe / 36524) - int(doe / 146096)) / 365)
    y = yoe + era * 400
    doy = doe - (365 * yoe + int(yoe / 4) - int(yoe / 100))
    mp = int((5 * doy + 2) / 153)
    d = doy - int((153 * mp + 2) / 5) + 1
    m = (mp < 10) ? mp + 3 : mp - 9
    y += (m <= 2)
    return sprintf("%04d-%02d-%02d", y, m, d)
  }
  # iso_daynum("YYYY-MM-DD"): day number, or -1 when not a real calendar date
  function iso_daynum(s,   p, z) {
    if (s !~ /^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]$/) return -1
    split(s, p, "-")
    if (p[2] + 0 < 1 || p[2] + 0 > 12 || p[3] + 0 < 1) return -1
    z = daynum(p[1] + 0, p[2] + 0, p[3] + 0)
    return (civil(z) == s) ? z : -1
  }
'

# valid_today DATE: exit 0 when DATE is a real YYYY-MM-DD date
valid_today() {
  awk -v s="$1" "$DATE_AWK"'BEGIN { exit (iso_daynum(s) < 0) ? 1 : 0 }'
}

# check_overdue FILE [TODAY]: prints FAIL and OVERDUE lines, then "SUMMARY <fails> <overdue> <parsed>"
check_overdue() {
  tr -d '\r' <"$1" | awk -v file="$1" -v today="${2:-}" "$DATE_AWK"'
    function trim(s) { gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
    function fail(line, msg) { printf "FAIL %s:%d: %s\n", file, line, msg; nfail++ }
    # due_daynum(text): day number of the needed-by text, or -1
    function due_daynum(t,   p, mon, y, z, n) {
      if (t ~ /^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [0-9][0-9]?$/) {
        split(t, p, " ")
        mon = index("JanFebMarAprMayJunJulAugSepOctNovDec", p[1])
        mon = (mon + 2) / 3
        y = (mon >= 11) ? 2026 : 2027
        z = daynum(y, mon, p[2] + 0)
        return (civil(z) == sprintf("%04d-%02d-%02d", y, mon, p[2] + 0)) ? z : -1
      }
      if (t ~ /^Weeks [0-9]+ to [0-9]+$/) {
        split(t, p, " ")
        if (p[2] + 0 > p[4] + 0) return -1
        n = p[4] + 0
      }
      else if (t ~ /^Week [0-9]+ to /) return -1
      else if (t ~ /^Week [0-9]+([ \t].*)?$/) { split(t, p, " "); n = p[2] + 0 }
      else return -1
      if (n < 1) return -1
      return week1_end + 7 * (n - 1)
    }
    BEGIN {
      nfail = 0; nover = 0; nparsed = 0; found = 0; in_table = 0
      week1_end = daynum(2026, 11, 20)
      if (today != "") todayn = iso_daynum(today)
    }
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
            found = 1; in_table = 1; hdrline = NR
            for (i = 2; i < n; i++) {
              c = trim(h[i])
              if (c == "ID") col["id"] = i
              else if (c == "Needed by") col["needed"] = i
              else if (c == "Status") col["status"] = i
            }
            if (!("needed" in col)) { fail(NR, "register table lacks column \"Needed by\""); badcols = 1 }
          }
        }
        next
      }
      if (!in_table) next
      if (line !~ /^\|/) { in_table = 0; next }
      if (line ~ /^\|[ \t]*:?-+/ || badcols) next
      n = split(line, f, "|")
      id = trim(f[col["id"]])
      if (id == "") next
      if (id !~ /^DEP-[0-9]+$/) { fail(NR, "unexpected ID " id); next }
      needed = trim(f[col["needed"]]); status = trim(f[col["status"]])
      due = due_daynum(needed)
      if (due < 0) { fail(NR, id ": needed-by \"" needed "\" is not a date"); next }
      nparsed++
      if (today != "" && due <= todayn && status != "resolved") {
        printf "OVERDUE %s:%d: %s: needed by %s (%s), status %s, days late %d\n", file, NR, id, needed, civil(due), status, todayn - due
        nover++
      }
    }
    END {
      if (!found) fail(1, "register table not found (no table with ID and Status columns)")
      printf "SUMMARY %d %d %d\n", nfail, nover, nparsed
    }'
}

main() {
  local file="" today="" have_file=0 have_today=0
  while [ "$#" -gt 0 ]; do
    case "$1" in
      -h | --help) usage; return 0 ;;
      --today)
        if [ "$#" -lt 2 ]; then echo "error: --today needs a date (YYYY-MM-DD)" >&2; usage >&2; return 2; fi
        today="$2"; have_today=1; shift 2 ;;
      *)
        if [ "$have_file" -eq 1 ]; then usage >&2; return 2; fi
        file="$1"; have_file=1; shift ;;
    esac
  done
  if [ "$have_today" -eq 1 ] && ! valid_today "$today"; then
    echo "error: --today \"$today\" is not a real YYYY-MM-DD date" >&2
    return 2
  fi
  if [ "$have_file" -eq 0 ]; then
    file="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/user-stories/dependencies/README.md"
    [ -f "$file" ] || file="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/dependencies/README.md"
  fi
  if [ ! -f "$file" ] || [ ! -r "$file" ]; then
    echo "error: cannot read $file" >&2
    usage >&2
    return 2
  fi

  local result nfail nover nparsed
  result="$(check_overdue "$file" "$today")"
  read -r nfail nover nparsed <<<"$(printf '%s\n' "$result" | sed -n 's/^SUMMARY //p')"
  if [ -z "${nparsed:-}" ]; then
    echo "error: internal failure parsing $file" >&2
    return 2
  fi
  printf '%s\n' "$result" | grep '^FAIL ' >&2
  printf '%s\n' "$result" | grep '^OVERDUE '
  if [ "${nfail:-1}" -ne 0 ] || [ "${nover:-1}" -ne 0 ]; then return 1; fi
  if [ -n "$today" ]; then
    echo "PASS $file: no dependency overdue on $today"
  else
    echo "PASS $file: $nparsed needed-by dates parse"
  fi
  return 0
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
  exit $?
fi
