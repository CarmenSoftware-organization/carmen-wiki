---
title: Applications — แบบจำลองข้อมูล (Data Model)
description: ตาราง tb_application และ tb_application_api, shape read/write ที่ไม่สมมาตร, semantics แบบ replace ของ PUT, api-catalog ที่ generate ขึ้น และตระกูล tb_application_role ที่มีเฉพาะใน schema
published: true
date: 2026-06-10T15:15:00.000Z
tags: book/platform, applications, data-model
editor: markdown
dateCreated: 2026-06-10T15:15:00.000Z
---

# Applications — แบบจำลองข้อมูล (Data Model)

> **At a Glance**
> **ตาราง:** `tb_application` &nbsp;·&nbsp; `tb_application_api` (grant row แบบ 1:N) &nbsp;·&nbsp; **Enum:** ไม่มี — `api_name` เป็น VarChar รูปแบบอิสระ &nbsp;·&nbsp; **Identity:** `tb_application.id` (UUID) คือค่า `x-app-id`; ไม่มีคอลัมน์ app-id แยกต่างหาก &nbsp;·&nbsp; **ทางแยกของ grant:** boolean `allow_all` — เมื่อเป็น true, row ของ `tb_application_api` ไม่มีความหมาย &nbsp;·&nbsp; **Shape การเขียน:** ไม่สมมาตร — การอ่านคืน `api_names: string[]` แบบแบน การเขียนส่ง `details.add[]` ด้วย **semantics แบบ replace** &nbsp;·&nbsp; **Catalog:** ไม่ใช่ตาราง — ไฟล์ที่ generate ขึ้นใน backend-gateway เสิร์ฟผ่าน `/api-system/applications/api-catalog`

> **Source of truth:** Prisma platform schema ฝั่ง backend อ่านไฟล์นี้ก่อนเสมอเมื่อเขียนหรืออัพเดทหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` เป็นสำเนาที่ generate อัตโนมัติ ไม่ใช่ไฟล์อ้างอิงหลัก

## 1. ภาพรวม

โมดูล Applications เป็นเจ้าของสองตาราง `tb_application` คือทะเบียนของ client: หนึ่ง row ต่อ machine caller ถือ identity (`name`, `description`), สถานะ (`is_active`) และสวิตช์โหมด grant (`allow_all`) `id` ของมันทำหน้าที่เป็น credential ไปด้วย — UUID ที่ client ต้องส่งเป็น header `x-app-id` — row จึงไม่ต้องมีคอลัมน์ key หรือ secret ของตัวเอง

`tb_application_api` คือรายการ grant แบบระบุชัด: หนึ่ง row ต่อคู่ (application, `api_name`) มันมีความหมายเฉพาะเมื่อ `allow_all` ของ parent เป็น `false`; เมื่อ `allow_all = true` `AppIdGuard` ของ backend ผ่านโดยไม่ปรึกษามันเลย **ไม่มีตารางสำหรับ catalog ที่เลือกได้**: ชุดของค่า `api_name` ที่ valid เป็นไฟล์ TypeScript ที่ generate ขึ้นใน backend gateway (§5.1) ไม่ใช่ reference data ใน Postgres

ทั้งสองตารางมี audit trio มาตรฐานของแพลตฟอร์มและ unique constraint ที่รองรับ soft-delete (`deleted_at` ร่วมอยู่ในทุก `@@unique`) ดังนั้นชื่อ application ที่ถูกลบหรือ grant ที่ถูกถอดออกสามารถสร้างใหม่ได้โดยไม่เกิด key ชนกัน

## 2. เอนทิตี

### 2.1 `tb_application`

API client ที่ลงทะเบียน Schema บรรทัด 75

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` — **UUID นี้คือค่า `x-app-id`** ที่ client ส่งมากับทุก request |
| `name` | `String @db.VarChar` | No | ชื่อ application; unique ในหมู่ live row |
| `description` | `String?` | Yes | คำอธิบาย free-text แบบ optional |
| `is_active` | `Boolean?` | Yes | Default `true`; badge Active/Inactive ใน SPA |
| `allow_all` | `Boolean?` | Yes | Default `false`; `true` มอบทุก endpoint ที่ถูก guard และทำให้ row ของ `tb_application_api` ไม่มีความหมาย |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาสร้าง row, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: user id ของผู้สร้าง (FK ไป `tb_user`) |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาอัพเดทล่าสุด, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: user id ของผู้อัพเดทล่าสุด (FK ไป `tb_user`) |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp ของ soft-delete; NULL = row ที่ยังใช้งานอยู่ |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: user id ของผู้ลบ |

