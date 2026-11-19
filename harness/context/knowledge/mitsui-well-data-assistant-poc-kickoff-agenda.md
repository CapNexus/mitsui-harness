<!-- Generated from knowledge/Mitsui - Well Data Assistant POC - Kickoff Agenda.docx by .bootstrap/prepare_inputs.py. Do not edit. -->

MITSUI E&P USA  |  CAPNEXUS

Well Data Assistant Proof of Concept

Project Kickoff Agenda

## Meeting Objectives

Agree the project kickoff date. The Period of Performance starts on the kickoff date confirmed in writing (email suffices).

Name a Mitsui owner for every week-one dependency. Named owners are the second condition for the Period of Performance to start.

Align on scope, success criteria, acceptance, and governance so both teams run the six weeks against the same plan.

## Attendees

## Agenda at a Glance

## Agenda Detail

### 1. Welcome and Introductions (5 min)

Introductions: name, role, and responsibility on the POC.

Confirm Mitsui's day-to-day point of contact and the executive sponsor.

### 2. Objectives and Scope Recap (8 min)

What we are building: a read-only Well Data Assistant that answers plain-English questions on well, geodatabase, and economics data in one Microsoft Teams channel, with IT and PMO users reaching the same governed tools from Claude Code and Claude Desktop. Every query runs as, and is logged against, the person who asked it.

In scope

AWS Control Tower landing zone (Log Archive, Audit, one POC workload account) delivered as infrastructure as code

Site-to-site VPN (AWS side) and PrivateLink endpoints for Bedrock, Athena, and logging

Daily one-way AWS DMS full load of approved tables from MEPWELL, SDEDBPROD, and MEPS_ARIES (about 15.4 GB) into Amazon S3 tables

Lake Formation permissions by Entra ID group, with column masking demonstrated

Four read-only MCP tools on AgentCore Gateway; assistant on AgentCore Runtime using Claude on Amazon Bedrock

Entra ID federation to IAM Identity Center; audit trail and CloudWatch dashboard

Evaluation, ~15-user pilot, readout with run-cost estimate, and handover

Out of scope (next phase, via Change Control)

Quorum and other application API tools; QLS/LIS, accounting/cost data, and Oracle sources

Querying source databases in place; change data capture, HA, production hardening, and post-readout support

Geospatial analysis, map rendering, and ArcGIS integration

Landing zone extensions, including enrollment of existing AWS accounts

AWS Direct Connect, Microsoft licensing, and AWS consumption charges (billed directly to Mitsui)

### 3. Approach and Six-Week Timeline (7 min)

Indicative plan, confirmed in the project plan (Deliverable 1).

Note: the daily load must run without intervention for the final two weeks, so a stable load by end of week 4 is a hard target.

### 4. Client Dependencies and Owners (15 min)

Goal: leave the call with a named Mitsui owner and a committed date for each item below.

Ground rule to state: the timeline moves day for day with delays in client dependencies; delays beyond two weeks go to Change Control.

### 5. Technical Discovery (12 min)

Landing zone

Home region and any regions to deny – US Only

Existing accounts, OUs, or SCPs we need to work around - No

Preferred IaC tooling and the repository and pipeline home for handover – No preference

Claude on Amazon Bedrock approved in Mitsui's account and region; any internal AI or security review to clear – Claude is default

Network

VPN device type and on-premises CIDR ranges; AWS CIDR ranges to avoid - Pauloalto

Firewall rule owner for SQL Server access and expected turnaround – Work with Matt S

Data

Which tables are approved in each database, and who approves them – Noah J

SQL Server versions, TDE or permission restrictions affecting DMS – SQL 2017

Daily load window and any source-system blackout periods -

Column to use for the masking demonstration; classification rules for royalty owner, lessor, or other sensitive data

Identity and access

Entra ID groups mapped to tables, including one restricted group for the permission test – Matt S

Conditional Access or MFA policies affecting Identity Center federation or Claude Desktop/Code sign-in – Currently using conditional access assigned by group

### 6. Success Criteria and Acceptance (5 min)

At least 80% of the ~30-question set answered correctly, as judged by Mitsui SMEs

Every write attempt refused by AgentCore Policy and Lake Formation; no network path from the assistant to on-premises databases

Users outside a permitted Entra ID group cannot see restricted tables or the masked column, in Teams or Claude Code/Desktop

Every pilot question traces to a named user, with the SQL run and rows returned

Typical Teams answers within 60 seconds

Daily load of all three databases runs without intervention for the final two weeks

IT/PMO users can list tables, describe columns, sample rows, and run SELECT under their own sign-in

At handover, landing zone reports no drift, controls compliant, POC account enrolled

Acceptance process: each deliverable is submitted with an acceptance form; Mitsui has 8 business days to accept or reject in writing with reasons. No written rejection within the Review Period means the deliverable is accepted. Confirm who signs acceptance forms.

Action: SMEs start drafting the question set in week 1, since it drives the 80% accuracy criterion.

### 7. Governance and Communications (4 min)

