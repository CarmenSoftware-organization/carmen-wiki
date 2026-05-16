---
title: SR Dashboard
description: Store Requisition summary tiles — requisitions by stage, aging beyond SLA, fulfillment progress, and pending approver actions.
published: true
date: 2026-05-16T15:00:00.000Z
tags: dashboard, store-requisition, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# SR Dashboard

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/dashboard/sr`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

SR Dashboard summarises the Store Requisition pipeline — requisitions by stage (draft / pending approval / approved / fulfilling / received), aging past SLA, fulfillment progress per outlet, and the approver-pending list for the signed-in user. Store Managers and Fulfillers use this page to triage transfers; tiles drill into the [[store-requisition]] module with the relevant filter pre-applied.

## 2. Related Modules

- [[store-requisition]] — the master transactional module
- [[store-requisition/stock-replenishment]] — auto-generated SR variant
- [[inventory]] — the underlying stock the SR moves between locations

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/dashboard/sr/` — frontend page
