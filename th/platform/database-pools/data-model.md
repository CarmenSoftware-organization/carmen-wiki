---
title: พูลฐานข้อมูล — โมเดลข้อมูล (Data Model)
description: The tb_database_pool entity that tb_business_unit.database_pool_id now references, replacing the dropped db_connection column.
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, database-pools, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# พูลฐานข้อมูล — โมเดลข้อมูล (Data Model)

## 1. At a Glance

- tb_database_pool — connection pool entity (host, credentials, schema strategy)
- Referenced by tb_business_unit.database_pool_id

## 2. References

- ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma
- ../carmen-platform/src/services/databasePoolService.ts

## 3. TODO

- [ ] Fill from source in Task 26
