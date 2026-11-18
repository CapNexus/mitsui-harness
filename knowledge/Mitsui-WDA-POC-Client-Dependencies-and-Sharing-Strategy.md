# Mitsui E&P USA: Well Data Assistant POC
## Client Dependencies and Sharing Strategy

| | |
|---|---|
| Source document | Mitsui.CapNexus.SOW2026001, Well Data Assistant Proof of Concept (dated Oct 29, 2026, signed Nov 9, 2026) |
| Prepared by | CapNexus, LLC, for Mitsui E&P USA LLC |
| Prepared | Nov 16, 2026 |
| Related document | Mitsui - Well Data Assistant POC - Kickoff Agenda (kickoff meeting Wed Nov 11, 2026). Where the two differ, the decisions log in the Kickoff Agenda governs and this document is updated to match. |
| Status | Shared with Mitsui. Kept by both parties as the system of record for client dependencies. Changes are recorded in the revision table below. |
| Conventions | Kick-off is Monday Nov 16, 2026. Week 1 is the week of Nov 16, Week 2 is Nov 23, Week 3 is Nov 30, Week 4 is Dec 7, Week 5 is Dec 14, Week 6 is Dec 21. "Mitsui" = Client. Times are US Central. The kickoff agenda states the weekly status call in Eastern time. |


| Revision | Date | Change |
|---|---|---|
| 1.0 | Nov 16, 2026 | First issue |
| 1.1 | Nov 16, 2026 | Decisions recorded: management-account access by temporary cross-account role (item 2.2), TypeScript or Python for code (item 1.7) |
| 1.2 | Nov 16, 2026 | Kick-off set to Nov 16, 2026. Calendar dates added to Sections 0, 1 and 3. CapNexus hands over the cross-account role details at kick-off. |
| 1.3 | Nov 16, 2026 | Aligned to the Kickoff Agenda: named owners, Region (us-east-1), Palo Alto virtual private network (VPN) device, SQL Server 2017, governance cadence, weekly timeline, and open items (new Section 1, "Owners and decisions from the kickoff") |
| 1.4 | Nov 16, 2026 | Management account clarified: a new AWS account created by Noah Jackson as the root user and handed over for Control Tower (items 2.2, 2.3). Kyle Hanshaw and Steve Van left blank. Kick-off confirmed as the start of the week of Nov 16. |
| 1.5 | Nov 16, 2026 | Subject matter expert (SME) time and effort commitments removed (items 4.6, 6.1, 9.1, summary table, risks). The SMEs' tasks remain. |
| 1.6 | Nov 16, 2026 | Abbreviations spelled out where they are used. The labels K and W1 to W6 replaced by kick-off and Week 1 to Week 6, so readers do not need to look them up. |

---

## 0. How to use this document

Section 1 is the one-page view of everything Mitsui must provide. Section 2 sets out how we exchange access and data safely. Section 3 gives the critical path and dates. Section 4 is the detailed list, in ten groups: for each item it states what Mitsui provides, why we need it, how Mitsui does it, how we use it, and how we know it is done. Section 5 lists the risks and dependencies. Section 6 lists the questions still open after the kickoff. The appendices hold ready-to-send scripts and templates.

### Findings that need a decision at kick-off

| # | Finding | Why it matters |
|---|---|---|
| 1 | **AWS Region is decided: US East (N. Virginia), us-east-1, US only (kickoff).** The Control Tower home Region, the IAM Identity Center Region and the Athena workgroup Region must line up, and the home Region cannot easily be changed later. | We do not revisit the Region (item 2.1). |
| 2 | **Teams bots must be single-tenant.** Microsoft stopped allowing new multi-tenant bot registrations after July 31, 2025. The Azure Bot resource therefore needs an Azure subscription and a single-tenant Entra app in Mitsui's tenant. | Mitsui must supply an Azure subscription or resource group (item 7.1). |
| 3 | **AWS Database Migration Service (DMS) cannot write directly to Amazon S3 Tables.** DMS writes CSV or Parquet to a regular S3 bucket. We stage there and load S3 Tables with Athena or Glue. | Design note only. There is no client action. It adds a staging bucket and one pipeline step. |
| 4 | **AWS DMS cannot use Windows (NTLM) authentication for SQL Server sources.** It needs SQL-authenticated logins, so each SQL Server instance must allow mixed-mode authentication. | If an instance is Windows-only, enabling mixed mode needs a service restart and a change window (item 4.2). |
| 5 | **Holiday calendar.** With kick-off on Nov 16, Week 2 contains Thanksgiving (Nov 26), Week 6 ends on Christmas Day (Dec 25), and the December change-freeze season falls in between. | Network, database administrator (DBA) and Entra changes may be blocked exactly when we need them (item 1.2). |
| 6 | **The Statement of Work (SOW) auto-accepts deliverables after 8 business days of silence.** | Mitsui must name an acceptance owner and know the clock (item 9.4). |
| 7 | **Entra ID does not support dynamic client registration.** Claude Code and Claude Desktop must use pre-registered Entra app clients. | Mitsui's Entra admin must create an additional app registration (item 5.4). |
| 8 | **The SDEDBPROD load approach is on hold and has no owner.** The kickoff agenda lists "compress to state zero, or read access to versioned views" as On Hold. | Needed before the first load (Week 2, from Mon Nov 23). Without it the AWS copy of the geodatabase can be stale (item 4.4). |
| 9 | **The management account is a new AWS account that Noah Jackson creates as the root user (due Nov 16) and hands over to CapNexus.** Root credentials stay with Mitsui. CapNexus works through the temporary cross-account role (item 2.2). Control Tower then creates the Log Archive, Audit and POC workload accounts from the three email addresses. | A new account starts with default service quotas and needs activation (contact details, payment method, verification) and root multi-factor authentication (MFA) before Control Tower can launch (item 2.2). |

---

## 1. Summary: what Mitsui provides

"Needed by" follows the Statement of Work (SOW): Assumption 3 (by kick-off), Assumption 5 (end of Week 1), Assumption 6 (Week 3 start, Week 6). Items without a SOW date are our proposed dates, needed to keep the SOW dates achievable. With kick-off on Nov 16, Week 1 ends Fri Nov 20 and Week 3 starts Mon Nov 30. Items due at kick-off that are not in place roll into Week 1, and under SOW Assumption 8 the timeline then moves day for day.

### Owners and decisions from the kickoff

Source: Kickoff Agenda, sections 4 to 7 and the Decisions Log. Mitsui attendees and the items they own:

| Mitsui person | Role | Owns |
|---|---|---|
| Noah Jackson | Manager - IT (Statement of Work (SOW) signer) | Day-to-day point of contact. Signs acceptance forms. Escalation point. Contact for Change Control requests. Owns: account email addresses (2.3), read-only SQL accounts (4.2), approval of tables (4.3), subject matter experts (SMEs) (9.1, 9.2), Teams administrator approval (7.2), pilot users (9.3). Creates the new management account as the root user (due Nov 16). Co-owns management account access (2.2). |
| Matt Schiefelbein | Network team | Virtual private network (VPN) and firewall rules for SQL Server access (3.1 to 3.4). Entra ID administrator tasks and Entra group mapping (5.x, 6.2). Co-owns management account access (2.2). |
| Kyle Hanshaw | IT | |
| Steve Van | Application Stack | |
| Jack Bradham | AWS Solutions | AWS contact (item 1.8). |
| Kim Sawyer | AWS Account Manager | AWS contact (item 1.8). |

CapNexus: Jeff Miller (Head of Delivery, kickoff meeting owner, written confirmation of kickoff date and owners), Mike Charow (Engagement Manager, weekly status, risks, assumptions, issues and dependencies (RAID) log), Soma Muniyappa (Solution Architect), Venkat Paidipalli (Data & Platform Engineer). CapNexus also provides the AI Engineer and the Integration & Test Engineer.

Decisions and answers recorded at the kickoff:

| Topic | Outcome |
|---|---|
| Project kickoff date (Period of Performance start) | Mon Nov 16, 2026 |
| Mitsui day-to-day point of contact | Noah Jackson |
| Acceptance form signer | Noah Jackson |
| Weekly status | Mondays, 3:00 PM Eastern (2:00 PM Central). CapNexus standard report, sent to the kickoff attendees. |
| Steering check-ins | Not needed |
| RAID log owner and escalation | Mike Charow (CapNexus). Escalation to Noah Jackson. |
| Change Control contact for out-of-scope requests (for example Quorum, QLS/LIS, Oracle) | Noah Jackson |
| AWS home Region | US East (N. Virginia), us-east-1. US only. |
| Existing accounts, organizational units (OUs) or service control policies (SCPs) to work around | None |
| Infrastructure-as-code tooling | No preference (TypeScript or Python) |
| Claude on Amazon Bedrock | Claude is the default model |
| VPN device | Palo Alto |
| SQL Server version | SQL Server 2017 |
| Firewall rules for SQL Server access | Matt Schiefelbein |
| Conditional Access | In use, assigned by group |
| Audit log retention beyond defaults | Not required (defaults) |

Still open after the kickoff:

| Open item | Needed by | Item |
|---|---|---|
| SDEDBPROD approach (compress to state zero or versioned views) and its owner | Before first load, Week 2 (Nov 23) | 4.4 |
| Daily load window and source blackout periods (blank at kickoff) | Week 2 | 4.5 |
| Column to mask and classification rules for royalty owner, lessor or other sensitive data (blank at kickoff) | Week 3 | 6.2 |
| Transparent Data Encryption (TDE) or other permission restrictions affecting AWS Database Migration Service (DMS) (only the SQL Server version was recorded) | Week 1 | 4.1 |
| Names of database administrators (DBAs), geographic information system (GIS) administrator, Azure administrator, InfoSec reviewer, SMEs (well, geodatabase, ARIES) and IT and project management office (IT/PMO) lead | Week 1 | 1.1 |
| Palo Alto model and PAN-OS version, public IP, routing type, Classless Inter-Domain Routing (CIDR) ranges | Week 1 | 3.1, 3.2 |
| Repository and pipeline home for handover | Week 1 | 1.7 |
| Conditional Access policies and groups that apply to the pilot and test users | Week 2 | 5.5 |
| New management account details: account ID, root email, activation complete, root multi-factor authentication (MFA) on, cross-account role created | Nov 16 to 17 | 2.2, Section 6, question 1 |

