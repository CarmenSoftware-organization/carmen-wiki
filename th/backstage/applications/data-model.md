---
title: Applications — แบบจำลองข้อมูล (Data Model)
description: ตาราง tb_application, tb_application_api, tb_application_bypass_user (รวมคอลัมน์สถานะบริการและ app-secret), shape read/write ไม่สมมาตร, replace ของ PUT, api-catalog และ tb_application_role
published: true
date: 2026-10-29T05:30:00.000Z
tags: book/backstage, applications, data-model
editor: markdown
dateCreated: 2026-06-10T15:15:00.000Z
---

# Applications — แบบจำลองข้อมูล (Data Model)

> **At a Glance**
> **ตาราง:** `tb_application` &nbsp;·&nbsp; `tb_application_api` (grant row แบบ 1:N) &nbsp;·&nbsp; `tb_application_bypass_user` (ผู้ใช้ที่ได้รับการยกเว้นจาก maintenance/read-only) &nbsp;·&nbsp; **Enum:** ไม่มี — `api_name` เป็น VarChar รูปแบบอิสระ &nbsp;·&nbsp; **Identity:** `tb_application.id` (UUID) คือค่า `x-app-id`; ไม่มีคอลัมน์ app-id แยกต่างหาก &nbsp;·&nbsp; **ทางแยกของ grant:** boolean `allow_all` — เมื่อเป็น true, row ของ `tb_application_api` ไม่มีความหมาย &nbsp;·&nbsp; **Shape การเขียน:** ไม่สมมาตร — การอ่านคืน `api_names: string[]` แบบแบน การเขียนส่ง `details.add[]` ด้วย **semantics แบบ replace** &nbsp;·&nbsp; **Concurrency:** `doc_version Int @default(0)` บนทั้งสองตาราง (เพิ่มเมื่อ 2026-06-12) บังคับใช้เป็น optimistic lock บน `PUT`/`POST` &nbsp;·&nbsp; **Catalog:** ไม่ใช่ตาราง — ไฟล์ที่ generate ขึ้นใน backend-gateway เสิร์ฟผ่าน `/api-system/applications/api-catalog`

> **Source of truth:** Prisma platform schema ฝั่ง backend อ่านไฟล์นี้ก่อนเสมอเมื่อเขียนหรืออัพเดทหน้านี้:
> - `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` เป็นสำเนาที่ generate อัตโนมัติ ไม่ใช่ไฟล์อ้างอิงหลัก

## 1. ภาพรวม

โมดูล Applications เป็นเจ้าของสามตาราง `tb_application` คือทะเบียนของ client: หนึ่ง row ต่อ machine caller ถือ identity (`name`, `description`), สถานะบริการ (`status` และคอลัมน์ message/until/changed-by), สวิตช์โหมด grant (`allow_all`) และ credential ตัวที่สองแบบเลือกได้คือ `x-app-secret` (`require_secret`, คอลัมน์ ciphertext และ last-4) `id` ของมันคือ UUID ที่ client ต้องส่งเป็น header `x-app-id`; secret แยกต่างหากและเป็นทางเลือก เว้นแต่ `require_secret` เปิดอยู่

`tb_application_bypass_user` ระบุผู้ใช้ที่ยังเข้าถึงได้เต็มที่ขณะ application อยู่ในสถานะ `maintenance` หรือ `read_only` (ไม่ใช่ใน `disabled`)

`tb_application_api` คือรายการ grant แบบระบุชัด: หนึ่ง row ต่อคู่ (application, `api_name`) มันมีความหมายเฉพาะเมื่อ `allow_all` ของ parent เป็น `false`; เมื่อ `allow_all = true` `AppIdGuard` ของ backend ผ่านโดยไม่ปรึกษามันเลย **ไม่มีตารางสำหรับ catalog ที่เลือกได้**: ชุดของค่า `api_name` ที่ valid เป็นไฟล์ TypeScript ที่ generate ขึ้นใน backend gateway (§5.1) ไม่ใช่ reference data ใน Postgres

`tb_application` และ `tb_application_api` มี audit trio มาตรฐานของแพลตฟอร์มและ unique constraint ที่รองรับ soft-delete (`deleted_at` ร่วมอยู่ในทุก `@@unique`) ดังนั้นชื่อ application ที่ถูกลบหรือ grant ที่ถูกถอดออกสามารถสร้างใหม่ได้โดยไม่เกิด key ชนกัน

