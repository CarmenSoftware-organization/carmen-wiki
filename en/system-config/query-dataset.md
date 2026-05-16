---
title: Query Dataset
description: Saved SQL / GraphQL queries surfaced as reusable datasets — Sysadmin curates, Reporting & Audit consumes via dashboards and reports.
published: true
date: 2026-05-16T15:00:00.000Z
tags: system-config, query, dataset, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Query Dataset

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/system-admin/query-dataset`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

Query Dataset is the saved-query registry: each row carries a parameterised SQL or GraphQL query plus its column metadata, the role(s) allowed to execute it, and the human-readable display name. Used by [[reporting-audit/report]] as the data source for report definitions, and by [[reporting-audit/widget]] for dashboard tiles. Sysadmin authors and tests; report authors then bind reports / widgets to a named dataset rather than embedding SQL inline.

## 2. Related Modules

- [[reporting-audit/report]] — reports consume datasets
- [[reporting-audit/widget]] — dashboard widgets consume datasets
- [[access-control/permission]] — per-dataset execution permission

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/system-admin/query-dataset/` — frontend page
