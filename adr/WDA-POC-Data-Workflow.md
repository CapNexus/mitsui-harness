# Well Data Assistant POC: Data Workflow

Mitsui E&P USA and CapNexus, SOW Mitsui.CapNexus.SOW2026001.

This document describes how data and identity move through the Well Data Assistant POC. It pairs with the architecture diagram [WDA-POC-Architecture.drawio](WDA-POC-Architecture.drawio). Step IDs (D1 to D8, Q1 to Q9, C1, I1 to I3, A1 to A2) are the same in both files.

## 1. Sources and assumptions

Sources: the signed SOW, the Kickoff Agenda, the Client Dependencies and Sharing Strategy (rev 1.6), and the task list under `task-list/`.

Where the documents differ, this file follows the task list. The one exception is the unattended-load window: it is Mon Dec 14 to Fri Dec 25 (decided Nov 17, matching the Dependencies document). The task list was updated to match.

Assumptions made where the sources are silent. Please correct any that are wrong:

| # | Assumption | Basis |
|---|---|---|
| 1 | The compute behind the four MCP tools, and behind the Teams bot messaging endpoint, is not named in the SOW. The diagram shows them as boxes without a service icon. | SOW names AgentCore Gateway, Runtime and Policy only. |
| 2 | The load step from the S3 staging bucket into S3 Tables uses Athena or Glue, whichever the Data & Platform Engineer picks. | Dependencies doc, finding 3. |
| 3 | Row limit and timeout values enforced by AgentCore Policy are not set yet, so none are shown. | SOW says "row limits and timeouts" without numbers. |
| 4 | Daily load window is not agreed. The 1:00 to 4:00 AM Central example is only an example. | Open item 4.5. |
| 5 | The SDEDBPROD approach (compress to state 0, or versioned `_evw` views) is undecided and has no owner. Both are shown. | Open item 4.4. |

## 2. Data end to end

Mitsui data is copied once a day, one way, into the POC account. Nothing flows back to the source databases.

```mermaid
flowchart LR
    subgraph ONPREM["Mitsui data center"]
        DB1["MEPWELL<br/>well hub and crosswalk<br/>about 0.2 GB"]
        DB2["SDEDBPROD<br/>ArcGIS geodatabase<br/>about 10 GB"]
        DB3["MEPS_ARIES<br/>economics and reserves<br/>about 5 GB"]
        PA["Palo Alto VPN device"]
    end

    subgraph AWSVPC["POC account, us-east-1, workload VPC"]
        VGW["Virtual private gateway"]
        DMS["AWS DMS<br/>replication instance"]
    end

    subgraph LAKE["Governed data lake"]
        STG[("S3 staging bucket<br/>CSV or Parquet")]
        LOAD["Glue or Athena load job<br/>plus row-count check"]
        S3T[("S3 Tables<br/>approved tables only")]
        CAT["Glue Data Catalog<br/>table and column descriptions"]
        LF["Lake Formation<br/>Entra group permissions<br/>and column masking"]
    end

    ATH["Amazon Athena<br/>identity-aware workgroup"]

    DB1 --> PA
    DB2 --> PA
    DB3 --> PA
    PA -- "D1 and D2: read-only SQL over IPsec VPN" --> VGW
    VGW -- "D3: private route, DMS subnet only" --> DMS
    DMS -- "D4: daily one-way full load" --> STG
    STG -- "D5: load approved tables" --> LOAD
    LOAD -- "D6: write lowercase tables" --> S3T
    S3T -- "D7: register" --> CAT
    LF -- "D8: governs access" --> CAT
    LF -- "governs access" --> S3T
    ATH -- "Q9: SELECT" --> S3T
    ATH -. "authorize and mask" .-> LF
```

