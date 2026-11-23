#!/usr/bin/env bash
# Canonical validator: the harness's independent verification gate.
#
# The driver re-runs this AFTER the build step and FAILS the run on a non-zero exit.
# The agent's claim of "done" is never trusted. Runs six stages (protected, format, lint,
# typecheck, test, build) and exits non-zero if ANY of them fails. All stages run so
# the operator sees every problem in one pass.
#
# Note: "typecheck" runs `npm run build` (tsc --noEmit) and "build" runs
# `npm run synth` (cdk synth). Neither deploys anything.
#
# The "protected" stage fails when the gate's own definition differs from the base ref:
# this script, the Jest, ESLint and Prettier configs, tsconfig*.json, and the "scripts"
# and "jest" (coverageThreshold) sections of package.json. This includes new, deleted and
# untracked files. Environment, set by the driver and never by the agent:
#   VALIDATE_BASE_REF               required; ref to compare against (e.g. origin/main)
#   VALIDATE_ALLOW_PROTECTED_EDITS  set to 1 only for a harness-* classification after a
#                                   human unlock; skips the protected stage
#   VALIDATE_SCAFFOLD               set to 1 only for the one-time project scaffold
#                                   (tsconfig, jest.config, eslint and prettier configs,
#                                   bin/app.ts, an initial test) after a human unlock.
#                                   The protected stage then ignores protected files that
#                                   are ADDED (new or untracked) but still fails on any
#                                   protected file that exists at the base ref and is
#                                   modified, deleted or renamed. All other stages still
#                                   run in full, so the scaffold must pass format, lint,
#                                   typecheck, test (including the coverage threshold) and
#                                   synth. Once the scaffold is merged, the driver must
#                                   stop setting this variable.
# The driver should run this script from the base ref copy (or from a location the agent
# cannot write to), so a rewritten validator cannot remove its own check.
#
# mitsui-harness additions (harness/run_story.py sets these, never the agent):
#   HARNESS_TARGET_REPO   the repo the story changes: a submodule (CDK/TypeScript stages) or
#                         this parent repo (planning stages). Default: this parent repo.
#   HARNESS_FREEZE_OVERRIDE=1  human override of the freeze stage (fixes for failed tests).
# Extra stages: `install` (npm ci: package-lock.json must be committed), `freeze` (load
# pipeline freeze from 2026-12-14, code freeze from 2026-12-18; task-list week 5), and
# `build` runs cdk synth with every AWS credential removed: synth is local, for unit tests.
# This script lives outside the submodules; .kiro hooks guard it (harness/answer-key.txt).

set -uo pipefail

# Resolve this script's path before changing directory.
self_abs="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
harness_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "${HARNESS_TARGET_REPO:-$harness_root}" || { echo "cannot enter HARNESS_TARGET_REPO" >&2; exit 1; }
root_abs="$(pwd)"
mode=code
[ "$root_abs" = "$harness_root" ] && mode=planning
self_rel="${self_abs#"$root_abs"/}"

fail=0

PROTECTED_PATHSPECS=(
  ':(glob)**/jest.config.*'
  ':(glob)**/.eslintrc*'
  ':(glob)**/eslint.config.*'
  ':(glob)**/.eslintignore'
  ':(glob)**/.prettierrc*'
  ':(glob)**/prettier.config.*'
  ':(glob)**/.prettierignore'
  ':(glob)**/tsconfig*.json'
)
# The validator itself is protected only where it lives (the parent repo).
[ "$mode" = planning ] && PROTECTED_PATHSPECS+=("$self_rel")