### At kick-off (Mon Nov 16)

| ID | Mitsui provides | Owner (Mitsui) | Statement of Work (SOW) ref |
|---|---|---|---|
| 1.1 | Named owners for every week-1 dependency (this starts the Period of Performance) | Noah Jackson | Period of Performance |
| 1.2 | Change-freeze calendar (kick-off date set: Nov 16) | Noah Jackson | Period of Performance |
| 1.3 | Security / vendor / architecture approval started | Noah Jackson to name the InfoSec reviewer | Assumption 9, 11 |
| 1.4 | Data classification and approval to copy the three databases to AWS | Noah Jackson (approves tables) | Scope |
| 2.1 | AWS Region decision | **Decided at kickoff: us-east-1, US only** | Scope |
| 2.2 | Access to the AWS Organizations management account with permission to deploy Control Tower | Matt Schiefelbein, Noah Jackson | Assumption 3 |
| 2.3 | Three unique email addresses for the Log Archive, Audit and POC workload accounts | Noah Jackson | Assumption 3 |
| 2.4 | Pre-flight facts about the existing AWS organization (none existing: no accounts, organizational units (OUs) or service control policies (SCPs)) | Matt Schiefelbein, Noah Jackson | Assumption 4 |

### By end of Week 1 (Fri Nov 20)

| ID | Mitsui provides | Owner (Mitsui) | Statement of Work (SOW) ref |
|---|---|---|---|
| 3.1 to 3.4 | Site-to-site virtual private network (VPN) (Palo Alto device, routing, IP plan, firewall rules, Domain Name System (DNS)) with network team support | Matt Schiefelbein | Assumption 5 |
| 4.1 | Source database inventory | Noah Jackson (database administrators (DBAs) to be named) | Assumption 1 |
| 4.2 | Read-only SQL Server logins for MEPWELL, SDEDBPROD, MEPS_ARIES that meet AWS Database Migration Service (DMS) requirements | Noah Jackson | Assumption 5 |
| 5.1, 5.2 | Microsoft Entra ID administrator for the enterprise application, federation and group mapping | Matt Schiefelbein | Assumption 5 |
| 2.6 | Anthropic model use-case submission and quota requests started | Matt Schiefelbein, Noah Jackson | Scope |

### Week 2 to Week 4 (Nov 23 to Dec 11)

| ID | Mitsui provides | Owner (Mitsui) | Needed by |
|---|---|---|---|
| 4.3 | Approved table list | Noah Jackson | Week 2 |
| 6.2 | Restricted tables, masked column, Entra group to table mapping | Matt Schiefelbein (groups), Noah Jackson (tables) | Week 3 |
| 4.4 | SDEDBPROD compress-to-state-0 job or versioned-view access | **On hold, no owner** | Before first load (Week 2) |
| 4.5 | Daily load window | Noah Jackson (database administrators (DBAs) to be named) | Week 2 |
| 5.3, 5.4, 5.6 | Entra groups, app registrations, test users | Matt Schiefelbein | Week 3 |
| 6.1 | Table and column descriptions with subject matter experts (SMEs) | Noah Jackson (SMEs) | Week 2 to Week 4 |
| 9.1, 9.2 | Named SMEs; question set of about 30 questions with expected answers | Noah Jackson (SMEs) | Week 1 to Week 4 |
| 7.1 | Azure subscription or resource group for the Azure Bot | To be named | Week 3 |
| 7.2 | Teams administrator approval for one pilot channel | Noah Jackson | **Start of Week 3 (Mon Nov 30)** |
| 8.1, 8.2 | Device readiness, approval of the connection method, IT and project management office (IT/PMO) user list | Noah Jackson (to confirm) | Week 3 |
| 9.3 | Names of about 15 pilot users, in the Entra groups | Noah Jackson | Week 4 |

### Week 5 and Week 6 (Dec 14 to Dec 25)

| ID | Mitsui provides | Owner (Mitsui) | Needed by |
|---|---|---|---|
| 9.3 | About 15 pilot users active | Noah Jackson | **Week 6** |
| 9.4 | User acceptance testing (UAT) participation, written acceptance or rejection within 8 business days | Noah Jackson (acceptance signer) | Per deliverable |
| 10.1 to 10.3 | Alarm recipients, handover recipients, readout attendees | Noah Jackson | Week 5 |

---

## 2. Sharing strategy

This section defines how Mitsui gives us access and data without handing over standing credentials or copies of data.

### Principles

1. **Mitsui creates identities for us. We do not hold Mitsui credentials.** Each CapNexus engineer gets a named account (Entra B2B guest, then an IAM Identity Center assignment). No shared logins. Root user credentials of the AWS accounts stay with Mitsui.
2. **Least privilege, time-boxed.** Elevated roles, such as Control Tower setup in the management account, are temporary and removed once the task is done. Only the five Statement of Work (SOW) roles (Engagement Manager, Solution Architect, Data & Platform Engineer, AI Engineer, Integration & Test Engineer) get access.
3. **Data never leaves Mitsui's AWS account.** The only copy of Mitsui data is the daily AWS Database Migration Service (DMS) load into the POC workload account. We do not request exports, extracts or database backups. We inspect data in place (Athena, screen-share) and keep samples inside the account.
4. **Secrets go through a vault, never email or chat.** SQL passwords, the System for Cross-domain Identity Management (SCIM) token and the bot secret move through AWS Secrets Manager or Mitsui's password manager. Mitsui staff enter them into Secrets Manager themselves where practical.
5. **We do not need direct access to Mitsui's network.** CapNexus engineers never connect to the SQL Servers. The database administrators (DBAs) run the scripts in Appendix A and send back the results. DMS in AWS is the only client of the databases.
6. **Everything is evidenced.** Every Mitsui item closes with evidence (a screenshot, a configuration export, or a command output) saved to the risks, assumptions, issues and dependencies (RAID) log. These close each acceptance criterion later.

### Access model: what each CapNexus role needs

| Access | Who at CapNexus | How Mitsui provides it | Duration |
|---|---|---|---|
| Teams meetings and shared channel for the project | All | Guest invite to the project Team | Whole POC |
| Entra B2B guest accounts | All five roles | Entra admin invites; adds to `sg-wda-capnexus-engineers` | Whole POC, removed at handover |
| AWS management account, Control Tower setup | Solution Architect, Data & Platform Engineer | Temporary cross-account role (item 2.2) | Week 1 only (hours) |
| AWS management account, IAM Identity Center configuration | Solution Architect | Scheduled sessions with the Mitsui admin, or a time-boxed role | Short sessions in Week 1 to Week 3 |
| AWS POC workload account, build access | All technical roles | IAM Identity Center permission sets assigned to the CapNexus group | Whole POC |
| Azure resource group (Azure Bot only) | Integration & Test Engineer | Contributor on one resource group, or Mitsui admin runs our steps | Week 2 to Week 3 |
| Entra admin tasks | None. Mitsui's admin performs them on a call with us | n/a | n/a |
| SQL Server and the on-prem network | None | n/a | n/a |

### Working rhythm

| Mechanism | Detail |
|---|---|
| Weekly status | Mondays, 3:00 PM Eastern (2:00 PM Central). CapNexus standard report, sent to the kickoff attendees. Mike Charow schedules and runs it. |
| Steering | Not needed (kickoff decision). |
| RAID log and dependency tracker | Owned by Mike Charow. Each dependency has ID, owner, due date, status and evidence link. This document is the reference for the dependency list. |
| Shared channel | One Teams channel for working questions, kept separate from the pilot channel. |
| Escalation | Mike Charow escalates to Noah Jackson. Any dependency more than 2 business days late is raised there. |
| Change Control | Out-of-scope requests (for example Quorum, QLS/LIS, Oracle) go to Noah Jackson. |
| Slippage | SOW Assumption 8: the timeline moves day for day with Client delays. Delays beyond 2 weeks go through Change Control. We record each slip in the tracker with the date and cause. |

---

## 3. Critical path and dates

Kick-off is Monday, Nov 16, 2026, after Statement of Work (SOW) signature on Nov 9. The plan is built backwards from the acceptance criterion "the daily load runs without intervention for the final two weeks". Because kick-off is also the day the week-1 dependencies start, anything not in place on Nov 16 begins to move the plan.

| When | Dates | What must be true | Depends on |
|---|---|---|---|
| Kick-off | Mon Nov 16 | Owners confirmed, Region decided (us-east-1), cross-account role details handed over by CapNexus, three account emails provided, new management account created by Noah Jackson (root) with multi-factor authentication (MFA) and the cross-account role in place | 1.1, 2.1 to 2.4 |
| Week 1 | Nov 16 to 20 | Mobilization, project plan and question set outline (Deliverable 1). Mitsui creates the cross-account role. Control Tower landing zone and POC account baseline. By Fri Nov 20: virtual private network (VPN), read-only SQL accounts, Entra administrator available. | 2.2, 2.3, 3.x, 4.2, 5.1 |
| Week 2 | Nov 23 to 27 (Thanksgiving Nov 26) | VPN and PrivateLink. AWS Database Migration Service (DMS) loads to S3 tables. Glue Data Catalog. Approved table list. **SDEDBPROD approach decided before the first load.** | 3.x, 4.1 to 4.5 |
| Week 3 | Nov 30 to Dec 4 | **Teams admin approval for the pilot channel by Mon Nov 30 (SOW).** Lake Formation permissions and masking. Entra federation. Model Context Protocol (MCP) tool layer. Group-to-table mapping. | 7.2, 5.x, 6.2 |
| Week 4 | Dec 7 to 11 | Assistant on AgentCore Runtime. Teams bot. Claude Code and Claude Desktop access. Subject matter expert (SME) table and column descriptions. Question set complete, pilot users named. **Stable daily load by Fri Dec 11 (hard target).** Core build in the Mitsui test environment. | 6.1, 7.1, 8.x, 9.2, 9.3 |
| Week 5 | Dec 14 to 18 | Question-set evaluation. Read-only and permission tests. Observability. SME answer validation. The two-week unattended-load window starts Mon Dec 14 and must run through Fri Dec 25. User acceptance testing (UAT) begins. | 4.5, 9.1 |
| Week 6 | Dec 21 to 25 (Dec 25 holiday) | Pilot with about 15 users. Readout and handover, planned by Thu Dec 24. | 9.3 |
| After Week 6 | To Fri Jan 8, 2027 | Review Period of 8 business days per deliverable. The Period of Performance ends at the later of acceptance of Deliverables 10 and 11, or 8 weeks from kick-off (Jan 8, 2027). | 9.4 |

