---
title: หน่วยธุรกิจ — Tenant Migrations
description: หน้าจอ standalone ระดับ fleet (/tenant-migrations) ที่ตรวจสอบและ apply schema migration ของฐานข้อมูล tenant ที่ค้างอยู่ทั่วทุก business unit — reuse cluster.read ที่ระดับ route แต่ทุก action จริงถูก gate เพิ่มเป็น super-admin เท่านั้น
published: true
date: 2026-07-29T09:46:00.000Z
tags: book/platform, business-units, tenant-migrations
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# หน่วยธุรกิจ — Tenant Migrations

> **At a Glance**
> **หน้าจอ:** `TenantMigrationManagement` (`/tenant-migrations`, เพิ่มเมื่อ 2026-06-30) &nbsp;·&nbsp; **Route gate:** `cluster.read` (reuse key เดียวกับ [Business Units](/th/platform/business-units)) &nbsp;·&nbsp; **Action gate:** ทุก action Check/Apply/Deploy ถูกจำกัดเพิ่มเป็น `isSuperAdmin` — ทั้งฝั่ง client และที่ backend guard &nbsp;·&nbsp; **Sidebar:** รายการ "Tenant Migrations" ในกลุ่ม Organization &nbsp;·&nbsp; **ความสัมพันธ์:** มุมมองรายการระดับ fleet ของ action เดียวกับที่การ์ด `TenantMigrationCard` ต่อ BU บน [Business Units — UI Screens](/th/platform/business-units/ui-screens) §4.13 ทำทีละ BU

## 1. ภาพรวม

Tenant Migrations เป็นหน้า standalone ไม่ใช่ sub-route ของ Business Units — แต่ทำงานกับ object โดเมนเดียวกันทุกประการ (ทุกแถว `business_unit` ที่ active) และความสามารถ backend เดียวกับการ์ด **Tenant Migrations** ที่บันทึกไว้แล้วบน[หน้าแก้ไข Business Units](/th/platform/business-units/ui-screens) §4.13 การ์ดนั้นตรวจสอบและ apply migration ให้กับ BU หนึ่งตัวที่กำลังแก้ไขอยู่ ส่วนหน้านี้ (`TenantMigrationManagement.tsx` เข้าถึงจากกลุ่ม Organization ใน sidebar ไม่ใช่จากหน้าจอ Business Units ใด ๆ) แสดงรายชื่อ business unit **ทั้งหมด** ในตารางเดียว ให้ operator ตรวจสอบ apply หรือ deploy แบบ batch ได้ทั่วทั้ง fleet จากมุมมองเดียว

หน้านี้โหลดรายการแถวจาก endpoint `businessUnitService.getAll()` ปกติ (endpoint เดียวกับที่หน้ารายการ Business Units ใช้) ดังนั้น **การเข้าถึงหน้านี้และเห็นตาราง BU ต้องมีแค่ `cluster.read`** — pattern การ reuse route เดียวกับที่ Business Units ใช้กับสาม route ของตัวเอง (ดู [Business Units — บทบาทและ Persona](/th/platform/business-units) §4) แต่ทุก operation ของ migration จริง ๆ เป็นอีกเรื่องหนึ่ง: ทั้ง frontend และ backend จำกัด Check/Apply/Deploy-all ไว้ให้เฉพาะ session ระดับ super-admin เท่านั้น (§3) การแบ่งนี้ — สิทธิ์อ่านกว้างสำหรับรายการ สิทธิ์เขียนแคบสำหรับ action — คล้ายกับการ gate ของการ์ดต่อ BU เอง (§4.13 ที่นั่นระบุว่า "ทุกคนที่แก้ไขได้เห็นการ์ด action ถูก gate ด้วย super-admin") ต่างกันตรงที่ที่นี่แม้แต่ **การตรวจสอบสถานะแบบอ่านอย่างเดียว** ก็อยู่ในข้อจำกัดนี้ด้วย เพราะต่างจากหน้าแก้ไข BU (ที่แสดงการ์ดสำหรับ BU เดียวที่ scope ด้วย `cluster.update` อยู่แล้ว) จุดประสงค์ทั้งหมดของหน้านี้คือสถานะ migration ระดับ fleet ซึ่ง backend ถือเป็นความสามารถเดียวที่สงวนไว้สำหรับ super-admin เท่านั้น ไม่ว่าจะถามถึง BU ไหนก็ตาม

