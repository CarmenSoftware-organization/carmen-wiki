---
title: Document Configuration
description: Per-document-type configuration — numbering, default workflow, output template, attachment policy.
published: true
date: 2026-05-16T15:00:00.000Z
tags: system-config, document, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Document Configuration

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/system-admin/document`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

Document Configuration is the per-document-type registry: for each transactional document (PR, PO, GRN, SR, adjustment, count, etc.) it stores the numbering scheme reference ([[system-config/running-code]]), the default workflow ([[system-config/workflow]]), the print template, the email / portal transmission template, and the per-type attachment policy (required, optional, blocked). Sysadmin curates this list; every new transactional module registers here.

## 2. Related Modules

- [[system-config/running-code]] — numbering scheme per document type
- [[system-config/workflow]] — default approval routing per type
- [[reporting-audit/attachment]] — attachment policy enforced at document level

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/system-admin/document/` — frontend page
