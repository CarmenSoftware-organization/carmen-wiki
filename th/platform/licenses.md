---
title: ไลเซนส์ (Licenses)
description: License centre — subscriptions, the per-cluster BU-quota ledger, the per-BU seat ledger, and expiry thresholds, reached also via legacy /subscriptions redirects.
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, licenses
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# ไลเซนส์ (Licenses)

## 1. At a Glance

- LicenseCenter (cluster-level overview) and ClusterLicenseDetail (per-cluster ledger)
- Backs the tb_cluster_license (BU-quota) and tb_business_unit_license (seat) ledgers referenced from Clusters and Business Units
- Legacy /subscriptions* routes redirect into this module

## 2. References

- ../carmen-platform/src/pages/LicenseCenter.tsx
- ../carmen-platform/src/pages/licenses/
- ../carmen-platform/src/services/subscriptionService.ts
- ../carmen-platform/src/services/clusterLicenseService.ts
- ../carmen-platform/src/services/businessUnitLicenseService.ts
- ../carmen-platform/src/services/expiryThresholdService.ts

## 3. TODO

- [ ] Fill from source in Task 13
