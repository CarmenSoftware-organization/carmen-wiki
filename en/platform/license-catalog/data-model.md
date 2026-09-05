---
title: License Catalog — Data Model
description: License feature and license feature group entities, and their relation to subscriptions built from them.
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, license-catalog, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# License Catalog — Data Model

## 1. At a Glance

- License feature entity — the catalog of purchasable capabilities
- License feature group entity — named bundles of features
- Referenced by subscriptionService.ts when composing a subscription

## 2. References

- ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma
- ../carmen-platform/src/services/licenseFeatureService.ts
- ../carmen-platform/src/services/licenseFeatureGroupService.ts

## 3. TODO

- [ ] Fill from source in Task 14
