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
| R-01 | With kick-off on 2026-11-11 (D-08), six weeks of Period of Performance end about 2026-12-23, but the project plan runs testing (P32) to 2026-12-30. The extra days may need Change Control or written agreement with Noah Jackson. | Mike Charow | 2026-11-23 | open | D-08 |
| R-02 | Identity-aware Athena workgroups in us-east-1 run queries only through EMR Studio or SageMaker Unified Studio, not the Athena console, and do not support federated JDBC/ODBC access. The tool Lambdas may not be able to call Athena with a propagated user identity. Design response: F06-S06 spike, then decide the identity mode (F06-S07, DEP-27). | Soma Muniyappa | 2026-11-27 | open | F02-S01 service check, evidence/F02/preflight/service-availability.md row 7 |
| R-03 | Claude model access in Bedrock for the POC account is documented but not proven: first-use form and quotas are open, and one Claude model listed for us-east-1 is legacy with end-of-life 2026-11-26. Design response: choose a current model and prove a call in F02-S08. | Soma Muniyappa | 2026-11-27 | open | F02-S01 service check, evidence/F02/preflight/service-availability.md row 8 |

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
| I-10 | CapNexusDeploymentRole (account 166390307071, Identity Delegated Admin) can be assumed without an external ID or MFA, and CapNexus has no role in the management account 463768556578. F02-S01 AC1 expects an AdministratorAccess role in the management account with MFA and an external ID, 4-hour sessions and 7-day expiry. Mitsui to accept the setup or tighten the trust policy. | Noah Jackson | 2026-11-27 | closed | Soma Muniyappa, 2026-11-22 |
| I-11 | Mitsui already set up Control Tower in the management account. Decide whether F02-S01 (pre-flight), F02-S06 (launch), F02-S07, F02-S10, F02-S11 and the F02-S09 target account stay as written or become verify-only stories. Solution architect decision. | Soma Muniyappa | 2026-11-27 | closed | Soma Muniyappa, 2026-11-22 |

## Decisions

| ID | Item | Owner | Date | Status | Source |
|---|---|---|---|---|---|
| D-01 | Which SDEDBPROD approach (compress to state 0 or versioned views) will the interim owner pick, and which GIS admin runs it? | Noah Jackson | 2026-11-23 | open | Feature List s7 q1 |
| D-02 | What are the daily load window and blackout periods? The window now has to hold through the holidays. | Noah Jackson | 2026-11-20 | open | Feature List s7 q2 |
| D-03 | Does Mitsui accept the Dec 24 export with a next-business-day check of the Dec 25 load? | Noah Jackson | 2026-11-20 | open | Feature List s7 q3 |
| D-04 | Is Entra P1 licensed, and does UPN equal primary email? | Matt Schiefelbein | 2026-11-20 | open | Feature List s7 q4 |
| D-05 | Which column is masked, and what are the classification rules? | Noah Jackson, Matt Schiefelbein | 2026-12-04 | open | Feature List s7 q5 |
| D-06 | Is Mitsui comfortable with the Claude Desktop internet-reachable Gateway path? | Noah Jackson | 2026-12-09 | open | Feature List s7 q6 |
| D-07 | Who is the executive sponsor above Noah Jackson for escalations? Answer: AWS (no named person). | Noah Jackson | 2026-11-20 | open | Feature List s7 q7; Soma Muniyappa, 2026-11-20 |
| D-08 | The project plan `knowledge/CapNexus - Mitsui Well Data Assistant POC - 2026-11-20.xlsx` is the source of truth for dates and owners where it differs from `task-list/`: kick-off 2026-11-11 to 2026-11-12 (not Nov 16); Uday Gulbi is a CapNexus team member; testing (P32) runs 2026-12-21 to 2026-12-30; Noah Jackson owns P23 Teams bot, P24 Claude clients and P25 descriptions and question set. | Soma Muniyappa | 2026-11-20 | closed | Soma Muniyappa, 2026-11-20 |
| D-09 | Backups for dependency owners are optional. F01-S02 closes with named owners only; roles without a separate name stay with the current owners. | Soma Muniyappa | 2026-11-20 | closed | Soma Muniyappa, 2026-11-20 |
| D-10 | Project management evidence (meeting notes, kick-off and owner confirmation, D1 submission, status reports) is kept in the CapNexus project management workspace, not copied into this repo. Gates are recorded here as attested by the named person, with a pointer to that workspace. | Soma Muniyappa | 2026-11-20 | closed | Soma Muniyappa, 2026-11-20 |
| D-11 | D1 review clock: submitted to Noah Jackson 2026-11-16; 8 business days excluding the 2026-11-26 and 2026-11-27 holidays end 2026-11-30. Silence by then is acceptance; the clock and written rejection path were explained at the meeting. | Mike Charow | 2026-11-30 | open | Soma Muniyappa, 2026-11-20 |
| D-12 | No shared Mitsui Teams channel for CapNexus engineers. Meetings run in the CapNexus team channel; continuous discussion does not use Teams. F01-S03 closes on AWS and Git access; the Entra guest invitation (part of DEP-29) is tracked under F6. The F10 pilot bot channel is unaffected. | Soma Muniyappa | 2026-11-20 | closed | Soma Muniyappa, 2026-11-20 |
| D-13 | F1 scripts cut to `check-overdue.sh` only. Dropped: `generate-status-report.sh`, `check-status-reports.sh` (F01-S05), `check-raid-log.sh --require-clock` (F01-S04), `shift-plan.sh` and a stored days-late field (F01-S06). Reports, clock and plan shifts are kept in the CapNexus project management workspace and the project plan (D-08, D-10). | Soma Muniyappa | 2026-11-20 | closed | Soma Muniyappa, 2026-11-20 |
| D-14 | I-10 and I-11 decided. (1) Accounts: management `463768556578` (Control Tower), Identity Delegated Admin `166390307071` (IAM Identity Center and account access delegation; CapNexusDeploymentRole), Log Archive `707641390779`, Audit `171584503454`, Blank Canvas `108953016877` (POC account, pending Mitsui confirmation). (2) CapNexusDeploymentRole without external ID or MFA is accepted for the POC. (3) F02-S01 rescoped (Mitsui answers Appendix B in writing). F02-S06, S07 verify-only, F02-S10 rescoped, F02-S11 and F02-S09 target account noted. | Soma Muniyappa | 2026-11-22 | closed | Soma Muniyappa, 2026-11-22 |
