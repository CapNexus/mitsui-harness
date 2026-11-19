<!-- Generated from knowledge/Mitsui.CapNexus.SOW2026001 - Well Data Assistant Proof of Concept - Clean 11.6.26.docx.pdf by .bootstrap/prepare_inputs.py. Do not edit. -->

Mitsui.CapNexus.SOW2026001 
 
 
CapNexus, LLC 
Statement of Work 
MITSUI.CAPNEXUS.SOW2026001 
  
  
Services:  Well Data Assistant Proof of Concept 
 
October 29, 2026 
 
 
 
  
Docusign Envelope ID: 534DE2FD-2D6D-8156-80D5-274B5B4EBB09

Mitsui.CapNexus.SOW2026001 
OVERVIEW: 
This CapNexus Statement of Work (“SOW”) provides a project cost summary and services specific to this 
project. This SOW is governed by the terms within and is between Mitsui E&P USA LLC, referenced herein 
as “Mitsui” or “Client” and CapNexus, LLC, referenced herein as “CapNexus” or “Provider.”  
SCOPE: 
CapNexus will design, build, and pilot a read-only Well Data Assistant for Client over six (6) weeks. Business 
users ask plain-English questions about well, geodatabase, and economics data in a Microsoft Teams 
channel, and IT and PMO users reach the same governed tools from Claude Code or Claude Desktop. Every 
answer is drawn from a daily one-way copy of approved tables from three of Client’s SQL Server databases 
into a new AWS Control Tower landing zone, and every query runs as, and is logged against, the person 
who asked it. The assistant runs on Amazon Bedrock AgentCore, with Client’s data published through a 
governed MCP tool layer. 
1. The scope of this engagement includes the following: 
• Landing zone: a simple AWS Control Tower landing zone in Client’s AWS Organizations 
management account, with Log Archive and Audit accounts, Security and Workloads 
organizational units, one POC workload account, the Control Tower default controls, an 
organization trail and AWS Config, and AWS IAM Identity Center as the access point for 
Microsoft Entra ID federation. 
• Mobilization: kick-off, confirmed project plan, agreed question set outline, and a POC 
workload account baseline delivered as infrastructure as code with a deployment pipeline, 
encryption keys, and logging. 
• Private connectivity: the AWS side of a site-to-site VPN to Client’s data center and AWS 
PrivateLink endpoints for Amazon Bedrock, Amazon Athena and logging services. 
• Data copy: an AWS DMS daily one-way full load of approved tables from three SQL Server 
databases into Amazon S3 tables, registered in the AWS Glue Data Catalog. The databases 
are MEPWELL (well hub and crosswalk, about 0.2 GB), SDEDBPROD (ArcGIS enterprise 
geodatabase, about 10 GB), and MEPS_ARIES (ARIES economics and reserves, about 5 GB). 
• Data governance: AWS Lake Formation approved tables, permissions by Microsoft Entra 
ID group, column masking demonstrated on at least one column, and table and column 
descriptions written with Client’s subject matter experts. 
• MCP tool layer: four read-only data tools (list_tables, describe_columns, sample_rows 
and run_select on Amazon Athena) published through Amazon Bedrock AgentCore 
Gateway, with AgentCore Policy enforcing approved tools, SELECT-only queries, row 
limits, and timeouts. 
• Well Data Assistant: an assistant on AgentCore Runtime using Claude on Amazon Bedrock 
with Amazon Bedrock Guardrails that writes SQL, joins MEPWELL, SDEDBPROD, and 
MEPS_ARIES data on well identifiers, and answers with a short table and the SQL it ran. 
• Identity and access: Microsoft Entra ID federated to AWS IAM Identity Center, with 
AgentCore Identity carrying the signed-in user through each tool call to Athena and Lake 
Docusign Envelope ID: 534DE2FD-2D6D-8156-80D5-274B5B4EBB09

