---
title: Business Unit — Data Model
description: Entity ของ BU, ความหมายของ array config, การเก็บ DB connection และ branding file token
published: true
date: 2026-06-10T16:30:00.000Z
tags: book/platform, business-units, data-model
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Business Unit — Data Model

## 1. At a Glance

- ฟิลด์ identity (ชื่อโรงแรม, code) บน `tb_business_unit`
- ฟิลด์รูปแบบ (date, currency, decimal) และ timezone
- บล็อก DB connection (`db_connection` JSON — UI ปัจจุบัน render แบบ read-only)
- Array `config[]` (คู่ key/value — ตอน save จะเก็บเฉพาะ row ที่มีทั้ง `key` และ `label`)
- Branding file token: `logo_file_token` / `avatar_file_token` — API resolve เป็น presigned object `logo`/`avatar` ฝังในตัว ไม่เปิดเผย token ดิบ; อัปโหลดผ่าน `POST /api-system/business-units/:id/logo` และ `/avatar`
- คอลัมน์ audit: API คืน object `audit` แบบ nested (`audit.created/updated/deleted` แต่ละตัวเป็น `{ at, id, name, avatar }`); SPA flatten กลับ โดย field แบบ flat ชนะเมื่อมีค่า
- Role ของ BU-user join (`enum_user_business_unit_role`: `admin`/`user`) orthogonal กับโมเดล Platform RBAC ([rbac](/th/platform/rbac))

## 2. References

- ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma — `model tb_business_unit`
- ../carmen-platform/src/types/index.ts — interface `BusinessUnit`, `BusinessUnitConfig`, `PresignedImage`
- ../carmen-platform/src/services/businessUnitService.ts — REST client (`/api-system/business-units`)

## 3. TODO

- [ ] เขียนตารางฟิลด์ฉบับเต็มตาม en/platform/business-units/data-model
- [ ] Document namespace ของ key ใน config array
