---
title: User Activity
description: Per-user activity timeline — login / logout, page views, document opens — distinct from the entity-level activity log.
published: true
date: 2026-05-16T15:00:00.000Z
tags: reporting-audit, activity, security, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# User Activity

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/system-admin/user-activity`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

User Activity is the user-centric view of system interaction: every login, logout, password change, role change, sensitive-page view (PR / PO detail, financial reports), and impersonation event. Distinct from [[reporting-audit/activity]] which is entity-centric (row-level change history). Auditor and Security Officer use this surface for forensic review and policy verification (e.g. confirm a specific user accessed PRs only during work hours).

## 2. Related Modules

- [[reporting-audit/activity]] — entity-level audit log (different axis)
- [[access-control/user]] — user master
- [[access-control/permission]] — what each user is allowed to do

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/system-admin/user-activity/` — frontend page
