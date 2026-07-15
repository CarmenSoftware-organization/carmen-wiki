---
title: Vendor Pricelist — User Flow — Finance (Correction)
description: Correction page — Finance is not a distinct persona in the vendor-pricelist module; no co-signoff or variance-audit mechanism exists here.
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, user-flow, finance, inventory, carmen-software, correction
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — User Flow — Finance (Correction)

> **This page previously described a full Finance Officer / Finance Manager persona** — a multi-currency / high-value pre-activation co-signoff gate and a post-receipt variance-audit dashboard joining pricelist rows to GRN and invoice records. Re-reading `price-list.service.ts`, `price-list-template.service.ts`, and `request-for-pricing.service.ts` directly (2026-07-16) found no matching code for any of it, and no `enum_stage_role` member for `finance` exists anywhere in the schema — mirroring the identical, already-confirmed finding for the `purchase-order` and `good-receive-note` modules' own Finance-persona pages.

## What was claimed vs. what exists

| Claim | Status |
| ----- | ------ |
| Finance Manager co-signoff required to activate a multi-currency or "high-value" pricelist. | **Not implemented.** There is no distinct approve endpoint on Price List at all — `status` is set via the ordinary update call, by whoever has edit rights on the record. A repo-wide search for `threshold` in this module returns zero relevant hits. |
| Finance Officer variance-audit dashboard joining `tb_pricelist_detail` to posted GRN / invoice records. | **Not implemented.** No such dashboard, report, or query surface exists in this module's frontend or backend. |
| Finance-side `system` comments recording sign-off / variance categorisation. | **Not implemented.** No service in this module writes a comment row automatically under any circumstance — see [01a-data-model-comments](/en/inventory/vendor-pricelist/01a-data-model-comments). |
| Currency / FX validation performed by Finance at pricelist activation. | **Not implemented.** No FX-rate lookup or currency-permitted-list check exists in `price-list.service.ts`. |

## What is real

- Any user with read access to the Price List screen can see a pricelist's `currency_id`/`currency_code` and its detail rows — there is nothing that specifically routes this to a Finance-tagged user.
- GRN-side price variance, if implemented, is a [good-receive-note](/en/inventory/good-receive-note) module concern; consult that module's own resync findings rather than this page for what GRN actually compares against a pricelist.
- If a Finance-facing variance or currency-governance surface is wanted, it does not exist today and would be new-feature work, not a documentation gap.

## References

- [vendor-pricelist](/en/inventory/vendor-pricelist) — module landing, corrected roles table.
- [02-business-rules.md](./02-business-rules.md) § 4 — confirmed-vs-design-target authorization claims.
- [03-user-flow.md](./03-user-flow.md) — persona index (Finance removed).
- [good-receive-note](/en/inventory/good-receive-note) — the module that actually owns any GRN-side price-variance behaviour.
