---
title: PR Dashboard
description: Purchase Request summary tiles — pending approvals, aging buckets, by-stage counts, and conversion-to-PO progress.
published: true
date: 2026-05-16T15:00:00.000Z
tags: dashboard, purchase-request, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# PR Dashboard

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/dashboard/pr`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

PR Dashboard summarises the Purchase Request pipeline — count-by-stage, aging beyond SLA, requests awaiting the signed-in user's approval, and the conversion bridge into PO. Approvers and Procurement Managers use this page to triage their day; tiles drill into the [[purchase-request]] module with the relevant filter pre-applied.

## 2. Related Modules

- [[purchase-request]] — the master transactional module
- [[purchase-request/my-approval]] — approver inbox that one of the tiles routes to
- [[system-config/workflow]] — stage definitions that drive count-by-stage

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/dashboard/pr/` — frontend page
