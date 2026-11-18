# Week 6: Testing, acceptance and handover

Dates: Dec 21 to Dec 25 (Fri Dec 25 is a holiday)

**Goal:** Testing only. No new features. Only fixes for failed tests. Mitsui verifies the acceptance criteria, CapNexus fixes defects, and the readout and handover session is held by Thu Dec 24.

## Mon 2026-12-21: Testing starts

| Done | Owner | Task |
|---|---|---|
| [ ] | Engagement Manager | Weekly status call, 3:00 PM Eastern. Walk through the Week 6 test plan and the written rejection path. |
| [ ] | Noah Jackson (Mitsui) | Confirm UAT (user acceptance testing) testers for the week and who verifies each criterion (InfoSec, Network, SMEs, IT, pilot lead). |
| [ ] | Mitsui subject matter experts | Score the frozen question set with the agreed tolerance. Record per-question results. |
| [ ] | CapNexus Integration & Test Engineer | Support the testers. Log each failed test with evidence and severity. |
| [ ] | Data & Platform Engineer | Check overnight load, row counts and alarms every morning this week. |

## Tue 2026-12-22: Permissions, write refusal and audit

| Done | Owner | Task |
|---|---|---|
| [ ] | Mitsui InfoSec and Network | Verify write attempts are refused, there is no network path to the on-premises databases, and out-of-group users cannot see restricted tables or the masked column. |
| [ ] | Mitsui IT and InfoSec | Verify audit log samples: every pilot question traces to a named user, SQL and row count. |
| [ ] | CapNexus AI Engineer | Fix any failed test. Re-run only the affected tests. |
| [ ] | CapNexus Integration & Test Engineer | Re-run permission tests for users A, B and C after any fix. |

## Wed 2026-12-23: Pilot, latency and IT/PMO tests

| Done | Owner | Task |
|---|---|---|
| [ ] | Mitsui pilot lead | Confirm typical answers in Teams arrive within 60 seconds, using the latency report. |
| [ ] | Mitsui IT/PMO (information technology and project management office) lead | Run the Claude Code and Claude Desktop test: list, describe, sample and SELECT. Record the sessions. |
| [ ] | CapNexus AI Engineer | Fix defects. Code changes need a retest note. |
| [ ] | Engagement Manager | Collect pilot feedback and wrong-answer reports. Draft the final readout figures. |
| [ ] | Solution Architect | Confirm Control Tower landing zone: no drift, controls compliant, account enrolled. Export the console evidence. |

## Thu 2026-12-24: Readout and handover

| Done | Owner | Task |
|---|---|---|
| [ ] | Data & Platform Engineer | Export DMS task history and alarm history for the unattended-load window (Dec 14 to Dec 24) as acceptance evidence. Send to the DBAs and IT verifiers. |
| [ ] | Engagement Manager | Hold the readout: results, AWS run-cost estimate from actual usage, next-phase recommendation (Deliverable 10). |
| [ ] | Solution Architect and Data & Platform Engineer | Hand over code, configuration and the runbook to the Mitsui IT operations owner. Run the knowledge-transfer session (Deliverable 11). |
| [ ] | Noah Jackson (Mitsui) | Decide: keep running, pause or tear down the AWS resources (item 10.2). |
| [ ] | Engagement Manager | Submit final deliverables. Start the 8-business-day Review Period. Agree when CapNexus access is removed. |

## Fri 2026-12-25: Christmas Day, no planned work

| Done | Owner | Task |
|---|---|---|
| [ ] | Whole CapNexus team | Holiday. No tasks scheduled. The daily load keeps running unattended (last day of the window) and alarms go to the Mitsui distribution list and the CapNexus on-call address. On the next business day, check the Dec 25 load and add it to the evidence export. |

## Exit criteria

- [ ] Every acceptance criterion in item 9.4 has evidence and a Mitsui verifier sign-off, or a written rejection reason
- [ ] Question-set score recorded by SMEs (target 80%, 24 of 30)
- [ ] Unattended-load evidence (DMS task and alarm history, Dec 14 to Dec 24, plus Dec 25 on the next business day) exported and verified by DBAs and IT
- [ ] Readout and handover session held by Thu Dec 24
- [ ] Mitsui decision on keep, pause or tear down the AWS resources recorded
- [ ] CapNexus access removed after handover (agreed with Mitsui)
- [ ] Review Period of 8 business days started for each deliverable (ends by Fri Jan 8, 2027)