## 2. เอนทิตี

### 2.1 `tb_application`

API client ที่ลงทะเบียน Schema บรรทัด 65

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` — **UUID นี้คือค่า `x-app-id`** ที่ client ส่งมากับทุก request |
| `name` | `String @db.VarChar` | No | ชื่อ application; unique ในหมู่ live row |
| `description` | `String?` | Yes | คำอธิบาย free-text แบบ optional |
| `is_active` | `Boolean?` | Yes | Default `true` เป็นแฟลกแบบ legacy: SPA ไม่เขียนมันอีกแล้ว (`toWritePayload` ตัดออกโดยตั้งใจ) และ read model ของ API derive มันจาก `status` (`isActiveFor(status)`); SPA อ่านมันเป็น fallback เท่านั้นเมื่อไม่มี `status` (`statusOf()`) |
| `status` | `String @db.VarChar` | No | Default `"running"`; หนึ่งใน `running` / `maintenance` / `read_only` / `disabled` CHECK constraint อยู่ใน migration ไม่ใช่ใน Prisma |
| `status_message` | `String?` | Yes | ข้อความที่แสดงให้ caller/ผู้ใช้ขณะไม่ได้ running (SPA จำกัด 1000 ตัวอักษร) |
| `status_until` | `DateTime? @db.Timestamptz(6)` | Yes | เวลา "expected back" ที่ประกาศไว้; แสดงผลเท่านั้น — ไม่มีอะไรสลับสถานะกลับอัตโนมัติ service ปฏิเสธค่าที่ไม่ใช่ ISO |
| `status_changed_at` / `status_changed_by_id` | `DateTime?` / `String? @db.Uuid` | Yes | ใครเปลี่ยนสถานะล่าสุดและเมื่อไร (FK ไป `tb_user`; API คืน `status_changed_by_name`) |
| `require_secret` | `Boolean` | No | Default `false`; เมื่อ true gateway ปฏิเสธคำขอที่ไม่มี `x-app-secret` ที่ถูกต้อง (`401 APP_SECRET_INVALID`) CHECK ใน migration: อนุญาตเฉพาะเมื่อ `secret_ciphertext` ถูกตั้ง |
| `secret_ciphertext` | `String?` | Yes | `enc:v1:<iv>:<tag>:<ct>` — AES-256-GCM ผ่าน `@repo/secret-crypto` ด้วย `SECRET_ENCRYPTION_KEY`; ถอดรหัสเฉพาะใน micro-cluster ไม่เคยส่งไป SPA |
| `secret_last4` | `String? @db.VarChar(4)` | Yes | สี่ตัวอักษรสุดท้ายของ plaintext ตั้งพร้อมกับ ciphertext; ขับเคลื่อน stub ที่ปิดบังและ `has_secret` |
| `secret_rotated_at` / `secret_rotated_by_id` | `DateTime?` / `String? @db.Uuid` | Yes | การ generate/rotate ล่าสุด (API คืน `secret_rotated_by_name`) |
| `secret_previous_ciphertext` / `secret_previous_expires_at` | `String?` / `DateTime?` | Yes | secret ก่อน rotation ที่ยังถูกรับจนถึงเวลาหมดอายุ (24 ชม. หลัง rotation, `APP_SECRET_GRACE_MS`); read model ทิ้งเวลาหมดอายุที่ผ่านไปแล้ว |
| `allow_all` | `Boolean?` | Yes | Default `false`; `true` มอบทุก endpoint ที่ถูก guard และทำให้ row ของ `tb_application_api` ไม่มีความหมาย |
| `device` | `String @db.VarChar` | No | Default `"web"`; คลาสของอุปกรณ์ที่ application นี้ระบุตัวตนเป็น รูปแบบอิสระที่ระดับ DB; SPA จำกัดค่าไว้ที่ `mobile` / `web` / `desktop` / `pos` (`DeviceType` / `DEVICE_OPTIONS`) อ่านโดย app-allowlist ของ backend-gateway (`getDevice(appId)`) เพื่อใช้พฤติกรรมเฉพาะอุปกรณ์ — เช่น [filter รายการ draft-only ของ GRN บน mobile](/th/inventory/good-receive-note/02-business-rules) |
| `doc_version` | `Int` | No | Default `0`; token optimistic-concurrency เพิ่มทั้ง platform schema (35 ตาราง) เมื่อ 2026-06-12 (`8e53bbe`) `ApplicationEdit` ส่งค่านี้กลับไปทุกครั้งที่ `POST`/`PUT`; การเขียนที่ล้าหลังจะถูกปฏิเสธด้วย `409` และ SPA โหลด record ใหม่พร้อม toast แจ้ง conflict แทนที่จะเขียนทับแบบเงียบ ๆ |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาสร้าง row, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: user id ของผู้สร้าง (FK ไป `tb_user`) |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาอัพเดทล่าสุด, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: user id ของผู้อัพเดทล่าสุด (FK ไป `tb_user`) |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp ของ soft-delete; NULL = row ที่ยังใช้งานอยู่ |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: user id ของผู้ลบ |

**Constraint:**
- `@id` บน `id`
- FK: `created_by_id` / `updated_by_id` / `status_changed_by_id` / `secret_rotated_by_id` → `tb_user.id` (`onDelete: NoAction, onUpdate: NoAction`)
- `@@unique([name, deleted_at])` — map `"application_name_deleted_at_u"` — หนึ่ง live row ต่อชื่อ; ชื่อที่ถูก soft-delete นำกลับมาใช้ได้

**Index:**
- `@@index([name, deleted_at])` — map `"application_name_deleted_at_idx"`

### 2.2 `tb_application_bypass_user`

Schema บรรทัด 112 หนึ่ง row ต่อการยกเว้น (application, user)

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `application_id` | `String @db.Uuid` | No | FK ไป `tb_application.id`, `onDelete: Cascade` |
| `user_id` | `String @db.Uuid` | No | FK ไป `tb_user.id` |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | ใครเพิ่ม row |

`@@unique([application_id, user_id])` (`application_bypass_user_app_user_u`) และ `@@index([user_id])` ไม่มี `deleted_at`/`doc_version`: รายการถูกแทนที่ทั้งชุดด้วย `PUT …/bypass-users` ซึ่งคืน `400` สำหรับ user id ที่ไม่รู้จักด้วย gateway ตรวจต่อคำขอ (`appAllowlistStore.isBypassUser`)

### 2.3 `tb_application_api`

หนึ่ง API grant แบบระบุชัด: application นี้เรียก endpoint ที่ถูก guard ด้วย `api_name` นี้ได้ Schema บรรทัด 126

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `application_id` | `String @db.Uuid` | No | FK ไป `tb_application.id` |
| `api_name` | `String @db.VarChar` | No | key ที่ได้รับ grant, shape `resource.action` (เช่น `cluster.create`); รูปแบบอิสระ — ความ valid เป็นไปตาม convention เทียบกับ catalog ที่ generate ขึ้น ไม่ใช่ constraint ของ DB |
| `doc_version` | `Int` | No | Default `0`; counter optimistic-lock เดียวกับ `tb_application` ข้างบน SPA ไม่ได้แสดงแยกต่างหาก — grant row ถูกเขียนทับใหม่ทั้งชุดเสมอผ่าน `PUT` แบบ replace-semantics ของ application แม่ |
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
tb_application  1 ─── M  tb_application_bypass_user   (Prisma FK, onDelete Cascade)
tb_application_bypass_user.user_id  ──>  tb_user.id
tb_application.created_by_id / updated_by_id / status_changed_by_id / secret_rotated_by_id  ──>  tb_user.id   (Prisma FK)
tb_application_api.created_by_id / updated_by_id  ──>  tb_user.id  (audit actor, Prisma FK)
```