**Constraint:**
- `@id` บน `id`
- FK: `created_by_id` / `updated_by_id` → `tb_user.id` (`onDelete: NoAction, onUpdate: NoAction`)
- `@@unique([name, deleted_at])` — map `"application_name_deleted_at_u"` — หนึ่ง live row ต่อชื่อ; ชื่อที่ถูก soft-delete นำกลับมาใช้ได้

**Index:**
- `@@index([name, deleted_at])` — map `"application_name_deleted_at_idx"`

### 2.2 `tb_application_api`

หนึ่ง API grant แบบระบุชัด: application นี้เรียก endpoint ที่ถูก guard ด้วย `api_name` นี้ได้ Schema บรรทัด 98

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `application_id` | `String @db.Uuid` | No | FK ไป `tb_application.id` |
| `api_name` | `String @db.VarChar` | No | key ที่ได้รับ grant, shape `resource.action` (เช่น `cluster.create`); รูปแบบอิสระ — ความ valid เป็นไปตาม convention เทียบกับ catalog ที่ generate ขึ้น ไม่ใช่ constraint ของ DB |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาสร้าง row, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: user id ของผู้สร้าง (FK ไป `tb_user`) |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาอัพเดทล่าสุด, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: user id ของผู้อัพเดทล่าสุด (FK ไป `tb_user`) |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp ของ soft-delete; NULL = row ที่ยังใช้งานอยู่ |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: user id ของผู้ลบ |

**Constraint:**
- `@id` บน `id`
- FK: `application_id` → `tb_application.id` (`onDelete: NoAction, onUpdate: NoAction`)
- FK: `created_by_id` / `updated_by_id` → `tb_user.id` (`onDelete: NoAction, onUpdate: NoAction`)
- `@@unique([application_id, api_name, deleted_at])` — map `"application_api_app_name_deleted_at_u"` — หนึ่ง live grant ต่อคู่ (application, key); grant ที่ถูกถอดออกสามารถเพิ่มกลับได้

**Index:**
- `@@index([application_id, deleted_at])` — map `"application_api_app_deleted_at_idx"` — ขับเคลื่อน "grant ของ application X" (การ flatten เป็น `api_names` ของ read model และการ lookup ของ guard)

## 3. ความสัมพันธ์

```
tb_application  1 ─── M  tb_application_api          (Prisma FK, NoAction/NoAction)
tb_application.created_by_id / updated_by_id  ──>  tb_user.id   (audit actor, Prisma FK)
tb_application_api.created_by_id / updated_by_id  ──>  tb_user.id  (audit actor, Prisma FK)
```

นั่นคือกราฟทั้งหมด: application เชื่อมโยงกับ grant row ของมันและ audit actor เท่านั้น ไม่มีความสัมพันธ์กับ cluster, business unit หรือ (นอกเหนือจาก audit) ผู้ใช้ — identity ของ application เป็น platform-global สังเกตว่า `onDelete: NoAction` หมายความว่าการลบ row ของ `tb_application` ที่ระดับฐานข้อมูลจะไม่ cascade เข้า `tb_application_api`; ในทางปฏิบัติแพลตฟอร์มใช้ soft-delete ดังนั้นการจัดการ orphan เป็นเรื่องของชั้น application

## 4. Enum

