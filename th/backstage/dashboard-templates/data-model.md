---
title: Dashboard Templates — Data Model
description: ตารางฝั่ง backstage ที่อยู่เบื้องหลังเทมเพลตแดชบอร์ด (tb_dashboard_widget_template, tb_dashboard_bu_default_version), enum ที่ใช้ และ row deploy ฝั่ง tenant ที่บันทึกสิ่งที่ business unit ได้รับ
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, dashboard-templates, data-model
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Dashboard Templates — Data Model

> **At a Glance**
> **ตาราง:** เป็นเจ้าของ 2 (backstage DB) + อ้างอิง 2 (tenant DB) &nbsp;·&nbsp; **Enum:** `enum_dashboard_widget_type`, `enum_dataset_shape` &nbsp;·&nbsp; **คอลัมน์ audit:** `doc_version`, `created_*`, `updated_*`, `deleted_*` บนตารางเทมเพลต &nbsp;·&nbsp; **กฎระดับ DB:** CHECK constraint ของ kind และ module, ตารางเวอร์ชันแถวเดียว &nbsp;·&nbsp; **ความต่างเทียบกับ SPA:** เล็กน้อย 2 จุด

> **แหล่งความจริง:** Backend Prisma backstage schema อ่านที่นี่ก่อนเสมอเมื่อเขียนหรืออัปเดตหน้านี้:
> - `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma`
> - `.../prisma/migrations/20261006100000_dashboard_widget_template/migration.sql` (CHECK constraint มีอยู่ที่นี่เท่านั้น)
>
> ไฟล์ `generated/client/schema.prisma` เป็นสำเนาที่สร้างอัตโนมัติและไม่ใช่แหล่งอ้างอิงที่แท้จริง

## 1. ภาพรวม

เทมเพลตอยู่ใน**ฐานข้อมูล backstage (system)** มีสองตาราง: row ของเทมเพลต และตัวนับแถวเดียวที่ทำเวอร์ชันให้ทั้งชุด BU-default เมื่อ deploy ทำงาน ข้อมูลจะออกจากฐานข้อมูล backstage: widget ถูกเขียนลงฐานข้อมูล **tenant** ของแต่ละ business unit (`tb_dashboard_bu_widget`) และผลลัพธ์ถูกบันทึกในตาราง tenant แถวเดียว (`tb_dashboard_bu_widget_deploy`) ตาราง tenant เป็นของ tenant schema และ micro-data จึงสรุปไว้ที่นี่เท่านั้น

## 2. Entities

