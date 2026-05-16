---
title: Inventory Transaction Log
description: Read-only timeline of every inventory-affecting transaction (GRN, SR, adjustment, count variance) for diagnostic and audit purposes.
published: true
date: 2026-05-16T15:00:00.000Z
tags: inventory, transaction, audit, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Inventory Transaction Log

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/inventory-management/transaction`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

The Inventory Transaction surface (`tb_inventory_transaction`, `tb_inventory_transaction_detail`) is the immutable activity tape of every quantity movement at every location. Each row carries the source document (PO / GRN / SR / adjustment / count), the affected product / location / lot / qty, the unit cost picked at posting time (per AVCO or FIFO), and the resulting `InventoryStatus` after-image. Frontend exposes this as a filterable log; testers use it to verify that GRN commits and adjustment posts produced the expected ledger row.

## 2. Related Modules

- [[inventory]] — current-state view this log writes into
- [[costing]] — cost-layer picks recorded per transaction
- [[good-receive-note]], [[inventory-adjustment]], [[store-requisition]], [[physical-count]] — source documents

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/inventory-management/transaction/` — frontend page