Mitsui.CapNexus.SOW2026001 
Formation. 
• Teams and IT/PMO access: Azure Bot Service registration, a Teams app in one pilot 
channel with a bot endpoint, and Claude Code and Claude Desktop configured to use the 
AgentCore Gateway tools under each user’s own sign-in. 
• Observability and audit: a trail of every question, tool call, SQL statement, user, time and 
result size using AgentCore Observability, AWS CloudTrail, and Bedrock invocation logging, 
with an Amazon CloudWatch dashboard and alarms. 
• Test, pilot and readout: question-set evaluation, read-only and permission tests, a pilot 
with about fifteen (15) Client users, a readout with an AWS run-cost estimate and next-
phase recommendation, and handover of code, configuration, and a runbook. 
2. The following items are not in scope under this SOW 
• Application API tools, including Quorum. 
• Additional data sources, including QLS/LIS and accounting or cost data. 
• Oracle data sources. 
• Querying source databases in place (data option B). 
• AWS Context, the AWS Agent Registry and Microsoft Fabric integration. 
• Change data capture, high availability, production hardening, wider rollout, and support 
after the readout. 
• AWS Direct Connect, Microsoft licensing and AWS service consumption charges. 
• Geospatial analysis, map rendering, and ArcGIS integration. SDEDBPROD feature 
attributes are in scope; shape columns are copied as text only where AWS DMS supports 
the data type. 
• Landing zone extensions, including Account Factory for Terraform, a network hub account, 
AWS Transit Gateway, enrollment or migration of existing AWS accounts, and additional 
workload accounts. 
3. Role Provided to perform work 
• Engagement Manager 
• Solution Architect 
• Data & Platform Engineer 
• AI Engineer 
• Integration & Test Engineer 
ASSUMPTIONS: 
1. The POC uses approved tables from three SQL Server databases: MEPWELL (about 200 MB), 
SDEDBPROD (about 10 GB), and MEPS_ARIES (about 5 GB), about 15.4 GB of data in total. Data is 
copied once a day by a one-way full load. Oracle sources are excluded. 
2. For SDEDBPROD, Client either compresses the geodatabase to state zero before each load or 
provides read access to versioned views, so the copy reflects current edits. Shape columns are 
Docusign Envelope ID: 534DE2FD-2D6D-8156-80D5-274B5B4EBB09

Mitsui.CapNexus.SOW2026001 
copied as text only where AWS DMS supports the data type. 
3. Client provides access to its AWS Organizations management account with permission to deploy 
AWS Control Tower, and email addresses for the Log Archive, Audit, and POC workload accounts, 
by the project kick-off date. AWS service consumption is billed directly to Client’s AWS account 
and is not included in this SOW. 
4. Client’s AWS organization has no existing AWS Control Tower landing zone. 
5. By the end of week one (1), Client provides a site-to-site VPN with network team support, read-
only SQL Server accounts for all three databases that meet AWS DMS source requirements, and a 
Microsoft Entra ID administrator for the enterprise application, federation, and group mapping. 
6. Client provides Teams administrator approval for one channel by the start of week three (3), 
subject matter experts covering well, geodatabase, and ARIES economics data for about six (6) 
hours a week to write a question set of about thirty (30) questions and validate answers, and 
about fifteen (15) pilot users in week six (6). 
7. The tool layer covers the four data tools named in Scope. Requests for application API tools, 
additional data sources or querying sources in place are recorded for a later phase and handled 
through Change Control. 
8. The timeline moves day for day with delays in Client dependencies, and delays beyond two (2) 
weeks are handled through Change Control. If carrying each user’s identity through to Athena 
cannot be completed within the POC, the pilot runs on permissions by Entra ID group. 
9. Client acknowledges that the timely provision of and access to office accommodations, facilities, 
equipment, assistance, cooperation, complete and accurate information and data from Client’s 
officers, agents, and employees, and suitably configured computer products (collectively, 
“cooperation”) are essential to the performance of any Services as set forth in this SOW. 
CapNexus will not be responsible for any deficiency in performing Services if such deficiency 
results from Client’s failure to provide full cooperation.  
10. CapNexus, Client and applicable 3rd party vendors will attend all relevant and scheduled in 
advance meetings. 
11. Client will provide CapNexus with full access to the relevant system functional, technical, and 
business resources with adequate skills and knowledge to support the performance of Services. 
12. Client will provide adequate remote access and on-site workspace to CapNexus employees to 
complete this SOW’s deliverables. 
13. CapNexus recognizes that Client has stakeholders and involvement from multiple vendors and 
agrees to participate and collaborate as needed and consistent with industry standards, but the 
ultimate ownership and management of these relationships is the Client’s responsibility. 
14. Client is responsible for final validation before any changes are deployed to production. 
Docusign Envelope ID: 534DE2FD-2D6D-8156-80D5-274B5B4EBB09

