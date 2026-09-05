---
title: ไลเซนส์ — โมเดลข้อมูล (Data Model)
description: tb_cluster_license (BU-quota ledger, winning-row semantics) and tb_business_unit_license (per-BU seat ledger, summed), plus subscription and expiry-threshold entities.
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, licenses, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# ไลเซนส์ — โมเดลข้อมูล (Data Model)

## 1. At a Glance

- tb_cluster_license — per-cluster BU-quota purchase ledger
- tb_business_unit_license — per-BU seat purchase ledger
- Subscription and expiry-threshold entities

## 2. References

- ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma
- ../carmen-platform/src/services/subscriptionService.ts
- ../carmen-platform/src/services/clusterLicenseService.ts
- ../carmen-platform/src/services/businessUnitLicenseService.ts

## 3. TODO

- [ ] Fill from source in Task 13