**If any week-1 dependency slips**, the unattended-load window moves with it and the 6-week plan fails. The week-1 items are therefore the highest risk to the schedule. Holiday absences in Week 2 and Week 6 leave little room to recover.

---

## 4. Detailed requirements (items grouped 1 to 10)

Each item states what Mitsui provides, why we need it, how it is done, how we use it, and when it is done.

---

## Group 1: Program and governance

### 1.1 Named owners and decision-makers

- **Mitsui provides:** Confirmation of the owners in the kickoff table (Section 1), and a named person, backup and email for each role still unnamed: database administrator (DBA) for each of the three databases, geographic information system (GIS) administrator, ARIES administrator or reserves lead, Azure administrator, InfoSec reviewer, business subject matter experts (SMEs) (well, geodatabase, ARIES economics), IT and project management office (IT/PMO) lead and pilot lead.
- **Why:** The Statement of Work (SOW) says the Period of Performance starts only after Mitsui "has named owners for the week one (1) dependencies". Without them nothing is time-bound.
- **How:** Noah Jackson (SOW signer, day-to-day contact and acceptance signer) names the remaining owners and backups in Week 1. One person can hold several roles. The executive sponsor was not named at the kickoff and no steering check-ins are planned.
- **How we use it:** The names go into the risks, assumptions, issues and dependencies (RAID) log and the weekly status report.
- **Done when:** Every row in Section 1 has an owner and a backup.

### 1.2 Kick-off date and change calendars

- **Mitsui provides:** The holiday calendar and any freeze windows for network, firewall, database, Entra and AWS Organizations changes between Nov 16, 2026 and Jan 8, 2027 (kick-off plus 8 weeks).
- **Why:** The SOW timeline is 6 weeks (8 maximum). The Nov 16 start overlaps Thanksgiving (Nov 26), Christmas (Dec 25) and year-end freezes. Network, database and Entra changes are the ones that block us.
- **How:** The project owner asks the change advisory board for the freeze dates. Kick-off is agreed as Nov 16, 2026 (the SOW accepts email confirmation).
- **How we use it:** We fix the plan around the freezes and ask Mitsui to submit changes early (virtual private network (VPN), firewall, SQL logins).
- **Done when:** Freeze dates are in the RAID log.
- **Watch-outs:** If Mitsui needs a change advisory board (CAB) ticket for every network change, it must be raised on day 1.

### 1.3 Security, vendor and architecture approvals

- **Mitsui provides:** Written approval (or a named reviewer with a committed turnaround) for:
  1. CapNexus as a vendor with access to the AWS and Entra environments.
  2. The architecture: copy of data to AWS, VPN, Bedrock, AgentCore, Teams bot.
  3. Sending question text, table schemas and result rows to Claude models on Amazon Bedrock.
  4. An internet-facing HTTPS endpoint that receives messages from Azure Bot Service (item 3.5).
  5. For IT/PMO use: how Claude Code and Claude Desktop traffic reaches AWS (item 8.1).
- **Why:** SOW Assumption 9 makes Mitsui's cooperation a condition of delivery. These are the reviews most likely to take longer than a week.
- **How:** At the kickoff Mitsui noted that Claude is the default model. CapNexus sends the architecture summary and data-flow diagram at kick-off, and Noah Jackson names the InfoSec reviewer. Mitsui InfoSec opens the review and returns questions.
- **How we use it:** Approvals gate the first AWS Database Migration Service (DMS) load and the Teams bot go-live.
- **Done when:** InfoSec confirms in writing, or gives a conditional approval with a list of conditions we can meet.
- **Watch-outs:** Bedrock model invocation logging stores prompts and responses. Security should know question text and result rows are logged (item 10.1).

### 1.4 Data classification and approval to copy data

- **Mitsui provides:** The data classification of MEPWELL, SDEDBPROD and MEPS_ARIES, and confirmation that the approved tables may be copied into AWS and queried with a large language model (LLM). This includes any contractual limits (joint-venture partner data, royalty-owner data, reserves and economics figures, price decks).
- **Why:** Economics and reserves data is the most sensitive item in scope. The SOW only copies "approved tables", so Mitsui decides what is approved.
- **How:** Data owners review the table inventory (item 4.1) and mark each table Approved, Approved with masking, or Not approved (item 4.3).
- **How we use it:** The list drives the DMS table mappings, Lake Formation permissions and masking.
- **Done when:** A signed-off approved-table list exists (Appendix E1).

### 1.5 AWS billing, budget and cost approval

- **Mitsui provides:** The payer (management) account owner, a billing contact, and an approved monthly budget for POC running costs.
- **Why:** The SOW says AWS consumption is "billed directly to Client's AWS account and is not included in this SOW". The cost is small but not zero (VPN, PrivateLink endpoints, DMS, Bedrock tokens, Athena, CloudWatch, Config).
- **How:** Mitsui confirms the budget. We send a monthly cost estimate in Week 1 and deploy an AWS Budgets alert to the billing contact.
- **How we use it:** The AWS run-cost estimate in the readout (Deliverable 10) uses the actual POC usage.
- **Done when:** Budget approved and alert recipients named.

### 1.6 Working access for CapNexus

- **Mitsui provides:** Entra B2B guest accounts for the CapNexus engineers, access to the shared Teams channel, and confirmation that no virtual desktop infrastructure (VDI), laptop or on-site workspace is required.
- **Why:** SOW Assumptions 11 and 12 require access to systems, resources and remote workspace. Our design needs only cloud access.
- **How:** Entra admin invites guests and adds them to `sg-wda-capnexus-engineers` (item 5.3). If Mitsui requires its own devices or VDI for vendors, say so at kick-off.
- **Done when:** Each CapNexus engineer signs in to the AWS access portal and Teams.

### 1.7 Source control, infrastructure as code and ticketing

- **Mitsui provides:** Where the infrastructure-as-code repository and pipeline should live for handover (Mitsui Git, for example GitHub or Azure DevOps), and the ticketing system for firewall, SQL and Entra requests.
- **Why:** Deliverable 2 and 11 are infrastructure as code with a deployment pipeline and handover. Work-for-hire terms mean Mitsui owns the code, so it should live in Mitsui's repository.
- **How:** Mitsui creates a repository and grants CapNexus engineers write access, or approves a CapNexus-hosted repository that is transferred at handover.
- **How we use it:** The pipeline in the POC workload account pulls from this repository.
- **Done when:** Repository agreed and engineers have access.
- **Decision (kickoff: no preference on tooling):** Infrastructure and application code are written in TypeScript or Python (for example AWS Cloud Development Kit (CDK) for infrastructure). AWS CodeCommit is closed to new customers, so the pipeline pulls from Mitsui's repository through AWS CodeConnections.

### 1.8 AWS account team contact

- **Mitsui provides:** The AWS contacts. At the kickoff these are Kim Sawyer (AWS Account Manager) and Jack Bradham (AWS Solutions). Confirm both can be engaged for quota and feature questions.
- **Why:** New accounts start with low Amazon Bedrock quotas for Claude models. The AWS team can speed up quota increases and confirm feature availability.
- **Done when:** Both contacts are in the RAID log.

---

## Group 2: AWS foundation

### 2.1 Region decision

- **Mitsui provides:** Confirmation of the AWS Region for the landing zone (the Control Tower home Region), and approval to use other US Regions for Claude cross-region inference.
- **Why:** Per AWS documentation, if IAM Identity Center already exists, the Control Tower home Region must match it. Athena's identity-aware workgroups, Lake Formation, Glue, S3 Tables, AgentCore Gateway, Identity and Runtime must all sit in a Region that supports them. Claude models on Bedrock often run through US cross-region inference profiles that route among us-east-1, us-east-2 and us-west-2.
- **How:** Mitsui stated the data-residency rule (US only) at the kickoff and confirms whether an IAM Identity Center instance exists.
- **How we use it:** We deploy everything to the home Region, and allow the destination Regions of the inference profile in the Control Tower Region-deny control.
- **Done when:** Decided at the kickoff: US East (N. Virginia), us-east-1, US only. No existing IAM Identity Center instance was reported, which Appendix B still confirms.
- **Design note:** Mitsui's rule is US only, so the Region-deny control blocks non-US Regions. Claude cross-region inference stays inside the US Regions us-east-1, us-east-2 and us-west-2. AgentCore Gateway, Identity and Runtime are available in all three. On day 1 we confirm AgentCore Policy, Claude model access and S3 Tables with Lake Formation in the chosen Region. The Control Tower Region-deny control can block cross-region inference unless the destination Regions are allowed.

### 2.2 Management account access to deploy Control Tower

