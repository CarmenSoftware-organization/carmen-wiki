---
title: การย้ายเทแนนต์ — โมเดลข้อมูล (Data Model)
description: ไม่มี entity สถานะ migration ที่ persist — ทุกสถานะบนหน้าจอนี้ถูก derive สด ๆ จาก tb_business_unit.db_schema บวกแถว tb_database_pool ที่ผูกไว้ ด้วยการเรียก Prisma CLI ไปยัง tenant connection ที่ resolve แล้ว และ parse text output ของมัน
published: true
date: '2026-09-06T19:00:00.000Z'
tags: book/platform, tenant-migrations, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# การย้ายเทแนนต์ — โมเดลข้อมูล (Data Model)

> **At a Glance**
> **ไม่มีตารางเฉพาะ** ไม่มีสิ่งใดใน `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` ที่ track สถานะ, การรัน, หรือประวัติของ migration เลย — ทุกสถานะที่โมดูลนี้แสดงคำนวณสดตอนขอ โดยการรัน Prisma CLI กับฐานข้อมูล tenant เป้าหมายแล้ว parse text output ของมัน (§2) &nbsp;·&nbsp; **การ resolve connection** อ่านสองตารางที่มีอยู่แล้ว ไม่ใช่ตารางเฉพาะ migration: `tb_business_unit.db_schema` บวกแถว `tb_database_pool` ที่ผูกไว้ (host/port/database/username/รหัสผ่านที่ถอดรหัสแล้ว) (§3) &nbsp;·&nbsp; **บัญชีว่า migration ไหน apply ไปแล้วหรือยังอยู่ในตาราง `_prisma_migrations` ของ Prisma เอง ภายใน tenant schema แต่ละตัว** — ไม่ได้อยู่ในฐานข้อมูลแพลตฟอร์มที่ wiki เล่มนี้บันทึกไว้ที่อื่น และ codebase นี้ไม่ query มันตรง ๆ นอกจากผ่าน CLI `prisma migrate` เอง &nbsp;·&nbsp; **ไม่มี optimistic lock ไม่มีประวัติการรันที่ persist** — concurrency ถูกบังคับด้วย in-memory `Set`/boolean flag เท่านั้น ซึ่งหายไปทุกครั้งที่ process restart (§5)

> **แหล่งข้อมูลอ้างอิง:** อ่านสิ่งเหล่านี้ก่อนอัปเดตหน้านี้
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_business_unit` (บรรทัด 176), `tb_database_pool` (บรรทัด 1382)
> - `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/tenant_migration/tenant_migration.service.ts` — `resolveConnection()`, `status()`, `deployResolved()`, `runBuStream()`, `deployAllStream()`, `resolve()`
> - `../carmen-turborepo-backend-v2/apps/micro-business/src/tenant/tenant.service.ts` — `resolveConnectionForBusinessUnit()`
> - `../carmen-turborepo-backend-v2/packages/db-connection-utils/src/tenant-url.ts` — `resolveTenantUrl()`, `buildTenantUrl()`
>
> ยืนยันกับ `carmen-turborepo-backend-v2` HEAD `937cf5ac4` (2026-09-06) และ `carmen-platform` HEAD `157a65e` (2026-09-04)

## 1. ภาพรวม

นี่คือโมดูลเดียวในเล่ม Platform ที่ "data model" ส่วนใหญ่เป็นคำตอบของคำถามว่า *อะไรที่ไม่มีอยู่* ไม่มีตาราง `tb_tenant_migration` ไม่มี run log ไม่มี column "สถานะ migration ล่าสุด" ต่อ BU เลย — ทั้งหน้าจอนี้ (และการ์ด `TenantMigrationCard` ต่อ BU, [Business Units — UI Screens](/th/platform/business-units/ui-screens) §4.5) ทำงานด้วยการ resolve connection string ของฐานข้อมูล tenant ของ business unit เอง เรียก Prisma CLI ไปยังมัน แล้ว parse สิ่งที่ CLI พิมพ์ออกมา state ที่ persist จริงมีอยู่แค่สองที่ ซึ่งไม่มีที่ไหนเป็นของโมดูลนี้เลย: `tb_business_unit`/`tb_database_pool` ใน schema **แพลตฟอร์ม** (ซึ่งแค่ระบุตำแหน่งฐานข้อมูล tenant) และตาราง `_prisma_migrations` ของ Prisma เอง ภายใน **แต่ละ tenant schema** (ที่ Prisma สร้างและดูแลเอง และ codebase นี้ไม่เคยอ่านหรือเขียนมันตรง ๆ นอกจากผ่าน CLI `prisma migrate`)

## 2. ไม่มี entity เฉพาะ — สถานะถูก derive ไม่ได้ persist

`status(bu_id)` (`tenant_migration.service.ts`) รัน `prisma migrate status --schema <schema>` กับ connection ที่ resolve แล้ว (§3) แล้วจำแนก stdout+stderr ที่รวมกันด้วย regex:

| ฟิลด์ที่ส่งกลับให้ frontend | คำนวณอย่างไร |
|---|---|
| `up_to_date` | `/up to date/i` ตรงกับ output ของ CLI |
| `has_pending` | `/not yet been applied/i` ตรงกับ output ของ CLI |
| `pending` | ทุกคู่ที่ตรง `\d{14}_[a-z0-9_]+` ใน output เดียวกัน ตัดตัวซ้ำ |
| `raw` | output เต็ม โดย connection string `postgres(ql)://...` หรือค่า `DATABASE_URL=...` ถูกลบออก (`sanitize()`) |