| Step | What happens | Control |
|---|---|---|
| D1 | DMS reads the approved tables with a SQL-authenticated, read-only login (`db_datareader`, `VIEW DATABASE STATE`, `VIEW DEFINITION`). | No `sysadmin` or `db_owner`. Credentials sit in Secrets Manager, encrypted with a customer-managed KMS key. |
| D2 | Traffic crosses the site-to-site VPN (two IPsec tunnels, Palo Alto on the Mitsui side). | Firewall allows only the DMS subnet, to a fixed TCP port per instance (default 1433). |
| D3 | The virtual private gateway routes to the DMS replication instance. | Only the DMS subnet has a route to the VPN. The assistant has no network path to the databases. |
| D4 | DMS writes CSV or Parquet to a regular S3 bucket. | DMS cannot write directly to S3 Tables, so this staging step is required. |
| D5 | A Glue or Athena job loads the approved tables from staging into S3 Tables. | Row counts are compared with the source after every load. A partial-load alarm covers DMS marking a dropped load as complete. |
| D6 | Tables are written with lowercase table and column names. | A source-to-target name mapping table is kept. Lake Formation and Glue require lowercase. |
| D7 | The tables are registered in the Glue Data Catalog with SME-written table and column descriptions. | The `describe_columns` tool reads these descriptions, so they drive SQL quality. |
| D8 | Lake Formation grants access by Entra group and masks at least one column. | Matrix signed off by Noah Jackson (tables) and Matt Schiefelbein (groups). |

## 3. Daily load run

The load runs once a day inside the agreed window. It must run without intervention for the final two weeks of the POC (Dec 14 to Dec 25).

```mermaid
sequenceDiagram
    autonumber
    participant GIS as GIS admin job (SDEDBPROD)
    participant SCH as DMS task schedule
    participant SQL as SQL Server (3 databases)
    participant DMS as AWS DMS
    participant STG as S3 staging bucket
    participant JOB as Glue or Athena load job
    participant S3T as S3 Tables and Glue Catalog
    participant CW as CloudWatch alarms
    participant DBA as Mitsui DL and CapNexus on-call

    GIS->>SQL: Compress geodatabase to state 0 (or expose versioned views)
    Note over GIS,SQL: Open decision. Must finish before the load window starts.
    SCH->>DMS: Start full-load task inside the window
    DMS->>SQL: Read approved tables (read-only login, over VPN)
    SQL-->>DMS: Rows
    DMS->>STG: Write CSV or Parquet files
    DMS-->>CW: Task status and errors
    DMS->>JOB: Task complete
    JOB->>STG: Read staged files
    JOB->>S3T: Replace tables (lowercase names)
    JOB->>DMS: Read table statistics (source row counts)
    JOB->>JOB: Compare source and target row counts
    alt Counts match
        JOB-->>CW: Load succeeded metric
    else Mismatch or task failed
        JOB-->>CW: Partial-load alarm
        CW->>DBA: Alarm email
        DBA->>SCH: Investigate and rerun (outside unattended window only for approved fixes)
    end
```

Rules for the unattended window (task list, Week 4 and Week 5):

- No manual loads and no source or VPN maintenance from Mon Dec 14 to Fri Dec 25. Mitsui DBAs and the network team are told in advance.
- Stable daily load by Fri Dec 11 is a hard target, and Dec 7 to Dec 11 is for stabilizing it.
- The load pipeline is frozen from Dec 14. Only fixes for a failed load are allowed.
- Fri Dec 25 is a holiday and the load still runs. On Thu Dec 24 the DMS task history and alarm history for Dec 14 to Dec 24 are exported as acceptance evidence. The Dec 25 run is checked on the next business day and added.

### Load decision flow

