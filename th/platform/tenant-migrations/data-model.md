---
title: การย้ายเทแนนต์ — โมเดลข้อมูล (Data Model)
description: The tenant-migration run/status entity tracked per business unit, read and written by tenantMigrationService.ts.
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, tenant-migrations, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# การย้ายเทแนนต์ — โมเดลข้อมูล (Data Model)

## 1. At a Glance

- Per-BU migration status/run entity
- Read by the same businessUnitService.ts list the Business Units module uses

## 2. References

- ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma
- ../carmen-platform/src/services/tenantMigrationService.ts
- ../carmen-platform/src/services/businessUnitService.ts

## 3. TODO

- [ ] Fill from source in Task 21
