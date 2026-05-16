---
title: Inventory Dashboard
description: Inventory summary tiles — stock on hand, low-stock alerts, locations with open counts, and adjustments awaiting review.
published: true
date: 2026-05-16T15:00:00.000Z
tags: dashboard, inventory, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Inventory Dashboard

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/dashboard/inventory`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

Inventory Dashboard summarises the stock-control surface — total stock value, items under reorder point, locations currently locked for Physical Count or Spot Check, and adjustment requests awaiting review. Inventory Controllers and Store Managers use this page to monitor inventory health; tiles drill into [[inventory]], [[inventory-adjustment]], [[physical-count]], or [[spot-check]] with the relevant filter pre-applied.

## 2. Related Modules

- [[inventory]] — system-of-record for stock balances
- [[inventory-adjustment]] — manual stock-in / stock-out
- [[physical-count]], [[spot-check]] — count operations that lock locations
- [[costing]] — cost engine that values the on-hand quantities

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/dashboard/inventory/` — frontend page