- **Mitsui provides:** A temporary **cross-account Identity and Access Management (IAM) role** in the management account (Statement of Work (SOW) Assumption 3), created by a Mitsui administrator:
  - Permissions: AdministratorAccess, needed only to launch Control Tower and complete the IAM Identity Center steps.
  - Trust: only the CapNexus AWS account and named CapNexus principals that we supply, with multi-factor authentication (MFA) required and an external ID.
  - Limits: maximum session of 4 hours, expiry within 7 days of creation (extended in writing if needed), and Mitsui reviews the CloudTrail events for the role.
- **Owner:** Matt Schiefelbein and Noah Jackson.
- **Account setup (Noah Jackson, as root user, due Nov 16):** The management account is a new AWS account. Root credentials are never shared with CapNexus. Noah:
  1. Creates the account with a Mitsui-owned root email (a distribution list, separate from the three account emails in item 2.3).
  2. Completes account activation: contact details, payment method and identity verification.
  3. Turns on MFA for the root user and stores the root credentials in Mitsui's vault.
  4. Confirms AWS Organizations is enabled with all features (or lets the Control Tower setup create it), and sends us the account ID.
  5. Creates the cross-account role described above.
- **Why:** Control Tower can only be launched from the Organizations management account. This is the highest-privilege access in the engagement, so it is time-boxed and removed afterwards.
- **How:** At kick-off, CapNexus hands over the account ID, principal Amazon Resource Names (ARNs) and external ID. Mitsui creates the role on day 1 and sends back the role ARN. After the landing zone and the Identity Center sessions are complete, Mitsui deletes the role.
- **How we use it:** To launch Control Tower, create the Workloads organizational unit (OU), and create the POC workload account.
- **Done when:** Landing zone status shows "Active" with Log Archive and Audit accounts.
- **Watch-outs:** After the launch, we need the management account only for short IAM Identity Center tasks (identity source switch, System for Cross-domain Identity Management (SCIM), trusted token issuer, application setup). Plan these as scheduled sessions with a Mitsui admin.

### 2.3 Three account email addresses

- **Owner:** Noah Jackson.
- **Mitsui provides:** Three unique email addresses (separate from the management account's root email), not used by any existing AWS account, for the Log Archive account, the Audit account and the POC workload account.
- **Why:** AWS requires a distinct root email for each account (SOW Assumption 3).
- **How:** Create three distribution lists (for example `aws-wda-logarchive@`, `aws-wda-audit@`, `aws-wda-poc@`) that more than one Mitsui person monitors. Do not use personal mailboxes. Do not use plus-addressing if the mail system does not deliver it.
- **How we use it:** Control Tower and Account Factory create the accounts. Root recovery and AWS notices go to these lists.
- **Done when:** Mitsui confirms all three can receive external mail.

### 2.4 Landing zone pre-flight facts

- **Mitsui provides:** Answers to the questionnaire in Appendix B (organization features, existing accounts, service control policies (SCPs), existing IAM Identity Center, AWS Config, CloudTrail, security services).
- **Why:** Assumption 4 says there is no Control Tower landing zone today. Control Tower still fails or behaves differently when AWS Organizations is not in "all features" mode, when AWS Config trusted access is already enabled in the management account, or when Security Token Service endpoints are inactive in the governed Regions.
- **How:** Mitsui stated at the kickoff that there are no existing accounts, OUs or SCPs to work around. Mitsui's AWS admin completes the remaining questions in Appendix B (Identity Center, AWS Config, CloudTrail, quotas, Marketplace). Because the management account is new, defaults apply (no organization trail, no AWS Config, default quotas). Noah Jackson does not create the Log Archive, Audit and POC accounts by hand, because Control Tower creates them from the emails.
- **How we use it:** We clear conflicts before the launch.
- **Done when:** Questionnaire returned and conflicts resolved.

### 2.5 Organization guardrails and change discipline

- **Mitsui provides:** Existing SCPs or tag policies that apply to the POC OU, and a commitment not to change the organization structure or the controls of the new OUs during the POC.
- **Why:** The acceptance criterion says "the AWS Control Tower landing zone reports no drift, its enabled controls report compliant, and the POC workload account is enrolled." Out-of-band changes cause drift.
- **How:** Mitsui informs its cloud team. We give the list of controls we enable.
- **Done when:** No drift at handover.

### 2.6 Amazon Bedrock model access and quotas

- **Mitsui provides:** An authorized person to complete the one-time Anthropic first-use details (company name, website, intended use) that AWS requires, plus approval of AWS Marketplace permissions for the model subscription if the organization blocks Marketplace actions.
- **Why:** The assistant uses Claude on Bedrock. New accounts also get low default token quotas, which can make a 15-user pilot throttle.
- **How:** We prepare the text. A Mitsui authorized person submits it. Where possible this is done in the management account so it applies to the member accounts.
- **How we use it:** Foundation model access in the workload account, and quota-increase requests filed in Week 1.
- **Done when:** A test invocation of the chosen Claude model succeeds in the POC account, and quotas cover pilot load.

### 2.7 IAM Identity Center enablement and management-account touchpoints

- **Mitsui provides:** Approval to enable an IAM Identity Center **organization instance** in the management account (or confirmation one exists), and a Mitsui administrator for each management-account session.
- **Why:** Trusted identity propagation to Athena and Lake Formation needs an organization instance. IAM Identity Center can only be set up in the management account.
- **How:** Sequence: enable Identity Center, switch identity source to Microsoft Entra ID (item 5.2), create or sync groups, then assign groups to the POC account. Changing the identity source can remove existing assignments, so we do it once, in one scheduled session. The kickoff plan puts Entra federation in Week 3. If the Entra administrator (Matt Schiefelbein) is available earlier we do it earlier, because CapNexus build access and Lake Formation group permissions depend on it.
- **How we use it:** Federated sign-in for CapNexus engineers and users, and the foundation for per-user identity in Athena.
- **Done when:** Identity Center shows Entra users and groups synced and a test sign-in works.

---

## Group 3: Network

### 3.1 Site-to-site VPN

- **Mitsui provides:** The customer gateway details, and a network engineer (Matt Schiefelbein) available during Week 1. The virtual private network (VPN) device is a Palo Alto firewall (kickoff):
  - Public IP address of the on-prem VPN device (static, not behind NAT unless NAT traversal is configured).
  - Palo Alto model and PAN-OS version (so we generate the correct AWS configuration file).
  - Routing type: static routes or Border Gateway Protocol (BGP) (and the autonomous system number (ASN) for BGP).
  - Approval for two tunnels to be established.
- **Why:** AWS Database Migration Service (DMS) must reach the SQL Servers in the data center. Statement of Work (SOW) scope: "the AWS side of a site-to-site VPN to Client's data center". Mitsui configures its side (Assumption 5).
- **How:** The network team sends us the details. We create the AWS side (virtual private gateway, customer gateway, VPN connection) and send the vendor-specific configuration file. The network team applies it and confirms the tunnels are up.
- **How we use it:** The VPN is the only path from AWS to the databases. Only the DMS subnet routes to it, which supports the acceptance criterion that "the assistant has no network path to Client's on-premises databases".
- **Done when:** Both tunnels show UP and a TCP test from the DMS subnet to each SQL Server port succeeds.
- **Design note:** AWS Direct Connect, Transit Gateway and a network hub account are out of scope. Use a virtual private gateway in the workload virtual private cloud (VPC). This item needs the workload account (Week 1 day 2), so the network engineer must be on standby then.

### 3.2 IP address plan

- **Mitsui provides:** The on-prem Classless Inter-Domain Routing (CIDR) ranges that must be reachable (the SQL Server subnets only, not the whole data center), and a non-overlapping CIDR block for the AWS VPC (for example a /24 or /23 from Mitsui's IPAM).
- **Why:** Overlapping ranges break routing. A small range keeps the exposed surface small.
- **How:** Network team assigns the AWS CIDR and lists the on-prem prefixes.
- **Done when:** Ranges recorded and approved.

### 3.3 Firewall rules to the SQL Servers

- **Mitsui provides:** Firewall rules that allow the DMS subnet (the AWS CIDR, narrowed to the replication instance addresses once known) to reach each SQL Server on its TCP port (default 1433).
- **Why:** AWS DMS connects over the VPN. If an instance uses a dynamic port or a named instance, DMS must know the actual port.
- **How:** Provide the server IP, instance name and the fixed port for each of the three databases. Use a static port rather than dynamic ports with SQL Browser (UDP 1434). Allow only the DMS addresses. Block all other AWS-to-on-prem traffic.
- **How we use it:** DMS source endpoints.
- **Done when:** DMS "test connection" succeeds for all three endpoints.

### 3.4 DNS

- **Mitsui provides:** Either IP addresses for the SQL Servers or an on-prem Domain Name System (DNS) server that can resolve their names, and approval for an outbound Route 53 Resolver endpoint to forward queries to it.
- **Why:** If the DMS endpoint uses a server name, AWS needs to resolve it. For SQL Server Always On, the listener name matters.
- **How:** Simplest option: give IP addresses. Otherwise supply DNS server IPs and the domain suffix.
- **Done when:** Name or IP is resolved from the DMS subnet.

### 3.5 Egress, ingress and allow-lists

- **Mitsui provides:**
  1. Confirmation that Mitsui's network and proxy do not block Microsoft Azure Bot Service traffic to our AWS endpoint (inbound to AWS from Microsoft, so normally no Mitsui rule is needed, but Mitsui's web application firewall (WAF) or cloud access security broker (CASB) policies sometimes interfere).
  2. For IT and project management office (IT/PMO) laptops: allow-listing of the AgentCore Gateway hostname (`*.gateway.bedrock-agentcore.<region>.amazonaws.com`) and the Entra sign-in endpoints.
  3. If Mitsui wants the Gateway restricted to the corporate network, say so now. It changes the design.
- **Why:** Claude Code and Claude Desktop call the Gateway from the user's machine (or, depending on the connection method, from Anthropic's cloud, see item 8.1).
- **Done when:** A test call from a Mitsui laptop reaches the Gateway.