ไม่มีอะไรถูกเขียนที่ไหนเลย — call `status` ครั้งถัดไปคำนวณใหม่ตั้งแต่ต้น การเรียก `deploy`/`deployStream` ก็รูปแบบเดียวกัน: รัน `prisma migrate deploy` แล้ว parse บรรทัด `Applying migration \`name\`` เพื่อสร้างรายการ "applied" ที่ stream ไปให้ UI ผลลัพธ์ (สำเร็จ/ล้มเหลว, ชื่อที่ apply แล้ว) ถูกส่งกลับครั้งเดียวและไม่ persist สิ่งเดียวที่จดจำว่า migration ไหน apply ไปแล้วคือตาราง `_prisma_migrations` ของ Prisma เอง ภายใน tenant schema — อยู่นอกขอบเขตของโมดูลนี้ (และ wiki เล่มนี้) นอกจากข้อเท็จจริงที่ว่ามันมีอยู่ และเป็นสิ่งที่ `migrate status`/`migrate deploy`/`migrate resolve` ทั้งหมดอ่านและเขียน

## 3. การ resolve tenant connection: `tb_business_unit` + `tb_database_pool`

`resolveConnection(bu_id)` (`tenant_migration.service.ts`) ค้นหาแถว `tb_business_unit` หนึ่งแถวพร้อม pool ที่ join มา แล้วเรียก `resolveConnectionForBusinessUnit()` (`tenant.service.ts`) ซึ่งจะ throw แทนที่จะคืน connection string เมื่อเงื่อนไขข้อใดข้อหนึ่งต่อไปนี้เป็นจริง:

| เงื่อนไขที่ตรวจ | ข้อความที่ throw (ผ่านการกรองแล้ว ไปถึง frontend ตรง ๆ) |
|---|---|
| `tb_business_unit.database_pool_id` เป็น null → ไม่มี `tb_database_pool` ที่ join ได้ | `Business unit {code} is not linked to a database pool` |
| `tb_business_unit.db_schema` เป็น null | `Business unit {code} has no database schema configured` |
| `tb_database_pool.deleted_at` ที่ join มาถูกตั้งค่า (soft-delete) | `Database pool '{name}' used by business unit {code} has been deleted` |
| `tb_database_pool.is_active` ที่ join มาเป็น false | `Database pool '{name}' used by business unit {code} is inactive` |
| `tb_database_pool.password` ถอดรหัสไม่สำเร็จ (`decryptSecret()`, `@repo/secret-crypto`) | `Failed to decrypt the database pool password (check SECRET_ENCRYPTION_KEY...)` |

ฟิลด์ที่เกี่ยวข้อง, `tb_business_unit` (`schema.prisma:176`):

| ฟิลด์ | ชนิด Prisma | Nullable | บทบาทที่นี่ |
|---|---|---|---|
| `id` | `String @db.Uuid` | ไม่ | พารามิเตอร์ `bu_id` บนทุก endpoint ของโมดูลนี้ |
| `code` | `String @db.VarChar(30)` | ไม่ | ถูกอ้างในทุกข้อความ error และ audit-log entry; ยังเป็นเป้าหมายลิงก์ของแถวกลับไปที่ `/business-units/:id/edit` |
| `database_pool_id` | `String? @db.Uuid` | **ใช่** | FK ไปยัง `tb_database_pool`; null หมายความว่า BU ยังไม่เคยถูกชี้ไปยัง pool |
| `db_schema` | `String? @db.VarChar` | **ใช่** | ชื่อ schema Postgres ของ tenant เองภายใน pool นั้น |
| ความสัมพันธ์ `tb_database_pool` | `tb_database_pool?` | — | `onDelete: NoAction` — แถว pool ไม่เคยถูก cascade-delete; pool ที่มี dependent อยู่ยัง soft-delete ได้ ซึ่งคือกรณี "has been deleted" ข้างต้นพอดี |