นั่นคือกราฟทั้งหมด: application เชื่อมโยงกับ grant row, bypass user และ audit/status/secret actor ของมัน ไม่มีความสัมพันธ์กับ cluster หรือ business unit — identity ของ application เป็น platform-global สังเกตว่า `onDelete: NoAction` หมายความว่าการลบ row ของ `tb_application` ที่ระดับฐานข้อมูลจะไม่ cascade เข้า `tb_application_api`; ในทางปฏิบัติแพลตฟอร์มใช้ soft-delete ดังนั้นการจัดการ orphan เป็นเรื่องของชั้น application

## 4. Enum

โมดูลนี้ **ไม่กำหนด Prisma enum ใด ๆ**; สถานะบริการเป็น `VarChar` ธรรมดาที่ป้องกันด้วย CHECK ใน migration และ union `ApplicationStatus` ของ SPA คือ `'running' | 'maintenance' | 'read_only' | 'disabled'` (`src/types/index.ts`) `api_name` เป็น `VarChar` รูปแบบอิสระ: คลังศัพท์ที่ valid เป็นข้อมูลปลายเปิด ขยายทุกครั้งที่การเรียก `AppIdGuard('...')` ตัวใหม่ลงใน backend gateway และ catalog ถูก regenerate — ไม่มีการเปลี่ยน schema เข้ามาเกี่ยวข้อง โหมดของ grant เป็น boolean ธรรมดา `allow_all` ไม่ใช่ enum ของโหมด คอลัมน์ `device` ก็เป็น `VarChar` รูปแบบอิสระเช่นกัน (default `"web"`) **ไม่ใช่** enum ของ DB: ฐานข้อมูลรับ string ใด ๆ ก็ได้ ขณะที่ SPA จำกัดค่าไว้ที่ชุดคงที่ `mobile` / `web` / `desktop` / `pos` ผ่าน union `DeviceType` และ `DEVICE_OPTIONS`

