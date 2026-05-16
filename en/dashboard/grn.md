---
title: GRN Dashboard
description: Goods Receive Note summary tiles — receipts pending commit, partial-receipt aging, by-location counts, and PO-line completion rate.
published: true
date: 2026-05-16T15:00:00.000Z
tags: dashboard, good-receive-note, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# GRN Dashboard

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/dashboard/grn`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

GRN Dashboard summarises the receiving pipeline — draft receipts awaiting commit, partial deliveries aging past expectation, receipts by location, and the per-PO-line completion rate that gates closing the PO. Receivers and Inventory Controllers use this page to spot stuck receipts; tiles drill into the [[good-receive-note]] module with the relevant filter pre-applied.

## 2. Related Modules

- [[good-receive-note]] — the master transactional module
- [[purchase-order]] — the upstream commitment
- [[inventory]] — the downstream stock impact once committed

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/dashboard/grn/` — frontend page
