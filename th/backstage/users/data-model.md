---
title: User — Data Model
description: Entity ของ user, ส่วนขยาย profile (avatar), สถานะ และ BU assignment ต่อ cluster — สิทธิ์แพลตฟอร์มอยู่ใน RBAC
published: true
date: 2026-10-29T05:00:00.000Z
tags: book/backstage, users, data-model
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# User — Data Model

## 1. At a Glance

- ตาราง: `tb_user` (identity anchor, ล่าสุดมี field ยืนยันอีเมล `email_verified_at`/`email_verification_token_hash`/`email_verification_expires_at` เพิ่มมาด้วย — ไม่มี UI ใช้งานในโมดูล Users เอง มีเฉพาะที่หน้า Backstage Users) + `tb_user_profile` (ชื่อแบ่งส่วน, `avatar_file_token` — API resolve เป็น string `avatar_url` แบบ presigned; มี `signature_file_token` เพิ่มมาด้วย ยังไม่มี UI ใช้งาน)
- สถานะ (active, disabled, deleted) ผ่าน `is_active` + soft-delete trio; API คืน audit เป็น object `audit` แบบ nested — `normalizeAudit()` ลองรูปแบบ **nested ก่อน** แล้วค่อย fallback ไปที่ field แบบ flat เมื่อไม่มีค่า nested (สลับทิศทางจากที่เคยระบุไว้ที่นี่)
- `doc_version Int @default(0)` บนทั้ง `tb_user` และ `tb_user_profile` — token optimistic-lock เพิ่มทั้ง platform schema เมื่อ 2026-07-16
- BU assignment ต่อ cluster ผ่าน `tb_user_tb_business_unit` (`role`: `admin`/`user`, flag `is_default`)
- **`tb_cluster_user.parent_bu_id` ถูกถอดออกจาก schema แล้ว** (migration `20260825000000_drop_cluster_user_parent_bu`) — ไม่เคยมี service ใดอ่านค่านี้; membership ของ BU จริงอยู่ที่ `tb_user_tb_business_unit` เท่านั้น
- สิทธิ์เข้า Backstage **ไม่ได้เก็บบนตารางเหล่านี้** — อยู่ในตาราง RBAC assignment ([rbac](/th/backstage/rbac))
- หมายเหตุเชิงประวัติ: จนถึง 2026-06-10 `tb_user` เคยมีคอลัมน์ enum `platform_role` (7 ค่า) ที่ขับเคลื่อนทุก gate ใน SPA — ทั้งคอลัมน์และ `enum_platform_role` ถูกถอดออกจาก schema แล้ว (commit `6091ffc`, `5f629f2` ใน `carmen-backstage`) แทนที่ด้วย role assignment ของ RBAC

## 2. References

- ../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma (เลขบรรทัดตรวจซ้ำกับ backend HEAD `c9d788829`, 2026-10-27) — `tb_cluster_user` (บรรทัด 405), `tb_user_profile` (บรรทัด 778), `tb_user_tb_business_unit` (บรรทัด 826), `tb_user` (บรรทัด 582)
- ../carmen-backstage/src/pages/UserEdit.tsx — interface `UserFormData` (7 ฟิลด์, บรรทัด 73–81)
- ../carmen-backstage/src/utils/audit.ts — `normalizeAudit()`, `latestActor()`, `auditCsvFields()`
- ../carmen-backstage/src/utils/docVersion.ts — helper optimistic-lock
- ../carmen-backstage/src/types/index.ts — interface `User`, `Audit`/`AuditEntry`

## 3. TODO

- [ ] เขียนตารางฟิลด์ฉบับเต็มตาม en/backstage/users/data-model (รวม `doc_version`, `signature_file_token`, field ยืนยันอีเมล 3 ตัวใหม่)
- [ ] Document shape ของ BU assignment