## 5. ความแตกต่างจาก shape ของ carmen-backstage SPA

type ของ SPA อยู่ใน `../carmen-backstage/src/types/index.ts` (`Application`, `ApplicationWritePayload`, `ApiCatalogGroup`); ชั้นการแปลคือ `src/services/applicationService.ts` model การอ่านและการเขียนจงใจ**ไม่สมมาตร**:

| Shape ของ SPA | แหล่งที่มาใน SPA | การจัดเก็บใน Prisma | หมายเหตุ |
| --------- | ---------- | -------------- | ----- |
| `Application.api_names: string[]` (แบน) | `Application` | join row ใน `tb_application_api` | API flatten grant row เป็น key string; SPA ไม่เคยเห็น id ของ grant-row |
| `Application.status*`, `bypass_users[]` (เฉพาะ detail), `has_secret`, `require_secret`, `secret_last4`, `secret_rotated_*`, `secret_previous_expires_at` | `Application` | คอลัมน์สถานะ/secret ข้างบน | ฟิลด์ secret เป็น read model ที่ derive: `has_secret` = มี `secret_last4`; plaintext และ ciphertext ไม่ออกจาก micro-cluster ยกเว้นผ่าน endpoint reveal/rotate ทั้งหมดเป็น optional ใน type เพราะ backend เก่าไม่ส่งมา |
| การเขียนสถานะ, bypass และ secret | `updateStatus`, `setBypassUsers`, `rotateSecret`, `revealSecret`, `setSecretEnforcement` | คอลัมน์เดียวกัน / `tb_application_bypass_user` | **ไม่เป็นส่วนของ payload `PUT`** — แต่ละอันมี endpoint ของตัวเอง (§6) ดังนั้นการ save ฟอร์มจะไม่มีทางทำให้ application ล่มหรือเปลี่ยน secret เป็นผลข้างเคียง `toWritePayload` ตัด `is_active` ออกด้วยเหตุผลนี้ |
| `ApplicationWritePayload.details: { add: { api_name }[] }` | `toWritePayload` ใน `applicationService.ts` | join row เดียวกัน | การเขียนห่อแต่ละ key เป็น `{ api_name }` ใต้ `details.add`; รายการถูก trim และตัวที่ว่างถูกทิ้ง **`details` ถูกละเว้นทั้งหมดเมื่อ `allow_all` เป็น true** |
| `PUT` = **semantics แบบ replace** | `applicationService.update` | n/a | การ save ทุกครั้งส่งชุดที่ต้องการแบบเต็มใน `details.add` — เทียบกับ role ของ RBAC ซึ่ง `PUT` ส่ง delta `{ add, remove }` อย่า port รูปแบบ delta มาที่นี่ (หรือกลับกัน) |
| chip "App ID" บนหน้าจอ edit | `ApplicationIdentityHero.tsx` (ย้ายออกจากตัวฟอร์มตั้งแต่ sync ก่อนหน้า — ไม่ใช่ field row ของการ์ด Settings อีกต่อไป) | ไม่ใช่คอลัมน์ | เป็น label สำหรับแสดง `id` ของเรคคอร์ด; ไม่มีคอลัมน์ `app_id` และไม่มี field ใน DTO |
| การ round-trip ของ `doc_version` | payload `ApplicationFormData`, `getDocVersion`/`isVersionConflict` | `tb_application.doc_version` | ใหม่ตั้งแต่ sync ก่อนหน้า — ตรงกันทั้งสองฝั่ง ไม่ใช่ความแตกต่าง; ระบุไว้เพื่อความครบถ้วนเนื่องจากเกิดขึ้นหลังการเปรียบเทียบครั้งแรก |
| `ApiCatalogGroup { module, api_names[] }` | `getApiCatalog` | **ไม่มีตาราง** | catalog คือ `app-api-catalog.generated.ts` ใน backend-gateway, emit จากการสแกน `AppIdGuard` (§5.1) |
| ความทนทานต่อ envelope ของ catalog | `getApiCatalog` | n/a | endpoint คืน `{ api_names: string[], groups?: ApiCatalogGroup[] }` ซึ่งอาจอยู่ใน envelope `{ data }` มาตรฐาน; service ยังรองรับ `string[]` เปล่า ๆ ด้วย เมื่อ `groups` หายไปหรือไม่ผ่าน runtime guard รายตัว client จะ derive กลุ่มที่เหมือนกันทุกประการผ่าน `groupApiNames()` (`src/utils/apiCatalog.ts`: module = prefix ก่อน `.` ตัวแรก; ชื่อที่ไม่มีจุดเป็นโมดูลของตัวเอง; `actionOf()` = ข้อความหลังจุดแรก) — กฎการแบ่งเดียวกับ generator ฝั่ง backend ดังนั้นผลลัพธ์ของ fallback เท่ากับผลลัพธ์ของ server |
| Shape ของ audit อ่านผ่าน `normalizeAudit()`/`auditColumns()` | `ApplicationManagement.tsx` (ตั้งแต่ `a85a166`, 2026-08-22 — นี่คือหนึ่งใน 5 ตารางหน้า Management ที่ย้ายออกจาก `fmt()` ของตัวเอง) | คอลัมน์ audit id | `normalizeAudit()` ลอง shape แบบ **nested** (`audit.created`/`audit.updated`) ก่อน แล้วถอยไปใช้คอลัมน์แบบ **flat** (`created_at`/`created_by_name`) เฉพาะเมื่อ nested ไม่มี — ไม่ใช่ทางกลับกัน actor ของ `updated` จะแสดงเฉพาะเมื่อ `everEdited` (มีชื่อ actor หรือ `at` ต่างจาก `created.at`) ไม่ใช่การเทียบ `updated_at === created_at` |
| `ApplicationSummaryData` (แถบ Registry) | `getRegistrySummary` → `GET /api-system/applications/summary` | n/a — query aggregate สด ไม่ใช่ตาราง | จำนวนที่ไม่กรอง ทั้งทะเบียน: `total`/`active`/`inactive`/`full_access`/`scoped`/`devices[]` บวก object `statuses` (จำนวนต่อสถานะ) และ `secrets` (`enforced` / `unenforced` / `none`) ที่ไม่บังคับ ซึ่งแถบ render เป็นส่วนเพิ่มเมื่อมี และจำนวน `deleted` (soft-deleted ทั้งทะเบียน) ที่**อยู่บน wire แต่ไม่ถูก render**โดย `ApplicationRegistrySummary` ในตอนนี้ แทนที่การกวาดฝั่ง client ด้วย `perpage: -1` เมื่อ 2026-08-24 (`99a93c8`, หนึ่งใน 5 หน้าที่ย้ายวันเดียวกัน) |
| API reach (`reachOf()`) | `utils/apiReach.ts`, เรียกโดย `ApplicationReachCell` (list) และ `ApplicationIdentityHero` (edit) | n/a — คำนวณฝั่ง client จาก catalog ที่โหลดมา | ไม่ใช่ข้อมูลที่เก็บไว้: `granted`/`anchored`/`full`/`modules`/`percent` ถูก derive ทุกครั้งที่ render จาก `allow_all`, `api_names` และขนาด catalog ที่ fetch แยกต่างหาก (`getApiCatalog()`) ฟังก์ชันเดียวป้อนทั้งสองหน้าจอเพื่อไม่ให้ list กับหน้ารายละเอียดขัดแย้งกันว่าอะไรคือ "full access" |