---

## Group 4: Source data (MEPWELL, SDEDBPROD, MEPS_ARIES)

### 4.1 Source inventory

- **Mitsui provides:** For each of the three databases: SQL Server version (2017 per the kickoff) and edition, whether Transparent Data Encryption (TDE) or other permission restrictions apply (TDE is transparent to queries, so we do not expect it to affect a full load, but we confirm), hosting (VM or physical, Always On availability group or standalone), instance name and port, collation, recovery model, database size, and the output of the two inventory scripts in Appendix A (table list with row counts and size, and columns with risky data types).
- **Why:** Statement of Work (SOW) sizes are approximate (about 0.2 GB, 10 GB, 5 GB). AWS Database Migration Service (DMS) does not support tables with `sql_variant` columns or sparse columns, and temporal tables and memory-optimized tables are not supported. We need to know before the first load.
- **How:** A database administrator (DBA) runs the scripts and sends back CSV output (names and counts only, no row data).
- **How we use it:** To build DMS table mappings, to size the replication instance and to spot unsupported columns.
- **Done when:** All three inventories received by end of Week 1.

### 4.2 Read-only SQL Server logins

- **Mitsui provides:** One SQL-authenticated login per database (or one login with access to all three), read-only, with the permissions in Appendix A. Mitsui also confirms **mixed-mode authentication** is enabled and sends credentials through the agreed vault.
- **Why:** SOW Assumption 5 requires "read-only SQL Server accounts for all three databases that meet AWS DMS source requirements". For a full-load-only task AWS documents these permissions: `db_datareader`, `VIEW DATABASE STATE` and `VIEW DEFINITION`. AWS DMS does not support NT LAN Manager (NTLM). SQL authentication is therefore the standard route.
- **How:** DBA runs the script in Appendix A. If Mitsui prefers least privilege, grant `SELECT` only on approved tables and views instead of `db_datareader`. We test that DMS works with it.
- **How we use it:** Credentials are stored in AWS Secrets Manager in the POC account (encrypted with a customer-managed Key Management Service (KMS) key) and used only by DMS endpoints.
- **Done when:** DMS test connection and a sample full load succeed.
- **Watch-outs:**
  - Never send `sysadmin` or `db_owner`. Full load does not need them. Change data capture is out of scope.
  - Enable Transport Layer Security (TLS) on the SQL Server connection if possible. Provide the CA certificate if the server certificate is not publicly trusted. Otherwise DMS needs "trust server certificate" and Security must approve.
  - Password expiry: set the login so the password does not expire during the POC, or schedule a rotation.

### 4.3 Approved table list

- **Mitsui provides:** A list, per database, of tables and views approved for copying, restricted tables, and any columns that must be masked (Appendix E1).
- **Why:** The SOW copies "approved tables" only. The list limits risk and keeps the load inside the stated 15.4 GB.
- **How:** Data owners and subject matter experts (SMEs) mark the inventory from item 4.1. Include join-key tables (the MEPWELL well hub and crosswalk) because every cross-database question depends on them.
- **How we use it:** DMS table mappings, Glue Data Catalog, Lake Formation permissions.
- **Done when:** List signed off by data owners by end of Week 2.
- **Watch-outs:** Table and column names in S3 Tables must be lowercase to work with Lake Formation and Glue. We lowercase them and keep a mapping to the source names.

### 4.4 SDEDBPROD currency and geometry

- **Status:** **On hold, no Mitsui owner** (kickoff agenda). A decision and an owner are needed before the first load in Week 2 (Mon Nov 23).
- **Mitsui provides:** One of the following (SOW Assumption 2), plus the geographic information system (GIS) administrator's agreement on schedule:
  - **Option 1:** A scheduled job that **compresses the geodatabase to state 0** before each daily load, so the base tables reflect current edits.
  - **Option 2:** Read access for the DMS login to **versioned views** (the `_evw` views) so reads reflect the DEFAULT version.
  
  Mitsui also states how geometry is stored (SQL Server `geometry`, `geography`, or legacy SDE binary) and the list of feature classes that are registered as versioned.
- **Why:** In a versioned ArcGIS enterprise geodatabase, recent edits sit in delta tables until compressed. Reading base tables without compressing gives stale data. DMS also supports views for full-load-only tasks.
- **How (Option 1):** The GIS administrator uses the geodatabase Compress tool (for example from an ArcPy scheduled task) as the geodatabase administrator. Compression to state 0 requires that editors have posted their edits to DEFAULT, that unneeded versions are reconciled and deleted, and that no conflicting connections are open. Schedule it before the load window (item 4.5).
- **How (Option 2):** GIS administrator creates read access for the DMS login on the `_evw` views and tells us the view names.
- **How we use it:** DMS table mappings point to the base tables (Option 1) or the views (Option 2).
- **Done when:** A test load shows a known recent edit in the AWS copy.
- **Watch-outs:** Shape columns are copied only as text where DMS supports the type. DMS converts `geometry` and `geography` to character large object (CLOB) for targets that do not support them, and does not support them in full-LOB mode, so we use limited-LOB mode with a size cap. Very large shapes can be truncated. Ask the GIS administrator for the largest shape size. Map rendering and ArcGIS integration are out of scope.

### 4.5 Load window and source impact

- **Status:** The load window and blackout periods were blank at the kickoff.
- **Mitsui provides:** An approved daily window (for example 1:00 to 4:00 AM Central, after the GIS compress job), and whether a read-only replica or readable secondary replica is available.
- **Why:** A daily full load reads every approved table. About 15 GB over the virtual private network (VPN) is a modest transfer but it can compete with batch jobs. If an Always On readable secondary exists, we can read from it with application intent read-only to avoid load on production.
- **How:** DBA states the window, known blackout periods (month-end close, ARIES batch jobs) and whether a secondary is available.
- **How we use it:** We schedule the DMS task and tune parallelism.
- **Done when:** Window agreed, first scheduled load runs.
- **Watch-outs:** DMS may mark a full-load task complete after a connection loss even if the data is incomplete, so we add row-count checks and an alarm. The SOW needs the load to run unattended for the final two weeks, so Mitsui should avoid maintenance on the source servers or the VPN in that period, or tell us beforehand.

### 4.6 Data dictionary, join keys and business context

- **Mitsui provides:** Existing documentation: entity-relationship (ER) diagrams, data dictionaries, ARIES table guides, and a written explanation of how wells are identified across databases (American Petroleum Institute (API) number format, unique well identifier (UWI), ARIES property IDs, crosswalk table logic).
- **Why:** The assistant joins MEPWELL, SDEDBPROD and MEPS_ARIES "on well identifiers". Without the crosswalk rules, joins will be wrong and question accuracy falls below the 80% target.
- **How:** SMEs send documents or walk us through the model in a working session in Week 1.
- **How we use it:** Table and column descriptions in the Glue Data Catalog (Deliverable 3), prompt context, and example queries.
- **Done when:** Join paths for all three database pairs are written down and reviewed by an SME.

---

## Group 5: Identity (Microsoft Entra ID and IAM Identity Center)

### 5.1 Entra ID administrator

- **Mitsui provides:** The Entra administrator (Matt Schiefelbein) available for scheduled sessions in Week 1 to Week 3 with these rights: Application Administrator or Cloud Application Administrator (to create the enterprise application and app registrations), and a Global Administrator or Privileged Role Administrator for tenant-wide admin consent.
- **Why:** Statement of Work (SOW) Assumption 5: "a Microsoft Entra ID administrator for the enterprise application, federation, and group mapping". Only a tenant admin can do these steps.
- **How:** The admin joins three working sessions with us: (1) federation and System for Cross-domain Identity Management (SCIM), (2) groups and app registrations, (3) token and trusted-issuer testing.
- **Done when:** Items 5.2 to 5.6 are complete.

### 5.2 Enterprise application, SAML federation and SCIM provisioning

- **Mitsui provides:** The **AWS IAM Identity Center** gallery application in Entra, configured for Security Assertion Markup Language (SAML) single sign-on and automatic (SCIM) provisioning, with the pilot groups assigned.
- **Why:** Entra ID is the identity source. Federation lets users sign in with their Mitsui account. SCIM keeps users and groups in sync so Lake Formation can grant access by Entra group.
- **How (Mitsui Entra admin, with us on the call):**
  1. In IAM Identity Center, choose **External identity provider** as the identity source. Download the service-provider metadata (ACS URL, issuer).
  2. In Entra, add the AWS IAM Identity Center application. Under single sign-on choose SAML and upload that metadata. Download the Entra federation metadata XML and upload it to Identity Center.
  3. In Identity Center, turn on automatic provisioning. Copy the SCIM endpoint and access token. The token is valid for one year, so set a renewal reminder.
  4. In Entra, set provisioning mode to Automatic, paste the endpoint and token, test the connection, set scope to "Sync only assigned users and groups", assign the groups from item 5.3, and start provisioning.
- **How we use it:** Sign-in for CapNexus engineers and for users, and the groups referenced in Lake Formation and AgentCore.
- **Done when:** A test user signs in to the AWS access portal through Entra, and a group member appears in Identity Center within one provisioning cycle (about 40 minutes, or use on-demand provisioning for testing).
- **Watch-outs:**
  - Assigning groups to enterprise applications and automatic provisioning typically need Entra ID P1 or higher. Microsoft licensing is excluded from the SOW, so Mitsui should confirm it has this.
  - The user principal name (UPN) should equal the primary email, because we map the token claim to the Identity Center user (item 5.4).
  - Do the identity-source switch once, right after the landing zone launch (item 2.7).

### 5.3 Security groups and membership

- **Mitsui provides:** Entra security groups, with membership, using these proposed names (Mitsui may rename):

