---
title: พูลฐานข้อมูล (Database Pools)
description: CRUD over the tenant database connection pools that business units are now assigned to via database_pool_id, replacing the dropped per-BU db_connection fields.
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, database-pools
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# พูลฐานข้อมูล (Database Pools)

## 1. At a Glance

- DatabasePoolManagement (list) and DatabasePoolEdit (create/edit)
- database_pool.read gates the nav/list; database_pool.manage gates create/edit/delete
- Referenced by Business Units' database_pool_id field (replaced db_connection)

## 2. References

- ../carmen-platform/src/pages/DatabasePoolManagement.tsx
- ../carmen-platform/src/pages/DatabasePoolEdit.tsx
- ../carmen-platform/src/services/databasePoolService.ts

## 3. TODO

- [ ] Fill from source in Task 26
