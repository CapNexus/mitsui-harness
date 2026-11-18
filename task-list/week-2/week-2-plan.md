# Week 2: Connectivity and the first data loads

Dates: Nov 23 to Nov 27 (Thanksgiving Thu Nov 26)

**Goal:** VPN up, DMS (Database Migration Service) loading approved tables into S3, SDEDBPROD approach decided, approved table list signed, SME work started. Heavy work is Monday to Wednesday because Thursday and Friday are the Thanksgiving holiday.

## Mon 2026-11-23: VPN validation and SDEDBPROD decision

| Done | Owner | Task |
|---|---|---|
| [ ] | Engagement Manager | Weekly status call, 3:00 PM Eastern (2:00 PM Central). Send the CapNexus standard report to the kick-off attendees. |
| [ ] | Solution Architect | Validate both VPN tunnels. Run TCP tests from the DMS subnet to each SQL Server on its fixed port (item 3.3). |
| [ ] | Engagement Manager with Noah Jackson | Decision needed before the first load: SDEDBPROD compress to state zero, or versioned views. Name an owner (item 4.4). |
| [ ] | Engagement Manager | Run the SME data-model session. Collect ER (entity-relationship) diagrams, data dictionaries and the well identifier crosswalk rules (item 4.6). |
| [ ] | Engagement Manager | Confirm the daily load window and blackout periods with database administrators (item 4.5). |

## Tue 2026-11-24: DMS setup

| Done | Owner | Task |
|---|---|---|
| [ ] | Data & Platform Engineer | Create the DMS replication instance, source endpoints and S3 staging bucket. Store SQL credentials in Secrets Manager with a customer-managed KMS (Key Management Service) key. |
| [ ] | Data & Platform Engineer | Run DMS test connection for all three endpoints. Fix port, certificate or authentication problems with the database administrators. |
| [ ] | Data & Platform Engineer | Design table mappings with lowercase names and a source-to-target name mapping table. |
| [ ] | Solution Architect | Entra administrator session 1: federation and SCIM (System for Cross-domain Identity Management) planning, Entra ID P1 licence check (risk 12). |
| [ ] | Engagement Manager with Noah Jackson | Sign off the approved table list (Appendix E1), including the MEPWELL well hub and crosswalk tables. Deadline is end of Week 2. |

## Wed 2026-11-25: First full loads

| Done | Owner | Task |
|---|---|---|
| [ ] | Data & Platform Engineer | Run the first full load of MEPWELL, then MEPS_ARIES, then SDEDBPROD (after the approach is in place). |
| [ ] | Data & Platform Engineer | Build the row-count check after each load and the alarm for partial loads (risk 9). |
| [ ] | Data & Platform Engineer | Load staged data into S3 Tables with Athena or Glue. Test one known recent SDEDBPROD edit shows up (item 4.4). |
| [ ] | CapNexus AI Engineer | Start the SME question writing with the outline from Deliverable 1. Target about 30 questions, 7 per database and 9 joins (item 9.2). |
| [ ] | Engagement Manager | Pre-fill the description sheet (Appendix E2) from table names and data types and send it to the SMEs. |
| [ ] | Engagement Manager | Pre-announce holiday coverage and the Week 3 Teams approval deadline to Noah Jackson. |

## Thu 2026-11-26: Thanksgiving, no planned work

| Done | Owner | Task |
|---|---|---|
| [ ] | Whole CapNexus team | Holiday. No tasks scheduled. DMS and VPN alarms stay on and go to the on-call address. |

## Fri 2026-11-27: Buffer day, no planned work

| Done | Owner | Task |
|---|---|---|
| [ ] | Whole CapNexus team | Day after Thanksgiving. Planned as a buffer. If Wednesday loads failed, only the Data & Platform Engineer picks up reruns. Everything else moves to Monday. |

## Exit criteria

- [ ] Both VPN tunnels UP and TCP tests pass from the DMS subnet to all three SQL Servers
- [ ] DMS test connection succeeds for MEPWELL, SDEDBPROD and MEPS_ARIES
- [ ] At least one full load of each database lands in the S3 staging bucket with row counts checked
- [ ] SDEDBPROD approach decided with a named owner
- [ ] Approved table list signed off by data owners
- [ ] Daily load window agreed