### 5.1 endpoint ของ catalog และ generator

`GET /api-system/applications/api-catalog` เสิร์ฟเนื้อหาของ `apps/backend-gateway/src/backstage/applications/app-api-catalog.generated.ts` ซึ่ง `scripts/generate-app-api-catalog/run.ts` ผลิตขึ้นโดยสแกนทุกไฟล์ `.ts` ใต้ source ของ gateway หาการเรียก `new AppIdGuard('<api_name>')` (match ด้วย regex), de-duplicate, เรียงลำดับ และจัดกลุ่มตามโมดูล ไฟล์ export ทั้ง `APP_API_CATALOG` แบบแบนและ `APP_API_CATALOG_GROUPS` ห้ามแก้ไขด้วยมือเด็ดขาด — regenerate ด้วย `bun run scripts/generate-app-api-catalog/run.ts` หลังเพิ่ม guard

### 5.2 มีเฉพาะใน schema: ตระกูล `tb_application_role`

platform schema ยังมี `tb_application_role` (บรรทัด 19), `tb_application_role_tb_permission` (บรรทัด 44) และ `tb_user_tb_application_role` (บรรทัด 805) แม้จะมี prefix ว่า `application` พวกมัน**ไม่ใช่ส่วนหนึ่งของแบบจำลอง machine-client ของโมดูลนี้**: พวกมันอธิบายชุด role ที่ scope ระดับ business unit (`tb_application_role.business_unit_id` → `tb_business_unit`) ที่ join row ของ `tb_permission` เข้ากับผู้ใช้ — คลังศัพท์ RBAC ภายในผลิตภัณฑ์สำหรับ application ฝั่ง inventory ไม่ใช่ grant สำหรับ caller ที่ใช้ `x-app-id` Platform SPA **ไม่มี surface สำหรับพวกมัน** — ไม่มีหน้า, service หรือ type ใดอ้างอิงถึงพวกมัน ยืนยันอีกครั้งเมื่อ 2026-07-29 — จึง document ไว้ที่นี่เพียงเพื่อแก้ความกำกวมของการตั้งชื่อ; ยังไม่จำเป็นต้องมีตาราง field จนกว่าจะมี UI (หมายเหตุ: catalog `api_name` ที่ generate ขึ้นมี endpoint ที่ถูก guard `application-role.*`/`application-role-permission.*`/`application-permission.*` อยู่ด้วย — เป็น route ของ backend-gateway ที่ไม่มี client ใน SPA นี้ เป็นข้อสังเกตแยกต่างหากจากตารางที่มีเฉพาะใน schema ข้างบน อย่าสับสนสองเรื่องนี้เข้าด้วยกัน)

