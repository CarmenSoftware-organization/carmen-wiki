---
title: Dashboard
description: Cross-module dashboard surface — landing screen plus per-module KPI views (PR, PO, GRN, Inventory, SR) that summarise live counts, aging, and exception buckets without opening each module.
published: true
date: 2026-05-16T15:00:00.000Z
tags: dashboard, kpi, reporting, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Dashboard

## 1. Overview

> **Status:** Documentation in progress — module registered for parity with the app navigation at `/dashboard/*`. Detail to be filled when the corresponding module captures land. For now this section serves as the navigation target so testers and developers can confirm the slugs exist and reach the related concepts.

The Dashboard module is the first screen most operators see on login. It aggregates read-only counts and exception buckets from across the procure-to-pay and inventory chains so that a manager can spot pending approvals, overdue receipts, low-stock locations, or open requisitions without opening each module individually. Each sub-page is a per-domain summary backed by the same transactional tables — drilling into a tile navigates the user into the underlying module (PR / PO / GRN / Inventory / SR) with the relevant filter pre-applied.

## 2. Pages in This Module

- [[dashboard/main]] — landing dashboard with cross-module KPIs
- [[dashboard/pr]] — Purchase Request summary tiles
- [[dashboard/po]] — Purchase Order summary tiles
- [[dashboard/grn]] — Goods Receive Note summary tiles
- [[dashboard/inventory]] — Inventory Management summary tiles
- [[dashboard/sr]] — Store Requisition summary tiles

## 3. Related Modules

- [[purchase-request]], [[purchase-order]], [[good-receive-note]] — procure-to-pay sources
- [[inventory]], [[store-requisition]] — inventory-side sources
- [[reporting-audit]] — deeper report catalogue once a tile-drill is not enough

## 4. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/dashboard/` — frontend pages
- `../carmen-inventory-frontend/constant/module-list.ts` — menu definition that registers each dashboard sub-page