| Group | Purpose | Members |
|---|---|---|
| `sg-wda-capnexus-engineers` | Build access in the POC workload account | CapNexus guests (5 roles) |
| `sg-wda-admins` | Mitsui administrators of the POC (dashboards, audit logs) | Mitsui IT |
| `sg-wda-users-well` | Read MEPWELL tables | Pilot users |
| `sg-wda-users-geo` | Read SDEDBPROD tables | Pilot users with geographic information system (GIS) need |
| `sg-wda-users-econ` | Read MEPS_ARIES tables | Pilot users with economics need |
| `sg-wda-econ-sensitive` | See the unmasked column (item 6.2) | Small subset |
| `sg-wda-itpmo-tools` | Use data tools from Claude Code and Claude Desktop | IT and project management office (IT/PMO) users |

- **Why:** Lake Formation grants "permissions by Microsoft Entra ID group". The acceptance criterion needs a user outside the permitted groups to be unable to see restricted tables or the masked column.
- **How:** Entra admin creates assigned (not dynamic, for now) security groups, and assigns them to the Identity Center enterprise application. Nested groups are not synced by SCIM, so use flat membership.
- **Done when:** Groups appear in Identity Center.

### 5.4 App registrations, token claims and trusted token issuer

- **Mitsui provides:** Three app registrations in Mitsui's tenant, with admin consent:

| App registration | Purpose | Key settings |
|---|---|---|
| `WDA-API` | The protected resource. Defines the audience and scope for tokens accepted by AgentCore Gateway. | Application ID URI and one delegated scope, for example `access_as_user`. |
| `WDA-TeamsBot` | Identity of the Teams bot. Referenced by the Azure Bot resource (item 7.1). | **Single tenant.** Client secret or certificate (stored in AWS Secrets Manager). Teams single sign-on: pre-authorize the Microsoft Teams desktop/mobile and web client IDs listed in Microsoft's documentation. |
| `WDA-Clients` | Public client for Claude Code and Claude Desktop. | Allow public client flows. Redirect URIs supplied by CapNexus after we confirm the connection method (Claude Code uses a localhost loopback). Delegated permission on the `WDA-API` scope. |

  Also: add optional claims (`email`, `upn`, and `groups` limited to groups assigned to the application, to avoid the 200-group overage).
- **Why:** AgentCore Identity and Gateway validate a signed-in user's Entra token and pass it through to Athena and Lake Formation, so each query runs as the person who asked. Entra does not support dynamic client registration, so Claude clients must use a pre-registered client ID.
- **How we use it:** We configure the Gateway JSON Web Token (JWT) authorizer with the tenant's OpenID Connect discovery URL and the `WDA-API` audience. In IAM Identity Center we create a **trusted token issuer** for the Entra tenant, mapping the token's `email` (or `oid`) claim to the Identity Center user, then use it for trusted identity propagation through Athena and Lake Formation.
- **Done when:** A Mitsui test user obtains a token for `WDA-API`, and the claims contain the expected `email` and group values.
- **Watch-outs:** SOW Assumption 8: if per-user identity cannot be carried through to Athena within the POC, the pilot runs on permissions by Entra group. The acceptance criterion "every question traces to a named user" still has to hold, so we log the user at the application layer in that case. Ask Mitsui to confirm it accepts this fallback now.

### 5.5 Conditional Access and MFA review

- **Mitsui provides:** The Conditional Access policies that apply to the new apps (multi-factor authentication (MFA), compliant device, sign-in frequency, location, device-code flow blocking, token protection) and exceptions needed for the test users.
- **Why:** Policies that block loopback or device-code sign-in, or that require a managed device, will break Claude Code or Claude Desktop sign-in. They also affect the Teams single sign-on (SSO) token exchange.
- **How:** Mitsui uses Conditional Access assigned by group (kickoff). Matt Schiefelbein lists the policies and groups that apply to the pilot users, test users and IT/PMO users, and which policies include "All cloud apps".
- **Done when:** Test sign-in from a Mitsui-managed laptop works.

### 5.6 Test users

- **Mitsui provides:** At least three Entra test users (with Teams licenses and mailboxes where needed): User A is in all permitted groups, User B is in permitted groups but not `sg-wda-econ-sensitive`, User C is in none of the groups.
- **Why:** The read-only and permission tests in Deliverable 9 need real users: "a user outside a permitted Entra ID group cannot see restricted tables or the masked column, whether they ask through Teams or through Claude Code or Claude Desktop".
- **Done when:** Users exist, can sign in and are in the groups described.

---

## Group 6: Data governance

### 6.1 Table and column descriptions

- **Mitsui provides:** Subject matter expert (SME) review of table and column descriptions for all approved tables: one or two plain sentences per table, descriptions for the columns used in the 30 questions, units (barrels, mcf, USD), code lists (status, well type), and caveats (known data quality problems, date semantics).
- **Why:** Statement of Work (SOW) Data governance and Deliverable 3: "table and column descriptions written with Client's subject matter experts". These descriptions feed the `describe_columns` tool and are the main input the model uses to write correct SQL.
- **How:** We pre-fill the sheet (Appendix E2) from table names, data types and documents. SMEs correct and complete it in Week 2 to Week 4.
- **How we use it:** Written into the Glue Data Catalog as table and column comments.
- **Done when:** SMEs confirm the descriptions for all tables used in the question set.

### 6.2 Restricted tables, masked column and group mapping

- **Mitsui provides:** (a) at least one column to mask, for example an owner or royalty field, a price assumption, or a reserves value; (b) which Entra group may see the unmasked value; (c) tables restricted to specific groups.
- **Why:** SOW: "column masking demonstrated on at least one column". Acceptance: a user outside the permitted group "cannot see restricted tables or the masked column".
- **How:** Data owners fill the access matrix in Appendix E3.
- **How we use it:** Lake Formation permissions and data filters per group.
- **Done when:** Matrix signed off by Noah Jackson (tables) and Matt Schiefelbein (groups) in Week 3. The masked column and the classification rules for royalty owner, lessor and other sensitive data were blank at the kickoff.

---

## Group 7: Microsoft Teams and Azure

### 7.1 Azure subscription and Azure Bot registration

- **Mitsui provides:** An Azure subscription (or a resource group in an existing one) in Mitsui's tenant, and either Contributor rights on that resource group for one CapNexus engineer or an Azure admin who creates the resource using our steps.
- **Why:** Statement of Work (SOW) scope: "Azure Bot Service registration". New bots must be single tenant or use a managed identity, and the Azure Bot resource lives in an Azure subscription. The free pricing tier is sufficient. The subscription is Mitsui's, so there is no CapNexus cost.
- **How:** Create an Azure Bot resource with app type **Single Tenant**, linked to the `WDA-TeamsBot` registration, enable the Microsoft Teams channel, and set the messaging endpoint to the HTTPS URL we supply (`.../api/messages`).
- **How we use it:** The bot receives channel messages, forwards them to the AgentCore Runtime, and replies with a short table and the SQL.
- **Done when:** "Test in Web Chat" in the Azure portal returns a reply from our endpoint.
- **Design note:** The bot secret is kept out of code. Rotate or use a certificate. The messaging endpoint is an internet-facing AWS endpoint (item 1.3 and 3.5). Protect it with JSON Web Token (JWT) validation of Bot Framework tokens and AWS web application firewall (WAF).

### 7.2 Teams administrator approval for one pilot channel

- **Mitsui provides (by start of Week 3):**
  1. A Team and **standard** channel for the pilot (suggested name "Well Data Assistant Pilot"), with a named owner.
  2. Approval, in the Teams admin center, to use a custom app: either upload our app package (we provide a zip with the manifest and icons) to the organization's app catalog, or allow the team owner to upload custom apps.
  3. App permission and setup policies that allow the pilot users to use the app.
  4. The bot added to the channel.
- **Why:** SOW Assumption 6: "Teams administrator approval for one channel by the start of week three (3)". Many tenants block custom apps by default.
- **How:** Teams admin: Manage apps, upload the package, set it to Allowed; check Permission policies and Setup policies for the pilot users; confirm "Allow interaction with custom apps" is on.
- **Done when:** A pilot user posts a message in the channel and receives a reply.
- **Watch-outs:** Teams retention policies apply to messages in the channel, including the bot's answers. Mitsui's compliance team should know. Private and shared channels have limited bot support, so use a standard channel and limit Team membership to pilot and test users.

### 7.3 Channel membership

- **Mitsui provides:** The list of pilot users and test users added to the Team (see item 9.3), and CapNexus testers as guests.
- **Done when:** Membership matches the groups in item 5.3.

---

## Group 8: IT/PMO access through Claude Code and Claude Desktop

### 8.1 Device readiness, network and data-flow approval

- **Mitsui provides:** Install rights for Claude Desktop and Claude Code on pilot laptops, any proxy or TLS-inspection settings (a corporate root CA may need to be trusted by Claude Code), and Security's acceptance of the data flow: rows returned by the data tools reach the Claude client and the model provider it uses.
- **Why:** The Gateway is called from the user's machine. For Claude Desktop remote connectors, requests may be sent from Anthropic's cloud, in which case the Gateway must be reachable from the internet and protected by the JSON Web Token (JWT) authorizer. We confirm the method in Week 3.
- **How:** Row limits (set by AgentCore Policy) and Lake Formation permissions limit what a client can pull. Mitsui Security decides if that is acceptable.
- **Done when:** Written approval of the connection method.

### 8.2 IT/PMO pilot users

- **Mitsui provides:** The names and emails of the IT and project management office (IT/PMO) users, all in `sg-wda-itpmo-tools`, including at least two who run the acceptance test.
- **Done when:** Users listed by Week 3.

---

## Group 9: SMEs, question set, pilot and acceptance

### 9.1 Subject matter experts

- **Mitsui provides:** Named subject matter experts (SMEs) covering well data, geodatabase data and ARIES economics data (Statement of Work (SOW) Assumption 6), available from Week 1.
- **Why:** SMEs write the question set, supply descriptions, and judge answers. The 80% acceptance threshold is "as judged by Client's subject matter experts", so their participation is a hard dependency.
- **Suggested sequence:** Week 1 data-model session. Week 1 to Week 3 question writing. Week 2 to Week 4 descriptions. Week 4 to Week 6 answer validation.
- **Done when:** SMEs are named in the risks, assumptions, issues and dependencies (RAID) log.

