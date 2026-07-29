---
title: Business Unit — Data Model
description: Entity ของ BU, ความหมายของ array config, การเก็บ DB connection และ branding file token
published: true
date: 2026-07-29T06:50:54.000Z
tags: book/platform, business-units, data-model
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Business Unit — Data Model

## 1. At a Glance

- ฟิลด์ identity (ชื่อโรงแรม, code) บน `tb_business_unit`
- ที่อยู่ hotel/company ถูก restructure เป็น 10 คอลัมน์ต่อฝั่ง: `*_address_line1`, `*_address_line2`, `*_sub_district`, `*_district`, `*_city`, `*_province`, `*_postal_code`, `*_country`, `*_latitude`, `*_longitude` (แทนที่ field เดี่ยว `hotel_address`/`company_address` เดิม)
- ฟิลด์รูปแบบ (date, currency, decimal) และ timezone
- บล็อก DB connection (`db_connection` JSON) — **แก้ไขจาก sync ก่อนหน้า**: UI ตอนนี้แก้ไขได้เป็นฟอร์มมีโครงสร้าง (field ที่รู้จัก + extras, password ถูก mask พร้อม reveal แบบ guarded) ไม่ใช่ `<pre>` แบบอ่านอย่างเดียว
- Array `config[]` (คู่ key/value/datatype — ตอน save จะเก็บเฉพาะ row ที่มีทั้ง `key` และ `label`; ตัวเลือก datatype มี `enum` เพิ่มมาด้วย)
- `doc_version Int @default(0)` — token optimistic-lock เพิ่มทั้ง platform schema เมื่อ 2026-07-16
- Branding file token: `logo_file_token` / `avatar_file_token` — API resolve เป็น presigned object `logo`/`avatar` ฝังในตัว ไม่เปิดเผย token ดิบ; อัปโหลดผ่าน `POST /api-system/business-units/:id/logo` และ `/avatar`
- คอลัมน์ audit: API คืน object `audit` แบบ nested (`audit.created/updated/deleted` แต่ละตัวเป็น `{ at, id, name, avatar }`); SPA flatten กลับ โดย field แบบ flat ชนะเมื่อมีค่า
- Role ของ BU-user join (`enum_user_business_unit_role`: `admin`/`user`) orthogonal กับโมเดล Platform RBAC ([rbac](/th/platform/rbac))

## 2. References

- ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma — `model tb_business_unit` (บรรทัด 117)
- ../carmen-platform/src/types/index.ts — interface `BusinessUnit` (รวม `doc_version?: number`), `BusinessUnitConfig`, `PresignedImage`
- ../carmen-platform/src/utils/dbConnection.ts — `objectToDbFields`/`dbFieldsToObject`
- ../carmen-platform/src/services/businessUnitService.ts — REST client (`/api-system/business-units`, `revealDbPassword`)

## 3. TODO

- [ ] เขียนตารางฟิลด์ฉบับเต็มตาม en/platform/business-units/data-model (รวมที่อยู่แบบ restructure ใหม่)
- [ ] Document namespace ของ key ใน config array
