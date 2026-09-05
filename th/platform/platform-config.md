---
title: การตั้งค่าแพลตฟอร์ม (Platform Config)
description: Single-screen, card-based platform-wide configuration (invitations, expiry thresholds, links, notification email, signup, license enforcement), gated by platform_config.read/manage.
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, platform-config
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# การตั้งค่าแพลตฟอร์ม (Platform Config)

## 1. At a Glance

- PlatformConfigManagement — card-based global configuration screen
- platform_config.read gates the nav/route; platform_config.manage gates every card save
- feature key platform_config

## 2. References

- ../carmen-platform/src/pages/PlatformConfigManagement.tsx
- ../carmen-platform/src/pages/platformConfig/
- ../carmen-platform/src/services/platformConfigService.ts

## 3. TODO

- [ ] Fill from source in Task 16
