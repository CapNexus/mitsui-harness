# Well Data Assistant POC: End-to-End Feature List

Mitsui E&P USA and CapNexus, SOW Mitsui.CapNexus.SOW2026001.

Sources read: SOW (PDF), Client Dependencies and Sharing Strategy rev 1.6, Kickoff Agenda (decisions log and discovery answers), `adr/WDA-POC-Data-Workflow.md`, `adr/WDA-POC-Architecture.drawio` (all labels), and the week 1 to 6 task list. Where the documents differ, the task list wins, as agreed.

## 1. How to read this document

- Each feature maps to one or more SOW deliverables (D1 to D11) and can be tested on its own. Section 4 gives the cross-feature end-to-end scenarios.
- Every feature lists the dependencies it needs. Each dependency (DEP-nn) is defined once in Section 3 with why it blocks us and the steps to resolve it. Features repeat only the dependency ID and a one-line reason.
- Step IDs (D1 to D8, Q1 to Q9, C1, I1 to I3, A1 to A2) are from the data workflow document.
- Dates follow the task list, except the unattended-load window. Decided Nov 17: the window is Mon Dec 14 to Fri Dec 25 (the Dependencies doc dates), not Dec 7 to Dec 18. The task list (md files and xlsx) and the workflow doc were updated to match on Nov 17.

## 2. Features

### Feature map

