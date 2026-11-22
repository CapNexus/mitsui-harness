---
id: F02-S01
feature: F2
title: Run the pre-flight checks and confirm services in us-east-1
tier: integrate
executor: mixed
owner: Soma
repo: planning
status: in-progress
sow: D2
due: 2026-11-17
blocked_by: [DEP-06]
depends_on_stories: []
params: [aws_home_region, aws_allowed_regions]
human_gates: [Mitsui answers the Appendix B questions in writing]
---

## Story

As Soma (solution architect), I want to confirm that the Mitsui organization is ready for the POC and that every service the design needs exists in us-east-1, so that we find a design gap in Week 1 and not in Week 3.

## Context

Task list Tue Nov 17. Mitsui already set up Control Tower in the management account `463768556578` (RAID I-11, decided 2026-11-22). CapNexus has no role in the management account. CapNexus works through `CapNexusDeploymentRole` in the Identity Delegated Admin account `166390307071` (delegated for IAM Identity Center and account access), so the Appendix B answers that need the management account come from Mitsui in writing. The service check covers AgentCore Gateway, Identity, Runtime and Policy, S3 Tables with Lake Formation, identity-aware Athena workgroups and Claude model access (risk 17).

Out of scope: verifying the landing zone (F02-S06) and the Bedrock call itself (F02-S08).

## Acceptance criteria

1. Given `CapNexusDeploymentRole`, when a CapNexus engineer assumes it, then the call succeeds and `sts get-caller-identity` shows account `166390307071`.
   - gate: Soma saves the `get-caller-identity` output (account ID and role name only, no keys) in `evidence/F02/preflight/`.
2. Given the organization, when the pre-flight checks run, then Organizations is in all-features mode and the account list is recorded. Each Appendix B question has an answer, and Mitsui supplies the ones that need management-account access (Config trusted access, STS in us-east-1).
   - verify: `scripts/check-appendix-b.sh evidence/F02/preflight/appendix-b.md` exits 0 when all 13 questions have an answer. Script is created by this story.
   - gate: Noah Jackson or Matt Schiefelbein sends the written answers.
3. Given the list of eight services, when each is checked in us-east-1, then the result (available, limited, missing) and a source link are recorded, and any gap is added to the RAID log as a design risk.
   - verify: `evidence/F02/preflight/service-availability.md` lists all eight services with a result and a link.
   - gate: Soma reviews each gap and records the design response in the RAID log.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-06 | A+D | Service availability and Claude model access in us-east-1 | `aws_home_region`, `aws_allowed_regions` |

## Evidence

`evidence/F02/preflight/`: caller identity (account ID and role name only), Appendix B answers, service availability table.

## Status log

- 2026-11-19: created
- 2026-11-22: rescoped after RAID I-11. Control Tower exists in `463768556578`. CapNexus role is in `166390307071`. DEP-02 removed from `blocked_by`, status set to ready. `organizations describe-organization` shows management account `463768556578` and feature set ALL.
- 2026-11-22: in-progress. Built check-appendix-b.sh with tests (plan in specs/checker-scripts/F02-S01-preflight-and-service-availability.md). Evidence in evidence/F02/preflight/: caller identity, ppendix-b.md (4 of 13 answered), service-availability.md (eight services, two limited: RAID R-02, R-03). Open gates: Mitsui answers questions 4 to 11 and 13, Soma saves live get-caller-identity output and records design responses for R-02 and R-03.
