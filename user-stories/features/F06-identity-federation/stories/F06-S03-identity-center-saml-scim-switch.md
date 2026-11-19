---
id: F06-S03
feature: F6
title: Switch Identity Center to Entra with SAML and SCIM
tier: integrate
executor: mixed
owner: Soma
repo: project-mep-AWS-Infrastructure
status: blocked
sow: D4
due: 2026-12-01
blocked_by: [DEP-02, DEP-14, DEP-29]
depends_on_stories: [F06-S02]
params: [entra_groups, aws_home_region]
human_gates: [Identity-source switch done once with the Entra administrator, CapNexus engineers confirm Entra sign-in]
---

## Story

As Soma (solution architect), I want IAM Identity Center to use Entra ID as its identity source with SCIM provisioning, so that Mitsui users and groups sign in with their Mitsui accounts and Lake Formation can grant access by Entra group.

## Context

Task list Week 3, Tue Dec 1. Steps follow item 5.2. The switch is done once, in one session, in the management account (enabled in F2). The agent writes the permission sets and the group-to-account assignments as code, so they can be reviewed and redeployed. The switch itself is a console action with the Entra administrator.

Before the switch, every CapNexus engineer must have a working Entra guest account (DEP-29). Otherwise they lose portal access.

Out of scope: trusted token issuer (F06-S05).

## Acceptance criteria

1. Given the permission sets and assignments as code, when synthesized, then `sg-wda-capnexus-engineers` and `sg-wda-admins` are assigned to the POC workload account with the agreed permission sets, and no user is assigned directly.
   - verify: `make test-identity-assignments` passes. Target created by this story.
2. Given the switch session, when SCIM provisioning runs, then users and all seven groups appear in Identity Center, and no group in Identity Center has nested members.
   - verify: `scripts/check-identity-center-groups.sh` (lists groups through `aws identitystore list-groups` and compares with `entra_groups`) exits 0. Script created by this story.
3. Given the switch is done, when a test user signs in to the AWS access portal, then sign-in goes through Entra and lands in the assigned account.
   - gate: screenshot saved in `user-stories/evidence/F06/`.
4. Given the switch is done, when each CapNexus engineer signs in, then each reaches the POC workload account through Entra.
   - gate: each engineer confirms in the shared Teams channel.
5. Given the SCIM token was created, when the session ends, then its expiry date is recorded for the runbook.
   - gate: date recorded in the RAID log.

## Dependencies

| ID | Type | What the story needs | Placeholder used until resolved |
|---|---|---|---|
| DEP-02 | D+B | Management account with Identity Center enabled | none |
| DEP-14 | D+B+A | Entra admin in the switch session | none |
| DEP-29 | D | CapNexus Entra guest accounts | none |

## Evidence

Group check output, portal sign-in screenshot, engineer confirmations.

## Status log

- 2026-11-19: created
