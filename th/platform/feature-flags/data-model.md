---
title: แฟล็กฟีเจอร์ — โมเดลข้อมูล (Data Model)
description: The feature-flag entity — key, state (active/hide/inactive) and scope — consumed by PrivateRoute's feature check across every gated module.
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, feature-flags, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# แฟล็กฟีเจอร์ — โมเดลข้อมูล (Data Model)

## 1. At a Glance

- Feature flag entity read/written by featureFlagService.ts
- States consumed by PrivateRoute's feature-flag check across every gated route

## 2. References

- ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma
- ../carmen-platform/src/services/featureFlagService.ts

## 3. TODO

- [ ] Fill from source in Task 20
