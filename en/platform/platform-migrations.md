---
title: Platform Migrations
description: A super-admin-only console for running platform-level database migrations and seed operations, with a live run console.
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, platform-migrations
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Platform Migrations

## 1. At a Glance

- PlatformMigrationManagement — operation list (OpRow) plus a RunConsole
- Gated by superAdminOnly:true, not a permission key
- feature key platform_migrations

## 2. References

- ../carmen-platform/src/pages/PlatformMigrationManagement.tsx
- ../carmen-platform/src/pages/platformMigration/
- ../carmen-platform/src/services/platformMigrationService.ts
- ../carmen-platform/src/services/platformSeedService.ts

## 3. TODO

- [ ] Fill from source in Task 25
