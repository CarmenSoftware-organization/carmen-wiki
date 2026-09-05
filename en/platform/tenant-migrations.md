---
title: Tenant Migrations
description: Fleet-wide screen that checks and applies pending tenant-database schema migrations across every business unit; reuses cluster.read, with every mutating action further restricted to super-admin.
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, tenant-migrations
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Tenant Migrations

## 1. At a Glance

- TenantMigrationManagement (+ DeployConsole, FleetSync) — fleet-wide migration console
- Route reuses cluster.read (shares the Clusters resource); actions are additionally super-admin gated
- Content currently exists at business-units/tenant-migrations.md — see cross-module note

## 2. References

- ../carmen-platform/src/pages/TenantMigrationManagement.tsx
- ../carmen-platform/src/pages/tenantMigration/DeployConsole.tsx
- ../carmen-platform/src/pages/tenantMigration/FleetSync.tsx
- ../carmen-platform/src/services/tenantMigrationService.ts
- en/platform/business-units/tenant-migrations.md (existing content pending relocation decision)

## 3. TODO

- [ ] Decide whether to relocate content from business-units/tenant-migrations.md or keep both — see cross-module note in .specs/resync-platform-2026-09-05-progress.md
- [ ] Fill from source in Task 21
