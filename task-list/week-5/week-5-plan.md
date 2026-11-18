# Week 5: Evaluate, harden, hand over and prepare for testing

Dates: Dec 14 to Dec 18

**Goal:** All build, evaluation, evidence and handover tasks finished. Week 6 is for testing only.

## Mon 2026-12-14: Pilot opens and first evaluation

| Done | Owner | Task |
|---|---|---|
| [ ] | Engagement Manager | Weekly status call, 3:00 PM Eastern. |
| [ ] | Engagement Manager | Open pilot access to the 15 pilot users in the Teams channel. Ask each user to try at least five questions this week and report wrong answers in the shared channel. |
| [ ] | Data & Platform Engineer | The two-week unattended-load window starts today (Dec 14 to Dec 25). Freeze the load pipeline. No manual loads and no source maintenance. Check overnight load, row counts and alarms. |
| [ ] | CapNexus AI Engineer | Run the question-set evaluation. Record per-question results. |
| [ ] | CapNexus Integration & Test Engineer | Start the write-attempt tests. Every write must be refused by AgentCore Policy and Lake Formation. |

## Tue 2026-12-15: Tune and observe

| Done | Owner | Task |
|---|---|---|
| [ ] | CapNexus AI Engineer | Fix wrong answers by improving descriptions, join hints and prompts. Do not tune on the held-back questions. |
| [ ] | Data & Platform Engineer | Check dashboards and alarms. Test one alarm reaches the Mitsui distribution list. |
| [ ] | CapNexus Integration & Test Engineer | Run the permission tests for users A, B and C through Teams, Claude Code and Claude Desktop. |
| [ ] | Solution Architect | Verify the route table and firewall rule export show no path from the assistant to the on-premises databases. |

## Wed 2026-12-16: Latency, pilot feedback and SME validation

| Done | Owner | Task |
|---|---|---|
| [ ] | CapNexus Integration & Test Engineer | Measure latency for typical answers in Teams (target under 60 seconds). Save the dashboard report. |
| [ ] | Engagement Manager | Review pilot feedback and wrong-answer reports with the AI Engineer. Log defects with severity. |
| [ ] | Engagement Manager | SMEs start validating answers against their own tools (ARIES, ArcGIS, well reports). |
| [ ] | CapNexus AI Engineer | Re-run the evaluation after fixes. |

## Thu 2026-12-17: Handover and readout material

| Done | Owner | Task |
|---|---|---|
| [ ] | Data & Platform Engineer | Finish infrastructure as code, pipeline and teardown scripts. Move the repository to Mitsui if agreed (item 1.7). |
| [ ] | Solution Architect | Write the runbook: load, alarms, rotate secrets, SCIM token renewal, teardown (Deliverable 11). |
| [ ] | Engagement Manager | Draft the readout deck: results, AWS run-cost estimate from actual usage, next-phase recommendation (Deliverable 10). |
| [ ] | Solution Architect | Confirm the Control Tower landing zone shows no drift and enabled controls are compliant. |

## Fri 2026-12-18: Code freeze and evidence pack

| Done | Owner | Task |
|---|---|---|
| [ ] | Whole CapNexus team | Code freeze. Only fixes for failed tests after this point. |
| [ ] | Data & Platform Engineer | Unattended-load window day 5. Check overnight load, row counts and alarms. The export of DMS task and alarm history happens on Thu Dec 24. |
| [ ] | Engagement Manager | Complete the evidence pack against the acceptance matrix in item 9.4, except the unattended-load evidence which follows on Dec 24. Send it to Noah Jackson. |
| [ ] | Engagement Manager | Publish the Week 6 test plan: who tests what, daily, and the written rejection path. Week 6 plan is in week-6. Fri Dec 25 is a holiday. |
| [ ] | Engagement Manager | Week 5 exit review. Confirm readout attendees and handover recipients (items 10.2, 10.3). |
| [ ] | Engagement Manager | Update the RAID log and confirm all Week 1 to Week 5 tasks are closed or have a named owner and date. |

## Exit criteria

- [ ] Question-set evaluation at or above 80% (24 of 30)
- [ ] Write-attempt, permission and latency tests passed with evidence saved
- [ ] Daily load is running unattended since Mon Dec 14 (window runs to Fri Dec 25)
- [ ] Runbook, code and infrastructure as code ready for handover
- [ ] Pilot users active and feedback collected
- [ ] Evidence pack complete against the acceptance matrix (load evidence follows Dec 24)
- [ ] Code freeze in effect
