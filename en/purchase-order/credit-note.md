---
title: Credit Note
description: Vendor-issued credit document reversing all or part of a prior PO / GRN — adjusts AP liability and either cost-revalues the inventory layer or returns goods.
published: true
date: 2026-05-16T15:00:00.000Z
tags: purchase-order, credit-note, accounting, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Credit Note

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/procurement/credit-note`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

A Credit Note (CRN) is the post-receipt correction instrument: when a vendor over-bills, ships defective goods, or grants a retrospective discount, the CRN documents the offset against the originating PO / GRN. The reason taxonomy is configured in [[master-data/credit-note-reason]]; the cost-side effect is captured by the costing engine via `COST_POST_003` (credit-note-amount revaluation) and `COST_XMOD_006` (credit-note cost chain). CRNs can be **amount-only** (price correction, no inventory movement) or **quantity-based** (return-to-vendor, consumes a cost layer).

## 2. Related Modules

- [[purchase-order]] — the PO/GRN chain CRNs reverse against
- [[good-receive-note]] — GRN line is the anchor for quantity-based CRNs
- [[costing]] — `COST_POST_003`, `COST_XMOD_006` for revaluation and lot-cost reversal
- [[master-data/credit-note-reason]] — reason code catalogue

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/procurement/credit-note/` — frontend page
- `../carmen/docs/purchase-order-management/` — credit-note flow within PO module