### 2.1 `tb_dashboard_widget_template`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
|---|---|---|---|
| **Identity** | | | |
| `id` | `String @id @db.Uuid` | No | Primary key |
| `kind` | `String @db.VarChar(20)` | No | `system` หรือ `bu_default` (CHECK) เปลี่ยนไม่ได้: ไม่อยู่ในรายการฟิลด์ที่ update |
| `module` | `String? @db.VarChar(50)` | Yes | โมดูลแดชบอร์ดเป้าหมาย `NULL` = `/dashboard` หลักของ BU อนุญาตเฉพาะ `bu_default` (CHECK) |
| `seed_key` | `String? @db.VarChar(100)` | Yes | identity ของ row ที่ seed เป็นเจ้าของ (`db:seed.dashboard-widget-template`); `NULL` = สร้างผ่าน API |
| **นิยาม widget** | | | |
| `dataset_id` | `String @db.VarChar(100)` | No | id ของ dataset จากแค็ตตาล็อก micro-data (เช่น `workflow.pending-approval`) ไม่มี FK; ตรวจกับแค็ตตาล็อกตอนเขียน |
| `widget_type` | `enum_dashboard_widget_type` | No | Render type |
| `title` | `String? @db.VarChar(255)` | Yes | title ภาษาอังกฤษแบบเดิม (เขียนคู่เป็น `title_i18n.en`) |
| `title_i18n` | `Json? @db.JsonB` | Yes | `{ en, th? }` ชนะ `title` |
| `order_index` | `Int @default(0)` | No | ตำแหน่งภายใน (kind, module) |
| `params` | `Json? @db.JsonB` | Yes | พารามิเตอร์ของ dataset, `{ name: string \| number }` |
| `display` | `Json? @db.JsonB` | Yes | ตัวเลือกการแสดงผลแบบอิสระ; serialize แล้วไม่เกิน 8 KB (micro-data ปฏิเสธที่ใหญ่กว่านี้ตอน deploy) SPA ของ backstage ไม่มีตัวแก้ไขสำหรับฟิลด์นี้ |
| **Scope (เฉพาะ system)** | | | |
| `allow_business_unit` | `Json? @db.JsonB` | Yes | array ของ BU code; `NULL`/`[]` = ไม่จำกัด |
| `deny_business_unit` | `Json? @db.JsonB` | Yes | array ของ BU code; deny ชนะ allow |
| **สถานะ** | | | |
| `is_active` | `Boolean @default(true)` | No | row ที่ inactive จะไม่ถูกเสิร์ฟ (system) และไม่ถูก deploy (bu_default) |
| **Audit** | | | |
| `doc_version` | `Int @default(0)` | No | Optimistic lock |
| `created_at`, `created_by_id`, `updated_at`, `updated_by_id`, `deleted_at`, `deleted_by_id` | `Timestamptz(6)?` / `Uuid?` | Yes | Soft delete ผ่าน `deleted_at` |

**Constraint:** `ck_dashboard_widget_template_kind` (`kind IN ('system','bu_default')`); `ck_dashboard_widget_template_module` (module เป็น NULL ได้เฉพาะเมื่อ kind เป็น `bu_default` ไม่งั้นต้องเป็นหนึ่งในเจ็ดชื่อโมดูล) partial unique index `(seed_key) WHERE seed_key IS NOT NULL` (migration `20261006130000_dashboard_widget_template_seed_key`) **Index:** `@@index([kind, module, deleted_at])` (`idx_dashboard_widget_template_kind_module`)

migration ที่สร้างตารางยัง insert system widget เริ่มต้น แต่ทำเฉพาะเมื่อยังไม่มีอยู่

### 2.2 `tb_dashboard_bu_default_version`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
|---|---|---|---|
| `id` | `Int @id @default(1)` | No | เป็น `1` เสมอ (CHECK `id = 1`) |
| `version` | `Int @default(0)` | No | เพิ่มขึ้นหนึ่งทุกครั้งที่เขียนเทมเพลต `bu_default`: create, update, delete, reorder migration insert เป็น 0; การเพิ่มครั้งแรกจะ upsert เป็น 1 ถ้า row หายไป |
| `updated_at`, `updated_by_id` | `Timestamptz(6)?`, `Uuid?` | Yes | ใครเพิ่มล่าสุด |

มีตัวนับเดียวสำหรับทั้งชุด ไม่ใช่ตัวละโมดูล การแก้ widget เพียงตัวเดียวทำให้ทุก BU กลายเป็น `outdated`

### 2.3 อ้างอิง: row deploy ฝั่ง tenant

`tb_dashboard_bu_widget_deploy` (tenant schema, `packages/prisma-shared-schema-tenant`): `id Int @id @default(1)`, `deployed_version Int`, `deployed_at`, `deployed_by_id`, `customized_at`, `customized_by_id` หนึ่ง row ต่อ tenant (CHECK `id = 1`) ดูแลโดย micro-data: การ deploy ตั้ง `deployed_version`/`deployed_at`/`deployed_by_id` และล้างฟิลด์ customized; การที่ BU admin แก้ board ของ BU ด้วยมือจะตั้ง `customized_at` (`DeployMarkCustomized`, `micro-data/db/widget_repo.go:119`) BU ที่มี BU widget อยู่แล้วก่อนมีระบบ deploy ถูก backfill เป็น customized ด้วย `deployed_version = 0` (tenant migration 131) ตัว widget เองเป็น row ของ `tb_dashboard_bu_widget`; ดู [Reporting Audit: Widget](/th/inventory/reporting-audit/widget)