Weekly status meeting: day, time, and attendees – Monday afternoon, 3:00 Eastern

Steering check-ins with the executive sponsor: cadence – Not needed

Status report format and distribution list – CapNexus standard format, attendees to kickoff call

RAID log ownership; escalation path on both sides – Mike C, escalation to Noah J

Change Control contact for out-of-scope requests (e.g., Quorum, QLS/LIS, Oracle) - Send to Noah J

Audit log retention requirements beyond defaults - Default

### 8. Decisions, Action Items, and Next Steps (4 min)

Read back decisions and owners. CapNexus sends a same-day follow-up email confirming the kickoff date and named owners, which serves as the written confirmation the SOW requires.

## Decisions Log

## Action Items

| Date | Wednesday, November 11, 2026 |

| Time / Duration | [Time] Central  |  60 minutes |

| Format | Microsoft Teams (remote; no travel planned under the SOW) |

| Reference | SOW Mitsui.CapNexus.SOW2026001, executed November 9, 2026 |

| Meeting Owner | Jeff Miller, Head of Delivery, CapNexus |

| Mitsui E&P USA | Role | CapNexus | Role |

| Noah Jackson | Manager - IT (SOW signer) | Jeff Miller | Head of Delivery |

| Kyle Hanshaw | IT | Mike Charow | Engagement Manager |

| Matt Schiefelbein | Network team | Soma Muniyappa | Solution Architect |

| Steve Van | Application Stack | Venkat Paidipalli | Data & Platform Engineer |

|  |  | Amy Teryazos | Sales |

| Jack Bradham | AWS Solutions | Tony Santiago | Managing Directory |

| Kim Sawyer | AWS Account Manager |  |  |

| # | Topic | Lead | Time |

| 1 | Welcome and introductions | Jeff Miller / Noah Jackson | 5 min |

| 2 | Objectives and scope recap | Engagement Manager | 8 min |

| 3 | Approach and six-week timeline | Solution Architect | 7 min |

| 4 | Client dependencies and owners | Jeff Miller | 15 min |

| 5 | Technical discovery | Solution Architect / Engineers | 12 min |

| 6 | Success criteria and acceptance | Engagement Manager | 5 min |

| 7 | Governance and communications | Engagement Manager | 4 min |

| 8 | Decisions, action items, next steps | Jeff Miller | 4 min |

| Week | CapNexus Focus | Mitsui Inputs |

| 1 | Mobilization, project plan, question set outline; Control Tower landing zone and POC account baseline | Management account access; VPN, SQL accounts, Entra admin by end of week |

| 2 | VPN and PrivateLink; DMS loads to S3 tables; Glue Data Catalog | Network and DBA support; approved table list |

| 3 | Lake Formation permissions and masking; Entra federation; MCP tool layer | Teams channel approval by start of week; group-to-table mapping |

| 4 | Well Data Assistant on AgentCore Runtime; Teams bot; Claude Code/Desktop access | SME table and column descriptions |

| 5 | Question-set evaluation; read-only and permission tests; observability | SME answer validation |

| 6 | Pilot, readout, and handover | ~15 pilot users; readout attendance |

| Dependency | Due | SOW | Mitsui Owner |

| AWS Organizations management account access with rights to deploy Control Tower | Kickoff | A3 | Matt S/Noah J |

| Email addresses for Log Archive, Audit, and POC workload accounts | Kickoff | A3 | Noah J |

| Confirmation of no existing Control Tower landing zone | Kickoff | A4 | Confirmed during meeting |

| Site-to-site VPN with network team support | End of wk 1 | A5 | Matt S |

| Read-only SQL Server accounts for MEPWELL, SDEDBPROD, MEPS_ARIES that meet DMS source requirements | End of wk 1 | A5 | Noah J |

| Microsoft Entra ID administrator (enterprise app, federation, group mapping) | End of wk 1 | A5 | Matt S |

| SDEDBPROD: compress to state zero before each load, or read access to versioned views | Before first load | A2 | On Hold |

| Teams administrator approval for one pilot channel | Start of wk 3 | A6 | Noah J |

| SMEs for well, geodatabase, and ARIES data (~6 hrs/week) to write ~30 questions and validate answers | Wk 1 onward | A6 | Noah J |

| ~15 pilot users | Wk 6 | A6 | Noah J |

| Decision | Outcome |

| Project kickoff date (Period of Performance start) | 11/16 |

| Mitsui day-to-day point of contact | Noah J |

| Acceptance form signer | Noah J |

| Weekly status cadence and time | Weekly on Mondays |

| AWS home region | US East 1 |

| SDEDBPROD load approach (state zero vs. versioned views) |  |

| # | Action | Owner | Due |

| 1 | Send written confirmation of kickoff date and named dependency owners | Jeff Miller | Nov 11 |

| 2 | Send out meeting agenda | Mike C | Nov 11 |

| 3 | AWS account creation | Noah J | Nov 16 |

| 4 | Schedule weekly status call | Mike C | Nov 12 |

| 5 |  |  |  |

| 6 |  |  |  |
