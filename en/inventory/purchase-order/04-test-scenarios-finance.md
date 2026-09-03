---
title: Purchase Order — Test Scenarios — Finance
description: Why no three-way-match / AP test scenarios exist for purchase-order in current source, and what is confirmed instead.
published: true
date: 2026-07-15T12:00:00.000Z
tags: purchase-order, test-scenarios, finance, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# Purchase Order — Test Scenarios — Finance

> **At a Glance**
> **Persona:** Finance — **unconfirmed as a distinct persona in current source** &nbsp;·&nbsp; **Module:** [purchase-order](/en/inventory/purchase-order)
> **E2E coverage:** none confirmed. A prior version of this page cited `403-po-finance-ap-match.spec.ts`, which **does not exist** in `../carmen-inventory-frontend-e2e/tests/`.

> ⚠️ **Major correction this pass.** The previous version of this page listed ~25 scenarios (FIN-HP-01 through FIN-EDGE-05) covering a pre-transmission Finance Manager sign-off stage and a Finance Officer three-way-match / AP-posting flow, including specific GL account entries, purchase-price-variance handling, and FX-adjustment postings. None of this maps to current source:
> - The cited spec file `403-po-finance-ap-match.spec.ts` was checked directly and **does not exist** in the e2e test directory. This means every "E2E coverage" claim on the removed scenarios was fabricated alongside the feature itself.
> - A repo-wide search of `carmen-turborepo-backend-v2` and `carmen-inventory-frontend-react` for `three-way`, `vendor_invoice`, `VendorInvoice`, and `tb_invoice` returned zero hits.
> - See [03-user-flow-finance.md](./03-user-flow-finance.md) for the full correction and what evidence was checked.
>
> This page is kept, rather than deleted, to record the correction and point to what actually exists. No scenario table is reconstructed here because there is no confirmed feature to write test scenarios against.

## What Was Removed and Why

| Removed scenario group | Reason |
|---|---|
| FIN-HP-01 through FIN-HP-06 (pre-transmission sign-off, three-way match, PPV, FX adjustment, GL postings) | No invoice-capture, AP-posting, or match-algorithm code found anywhere in current source. |
| FIN-PERM-01 through FIN-PERM-07 | Depend entirely on the non-existent AP/invoice feature and a `finance` stage role that does not exist in `enum_stage_role`. |
| FIN-VAL-01 through FIN-VAL-07 | Same — validation rules for a feature that is not implemented. |
| FIN-EDGE-01 through FIN-EDGE-05 | Same. |

## What Is Confirmed Instead

- Any user (regardless of title) can be assigned to a generic `approve` workflow stage — see [04-test-scenarios-procurement-manager.md](./04-test-scenarios-procurement-manager.md) for the real, e2e-grounded mechanics of stage approval, send-back, and reject. A tenant could name that stage's assigned user "Finance Manager," but no code treats them differently from any other approver.
- [Credit Note](/en/inventory/purchase-order/credit-note) is a real, implemented AP-adjacent document with confirmed Prisma tables and routes. It posts an AP debit memo against a prior GRN; it is not a three-way match and has no dedicated test-scenario page in this module (it is a sibling document type, not a PO-module persona).

## References

- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) — the full correction, including the exact searches run and what they returned.
- Sibling: [04-test-scenarios-procurement-manager.md](./04-test-scenarios-procurement-manager.md) — the real, e2e-grounded generic approval-stage mechanics.
- [Credit Note](/en/inventory/purchase-order/credit-note) — the one real AP-adjacent feature in this module.
- Business rules: [02-business-rules.md](./02-business-rules.md) § 5 (`PO_POST_008` / `PO_POST_009`, marked not implemented), § 6 (`PO_XMOD_007`, marked not implemented).
