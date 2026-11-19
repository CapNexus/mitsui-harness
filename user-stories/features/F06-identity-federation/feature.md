---
id: F6
title: Identity federation (Entra to AWS)
sow: D4
due: 2026-12-02
status: draft
depends_on_features: [F2]
blocked_by: [DEP-02, DEP-14, DEP-15, DEP-27, DEP-29]
---

## Description

Federate Microsoft Entra ID to IAM Identity Center (SAML sign-in, SCIM provisioning) and register a trusted token issuer for the Entra tenant. Create the Entra security groups (`sg-wda-users-well`, `-geo`, `-econ`, `sg-wda-econ-sensitive`, `sg-wda-itpmo-tools`, `sg-wda-admins`, `sg-wda-capnexus-engineers`) and the app registrations WDA-API, WDA-TeamsBot and WDA-Clients. Switch the identity source once, in one session. Test whether the signed-in user can be propagated to Athena.

Source: `WDA-POC-Feature-List.md`, F6. Workflow steps I1 to I3 in `adr/WDA-POC-Data-Workflow.md`, section 6.

## Feature-level acceptance criteria

| # | Criterion | Covered by |
|---|---|---|
| 1 | Entra users and groups appear in IAM Identity Center through SCIM, and group membership is flat (no nested groups). | F06-S02, F06-S03 |
| 2 | A test user signs in to the AWS access portal through Entra, and CapNexus engineers sign in the same way. | F06-S03 |
| 3 | WDA-API, WDA-TeamsBot and WDA-Clients exist with admin consent, and WDA-Clients is a pre-registered public client usable by Claude Code and Claude Desktop. | F06-S02 |
| 4 | The trusted token issuer maps the email claim, and a token from Entra is accepted for the WDA-API audience. | F06-S04, F06-S05 |
| 5 | Identity propagation test: a query run for User A in Athena is attributed to User A in CloudTrail or Athena query history. If this fails, the fallback (permissions by Entra group, user logged in the application) is documented and Noah Jackson accepts it in writing before Fri Dec 4. | F06-S06, F06-S07 |
| 6 | Conditional Access policies that apply to pilot, test and IT/PMO users are reviewed, and any that block loopback or device-code sign-in are listed with a resolution. | F06-S08 |

## Stories

| ID | Title | Tier | Executor | Blocked by | Status |
|---|---|---|---|---|---|
| [F06-S01](stories/F06-S01-entra-federation-prerequisites.md) | Confirm Entra prerequisites and run federation planning session | integrate | mixed | DEP-14 | blocked |
| [F06-S02](stories/F06-S02-entra-groups-and-app-registrations.md) | Create the Entra groups and app registrations | integrate | human | DEP-14 | blocked |
| [F06-S03](stories/F06-S03-identity-center-saml-scim-switch.md) | Switch Identity Center to Entra with SAML and SCIM | integrate | mixed | DEP-02, DEP-14, DEP-29 | blocked |
| [F06-S04](stories/F06-S04-trusted-token-issuer-construct.md) | Build the trusted token issuer and identity-aware Athena workgroup as code | build | agent | none | ready |
| [F06-S05](stories/F06-S05-trusted-token-issuer-mitsui-tenant.md) | Deploy the trusted token issuer for the Mitsui Entra tenant | integrate | mixed | DEP-14 | blocked |
| [F06-S06](stories/F06-S06-identity-propagation-sandbox-spike.md) | Spike identity propagation to Athena in the sandbox | build | agent | none | ready |
| [F06-S07](stories/F06-S07-identity-propagation-test-and-decision.md) | Test identity propagation in the POC account and decide the identity mode | integrate | mixed | DEP-27, DEP-14 | blocked |
| [F06-S08](stories/F06-S08-conditional-access-review.md) | Review Conditional Access for pilot, test and IT/PMO users | integrate | mixed | DEP-15 | blocked |

## Open points

- DEP-27 (type E) is open. F06-S07 sets the proposed parameter `identity_mode` (`propagated` or `group_fallback`). F7 and F8 build both modes behind this switch.
- Feature List Section 7, question 4: Entra P1 licence and UPN equals primary email are unconfirmed. F06-S01 confirms both. Without P1, SCIM and group assignment fail and F6 to F8 slip.
- The identity-source switch happens once, on Tue Dec 1. Any CapNexus engineer without a working Entra guest account (DEP-29) loses portal access at the switch.
- The SCIM token is valid for one year. Record the renewal date in the runbook (F14).
- Proposed new parameters, not yet in `config/parameters.md`: `identity_mode`, `test_users`.