## 6. แหล่งข้อมูลอ้างอิง

REST surface ที่ `applicationService.ts` ใช้:

| Method + Path | วัตถุประสงค์ | หมายเหตุ |
|---|---|---|
| `GET /api-system/applications` | List | แบ่งหน้า; field ค้นหา `name`, `description`; filter `advance` บน `status: { in: [...] }` และ `device`; row อาจมี `audit` ซ้อนอยู่ |
| `PATCH /api-system/applications/:id/status` | เปลี่ยนสถานะบริการ | Body `{ status, status_message?, status_until?, doc_version? }`; `409 APP_SELF_LOCK` ถ้าเป้าหมายคือ app ของผู้เรียกเองและ `status` ไม่ใช่ `running`; permission `application.update` |
| `PUT /api-system/applications/:id/bypass-users` | แทนที่รายการ bypass | Body `{ user_ids }`; semantics แบบ replace; `application.update` |
| `POST /api-system/applications/:id/secret/rotate` | Generate / rotate secret | คืน plaintext ใหม่ครั้งเดียว; ตัวเดิมยังใช้ได้ 24 ชม.; `application.secret.manage` |
| `GET /api-system/applications/:id/secret` | Reveal secret | `404` เมื่อไม่มี; ทุกการ reveal ถูกบันทึก audit; `application.secret.reveal` |
| `PATCH /api-system/applications/:id/secret/enforcement` | เปิด/ปิด `require_secret` | Body `{ require_secret, doc_version? }`; `400 APP_SECRET_MISSING`, `409 APP_SECRET_SELF_LOCK`; `application.secret.manage` |
| `POST /api-system/applications` | สร้าง | `details.add` มีอยู่เฉพาะเมื่อ `allow_all` เป็น false |
| `GET /api-system/applications/:id` | Detail | คืน `api_names: string[]` แบบแบน |
| `PUT /api-system/applications/:id` | อัพเดท | **Semantics แบบ replace** — ชุดที่ต้องการแบบเต็มใน `details.add` |
| `DELETE /api-system/applications/:id` | ลบ | เข้าถึงได้จาก dropdown ของ row ในหน้า list เท่านั้น |
| `GET /api-system/applications/api-catalog` | catalog ของ `api_name` ที่เลือกได้ | `{ api_names, groups? }`, ทนทานต่อ envelope; มี fallback การจัดกลุ่มฝั่ง client |
| `GET /api-system/applications/summary` | Aggregate สำหรับแถบ Registry ของหน้า list | ไม่กรอง — อธิบายทั้งทะเบียน ไม่ใช่มุมมอง search/advance ปัจจุบัน; ไม่มี block `paginate` ใหม่ตั้งแต่ sync ก่อนหน้า (ก่อน 2026-08-24 เป็นการกวาดฝั่ง client ด้วย `perpage: -1`) |

