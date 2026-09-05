---
title: Licenses — Permissions
description: subscription.read gates the nav entry; subscription.manage and license.manage gate purchase/edit actions across subscriptions, seats and BU quota.
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, licenses, permissions
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Licenses — Permissions

## 1. At a Glance

- subscription.read — nav/list gate
- subscription.manage / license.manage — CRUD gates on purchase and edit forms
- No dedicated e2e suite — verify against implementation only

## 2. References

- ../carmen-platform/src/components/nav/platformNav.ts
- ../carmen-platform/src/pages/LicenseCenter.tsx

## 3. TODO

- [ ] Fill from source in Task 13
