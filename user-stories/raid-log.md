# RAID log

Risks, assumptions, issues and decisions for the Well Data Assistant POC. Client dependencies
are tracked separately in [`dependencies/README.md`](dependencies/README.md). Run
`scripts/check-raid-log.sh` to check this file.

The Issues and Decisions sections are seeded from `WDA-POC-Feature-List.md`: Section 5 "Still
open" items 1 to 9 and Section 7 questions 1 to 7. The Source column names the item
(`Feature List s5 gap <n>`, `Feature List s7 q<n>`). Where the source names no owner, Mike
(CapNexus project manager) owns the item as the person raising it. Dates are the due date in
the source, otherwise 2026-11-20 (Deliverable 1 due date). Both are proposals for Mike to adjust.

Status values: `open`, `closed`. Date format: `YYYY-MM-DD`.

## Risks

Filled as risks arise.

| ID | Item | Owner | Date | Status | Source |
|---|---|---|---|---|---|

## Assumptions

Filled as assumptions are recorded.

| ID | Item | Owner | Date | Status | Source |
|---|---|---|---|---|---|

## Issues

| ID | Item | Owner | Date | Status | Source |
|---|---|---|---|---|---|
| I-01 | Unattended-load window moved to Dec 14 to Dec 25 (decided Nov 17). It conflicts with the task list, the workflow doc and the diagram timeline. Dec 25 is a holiday and the readout is Dec 24, so the window cannot be fully exported before the readout. | Mike | 2026-11-20 | open | Feature List s5 gap 1 |
| I-02 | Tool name differs between sources: `run_select` (SOW, diagram, workflow doc) and `run_select_query` (Week 3 task list). Use `run_select`. | Mike | 2026-11-20 | open | Feature List s5 gap 2 |
| I-03 | Pilot timing differs: SOW and Kickoff Agenda say Week 6, the task list opens access Mon Dec 14. Get Mitsui's written agreement to the earlier start. | Mike | 2026-11-20 | open | Feature List s5 gap 3 |
| I-04 | Kickoff decisions log is incomplete: the SDEDBPROD owner is Mitsui but no person is named and the approach is blank. The daily load window and masked column are blank in the discovery notes (DEP-11, DEP-12, DEP-16). | Mike | 2026-11-20 | open | Feature List s5 gap 4 |
| I-05 | Executive sponsor: the agenda asks to confirm one, no name was recorded, and steering check-ins were declined. Ask Noah who escalates above him. | Noah Jackson | 2026-11-20 | open | Feature List s5 gap 5 |
| I-06 | Action items 5 and 6 are empty in the Kickoff Agenda. | Mike | 2026-11-20 | open | Feature List s5 gap 6 |
| I-07 | Bot endpoint reachability: the diagram says private subnets and no internet gateway, but Azure Bot Service must reach `/api/messages` over the internet. The endpoint must be public and WAF-protected while the tools stay private. | Mike | 2026-11-20 | open | Feature List s5 gap 7 |
| I-08 | PrivateLink scope: if the bot compute is in the VPC it needs a route to AgentCore Runtime. Confirm an AgentCore interface endpoint exists in us-east-1 or keep the bot compute outside the VPC. | Mike | 2026-11-20 | open | Feature List s5 gap 8 |
| I-09 | Timeline status: check first the items due Nov 16 (management account, three emails, owners). A slip moves the plan day for day. | Mike | 2026-11-20 | open | Feature List s5 gap 9 |

## Decisions

| ID | Item | Owner | Date | Status | Source |
|---|---|---|---|---|---|
| D-01 | Which SDEDBPROD approach (compress to state 0 or versioned views) will the interim owner pick, and which GIS admin runs it? | Noah Jackson | 2026-11-23 | open | Feature List s7 q1 |
| D-02 | What are the daily load window and blackout periods? The window now has to hold through the holidays. | Noah Jackson | 2026-11-20 | open | Feature List s7 q2 |
| D-03 | Does Mitsui accept the Dec 24 export with a next-business-day check of the Dec 25 load? | Noah Jackson | 2026-11-20 | open | Feature List s7 q3 |
| D-04 | Is Entra P1 licensed, and does UPN equal primary email? | Matt Schiefelbein | 2026-11-20 | open | Feature List s7 q4 |
| D-05 | Which column is masked, and what are the classification rules? | Noah Jackson, Matt Schiefelbein | 2026-12-04 | open | Feature List s7 q5 |
| D-06 | Is Mitsui comfortable with the Claude Desktop internet-reachable Gateway path? | Noah Jackson | 2026-12-09 | open | Feature List s7 q6 |
| D-07 | Who is the executive sponsor above Noah Jackson for escalations? | Noah Jackson | 2026-11-20 | open | Feature List s7 q7 |
