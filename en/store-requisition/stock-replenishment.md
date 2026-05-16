---
title: Stock Replenishment
description: Auto-generated SR proposal based on min / max / par / reorder thresholds at each location — the policy-driven counterpart to the manual Store Requisition flow.
published: true
date: 2026-05-16T15:00:00.000Z
tags: store-requisition, replenishment, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Stock Replenishment

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/store-operation/stock-replenishment`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

Stock Replenishment runs a scheduled (or manual) sweep over every `(product, location)` pair with replenishment policy configured. For each row where `on_hand + on_order < min_qty`, the engine proposes a [[store-requisition]] line for review. The Inventory Controller approves or edits the proposal, then it becomes a regular SR routed through the standard approval chain. Policy lives in `tb_product_location` (linked to [[product]]) and the authority is governed by `INV_AUTH_004`.

## 2. Related Modules

- [[store-requisition]] — the document type produced
- [[inventory]] — current on-hand quantities the engine reads
- [[product]] — per-location replenishment policy (min / max / par / reorder)

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/store-operation/stock-replenishment/` — frontend page