## 2. Layout ของหน้าจอ

- **Header** — `PageHeader` หัวข้อ "Tenant migrations" คำบรรยาย "Check which tenant databases are behind on schema migrations, and roll them out."
- **การ์ดสรุป Fleet Sync** (`FleetSync`) — การ์ดแนวนอนแสดง `{จำนวนที่ in-sync} / {BU ทั้งหมด}` ด้วยตัวเลขขนาดใหญ่แบบ monospace, progress bar สามสี (เขียว/เหลือง/แดง) สำหรับ in-sync/behind/errored และแถว legend พร้อมจำนวนรวมของ migration ที่ค้างทั่วทุก tenant ที่ behind ก่อนรัน "Check all" ครั้งแรกจะแสดง "Not checked yet" แทน bar ช่อง action ทางขวาของการ์ดมีปุ่ม **Check all**, **Deploy all**, และ **Export**
- **Deploy Console** (`DeployConsole`) — render เฉพาะตอนที่ batch "Deploy all" กำลังทำงาน: panel รูปแบบ terminal สีเข้ม พร้อม progress bar (applied/total ของ BU ที่กำลัง migrate), code ของ BU ปัจจุบัน และ log แบบ scroll ที่มีสี ต่อ BU ที่เสร็จแล้ว (เขียวสำหรับ applied/up-to-date, แดงสำหรับ failed)
- **ช่องค้นหา** — filter ฝั่ง client เหนือตาราง BU (code/name) โฟกัสได้ผ่าน global search shortcut
- **ตาราง BU** (`DataTable`, 3 คอลัมน์ sticky ซ้าย) — คอลัมน์: **Code** (ลิงก์ไป `/business-units/:id/edit`), **Name**, **Status** (badge — "In sync" / "N behind" / "Error" / "Not checked" บวกบรรทัด inline "Applying X/Y … ชื่อ migration ปัจจุบัน" ระหว่างที่ Apply ต่อแถวกำลัง stream หรือ error message inline), **Pending** (จำนวน), **Last checked** (HH:MM:SS ตามเวลา client) และคอลัมน์ row-actions (ไอคอน **Check** และ **Apply** ที่แสดงเฉพาะเมื่อแถวนั้นมี migration ค้างอยู่)
- **Empty state** — "No business units" พร้อมปุ่ม "Go to Business Units" แสดงเมื่อ fleet มี BU เป็นศูนย์ (ไม่ใช่ migration ค้างเป็นศูนย์)
- `DevDebugSheet` (dev เท่านั้น) แสดง response ดิบของ `GET /api-system/business-units`

หากรายการ BU ถูก paginate ฝั่ง server เกินกว่าที่ fetch เดียว (`perpage: 1000`) จะคืนมา จะมี banner เตือน "Showing N of M business units. Increase the page size to see all." — หน้านี้ไม่ paginate ต่อเพื่อดึงส่วนที่เหลือเอง

## 3. Action และการ Gate

| Action | Trigger ของ UI | เรียก Backend | Gate |
|---|---|---|---|
| แสดงรายการ business unit | โหลดหน้า | `businessUnitService.getAll({ perpage: 1000, sort: 'code:asc' })` | `cluster.read` (เหมือน [รายการ Business Units](/th/platform/business-units/ui-screens)) |
| Check (แถวเดียว) | ไอคอน row action | `GET /api-system/tenant/migrations/:bu_id/status` | Backend: bearer token ระดับ super-admin หรือ `x-deploy-token` ที่ตรงกัน Frontend: ปุ่มถูก disable พร้อม tooltip "Super-admin required." เมื่อ `!isSuperAdmin` |
| Check all | ปุ่มบนการ์ด Fleet Sync | เรียก `GET .../status` ต่อ BU จำกัด concurrency ที่ 4 พร้อมกัน (`mapWithConcurrency`) | เหมือน Check |
| Apply (แถวเดียว) | ไอคอน Apply ต่อแถว → confirm dialog | `POST /api-system/tenant/migrations/:bu_id/deploy/stream` (NDJSON progress) | เหมือน Check |
| Deploy all | ปุ่มบนการ์ด Fleet Sync → confirm dialog | `POST /api-system/tenant/migrations/all/deploy/stream` (NDJSON progress ทีละ BU ฝั่ง server) | เหมือน Check |
| Export | ปุ่มบนการ์ด Fleet Sync | CSV ฝั่ง client จาก code/name/status/pending/last-checked ของ state ที่โหลดไว้แล้ว | ไม่มี — export สิ่งที่ตารางแสดงอยู่ปัจจุบัน |

