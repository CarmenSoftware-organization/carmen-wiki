---
title: Report History
description: Archive of every executed report run — date, parameters, status, link to the generated file or rendered output.
published: true
date: 2026-05-16T15:00:00.000Z
tags: reporting-audit, history, archive, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Report History

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/report/history`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

Report History is the per-run log of every report execution — manual and scheduled. Each row carries the report id, the parameters used, the run timestamp, the executing user (or service for scheduled), the status (`succeeded`, `failed`, `pending`), and the output reference (file path, attachment id, or email message id). Used by Auditor and Finance for post-hoc verification of which numbers were exported on which date.

## 2. Related Modules

- [[reporting-audit/report]] — the report definitions
- [[reporting-audit/schedule]] — scheduled runs land here
- [[reporting-audit/attachment]] — output files when archived

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/report/history/` — frontend page
