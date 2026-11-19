---
id: F02-S01
feature: F2
title: Run the pre-flight checks and confirm services in us-east-1
tier: integrate
executor: mixed
owner: Soma
repo: planning
status: blocked
sow: D2
due: 2026-11-17
blocked_by: [DEP-02, DEP-06]
depends_on_stories: []
params: [aws_home_region, aws_allowed_regions]
human_gates: [Mitsui creates the cross-account role and sends its ARN]
---

## Story

As Soma (solution architect), I want to confirm that the management account is ready for Control Tower and that every service the design needs exists in us-east-1, so that we find a design gap in Week 1 and not in Week 3.

## Context

Task list Tue Nov 17. Mitsui creates a temporary cross-account role (AdministratorAccess, MFA and external ID, 4-hour sessions, 7-day expiry). CapNexus tests it and answers the Appendix B pre-flight questions. The service check covers AgentCore Gateway, Identity, Runtime and Policy, S3 Tables with Lake Formation, identity-aware Athena workgroups and Claude model access (risk 17).

Out of scope: launching Control Tower (F02-S06) and the Bedrock call itself (F02-S08).

## Acceptance criteria

1. Given the role ARN from Mitsui, when a CapNexus engineer assumes it with MFA and the external ID, then the call succeeds and `sts get-caller-identity` shows the management account.
   - gate: Mitsui sends the role ARN. Soma saves the `get-caller-identity` output (account ID only) in `evidence/F02/preflight/`.
2. Given the management account, when the pre-flight checks run, then Organizations is in all-features mode, Config trusted access status is known, and STS is active in us-east-1. Each Appendix B question has an answer.
   - verify: `scripts/check-appendix-b.sh evidence/F02/preflight/appendix-b.md` exits 0 when all 13 questions have an answer. Script is created by this story.
3. Given the list of eight services, when each is checked in us-east-1, then the result (available, limited, missing) and a source link are recorded, and any gap is added to the RAID log as a design risk.
   - verify: `evidence/F02/preflight/service-availability.md` lists all eight services with a result and a link.
   - gate: Soma reviews each gap and records the design response in the RAID log.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-02 | D+B | Management account with root MFA and the cross-account role | None. The story waits. |
| DEP-06 | A+D | Service availability and Claude model access in us-east-1 | `aws_home_region`, `aws_allowed_regions` |

## Evidence

`evidence/F02/preflight/`: caller identity (account ID only), Appendix B answers, service availability table.

## Status log

- 2026-11-19: created