โมดูลนี้ **ไม่กำหนด enum ใด ๆ** `api_name` เป็น `VarChar` รูปแบบอิสระ: คลังศัพท์ที่ valid เป็นข้อมูลปลายเปิด ขยายทุกครั้งที่การเรียก `AppIdGuard('...')` ตัวใหม่ลงใน backend gateway และ catalog ถูก regenerate — ไม่มีการเปลี่ยน schema เข้ามาเกี่ยวข้อง โหมดของ grant เป็น boolean ธรรมดา `allow_all` ไม่ใช่ enum ของโหมด

## 5. ความแตกต่างจาก shape ของ carmen-platform SPA

type ของ SPA อยู่ใน `../carmen-platform/src/types/index.ts` (`Application`, `ApplicationWritePayload`, `ApiCatalogGroup`); ชั้นการแปลคือ `src/services/applicationService.ts` model การอ่านและการเขียนจงใจ**ไม่สมมาตร**:

| Shape ของ SPA | แหล่งที่มาใน SPA | การจัดเก็บใน Prisma | หมายเหตุ |
| --------- | ---------- | -------------- | ----- |
| `Application.api_names: string[]` (แบน) | `Application` | join row ใน `tb_application_api` | API flatten grant row เป็น key string; SPA ไม่เคยเห็น id ของ grant-row |
| `ApplicationWritePayload.details: { add: { api_name }[] }` | `toWritePayload` ใน `applicationService.ts` | join row เดียวกัน | การเขียนห่อแต่ละ key เป็น `{ api_name }` ใต้ `details.add`; รายการถูก trim และตัวที่ว่างถูกทิ้ง **`details` ถูกละเว้นทั้งหมดเมื่อ `allow_all` เป็น true** |
| `PUT` = **semantics แบบ replace** | `applicationService.update` | n/a | การ save ทุกครั้งส่งชุดที่ต้องการแบบเต็มใน `details.add` — เทียบกับ role ของ RBAC ซึ่ง `PUT` ส่ง delta `{ add, remove }` อย่า port รูปแบบ delta มาที่นี่ (หรือกลับกัน) |
| field "App ID" บนหน้าจอ edit | `ApplicationEdit.tsx` | ไม่ใช่คอลัมน์ | เป็น label สำหรับแสดง `id` ของเรคคอร์ด; ไม่มีคอลัมน์หรือ field `app_id` ใน DTO |
| `ApiCatalogGroup { module, api_names[] }` | `getApiCatalog` | **ไม่มีตาราง** | catalog คือ `app-api-catalog.generated.ts` ใน backend-gateway, emit จากการสแกน `AppIdGuard` (§5.1) |
| ความทนทานต่อ envelope ของ catalog | `getApiCatalog` | n/a | endpoint คืน `{ api_names: string[], groups?: ApiCatalogGroup[] }` ซึ่งอาจอยู่ใน envelope `{ data }` มาตรฐาน; service ยังรองรับ `string[]` เปล่า ๆ ด้วย เมื่อ `groups` หายไปหรือไม่ผ่าน runtime guard รายตัว client จะ derive กลุ่มที่เหมือนกันทุกประการผ่าน `groupApiNames()` (`src/utils/apiCatalog.ts`: module = prefix ก่อน `.` ตัวแรก; ชื่อที่ไม่มีจุดเป็นโมดูลของตัวเอง; `actionOf()` = ข้อความหลังจุดแรก) — กฎการแบ่งเดียวกับ generator ฝั่ง backend ดังนั้นผลลัพธ์ของ fallback เท่ากับผลลัพธ์ของ server |
| `created_at`/`created_by_name` แบบแบนบน row ของ list | `ApplicationManagement.tsx` | คอลัมน์ audit id | response ของ list อาจซ้อนข้อมูล audit เป็น `audit.created/updated` `{ at, name }`; SPA flatten และรองรับทั้งสอง shape |

### 5.1 endpoint ของ catalog และ generator

