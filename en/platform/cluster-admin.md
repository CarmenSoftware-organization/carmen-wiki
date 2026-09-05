---
title: Cluster Admin
description: The cluster-admin persona's own entry point — a membership-scoped mirror of Cluster, Business Units, Users, Licenses and Profile, with no platform-side RBAC permission filtering.
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, cluster-admin
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Cluster Admin

## 1. At a Glance

- Second persona, distinct from the platform-side RBAC-gated screens
- ClusterAdminRoute gates on cluster membership, not a permission string
- Mirrors Cluster, Business Units, Users, Licenses and Profile for one :clusterId

## 2. References

- ../carmen-platform/src/pages/clusterAdmin/ClusterAdminEntry.tsx
- ../carmen-platform/src/pages/clusterAdmin/
- ../carmen-platform/src/services/clusterAdminService.ts
- ../carmen-platform/src/components/nav/clusterAdminNav.ts

## 3. TODO

- [ ] Fill from source in Task 15