```mermaid
flowchart TD
    A["Load window opens"] --> B{"SDEDBPROD current?<br/>compressed to state 0<br/>or versioned views"}
    B -- "No" --> B1["Skip SDEDBPROD<br/>raise alarm to GIS admin"]
    B -- "Yes" --> C["DMS full load of 3 databases"]
    B1 --> C
    C --> D{"DMS task<br/>completed?"}
    D -- "No" --> X["Partial-load alarm<br/>email to Mitsui DL"]
    D -- "Yes" --> E["Load staged files into S3 Tables"]
    E --> F{"Row counts match<br/>source?"}
    F -- "No" --> X
    F -- "Yes" --> G["Update Glue Catalog<br/>metadata if schema changed"]
    G --> H["Data ready for questions"]
    X --> I["Investigate, fix, rerun"]
    I --> C
```

## 4. Business question to answer (Microsoft Teams)

A pilot user asks a question in the Teams channel. The assistant writes SQL, runs it as that user, and replies with a short table and the SQL. The target is a typical answer within 60 seconds.

```mermaid
sequenceDiagram
    autonumber
    actor U as Pilot user
    participant T as Microsoft Teams
    participant AB as Azure Bot Service (single tenant)
    participant WAF as AWS WAF and bot endpoint
    participant RT as AgentCore Runtime (assistant)
    participant BR as Bedrock Claude with Guardrails
    participant GW as AgentCore Gateway
    participant POL as AgentCore Policy
    participant TL as MCP tools
    participant ATH as Athena
    participant LF as Lake Formation
    participant S3T as S3 Tables

    U->>T: Q1 Ask a question in plain English
    T->>AB: Q2 Message with Teams sign-in token
    AB->>WAF: Q3 HTTPS POST /api/messages
    WAF->>WAF: Validate Bot Framework JWT
    WAF->>RT: Q4 Question plus user identity
    RT->>BR: Q5 Plan the steps
    RT->>GW: Q6 MCP call list_tables with user token
    GW->>GW: Validate Entra JWT (WDA-API audience)
    GW->>POL: Q7 Check tool, SELECT only, limits
    POL-->>GW: Allowed
    GW->>TL: Call tool
    TL->>ATH: Q8 Query as the signed-in user
    ATH->>LF: Check permissions for the user's groups
    LF-->>ATH: Allowed tables and masked columns
    ATH->>S3T: Q9 Read approved data
    S3T-->>ATH: Rows
    ATH-->>TL: Result (masked where required)
    TL-->>RT: Rows or schema
    loop Until the answer is ready
        RT->>BR: Next step (describe_columns, sample_rows, run_select)
        RT->>GW: Tool call with user token
    end
    RT->>BR: Format the answer
    RT-->>WAF: Short table plus the SQL that ran
    WAF-->>T: Reply
    T-->>U: Answer in channel
```

The assistant uses the four read-only tools in the usual order:

1. `list_tables` finds candidate tables.
2. `describe_columns` reads the SME descriptions and join hints.
3. `sample_rows` checks values and formats.
4. `run_select` runs the final SQL on Athena. Cross-database questions join MEPWELL, SDEDBPROD and MEPS_ARIES on well identifiers using the MEPWELL crosswalk tables.

## 5. IT/PMO access from Claude Code and Claude Desktop

IT/PMO users reach the same Gateway tools directly, under their own sign-in. The Teams bot and the assistant runtime are not involved.

```mermaid
sequenceDiagram
    autonumber
    actor IT as IT/PMO user (sg-wda-itpmo-tools)
    participant CL as Claude Code or Claude Desktop
    participant EN as Microsoft Entra ID
    participant GW as AgentCore Gateway
    participant POL as AgentCore Policy
    participant TL as MCP tools
    participant ATH as Athena and Lake Formation

    IT->>CL: Add the Gateway as an MCP server
    CL->>EN: Sign in with the pre-registered WDA-Clients app
    Note over CL,EN: Entra has no dynamic client registration.<br/>Conditional Access and MFA apply.
    EN-->>CL: Access token for WDA-API
    CL->>GW: C1 MCP call with Entra JWT
    GW->>GW: Validate issuer, audience and signature
    GW->>POL: Check tool, SELECT only, limits
    POL-->>GW: Allowed or refused
    GW->>TL: list_tables, describe_columns, sample_rows, run_select
    TL->>ATH: Query as the signed-in user
    ATH-->>TL: Rows (masked where required)
    TL-->>GW: Result
    GW-->>CL: Result
    CL-->>IT: Answer built by the user's Claude client
```

