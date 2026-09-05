---
title: Activity Events — Data Model
description: The activity/audit-log entity recording actor, action, target record and timestamp for every logged change across the platform.
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, activity-events, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Activity Events — Data Model

## 1. At a Glance

- Activity event entity — actor, action, target, timestamp
- The PLATFORM_SCOPED_RECORD sentinel referenced by other modules' View History gate

## 2. References

- ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma
- ../carmen-platform/src/services/analyticsService.ts

## 3. TODO

- [ ] Fill from source in Task 24
