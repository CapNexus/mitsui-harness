# F02-S01 Appendix B pre-flight answers

Questions copied from `knowledge/Mitsui-WDA-POC-Client-Dependencies-and-Sharing-Strategy.md`, Appendix B. An answer cell stays empty until the question is fully answered. Partial findings are in the notes below the table. Check with `bash user-stories/scripts/check-appendix-b.sh user-stories/evidence/F02/preflight/appendix-b.md` (run from the repository root). It exits 0 only when all 13 are answered.

Last updated 2026-11-22.

| # | Question | Mitsui answer |
|---|---|---|
| 1 | Is AWS Organizations enabled with **all features**? Management account ID? | Yes, feature set ALL. Management account 463768556578. Source: `aws organizations describe-organization`, run by Soma Muniyappa 2026-11-22. |
| 2 | Number and names of existing member accounts. Any named "Audit" or "Log Archive"? | Five accounts including management: AWSMEP-Management-Team Management Account (463768556578), Identity Delegated Admin (166390307071), Log Archive (707641390779), Audit (171584503454), Blank Canvas (108953016877). Log Archive and Audit exist. Source: `aws organizations list-accounts`, 2026-11-22. |
| 3 | Is there an existing AWS Control Tower landing zone (Statement of Work (SOW) says no)? | Yes. Mitsui set up Control Tower in the management account (Soma Muniyappa, 2026-11-20 and 2026-11-22). The SOW assumption no longer holds. Status is verified in F02-S06. |
| 4 | Is IAM Identity Center enabled? In which Region? Identity source? | |
| 5 | Is AWS Config trusted access enabled for the organization? Any existing Config recorder or delivery channel in the management account? | |
| 6 | Is there an organization CloudTrail trail? Other security tooling (GuardDuty, Security Hub, Macie)? | |
| 7 | Existing service control policies (SCPs), and which organizational units (OUs) they attach to. Any Region restriction? | |
| 8 | Are AWS STS endpoints active in the Regions we will govern? | |
| 9 | Is AWS Marketplace access allowed for the member accounts? | |
| 10 | Who receives root-account notices and who is the billing contact? | |
| 11 | Required tags, naming standards, Key Management Service (KMS) and encryption standards? | |
| 12 | Existing AWS service quotas that might be limiting in the management account? | New account, default quotas (kickoff). To reconfirm for Bedrock in F02-S08. |
| 13 | Is there an existing AWS-to-on-prem network (virtual private network (VPN), Direct Connect)? | |

## Notes on open questions

- 4: IAM Identity Center is administered from account 166390307071 (delegated since 2026-11-18, `sso.amazonaws.com`). Region and identity source are not confirmed. `aws sso-admin list-instances` from that account would answer both (read-only).
- 5, 6, 8, 9, 10, 11, 13: need management-account access or Mitsui's answer. Noah Jackson or Matt Schiefelbein reply in writing (F02-S01 gate).
- 7: the kickoff answer "no existing SCPs, US only" predates the Control Tower launch. Control Tower adds Region-deny and other controls, so Mitsui must restate it.