ทุก endpoint ระดับ migration ข้างต้นอยู่หลัง `TenantMigrationGuard` ของ backend (`../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/tenant-migration.guard.ts`) ซึ่งต้องการ **หนึ่งใน**: session Keycloak ระดับ super-admin หรือ header `x-deploy-token` ที่ตรงกัน (deploy credential สำหรับ CI/CD เปรียบเทียบด้วย `timingSafeEqual`) — ไม่มี path ผ่าน `cluster.*` หรือ RBAC permission อื่นใดเข้าถึงได้เลย ทั้ง controller ยังปิดได้ทั้งหมดด้วย feature flag `TENANT_MIGRATION_API_ENABLED` ซึ่งเมื่อปิด ทุกการเรียก (รวมถึง status check) จะ 403 ด้วย "Tenant migration API is disabled" ไม่ว่าใครจะเรียกก็ตาม ค่า `disabledReason = !isSuperAdmin ? 'Super-admin required.' : null` ของ frontend จึงเป็นความสะดวกฝั่ง UI ที่ตรงกับ (ไม่ใช่แทนที่) การตรวจสอบจริงฝั่ง server — ต่างจากช่องว่างที่ยืนยันแล้วของ [SQL Workbench](/th/platform/sql-workbench) และ [Query Dataset](/th/inventory/system-config/query-dataset) guard ของ tenant-migrations ฝั่ง backend ไม่สามารถถูก bypass ได้ด้วยการเรียก API ตรง ๆ จาก session ที่ไม่ใช่ super-admin

## 4. ความสัมพันธ์กับหน้าแก้ไข Business Units

- การ์ด `TenantMigrationCard` ต่อ BU บน [Business Units — UI Screens](/th/platform/business-units/ui-screens) §4.13 และหน้านี้เรียก `tenantMigrationService` (`getStatus`, `deployStream`, `deployAllStream`) และ backend controller **เดียวกัน** — มี implementation ของ "ตรวจสอบสถานะ" และ "apply migration" เพียงชุดเดียว ที่แสดงผลจากสองหน้าจอ
- **ไม่มีลิงก์ในแอป** จากหน้าแก้ไข Business Units ไปยังหน้า fleet-wide นี้ หรือย้อนกลับ — อ่านตรงจาก source ของทั้งสอง component ทางเดียวที่จะมาหน้านี้คือรายการ sidebar "Tenant Migrations" (กลุ่ม Organization) หรือพิมพ์ URL เอง หน้าแก้ไข BU เองไม่มีปุ่ม "ดูใน fleet list" และลิงก์ "Code" ต่อแถวของหน้านี้ก็พาไปหน้าแก้ไข BU นั้นตรง ๆ ไม่ใช่เวอร์ชัน filter ของตัวเอง
- การ stream deploy จากหน้าจอไหนก็ตามเป็นแบบ fire-and-forget อย่างแท้จริงเมื่อเริ่มแล้ว: `AbortController` ของ frontend ตอน unmount/navigate away หยุดแค่ **browser** จากการรอ stream NDJSON — comment ในโค้ดของ `tenantMigrationService.ts` และ source ของหน้านี้เองระบุชัดว่า `runBuStream`/`deployAllStream` ฝั่ง backend ถูกออกแบบให้ **ไม่** ถูกยกเลิกเมื่อ client disconnect ดังนั้น migration ที่กำลังรันอยู่จะทำงานต่อจนเสร็จ (หรือจนถึง timeout ของ `spawnPrisma` เอง) แม้ operator จะออกจากหน้าไปกลางทาง ไม่มี endpoint cancel/rollback สำหรับโดเมนนี้