### 9.2 Question set of about 30 questions

- **Mitsui provides:** The outline in Week 1 (Deliverable 1) and the full set by Week 3 to Week 4: about 30 plain-English business questions, each with expected answer, the date the answer is valid for, tables involved, and the SME who owns it.
- **Why:** Acceptance: "At least 80% of the agreed question set... is answered correctly" (24 of 30).
- **Suggested mix:** about 7 questions on each database alone and about 9 that join two or three databases on well identifiers.
- **How:** SMEs obtain expected answers from their own tools (ARIES, ArcGIS, well reports) or a reference SQL query, and record the data date. Agree the scoring rule up front: correct means the numbers match the expected answer within the stated tolerance.
- **How we use it:** To tune prompts and to run the evaluation report (Deliverable 9).
- **Done when:** The question set is signed off by the SMEs and frozen.
- **Approach:** We hold back about 10 questions from tuning so the final score is a fair measure. Because data reloads daily, freeze expected answers to a snapshot date or write questions about historical data.

### 9.3 Pilot users

- **Mitsui provides:** About 15 pilot users, active in Week 6 (SOW Assumption 6), named by Week 4 so they are in the Entra groups, in the Team and trained. Include a mix of well engineers, geographic information system (GIS) staff and economics analysts.
- **Why:** The acceptance criteria on response time, audit trail and permission behavior need real usage.
- **How:** Noah Jackson nominates users. CapNexus gives a 30-minute enablement session and a one-page guide in Week 5. Ask each user to try at least five questions a week and report wrong answers in the shared channel.
- **Done when:** All pilot users complete at least one question.

### 9.4 UAT, acceptance and final validation

- **Mitsui provides:** Noah Jackson as the acceptance owner (kickoff decision) who signs or rejects deliverables, user acceptance testing (UAT) testers, and written rejection reasons that cite how a deliverable does not meet the SOW.
- **Why:** Per the SOW: Mitsui has **8 business days** to accept or reject each deliverable, and a deliverable is accepted if the period ends with no written rejection. UAT support runs 2 continuous weeks from delivery to the test environment (Terms 2). Mitsui is responsible for final validation before any production change (Assumption 14).
- **How:** We deliver in stages, so reviews overlap. The core build must reach the Mitsui test environment by end of Week 4 so UAT finishes by end of Week 6.
- **Acceptance evidence matrix:**

| Acceptance criterion | Evidence we produce | Mitsui verifier |
|---|---|---|
| 80% of the question set correct | Evaluation report with per-question results | SMEs |
| Every write attempt refused by AgentCore Policy and Lake Formation; no network path to on-prem | Write-attempt test log; route table and firewall rule export | InfoSec, Network |
| Out-of-group user cannot see restricted tables or the masked column (Teams and Claude) | Test results for User A, B and C | InfoSec, Data owners |
| Every pilot question traces to a named user, SQL and row count | Audit log samples | IT, InfoSec |
| Typical answers in Teams within 60 seconds | Latency report from the dashboard | Pilot lead |
| Daily load runs unattended for the final 2 weeks | AWS Database Migration Service (DMS) task history, alarm history | Database administrators (DBAs), IT |
| IT and project management office (IT/PMO) can list, describe, sample and SELECT from Claude | Recorded test sessions | IT/PMO lead |
| Control Tower: no drift, controls compliant, account enrolled | Control Tower console export | AWS org owner |

---

## Group 10: Observability, handover and readout

### 10.1 Audit and logging policy

- **Mitsui provides:** Confirmation that default retention is acceptable (kickoff decision: no requirement beyond defaults), who may read the audit logs and Bedrock invocation logs, the alarm distribution list (email), and confirmation that employee questions may be logged.
- **Why:** Statement of Work (SOW): "a trail of every question, tool call, SQL statement, user, time and result size". Bedrock invocation logs can hold prompts and answer text, so they contain business data and may be subject to privacy or human resources (HR) rules.
- **How:** We record the default retention settings in the runbook. InfoSec confirms access. We encrypt logs with the customer-managed Key Management Service (KMS) key and restrict access with Lake Formation or Identity and Access Management (IAM).
- **Done when:** Policy approved and alarm recipients receive a test alarm.

### 10.2 Handover recipients and post-POC state

- **Mitsui provides:** The IT operations owner who receives the runbook and code, attendees for a knowledge-transfer session, and a decision on what happens to the AWS resources after the readout.
- **Why:** Deliverable 11 is a handover of code, configuration and a runbook. Support after the readout is out of scope, but AWS consumption continues if the resources stay on.
- **How:** Mitsui decides: keep running, pause, or tear down (our infrastructure as code supports teardown). CapNexus removes its own access at handover.
- **Done when:** Handover session held and CapNexus access removed.

### 10.3 Readout attendees and next-phase input

- **Mitsui provides:** Decision-makers for the readout and their priorities for the next phase.
- **Why:** The out-of-scope list (application API tools such as Quorum, QLS/LIS, accounting or cost data, Oracle sources, querying in place, geospatial, production hardening) is the likely next phase. Deliverable 10 includes a next-phase recommendation.
- **Done when:** Readout held by end of Week 6.

---

## 5. Risks and dependencies

| # | Risk | Impact | Mitigation | Owner |
|---|---|---|---|---|
| 1 | Identity propagation to Athena and Lake Formation may not complete in the POC. | Permission model falls back to Entra groups (Assumption 8). | Confirm fallback is acceptable. Log the user at the application layer so the audit criterion still holds. | Solution Architect |
| 2 | Holiday and year-end freezes. | Week-1 dependencies slip and the 2-week unattended-load window is lost. | Agree freeze dates now (item 1.2). | Noah Jackson |
| 3 | Region choice is hard to undo. | Rework of landing zone. | Decided at the kickoff: us-east-1, US only. Not revisited (item 2.1). | Mitsui, CapNexus |
| 4 | Low Bedrock quotas on a new account. | Throttling during pilot. | File quota requests in Week 1, involve the AWS account team. | Data & Platform Engineer |
| 5 | Region-deny control blocks cross-region inference. | Model calls fail. | Allow the inference-profile destination Regions in the control. | Solution Architect |
| 6 | SQL Server is Windows-authentication only. | No AWS Database Migration Service (DMS) source login. | Mixed mode, approved in change window (item 4.2). | Database administrator (DBA) |
| 7 | SDEDBPROD copy shows stale edits. | Wrong answers on geographic information system (GIS) questions. | Compress to state 0 or versioned views (item 4.4). | GIS admin |
| 8 | Large shape columns truncated in text form. | Incomplete geometry text. | Out of scope for analysis. Document the size cap. | Data & Platform Engineer |
| 9 | DMS marks a full load complete after a connection drop. | Partial data unnoticed. | Row-count checks after each load, with an alarm. | Data & Platform Engineer |
| 10 | S3 Tables need lowercase names. | Names differ from source. | Lowercase with a mapping table. | Data & Platform Engineer |
| 11 | Teams custom app policy blocks the bot. | Channel go-live slips past Week 3. | Open the Teams admin request in Week 1 (item 7.2). | Teams admin |
| 12 | Entra P1 not licensed. | No group assignment or System for Cross-domain Identity Management (SCIM) provisioning. | Confirm early. Microsoft licensing is excluded from the Statement of Work (SOW). | Entra admin |
| 13 | Claude Desktop remote connectors may call from Anthropic's cloud. | Gateway must be reachable from the internet. | JWT-protected Gateway, approval by InfoSec (item 8.1). | InfoSec |
| 14 | Subject matter experts (SMEs) are not available when needed. | Question set and the 80% judgment slip. | Weekly check; escalate to Noah Jackson. | Pilot lead |
| 15 | User acceptance testing (UAT) is 2 weeks and the Review Period is 8 business days. | Acceptance runs beyond Week 6 (Period of Performance is the later of acceptance or 8 weeks). | Stage deliveries; core build to test environment by end of Week 4. | CapNexus Engagement Manager |
| 16 | Logs contain question text and business data. | Privacy or confidentiality concern. | Retention and access policy (item 10.1). | InfoSec |
| 17 | AgentCore Policy, S3 Tables with Lake Formation, and identity-aware Athena workgroups may be limited in the chosen Region or have constraints. | Design changes. | Confirm on day 1 (item 2.1). | Solution Architect |
| 18 | SDEDBPROD load approach is on hold with no owner. | Stale or missing geodatabase data at the first load (Mon Nov 23). | Name an owner and decide before Week 2 (item 4.4). | Noah Jackson |
| 19 | Daily load window is undefined. | Load runs compete with batch jobs, or fail in a blackout. | Agree the window in Week 2 (item 4.5). | Noah Jackson |

---

## 6. Questions still open after the kickoff

1. For the new management account: what are the account ID and root email, is activation complete (payment method, verification), is root multi-factor authentication (MFA) on, and is AWS Organizations enabled with all features (item 2.2)?
2. What is the SDEDBPROD approach (compress to state zero or versioned views), and who owns it (item 4.4)?
3. What is the daily load window, and what are the source blackout periods (item 4.5)?
4. Are all three SQL Server 2017 instances on mixed-mode authentication, and which have a readable secondary? Does Transparent Data Encryption (TDE) apply (items 4.1, 4.2)?
5. How is geometry stored in SDEDBPROD (item 4.4)?
6. Which column is masked, and what are the classification rules for royalty owner, lessor and other sensitive data (item 6.2)?
7. Who are the database administrators (DBAs), geographic information system (GIS) administrator, Azure administrator, InfoSec reviewer, subject matter experts (SMEs) and IT and project management office (IT/PMO) lead (item 1.1)?
8. Is Entra ID P1 or higher licensed, and does the user principal name (UPN) equal the primary email for all users? Which Conditional Access groups and policies apply (items 5.2, 5.5)?
9. Does Mitsui allow custom Teams apps today? Is Azure available for the Azure Bot resource (items 7.1, 7.2)?
10. Is a change advisory board (CAB) ticket required for virtual private network (VPN), firewall, SQL login and Entra changes, and how long does it take (item 1.2)?
11. Where should the infrastructure-as-code repository and pipeline live for handover (item 1.7)?
12. What happens to the AWS resources after the readout (item 10.2)?

