---
title: แฟล็กฟีเจอร์ (Feature Flags)
description: The single-screen list of feature-flag switches (active/hide/inactive per module) gated by feature_flag.manage only, deliberately carrying no feature key of its own.
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, feature-flags
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# แฟล็กฟีเจอร์ (Feature Flags)

## 1. At a Glance

- FeatureFlagManagement — single-screen list of feature flags
- feature_flag.manage — single gate, no separate .read key
- Deliberately has no feature key of its own — a switch that hides itself could never be restored from the UI

## 2. References

- ../carmen-platform/src/pages/FeatureFlagManagement.tsx
- ../carmen-platform/src/services/featureFlagService.ts
- ../carmen-platform/src/components/nav/platformNav.ts

## 3. TODO

- [ ] Fill from source in Task 20
