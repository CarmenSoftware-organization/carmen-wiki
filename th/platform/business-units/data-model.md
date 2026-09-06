---
title: Business Unit — Data Model
description: Entity ของ BU, ledger ที่นั่ง tb_business_unit_license ที่แทนที่ max_license_users, ตัวชี้ database_pool_id/db_schema ที่แทนที่ db_connection, และ branding file token
published: true
date: 2026-09-05T07:40:00.000Z
tags: book/platform, business-units, data-model
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Business Unit — Data Model

## 1. At a Glance

- ฟิลด์ identity (ชื่อโรงแรม, `code`) บน `tb_business_unit` — **`code` ตอนนี้ unique ทั่วทั้งแพลตฟอร์ม ไม่ใช่แค่ต่อ cluster** และ backend เป็นคนสุ่มให้ตอนสร้าง (Crockford base32, 8 ตัวอักษร) ผู้ใช้ไม่มีช่องให้กรอกอีกต่อไป
- ที่อยู่ hotel/company ถูก restructure เป็น 10 คอลัมน์ต่อฝั่ง: `*_address_line1`, `*_address_line2`, `*_sub_district`, `*_district`, `*_city`, `*_province`, `*_postal_code`, `*_country`, `*_latitude`, `*_longitude`
- ฟิลด์รูปแบบ (date, currency, decimal) และ timezone
- **`max_license_users` ถูกถอดออกจากคอลัมน์จริงแล้ว** (migration `20260821000000_drop_bu_max_license_users`) — ที่นั่งตอนนี้เป็น ledger แบบมีวันที่ในตารางใหม่ `tb_business_unit_license` (หนึ่งแถวต่อสัญญาที่นั่ง) รวมผ่าน view `v_business_unit_seat`
- **`db_connection` (JSON blob) ถูกถอดออกจากคอลัมน์จริงแล้วเช่นกัน** — แทนที่ด้วย `database_pool_id` (FK ไปตารางใหม่ `tb_database_pool`) และ `db_schema` (ชื่อ schema ของ BU เอง) BU ไม่ถือ host/port/username/password ของตัวเองอีกต่อไป
- Array `config[]` (คู่ key/value/datatype — ตอน save จะเก็บเฉพาะ row ที่มีทั้ง `key` และ `label`; ตัวเลือก datatype มี `enum` เพิ่มมาด้วย)
- `doc_version Int @default(0)` — token optimistic-lock เพิ่มทั้ง platform schema เมื่อ 2026-07-16
- Branding file token: `logo_file_token` / `avatar_file_token` — API resolve เป็น presigned object `logo`/`avatar` ฝังในตัว ไม่เปิดเผย token ดิบ; อัปโหลดผ่าน `POST /api-system/business-units/:id/logo` และ `/avatar`
- คอลัมน์ audit: API คืน object `audit` แบบ nested (`audit.created/updated/deleted` แต่ละตัวเป็น `{ at, id, name, avatar }`); SPA flatten กลับผ่าน `normalizeAudit()` ที่ใช้ร่วมกันทั้งหน้ารายการและหน้าแก้ไข
- Role ของ BU-user join (`enum_user_business_unit_role`: `admin`/`user`) orthogonal กับโมเดล Platform RBAC ([rbac](/th/platform/rbac))

## 2. References

- ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma — `model tb_business_unit`, `model tb_business_unit_license` (ledger ที่นั่งใหม่), `model tb_database_pool` (ตารางใหม่ที่ `db_connection` เดิมถูกแทนที่ด้วย)
- ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260821000000_drop_bu_max_license_users/ — migration ที่ลบ `max_license_users`
- ../carmen-platform/src/types/index.ts — interface `BusinessUnit` (รวม `doc_version?: number`), `BusinessUnitConfig`, `BusinessUnitLicense`, `DatabasePool`, `PresignedImage`
- ../carmen-platform/src/utils/{databasePool,buLicense}.ts — ตัวสุ่มชื่อ schema และการคำนวณ ledger ที่นั่ง
- ../carmen-platform/src/services/businessUnitService.ts — REST client (`/api-system/business-units`) — **`revealDbPassword` ไม่มีอยู่แล้ว** เพราะ `db_connection`/password ถูกถอดออกทั้งบล็อก

## 3. TODO

- [ ] เขียนตารางฟิลด์ฉบับเต็มตาม en/platform/business-units/data-model (รวม `tb_business_unit_license`/`tb_database_pool` และการเปลี่ยน `code` เป็น unique ทั่วแพลตฟอร์ม)
- [ ] Document namespace ของ key ใน config array
