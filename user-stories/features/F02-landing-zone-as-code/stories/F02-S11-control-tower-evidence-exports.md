---
id: F02-S11
feature: F2
title: Export Control Tower drift and compliance evidence
tier: integrate
executor: mixed
owner: Soma
repo: planning
status: blocked
sow: D2
due: 2026-12-23
blocked_by: [DEP-02]
depends_on_stories: [F02-S06, F02-S07, F02-S10]
params: []
human_gates: [Soma reviews each export before it goes into the evidence pack]
---

## Story

As Soma (solution architect), I want a script that exports the landing zone, control and account enrollment status, so that the acceptance pack shows no drift and compliant controls in both Week 5 and Week 6.

## Context

F2 criteria 1 and 7. Task list Thu Dec 17 (Week 5 check) and Wed Dec 23 (Week 6 export). The script runs through Identity Center access, because the cross-account role is gone after Nov 20.

## Acceptance criteria

1. Given the landing zone, when the export script runs, then it writes landing zone status and drift, each enabled control with its compliance status, and the POC account enrollment status to one dated file.
   - verify: `scripts/export-control-tower-status.sh` exits 0 and the output file has all three sections. Script is created by this story.
2. Given the Week 5 check on Dec 17, when the export runs, then drift is `IN_SYNC`, all controls are compliant, and the POC account is enrolled.
   - verify: the same script with `--assert` exits 0. Output saved as `evidence/F02/control-tower/2026-12-17.md`.
   - gate: Soma reviews and records any finding in the RAID log.
3. Given the Week 6 check on Dec 23, when the export runs again, then the same assertions pass.
   - verify: `--assert` exits 0. Output saved as `evidence/F02/control-tower/2026-12-23.md`.

## Dependencies

None open. Needs Identity Center access to the management account after F02-S10.

## Evidence

`evidence/F02/control-tower/` with the Dec 17 and Dec 23 exports.

## Status log

- 2026-11-19: created
- 2026-11-19: blocked_by DEP-02 added. CapNexus needs management-account access after the cross-account role is deleted.
