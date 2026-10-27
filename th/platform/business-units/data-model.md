---
title: Business Unit — Data Model
description: Entity ของ BU, ledger ที่นั่ง tb_business_unit_license, ledger interface licence (INF), database_pool_id/db_schema ที่แทน db_connection, branding file token และบันทึกภายใน
published: true
date: '2026-10-27T15:00:00.000Z'
tags: book/platform, business-units, data-model
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Business Unit — Data Model

## 1. At a Glance

- ฟิลด์ identity (ชื่อโรงแรม, `code`) บน `tb_business_unit` — **`code` ตอนนี้ unique ทั่วทั้งแพลตฟอร์ม ไม่ใช่แค่ต่อ cluster** และ backend เป็นคนสุ่มให้ตอนสร้าง (Crockford base32, 8 ตัวอักษร) ผู้ใช้ไม่มีช่องให้กรอกอีกต่อไป
- ที่อยู่ hotel/company ถูก restructure เป็น 10 คอลัมน์ต่อฝั่ง: `*_address_line1`, `*_address_line2`, `*_sub_district`, `*_district`, `*_city`, `*_province`, `*_postal_code`, `*_country`, `*_latitude`, `*_longitude`
- ฟิลด์รูปแบบ (date, currency, decimal) และ timezone (คอลัมน์ `perpage_format` ถูก drop แล้วโดย migration `20260928100000_drop_business_unit_perpage_format`); `calculation_method` (`enum_calculation_method`) มีค่า `average` / `fifo` / `average_per_location`
- **`max_license_users` ถูกถอดออกจากคอลัมน์จริงแล้ว** (migration `20260821000000_drop_bu_max_license_users`) — ที่นั่งตอนนี้เป็น ledger แบบมีวันที่ในตารางใหม่ `tb_business_unit_license` (หนึ่งแถวต่อสัญญาที่นั่ง) รวมผ่าน view `v_business_unit_seat`
- **`tb_business_unit_interface_license` — ledger interface licence ต่อ BU (ตั้งแต่ 2026-09-10)**: หนึ่งแถวต่อ feature group ชนิด `interface` ต่อช่วงวันที่ เลขที่ขึ้นต้น `INF` เอกสารฉบับเต็มอยู่ที่ [Licenses — Data Model](/th/platform/licenses/data-model) §2.4; ตาราง entitlement แบบแบน `tb_business_unit_interface` ที่มันมาแทนถูก drop เมื่อ 2026-09-08 FK `license_feature_group_id → tb_license_feature_group.id` เป็นเส้นทางเดียวจาก BU ไปยัง catalog ของ licence ที่ไม่ผ่าน `tb_subscription_bu`
- **`db_connection` (JSON blob) ถูกถอดออกจากคอลัมน์จริงแล้วเช่นกัน** — แทนที่ด้วย `database_pool_id` (FK ไปตารางใหม่ `tb_database_pool`) และ `db_schema` (ชื่อ schema ของ BU เอง) BU ไม่ถือ host/port/username/password ของตัวเองอีกต่อไป
- Array `config[]` (คู่ key/value/datatype — ตอน save จะเก็บเฉพาะ row ที่มีทั้ง `key` และ `label`; ตัวเลือก datatype มี `enum` เพิ่มมาด้วย)
- `doc_version Int @default(0)` — token optimistic-lock เพิ่มทั้ง platform schema เมื่อ 2026-07-16
- Branding file token: `logo_file_token` / `avatar_file_token` — API resolve เป็น presigned object `logo`/`avatar` ฝังในตัว ไม่เปิดเผย token ดิบ; อัปโหลดผ่าน `POST /api-system/business-units/:id/logo` และ `/avatar`
- คอลัมน์ audit: API คืน object `audit` แบบ nested (`audit.created/updated/deleted` แต่ละตัวเป็น `{ at, id, name, avatar }`); SPA flatten กลับผ่าน `normalizeAudit()` ที่ใช้ร่วมกันทั้งหน้ารายการและหน้าแก้ไข
- **`tb_business_unit_note` — บันทึกภายในของเจ้าหน้าที่ (ใหม่ 2026-10-26)**: โน้ตอิสระและไฟล์แนบที่เจ้าหน้าที่ Backstage ทิ้งไว้บน BU ไม่แสดงให้ tenant เห็นเลย เพิ่มโดย migration `20261026160000_add_business_unit_note`; permission `bu_note.view` / `bu_note.manage` join M:N เดิม `tb_business_unit_tb_module` และแค็ตตาล็อก `tb_module` ไม่มีอีกแล้ว (drop โดย migration `20260818000000_license_model`)
- `tb_user_tb_business_unit.seat_released_at` (ใหม่ 2026-10-27, migration `20261027090000_add_user_bu_seat_released_at`) ถูกตั้งโดย action **Release seat** ของ cluster ซึ่งตั้ง `is_active = false` ด้วย
- Role ของ BU-user join (`enum_user_business_unit_role`: `admin`/`user`) orthogonal กับโมเดล Platform RBAC ([rbac](/th/platform/rbac))

## 2. References

- ../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma — `model tb_business_unit`, `model tb_business_unit_license` (ledger ที่นั่งใหม่), `model tb_business_unit_interface_license` (ledger interface licence, 2026-09-10), `model tb_database_pool` (ตารางใหม่ที่ `db_connection` เดิมถูกแทนที่ด้วย)
- ../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/migrations/20260821000000_drop_bu_max_license_users/ — migration ที่ลบ `max_license_users`
- ../carmen-backstage/src/types/index.ts — interface `BusinessUnit` (รวม `doc_version?: number`), `BusinessUnitConfig`, `BusinessUnitLicense`, `DatabasePool`, `PresignedImage`
- ../carmen-backstage/src/utils/{databasePool,buLicense}.ts — ตัวสุ่มชื่อ schema และการคำนวณ ledger ที่นั่ง
- ../carmen-backstage/src/services/businessUnitService.ts — REST client (`/api-system/business-units`) — **`revealDbPassword` ไม่มีอยู่แล้ว** เพราะ `db_connection`/password ถูกถอดออกทั้งบล็อก

## 3. TODO

- [ ] เขียนตารางฟิลด์ฉบับเต็มตาม en/platform/business-units/data-model (รวม `tb_business_unit_license`/`tb_business_unit_interface_license`/`tb_database_pool` และการเปลี่ยน `code` เป็น unique ทั่วแพลตฟอร์ม)
- [ ] Document namespace ของ key ใน config array