Mitsui.CapNexus.SOW2026001 
DELIVERABLES: 
The deliverables for this statement of work are as follows: 
1. Confirmed project plan and question set outline. 
2. AWS Control Tower landing zone and POC workload account delivered as infrastructure as code, 
including private connectivity and the deployment pipeline. 
3. Daily one-way copy of approved tables from MEPWELL, SDEDBPROD, and MEPS_ARIES in Amazon 
S3 tables, registered in the AWS Glue Data Catalog with table and column descriptions. 
4. AWS Lake Formation access policy with Entra ID group permissions and column masking 
demonstrated. 
5. MCP tool layer on Amazon Bedrock AgentCore Gateway with four read-only data tools. 
6. Well Data Assistant on AgentCore Runtime, available in one Microsoft Teams channel. 
7. IT/PMO access to the data tools from Claude Code and Claude Desktop under each user’s own 
sign-in. 
8. Audit trail and Amazon CloudWatch monitoring dashboard. 
9. Evaluation report covering question-set accuracy, read-only tests and permission tests. 
10. Pilot readout with an AWS run-cost estimate and next-phase recommendation. 
11. Handover of infrastructure as code, configuration, and a runbook. 
PERIOD OF PERFORMANCE: 
The Period of Performance commences on the project kick-off date mutually agreed in writing by the 
parties (email sufficing) after this SOW is signed and Client has named owners for the week one (1) 
dependencies. The Period of Performance concludes upon the later of i) Client’s acceptance of the pilot 
readout and handover (Deliverables 10 and 11), which are planned for delivery six (6) weeks from 
commencement, or ii) eight (8) weeks from commencement, unless extended through Change Control.  
ACCEPTANCE CRITERIA: 
CapNexus submits each deliverable to Client with an acceptance form. Client has eight (8) business days 
(“Review Period”) to accept the deliverable or reject it with written reasons that state how it does not 
meet this SOW. CapNexus will correct and resubmit any rejected deliverable(s), and the same Review 
Period will apply to the resubmission. A deliverable is accepted when Client signs the acceptance form, 
or when the Review Period ends without a written rejection. 
Docusign Envelope ID: 534DE2FD-2D6D-8156-80D5-274B5B4EBB09

Mitsui.CapNexus.SOW2026001 
The proof of concept is measured against the following criteria: 
• At least eighty percent (80%) of the agreed question set of about thirty (30) business 
questions, drawn from MEPWELL, SDEDBPROD, and MEPS_ARIES, is answered correctly, 
as judged by Client’s subject matter experts. 
• Every write attempt in the test suite is refused by both AgentCore Policy and AWS Lake 
Formation, and the assistant has no network path to Client’s on-premises databases. 
• A user outside a permitted Entra ID group cannot see restricted tables or the masked 
column, whether they ask through Teams or through Claude Code or Claude Desktop. 
• Every question asked during the pilot traces in the audit log to a named user, with the 
SQL that ran and the number of rows returned. 
• Typical questions are answered in the Teams channel within sixty (60) seconds. 
• The daily load of all three databases runs without intervention for the final two (2) weeks 
of the proof of concept. 
• IT and PMO users can list tables, describe columns, sample rows, and run a SELECT query 
from Claude Code or Claude Desktop under their own sign-in. 
• At handover, the AWS Control Tower landing zone reports no drift, its enabled controls 
report compliant, and the POC workload account is enrolled. 
 
FEES: 
Client acknowledges that the Services described in this Statement of Work are being provided at no 
cost. No fees or expenses will be invoiced by CapNexus for this engagement unless otherwise agreed in 
writing by both parties. 
Fees 
Cost (USD) $45,980.00 
Discount (CapNexus + AWS Contribution) ($45,980.00) 
Total Cost (USD) $0.00 
 