ฟิลด์ที่เกี่ยวข้อง, `tb_database_pool` (`schema.prisma:1382`) — เป้าหมาย connection ที่แพลตฟอร์มจัดการร่วมกัน ให้หลาย BU ชี้มาได้:

| ฟิลด์ | ชนิด Prisma | Nullable | บทบาทที่นี่ |
|---|---|---|---|
| `host`, `port`, `database`, `username` | `String`/`Int` | ไม่ | ส่งเข้า `buildTenantUrl()` ตรง ๆ (host/port ผ่านการตรวจสอบ `isSafeHost`/`isSafePort`; ที่เหลือถูก percent-encode) |
| `password` | `String @db.VarChar` | ไม่ | Ciphertext จาก `encryptSecret()`; ถอดรหัสต่อ request โดย `resolveTenantUrl()` ไม่เคยถูกส่งกลับให้ client ใด ๆ |
| `is_active` | `Boolean @default(true)` | ไม่ | ตรวจอย่างชัดเจนใน `resolveConnection()` แม้ความสัมพันธ์จะเป็น to-one — ความสัมพันธ์แบบ to-one ของ Prisma ยังคืนแถวที่ soft-delete/ปิดใช้งานตามปกติ |
| `deleted_at` | `DateTime?` | ใช่ | เครื่องหมาย soft-delete ตรวจแบบเดียวกัน |

URL ที่ได้ (`buildTenantUrl()`, `@repo/db-connection-utils`): `postgresql://{user}:{password}@{host}:{port}/{database}?schema={db_schema}` — เซิร์ฟเวอร์ Postgres หนึ่งตัวโฮสต์ฐานข้อมูลจริงหนึ่งฐานต่อ pool โดยแยกข้อมูล tenant ของแต่ละ BU ด้วย schema ที่มีชื่อของตัวเองภายในนั้นผ่าน query parameter `?schema=` ไม่ใช่ฐานข้อมูลแยกต่อ BU

## 4. Concurrency: in-memory เท่านั้น

`TenantMigrationService` (micro-business) มีฟิลด์สองตัวที่มีอายุแค่ตลอดชีวิตของ process: `runningBuIds: Set<string>` (ทีละ BU) และ `isBatchRunning: boolean` (ทีละ batch ระดับ fleet) ทั้งสองถูกตรวจก่อนที่ `deploy`/`deployStream`/`resolve` จะดำเนินต่อ และคืน `ALREADY_EXISTS` / 409 "already running" เมื่อถูกถืออยู่ ทั้งสองถูกล้างใน `finally` block ทุก path รวมถึงตอน client ตัดการเชื่อมต่อที่ทิ้ง child process `prisma migrate deploy` ให้รันต่อไป (§3.3 บน[หน้าลงจอด](/th/platform/tenant-migrations)) **การ restart process ของ micro-business ล้าง lock ทั้งสองเงียบ ๆ** — หาก child process ของ `prisma migrate deploy` ยังรันข้าม restart ได้จริง (timeout ของตัวเอง `TENANT_MIGRATION_TIMEOUT_MS` ดีฟอลต์ 120000ms ซึ่งปกติจะป้องกันกรณีนี้อยู่แล้ว) จะไม่มีอะไรจดจำว่า lock เคยถูกถืออยู่

## 5. Edge Cases