การอ้างอิง commit/PR ข้ามฝั่งด้านบนทั้งหมดอยู่ใน `../carmen-turborepo-backend` หรือ `../carmen-backstage` ตามที่ระบุไว้แล้วตรงจุดอ้างอิงแต่ละแห่ง; ส่วนข้างล่างนี้แยก primary/secondary สำหรับรายการอ้างอิงของหน้านี้เอง

**หลัก (source of truth):**
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma` — `tb_application` (บรรทัด 65), `tb_application_bypass_user` (บรรทัด 112), `tb_application_api` (บรรทัด 126); ตระกูลที่มีเฉพาะใน schema ที่บรรทัด 19, 44, 805 อ่านซ้ำ 2026-10-27 ที่ origin/main: คอลัมน์สถานะ คอลัมน์ secret และตาราง bypass เป็นของใหม่ตั้งแต่การอ่านเมื่อ 2026-09-05
- `../carmen-turborepo-backend/scripts/generate-app-api-catalog/run.ts` — generator ของ catalog (การสแกน `AppIdGuard`, กฎการจัดกลุ่ม, path ของ output)
- `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/applications/app-api-catalog.generated.ts` — catalog ที่ generate จริง: 1,140 key `api_name` ใน 181 กลุ่มโมดูล ตามที่นับเมื่อ 2026-10-27 (เดิม 900/148 เมื่อ 2026-09-05)

**รอง (shape ฝั่ง consumer):**
- `../carmen-backstage/src/types/index.ts` — `Application` (รวม `doc_version?: number`), `ApplicationWritePayload`, `ApiCatalogGroup`, `ApplicationSummaryData`, `DeviceCount`
- `../carmen-backstage/src/services/applicationService.ts` — `toWritePayload` (รวม `doc_version`), การจัดการ envelope ของ `getApiCatalog` และ fallback การจัดกลุ่ม, `getRegistrySummary()`
- `../carmen-backstage/src/utils/apiCatalog.ts` — `moduleOf`, `actionOf`, `groupApiNames` บวก (ใหม่) `verbOf`/`isAuthorityAction`/`countAuthority`
- `../carmen-backstage/src/utils/apiReach.ts` — `reachOf()` ฟังก์ชันคำนวณรัศมีตัวเดียวที่ `ApplicationReachCell` (list) และ `ApplicationIdentityHero` (edit) ใช้ร่วมกัน
- `../carmen-backstage/src/utils/audit.ts` — `normalizeAudit()` (ลอง nested ก่อน flat เป็นทางถอย; `updated` ถูกกำหนดด้วย `everEdited`) ที่ list ของโมดูลนี้ใช้ตั้งแต่ 2026-08-22
- `../carmen-backstage/src/utils/docVersion.ts` — helper optimistic-lock `getDocVersion`/`isVersionConflict`/`notifyVersionConflict` ที่ `ApplicationEdit.tsx` ใช้

**Cross-link:** [หน้า landing ของ Applications](/th/backstage/applications) &nbsp;·&nbsp; [UI Screens](/th/backstage/applications/ui-screens) &nbsp;·&nbsp; [Permissions](/th/backstage/applications/permissions) &nbsp;·&nbsp; [Backstage Roles data-model](/th/backstage/rbac/data-model) (จุดเทียบของการเขียนแบบ delta)
