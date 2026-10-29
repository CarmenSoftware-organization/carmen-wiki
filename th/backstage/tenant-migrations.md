---
title: การย้ายเทแนนต์ (Tenant Migrations)
description: หน้าจอระดับ fleet ที่ตรวจและ apply schema migration (กับ dashboard view) ของฐานข้อมูล tenant ทั่วทุก business unit ดูต้องมี tenant_migration.read เปลี่ยนแปลงต้องมี tenant_migration.apply
published: true
date: 2026-10-29T05:30:00.000Z
tags: book/backstage, tenant-migrations
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# การย้ายเทแนนต์ (Tenant Migrations)

> **At a Glance**
> **หน้าจอ:** `TenantMigrationManagement` (+ `FleetSync`, `DeployConsole`) ที่ `/tenant-migrations` เพิ่มโดย `../carmen-backstage` commit `c59bbba` (2026-06-30) &nbsp;·&nbsp; **Route gate:** `tenant_migration.read` (resource ของตัวเองตั้งแต่ 2026-09-29, commit `40f2e61c`; ก่อนหน้านั้น route reuse `cluster.read`) บวก feature flag `tenant_migrations` ของโมดูลนี้บน `PrivateRoute` ตรวจหลัง permission gate &nbsp;·&nbsp; **Action gate:** Check และ Check all ใช้แค่ `tenant_migration.read` ของ route; **Apply, Deploy all, Resolve และ Apply dashboard views** ต้องมี `tenant_migration.apply` ตรวจระดับ Backstage ทั้งระบบ (`clusterId={BACKSTAGE_SCOPED_RECORD}`) — grant ที่มีเฉพาะ cluster ไม่นับ `TenantMigrationGuard` ฝั่ง backend บังคับการแยกเดียวกันต่อ route และยังรับ header `x-deploy-token` ที่ตรงกันเป็นทางเลือกสำหรับ CI &nbsp;·&nbsp; **ใหม่ตั้งแต่ 2026-10-06:** สถานะ **dashboard views** ต่อ BU และ action Apply-views (`/migrations/tenant` ของ micro-data) ที่ gateway ต่อท้ายหลัง Prisma deploy ทุกครั้ง &nbsp;·&nbsp; **ใหม่ตั้งแต่ 2026-09-16 (PRs #296, #297):** คอลัมน์ **Schema** (`db_schema` ของ tenant + ชื่อ pool) และ path **Resolve** ในแอปสำหรับ migration ที่ค้าง (`POST .../:bu_id/resolve`) ทั้งจากตารางนี้และการ์ดต่อ BU — ช่องว่าง "ไม่มีผู้เรียกฝั่ง frontend ของ `resolve`" ที่การแก้ไขรอบ 2026-09-06 ของหน้านี้บันทึกไว้ปิดแล้ว &nbsp;·&nbsp; **Sidebar:** มีรายการ "Tenant Migrations" เป็นของตัวเองในกลุ่ม Organization (`src/components/nav/backstageNav.ts:17`) วาดเป็น sub-row ใต้ Business Units (`parentPath: '/business-units'`) แต่เป็น route และ permission แยกกัน &nbsp;·&nbsp; **สวิตช์ปิด/เปิด:** `TENANT_MIGRATION_API_ENABLED` เป็น env var ที่ **ปิดโดยดีฟอลต์** — ทุก endpoint รวมถึง status check จะ 403 จนกว่าจะตั้งเป็น `true` อย่างชัดเจน &nbsp;·&nbsp; **ความสัมพันธ์:** มุมมองตารางระดับ fleet ของความสามารถ backend เดียวกับที่การ์ด `TenantMigrationCard` ต่อ BU บน [Business Units — UI Screens](/th/backstage/business-units/ui-screens) §4.5 ทำทีละ BU &nbsp;·&nbsp; **e2e suite:** ไม่มี — ทุกข้อความด้านล่างมาจากการอ่าน implementation ไม่ใช่จาก test coverage

![การย้ายเทแนนต์ (Tenant Migrations) screen](/screenshots/platform/tenant-migrations/index.png)

## 1. ภาพรวม

Tenant Migrations คือคอนโซลระดับ fleet ของแพลตฟอร์มสำหรับ Prisma migration ระดับ schema ของ tenant ที่ฐานข้อมูลของทุก business unit ต้องรับไปในที่สุด หน้านี้อยู่ที่ route ระดับบนสุดของตัวเอง `/tenant-migrations` พร้อมรายการ sidebar ของตัวเองในกลุ่ม Organization (แสดงเป็น sub-row ใต้ Business Units ข้าง Tenant Seed Data และ Data Import) — มี route, permission (`tenant_migration.read`) และ feature flag ของตัวเอง แม้รายการแถวจะมาจาก business-unit service เดียวกับที่หน้ารายการ Business Units ใช้ (`fetchAllBusinessUnits({ sort: 'code:asc' })` ซึ่งเดินทีละหน้า หน้าละ 100 สูงสุด 10 หน้า) `TenantMigrationManagement.tsx` แสดงรายชื่อ business unit ทุกตัวที่การเรียกนั้นคืนมาในตารางเดียว ให้ operator ตรวจสอบ apply หรือ deploy แบบ batch migration ที่ค้างได้ทั่วทั้ง fleet จากหน้าจอเดียว — เป็นความสามารถ backend เดียวกับที่การ์ด `TenantMigrationCard` ต่อ BU บน[หน้าแก้ไข Business Units](/th/backstage/business-units/ui-screens) §4.5 ทำทีละ BU (§3.5)

การเข้าถึงหน้านี้ การเห็นตาราง BU และการรัน **Check** ต้องมี `tenant_migration.read` บวก feature flag `tenant_migrations` ของโมดูลนี้เอง สิ่งใดที่เปลี่ยนฐานข้อมูล tenant — Apply, Deploy all, Resolve, Apply dashboard views — ต้องมี `tenant_migration.apply` เพิ่ม: ฝั่ง frontend disable ปุ่มเหล่านั้นพร้อม tooltip "Requires the tenant_migration.apply permission." และ `TenantMigrationGuard` ฝั่ง backend ตรวจ key เดียวกันต่อ route ไม่ว่าฝั่ง frontend จะทำอะไร (§4) ก่อน 2026-09-29 ทั้งหน้าจอจำกัดเฉพาะ super-admin (`isSuperAdmin`); gate นั้นหายไปแล้ว เดิมเนื้อหาของโมดูลนี้เคยอยู่เป็นหน้าย่อยของ Business Units (`business-units/tenant-migrations.md`) — ถูกย้ายมาที่นี่เพราะ `/tenant-migrations` มี route, nav entry, และ feature key (`tenant_migrations`, แยกจาก `business_units`) เป็นของตัวเองมาโดยตลอด — หน้า [Business Units](/th/backstage/business-units) ตอนนี้ลิงก์มาที่นี่สำหรับภาพรวมระดับ fleet และเก็บเฉพาะเรื่องการ์ดต่อ BU ที่ฝังอยู่ไว้บนหน้าย่อยของตัวเอง

## 2. บริบททางธุรกิจ

การ deploy ของ Carmen Blue หนึ่งชุดรัน schema ที่ Prisma จัดการหนึ่งชุดต่อหนึ่ง business unit (property/โรงแรม) ทุกชุดใช้ migration history ร่วมกันชุดเดียวที่นิยามไว้ใน package `@repo/prisma-shared-schema-tenant` เดียว เมื่อใดก็ตามที่ package นั้นได้ migration ใหม่ ทุก tenant schema ในทุก cluster ต้องรัน `prisma migrate deploy` ก่อนที่โค้ดแอปพลิเคชันที่สอดคล้องกันจะพึ่งพา column/table ใหม่ได้ — และผู้ให้บริการโรงแรมหนึ่งรายอาจมีหลายสิบ property ที่ rollout คนละจังหวะกัน หากไม่มีมุมมองระดับ fleet operator ต้องเปิดหน้าแก้ไขของแต่ละ BU แล้วเช็คแท็บ Technical ทีละตัว หน้าจอนี้จึงมีไว้เพื่อตอบคำถาม "tenant ตัวไหนตามหลัง และตามหลังแค่ไหน" ในมุมมองเดียว (`FleetSync`, §3.1) และให้ operator ที่ถือ `tenant_migration.apply` (หรือ pipeline CI/CD ผ่าน deploy token, §4.2) ผลักดันทุกตัวไปข้างหน้า — หรือไล่ทั้ง fleet ในครั้งเดียว — โดยไม่ต้องออกจากหน้า

## 3. แนวคิดสำคัญ

### 3.1 Layout ของหน้าจอ

- **Header** — `PageHeader` หัวข้อ "Tenant migrations" คำบรรยาย "Check which tenant databases are behind on schema migrations, and roll them out."
- **การ์ดสรุป Fleet Sync** (`FleetSync`) — การ์ดแนวนอนแสดง `{จำนวนที่ in-sync} / {BU ทั้งหมด}` ด้วยตัวเลขขนาดใหญ่แบบ monospace, progress bar สามสี (เขียว/เหลือง/แดง) สำหรับ in-sync/behind/errored และแถว legend พร้อมจำนวน (ตัวเลขรวม migration ที่ค้างจะโผล่ก็ต่อเมื่อไม่ใช่ศูนย์) ก่อนรัน "Check all" ครั้งแรกจะแสดง "Not checked yet" แทน bar ช่อง action มีปุ่ม **Check all**, **Deploy all**, และ **Export**
- **Deploy Console** (`DeployConsole`) — render เฉพาะตอนที่ batch "Deploy all" กำลังทำงาน: panel รูปแบบ terminal สีเข้ม พร้อม progress bar (applied/total ของ BU ที่กำลัง migrate), code ของ BU ปัจจุบัน และ log แบบ scroll ที่มีสีต่อ BU ที่เสร็จแล้ว (เขียวสำหรับ applied/up-to-date, แดงสำหรับ failed)
- **ช่องค้นหา** — filter ฝั่ง client เหนือตาราง BU (code/name)
- **ตาราง BU** (`DataTable`, 3 คอลัมน์ sticky ซ้าย) — **Code** (ลิงก์ไป `/business-units/:id/edit`), **Name**, **Schema** (ใหม่, PR #296 — `db_schema` ของ BU แบบ monospace พร้อมชื่อ `tb_database_pool` ที่ผูกไว้ตัวเล็กด้านล่าง `—` เมื่อยังไม่ตั้ง schema; เป็นคอลัมน์ derived ตัวเดียวที่ตั้งใจให้ค้นหาได้ เพราะการพิมพ์ชื่อ schema แล้วหาแถวที่ชี้มันเป็นคำถามจริงของ operator), **Status** (badge — "In sync" / "N behind" / "Error" / "Not checked" บวกบรรทัด inline "Applying X/Y … ชื่อ migration ปัจจุบัน" ระหว่าง Apply ต่อแถวกำลัง stream หรือ error message inline; เมื่อแถวถูกตรวจแล้ว badge ที่สองแสดงสถานะ dashboard-views — "N views behind" หรือ "Views in sync" — หรือ error inline "Views: …" ถ้า micro-data รายงานไม่ได้), **Last checked** (HH:MM:SS ตามเวลา client) และคอลัมน์ row-actions (ไอคอน **Check**, **Apply** ที่แสดงเฉพาะแถวที่มี migration ค้าง, ไอคอน **Apply dashboard views** บนทุกแถวที่ตรวจแล้ว (disable พร้อม tooltip "Views in sync" เมื่อไม่มีอะไรตามหลัง — §3.2c) และ — ตั้งแต่ PR #297 — ไอคอนประแจ **Resolve** บนทุกแถวที่สถานะเป็น `error`, §3.2a) Status และ Last checked เรียงฝั่ง client ด้วยการคลิกหัวคอลัมน์ตั้งแต่ PR #292 (`accessorFn` เหนือ rank/เวลาที่ derive ไว้แล้ว — `accessorFn` มีไว้แค่เปิดปุ่ม sort; ทั้งสองคอลัมน์ถูกตัดออกจากช่องค้นหาอย่างชัดเจน เพื่อไม่ให้ rank สถานะหรือ timestamp ไปตรงกับคำค้นที่พิมพ์) ไม่มีคอลัมน์ Pending บนหน้าจอ — badge Status พูดจำนวนอยู่แล้ว ("3 behind" / "In sync") ไฟล์ CSV export (ด้านล่าง) ยังมีคอลัมน์นี้ บวกคอลัมน์ Schema และ pool เพราะที่นั่นค่าเปล่า ๆ มีประโยชน์จริงสำหรับคำนวณต่อ
- **Empty state** — "No business units" พร้อมปุ่ม "Go to Business Units" แสดงเมื่อ fleet มี BU เป็นศูนย์ (ไม่ใช่ migration ค้างเป็นศูนย์)
- `DevDebugSheet` (dev เท่านั้น) แสดงรายการ business unit ดิบที่หน้านี้โหลดมา

ตั้งแต่ `254b05ee` (2026-09-30) รายการถูกโหลดด้วย `fetchAllBusinessUnits` ซึ่งเดินผ่าน `GET /api-system/business-units` ทีละหน้า (หน้าละ 100 สูงสุด 10 หน้า, `utils/fetchAllPages.ts`); การ fetch ครั้งเดียวแบบ `perpage: 1000` เดิมและคำเตือน "Showing N of M business units" ถูกเอาออกแล้ว

### 3.2 Action และการเรียก backend

| Action | Trigger ของ UI | เรียก Backend | Gate |
|---|---|---|---|
| แสดงรายการ business unit | โหลดหน้า | `fetchAllBusinessUnits({ sort: 'code:asc' })` → `GET /api-system/business-units` ทีละหน้า | `tenant_migration.read` (route) |
| Check (แถวเดียว) | ไอคอน row action | `GET /api-system/tenant/migrations/:bu_id/status` (สำหรับ BU เดียว gateway คืนสถานะ `views` ของ micro-data ด้วย) | Frontend: ไม่มี gate เพิ่มนอกจาก route Backend: `tenant_migration.read` ผ่าน `TenantMigrationGuard` (§4.2) |
| Check all | ปุ่มบนการ์ด Fleet Sync | เรียก `GET .../status` ต่อ BU จำกัด concurrency ที่ 4 พร้อมกัน (`mapWithConcurrency`) | เหมือน Check (ปุ่มไม่ถูก gate ด้วย `apply`) |
| Apply (แถวเดียว) | ไอคอน Apply ต่อแถว → confirm dialog | `POST /api-system/tenant/migrations/:bu_id/deploy/stream` (NDJSON progress; gateway ต่อด้วยขั้น dashboard-views ของ BU หลัง Prisma deploy สำเร็จ, §3.2c) | Frontend: disable พร้อม tooltip เรื่อง permission เว้นแต่มี `tenant_migration.apply` Backend: `tenant_migration.apply` |
| Deploy all | ปุ่มบนการ์ด Fleet Sync → confirm dialog | `POST /api-system/tenant/migrations/all/deploy/stream` (NDJSON progress ทีละ BU ฝั่ง server, ขั้น views ต่อ BU) | เหมือน Apply |
| Resolve (ทีละแถว) — **ใหม่, PR #297** | ไอคอนประแจบนแถว `error` → `TenantMigrationResolveDialog` | `POST /api-system/tenant/migrations/:bu_id/resolve` พร้อม `{ migration_name, action: 'applied' \| 'rolled-back' }` — JSON ธรรมดา ไม่ใช่ stream ดังนั้น interceptor ของ axios ปกติที่ refresh-แล้ว-retry เมื่อ 401 และ `x-app-id` ใช้ได้ | เหมือน Apply (`tenant_migration.apply`); backend ตรวจเพิ่มว่าชื่อตรง pattern (400), โฟลเดอร์ migration มีอยู่ (400) และไม่มี deploy/resolve ของ BU เดียวกันกำลังทำงาน (409) |
| Apply dashboard views (ทีละแถว) — **ใหม่, 2026-10-06** | ไอคอน layout-dashboard บนแถวที่ตรวจแล้ว | `POST /api-system/tenant/migrations/:bu_id/views/apply` — JSON ธรรมดา `{ applied: string[], skipped: number }` | เหมือน Apply Backend error: 409 (views migration ของ BU กำลังรันอยู่), 422 (tenant schema ว่าง — apply Prisma migration ก่อน), 502/503/504 (micro-data ล้มเหลว ถูกปิด หรือ timeout) |
| Export | ปุ่มบนการ์ด Fleet Sync | CSV ฝั่ง client จาก code/name/schema/pool/status/pending/last-checked ของ state ที่โหลดไว้แล้ว | ไม่มี — export สิ่งที่ตารางแสดงอยู่ปัจจุบัน |

ฝั่ง frontend ไม่เคยเรียก `POST /api-system/tenant/migrations/:bu_id/deploy` แบบไม่ stream เลย — `tenantMigrationService.deploy()` ถูกนิยามไว้แต่ไม่มีผู้เรียกใน `carmen-backstage` เลย (ยืนยันจาก grep ทุกจุดที่เรียก `tenantMigrationService.`) ทั้ง `TenantMigrationManagement` และการ์ด `TenantMigrationCard` ต่อ BU รัน apply ผ่าน streaming variant เท่านั้น

**ป้ายของปุ่ม Deploy all ขึ้นอยู่กับ state โดยตั้งใจ** (`../carmen-backstage` commit `dbb1107`, 2026-09-01 ซึ่งถอดคอลัมน์ Pending บนหน้าจอออกไปด้วยในคราวเดียวกัน): ปุ่มใช้ `variant={behindCount > 0 ? 'destructive' : 'outline'}` — เป็นสีแดงเฉพาะเมื่อมี BU ที่ behind มากกว่าศูนย์ พร้อมป้ายที่บอกรัศมีของตัวเอง ("Deploy 3 behind" แทน "Deploy all" เฉย ๆ) และถูก disable (ไม่ใช่แค่จางลง) เมื่อตรวจแล้วพบว่าไม่มีอะไรให้ deploy เหตุผลจาก comment ของปุ่มเองคือโดเมนนี้ไม่มี endpoint cancel/rollback ปุ่มที่ดูเร่งด่วนที่สุดบนจอจึงไม่ควรเป็นปุ่มที่ operator ย้อนกลับไม่ได้มากที่สุด

### 3.2a การ resolve migration ที่ค้างจากหน้าจอ

`prisma migrate resolve --applied|--rolled-back <name>` เขียนทับหนึ่งแถวของตาราง `_prisma_migrations` ของ tenant **โดยไม่รัน SQL ของ migration นั้น** — เครื่องมือเดียวสำหรับ migration ที่ล้มเหลวกลางทางแล้วบล็อกทุก `migrate deploy` ที่ตามมา endpoint ฝั่ง backend มีมาตั้งแต่โมดูลออก; สิ่งที่ PR #297 (2026-09-16) เพิ่มคือ path ฝั่ง frontend:

- **ปุ่มปรากฏที่ไหน** บน**ทุก**แถวที่สถานะเป็น `error` ไม่ใช่เฉพาะแถวที่ parse ชื่อ migration ที่ล้มเหลวได้ — ตั้งใจ ตามเหตุผลของ commit เอง: การผูกการมองเห็นปุ่มกับการ parse ที่สำเร็จจะทำให้ปุ่มหายไปในวันที่ Prisma เปลี่ยนคำใน output ซึ่งเป็นวันที่ต้องใช้มันพอดี ราคาที่ต้องจ่ายคือแถวที่ error ด้วยเหตุผลอื่น (เช่น DB ที่เข้าถึงไม่ได้) ก็แสดงประแจด้วย; backend ตอบตามตรงในกรณีนั้น
- **dialog** (`TenantMigrationResolveDialog` ใช้ร่วมกันแบบเดียวกันเป๊ะระหว่างตารางนี้กับการ์ดต่อ BU — implementation เดียว เพราะทั้งคู่ยิง endpoint เดียวกันและต้องมีคำเตือนเดียวกัน) ถามชื่อโฟลเดอร์ migration (validate ฝั่ง client ด้วย `MIGRATION_NAME_RE = /^[0-9]{6,}_[A-Za-z0-9_-]+$/` regex เดียวกับ backend; ชื่อที่ไม่ตรงได้ข้อความ inline และปุ่มถูก disable) และ select ของ action ที่**ค่าเริ่มต้นเป็น `rolled-back`** — ฝั่งที่ปลอดภัยกว่า เพราะการทำเครื่องหมาย migration เป็น `applied` ทั้งที่ SQL ไม่เคยรันจะทิ้ง schema ให้ล้าหลังเงียบ ๆ ตลอดไป และ Deploy จะไม่แตะชื่อนั้นอีกเลย ข้อความใน dialog บอกไว้ตรง ๆ
- **ชื่อถูกกรอกล่วงหน้า** จาก `err.response.data.message` ดิบของ `GET /status` ที่ล้มเหลว — `parseFailedMigration()` (`utils/migrationError.ts`) หยิบ token `\d{6,}_slug` ตัวแรก*หลัง*คำว่า "fail" ใน output ของ Prisma เพราะชื่อก่อนบรรทัดนั้นคือตัวที่สำเร็จ มันอ่าน axios error ดิบโดยตั้งใจแทน `getErrorDetail()` ซึ่ง redact ข้อความใน production: การอ่านสำเนาที่ redact แล้วจะทำให้การกรอกล่วงหน้าทำงานบนเครื่องนักพัฒนาแต่ไม่ทำอะไรเลยบน production เงียบ ๆ
- **หลังสำเร็จ** แถวถูก re-check ทันที (`checkOne(bu)`); ถ้าไม่ทำ แถวจะยังคง badge Error เดิมทั้งที่การแก้ไขลงไปแล้ว

### 3.2c Dashboard view (micro-data) ควบคู่กับ Prisma migration

schema tenant ของแต่ละ BU ยังมี dashboard view ที่ micro-data เป็นเจ้าของด้วย ตั้งแต่ `c65b21f5` (2026-10-06) หน้าจอนี้แสดงและ apply มันข้าง ๆ สถานะ Prisma:

- **สถานะ** `GET /status` ของ BU เดียวเพิ่ม `views` (`{ bu_code, schema, baseline_applied, pending[], changed[], applied[] }` หรือ `{ error }`) ที่ดึงจาก micro-data เมื่อ gateway ตั้ง `MICRO_DATA_MIGRATION_TOKEN` ไว้; `all` จงใจข้ามเพื่อไม่ให้การเรียกสถานะครั้งเดียวกระจายเป็น N คำขอไป micro-data (`tenant-migrations.service.ts`) badge ที่สองของแถวนับ `pending + changed`
- **Apply** ไอคอน Apply-views ของแถวเรียก `POST …/views/apply` ตรง ๆ (path ซ่อมแซม) path ปกติเป็นอัตโนมัติ: deploy stream ของ gateway ต่อขั้น views หลัง Prisma deploy ของแต่ละ BU (`chain-views-after-prisma.ts`) โดยส่ง heartbeat ของ log (`views: applying …` ทุก 20 วินาทีขณะรัน) และ event `views-complete` ต่อ BU; หน้าจอพับ event นั้นเข้าสถานะ views ของแถวและบันทึกบรรทัด "views: applied N" หรือ "failed" ใน Deploy Console ถ้าขั้น Prisma ล้มเหลว ขั้น views ของ BU นั้นจะถูกรายงานเป็น `skipped: prisma failed`
- **สรุป** summary ของ event `done` สุดท้ายเพิ่ม `views_failed: string[]` (รหัส BU); toast ของ Deploy-all อ่านว่า "Deployed: N ok, M failed, views failed on K." และลดเป็นคำเตือนเมื่อ K > 0
- **เมื่อปิด** ถ้า gateway ไม่มี token ของ micro-data `views` จะไม่มี และขั้นนั้นถูกข้าม (`viewsClient.isEnabled()`) badge และไอคอนจึงไม่ปรากฏสำหรับสถานะนั้น

### 3.2b แถวรายการ business unit และคอลัมน์ Schema

คอลัมน์ใหม่ทั้งสองอ่านฟิลด์ที่รายการแถวมีอยู่แล้ว (`tb_business_unit.db_schema`, `database_pool.name`) — ไม่มี request ใหม่ ต่ำกว่า breakpoint `lg` `DataTable` render หนึ่งการ์ดต่อแถว และชื่อ pool จะขึ้นบรรทัดใหม่แทนที่จะถูกตัดที่นั่น เพราะชื่อ pool ที่ถูกตัดในการ์ดไม่มี tooltip ตอน hover ให้เห็นส่วนที่เหลือ (วัดที่ 390px: ชื่อ 218px ในเซลล์ 206px)

### 3.3 สถานะของ migration และสิ่งที่ทำให้มันเดินหน้าหรือค้าง

ไม่มีแถวสถานะ migration ที่ persist อยู่ใน schema ของแพลตฟอร์มเองเลย (ดู [Data Model](/th/backstage/tenant-migrations/data-model) §2) — ทุกสถานะบนหน้าจอนี้ถูกคำนวณสด ๆ ต่อ request โดยการเรียก Prisma CLI ไปยังฐานข้อมูล tenant เป้าหมาย แล้วจับ pattern จาก text ที่มันพิมพ์ออกมา:

- **`up_to_date`** — output ของ `prisma migrate status` ตรงกับ `/up to date/i`
- **`has_pending`** — output ตรงกับ `/not yet been applied/i`; ชื่อ migration ที่ค้างแต่ละตัวถูกดึงออกจาก output เดียวกันด้วย pattern ทั่วไป `\d{14}_[a-z0-9_]+`
- **กรณีอื่นที่ exit code ไม่เป็นศูนย์** จะตกไปเป็น error ธรรมดา (`Result.error`) — โค้ดนี้ไม่มีการจำแนก "ค้าง" หรือ "ล้มเหลว" เป็นพิเศษเลย migration ที่เคยล้มเหลวระหว่าง `migrate deploy` จะถูกรายงานด้วยคำที่ Prisma CLI ใช้เอง ซึ่ง service นี้ไม่ได้จับ pattern พิเศษให้ — มันจะไม่ตรงทั้ง `has_pending` และ `up_to_date` และจะโผล่มาเป็น error ทั่วไปของการ check status ที่พกข้อความดิบของ Prisma มาด้วย — ซึ่งเป็นข้อความเดียวกับที่ `parseFailedMigration()` ของ frontend ขุดหาชื่อสำหรับกรอกล่วงหน้าใน dialog Resolve (§3.2a)

**การทำให้ migration เดินหน้า** คือการรัน `prisma migrate deploy --schema <schema>` กับ connection string ของ tenant ที่ resolve แล้ว — connection ที่ resolve แล้วมาจาก `tb_business_unit.db_schema` บวกแถว `tb_database_pool` ที่ผูกไว้ (host/port/database/username และรหัสผ่านที่ถอดรหัสแล้ว) **ไม่ใช่** จาก column `db_connection` ที่ไม่มีอยู่บน `tb_business_unit` อีกต่อไป (§4.3 ชี้ comment ที่ล้าสมัยใน frontend service file ซึ่งยังบรรยายกลไกเดิม) เมื่อสำเร็จ บรรทัด `Applying migration \`name\`` ของ CLI จะถูก parse เพื่อสร้างรายการ "applied" ที่ stream กลับมาเป็น `applying` progress event; event `done` ที่ `already_up_to_date: applied.length === 0` จะปิด stream

**สิ่งที่ `deploy` ที่ล้มเหลวทิ้งไว้เบื้องหลัง:** exit code ที่ไม่เป็นศูนย์จาก `prisma migrate deploy` ถูกรายงานเป็น stream `error` event (หรือ HTTP error บน path ที่ไม่ stream) พร้อม output ของ CLI ที่ผ่านการกรองข้อมูลอ่อนไหวแล้ว — operation จะไม่ถูก retry และไม่มีอะไรใน backend ตรวจสอบว่า migration *ตัวไหน* ล้มเหลว การรันต่อ BU และแบบ batch ถูกป้องกันด้วย in-memory lock (`runningBuIds` ต่อ BU, `isBatchRunning` สำหรับทั้ง fleet) ที่คืน 409 "already running" ขณะถูกถืออยู่ แต่ทั้งสอง lock ไม่มีอายุยืนกว่า request เดียว — ไม่มีอะไรจดจำว่า BU ไหนถูกทิ้งไว้กลาง migration เมื่อ process เดินหน้าต่อไปแล้ว endpoint ที่สร้างมาเพื่อล้าง migration ที่ค้างจริง ๆ คือ `POST :bu_id/resolve` (`prisma migrate resolve --applied|--rolled-back <name>`); **ตั้งแต่ PR #297 มันเข้าถึงได้จากหน้าจอนี้และจากการ์ดต่อ BU** (§3.2a) — การแก้ไขรอบ 2026-09-06 ของหน้านี้บันทึกไว้ว่าไม่มีโค้ด frontend เรียกมัน ซึ่งจริงในตอนนั้นและไม่จริงแล้ว

**Deploy-all ป้องกันได้แค่ BU *ถัดไป* ไม่ใช่ตัวที่กำลังทำอยู่** comment ของ `deployAllStream` เอง (`tenant_migration.service.ts:538-625` ใน `../carmen-turborepo-backend`) ระบุว่าการยกเลิกหยุดแค่ batch จากการเริ่ม tenant ถัดไป — BU ที่กำลัง migrate อยู่ตอน client ตัดการเชื่อมต่อจะทำงานต่อจนเสร็จ (หรือจนถึง timeout ของตัวเอง) ไม่ว่ากรณีใด — `AbortController` ของ frontend ตอน unmount หยุดแค่ browser จากการรอฟัง ตาม doc comment บน `tenantMigrationService._streamDeploy` ไม่มี endpoint cancel/rollback สำหรับโดเมนนี้เลย

### 3.4 สวิตช์ปิด/เปิด และ path ของ CI deploy-token

ทั้ง controller ของ tenant-migration อยู่หลัง `TENANT_MIGRATION_API_ENABLED` ซึ่งเป็น environment-variable boolean ที่ **ปิดโดยดีฟอลต์** เมื่อไม่ได้ตั้งค่า (`boolFromString(false)`, `../carmen-turborepo-backend/apps/backend-gateway/src/libs/config.env.ts:209`) — ทุกการเรียก รวมถึง status check ธรรมดา จะ 403 ด้วย "Tenant migration API is disabled" จนกว่า operator จะตั้งค่าเป็นสตริง `true` อย่างชัดเจน นี่เป็น env var ธรรมดา ต่างจากสวิตช์ชื่อคล้ายกันของโมดูล [Backstage Migrations](/th/backstage/backstage-migrations) แยกต่างหาก ซึ่งสวิตช์เปิด/ปิดของมันถูกย้ายเข้า `tb_backstage_config` (`backstage_migration.api_enabled`) แล้ว — comment เหนือ `BACKSTAGE_DEPLOY_TOKEN` ใน `config.env.ts` (บรรทัด 199-206) พูดถึงโมดูลอื่นนั้น ไม่ใช่โมดูลนี้; สวิตช์ของโมดูลนี้ยังไม่ได้ย้าย

นอกจาก session ที่ถือ key `tenant_migration.*` ของ route แล้ว backend ยังรับ header `x-deploy-token` (เปรียบเทียบด้วย `timingSafeEqual` เทียบกับ `TENANT_DEPLOY_TOKEN`) เป็น credential ทางเลือก ออกแบบไว้ให้ pipeline CI/CD สั่ง deploy ได้โดยไม่ต้องมี session ของมนุษย์ หน้าจอ SPA นี้ไม่เคยใช้ path นั้นเลย — authenticate ในฐานะ operator ที่ signed-in เท่านั้นเสมอ — ดังนั้น path ของ deploy-token จึงมองไม่เห็นจาก UI นี้เลย การใช้มันต้องเรียก API ตรง ๆ (เช่นผ่าน Bruno collection, §6)

### 3.5 ความสัมพันธ์กับหน้าแก้ไข Business Units

- การ์ด `TenantMigrationCard` ต่อ BU บน [Business Units — UI Screens](/th/backstage/business-units/ui-screens) §4.5 และหน้านี้เรียก `tenantMigrationService` (`getStatus`, `deployStream`, `deployAllStream`) และ backend controller **เดียวกัน** — มี implementation ของ "ตรวจสอบสถานะ" และ "apply migration" เพียงชุดเดียว ที่แสดงผลจากสองหน้าจอ [Business Units — Tenant Migrations](/th/backstage/business-units/tenant-migrations) ตอนนี้เป็น pointer สั้น ๆ ที่ครอบคลุมเฉพาะการ์ดที่ฝังอยู่นั้น หน้านี้คือเรื่องเต็มของหน้าจอระดับ fleet
- ทั้งสองหน้าจอใช้การแยก permission เดียวกัน บนหน้าแก้ไข Business Unit การ์ดจะ render เฉพาะเมื่อมี `tenant_migration.read` และได้รับ `canApply = hasPermission('tenant_migration.apply', …)` ทั้งคู่ด้วย `clusterId={BACKSTAGE_SCOPED_RECORD}` (`BusinessUnitEdit.tsx:828-836`); ภายในการ์ด Check ถูก disable เฉพาะเมื่อ BU ไม่มี pool + schema (`checkReason` = `hasDbConnection` เป็น false) ส่วน Apply และ Resolve ต้องมี `canApply` ด้วย (`TenantMigrationCard.tsx:49-51`) ตารางระดับ fleet นี้ไม่มีการ pre-check `hasDbConnection`: มันให้ operator ลอง Check/Apply บนแถวใดก็ได้ และแสดง error ใดก็ตามที่ `resolveConnection` โยนออกมา (§3.3) เมื่อส่งคำขอแล้ว
- ทั้งสองหน้าจอเปิด `TenantMigrationResolveDialog` **ตัวเดียวกัน** (§3.2a) การ์ดมีข้อบกพร่องที่สองที่แก้ใน PR เดียวกัน: มันเคยกลืน `GET /status` ที่ล้มเหลวไปทั้งหมด เหลือแค่ toast ที่หายไปในสี่วินาทีและ BU ที่อ่านว่า "Not checked" ตลอดไป; ตอนนี้มันเก็บ error ไว้บนหน้าจอ (`role="alert"`, ข้อความดิบ) เพื่อให้ปุ่ม Resolve มีอะไรให้เกาะและมีชื่อให้กรอกล่วงหน้า
- **ไม่มีลิงก์ในแอป** ระหว่างสองหน้าจอนี้ในทิศทางใดเลย — ยืนยันจากการอ่าน source ของทั้งสอง component ทางเดียวที่จะมาหน้านี้คือรายการ sidebar "Tenant Migrations" หรือพิมพ์ URL เอง คอลัมน์ "Code" ของหน้านี้พาไปหน้าแก้ไข BU นั้นตรง ๆ ไม่ใช่เวอร์ชัน filter ของตัวเอง

## 4. บทบาทและสิทธิ์

> **เปลี่ยนเมื่อ 2026-09-29** (`9adbf5e7`, `40f2e61c`, `d51121f1`): โมดูลนี้มี resource permission ของตัวเอง `tenant_migration` พร้อมสอง action — `read` (ดูสถานะ BU เดียวหรือทั้ง fleet) และ `apply` (deploy migration ที่ค้างทีละ BU หรือทุก BU และ resolve ตัวที่ล้มเหลว) gate `cluster.read` ของ route เดิมและ gate action เฉพาะ super-admin หายไปแล้ว role ที่ seed ไว้: `Backstage Admin` ถือ `tenant_migration.*`; `Support Manager` และ `Support Staff` ถือเฉพาะ `tenant_migration.read` (`seed.backstage-role-permission.data.ts`)

### 4.1 เมทริกซ์ด่านฝั่ง frontend

| จุด | ประเภท Gate | Key | หมายเหตุ |
|---|---|---|---|
| route `/tenant-migrations` | `requiredPermission` + `feature` | `tenant_migration.read` + `tenant_migrations` | `App.tsx:271-278` |
| รายการ sidebar "Tenant Migrations" | filter ด้วย `permission` + `feature` | `tenant_migration.read` / `tenant_migrations` | `navGroup.organization`, `parentPath: '/business-units'`, `src/components/nav/backstageNav.ts:17` |
| ปุ่ม Check ต่อแถว | `disabled={busy \|\| batchRunning}` (`readDisabled`) | ไม่มี นอกจาก route | Check ใช้ได้กับทุก session ที่เปิดหน้านี้ได้ |
| ปุ่ม Apply ต่อแถว (render เฉพาะเมื่อ `has_pending`) | `writeDisabled` = `!canApply \|\| busy \|\| batchRunning` | `tenant_migration.apply`, `clusterId={BACKSTAGE_SCOPED_RECORD}` | Tooltip "Requires the tenant_migration.apply permission."; มี confirm dialog ก่อนเริ่ม stream |
| ปุ่ม Check all | `anyBusy \|\| bus.length === 0` | ไม่มี นอกจาก route | ไม่ถูก gate ด้วย `apply` |
| ปุ่ม Deploy all | `!!applyReason \|\| anyBusy \|\| bus.length === 0 \|\| nothingToDeploy` | `tenant_migration.apply` | ยัง disable เองเมื่อไม่มีอะไรค้าง (§3.2) |
| Apply dashboard views ต่อแถว (render บนแถวที่ตรวจแล้ว) | `writeDisabled \|\| viewsInSync` | `tenant_migration.apply` | Tooltip "Views in sync" เมื่อ disable ด้วยเหตุผลนั้น |
| Resolve ต่อแถว (ประแจ render เฉพาะเมื่อสถานะของแถวเป็น `error`) | `writeDisabled` | `tenant_migration.apply` | เปิด `TenantMigrationResolveDialog`; ปุ่ม Resolve ของ dialog เองถูก disable เพิ่มจนกว่าชื่อ migration จะตรง `MIGRATION_NAME_RE` (§3.2a) |
| ปุ่ม Export | `disabled={loading \|\| bus.length === 0 \|\| anyBusy}` | ไม่มี | Export เฉพาะ state ที่ client โหลดไว้แล้วเท่านั้น |

### 4.2 การบังคับใช้ฝั่ง backend

ทุก endpoint ระดับ migration อยู่หลัง `TenantMigrationGuard` (`../carmen-turborepo-backend/apps/backend-gateway/src/auth/guards/tenant-migration.guard.ts`) ใช้ครั้งเดียวกับทั้ง controller ผ่าน `@UseGuards(TenantMigrationGuard)` มันบังคับ `TENANT_MIGRATION_API_ENABLED` ก่อน ก่อนการตรวจ credential ใด ๆ ดังนั้นเมื่อ flag ปิดจะ 403 ไม่ว่าใครเรียก จากนั้นต้องการ **หนึ่งใน**: header `x-deploy-token` ที่ตรงกัน (เทียบแบบ constant-time, §3.4; actor ถูกบันทึกเป็น `ci:deploy-token`) หรือ session Keycloak ที่ permission ของ Backstage ซึ่ง route ประกาศไว้ผ่าน `BackstagePermissionGuard` **ที่ scope ระดับ Backstage** — grant ที่ถือเฉพาะ cluster เดียวถูกปฏิเสธ (`Missing backstage permission: <key> (backstage scope required)`) เพราะ route เหล่านี้แตะ BU ใดก็ได้และ `all` key ของ route คือ `tenant_migration.read` สำหรับ `GET :bu_id/status` และ `tenant_migration.apply` สำหรับ `deploy`, `deploy/stream`, `views/apply` และ `resolve` (`tenant-migrations.controller.ts`); super-admin ผ่านทั้งคู่ route ที่ไม่ประกาศ key จะถูกปฏิเสธทันที `applyReason` ของ frontend ("Requires the tenant_migration.apply permission.") เป็นความสะดวกของ UI ที่ตรงกับ ไม่ได้ทดแทน การตรวจฝั่ง server นี้ — ต่างจากช่องว่างที่ยืนยันแล้วของ [SQL Workbench](/th/backstage/sql-workbench) และ [Query Dataset](/th/inventory/system-config/query-dataset) guard ฝั่ง backend ของ tenant-migrations ไม่สามารถเลี่ยงได้ด้วยการเรียก API ตรง ๆ โดยไม่มี key

### 4.3 ยืนยันซ้ำกับ source ปัจจุบัน: comment ที่ล้าสมัย แก้ไขแล้ว

ไฟล์ `tenantMigrationService.ts` ฝั่ง frontend ยังมี comment นี้อยู่ ไม่เปลี่ยนแปลงตั้งแต่เขียนครั้งแรก (`../carmen-backstage` commit `8fc1124`, 2026-06-29): *"The backend resolves the target tenant DB from the BU's stored db_connection."* คำบรรยายนี้ถูกแซงหน้าโดย `../carmen-turborepo-backend` commit `af2437074` (2026-08-13) ซึ่งย้ายการ resolve connection จาก column `tb_business_unit.db_connection` (JSON) ที่ถูกถอดออกแล้ว ไปเป็น `db_schema` บวกแถว `tb_database_pool` ที่ผูกไว้ (ยืนยันจากการอ่าน `resolveConnection()` ใน `apps/micro-business/src/tenant/tenant.service.ts` โดยตรง — ไม่มี path โค้ดใดใน tree ปัจจุบันอ่าน `db_connection` เพื่อจุดประสงค์นี้อีกแล้ว) comment ไม่เคยถูกอัปเดตให้ตรงกัน มันคือหนี้เอกสารในตัว source เอง ไม่ใช่คำบรรยายพฤติกรรมปัจจุบัน — หน้านี้บรรยายกลไก pool/schema ที่โค้ดรันจริง (§3.3)

### 4.4 ยืนยันซ้ำกับ source ปัจจุบัน: การ map error status ที่ตายแล้วบน stream path

ตัวจัดการ `deployStream` ฝั่ง gateway map ความล้มเหลวก่อนเริ่ม stream เป็น HTTP status ด้วยการจับ pattern ข้อความ error (`resolvePreStreamErrorStatus()`, `tenant-migrations.controller.ts`) เพิ่มเข้ามาใน commit `4ca923229` (2026-06-30) ตอนที่ความล้มเหลวของ `resolveConnection` ยังอ่านว่า "no database connection configured" / "unsupported database provider" การ refactor เดียวกัน `af2437074` (§4.3) เปลี่ยนข้อความที่โยนออกมาจริงเป็น "is not linked to a database pool", "has no database schema configured", "has been deleted", และ "is inactive" — ไม่มีข้อความไหนตรงกับ regex ของ `resolvePreStreamErrorStatus` เลย ผลที่เกิดขึ้นจริง: ตั้งแต่ 2026-08-13 เป็นต้นมา BU ที่ไม่ได้ผูก pool, ไม่ได้ตั้ง schema, หรือ pool ถูกปิด/ลบ จะได้ HTTP 500 กลับจาก `/deploy/stream` (ค่า fallback ของ function เมื่อข้อความไม่ตรง) แทนที่จะเป็น 422 ตามที่เอกสารระบุ ตัวข้อความเองยังไปถึง operator ถูกต้อง (`errorMsg` ต่อแถวของ frontend แสดง text ดิบไม่ว่า status code จะเป็นอะไร และ `handleMigrationError` จะแยกเฉพาะ 403/409 เป็นพิเศษเท่านั้น) ดังนั้นนี่คือช่องว่างจริงในสัญญา status code ของ API ไม่ใช่ช่องว่างในสิ่งที่ operator เห็นบนจอ `GET /status` และ `POST /deploy` แบบไม่ stream ไม่ได้รับผลกระทบ — คืน status ผ่าน `StdResponse.fromResult()`'s generic `ErrorCode` mapping ไม่ใช่ regex ตัวนี้

## 5. โมดูลที่เกี่ยวข้อง

- [Business Units](/th/backstage/business-units) — ทุกแถวบนหน้านี้คือ `business_unit` หนึ่งตัว หน้าย่อย [Tenant Migrations](/th/backstage/business-units/tenant-migrations) ที่นั่นครอบคลุมเฉพาะการ์ด `TenantMigrationCard` ต่อ BU ที่ฝังอยู่ ไม่ใช่หน้าจอระดับ fleet นี้
- [Database Pools](/th/backstage/database-pools) — แถว `tb_database_pool` ที่ `database_pool_id` ของ BU ชี้ไป pool ที่ถูกปิดหรือ soft-delete ทำให้ connection ของ tenant นั้น resolve ไม่ได้ (§3.3, §4.4)
- [Backstage Roles](/th/backstage/rbac) — โมเดล permission เบื้องหลัง `tenant_migration.*` และ (`rbac/permissions.md`) ตาราง gate ระดับ route ที่มี `/tenant-migrations` อยู่ด้วย
- [SQL Workbench](/th/backstage/sql-workbench) — คอนโซลฐานข้อมูลต่อ tenant อีกตัว เพิ่มมาในช่วงเดียวกัน §4.2 ข้างต้นเทียบช่องว่าง permission จริงของมันกับของโมดูลนี้ (ที่ bypass ไม่ได้)

## 6. แหล่งอ้างอิง

- `../carmen-backstage/src/pages/TenantMigrationManagement.tsx` — หน้า fleet แบบ standalone: state, คอลัมน์, handler ของ Check/Apply/Deploy-all/Export, การ cleanup abort-on-unmount ของ `activeStreamControllersRef`
- `../carmen-backstage/src/pages/tenantMigration/{FleetSync,DeployConsole}.tsx` — การ์ดสรุปและ console สำหรับ batch-deploy แบบสด
- `../carmen-backstage/src/services/tenantMigrationService.ts` — `getStatus`, `deploy` (ไม่มีผู้เรียก), `deployStream`, `deployAllStream`, `resolve` (PR #297), `applyViews` (2026-10-06) และ doc comment เรื่อง semantics ของการ abort stream (§4.3 ชี้บรรทัด `db_connection` ที่ล้าสมัย)
- `../carmen-backstage/src/components/TenantMigrationCard.tsx`, `src/components/TenantMigrationResolveDialog.tsx`, `src/utils/migrationError.ts` (`MIGRATION_NAME_RE`, `parseFailedMigration`) — การ์ดต่อ BU ที่บันทึกไว้ใน [Business Units — UI Screens](/th/backstage/business-units/ui-screens) §4.5, dialog Resolve ที่ใช้ร่วมกัน และตัว parse ชื่อ (§3.2a)
- `../carmen-backstage/src/types/index.ts` — `TenantMigrationResolveAction`, `TenantMigrationResolveResult` (ทุกฟิลด์เป็น optional เพื่อให้ backend ที่เพิ่มหรือตัดฟิลด์ทำหน้าพังไม่ได้)
- `../carmen-backstage/src/App.tsx:271-278` — route `/tenant-migrations` (`requiredPermission="tenant_migration.read"` บวก `feature="tenant_migrations"`)
- `../carmen-backstage/src/components/nav/backstageNav.ts:17` — รายการ sidebar (`permission: 'tenant_migration.read'`, `feature: 'tenant_migrations'`, `groupKey: 'navGroup.organization'`, `parentPath: '/business-units'`)
- `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/tenant-migrations/tenant-migrations.controller.ts` — endpoint `status`, `deploy`, `deploy/stream`, `views/apply`, `resolve`, และ `resolvePreStreamErrorStatus()` (§4.4)
- `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/tenant-migrations/tenant-migrations.service.ts` — RPC proxy บาง ๆ ของ gateway ไปยัง micro-business
- `../carmen-turborepo-backend/apps/backend-gateway/src/auth/guards/tenant-migration.guard.ts` — guard permission-หรือ-deploy-token (§4.2); `../carmen-turborepo-backend/apps/backend-gateway/src/libs/config.env.ts:209-210` — `TENANT_MIGRATION_API_ENABLED`/`TENANT_DEPLOY_TOKEN` (§3.4)
- `../carmen-turborepo-backend/apps/micro-business/src/authen/tenant_migration/tenant_migration.service.ts` — `status`, `deploy`, `deployStream`, `deployAllStream`, `resolve`, `resolveConnection`, lock `runningBuIds`/`isBatchRunning` (§3.3)
- `../carmen-turborepo-backend/apps/micro-business/src/tenant/tenant.service.ts` — `resolveConnectionForBusinessUnit()` / `resolveConnection()`, ตัวสร้าง connection string จาก pool+schema (§4.3)
- `../carmen-turborepo-backend-bruno/collections/carmen-inventory/platform/tenant-migrations/` — Bruno request สำหรับ `status`, `deploy`, `deploy-stream`, `resolve`

## 7. หน้าย่อยของโมดูลนี้

- [Data Model](/th/backstage/tenant-migrations/data-model) — เหตุผลที่ไม่มี entity สถานะ migration ที่ persist, ฟิลด์ `tb_business_unit`/`tb_database_pool` ที่ใช้ resolve tenant connection, และ edge case ในการ resolve นั้น
