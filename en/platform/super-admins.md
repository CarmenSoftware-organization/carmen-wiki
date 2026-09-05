---
title: Super Admins
description: Card-based roster of super admins, gated by superAdminOnly rather than a permission string, with a self-removal guard and a UserPicker typeahead.
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, super-admins
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Super Admins

## 1. At a Glance

- SuperAdminManagement — card-based roster, no DataTable
- Gated by superAdminOnly:true on the nav entry, not a permission key
- Self-removal guard; UserPicker typeahead to add a member
- e2e suite super-admins (has coverage, unlike most modules in this batch)

## 2. References

- ../carmen-platform/src/pages/SuperAdminManagement.tsx
- ../carmen-platform/src/services/superAdminService.ts
- ../carmen-platform/src/components/nav/platformNav.ts

## 3. TODO

- [ ] Fill from source in Task 19
