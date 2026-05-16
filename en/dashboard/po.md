---
title: PO Dashboard
description: Purchase Order summary tiles — open orders by status, overdue receipts, value-by-vendor, and PO-to-GRN match progress.
published: true
date: 2026-05-16T15:00:00.000Z
tags: dashboard, purchase-order, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# PO Dashboard

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/dashboard/po`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

PO Dashboard summarises the Purchase Order pipeline — open orders by status, overdue against expected-delivery date, total commitment by vendor, and the three-way-match progress against GRN and invoice. Purchasers and Procurement Managers use this page to chase deliveries; tiles drill into the [[purchase-order]] module with the relevant filter pre-applied.

## 2. Related Modules

- [[purchase-order]] — the master transactional module
- [[good-receive-note]] — receiving against the PO
- [[vendor-pricelist]] — vendor master referenced in by-vendor groupings

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/dashboard/po/` — frontend page
