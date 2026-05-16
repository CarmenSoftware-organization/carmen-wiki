---
title: My Approval
description: Personal approval queue surfacing every PR (and related document) the current user must act on — single pane across modules.
published: true
date: 2026-05-16T15:00:00.000Z
tags: purchase-request, approval, workflow, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# My Approval

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/procurement/approval`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

The My Approval surface in the app is the per-user inbox that aggregates every workflow stage currently assigned to the signed-in user across PR, PO, and other approvable documents. Behaviour is driven by the workflow engine ([[system-config/workflow]]) — the page filters documents whose `workflow_current_stage` matches a stage where the user appears in `user_action.execute[]`. From here approvers fire approve / reject / send-back / split-reject actions identically to opening each document one-by-one.

## 2. Related Modules

- [[purchase-request]] — primary approvable document type
- [[purchase-order]] — also surfaced here when PO requires manual approval
- [[system-config/workflow]] — stage / role / threshold configuration
- [[access-control/application-role]] — role-to-permission mapping that determines visibility

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/procurement/approval/` — frontend page
- `../carmen/docs/purchase-request-management/PR-User-Experience.md` — approver experience