Open item: for Claude Desktop remote connectors, requests may come from Anthropic's cloud. If so, the Gateway must be reachable from the internet and protected by the JWT authorizer. Mitsui InfoSec decides on the connection method (item 8.1, Week 3 and Week 4). Rows returned by the tools reach the Claude client and its model provider, which InfoSec must accept.

## 6. Identity and permission flow

### 6.1 One-time setup

```mermaid
flowchart LR
    subgraph MITSUI["Mitsui Entra ID (Matt Schiefelbein)"]
        G["Security groups<br/>sg-wda-users-well, -geo, -econ<br/>sg-wda-econ-sensitive<br/>sg-wda-itpmo-tools"]
        APP["App registrations<br/>WDA-API, WDA-TeamsBot, WDA-Clients"]
    end
    subgraph MGMT["AWS management account"]
        IDC["IAM Identity Center<br/>external identity provider = Entra"]
        TTI["Trusted token issuer<br/>for the Entra tenant"]
    end
    subgraph POC["POC workload account"]
        LF["Lake Formation grants<br/>by Entra group"]
        GW["AgentCore Gateway<br/>JWT authorizer"]
        ATH["Athena workgroup<br/>identity-aware"]
    end

    G -- "I1: SAML sign-in and SCIM sync" --> IDC
    IDC --> LF
    APP -- "I2: OIDC discovery URL and WDA-API audience" --> GW
    APP --> TTI
    TTI -- "I3: trusted identity propagation" --> ATH
    ATH --> LF
```

SCIM does not sync nested groups, so group membership must be flat. The identity source is switched once, in one session (Tue Dec 1 in the task list).

Fallback (SOW Assumption 8): if the signed-in user cannot be carried through to Athena within the POC, the pilot runs on permissions by Entra group. The user is then logged at the application layer so every question still traces to a named person. Noah Jackson must accept this fallback in writing.

### 6.2 What each test user sees

The permission tests use three Entra users and run through Teams, Claude Code and Claude Desktop.

```mermaid
flowchart TD
    Q["Question arrives with<br/>the user's Entra token"] --> V{"Valid token<br/>for WDA-API?"}
    V -- "No" --> R1["Refused at Gateway"]
    V -- "Yes" --> W{"Tool is read-only<br/>and SQL is SELECT?"}
    W -- "No, write attempt" --> R2["Refused by AgentCore Policy"]
    W -- "Yes" --> L{"User's group allows<br/>the table?"}
    L -- "No" --> R3["Refused by Lake Formation<br/>table not visible"]
    L -- "Yes" --> M{"User in<br/>sg-wda-econ-sensitive?"}
    M -- "Yes" --> F["Full result<br/>unmasked column"]
    M -- "No" --> K["Result with masked column"]
```

| Test user | Group membership | Expected result |
|---|---|---|
| User A | All permitted groups, including `sg-wda-econ-sensitive` | Sees all approved tables and the unmasked column. |
| User B | Permitted groups, not `sg-wda-econ-sensitive` | Sees approved tables. The masked column is hidden. |
| User C | None of the groups | Sees no restricted tables and no masked column. |

Write attempts must be refused twice: by AgentCore Policy first, then by Lake Formation if the first layer were bypassed.

## 7. Audit and observability

Every question must trace to a named user, the SQL that ran, and the rows returned.