---

## Appendix A: SQL Server scripts for Mitsui DBAs

Run these in SQL Server Management Studio. All results are metadata only (names, counts, sizes). Do not send row data.

### A1. Instance facts

```sql
SELECT @@VERSION AS sql_version;
SELECT SERVERPROPERTY('Edition')              AS edition,
       SERVERPROPERTY('IsHadrEnabled')        AS always_on_enabled,
       SERVERPROPERTY('IsIntegratedSecurityOnly') AS windows_auth_only; -- 1 = Windows-only; mixed mode needed
SELECT name, recovery_model_desc, compatibility_level, is_read_only
FROM sys.databases
WHERE name IN ('MEPWELL','SDEDBPROD','MEPS_ARIES');
```

### A2. Read-only login for AWS DMS (full load only)

Run once on the instance, then in each database. Replace the password placeholder with a generated value and send it through the agreed vault, not email.

```sql
USE master;
CREATE LOGIN dms_wda_ro WITH PASSWORD = '<generated-password>', CHECK_POLICY = ON, CHECK_EXPIRATION = OFF;

-- Repeat for MEPWELL, SDEDBPROD and MEPS_ARIES:
USE MEPWELL;
CREATE USER dms_wda_ro FOR LOGIN dms_wda_ro;
ALTER ROLE db_datareader ADD MEMBER dms_wda_ro;   -- or GRANT SELECT on approved tables only
GRANT VIEW DATABASE STATE TO dms_wda_ro;
GRANT VIEW DEFINITION     TO dms_wda_ro;
```

Check the login is not privileged:

```sql
SELECT IS_SRVROLEMEMBER('sysadmin', 'dms_wda_ro') AS is_sysadmin;   -- expect 0
```

These are the permissions AWS documents for AWS Database Migration Service (DMS) tasks that only do a full load. Change data capture is out of scope, so no `db_owner`, `sysadmin` or `VIEW SERVER STATE` is requested.

### A3. Table inventory (run in each database)

```sql
SELECT s.name AS schema_name, t.name AS table_name,
       SUM(CASE WHEN p.index_id IN (0,1) THEN p.rows ELSE 0 END) AS row_count,
       CAST(SUM(a.total_pages) * 8 / 1024.0 AS DECIMAL(18,2))    AS size_mb
FROM sys.tables t
JOIN sys.schemas s     ON s.schema_id = t.schema_id
JOIN sys.indexes i     ON i.object_id = t.object_id
JOIN sys.partitions p  ON p.object_id = i.object_id AND p.index_id = i.index_id
JOIN sys.allocation_units a
     ON (a.type IN (1,3) AND a.container_id = p.hobt_id)
     OR (a.type = 2      AND a.container_id = p.partition_id)
GROUP BY s.name, t.name
ORDER BY size_mb DESC;
```

### A4. Columns that need attention (run in each database)

```sql
SELECT s.name AS schema_name, t.name AS table_name, c.name AS column_name,
       ty.name AS type_name, c.max_length, c.is_sparse
FROM sys.columns c
JOIN sys.tables  t  ON t.object_id = c.object_id
JOIN sys.schemas s  ON s.schema_id = t.schema_id
JOIN sys.types   ty ON ty.user_type_id = c.user_type_id
WHERE ty.name IN ('sql_variant','geometry','geography','hierarchyid','xml','image','text','ntext','datetimeoffset')
   OR c.is_sparse = 1
   OR c.max_length = -1
ORDER BY s.name, t.name, c.column_id;
```

Also report any tables that use temporal (system-versioned) tables, memory-optimized tables, column-level encryption or Always Encrypted. DMS does not support these.

### A5. SDEDBPROD extras (GIS administrator)

- List of feature classes and tables to copy, and whether each is registered as versioned.
- Geometry storage type per feature class (SQL Server geometry, geography, or legacy SDE binary). `sde.SDE_geometry_columns` and the ArcGIS Catalog properties show this.
- Name of the compress job (or the versioned view names) and its schedule.

---

## Appendix B: AWS organization pre-flight questionnaire

| # | Question | Mitsui answer |
|---|---|---|
| 1 | Is AWS Organizations enabled with **all features**? Management account ID? | New account created by Noah Jackson (Nov 16). Organizations status and account ID to confirm. |
| 2 | Number and names of existing member accounts. Any named "Audit" or "Log Archive"? | None to work around (kickoff). Confirm. |
| 3 | Is there an existing AWS Control Tower landing zone (Statement of Work (SOW) says no)? | No (SOW Assumption 4, confirmed at the kickoff) |
| 4 | Is IAM Identity Center enabled? In which Region? Identity source? | |
| 5 | Is AWS Config trusted access enabled for the organization? Any existing Config recorder or delivery channel in the management account? | |
| 6 | Is there an organization CloudTrail trail? Other security tooling (GuardDuty, Security Hub, Macie)? | |
| 7 | Existing service control policies (SCPs), and which organizational units (OUs) they attach to. Any Region restriction? | No existing SCPs (kickoff). Region restriction: US only. |
| 8 | Are AWS STS endpoints active in the Regions we will govern? | |
| 9 | Is AWS Marketplace access allowed for the member accounts? | |
| 10 | Who receives root-account notices and who is the billing contact? | |
| 11 | Required tags, naming standards, Key Management Service (KMS) and encryption standards? | |
| 12 | Existing AWS service quotas that might be limiting in the management account? | New account, default quotas. |
| 13 | Is there an existing AWS-to-on-prem network (virtual private network (VPN), Direct Connect)? | |

---

## Appendix C: Network information sheet

| Item | Value |
|---|---|
| Customer gateway device (make, model, firmware) | Palo Alto (kickoff). Model and PAN-OS version to confirm. |
| Customer gateway public IP | |
| Routing (static or Border Gateway Protocol (BGP); autonomous system number (ASN)) | |
| On-prem CIDRs to reach (SQL Server subnets only) | |
| AWS virtual private cloud (VPC) Classless Inter-Domain Routing (CIDR) assigned by Mitsui | |
| SQL Server IP / name, instance, fixed TCP port: MEPWELL | |
| SQL Server IP / name, instance, fixed TCP port: SDEDBPROD | |
| SQL Server IP / name, instance, fixed TCP port: MEPS_ARIES | |
| Domain Name System (DNS) servers and domain suffix (if names are used) | |
| Network engineer and backup (Week 1 availability) | Matt Schiefelbein. Backup to be named. |
| Change advisory board (CAB) ticket numbers | |

---

## Appendix D: Entra, Teams and Azure checklist (Mitsui administrators)

**Entra ID**
- [ ] Administrator available for three sessions in Week 1 to Week 3 (item 5.1)
- [ ] AWS IAM Identity Center enterprise application: Security Assertion Markup Language (SAML) configured, provisioning on (item 5.2)
- [ ] Security groups created and assigned to the application (item 5.3)
- [ ] App registrations `WDA-API`, `WDA-TeamsBot`, `WDA-Clients` created, admin consent granted (item 5.4)
- [ ] Optional claims added (`email`, `upn`, `groups`)
- [ ] Conditional Access policies reviewed (item 5.5)
- [ ] Test users A, B and C created (item 5.6)
- [ ] Guest accounts for the five CapNexus roles

**Azure**
- [ ] Subscription or resource group named (item 7.1)
- [ ] Azure Bot resource (single tenant) created with the Teams channel enabled
- [ ] Messaging endpoint set to the CapNexus-supplied URL

**Teams**
- [ ] Team and standard channel created, owner named (item 7.2)
- [ ] Custom app upload allowed or package uploaded to the org catalog
- [ ] Permission and setup policies allow pilot users
- [ ] Bot added to the channel, test message answered

---

## Appendix E: Templates

### E1. Approved table list (item 4.3)

| Database | Schema | Table or view | Rows | Size MB | Decision (Approved / Approved with masking / Not approved) | Allowed groups | Notes | Data owner |
|---|---|---|---|---|---|---|---|---|

### E2. Description sheet (item 6.1)

| Database | Table | Table description | Column | Column description | Unit | Code values or format | Caveats | Subject matter expert (SME) reviewer |
|---|---|---|---|---|---|---|---|---|

### E3. Masking and access matrix (item 6.2)

| Database | Table | Column (if masked) | Masking rule | Groups with full access | Groups with masked access | Groups with no access |
|---|---|---|---|---|---|---|

### E4. Question set (item 9.2)

| ID | Question (plain English) | Databases involved | Tables | Expected answer | Data date | Tolerance | SME owner | Difficulty (single / join) |
|---|---|---|---|---|---|---|---|---|

---

*Sources checked for technical statements:* AWS Database Migration Service (DMS) user guide (SQL Server as a source: full-load permissions, NT LAN Manager (NTLM) limitation, views, geometry handling; Amazon S3 as a target: CSV and Parquet only, no S3 Tables target), AWS Control Tower prerequisites (Region alignment with IAM Identity Center, AWS Config trusted access, STS endpoints), AWS IAM Identity Center trusted identity propagation with Athena, AWS Amazon S3 Tables integration notes (lowercase names), Amazon Bedrock AgentCore supported Regions, and Microsoft Azure Bot Service documentation (multi-tenant bot creation deprecated after July 31, 2025). CapNexus re-confirms Region and service availability against current vendor documentation at kick-off.
