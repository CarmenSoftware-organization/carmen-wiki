---
title: Cluster — Data Model
description: Entity ของ cluster, ความสัมพันธ์กับ BU และ user, ฟิลด์ไลเซนส์ และ branding file token
published: true
date: 2026-07-29T06:35:38.000Z
tags: book/platform, clusters, data-model
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Cluster — Data Model

## 1. At a Glance

- Entity `tb_cluster`: ฟิลด์ identity (`code`, `name`, `alias_name`), branding file token (`logo_file_token`, `avatar_file_token` — API resolve เป็น presigned object `logo`/`avatar` ฝังในตัว ไม่เปิดเผย token ดิบ), license cap `max_license_bu`, counter `doc_version Int @default(0)` สำหรับ optimistic lock (เพิ่มทั้ง platform schema 35 ตารางเมื่อ 2026-07-16 — `PUT` ที่ใช้ `doc_version` เก่าจะถูกปฏิเสธด้วย `409`) และ audit/soft-delete trio (API คืนเป็น object `audit` แบบ nested; SPA flatten กลับ โดย field แบบ flat ชนะเมื่อมีค่า)
- One-to-many กับ Business Units (`tb_business_unit.cluster_id`)
- M:N กับ user ผ่าน `tb_cluster_user` (`role` ต่อ cluster: `admin`/`user` — orthogonal กับโมเดล Platform RBAC, ดู [rbac](/th/platform/rbac); `tb_cluster_user` มี `doc_version` เช่นกัน แต่การแก้ไข role/parent-BU แบบ inline ในหน้า edit ยังไม่ส่งค่านี้ไปด้วย)
- การอัปโหลด branding ผ่าน multipart endpoint เฉพาะ: `POST /api-system/clusters/:id/logo` และ `POST /api-system/clusters/:id/avatar`

## 2. References

- ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma — `model tb_business_unit` (บรรทัด 117), `model tb_cluster` (บรรทัด 225), `model tb_cluster_user` (บรรทัด 255), `enum enum_cluster_user_role` (บรรทัด 675)
- ../carmen-platform/src/types/index.ts — interface `Cluster` (รวม `doc_version?: number`), `PresignedImage`, `Audit`/`AuditEntry`
- ../carmen-platform/src/utils/docVersion.ts — helper `getDocVersion`/`isVersionConflict`/`notifyVersionConflict`
- ../carmen-platform/src/services/clusterService.ts — REST client (`/api-system/clusters`)

## 3. TODO

- [ ] เขียนตารางฟิลด์ฉบับเต็มตาม en/platform/clusters/data-model
- [ ] เพิ่ม entity diagram