check_protected() {
  if [ "${VALIDATE_ALLOW_PROTECTED_EDITS:-0}" = "1" ]; then
    echo "  protected-file check skipped: human unlock for a harness-* change"
    return 0
  fi

  local ref="${VALIDATE_BASE_REF:-}"
  if [ -z "$ref" ]; then
    echo "  VALIDATE_BASE_REF is not set; cannot verify protected files" >&2
    return 1
  fi

  local base
  if ! base="$(git merge-base HEAD "$ref" 2>/dev/null)"; then
    echo "  cannot resolve a merge base between HEAD and '${ref}'" >&2
    return 1
  fi

  local scaffold=0
  if [ "${VALIDATE_SCAFFOLD:-0}" = "1" ]; then
    scaffold=1
    echo "  scaffold mode (human unlock): added protected files are allowed; existing ones stay protected"
  fi

  local rc=0 changed
  if [ "$scaffold" = "1" ]; then
    # Exclude added files (--diff-filter=a); disable rename detection so a protected
    # file renamed or moved away from the base still shows up as deleted.
    changed="$(
      git diff --no-renames --diff-filter=a --name-only "$base" -- "${PROTECTED_PATHSPECS[@]}" | sort -u
    )"
  else
    changed="$(
      {
        git diff --name-only "$base" -- "${PROTECTED_PATHSPECS[@]}"
        git ls-files --others --exclude-standard -- "${PROTECTED_PATHSPECS[@]}"
      } | sort -u
    )"
  fi
  if [ -n "$changed" ]; then
    echo "  protected files differ from ${ref}:" >&2
    echo "$changed" | sed 's/^/    /' >&2
    rc=1
  fi

  # package.json: only the sections the gates depend on are protected.
  [ -f package.json ] || [ "$mode" = code ] || return "$rc"
  # First story on an empty repo: the base has no package.json, so the scaffold creates it
  # and its sections cannot "change". Once the base has one, the sections stay protected.
  if [ "$scaffold" = "1" ] && ! git cat-file -e "${base}:package.json" 2>/dev/null; then
    echo "  scaffold mode: package.json is new (absent at the base ref); sections not compared"
    return "$rc"
  fi
  local base_pkg
  base_pkg="$(git show "${base}:package.json" 2>/dev/null || echo '{}')"
  if ! BASE_PKG="$base_pkg" node -e '
    const fs = require("fs");
    const b = JSON.parse(process.env.BASE_PKG);
    const c = JSON.parse(fs.readFileSync("package.json", "utf8"));
    let bad = false;
    for (const k of ["scripts", "jest"]) {
      if (JSON.stringify(b[k] ?? null) !== JSON.stringify(c[k] ?? null)) {
        console.error("  package.json section changed: " + k);
        bad = true;
      }
    }
    process.exit(bad ? 1 : 0);
  '; then
    rc=1
  fi

  return "$rc"
}

run_stage() {
  local name="$1"
  shift
  echo "== validate: ${name} =="
  if "$@"; then
    echo "  ${name} PASS"
  else
    fail=1
    echo "  ${name} FAILED"
  fi
}

check_freeze() {
  if [ "${HARNESS_FREEZE_OVERRIDE:-0}" = "1" ]; then
    echo "  freeze check skipped: human override"; return 0
  fi
  [ "$mode" = code ] || return 0
  local today base changed
  today="$(date +%F)"
  base="$(git merge-base HEAD "${VALIDATE_BASE_REF:-HEAD}" 2>/dev/null || echo HEAD)"
  changed="$({ git diff --name-only "$base"; git ls-files --others --exclude-standard; } | sort -u)"
  [ -n "$changed" ] || return 0
  if [[ ! "$today" < "2026-12-18" ]]; then
    echo "  code freeze since 2026-12-18: only fixes for failed tests, with HARNESS_FREEZE_OVERRIDE=1" >&2
    return 1
  fi
  if [[ ! "$today" < "2026-12-14" ]] && echo "$changed" | grep -Eiq '(glue|dms|load|ingest|replicat)'; then
    echo "  load pipeline freeze since 2026-12-14 (unattended-load window); changed:" >&2
    echo "$changed" | grep -Ei '(glue|dms|load|ingest|replicat)' | sed 's/^/    /' >&2
    return 1
  fi
}

synth_offline() {
  # Local synth for unit tests: no credentials, no context lookups, no metadata endpoint.
  env -u AWS_PROFILE -u AWS_DEFAULT_PROFILE -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY       -u AWS_SESSION_TOKEN AWS_EC2_METADATA_DISABLED=true AWS_CONFIG_FILE=/dev/null       AWS_SHARED_CREDENTIALS_FILE=/dev/null npm run synth
}

planning_scripts() {   # $1 = checks | tests
  local dir=user-stories/scripts pattern=check-*.sh n=0 f
  [ "$1" = tests ] && { dir=user-stories/scripts/tests; pattern=*.sh; }
  for f in "$dir"/$pattern; do
    [ -f "$f" ] || continue
    n=$((n + 1))
    bash "$f" || { echo "  $f FAILED" >&2; return 1; }
  done
  [ "$n" -gt 0 ] || echo "  no $1 yet under $dir"
}

run_stage protected check_protected
run_stage freeze    check_freeze
if [ "$mode" = planning ]; then
  run_stage checks  planning_scripts checks
  run_stage tests   planning_scripts tests
else
  run_stage install   npm ci --no-audit --no-fund
  run_stage format    npm run format:check
  run_stage lint      npm run lint
  run_stage typecheck npm run build
  run_stage test      npm test
  run_stage build     synth_offline
fi

echo
if [ "$fail" -ne 0 ]; then echo "validate: FAIL"; exit 1; fi
echo "validate: PASS"; exit 0