`GET /api-system/applications/api-catalog` เสิร์ฟเนื้อหาของ `apps/backend-gateway/src/platform/applications/app-api-catalog.generated.ts` ซึ่ง `scripts/generate-app-api-catalog/run.ts` ผลิตขึ้นโดยสแกนทุกไฟล์ `.ts` ใต้ source ของ gateway หาการเรียก `new AppIdGuard('<api_name>')` (match ด้วย regex), de-duplicate, เรียงลำดับ และจัดกลุ่มตามโมดูล ไฟล์ export ทั้ง `APP_API_CATALOG` แบบแบนและ `APP_API_CATALOG_GROUPS` ห้ามแก้ไขด้วยมือเด็ดขาด — regenerate ด้วย `bun run scripts/generate-app-api-catalog/run.ts` หลังเพิ่ม guard

### 5.2 มีเฉพาะใน schema: ตระกูล `tb_application_role`

platform schema ยังมี `tb_application_role` (บรรทัด 31), `tb_application_role_tb_permission` (บรรทัด 55) และ `tb_user_tb_application_role` (บรรทัด 580) แม้จะมี prefix ว่า `application` พวกมัน**ไม่ใช่ส่วนหนึ่งของแบบจำลอง machine-client ของโมดูลนี้**: พวกมันอธิบายชุด role ที่ scope ระดับ business unit (`tb_application_role.business_unit_id` → `tb_business_unit`) ที่ join row ของ `tb_permission` เข้ากับผู้ใช้ — คลังศัพท์ RBAC ภายในผลิตภัณฑ์สำหรับ application ฝั่ง inventory ไม่ใช่ grant สำหรับ caller ที่ใช้ `x-app-id` Platform SPA **ไม่มี surface สำหรับพวกมัน** — ไม่มีหน้า, service หรือ type ใดอ้างอิงถึงพวกมัน ณ 2026-06-10 — จึง document ไว้ที่นี่เพียงเพื่อแก้ความกำกวมของการตั้งชื่อ; ยังไม่จำเป็นต้องมีตาราง field จนกว่าจะมี UI

## 6. แหล่งข้อมูลอ้างอิง

REST surface ที่ `applicationService.ts` ใช้:

| Method + Path | วัตถุประสงค์ | หมายเหตุ |
|---|---|---|
| `GET /api-system/applications` | List | แบ่งหน้า; field ค้นหา `name`, `description`; filter `advance` บน `is_active`; row อาจมี `audit` ซ้อนอยู่ |
| `POST /api-system/applications` | สร้าง | `details.add` มีอยู่เฉพาะเมื่อ `allow_all` เป็น false |
| `GET /api-system/applications/:id` | Detail | คืน `api_names: string[]` แบบแบน |
| `PUT /api-system/applications/:id` | อัพเดท | **Semantics แบบ replace** — ชุดที่ต้องการแบบเต็มใน `details.add` |
| `DELETE /api-system/applications/:id` | ลบ | เข้าถึงได้จาก dropdown ของ row ในหน้า list เท่านั้น |
| `GET /api-system/applications/api-catalog` | catalog ของ `api_name` ที่เลือกได้ | `{ api_names, groups? }`, ทนทานต่อ envelope; มี fallback การจัดกลุ่มฝั่ง client |

**หลัก (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_application` (บรรทัด 75), `tb_application_api` (บรรทัด 98); ตระกูลที่มีเฉพาะใน schema ที่บรรทัด 31, 55, 580
- `../carmen-turborepo-backend-v2/scripts/generate-app-api-catalog/run.ts` — generator ของ catalog (การสแกน `AppIdGuard`, กฎการจัดกลุ่ม, path ของ output)

**รอง (shape ฝั่ง consumer):**
- `../carmen-platform/src/types/index.ts` — `Application`, `ApplicationWritePayload`, `ApiCatalogGroup`
- `../carmen-platform/src/services/applicationService.ts` — `toWritePayload`, การจัดการ envelope ของ `getApiCatalog` และ fallback การจัดกลุ่ม
- `../carmen-platform/src/utils/apiCatalog.ts` — `moduleOf`, `actionOf`, `groupApiNames`

**Cross-link:** [หน้า landing ของ Applications](/th/platform/applications) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Permissions](./permissions.md) &nbsp;·&nbsp; [Platform RBAC data-model](../rbac/data-model.md) (จุดเทียบของการเขียนแบบ delta)