| สถานการณ์ | สิ่งที่เกิดขึ้นจริง | Source |
|---|---|---|
| BU ยังไม่มี `database_pool_id` หรือ `db_schema` | `resolveConnection` throw "not linked to a database pool" / "has no database schema configured"; บนตาราง fleet จะโผล่เป็น error ต่อแถวตอน Check (ไม่มีการตรวจล่วงหน้าเหมือน `hasDbConnection` ของการ์ดต่อ BU) | `tenant.service.ts` |
| pool ที่ BU ผูกไว้ถูก soft-delete หรือ `is_active: false` | error path เดียวกัน "has been deleted" / "is inactive" — pool ที่ถูก retire ทำให้ migration ของทุก BU ที่ยังชี้มาที่นี่พังเงียบ ๆ จนกว่าจะถูก repoint | `tenant.service.ts` |
| `prisma migrate deploy` ล้มเหลวระหว่าง batch (`/deploy/all/stream`) | BU ที่ล้มเหลวถูกรายงานผ่าน `bu-complete` พร้อม `error`; loop เดินต่อไป BU ถัดไป — migration ที่ค้างจริง ๆ ในตาราง `_prisma_migrations` ของ tenant นั้นถูกทิ้งไว้ตามที่ Prisma CLI ทิ้งไว้เป๊ะ ไม่มีการแก้ไขผ่าน UI เลย (`resolve` ไม่มีผู้เรียกฝั่ง frontend, [หน้าลงจอด](/th/platform/tenant-migrations) §3.3) | `tenant_migration.service.ts:560-586` |
| ความล้มเหลวในการ resolve connection มาถึง `/deploy/stream` | ตกไปยัง mapping ข้อความที่ล้าสมัยของ gateway จนได้ HTTP 500 แทนที่จะเป็น 422 ตามเอกสาร — ตัวข้อความยังถูกต้อง มีแค่ status code ที่ผิด (ยืนยันว่าล้าสมัยตั้งแต่ commit `af2437074`, [หน้าลงจอด](/th/platform/tenant-migrations) §4.4) | `tenant-migrations.controller.ts` |
| `TENANT_MIGRATION_API_ENABLED` ไม่ได้ตั้งค่า | ทุก endpoint 403 รวมถึง `status` — แยกไม่ออกจากปัญหา permission จาก UI นอกจากข้อความตัวอักษรล้วน ๆ | `config.env.ts:222` |

## 6. คำแนะนำ

- **แก้ regex ของ `resolvePreStreamErrorStatus()`** (หรือดีกว่านั้น ให้ `deployStream`/`_streamDeploy` ส่ง `ErrorCode` ต้นทางผ่านไปยัง pre-start error ของ stream แทนการ derive status จาก message text ซ้ำอีกครั้ง) เพื่อให้ความล้มเหลวในการ resolve connection บน stream path คืน 422 เดียวกับที่ endpoint `/deploy` แบบไม่ stream คืนอยู่แล้ว
- **อัปเดต comment `db_connection` ที่ล้าสมัย** ใน `../carmen-platform/src/services/tenantMigrationService.ts` ให้บรรยายกลไก pool/schema เพื่อไม่ให้คนอ่านคนถัดไปไปตามหา column ที่ถูกถอดออกไปหลายเดือนแล้ว
- **ต่อ `resolve()` เข้ากับ UI** แม้จะเป็นแบบขั้นต่ำ (เช่น action สำหรับ super-admin เท่านั้นบนแถวที่อยู่ใน error state อยู่แล้ว) เพื่อไม่ให้ migration ที่ค้างต้องเรียก API ตรง ๆ ถึงจะล้างได้
- **พิจารณาบันทึกผลการรันล่าสุดแบบ persist** (bu id, ชื่อ migration, ผลลัพธ์, timestamp) หากคาดหวังให้หน้าจอนี้ตอบคำถาม "การพยายาม deploy ล่าสุดของ BU X เกิดอะไรขึ้น" ย้อนหลังได้ — ทุกวันนี้คำตอบนั้นมีอยู่แค่ใน application log กับตาราง `_prisma_migrations` ของ tenant เอง

## 7. แหล่งอ้างอิง

- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:176` (`tb_business_unit`), `:1382` (`tb_database_pool`)
- `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/tenant_migration/tenant_migration.service.ts` — `resolveConnection`, `status`, `deploy`, `deployResolved`, `deployStream`, `runBuStream`, `deployAllStream`, `resolve`, `listActiveConnectionsWithSkips`
- `../carmen-turborepo-backend-v2/apps/micro-business/src/tenant/tenant.service.ts` — `resolveConnectionForBusinessUnit`, `BusinessUnitConnectionSource`
- `../carmen-turborepo-backend-v2/packages/db-connection-utils/src/tenant-url.ts` — `buildTenantUrl`, `resolveTenantUrl`
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/tenant-migrations/tenant-migrations.controller.ts` — `resolvePreStreamErrorStatus()`
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/libs/config.env.ts:222` — `TENANT_MIGRATION_API_ENABLED`, `TENANT_DEPLOY_TOKEN`
- [Tenant Migrations](/th/platform/tenant-migrations) — หน้าลงจอดของโมดูลที่ data model นี้รองรับ
