---
title: Wastage Reporting
description: Specialised stock-out adjustment for spoilage, breakage, expiry, and theft — categorised so finance can analyse loss patterns.
published: true
date: 2026-05-16T15:00:00.000Z
tags: inventory-adjustment, wastage, loss, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Wastage Reporting

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/store-operation/wastage-reporting`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

Wastage Reporting is a sub-flavour of [[inventory-adjustment]] (specifically `tb_stock_out`) where the adjustment reason maps to a wastage category — spoilage, breakage, expiry, theft, sample, or other. The document still posts an inventory decrement and a cost-layer consumption identical to a regular stock-out, but the reason category drives finance reporting (loss as a % of revenue per outlet / period / product family) and may flag downstream alerts for the F&B Controller. Distinct from [[inventory-adjustment]] only by category convention; the schema is shared.

## 2. Related Modules

- [[inventory-adjustment]] — parent document type (`tb_stock_out`)
- [[master-data/adjustment-type]] — wastage reason catalogue
- [[reporting-audit]] — loss-per-period analytics

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/store-operation/wastage-reporting/` — frontend page