| ID | Feature | SOW deliverable | Due (task list) |
|---|---|---|---|
| [F1](#f1) | Mobilization, plan and governance | D1 | Fri Nov 20 |
| [F2](#f2) | AWS landing zone and POC account as code | D2 | Thu Nov 19 to Fri Nov 20, drift check Dec 17 |
| [F3](#f3) | Private connectivity (VPN and PrivateLink) | D2 | Mon Nov 23 |
| [F4](#f4) | Daily one-way data copy into S3 Tables | D3 | First loads Nov 25, stable Dec 11 |
| [F5](#f5) | Data catalog with SME descriptions | D3 | Dec 10 |
| [F6](#f6) | Identity federation (Entra to AWS) | D4 | Dec 1 to Dec 2 |
| [F7](#f7) | Data access control and column masking | D4 | Dec 2 to Dec 4 |
| [F8](#f8) | MCP tool layer behind AgentCore Gateway and Policy | D5 | Dec 3 |
| [F9](#f9) | Well Data Assistant on AgentCore Runtime | D6 | Dec 7 |
| [F10](#f10) | Microsoft Teams channel bot | D6 | Dec 8 |
| [F11](#f11) | IT/PMO access from Claude Code and Claude Desktop | D7 | Dec 9 |
| [F12](#f12) | Audit trail and monitoring | D8 | Dec 7 to Dec 9 |
| [F13](#f13) | Evaluation, security tests and pilot | D9 | Dec 14 to Dec 24 |
| [F14](#f14) | Readout, handover and runbook | D10, D11 | Thu Dec 24 |

Build order that follows the dependencies: [F1](#f1), [F2](#f2), [F3](#f3), [F4](#f4), [F5](#f5) and [F6](#f6) (parallel), [F7](#f7), [F8](#f8), [F9](#f9), then [F10](#f10), [F11](#f11) and [F12](#f12) (parallel), then [F13](#f13) and [F14](#f14).

---

<a id="f1"></a>
### F1. Mobilization, plan and governance

**Description.** Kick off the engagement, name owners for every client dependency, keep a RAID log and dependency tracker, and submit Deliverable 1 (confirmed project plan and question set outline). This feature also covers the weekly status call and the 8-business-day review clock.

**Acceptance criteria.**
1. Written confirmation of the kick-off date (Mon Nov 16) and named owners and backups for each Week 1 dependency exists in the RAID log.
2. The RAID log and dependency tracker contain every item from the Dependencies doc, each with an owner, due date and status.
3. A shared Teams channel exists and the CapNexus engineers can sign in to it.
4. Deliverable 1 (project plan and question set outline) is submitted with an acceptance form, and the date the 8-business-day review clock started is recorded.
5. A weekly status report is sent every Monday at 3:00 PM Eastern to the kick-off attendees.
6. Any slipped Week 1 dependency is logged with date and cause, and the plan dates are shifted day for day (SOW Assumption 8).

**Dependencies.**

| ID | Why this feature needs it |
|---|---|
| [DEP-01](#dep-01) | Without named owners the RAID log has no one to chase. |
| [DEP-04](#dep-04) | Freeze dates decide whether Week 2 and Week 6 dates are realistic. |
| [DEP-23](#dep-23) | Someone must sign or reject D1 within 8 business days. |
| [DEP-26](#dep-26) | Budget approval keeps AWS spend from being blocked later. |
| [DEP-29](#dep-29) | CapNexus engineers need Teams, AWS portal and Entra guest access to work. |

---

<a id="f2"></a>
### F2. AWS landing zone and POC account as code

**Description.** Build an AWS Control Tower landing zone in Mitsui's new management account (home Region us-east-1) with Log Archive and Audit accounts, Security and Workloads OUs, one POC workload account, default controls, organization trail and AWS Config. Enable IAM Identity Center. Deliver the baseline as CDK infrastructure as code with a pipeline, KMS keys, logging, a budget alert, and teardown scripts. Allow Region-deny exceptions for us-east-2 and us-west-2 so Claude cross-region inference works.

**Acceptance criteria.**
1. Control Tower shows the landing zone as Active, with Log Archive, Audit and POC workload accounts enrolled and no drift.
2. The Region-deny control allows us-east-1, us-east-2 and us-west-2, and a Bedrock Claude call from the POC account succeeds.
3. All POC resources deploy from the IaC repository through the pipeline from an empty account. Manual console changes are not required.
4. A customer-managed KMS key exists and is used for Secrets Manager and logs.
5. An AWS Budgets alert reaches the billing contact (send a test).
6. The temporary cross-account role is deleted by Mitsui after use, and Mitsui sends CloudTrail review confirmation.
7. A Control Tower console export (no drift, controls compliant, account enrolled) is saved as acceptance evidence, once in Week 5 and once in Week 6.
8. A teardown script removes the POC resources in a test run and leaves the landing zone intact.

**Dependencies.**

| ID | Why this feature needs it |
|---|---|
| [DEP-02](#dep-02) | Control Tower launches only from an activated management account with root MFA and the role. |
| [DEP-03](#dep-03) | Control Tower needs three unique emails to create the accounts. |
| [DEP-06](#dep-06) | Region and Bedrock/AgentCore service availability decide the design. |
| [DEP-25](#dep-25) | The pipeline needs a repository home before it can be wired up. |
| [DEP-26](#dep-26) | Budget approval and billing contact for the Budgets alert. |

---

<a id="f3"></a>
### F3. Private connectivity (VPN and PrivateLink)

**Description.** Build the AWS side of a site-to-site IPsec VPN to Mitsui's Palo Alto: workload VPC from the Mitsui-assigned CIDR, virtual private gateway, customer gateway, two tunnels. Route to the VPN only from the DMS subnet. Add PrivateLink endpoints for Bedrock, Athena and logging. The assistant must have no network path to the source databases.

**Acceptance criteria.**
1. Both VPN tunnels show UP.
2. TCP tests from the DMS subnet to each of the three SQL Servers succeed on each server's fixed port.
3. Route table and firewall rule exports show that only the DMS subnet can reach the on-premises databases.
4. A connection attempt from the assistant or tool compute subnets to a SQL Server port fails.
5. PrivateLink endpoints for Bedrock, Athena and logging resolve inside the VPC, and a Bedrock call from the VPC succeeds without internet egress.
6. The route and firewall exports are saved as evidence for InfoSec and Network.

**Dependencies.**

| ID | Why this feature needs it |
|---|---|
| [DEP-07](#dep-07) | Palo Alto details, CIDRs and firewall rules are on Mitsui's side only. |
| [DEP-04](#dep-04) | VPN and firewall changes fall under change control and freezes. |
| [DEP-05](#dep-05) | InfoSec must approve the architecture before traffic opens. |
| [DEP-02](#dep-02) | The VPC lives in the POC account created by Control Tower. |

---

<a id="f4"></a>
### F4. Daily one-way data copy into S3 Tables

**Description.** Copy approved tables from MEPWELL (about 0.2 GB), SDEDBPROD (about 10 GB) and MEPS_ARIES (about 5 GB) once a day. DMS reads over the VPN with a read-only SQL login and writes CSV or Parquet to an S3 staging bucket. A Glue or Athena job loads S3 Tables with lowercase table and column names, keeps a source-to-target name map, compares row counts with the source, and raises an alarm on any mismatch or failed task. SDEDBPROD must reflect current edits (compressed to state 0 or read through versioned `_evw` views).

**Acceptance criteria.**
1. DMS test connection succeeds for all three endpoints, and credentials are in Secrets Manager under the customer-managed KMS key.
2. Only tables on the signed approved list are loaded, and nothing else appears in S3 Tables.
3. After each load, target row counts equal source row counts for every approved table.
4. All table and column names in S3 Tables are lowercase, and the name mapping table covers 100% of them.
5. A known recent SDEDBPROD edit appears in the AWS copy after the next load.
6. Fault test: stopping the DMS task or dropping the connection mid-load raises the partial-load alarm and an email reaches the Mitsui distribution list.
7. The load runs on schedule inside the agreed window with no manual action. Four consecutive clean daily loads by Fri Dec 4, five by Fri Dec 11 (hard target).
8. The unattended window runs Mon Dec 14 to Fri Dec 25 with no manual loads. The DMS task history and alarm history are exported on Thu Dec 24 (readout day) for Dec 14 to Dec 24. The Dec 25 holiday load is checked by Mitsui DBAs on the next business day and added to the evidence.
8a. The load pipeline is frozen from Dec 14. Only fixes for a failed load are allowed during the window.
9. Nothing writes back to the source databases (the per-database login `dms_wda_ro` has only `db_datareader`, `VIEW DATABASE STATE`, `VIEW DEFINITION`).
10. Shape columns arrive as text only where DMS supports the type, and the size cap is documented.

**Dependencies.**

| ID | Why this feature needs it |
|---|---|
| [DEP-03](#dep-03) | Needs the POC account to exist. |
| [DEP-07](#dep-07), [F3](#f3) | DMS cannot reach SQL Server without the VPN and firewall rules. |
| [DEP-08](#dep-08) | Mixed-mode authentication and TDE status decide whether DMS can connect at all. |
| [DEP-09](#dep-09) | DMS needs SQL-authenticated read-only logins. |
| [DEP-10](#dep-10) | Defines which tables are loaded. |
| [DEP-11](#dep-11) | Without it, SDEDBPROD data is stale. |
| [DEP-12](#dep-12) | Sets the DMS schedule and avoids source batch jobs. |
| [DEP-13](#dep-13) | Join keys and crosswalk rules decide which columns and tables are needed. |
| [DEP-05](#dep-05) | InfoSec/data owners must approve copying the data. |

---

<a id="f5"></a>
### F5. Data catalog with SME descriptions

**Description.** Register every approved table in the Glue Data Catalog with table and column descriptions written with Mitsui SMEs, including join hints and well-identifier crosswalk rules. The `describe_columns` tool reads these descriptions, so they drive SQL quality.

**Acceptance criteria.**
1. Every approved table and column is registered in the Glue Data Catalog.
2. Every table and column used by the frozen question set has an SME-written description. Missing descriptions are listed and approved as exceptions.
3. Descriptions identify the join keys between MEPWELL, SDEDBPROD and MEPS_ARIES and cite the crosswalk table.
4. `describe_columns` returns the description text for a sample of 10 tables.
5. After a schema change in a source table, the catalog updates after the next load (or the difference is reported by an alarm).

**Dependencies.**

| ID | Why this feature needs it |
|---|---|
| [F4](#f4) | Tables must exist before they are registered. |
| [DEP-17](#dep-17) | Descriptions can only come from SMEs. |
| [DEP-13](#dep-13) | Join hints depend on the crosswalk rules. |
| [DEP-10](#dep-10) | Defines which tables get described. |

---

<a id="f6"></a>
### F6. Identity federation (Entra to AWS)

**Description.** Federate Microsoft Entra ID to IAM Identity Center (SAML sign-in, SCIM provisioning) and register a trusted token issuer for the Entra tenant. Create the Entra security groups (`sg-wda-users-well`, `-geo`, `-econ`, `sg-wda-econ-sensitive`, `sg-wda-itpmo-tools`, `sg-wda-admins`, `sg-wda-capnexus-engineers`) and the app registrations WDA-API, WDA-TeamsBot and WDA-Clients. Switch the identity source once, in one session. Test whether the signed-in user can be propagated to Athena.

**Acceptance criteria.**
1. Entra users and groups appear in IAM Identity Center through SCIM, and group membership is flat (no nested groups).
2. A test user signs in to the AWS access portal through Entra, and CapNexus engineers sign in the same way.
3. WDA-API, WDA-TeamsBot and WDA-Clients exist with admin consent, and WDA-Clients is a pre-registered public client usable by Claude Code and Claude Desktop.
4. The trusted token issuer maps the email claim, and a token from Entra is accepted for the WDA-API audience.
5. Identity propagation test: a query run for User A in Athena is attributed to User A in CloudTrail or Athena query history. If this fails, the fallback (permissions by Entra group, user logged in the application) is documented and Noah Jackson accepts it in writing before Fri Dec 4.
6. Conditional Access policies that apply to pilot, test and IT/PMO users are reviewed, and any that block loopback or device-code sign-in are listed with a resolution.

**Dependencies.**

| ID | Why this feature needs it |
|---|---|
| [DEP-02](#dep-02) | Identity Center is enabled in the management account. |
| [DEP-14](#dep-14) | Only the Entra administrator can create groups, apps and SCIM. |
| [DEP-15](#dep-15) | Conditional Access can silently block the Claude clients. |
| [DEP-27](#dep-27) | Identity propagation to Athena may not work in the POC. |
| [DEP-29](#dep-29) | Guest accounts for CapNexus engineers. |

---

<a id="f7"></a>
### F7. Data access control and column masking

**Description.** Lake Formation grants table access by Entra group, hides restricted tables, and masks at least one column for users outside `sg-wda-econ-sensitive`. The masking and access matrix (Appendix E3) is signed by Mitsui.

**Acceptance criteria.**
1. Three test users exist: User A (all groups, including `sg-wda-econ-sensitive`), User B (permitted groups, not `sg-wda-econ-sensitive`), User C (no groups).
2. User A sees all approved tables and the unmasked column.
3. User B sees approved tables and the column is masked.
4. User C sees no restricted tables and no masked column.
5. Results in criteria 2 to 4 are identical through the Gateway, Teams, Claude Code and Claude Desktop.
6. An INSERT, UPDATE, DELETE or DDL attempt is refused by Lake Formation when sent directly to Athena (this is the second layer after [F8](#f8)).
7. The masking and access matrix is signed by Noah Jackson (tables) and Matt Schiefelbein (groups).

**Dependencies.**

| ID | Why this feature needs it |
|---|---|
| [F4](#f4), [F5](#f5), [F6](#f6) | Needs tables, catalog and Entra groups in place. |
| [DEP-16](#dep-16) | Cannot build a data filter without the masked column and classification rules. |
| [DEP-14](#dep-14) | Test users and groups are created by the Entra admin. |
| [DEP-27](#dep-27) | Per-user enforcement depends on identity propagation, or the fallback. |

---

<a id="f8"></a>
### F8. MCP tool layer behind AgentCore Gateway and Policy

**Description.** Publish four read-only tools (`list_tables`, `describe_columns`, `sample_rows`, `run_select`) through AgentCore Gateway with a JWT authorizer for the WDA-API audience. AgentCore Policy allows only the approved tools, only SELECT statements, and enforces row limits and timeouts. The tools query Athena as the signed-in user.

**Acceptance criteria.**
1. A request without a token, with a wrong audience, or with a bad signature is refused at the Gateway.
2. With a valid Entra token, each of the four tools returns correct results for User A.
3. A write attempt (INSERT, UPDATE, DELETE, DROP, CREATE, multi-statement SQL with a write) is refused by AgentCore Policy, and the refusal is logged.
4. A SELECT above the row limit is capped, and a query above the timeout is cancelled, using the values in Section 6 (or the values Mitsui changes them to). The limits are recorded in the runbook.
5. The tools have no network path to the source databases.
6. Tool names are consistent in code, policy and documentation (see Section 5, note 2 on `run_select` vs `run_select_query`).

**Dependencies.**

| ID | Why this feature needs it |
|---|---|
| [F4](#f4), [F5](#f5), [F7](#f7) | The tools need data, descriptions and permissions to return meaningful results. |
| [F6](#f6) | The authorizer needs the Entra OIDC discovery URL and the WDA-API audience. |
| [DEP-06](#dep-06) | AgentCore Gateway and Policy must be available in us-east-1. |
| [DEP-27](#dep-27) | Decides whether the tool carries the user's identity to Athena. |

---

<a id="f9"></a>
### F9. Well Data Assistant on AgentCore Runtime

**Description.** An assistant on AgentCore Runtime that uses Claude on Bedrock with Guardrails. It discovers tables, reads descriptions, samples values, writes SQL, joins MEPWELL, SDEDBPROD and MEPS_ARIES on well identifiers through the crosswalk, and answers with a short table plus the SQL it ran. It refuses non-SELECT requests. It calls tools with the asking user's token.

**Acceptance criteria.**
1. A plain-English question returns a short table and the SQL that ran.
2. A cross-database question joins at least two of the three databases through the MEPWELL crosswalk and returns the SME-expected result.
3. A request such as "delete the rows for well X" is refused in the answer, and no write reaches Athena.
4. Bedrock Guardrails are attached, and a prompt-injection test string inside a data value does not cause a tool call outside the four tools.
5. The assistant calls tools with the asking user's token, not a shared service identity (confirmed in the audit log).
6. Bedrock throttling does not appear during a test of 15 concurrent users (quota request granted).

**Dependencies.**

| ID | Why this feature needs it |
|---|---|
| [F8](#f8), [F5](#f5) | The assistant needs the tools and the descriptions. |
| [DEP-06](#dep-06) | Claude model access, first-use form and quotas must be approved on a new account. |
| [DEP-13](#dep-13), [DEP-21](#dep-21) | Join rules and example questions drive prompt design. |

---

<a id="f10"></a>
### F10. Microsoft Teams channel bot

**Description.** An Azure Bot (single tenant) in Mitsui's Azure subscription, a bot messaging endpoint behind AWS WAF that validates the Bot Framework JWT, and a Teams app installed in one pilot channel. Answers are a short table plus the SQL. Typical answers arrive within 60 seconds.

**Acceptance criteria.**
1. Test in Web Chat returns an answer.
2. After the app is installed in the pilot channel, a Mitsui test user asks a question and receives a table plus SQL in the channel.
3. A POST to `/api/messages` with an invalid or missing Bot Framework JWT is rejected before it reaches the assistant.
4. The answer reflects the asker's permissions: User C gets no restricted tables.
5. The median and typical (for example p90) latency for the frozen question set is under 60 seconds, shown in the dashboard report.
6. All 15 pilot users are in the Entra groups, the Team and the pilot channel, and each completes at least one question.

**Dependencies.**

| ID | Why this feature needs it |
|---|---|
| [F9](#f9), [F6](#f6) | The bot forwards questions and the user's identity to the assistant. |
| [DEP-18](#dep-18) | The Azure Bot resource must live in a Mitsui Azure subscription. |
| [DEP-19](#dep-19) | Teams admin must approve custom apps for one channel. |
| [DEP-22](#dep-22) | Pilot users must be named and enrolled. |

---

<a id="f11"></a>
### F11. IT/PMO access from Claude Code and Claude Desktop

**Description.** IT/PMO users add the Gateway as an MCP server in Claude Code and Claude Desktop. They sign in with their own Entra account through the pre-registered WDA-Clients app (Entra has no dynamic client registration). They can list, describe, sample and SELECT. If Claude Desktop calls from Anthropic's cloud, the Gateway is internet-reachable and protected only by the JWT authorizer, which InfoSec must approve.

**Acceptance criteria.**
1. InfoSec approves the connection method in writing, including acceptance that returned rows reach the Claude client and its model provider.
2. On a Mitsui-managed laptop, a member of `sg-wda-itpmo-tools` signs in through Entra (MFA applies) from Claude Code and from Claude Desktop.
3. From each client, a recorded session shows list, describe, sample and SELECT working.
4. A user outside `sg-wda-itpmo-tools` cannot use the tools.
5. Users A, B and C get the same permission results as in Teams.
6. A write attempt from each client is refused.
7. The IT/PMO lead signs off on the recorded sessions.

**Dependencies.**

| ID | Why this feature needs it |
|---|---|
| [F8](#f8), [F6](#f6) | Needs the Gateway and WDA-Clients app. |
| [DEP-20](#dep-20) | InfoSec and device approval gate the connection method. |
| [DEP-15](#dep-15) | Conditional Access can block device-code or loopback sign-in. |
| [DEP-14](#dep-14) | The Entra admin must register the client app and group. |

---

<a id="f12"></a>
### F12. Audit trail and monitoring

**Description.** Every question is traceable to a named user, tool call, SQL statement, time and result size using AgentCore Observability, CloudTrail and Bedrock invocation logging. Logs are encrypted with the customer-managed KMS key. A CloudWatch dashboard shows latency, errors and throttling. Alarms (partial load, errors) go by SNS email to the Mitsui distribution list.

**Acceptance criteria.**
1. For 20 sampled pilot questions, an audit record shows user, question, tool calls, SQL, timestamp and row count, with no gaps.
2. Records are tied to a named person even if the identity-propagation fallback is in use.
3. CloudTrail captures Athena, Lake Formation and DMS API activity and is stored in the Log Archive account.
4. Logs and the Bedrock invocation log are encrypted with the customer-managed KMS key, and only the people InfoSec named can read them.
5. The dashboard shows latency, errors and throttling, and the latency report supports the 60-second claim.
6. A test alarm reaches every recipient on the Mitsui distribution list.
7. Retention uses AWS defaults and this is recorded in the runbook.

**Dependencies.**

| ID | Why this feature needs it |
|---|---|
| [F2](#f2) | Needs the Log Archive account, KMS key and organization trail. |
| [DEP-24](#dep-24) | Mitsui must approve who reads logs that contain business data, and supply alarm recipients. |
| [DEP-27](#dep-27) | Determines whether user identity comes from Athena or the application layer. |

---

<a id="f13"></a>
### F13. Evaluation, security tests and pilot

**Description.** Run and prove the acceptance criteria: question-set accuracy, write-refusal, permission tests, latency, unattended load and the pilot with about 15 users. Collect the evidence pack against the acceptance matrix (item 9.4) and publish the Week 6 test plan and written rejection path. This is Deliverable 9 (evaluation report).

**Acceptance criteria.**
1. At least 80% of the frozen question set (24 of 30) is correct as scored by Mitsui SMEs, using the agreed tolerance. About 10 held-back questions were not used for tuning.
2. Every write attempt is refused by AgentCore Policy and, when Policy is bypassed in a test, by Lake Formation. Log saved.
3. Users A, B and C results match the expected table through Teams, Claude Code and Claude Desktop.
4. Route table and firewall export show no path from the assistant to the on-premises databases.
5. Typical Teams answers arrive within 60 seconds, confirmed by the pilot lead from the dashboard report.
6. The daily load ran unattended Dec 14 to Dec 25, verified from DMS task and alarm history (export Dec 24, Dec 25 added after the holiday).
7. Each pilot user has asked at least five questions, and wrong answers have been logged with a severity.
8. Every acceptance criterion in item 9.4 has evidence and a Mitsui verifier sign-off, or a written rejection reason. The evidence pack is sent by Fri Dec 18 for everything except the load evidence, which follows on Dec 24 and in the first week after the holiday.
9. Code freeze is in effect from Dec 18, with only fixes for failed tests.

**Dependencies.**

| ID | Why this feature needs it |
|---|---|
| [F4](#f4) to [F12](#f12) | The tests exercise the whole build. |
| [DEP-21](#dep-21) | The 80% judgment needs a signed, frozen question set and SMEs to score it. |
| [DEP-22](#dep-22) | The pilot needs about 15 active users. |
| [DEP-23](#dep-23) | Acceptance needs named testers and verifiers per criterion. |
| [DEP-12](#dep-12) | A fixed load window is needed for the unattended-load evidence. |

---

<a id="f14"></a>
### F14. Readout, handover and runbook

**Description.** Hand over code, IaC, configuration and a runbook to the Mitsui IT operations owner, run a knowledge-transfer session, and hold the readout with actual-usage AWS run-cost estimate and next-phase recommendation (D10, D11). Mitsui decides to keep, pause or tear down the resources.

**Acceptance criteria.**
1. The runbook covers: daily load and alarms, rerun procedure, secret rotation, SCIM token renewal, Region/limits settings, and teardown.
2. The IaC and pipeline repository is in the agreed home, and a Mitsui engineer can deploy from it.
3. The knowledge-transfer session is held with the named IT operations owner by Thu Dec 24.
4. The readout deck states results against each criterion, an AWS run-cost estimate from actual usage, and the next-phase recommendation (for example Quorum, QLS/LIS, Oracle, geospatial).
5. Noah Jackson records the keep, pause or tear down decision.
6. CapNexus access is removed after handover.
7. D10 and D11 are submitted with acceptance forms, and the 8-business-day review period is recorded (ends by Fri Jan 8, 2027).

**Dependencies.**

| ID | Why this feature needs it |
|---|---|
| [DEP-25](#dep-25) | Repository home for handover. |
| [DEP-28](#dep-28) | Recipients, attendees and post-POC decision are Mitsui's. |
| [DEP-23](#dep-23) | Acceptance owner signs D10 and D11. |
| [F2](#f2), [F13](#f13) | Teardown scripts and test results feed the runbook and readout. |

---

## 3. Dependency register

Owner, "needed by" and SOW or doc item are in brackets. Steps are ordered and can be copied into the RAID log.

### Program and governance

<a id="dep-01"></a>**DEP-01 Named owners and backups** (Noah Jackson; kick-off; item 1.1). *Why:* the Period of Performance depends on it, and unnamed DBA, GIS admin, Azure admin, InfoSec reviewer, SMEs and IT/PMO lead have no one to chase. *Resolve:*
1. Send Noah the owner table from item 1.1 before or at kick-off.
2. Ask for a name and a backup for each role.
3. Record them in the RAID log and escalate blanks to Noah on the next business day.

<a id="dep-04"></a>**DEP-04 Change-freeze calendar and CAB rules** (Noah Jackson; Week 1; item 1.2). *Why:* Thanksgiving, December freezes and Christmas fall inside the plan. *Resolve:*
1. Ask for the holiday and freeze calendar.
2. Ask whether VPN, firewall, SQL login and Entra changes need a CAB ticket and the lead time.
3. Open CAB tickets in Week 1 and mark dates on the plan.

<a id="dep-05"></a>**DEP-05 InfoSec, vendor and data-copy approval** (Noah Jackson to name the InfoSec reviewer; Week 1 and ongoing; items 1.3, 1.4). *Why:* the data leaves Mitsui's data center and goes to Bedrock. *Resolve:*
1. Mitsui names the InfoSec reviewer.
2. Send the architecture summary and the data flow diagram (scheduled for Mon Nov 16 in the task list).
3. Walk through the data classification of approved tables with data owners and get approval in writing.

<a id="dep-23"></a>**DEP-23 Acceptance owner and UAT testers** (Noah Jackson; Week 6; item 9.4). *Why:* SOW deliverables are accepted by silence after 8 business days and need a named verifier per criterion. *Resolve:*
1. Confirm Noah as signer (decided at kick-off).
2. Map each row in the acceptance matrix to a Mitsui verifier by Dec 21.
3. Explain the clock and the written rejection path at the Week 1 and Week 6 calls.

<a id="dep-25"></a>**DEP-25 Repository and pipeline home** (Mitsui; Week 1; item 1.7). *Why:* the pipeline skeleton and handover need one place. *Resolve:*
1. Ask Mitsui whether to use their Git host or CapNexus's repo first.
2. Create the repo (CDK, TypeScript or Python) and connect through AWS CodeConnections.
3. Move it to Mitsui on Thu Dec 17 if agreed.

<a id="dep-26"></a>**DEP-26 Budget approval and billing contact** (Noah Jackson; Week 1; item 1.5). *Why:* AWS consumption is billed to Mitsui and is outside the SOW. *Resolve:*
1. Send the monthly cost estimate (scheduled for Tue Nov 17 in the task list).
2. Get written approval and a billing contact email.
3. Deploy the Budgets alert.

<a id="dep-29"></a>**DEP-29 CapNexus working access** (Mitsui; Week 1; item 1.6). *Why:* five CapNexus roles need Teams, Entra guest and AWS portal access. *Resolve:*
1. Send the guest invitation list.
2. Mitsui sends invitations.
3. Each engineer confirms sign-in.

<a id="dep-28"></a>**DEP-28 Handover recipients, readout attendees and post-POC decision** (Noah Jackson; Week 5; items 10.2, 10.3). *Why:* D10 and D11 cannot be delivered without recipients. *Resolve:*
1. Ask for the IT operations owner and readout attendees by Dec 14.
2. Schedule the readout and KT for Dec 24 (before the holiday).
3. Ask for a keep, pause or tear-down decision at the readout.

### AWS foundation

<a id="dep-02"></a>**DEP-02 Management account, root MFA and cross-account role** (Noah Jackson, Matt Schiefelbein; Nov 16 to 17; item 2.2). *Why:* Control Tower deploys only from an activated Organizations management account, and CapNexus has no other access. *Resolve:*
1. Noah creates the account as root, activates it (contact, payment, verification) and turns on root MFA.
2. CapNexus sends account ID, principal ARNs and external ID.
3. Mitsui creates the role (AdministratorAccess, MFA and external ID, 4-hour sessions, 7-day expiry) and sends the ARN.
4. CapNexus tests the assume-role and runs the pre-flight checks (Organizations all-features, Config trusted access, STS in us-east-1).
5. Mitsui deletes the role after Control Tower and Identity Center preparation (Fri Nov 20).

<a id="dep-03"></a>**DEP-03 Three account emails** (Noah Jackson; kick-off; item 2.3). *Why:* Control Tower creates Log Archive, Audit and POC accounts from unique emails. *Resolve:* Noah creates three mailbox or distribution addresses that Mitsui can receive, sends them to CapNexus before launch (Wed Nov 18), and confirms none is already tied to an AWS account.

<a id="dep-06"></a>**DEP-06 Region, service availability, Bedrock model access and quotas** (Solution Architect with Matt and Noah; Week 1; items 2.1, 2.6, risks 4, 5, 17). *Why:* a new account has default Bedrock quotas, the Anthropic first-use form is required, and AgentCore Gateway, Identity, Runtime, Policy, S3 Tables with Lake Formation and identity-aware Athena must exist in us-east-1. *Resolve:*
1. Confirm each service in us-east-1 on Tue Nov 17 and record any gap as a design risk.
2. Send Mitsui the Anthropic use-case text and the quota request for submission.
3. Allow us-east-2 and us-west-2 in the Region-deny control for cross-region inference.
4. Involve the AWS account team (Jack Bradham, Kim Sawyer) if quotas lag.
5. Test a Claude call from the POC account in Week 1 or Week 2.

### Network and source data

<a id="dep-07"></a>**DEP-07 VPN, IP plan, DNS and firewall rules** (Matt Schiefelbein; Fri Nov 20; items 3.1 to 3.4). *Why:* the data copy and the no-path test both depend on the network design. *Resolve:*
1. Request Palo Alto model, PAN-OS version, public IP, routing type and CIDRs (Appendix C sheet).
2. Create the AWS side (VPC, virtual private gateway, customer gateway) from Mitsui CIDRs and send the Palo Alto config file.
3. Mitsui configures the device and allows only the DMS subnet to the SQL Server IPs and fixed ports.
4. Validate both tunnels and run TCP tests on Mon Nov 23.
5. If late, log the blocker with a date in the RAID log.

<a id="dep-08"></a>**DEP-08 Source inventory, mixed-mode authentication and TDE** (DBAs via Noah; Week 1; items 4.1, 4.2). *Why:* DMS cannot use Windows authentication, and TDE or permission limits may block it. *Resolve:*
1. Send Appendix A scripts (A1, A3, A4) to the DBAs on Mon Nov 16.
2. Review returned inventories by Fri Nov 20 and list unsupported column types.
3. If an instance is Windows-only, schedule a mixed-mode change and restart in a change window.
4. Confirm any readable secondary.

<a id="dep-09"></a>**DEP-09 Read-only SQL logins** (Noah Jackson, DBAs; Fri Nov 20; item 4.2). *Why:* DMS reads the sources with these. *Resolve:*
1. DBAs run Appendix A2 (`db_datareader`, `VIEW DATABASE STATE`, `VIEW DEFINITION`, no `sysadmin` or `db_owner`).
2. They send credentials through a secure channel.
3. CapNexus stores them in Secrets Manager under the customer-managed KMS key and runs DMS test connection.

<a id="dep-10"></a>**DEP-10 Approved table list** (Noah Jackson; end of Week 2, Fri Nov 27; item 4.3, Appendix E1). *Why:* limits what data is copied and drives the catalog and permissions. *Resolve:*
1. Pre-fill Appendix E1 from the inventory.
2. Review with data owners, including MEPWELL hub and crosswalk tables.
3. Noah signs the list. Any later change goes through the RAID log.

<a id="dep-11"></a>**DEP-11 SDEDBPROD approach and owner** (owner is Mitsui, decided Nov 17; the named person is still blank, and the approach is undecided; before first load Mon Nov 23; item 4.4). *Why:* without it the AWS copy of the geodatabase misses current edits. *Resolve:*
1. Put the decision on the Nov 23 agenda with Noah.
2. Pick one: compress to state 0 before the load window, or read access to versioned `_evw` views.
3. Noah Jackson is the interim owner (decided Nov 17) until Mitsui names the GIS admin, and agree timing so the job ends before the load starts.
4. Document geometry storage and largest shape size.
5. Prove it with a known recent edit (Nov 25).
6. If undecided by Nov 23, load MEPWELL and MEPS_ARIES first and raise an alarm for SDEDBPROD.

<a id="dep-12"></a>**DEP-12 Daily load window and blackouts** (Noah Jackson, DBAs; Week 2; item 4.5). *Why:* sets the DMS schedule and avoids competing with source batch jobs. *Resolve:*
1. Ask DBAs for existing batch, backup and maintenance windows.
2. Agree a window (the 1:00 to 4:00 AM Central in the workflow doc is only an example).
3. Set the schedule on Tue Dec 1 and tell DBAs and the network team there is no maintenance Dec 14 to Dec 25.

<a id="dep-13"></a>**DEP-13 Data dictionary, join keys and SME sessions** (Noah Jackson, SMEs; Week 2; items 4.6, 9.1). *Why:* cross-database joins use the MEPWELL crosswalk. *Resolve:*
1. Hold the SME data-model session Mon Nov 23.
2. Collect ER diagrams, data dictionaries and crosswalk rules.
3. Record the SME names in the RAID log.

### Identity

<a id="dep-14"></a>**DEP-14 Entra administrator, licensing, groups and app registrations** (Matt Schiefelbein; Week 1 to Week 3; items 5.1 to 5.4, 5.6). *Why:* only Mitsui can create groups, apps, consent and SCIM, and SCIM and group assignment need Entra P1. *Resolve:*
1. Confirm the admin and P1 licence in Week 1.
2. Book sessions for Nov 24 (federation planning) and Nov 30 (groups and apps).
3. Create the five security groups (flat membership) and WDA-API, WDA-TeamsBot, WDA-Clients with admin consent.
4. Switch the Identity Center identity source on Dec 1 in one session.
5. Confirm UPN equals primary email, or map the claim.
6. Create test users A, B and C.

<a id="dep-15"></a>**DEP-15 Conditional Access and MFA review** (Matt Schiefelbein; Week 2 to Week 3; item 5.5). *Why:* policies assigned by group can block loopback or device-code sign-in used by Claude clients. *Resolve:*
1. Get the list of policies and groups that apply.
2. Test a sign-in from a managed laptop on Dec 9 (earlier if possible).
3. Send problems to Matt with the failed sign-in log.

<a id="dep-27"></a>**DEP-27 Identity propagation to Athena** (Solution Architect; test Wed Dec 2; SOW Assumption 8; risk 1). *Why:* per-user query identity in Athena and Lake Formation may not work within the POC. *Resolve:*
1. Test with the trusted token issuer and an identity-aware Athena workgroup on Dec 2.
2. If it fails, switch to permissions by Entra group and log the user in the application.
3. Get Noah's written acceptance of the fallback.

### Governance, Teams and clients

<a id="dep-16"></a>**DEP-16 Masked column and classification rules** (Noah Jackson, Matt Schiefelbein; Week 3, requested Nov 30; item 6.2). *Why:* the Lake Formation filter and the User A/B/C results cannot be defined without it. *Resolve:*
1. Ask for the column and rules for royalty owner, lessor and other sensitive data on Nov 30.
2. Pre-fill Appendix E3 with a proposal from the inventory.
3. Noah and Matt sign by Fri Dec 4.

<a id="dep-17"></a>**DEP-17 SME table and column descriptions** (Noah Jackson, SMEs; Week 2 to Week 4; item 6.1). *Why:* descriptions drive SQL quality. *Resolve:*
1. Pre-fill Appendix E2 from names and data types (Nov 25).
2. Chase weekly, and load whatever has been received on Nov 30.
3. Collect the rest by Dec 10 and escalate to Noah if any are missing.

<a id="dep-18"></a>**DEP-18 Azure subscription for the Azure Bot** (to be named; Week 3; item 7.1). *Why:* single-tenant bots need an Azure subscription and Entra app in Mitsui's tenant. *Resolve:*
1. Ask for the Azure admin and a subscription or resource group in Week 1.
2. Grant a CapNexus engineer rights to create the bot resource.
3. Create the bot on Dec 3.

<a id="dep-19"></a>**DEP-19 Teams administrator approval for one pilot channel** (Noah Jackson; Mon Nov 30 per SOW; item 7.2). *Why:* a Teams custom app policy can block the bot and push go-live past Week 3. *Resolve:*
1. Open the request in Week 1.
2. Send the app package details and channel name.
3. Escalate Monday morning on Nov 30 if not confirmed.

<a id="dep-20"></a>**DEP-20 IT/PMO device readiness, connection-method approval and user list** (Noah Jackson, InfoSec; Week 3 to Week 4; items 8.1, 8.2). *Why:* Claude Desktop remote connectors may call from Anthropic's cloud, which needs an internet-reachable Gateway. *Resolve:*
1. Send connection options to InfoSec on Dec 8 (earlier if possible).
2. Get a written decision that covers the data reaching Anthropic's cloud.
3. Get the IT/PMO user list and device readiness by Dec 9.

<a id="dep-21"></a>**DEP-21 SMEs and question set of about 30 questions** (Noah Jackson, SMEs; Week 1 to Week 4; items 9.1, 9.2). *Why:* the 80% criterion is judged by SMEs against this set. *Resolve:*
1. Send the Deliverable 1 outline (about 7 per database and 9 joins).
2. SMEs write expected answers, data date, tables and owner.
3. Agree the tolerance and use snapshot-date answers because data reloads daily.
4. Freeze on Dec 10 with about 10 held back.

<a id="dep-22"></a>**DEP-22 About 15 pilot users** (Noah Jackson; named Week 4, active Week 5 to 6; item 9.3). *Why:* latency, audit and permission acceptance needs real usage. *Resolve:*
1. Noah nominates a mix of well engineers, GIS and economics analysts, plus a pilot lead (Dec 7).
2. Add them to Entra groups, the Team and the pilot channel.
3. Run a 30-minute enablement session and send the one-page guide (Dec 10).

<a id="dep-24"></a>**DEP-24 Audit and logging policy and alarm recipients** (Noah Jackson, InfoSec; Week 4 to Week 5; item 10.1). *Why:* logs hold question text and result rows. *Resolve:*
1. Get a list of who may read audit and Bedrock logs.
2. Get the distribution list address for SNS.
3. Send a test alarm on Dec 15 and get the recipients' confirmation.

---

## 4. End-to-end acceptance scenarios

These run after [F13](#f13) is delivered and cover the whole chain.

| # | Scenario | Pass condition |
|---|---|---|
| E2E-1 | Overnight load to answer. A scheduled load runs, then a pilot user asks a question that depends on yesterday's change. | Row counts match, the new value appears in the Teams answer in under 60 seconds with the SQL shown. |
| E2E-2 | Cross-database question. A pilot user asks something that needs MEPWELL, SDEDBPROD and MEPS_ARIES. | The answer matches the SME expected result, and the SQL joins through the crosswalk. |
| E2E-3 | Same question as User A, B and C in Teams, Claude Code and Claude Desktop. | A sees the full column, B sees it masked, C sees no restricted tables. Same result in every client. |
| E2E-4 | Write attempt from Teams, Claude Code and Claude Desktop. | Refused by AgentCore Policy, log entry present, and no change in data. |
| E2E-5 | Audit trace. Pick any pilot question. | Audit record shows the named user, SQL, time and row count. |
| E2E-6 | Partial-load failure. Stop DMS mid-load. | Alarm email arrives at the Mitsui list, and the assistant is not served half-loaded data silently (or the issue is documented). |
| E2E-7 | Unauthorized caller. Call the bot endpoint and the Gateway with invalid tokens. | Both reject the call. |
| E2E-8 | Teardown and redeploy. Run the teardown script, then redeploy from the repo. | Environment returns to the same state, per the runbook. |

## 5. Conflicts and gaps found in the source documents

Resolved by reading the Kickoff Agenda and the diagram:
- **Kick-off date.** The meeting was Wed Nov 11. The decisions log sets the kick-off (Period of Performance start) as 11/16. No conflict.
- **SME time.** The Kickoff Agenda and SOW both say about 6 hours a week. Rev 1.5 of the Dependencies doc removed that figure. The SOW wording applies.
- **Tool target.** The diagram says "Tool target implementation to be confirmed in Week 3". Section 6 proposes one.

Still open:
1. **Unattended-load window moved to Dec 14 to Dec 25 (decided Nov 17).** This follows the Dependencies doc and the SOW "final two weeks". It conflicts with the task list (Week 4 Mon Dec 7, Week 5 Fri Dec 18), the workflow doc and the diagram timeline. Consequences to handle:
   - Dec 25 is a holiday and the readout is Dec 24, so the window cannot be fully exported before the readout. Plan: export Dec 14 to Dec 24 on Dec 24, and Mitsui DBAs confirm the Dec 25 load afterward. Confirm Mitsui accepts that.
   - The stable-load hard target stays Fri Dec 11 (kickoff). Week 4 and early Week 5 now have runs outside the window that can still be fixed. The pipeline freeze starts Dec 14.
   - The Week 3 to Week 6 task files, the xlsx and the workflow doc (sections 1, 3 and 8) were updated on Nov 17. A new Dec 24 task exports the DMS and alarm history. The architecture `.drawio` has no dates, so it is unchanged.
   - Mitsui DBAs, network team and the holiday freeze calendar ([DEP-04](#dep-04)) must cover Dec 14 to Dec 25.
2. **Tool name.** The SOW, diagram and workflow doc say `run_select`. The Week 3 task list says `run_select_query`. Use `run_select`.
3. **Pilot timing.** The SOW and Kickoff Agenda put pilot users in Week 6. The task list opens access Mon Dec 14. Get Mitsui's written agreement to the earlier start.
4. **Kickoff decisions log is incomplete.** The SDEDBPROD owner is Mitsui (decided Nov 17), but no person is named and the approach is still blank. Also, the daily load window and masked column are blank in the discovery notes. They are [DEP-11](#dep-11), [DEP-12](#dep-12) and [DEP-16](#dep-16).
5. **Executive sponsor.** The agenda asks to confirm one. No name was recorded, and steering check-ins were declined. Ask Noah who escalates above him.
6. **Action items 5 and 6 are empty** in the Kickoff Agenda.
7. **Bot endpoint reachability.** The diagram says private subnets and no internet gateway, but Azure Bot Service must reach `/api/messages` over the internet. The endpoint must be a public, WAF-protected entry point (see Section 6), while the tools stay private.
8. **PrivateLink scope.** The SOW and diagram list endpoints for Bedrock, Athena and logging only. If the bot compute is in the VPC, it also needs a route to AgentCore Runtime. Confirm an AgentCore interface endpoint exists in us-east-1 or keep the bot compute outside the VPC (it has no database path).
9. **Timeline status.** Today is Tue Nov 17 (Week 1, day 2). Check first the items due Nov 16: management account, three emails, owners. A slip moves the plan day for day.

## 6. Proposed decisions (for Mitsui and CapNexus sign-off)

These are my proposals, not documented decisions. Row and time values are starting points to tune in Week 3 against real queries, and they must stay under the 60-second Teams target.

**Compute for the MCP tools.** AWS Lambda functions registered as AgentCore Gateway Lambda targets, one per tool, in the workload VPC with interface endpoints to Athena and logs.
- Why: Gateway supports Lambda targets directly, nothing runs to maintain, and the tools get no route to on-premises ([F3](#f3) criterion 4).
- Trade-off: a container service gives more control, but adds a cluster for four small tools.

**Compute for the Teams bot endpoint.** Amazon API Gateway (REST API) with AWS WAF attached, forwarding `/api/messages` to a Lambda function that validates the Bot Framework JWT and calls AgentCore Runtime.
- Why: WAF attaches to API Gateway REST APIs but not to Lambda function URLs, and the diagram requires WAF in front of the endpoint.
- Note: see gap 8 for the VPC question.

**AgentCore Policy limits (starting values).**

| Tool | Row limit | Timeout | Other |
|---|---|---|---|
| `list_tables` | 200 tables | 10 s | Only tables the user may see |
| `describe_columns` | 300 columns per table | 10 s | |
| `sample_rows` | 10 default, 50 max | 10 s | Masked columns stay masked |
| `run_select` | 1,000 rows | 30 s | Single SELECT only, no semicolons, no write keywords |
| Whole question | n/a | 55 s | Leaves headroom under the 60 s target |

Also set an Athena workgroup per-query data-scan cutoff of 10 GB (the largest database is about 10 GB) to cap cost from a bad query.

**Cost notes (accepted Nov 17, prices to be checked in the AWS Pricing Calculator).**
- Lambda and API Gateway cost is negligible at about 15 users. The main costs are DMS, the VPN, interface endpoints, Bedrock tokens and Athena scans.
- DMS: prefer DMS Serverless (bills only while a task runs). If a provisioned instance is used, pick the smallest class that completes the 15 GB load inside the window, and leave it running (no stop/start automation during the unattended window).
- Interface endpoints: single Availability Zone for the POC (high availability is out of scope).
- Bedrock: keep `describe_columns` output short, use prompt caching for the system prompt and schema, and test a smaller Claude model for simple steps against the 80% target.
- Athena: Parquet tables and the 10 GB per-query scan cutoff.
- Keep default log retention. Run the teardown script after handover unless Mitsui chooses to keep the environment. The VPN, DMS and endpoints keep billing until then.

## 7. Open questions for Mitsui and the team

1. Which SDEDBPROD approach (compress to state 0 or versioned views) will Noah Jackson, the interim owner, pick by Mon Nov 23, and which GIS admin runs it?
2. What are the daily load window and blackout periods? The window now has to hold through the holidays.
3. Does Mitsui accept the Dec 24 export with a next-business-day check of the Dec 25 load?
4. Is Entra P1 licensed, and does UPN equal primary email?
5. Which column is masked, and what are the classification rules?
6. Is Mitsui comfortable with the Claude Desktop internet-reachable Gateway path?
7. Who is the executive sponsor above Noah Jackson for escalations?