## 3. ความสัมพันธ์

ไม่มี foreign key ภายในโมดูล มีเพียงลิงก์แบบ soft: `dataset_id` ไปยัง dataset registry ของ micro-data, รายการ `allow/deny_business_unit` ไปยัง `tb_business_unit.code` และ `created_by_id`/`updated_by_id` ไปยังผู้ใช้ ตัวนับเวอร์ชันสัมพันธ์กับเทมเพลตโดยข้อตกลง (service เพิ่มใน transaction เดียวกับการเขียน; ไม่มี database trigger)

## 4. Enums

| Enum | ค่า | หมายเหตุ |
|---|---|---|
| `enum_dashboard_widget_type` | `kpi`, `line`, `area`, `bar`, `pie`, `heatmap`, `gauge`, `table`, `sparkline` | API ตรวจ `widget_type` กับ enum นี้ (zod) แล้วตรวจกับ `supported_renders` ของ dataset |
| `enum_dataset_shape` | `scalar`, `scalar_delta`, `time_series`, `categorical`, `ranked`, `matrix` | กำหนดว่า dataset รองรับ render อะไร; micro-data ใช้ แสดงใน dropdown ของ dataset เป็น `name · shape` |

สถานะ deploy (`never`, `customized`, `outdated`, `current`) และโหมด deploy (`skip_customized`, `overwrite`) ไม่ใช่ enum ของฐานข้อมูล: สถานะคำนวณใน `deployStatusOf` (`deploy-status-of.ts`), โหมดเป็น zod enum บน deploy DTO

## 5. ความต่างจากรูปร่างของ SPA carmen-backstage

| ส่วน | Prisma / API | SPA type | หมายเหตุ |
|---|---|---|---|
| `widget_type` | enum 9 ค่า | `string` (`DashboardTemplate.widget_type`) | ปลอดภัย: dialog เสนอเฉพาะ render ที่แค็ตตาล็อกรายงาน มีไอคอนสำหรับ enum ทั้ง 9 ค่า; สตริงอื่นใดจะ fallback เป็นไอคอนกลาง (`widgetTypes.ts`) |
| `display`, `seed_key`, `*_by_id` | มีบน row | `display` มี type แต่ไม่เคยถูกแก้; ตัวอื่นไม่มี | `display` round-trip ได้โดยไม่ถูกแตะ ก็ต่อเมื่อ SPA ไม่ส่งมันใน PATCH ซึ่งเป็นเช่นนั้น (dialog ไม่ส่ง `display`) |

นอกนั้นสอดคล้องกับ `DashboardTemplate` (`src/types/index.ts:2010`) ณ 2026-10-27

## 6. แหล่งอ้างอิง

- หลัก: `packages/prisma-shared-schema-backstage/prisma/schema.prisma` (`tb_dashboard_widget_template`, `tb_dashboard_bu_default_version`, enum), migration `20261006100000_dashboard_widget_template`, `20261006130000_dashboard_widget_template_seed_key`, `20261008100000_dashboard_widget_template_title_i18n`
- รอง: `../carmen-backstage/src/types/index.ts` (`DashboardTemplate*`, `DashboardDeploy*`, `DashboardDatasetInfo`)
- ฝั่ง tenant: `packages/prisma-shared-schema-tenant/prisma/schema.prisma` (`tb_dashboard_bu_widget_deploy`), `micro-data/migrations/tenant/131_dash_bu_widget_module.up.sql`
- หน้าข้างเคียง: [Dashboard Templates](/th/backstage/dashboard-templates), [Lifecycle](/th/backstage/dashboard-templates/lifecycle)
