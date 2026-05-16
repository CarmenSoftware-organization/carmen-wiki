---
title: Main Dashboard
description: Landing dashboard surfacing top-level KPIs across PR, PO, GRN, Inventory, and SR — the single pane shown immediately after login.
published: true
date: 2026-05-16T15:00:00.000Z
tags: dashboard, landing, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Main Dashboard

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/dashboard/main`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

Main Dashboard is the post-login landing surface. It composes the highest-value tiles from each per-domain dashboard ([[dashboard/pr]], [[dashboard/po]], [[dashboard/grn]], [[dashboard/inventory]], [[dashboard/sr]]) into one pane so that approvers, store managers, and inventory controllers see their pending workload at a glance. Each tile drills into the underlying module with a pre-applied filter.

## 2. Related Modules

- [[dashboard]] — module index with all sub-page tiles
- [[purchase-request/my-approval]] — the approval inbox tile most operators click first
- [[reporting-audit/widget]] — widget catalogue that backs each tile

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/dashboard/main/` — frontend page