```mermaid
flowchart LR
    subgraph SRC["Event sources"]
        RT["AgentCore Runtime and Gateway"]
        BR["Bedrock model calls"]
        API["AWS API activity<br/>Athena, Lake Formation, DMS"]
        DMSEV["DMS task events<br/>and row-count checks"]
    end
    subgraph SINK["Observability stack"]
        AO["AgentCore Observability<br/>question, tool call, SQL,<br/>user, time, result size"]
        BL["Bedrock invocation logging<br/>prompts and responses"]
        CT["CloudTrail"]
        CW["CloudWatch dashboard<br/>and alarms"]
    end
    subgraph ORG["Log Archive account"]
        LA[("Log archive S3 bucket<br/>org trail and Config")]
    end
    SNS["SNS email to<br/>Mitsui distribution list"]

    RT -- "A1" --> AO
    BR --> BL
    API --> CT
    DMSEV --> CW
    AO --> CW
    BL --> CW
    CT --> CW
    CT -- "A2" --> LA
    CW -- "alarms" --> SNS
```

Handling notes:

- Logs are encrypted with the customer-managed KMS key. Retention uses AWS defaults (kickoff decision).
- Bedrock invocation logs contain question text and result rows, so they count as business data. Mitsui InfoSec decides who may read them (item 10.1).
- The CloudWatch dashboard reports latency, errors and throttling. The latency report supports the 60-second criterion.

## 8. Data readiness timeline

Dates follow the task list. Week 6 is test-only.

```mermaid
gantt
    title Data and access readiness (Nov 16 to Dec 25, 2026)
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Foundation
    Control Tower and POC account       :a1, 2026-11-16, 5d
    VPN and read-only SQL logins        :a2, 2026-11-16, 5d
    section Data load
    DMS setup and first full loads      :b1, 2026-11-23, 3d
    Approved table list signed off      :milestone, b2, 2026-11-27, 0d
    Schedule daily load                 :b3, 2026-12-01, 1d
    Four consecutive daily loads        :b4, 2026-12-01, 4d
    Unattended-load window              :crit, b5, 2026-12-14, 12d
    section Governance and identity
    Glue Catalog and SME descriptions   :c1, 2026-11-30, 11d
    Entra federation and token issuer   :c2, 2026-12-01, 2d
    Lake Formation and masking          :c3, 2026-12-02, 3d
    section Assistant and access
    MCP tools behind Gateway            :d1, 2026-12-02, 3d
    Assistant on AgentCore Runtime      :d2, 2026-12-07, 2d
    Teams bot and Claude clients        :d3, 2026-12-08, 2d
    section Validation
    Evaluation, permission and latency tests :e1, 2026-12-14, 5d
    UAT, acceptance and handover        :e2, 2026-12-21, 4d
```

## 9. Open items that change the data flow

| Item | Effect on the flow | Needed by | Owner |
|---|---|---|---|
| SDEDBPROD approach and owner (item 4.4) | Decides whether DMS reads base tables or `_evw` views. Without it the AWS copy can be stale. | Before first load, Mon Nov 23 | Noah Jackson (on hold, no owner) |
| Daily load window and blackout periods (item 4.5) | Sets the DMS schedule and the GIS compress timing. | Week 2 | Noah Jackson, DBAs |
| Masked column and classification rules (item 6.2) | Defines the Lake Formation data filter at step D8 and the User A/B/C results. | Week 3 | Noah Jackson, Matt Schiefelbein |
| TDE or other source restrictions, mixed-mode authentication (items 4.1, 4.2) | DMS needs SQL-authenticated logins. A Windows-only instance needs a restart and change window. | Week 1 | DBAs |
| Identity propagation to Athena (SOW Assumption 8) | If it fails, permissions are by Entra group with user logging in the application. | Week 3 | Solution Architect |
| Claude Desktop connection method (item 8.1) | May require the Gateway to be internet-reachable. | Week 3 to Week 4 | Mitsui InfoSec |
| Geometry storage and largest shape size (item 4.4) | Shape columns copy as text only where DMS supports the type. Limited-LOB mode with a size cap can truncate very large shapes. | Week 2 | GIS admin |