TERMS AND CONDITIONS: 
1. CapNexus resources will not be scheduled until a copy of this SOW has been signed by an 
authorized representative of Client and returned to CapNexus, with work start dates contingent 
on resource availability. 
2. The period of support for Client User Acceptance Testing (UAT), commences upon CapNexus 
delivery to the Client test environment and runs continuously for a two (2) week duration. Delay 
in client testing or requests for additional time will be subject to change control. 
3. No travel is planned under this SOW. Any travel and associated expenses must be pre-approved 
in writing by Client before they are incurred. 
Docusign Envelope ID: 534DE2FD-2D6D-8156-80D5-274B5B4EBB09

Mitsui.CapNexus.SOW2026001 
4. Requests for additional time or resources are subject to the Change Control process and to 
resource availability. Any fees for a change are stated in the change request and apply only when 
both parties approve it in writing. 
WORK FOR HIRE: 
1. Work Product, Proprietary Rights, and Pre-Existing Work. If CapNexus delivers or is required to 
deliver to Client any work product in connection with the Services, including but not limited to 
concepts, works, inventions, information, drawings, designs, programs, or software (whether 
developed by CapNexus or any of its Personnel, either alone or with others, and whether 
completed or in-progress) (collectively, “Work Product”), then Client owns, or CapNexus hereby 
irrevocably assigns to Client, and shall cause its Personnel and subcontractors to assign, all right, 
title and interest (including, but not limited to, all trademarks, trade secrets, copyrights, patents 
and any other intellectual property or proprietary rights) (collectively, "Proprietary Rights") in 
such Work Product to Client, except that Work Product does not include: (a) any inventions or 
developments made by CapNexus prior to the Effective Date, being the date on which both parties 
have signed this SOW; or (b) any improvements CapNexus may make to its own proprietary 
software or any of its internal processes as a result of this SOW, provided that such improvements 
do not infringe Client’s Proprietary Rights (“Pre-Existing Work”). To the extent any Pre-Existing 
Work is incorporated into the Work Product, CapNexus hereby grants Client and its affiliates a 
perpetual, irrevocable, royalty-free, non-exclusive license to use, copy, and modify such Pre-
Existing Work as part of the Work Product. 
2. Work for Hire. The Work Product has been specially ordered and commissioned by Client. 
CapNexus agrees that the Work Product is a "work made for hire" for copyright purposes, with all 
copyrights in the Work Product owned by Client. 
3. Retained Rights and License Back. Notwithstanding the foregoing assignment of Work Product 
and Proprietary Rights to Client, CapNexus retains, and Client hereby grants to CapNexus, a 
perpetual, irrevocable, worldwide, royalty-free, fully paid-up, non-exclusive, and sublicensable 
license to use, reproduce, modify, create derivative works of, distribute, and incorporate into 
CapNexus’s own products, services, platforms, and future client engagements any (a) generic 
methodologies, (b) software architectures, design patterns, and reusable components, (c) data 
acquisition and ingestion patterns, (d) analytical techniques, (e) algorithms and scoring 
methodologies, and (f) general know-how, skills, and experience of CapNexus personnel 
developed, derived, or improved during the course of this engagement. The foregoing retained 
rights do not extend to, and this license shall not include: (i) Client’s confidential information as 
described in the Confidentiality/Publicity section of this SOW, (ii) Client’s proprietary business 
data, trade secrets, and operational data, (iii) Client-specific business logic, workflows, or 
configurations developed uniquely for Client’s operations, (iv) Client’s trademarks, trade names, 
service marks, branding, or product identifiers, or (v) any output or deliverable in a form that 
would permit identification of Client, Client’s business, or Client’s customers. 
INDEMNITY: 
Docusign Envelope ID: 534DE2FD-2D6D-8156-80D5-274B5B4EBB09

