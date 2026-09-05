---
title: Cluster Admin — Permissions
description: No permission-string gate anywhere in this module — ClusterAdminRoute checks cluster membership only, a distinct axis from the platform-side platform_role/permission keys.
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, cluster-admin, permissions
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Cluster Admin — Permissions

## 1. At a Glance

- ClusterAdminRoute — membership check, not a permission string
- clusterAdminNav.ts applies no permission filtering at all
- Contrast with the platform-side RBAC gates in rbac/permissions.md

## 2. References

- ../carmen-platform/src/components/ClusterAdminRoute.tsx
- ../carmen-platform/src/components/nav/clusterAdminNav.ts

## 3. TODO

- [ ] Fill from source in Task 15
