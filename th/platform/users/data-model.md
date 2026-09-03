---
title: User — Data Model
description: Entity ของ user, ส่วนขยาย profile (avatar), สถานะ และ BU assignment ต่อ cluster — สิทธิ์แพลตฟอร์มอยู่ใน RBAC
published: true
date: 2026-07-29T07:06:05.000Z
tags: book/platform, users, data-model
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# User — Data Model

## 1. At a Glance

- ตาราง: `tb_user` (identity anchor) + `tb_user_profile` (ชื่อแบ่งส่วน, `avatar_file_token` — API resolve เป็น string `avatar_url` แบบ presigned; มี `signature_file_token` เพิ่มมาด้วย ยังไม่มี UI ใช้งาน)
- สถานะ (active, disabled, deleted) ผ่าน `is_active` + soft-delete trio; API คืน audit เป็น object `audit` แบบ nested (SPA flatten กลับ — field แบบ flat ชนะเมื่อมีค่า)
- `doc_version Int @default(0)` บนทั้ง `tb_user` และ `tb_user_profile` — token optimistic-lock เพิ่มทั้ง platform schema เมื่อ 2026-07-16
- BU assignment ต่อ cluster ผ่าน `tb_user_tb_business_unit` (`role`: `admin`/`user`, flag `is_default`)
- สิทธิ์เข้า Platform admin **ไม่ได้เก็บบนตารางเหล่านี้** — อยู่ในตาราง RBAC assignment ([rbac](/th/platform/rbac))
- หมายเหตุเชิงประวัติ: จนถึง 2026-06-10 `tb_user` เคยมีคอลัมน์ enum `platform_role` (7 ค่า) ที่ขับเคลื่อนทุก gate ใน SPA — ทั้งคอลัมน์และ `enum_platform_role` ถูกถอดออกจาก schema แล้ว (commit `6091ffc`, `5f629f2` ใน `carmen-platform`) แทนที่ด้วย role assignment ของ RBAC

## 2. References

- ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma — `tb_cluster_user` (บรรทัด 255), `tb_user_profile` (บรรทัด 579), `tb_user_tb_business_unit` (บรรทัด 627), `tb_user` (บรรทัด 494)
- ../carmen-platform/src/pages/UserEdit.tsx — interface `UserFormData` (7 ฟิลด์, บรรทัด 66–74)
- ../carmen-platform/src/utils/docVersion.ts — helper optimistic-lock
- ../carmen-platform/src/types/index.ts — interface `User`, `Audit`/`AuditEntry`

## 3. TODO

- [ ] เขียนตารางฟิลด์ฉบับเต็มตาม en/platform/users/data-model (รวม `doc_version`, `signature_file_token`)
- [ ] Document shape ของ BU assignment