Mitsui.CapNexus.SOW2026001 
1. CapNexus agrees to accept defence and defend, indemnify and hold harmless Client (including its 
subsidiaries, employees, directors and affiliates) from and against all claims and actions, including 
all expenses incidental to such claims and actions, based on or arising out of damages or injuries 
to persons or property caused by wilful misconduct, error, negligent act or omission of CapNexus 
or any of its agents, subcontractors and employees in the performance of Services which arise out 
of this SOW, except to the extent that such claims and actions arise out of Client's wilful 
misconduct, error, negligent act or omission. 
2. Client agrees to accept defence and defend, indemnify and hold harmless CapNexus from and 
against all claims and actions, including all expenses incidental to such claims and actions, based 
on or arising out of, damages or injuries to persons or property caused by wilful misconduct, error, 
negligent act or omission of Client or any of its agents, subcontractors and employees which arise 
directly in connection with this SOW, except to the extent that such claims and actions arise out 
of CapNexus's wilful misconduct, error, negligent act or omission. 
3. CapNexus agrees to accept defence and defend, indemnify and hold harmless the Client and any 
of its subsidiaries, employees, directors and affiliates from and against all claims and actions, 
including all expenses incidental to such claims and actions PREMISED UPON ALLEGED 
INFRINGEMENT OF PATENTS, COPYRIGHTS, TRADEMARKS, LICENSES, SOFTWARE COPYRIGHT OR 
OTHER SOFTWARE RIGHTS, OTHER INTELLECTUAL PROPERTY RIGHTS, OR UNFAIR COMPETITION, 
arising out of the Services or Work Product provided by CapNexus under this SOW. 
4. CapNexus agrees to accept defense and defend, indemnify and hold harmless Client and any of 
its subsidiaries, employees, directors and affiliates from and against all third-party claims and 
actions, including all expenses incidental to such claims and actions, arising out of (a) any breach 
by CapNexus or its agents, subcontractors or employees of the Confidentiality/Publicity section 
of this SOW, (b) any unauthorized access to, or use or disclosure of, Client's data or systems 
caused by CapNexus or its agents, subcontractors or employees, or (c) any violation of applicable 
law by CapNexus or its agents, subcontractors or employees in the performance of the Services. 
INSURANCE:  
During the Period of Performance of this SOW, CapNexus shall maintain commercial general liability and 
cyber/technology errors and omissions insurance in amounts customary for its industry, and shall provide 
certificates of insurance to Client upon request. 
CONFIDENTIALITY/PUBLICITY: 
Each Party and its representatives (a) will protect and keep confidential the existence of this SOW, its 
terms and conditions and any other information obtained in connection with this SOW or related to the 
Services that is identified as confidential or proprietary or that, given the nature of such information or 
the manner of its disclosure, reasonably should be considered confidential or proprietary (including but 
not limited to all information relating to Client’s or its affiliates’ technology, geophysical data, customers, 
vendors, royalty owners, lessors, business plans, marketing activities and finances), (b) will use such 
information only for the purpose(s) for which it was originally disclosed and in any case only for the 
Docusign Envelope ID: 534DE2FD-2D6D-8156-80D5-274B5B4EBB09

Mitsui.CapNexus.SOW2026001 
purpose of fulfilling its obligations under this SOW.  
NON-SOLICITATION: 
Each party covenants and agrees that neither will, during the term of this SOW, and for a period of twelve 
(12) months thereafter, regardless for the reason for termination of this SOW, directly or indirectly solicit 
for employment and/or engage personnel for CapNexus Services without the express written consent of 
the other party. 
CHANGE CONTROL: 
Any services outside of the scope of this Statement of Work will be contracted under separate commercial 
cover in a document executed by both parties to this SOW (i.e., Change Control or additional SOW signed 
by the parties). 
 
GOVERNING LAW: 
This SOW shall be governed by the laws of the State of Texas, without regard to its conflict of laws 
principles. The exclusive venue for any dispute arising out of this SOW shall be the state or federal courts 
located in Harris County, Texas. 
 
ACCEPTANCE AND AUTHORIZATION: 
The terms and conditions of this Statement of Work apply in full to the services and products provided 
herein. 
IN WITNESS WHEREOF, the parties hereto each acting with proper authority have executed this SOW, 
under seal. 
Mitsui E&P USA LLC   CapNexus, LLC 
 
 
  
Full name   Full name 
      
  
Title   Title 
      
  
Signature   Signature 
      
Docusign Envelope ID: 534DE2FD-2D6D-8156-80D5-274B5B4EBB09
11/9/2026
Manager - IT
Noah Jackson
 MARY HALE
EVP Finance & Admin
11/9/2026

Mitsui.CapNexus.SOW2026001 
  
             Date                 Date 
Docusign Envelope ID: 534DE2FD-2D6D-8156-80D5-274B5B4EBB09
