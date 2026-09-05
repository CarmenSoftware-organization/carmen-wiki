---
title: การตั้งค่าแพลตฟอร์ม — โมเดลข้อมูล (Data Model)
description: The platform config key/value entity backing each configuration card (invitations, expiry thresholds, links, notification email, signup, license enforcement).
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, platform-config, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# การตั้งค่าแพลตฟอร์ม — โมเดลข้อมูล (Data Model)

## 1. At a Glance

- Config entity read and written by platformConfigService.ts
- Card-to-key mapping used by PlatformConfigManagement's per-domain cards

## 2. References

- ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma
- ../carmen-platform/src/services/platformConfigService.ts

## 3. TODO

- [ ] Fill from source in Task 16
