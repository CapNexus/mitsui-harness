# Dependency register

This register is the dependency tracker for F1 (feature list Section 3). The "why" and the resolve steps for each DEP stay in `../../WDA-POC-Feature-List.md` Section 3. This file adds the type, which tells the harness what it can do.

## Types

| Type | Meaning | Harness behavior |
|---|---|---|
| A | A value (CIDR, table list, column name, URL, address) | Build with a placeholder from `config/parameters.md`. Swapping the value is a config change. |
| B | A secret or credential | Reference it by Secrets Manager name only. A human enters the value. The harness never sees it. |
| C | An approval or sign-off | Human gate. Stop at the gate. |
| D | Access or an action in Mitsui's environment | Human gate. Stop at the gate. |
| E | A decision that changes the design | Ask a human before building. Build the likely option behind a switch, or wait. |

A secondary type is shown after the primary one (for example A+C: a value that also needs a signature).

## Register

Status values: `open`, `requested`, `in-progress`, `resolved`, `slipped`. A `slipped` row needs a slip date and cause in the Notes column (SOW Assumption 8), written as `slip-date: YYYY-MM-DD; cause: <text>`. Notes stay empty for other rows.

| ID | Dependency | Owner (Mitsui) | Needed by | Type | Status | Used by features | Notes |
|---|---|---|---|---|---|---|---|
| DEP-01 | Named owners and backups | Noah Jackson | Nov 16 | D | resolved | F1 | Owners named at the team meeting; no backups named, backups optional (RAID D-09). Attested by Soma Muniyappa 2026-11-20. |
| DEP-02 | Management account, root MFA, cross-account role | Noah Jackson, Matt Schiefelbein | Nov 17 | D+B | in-progress | F2, F3, F6 | Control Tower set up; management account update expected week of 2026-11-23 (Soma Muniyappa, 2026-11-20). |
| DEP-03 | Three account emails | Noah Jackson | Nov 18 | D+A | open | F2, F4 | |
| DEP-04 | Change-freeze calendar and CAB rules | Noah Jackson | Week 1 | C | open | F1, F3 | |
| DEP-05 | InfoSec, vendor and data-copy approval | Noah Jackson (names reviewer) | Week 1 and ongoing | C | open | F3, F4 | |
| DEP-06 | Region, service availability, Bedrock access and quotas | Soma (Solution Architect), Matt, Noah | Week 1 | A+D | open | F2, F8, F9 | |
| DEP-07 | VPN, IP plan, DNS, firewall rules | Matt Schiefelbein | Nov 20 | A+D | open | F3, F4 | |
| DEP-08 | Source inventory, mixed-mode authentication, TDE | DBAs via Noah | Week 1 | D+A | open | F4 | |
| DEP-09 | Read-only SQL logins | Noah Jackson, DBAs | Nov 20 | B | open | F4 | |
| DEP-10 | Approved table list | Noah Jackson | Nov 27 | A+C | open | F4, F5 | |
| DEP-11 | SDEDBPROD approach and owner | Noah Jackson (interim) | Nov 23 | E | open | F4 | |
| DEP-12 | Daily load window and blackouts | Noah Jackson, DBAs | Week 2 | A | open | F4, F13 | |
| DEP-13 | Data dictionary, join keys, SME sessions | Noah Jackson, SMEs | Week 2 | A | open | F4, F5, F9 | |
| DEP-14 | Entra administrator, licensing, groups, app registrations | Matt Schiefelbein | Weeks 1 to 3 | D+B+A | open | F6, F7, F11 | |
| DEP-15 | Conditional Access and MFA review | Matt Schiefelbein | Weeks 2 to 3 | D | open | F6, F11 | |
| DEP-16 | Masked column and classification rules | Noah Jackson, Matt Schiefelbein | Dec 4 | A+C | open | F7 | |
| DEP-17 | SME table and column descriptions | Noah Jackson, SMEs | Dec 10 | A | open | F5 | |
| DEP-18 | Azure subscription for the Azure Bot | to be named | Week 3 | D | open | F10 | |
| DEP-19 | Teams administrator approval for one pilot channel | Noah Jackson | Nov 30 | C | open | F10 | |
| DEP-20 | IT/PMO device readiness, connection-method approval, user list | Noah Jackson, InfoSec | Dec 9 | C+E | open | F11 | |
| DEP-21 | SMEs and question set of about 30 questions | Noah Jackson, SMEs | Dec 10 | A | open | F9, F13 | |
| DEP-22 | About 15 pilot users | Noah Jackson | Week 4 | A+D | open | F10, F13 | |
| DEP-23 | Acceptance owner and UAT testers | Noah Jackson | Week 6 | C | in-progress | F1, F13, F14 | Noah Jackson confirmed as acceptance owner (Soma Muniyappa, 2026-11-20). UAT testers not yet named. |
| DEP-24 | Audit and logging policy, alarm recipients | Noah Jackson, InfoSec | Week 5 | A | open | F12 | |
| DEP-25 | Repository and pipeline home | Mitsui | Week 1 | A+D | open | F2, F14 | |
| DEP-26 | Budget approval and billing contact | Noah Jackson | Week 1 | C+A | open | F1, F2 | |
| DEP-27 | Identity propagation to Athena | Soma (Solution Architect, test), Noah (accepts fallback) | Dec 2 | E | open | F6, F7, F8, F12 | |
| DEP-28 | Handover recipients, readout attendees, post-POC decision | Noah Jackson | Dec 14 | A+C | open | F14 | |
| DEP-29 | CapNexus working access (Teams, Entra guest, AWS portal) | Mitsui | Week 1 | D | in-progress | F1, F6 | All five engineers have AWS and Git access (Soma Muniyappa, 2026-11-20). Shared Teams channel not needed (RAID D-12). Entra guest invitation still open, tracked under F6. |

Status values start as `open` because this folder has no record of what was sent. Update them as items are requested and resolved.