## 5. ช่องว่างและ Edge Case ที่ทราบแล้ว

- **`POST :bu_id/resolve` ไม่มีผู้เรียกฝั่ง frontend ใน carmen-platform เลย** backend มี endpoint จริง (`tenant-migrations.controller.ts` `resolve()`) สำหรับทำเครื่องหมาย migration ที่ค้าง/ล้มเหลวว่า `applied` หรือ `rolled-back` ตามชื่อ — ยืนยันจากการอ่าน source ตรงของ `tenantMigrationService.ts`, `TenantMigrationManagement.tsx`, และ `TenantMigrationCard.tsx` ไม่มีไฟล์ใดอ้างอิงถึง `resolve` เลย operator ที่เจอ migration ค้าง (comment ของ Swagger ใน controller เองระบุ `409` "A migration operation is already running") ไม่มี path ผ่าน UI ในการแก้ไข ต้องเรียกตรง (เช่นผ่าน Bruno)
- **Deploy-all กันได้แค่ BU *ถัดไป* ไม่ใช่ตัวที่กำลังทำอยู่** comment ฝั่ง backend ของ batch stream เอง (`tenant_migration.service.ts:504-518`) ระบุว่าการยกเลิกหยุดแค่ batch จากการเริ่ม tenant ถัดไป — BU ที่กำลัง migrate อยู่ตอน disconnect จะทำงานต่อจนเสร็จไม่ว่าจะเกิดอะไรขึ้น
- **flag `TENANT_MIGRATION_API_ENABLED` เป็นระดับ fleet และ all-or-nothing** — ไม่มี toggle ต่อ BU หรือต่อ environment ที่มองเห็นได้จากหน้านี้ เมื่อปิด ทุกแถว Check/Apply จะ fail เหมือนกันด้วย "Tenant migration API is disabled" ซึ่ง error text ต่อแถวของหน้านี้จะแสดงตามนั้น ไม่ได้แยกเป็น state "flag ปิด" ที่แยกแยะได้
- **UI ไม่มีการบ่งชี้ path ของ deploy-token** backend รับ header `x-deploy-token` เป็นทางเลือกแทน session super-admin (ออกแบบสำหรับ CI/CD) แต่หน้าจอ SPA นี้ authenticate ในฐานะ operator ที่ signed-in เท่านั้นเสมอ — path ของ token ไม่ใช่สิ่งที่หน้านี้ใช้หรือแสดง

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/pages/TenantMigrationManagement.tsx`, `src/pages/tenantMigration/{FleetSync,DeployConsole}.tsx` — หน้า standalone, การ์ดสรุป และ console สำหรับ batch-deploy
- `../carmen-platform/src/services/tenantMigrationService.ts` — `getStatus`, `deployStream`, `deployAllStream`, และ doc comment เรื่อง semantics ของการ abort stream
- `../carmen-platform/src/components/TenantMigrationCard.tsx` — การ์ดต่อ BU ที่บันทึกไว้ใน [Business Units — UI Screens](/th/platform/business-units/ui-screens) §4.13 ใช้ service เดียวกัน
- `../carmen-platform/src/App.tsx:145` — route `/tenant-migrations` (`requiredPermission="cluster.read"`); `src/components/Layout.tsx:55` — รายการ sidebar
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/tenant-migrations/tenant-migrations.controller.ts` — endpoint `status`, `deploy`, `deploy/stream`, `resolve`
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/tenant-migration.guard.ts` — guard super-admin-หรือ-deploy-token ที่ใช้กับทั้ง controller; feature flag `envConfig.TENANT_MIGRATION_API_ENABLED`
- `../carmen-turborepo-backend-bruno/collections/carmen-inventory/platform/tenant-migrations/` — request Bruno สำหรับ `status`, `deploy`, `deploy-stream`, `resolve`
- [Business Units](/th/platform/business-units) และ [Business Units — UI Screens](/th/platform/business-units/ui-screens) §4.13 — การ์ดต่อ BU และ gotcha การ reuse key `cluster.*` ที่หน้านี้สืบทอดมา
