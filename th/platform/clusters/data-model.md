---
title: Cluster — Data Model
description: Entity ของ cluster, ความสัมพันธ์กับ BU และ user, ฟิลด์ไลเซนส์ และ branding file token
published: true
date: 2026-06-10T16:30:00.000Z
tags: book/platform, clusters, data-model
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Cluster — Data Model

## 1. At a Glance

- Entity `tb_cluster`: ฟิลด์ identity (`code`, `name`, `alias_name`), branding file token (`logo_file_token`, `avatar_file_token` — API resolve เป็น presigned object `logo`/`avatar` ฝังในตัว ไม่เปิดเผย token ดิบ), license cap `max_license_bu` และ audit/soft-delete trio (API คืนเป็น object `audit` แบบ nested; SPA flatten กลับ โดย field แบบ flat ชนะเมื่อมีค่า)
- One-to-many กับ Business Units (`tb_business_unit.cluster_id`)
- M:N กับ user ผ่าน `tb_cluster_user` (`role` ต่อ cluster: `admin`/`user` — orthogonal กับโมเดล Platform RBAC, ดู [rbac](/th/platform/rbac))
- การอัปโหลด branding ผ่าน multipart endpoint เฉพาะ: `POST /api-system/clusters/:id/logo` และ `POST /api-system/clusters/:id/avatar`

## 2. References

- ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma — `model tb_cluster`, `model tb_cluster_user`, `enum enum_cluster_user_role`
- ../carmen-platform/src/types/index.ts — interface `Cluster`, `PresignedImage`, `Audit`/`AuditEntry`
- ../carmen-platform/src/services/clusterService.ts — REST client (`/api-system/clusters`)

## 3. TODO

- [ ] เขียนตารางฟิลด์ฉบับเต็มตาม en/platform/clusters/data-model
- [ ] เพิ่ม entity diagram
