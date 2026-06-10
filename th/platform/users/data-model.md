---
title: User — Data Model
description: Entity ของ user, ส่วนขยาย profile (avatar), สถานะ และ BU assignment ต่อ cluster — สิทธิ์แพลตฟอร์มอยู่ใน RBAC
published: true
date: 2026-06-10T16:30:00.000Z
tags: book/platform, users, data-model
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# User — Data Model

## 1. At a Glance

- ตาราง: `tb_user` (identity anchor) + `tb_user_profile` (ชื่อแบ่งส่วน, `avatar_file_token` — API resolve เป็น string `avatar_url` แบบ presigned)
- สถานะ (active, disabled, deleted) ผ่าน `is_active` + soft-delete trio; API คืน audit เป็น object `audit` แบบ nested (SPA flatten กลับ — field แบบ flat ชนะเมื่อมีค่า)
- BU assignment ต่อ cluster ผ่าน `tb_user_tb_business_unit` (`role`: `admin`/`user`, flag `is_default`)
- สิทธิ์เข้า Platform admin **ไม่ได้เก็บบนตารางเหล่านี้** — อยู่ในตาราง RBAC assignment ([rbac](/th/platform/rbac))
- หมายเหตุเชิงประวัติ: จนถึง 2026-06-10 `tb_user` เคยมีคอลัมน์ enum `platform_role` (7 ค่า) ที่ขับเคลื่อนทุก gate ใน SPA — ทั้งคอลัมน์และ `enum_platform_role` ถูกถอดออกจาก schema แล้ว (commit `6091ffc`, `5f629f2` ใน `carmen-platform`) แทนที่ด้วย role assignment ของ RBAC

## 2. References

- ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma — `tb_user`, `tb_user_profile`, `tb_cluster_user`, `tb_user_tb_business_unit`
- ../carmen-platform/src/pages/UserEdit.tsx — interface `UserFormData` (7 ฟิลด์)
- ../carmen-platform/src/types/index.ts — interface `User`, `Audit`/`AuditEntry`

## 3. TODO

- [ ] เขียนตารางฟิลด์ฉบับเต็มตาม en/platform/users/data-model
- [ ] Document shape ของ BU assignment
