---
title: การย้ายเทแนนต์ (Tenant Migrations)
description: หน้าจอระดับ fleet ที่ตรวจสอบและ apply schema migration ของฐานข้อมูล tenant ที่ค้างอยู่ทั่วทุก business unit ทุก action ถูกจำกัดเฉพาะ super-admin
published: true
date: '2026-09-06T23:45:00.000Z'
tags: book/platform, tenant-migrations
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# การย้ายเทแนนต์ (Tenant Migrations)

> **At a Glance**
> **หน้าจอ:** `TenantMigrationManagement` (+ `FleetSync`, `DeployConsole`) ที่ `/tenant-migrations` เพิ่มโดย `../carmen-platform` commit `c59bbba` (2026-06-30) &nbsp;·&nbsp; **Route gate:** `cluster.read` — reuse มาจาก [Clusters](/th/platform/clusters) key เดียวกับที่ gate [Business Units](/th/platform/business-units) ด้วย — บวก feature flag `tenant_migrations` ของโมดูลนี้เองบน `PrivateRoute` ตรวจหลัง permission gate &nbsp;·&nbsp; **Action gate:** ทุก action Check / Apply / Deploy-all ถูกจำกัดเพิ่มเป็น `isSuperAdmin` ฝั่ง frontend และที่ backend `TenantMigrationGuard` ต้องมี session ระดับ super-admin **หรือ** header `x-deploy-token` ที่ตรงกัน &nbsp;·&nbsp; **Sidebar:** มีรายการ "Tenant Migrations" เป็นของตัวเองในกลุ่ม Organization (`src/components/nav/platformNav.ts:14`) — ไม่ได้ซ้อนอยู่ใต้ Business Units หรือ Clusters แม้จะใช้ permission key ร่วมกัน &nbsp;·&nbsp; **สวิตช์ปิด/เปิด:** `TENANT_MIGRATION_API_ENABLED` เป็น env var ที่ **ปิดโดยดีฟอลต์** — ทุก endpoint รวมถึง status check จะ 403 จนกว่าจะตั้งเป็น `true` อย่างชัดเจน &nbsp;·&nbsp; **ความสัมพันธ์:** มุมมองตารางระดับ fleet ของความสามารถ backend เดียวกับที่การ์ด `TenantMigrationCard` ต่อ BU บน [Business Units — UI Screens](/th/platform/business-units/ui-screens) §4.5 ทำทีละ BU &nbsp;·&nbsp; **e2e suite:** ไม่มี — ทุกข้อความในหน้านี้มาจากการอ่าน source โดยตรง ไม่ใช่จาก test coverage

## 1. ภาพรวม

Tenant Migrations คือคอนโซลระดับ fleet ของแพลตฟอร์มสำหรับ Prisma migration ระดับ schema ของ tenant ที่ฐานข้อมูลของทุก business unit ต้องรับไปในที่สุด หน้านี้อยู่ที่ route ระดับบนสุดของตัวเอง `/tenant-migrations` พร้อมรายการ sidebar ของตัวเองในกลุ่ม Organization — ไม่ได้ซ้อนอยู่ใต้ [Business Units](/th/platform/business-units) หรือ [Clusters](/th/platform/clusters) แม้ route ของมันจะ reuse permission key `cluster.read` และรายการแถวก็มาจาก `businessUnitService.getAll({ perpage: 1000, sort: 'code:asc' })` เดียวกับที่หน้ารายการ Business Units ใช้ `TenantMigrationManagement.tsx` แสดงรายชื่อ business unit ทุกตัวที่ call นี้คืนมาในตารางเดียว ให้ operator ตรวจสอบ apply หรือ deploy แบบ batch migration ที่ค้างได้ทั่วทั้ง fleet จากหน้าจอเดียว — เป็นความสามารถ backend เดียวกับที่การ์ด `TenantMigrationCard` ต่อ BU บน[หน้าแก้ไข Business Units](/th/platform/business-units/ui-screens) §4.5 ทำทีละ BU (§3.5)

การเข้าถึงหน้านี้และเห็นตาราง BU ต้องมีแค่ `cluster.read` บวก feature flag `tenant_migrations` ของโมดูลนี้เอง — เป็น gate ที่กว้างและใช้ร่วมกับอีกสองรายการ sidebar ที่ใช้ permission เดียวกัน ([clusters](/th/platform/clusters), [business-units](/th/platform/business-units)) ส่วน operation การ migrate จริง ๆ เป็นอีกเรื่องหนึ่งที่แคบกว่ามาก: ฝั่ง frontend disable ทุกปุ่ม — รวมถึง Check ที่เป็นแค่การอ่าน — สำหรับผู้ที่ไม่ใช่ super-admin และฝั่ง backend `TenantMigrationGuard` ก็ยืนอยู่หน้า controller ทั้งตัวไม่ว่าฝั่ง frontend จะทำอะไร (§4) เดิมเนื้อหาของโมดูลนี้เคยอยู่เป็นหน้าย่อยของ Business Units (`business-units/tenant-migrations.md`) — ถูกย้ายมาที่นี่เพราะ `/tenant-migrations` มี route, nav entry, และ feature key (`tenant_migrations`, แยกจาก `business_units`) เป็นของตัวเองมาโดยตลอด — หน้า [Business Units](/th/platform/business-units) ตอนนี้ลิงก์มาที่นี่สำหรับภาพรวมระดับ fleet และเก็บเฉพาะเรื่องการ์ดต่อ BU ที่ฝังอยู่ไว้บนหน้าย่อยของตัวเอง

## 2. บริบททางธุรกิจ

การ deploy ของ Carmen หนึ่งชุดรัน schema ที่ Prisma จัดการหนึ่งชุดต่อหนึ่ง business unit (property/โรงแรม) ทุกชุดใช้ migration history ร่วมกันชุดเดียวที่นิยามไว้ใน package `@repo/prisma-shared-schema-tenant` เดียว เมื่อใดก็ตามที่ package นั้นได้ migration ใหม่ ทุก tenant schema ในทุก cluster ต้องรัน `prisma migrate deploy` ก่อนที่โค้ดแอปพลิเคชันที่สอดคล้องกันจะพึ่งพา column/table ใหม่ได้ — และผู้ให้บริการโรงแรมหนึ่งรายอาจมีหลายสิบ property ที่ rollout คนละจังหวะกัน หากไม่มีมุมมองระดับ fleet operator ต้องเปิดหน้าแก้ไขของแต่ละ BU แล้วเช็คแท็บ Technical ทีละตัว หน้าจอนี้จึงมีไว้เพื่อตอบคำถาม "tenant ตัวไหนตามหลัง และตามหลังแค่ไหน" ในมุมมองเดียว (`FleetSync`, §3.1) และให้ super-admin (หรือ pipeline CI/CD ผ่าน deploy token, §4.2) ผลักดันทุกตัวไปข้างหน้า — หรือไล่ทั้ง fleet ในครั้งเดียว — โดยไม่ต้องออกจากหน้า

## 3. แนวคิดสำคัญ

### 3.1 Layout ของหน้าจอ

- **Header** — `PageHeader` หัวข้อ "Tenant migrations" คำบรรยาย "Check which tenant databases are behind on schema migrations, and roll them out."
- **การ์ดสรุป Fleet Sync** (`FleetSync`) — การ์ดแนวนอนแสดง `{จำนวนที่ in-sync} / {BU ทั้งหมด}` ด้วยตัวเลขขนาดใหญ่แบบ monospace, progress bar สามสี (เขียว/เหลือง/แดง) สำหรับ in-sync/behind/errored และแถว legend พร้อมจำนวน (ตัวเลขรวม migration ที่ค้างจะโผล่ก็ต่อเมื่อไม่ใช่ศูนย์) ก่อนรัน "Check all" ครั้งแรกจะแสดง "Not checked yet" แทน bar ช่อง action มีปุ่ม **Check all**, **Deploy all**, และ **Export**
- **Deploy Console** (`DeployConsole`) — render เฉพาะตอนที่ batch "Deploy all" กำลังทำงาน: panel รูปแบบ terminal สีเข้ม พร้อม progress bar (applied/total ของ BU ที่กำลัง migrate), code ของ BU ปัจจุบัน และ log แบบ scroll ที่มีสีต่อ BU ที่เสร็จแล้ว (เขียวสำหรับ applied/up-to-date, แดงสำหรับ failed)
- **ช่องค้นหา** — filter ฝั่ง client เหนือตาราง BU (code/name)
- **ตาราง BU** (`DataTable`, 3 คอลัมน์ sticky ซ้าย) — **Code** (ลิงก์ไป `/business-units/:id/edit`), **Name**, **Status** (badge — "In sync" / "N behind" / "Error" / "Not checked" บวกบรรทัด inline "Applying X/Y … ชื่อ migration ปัจจุบัน" ระหว่าง Apply ต่อแถวกำลัง stream หรือ error message inline), **Last checked** (HH:MM:SS ตามเวลา client) และคอลัมน์ row-actions (ไอคอน **Check** และ **Apply** ที่แสดงเฉพาะแถวที่มี migration ค้าง) ไม่มีคอลัมน์ Pending บนหน้าจอ — badge Status พูดจำนวนอยู่แล้ว ("3 behind" / "In sync") ไฟล์ CSV export (ด้านล่าง) ยังมีคอลัมน์นี้ เพราะที่นั่นตัวเลขเปล่า ๆ มีประโยชน์จริงสำหรับคำนวณต่อ
- **Empty state** — "No business units" พร้อมปุ่ม "Go to Business Units" แสดงเมื่อ fleet มี BU เป็นศูนย์ (ไม่ใช่ migration ค้างเป็นศูนย์)
- `DevDebugSheet` (dev เท่านั้น) แสดง response ดิบของ `GET /api-system/business-units`

หากรายการ BU ถูก paginate ฝั่ง server เกินกว่าที่ fetch เดียว (`perpage: 1000`) จะคืนมา จะมี banner เตือน "Showing N of M business units. Increase the page size to see all." — หน้านี้ไม่ paginate ต่อเพื่อดึงส่วนที่เหลือเอง

### 3.2 Action และการเรียก backend

| Action | Trigger ของ UI | เรียก Backend | Gate |
|---|---|---|---|
| แสดงรายการ business unit | โหลดหน้า | `businessUnitService.getAll({ perpage: 1000, sort: 'code:asc' })` | `cluster.read` |
| Check (แถวเดียว) | ไอคอน row action | `GET /api-system/tenant/migrations/:bu_id/status` | Frontend: disable พร้อม tooltip "Super-admin required." เมื่อ `!isSuperAdmin` Backend: `TenantMigrationGuard` (§4.2) |
| Check all | ปุ่มบนการ์ด Fleet Sync | เรียก `GET .../status` ต่อ BU จำกัด concurrency ที่ 4 พร้อมกัน (`mapWithConcurrency`) | เหมือน Check |
| Apply (แถวเดียว) | ไอคอน Apply ต่อแถว → confirm dialog | `POST /api-system/tenant/migrations/:bu_id/deploy/stream` (NDJSON progress) | เหมือน Check |
| Deploy all | ปุ่มบนการ์ด Fleet Sync → confirm dialog | `POST /api-system/tenant/migrations/all/deploy/stream` (NDJSON progress ทีละ BU ฝั่ง server) | เหมือน Check |
| Export | ปุ่มบนการ์ด Fleet Sync | CSV ฝั่ง client จาก code/name/status/pending/last-checked ของ state ที่โหลดไว้แล้ว | ไม่มี — export สิ่งที่ตารางแสดงอยู่ปัจจุบัน |

ฝั่ง frontend ไม่เคยเรียก `POST /api-system/tenant/migrations/:bu_id/deploy` แบบไม่ stream เลย — `tenantMigrationService.deploy()` ถูกนิยามไว้แต่ไม่มีผู้เรียกใน `carmen-platform` เลย (ยืนยันจาก grep ทุกจุดที่เรียก `tenantMigrationService.`) ทั้ง `TenantMigrationManagement` และการ์ด `TenantMigrationCard` ต่อ BU รัน apply ผ่าน streaming variant เท่านั้น

**ป้ายของปุ่ม Deploy all ขึ้นอยู่กับ state โดยตั้งใจ** (`../carmen-platform` commit `dbb1107`, 2026-09-01 ซึ่งถอดคอลัมน์ Pending บนหน้าจอออกไปด้วยในคราวเดียวกัน): ปุ่มใช้ `variant={behindCount > 0 ? 'destructive' : 'outline'}` — เป็นสีแดงเฉพาะเมื่อมี BU ที่ behind มากกว่าศูนย์ พร้อมป้ายที่บอกรัศมีของตัวเอง ("Deploy 3 behind" แทน "Deploy all" เฉย ๆ) และถูก disable (ไม่ใช่แค่จางลง) เมื่อตรวจแล้วพบว่าไม่มีอะไรให้ deploy เหตุผลจาก comment ของปุ่มเองคือโดเมนนี้ไม่มี endpoint cancel/rollback ปุ่มที่ดูเร่งด่วนที่สุดบนจอจึงไม่ควรเป็นปุ่มที่ operator ย้อนกลับไม่ได้มากที่สุด

### 3.3 สถานะของ migration และสิ่งที่ทำให้มันเดินหน้าหรือค้าง

ไม่มีแถวสถานะ migration ที่ persist อยู่ใน schema ของแพลตฟอร์มเองเลย (ดู [Data Model](/th/platform/tenant-migrations/data-model) §2) — ทุกสถานะบนหน้าจอนี้ถูกคำนวณสด ๆ ต่อ request โดยการเรียก Prisma CLI ไปยังฐานข้อมูล tenant เป้าหมาย แล้วจับ pattern จาก text ที่มันพิมพ์ออกมา:

- **`up_to_date`** — output ของ `prisma migrate status` ตรงกับ `/up to date/i`
- **`has_pending`** — output ตรงกับ `/not yet been applied/i`; ชื่อ migration ที่ค้างแต่ละตัวถูกดึงออกจาก output เดียวกันด้วย pattern ทั่วไป `\d{14}_[a-z0-9_]+`
- **กรณีอื่นที่ exit code ไม่เป็นศูนย์** จะตกไปเป็น error ธรรมดา (`Result.error`) — โค้ดนี้ไม่มีการจำแนก "ค้าง" หรือ "ล้มเหลว" เป็นพิเศษเลย migration ที่เคยล้มเหลวระหว่าง `migrate deploy` จะถูกรายงานด้วยคำที่ Prisma CLI ใช้เอง ซึ่ง service นี้ไม่ได้จับ pattern พิเศษให้ — มันจะไม่ตรงทั้ง `has_pending` และ `up_to_date` และจะโผล่มาเป็น error ทั่วไปของการ check status

**การทำให้ migration เดินหน้า** คือการรัน `prisma migrate deploy --schema <schema>` กับ connection string ของ tenant ที่ resolve แล้ว — connection ที่ resolve แล้วมาจาก `tb_business_unit.db_schema` บวกแถว `tb_database_pool` ที่ผูกไว้ (host/port/database/username และรหัสผ่านที่ถอดรหัสแล้ว) **ไม่ใช่** จาก column `db_connection` ที่ไม่มีอยู่บน `tb_business_unit` อีกต่อไป (§4.3 ชี้ comment ที่ล้าสมัยใน frontend service file ซึ่งยังบรรยายกลไกเดิม) เมื่อสำเร็จ บรรทัด `Applying migration \`name\`` ของ CLI จะถูก parse เพื่อสร้างรายการ "applied" ที่ stream กลับมาเป็น `applying` progress event; event `done` ที่ `already_up_to_date: applied.length === 0` จะปิด stream

**สิ่งที่ `deploy` ที่ล้มเหลวทิ้งไว้เบื้องหลัง:** exit code ที่ไม่เป็นศูนย์จาก `prisma migrate deploy` ถูกรายงานเป็น stream `error` event (หรือ HTTP error บน path ที่ไม่ stream) พร้อม output ของ CLI ที่ผ่านการกรองข้อมูลอ่อนไหวแล้ว — operation จะไม่ถูก retry และไม่มีอะไรใน codebase นี้ตรวจสอบว่า migration *ตัวไหน* ล้มเหลว การรันต่อ BU และแบบ batch ถูกป้องกันด้วย in-memory lock (`runningBuIds` ต่อ BU, `isBatchRunning` สำหรับทั้ง fleet) ที่คืน 409 "already running" ขณะถูกถืออยู่ แต่ทั้งสอง lock ไม่มีอายุยืนกว่า request เดียว — ไม่มีอะไรจดจำว่า BU ไหนถูกทิ้งไว้กลาง migration เมื่อ process เดินหน้าต่อไปแล้ว endpoint เดียวที่สร้างมาเพื่อล้าง migration ที่ค้างจริง ๆ คือ `POST :bu_id/resolve` (`prisma migrate resolve --applied|--rolled-back <name>`, §4.4) — ยืนยันด้วย grep แล้วว่าไม่มีโค้ด frontend จุดใดใน `carmen-platform` เรียกมันเลย operator ที่เจอ migration ค้างวันนี้จึงไม่มี path ผ่าน UI ในการแก้ไข

**Deploy-all ป้องกันได้แค่ BU *ถัดไป* ไม่ใช่ตัวที่กำลังทำอยู่** comment ของ `deployAllStream` เอง (`tenant_migration.service.ts:504-518` ใน `../carmen-turborepo-backend-v2`) ระบุว่าการยกเลิกหยุดแค่ batch จากการเริ่ม tenant ถัดไป — BU ที่กำลัง migrate อยู่ตอน client ตัดการเชื่อมต่อจะทำงานต่อจนเสร็จ (หรือจนถึง timeout ของตัวเอง) ไม่ว่ากรณีใด — `AbortController` ของ frontend ตอน unmount หยุดแค่ browser จากการรอฟัง ตาม doc comment บน `tenantMigrationService._streamDeploy` ไม่มี endpoint cancel/rollback สำหรับโดเมนนี้เลย

### 3.4 สวิตช์ปิด/เปิด และ path ของ CI deploy-token

ทั้ง controller ของ tenant-migration อยู่หลัง `TENANT_MIGRATION_API_ENABLED` ซึ่งเป็น environment-variable boolean ที่ **ปิดโดยดีฟอลต์** เมื่อไม่ได้ตั้งค่า (`boolFromString(false)`, `../carmen-turborepo-backend-v2/apps/backend-gateway/src/libs/config.env.ts:222`) — ทุกการเรียก รวมถึง status check ธรรมดา จะ 403 ด้วย "Tenant migration API is disabled" จนกว่า operator จะตั้งค่าเป็นสตริง `true` อย่างชัดเจน นี่เป็น env var ธรรมดา ต่างจากโมดูล [Platform Migrations](/th/platform/platform-migrations) ที่ชื่อคล้ายกันแต่แยกกัน ซึ่งสวิตช์เปิด/ปิดของตัวเองถูกย้ายไปอยู่ใน `tb_platform_config` (`platform_migration.api_enabled`) — comment ที่อยู่เหนือ `TENANT_MIGRATION_API_ENABLED` ใน `config.env.ts` โดยตรงพูดถึงโมดูลอื่นนั้น ไม่ใช่โมดูลนี้ สวิตช์ของโมดูลนี้ยังไม่ได้ย้ายไปไหน

นอกจาก session ระดับ super-admin แล้ว backend ยังรับ header `x-deploy-token` (เปรียบเทียบด้วย `timingSafeEqual` เทียบกับ `TENANT_DEPLOY_TOKEN`) เป็น credential ทางเลือก ออกแบบไว้ให้ pipeline CI/CD สั่ง deploy ได้โดยไม่ต้องมี session ของมนุษย์ หน้าจอ SPA นี้ไม่เคยใช้ path นั้นเลย — authenticate ในฐานะ operator ที่ signed-in เท่านั้นเสมอ — ดังนั้น path ของ deploy-token จึงมองไม่เห็นจาก UI นี้เลย การใช้มันต้องเรียก API ตรง ๆ (เช่นผ่าน Bruno collection, §6)

### 3.5 ความสัมพันธ์กับหน้าแก้ไข Business Units

- การ์ด `TenantMigrationCard` ต่อ BU บน [Business Units — UI Screens](/th/platform/business-units/ui-screens) §4.5 และหน้านี้เรียก `tenantMigrationService` (`getStatus`, `deployStream`, `deployAllStream`) และ backend controller **เดียวกัน** — มี implementation ของ "ตรวจสอบสถานะ" และ "apply migration" เพียงชุดเดียว ที่แสดงผลจากสองหน้าจอ [Business Units — Tenant Migrations](/th/platform/business-units/tenant-migrations) ตอนนี้เป็น pointer สั้น ๆ ที่ครอบคลุมเฉพาะการ์ดที่ฝังอยู่นั้น หน้านี้คือเรื่องเต็มของหน้าจอระดับ fleet
- ทั้งสองหน้าจอ gate เหมือนกันด้วย `isSuperAdmin` สำหรับ**ทุก** action รวมถึง Check — ยืนยันตรงจากการอ่าน `TenantMigrationCard.tsx` เอง (`actionsDisabled` ใช้กับปุ่ม Check-status เช่นเดียวกับปุ่ม Apply) ไม่ใช่แค่จาก `TenantMigrationManagement.tsx` เท่านั้น gate เดียวที่ตารางนี้**ไม่มี**แต่การ์ดมีคือ `hasDbConnection` (BU มี pool + schema ตั้งค่าไว้แล้วหรือยัง): การ์ด disable ปุ่มล่วงหน้าเมื่อเงื่อนไขนี้เป็นเท็จ ในขณะที่ตารางนี้ปล่อยให้ operator กด Check/Apply บนแถวไหนก็ได้ แล้วแสดง error ที่ `resolveConnection` โยนออกมาตามจริง (§3.3) เมื่อ request ถูกส่งไปแล้วเท่านั้น
- **ไม่มีลิงก์ในแอป** ระหว่างสองหน้าจอนี้ในทิศทางใดเลย — ยืนยันจากการอ่าน source ของทั้งสอง component ทางเดียวที่จะมาหน้านี้คือรายการ sidebar "Tenant Migrations" หรือพิมพ์ URL เอง คอลัมน์ "Code" ของหน้านี้พาไปหน้าแก้ไข BU นั้นตรง ๆ ไม่ใช่เวอร์ชัน filter ของตัวเอง

## 4. บทบาทและสิทธิ์

> **Key-reuse gotcha เดียวกับ Business Units:** `cluster.read` ที่ route `/tenant-migrations` ต้องการ ไม่ได้บอกใบ้เลยว่ามันเปิดหน้าจอนี้ได้ — key เดียวกันเปิด [Clusters](/th/platform/clusters) และ [Business Units](/th/platform/business-units) ด้วย feature flag `tenant_migrations` (§4.1) เป็นสวิตช์เดียวที่ปิดหน้าจอนี้ได้โดยไม่กระทบอีกสองหน้า

### 4.1 เมทริกซ์ด่านฝั่ง frontend

| จุด | ประเภท Gate | Key | หมายเหตุ |
|---|---|---|---|
| route `/tenant-migrations` | `requiredPermission` + `feature` | `cluster.read` + `tenant_migrations` | Key ที่ reuse มา บวก feature flag ของตัวเอง |
| รายการ sidebar "Tenant Migrations" | filter ด้วย `permission` + `feature` | `cluster.read` / `tenant_migrations` | `navGroup.organization`, `src/components/nav/platformNav.ts:14` |
| ปุ่ม Check ต่อแถว | `disabled={!!disabledReason \|\| busy \|\| batchRunning}` | `isSuperAdmin` | Tooltip: "Super-admin required." |
| ปุ่ม Apply ต่อแถว (render เฉพาะเมื่อ `has_pending`) | `disabledReason` เดียวกัน | `isSuperAdmin` | มี confirm dialog ก่อนเริ่ม stream |
| ปุ่ม Check all / Deploy all | `disabledReason` เดียวกัน บวกการ disable ตาม state เพิ่มเติม (§3.2) | `isSuperAdmin` | Deploy all ยัง disable เองเมื่อไม่มีอะไรค้าง |
| ปุ่ม Export | `disabled={loading \|\| bus.length === 0 \|\| anyBusy}` | ไม่มี | Export เฉพาะ state ที่ client โหลดไว้แล้วเท่านั้น |

### 4.2 การบังคับใช้ฝั่ง backend

ทุก endpoint ระดับ migration อยู่หลัง `TenantMigrationGuard` (`../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/tenant-migration.guard.ts`) ใช้ครั้งเดียวกับทั้ง controller ผ่าน `@UseGuards(TenantMigrationGuard)` ต้องการ **หนึ่งใน**: header `x-deploy-token` ที่ตรงกัน (เทียบแบบ constant-time, §3.4) หรือ session Keycloak ระดับ super-admin (`KeycloakGuard` แล้วตามด้วย `PlatformSuperAdminGuard` ต้องผ่านทั้งคู่) — ไม่มี path ผ่าน `cluster.*` หรือ RBAC permission อื่นใดเข้าถึงได้เลย guard ยังบังคับ `TENANT_MIGRATION_API_ENABLED` ก่อนตรวจ credential ทั้งสองแบบด้วย ดังนั้น flag ที่ปิดจะ 403 ไม่ว่าใครจะเรียกก็ตาม ค่า `disabledReason = !isSuperAdmin ? 'Super-admin required.' : null` ของ frontend จึงเป็นความสะดวกฝั่ง UI ที่ตรงกับ (ไม่ใช่แทนที่) การตรวจสอบจริงฝั่ง server — ต่างจากช่องว่างที่ยืนยันแล้วของ [SQL Workbench](/th/platform/sql-workbench) และ [Query Dataset](/th/inventory/system-config/query-dataset) guard ของ tenant-migrations ฝั่ง backend ไม่สามารถถูก bypass ได้ด้วยการเรียก API ตรง ๆ จาก session ที่ไม่ใช่ super-admin

### 4.3 ยืนยันซ้ำกับ source ปัจจุบัน: comment ที่ล้าสมัย แก้ไขแล้ว

ไฟล์ `tenantMigrationService.ts` ฝั่ง frontend ยังมี comment นี้อยู่ ไม่เปลี่ยนแปลงตั้งแต่เขียนครั้งแรก (`../carmen-platform` commit `8fc1124`, 2026-06-29): *"The backend resolves the target tenant DB from the BU's stored db_connection."* คำบรรยายนี้ถูกแซงหน้าโดย `../carmen-turborepo-backend-v2` commit `af2437074` (2026-08-13) ซึ่งย้ายการ resolve connection จาก column `tb_business_unit.db_connection` (JSON) ที่ถูกถอดออกแล้ว ไปเป็น `db_schema` บวกแถว `tb_database_pool` ที่ผูกไว้ (ยืนยันจากการอ่าน `resolveConnection()` ใน `apps/micro-business/src/tenant/tenant.service.ts` โดยตรง — ไม่มี path โค้ดใดใน tree ปัจจุบันอ่าน `db_connection` เพื่อจุดประสงค์นี้อีกแล้ว) comment ไม่เคยถูกอัปเดตให้ตรงกัน มันคือหนี้เอกสารในตัว source เอง ไม่ใช่คำบรรยายพฤติกรรมปัจจุบัน — หน้านี้บรรยายกลไก pool/schema ที่โค้ดรันจริง (§3.3)

### 4.4 ยืนยันซ้ำกับ source ปัจจุบัน: การ map error status ที่ตายแล้วบน stream path

ตัวจัดการ `deployStream` ฝั่ง gateway map ความล้มเหลวก่อนเริ่ม stream เป็น HTTP status ด้วยการจับ pattern ข้อความ error (`resolvePreStreamErrorStatus()`, `tenant-migrations.controller.ts`) เพิ่มเข้ามาใน commit `4ca923229` (2026-06-30) ตอนที่ความล้มเหลวของ `resolveConnection` ยังอ่านว่า "no database connection configured" / "unsupported database provider" การ refactor เดียวกัน `af2437074` (§4.3) เปลี่ยนข้อความที่โยนออกมาจริงเป็น "is not linked to a database pool", "has no database schema configured", "has been deleted", และ "is inactive" — ไม่มีข้อความไหนตรงกับ regex ของ `resolvePreStreamErrorStatus` เลย ผลที่เกิดขึ้นจริง: ตั้งแต่ 2026-08-13 เป็นต้นมา BU ที่ไม่ได้ผูก pool, ไม่ได้ตั้ง schema, หรือ pool ถูกปิด/ลบ จะได้ HTTP 500 กลับจาก `/deploy/stream` (ค่า fallback ของ function เมื่อข้อความไม่ตรง) แทนที่จะเป็น 422 ตามที่เอกสารระบุ ตัวข้อความเองยังไปถึง operator ถูกต้อง (`errorMsg` ต่อแถวของ frontend แสดง text ดิบไม่ว่า status code จะเป็นอะไร และ `handleMigrationError` จะแยกเฉพาะ 403/409 เป็นพิเศษเท่านั้น) ดังนั้นนี่คือช่องว่างจริงในสัญญา status code ของ API ไม่ใช่ช่องว่างในสิ่งที่ operator เห็นบนจอ `GET /status` และ `POST /deploy` แบบไม่ stream ไม่ได้รับผลกระทบ — คืน status ผ่าน `StdResponse.fromResult()`'s generic `ErrorCode` mapping ไม่ใช่ regex ตัวนี้

## 5. โมดูลที่เกี่ยวข้อง

- [Business Units](/th/platform/business-units) — ทุกแถวบนหน้านี้คือ `business_unit` หนึ่งตัว หน้าย่อย [Tenant Migrations](/th/platform/business-units/tenant-migrations) ที่นั่นครอบคลุมเฉพาะการ์ด `TenantMigrationCard` ต่อ BU ที่ฝังอยู่ ไม่ใช่หน้าจอระดับ fleet นี้
- [Clusters](/th/platform/clusters) — ที่มาของ permission key `cluster.read` ที่ route และ nav entry ของโมดูลนี้ reuse มา
- [Database Pools](/th/platform/database-pools) — แถว `tb_database_pool` ที่ `database_pool_id` ของ BU ชี้ไป pool ที่ถูกปิดหรือ soft-delete ทำให้ connection ของ tenant นั้น resolve ไม่ได้ (§3.3, §4.4)
- [Platform RBAC](/th/platform/rbac) — โมเดล permission เบื้องหลัง `cluster.read` และ (`rbac/permissions.md`) ตาราง gate ระดับ route ที่มี `/tenant-migrations` อยู่ด้วย
- [SQL Workbench](/th/platform/sql-workbench) — คอนโซลฐานข้อมูลต่อ tenant อีกตัวที่ใกล้เคียงกับ super-admin เพิ่มมาในช่วงเดียวกัน §4.2 ข้างต้นเทียบช่องว่าง permission จริงของมันกับของโมดูลนี้ (ที่ bypass ไม่ได้)

## 6. แหล่งอ้างอิง

- `../carmen-platform/src/pages/TenantMigrationManagement.tsx` — หน้า fleet แบบ standalone: state, คอลัมน์, handler ของ Check/Apply/Deploy-all/Export, การ cleanup abort-on-unmount ของ `activeStreamControllersRef`
- `../carmen-platform/src/pages/tenantMigration/{FleetSync,DeployConsole}.tsx` — การ์ดสรุปและ console สำหรับ batch-deploy แบบสด
- `../carmen-platform/src/services/tenantMigrationService.ts` — `getStatus`, `deploy` (ไม่มีผู้เรียก), `deployStream`, `deployAllStream`, และ doc comment เรื่อง semantics ของการ abort stream (§4.3 ชี้บรรทัด `db_connection` ที่ล้าสมัย)
- `../carmen-platform/src/components/TenantMigrationCard.tsx` — การ์ดต่อ BU ที่บันทึกไว้ใน [Business Units — UI Screens](/th/platform/business-units/ui-screens) §4.5 ใช้ service เดียวกัน (§3.5)
- `../carmen-platform/src/App.tsx:251-256` — route `/tenant-migrations` (`requiredPermission="cluster.read"` บวก `feature="tenant_migrations"`)
- `../carmen-platform/src/components/nav/platformNav.ts:14` — รายการ sidebar (`permission: 'cluster.read'`, `feature: 'tenant_migrations'`, `groupKey: 'navGroup.organization'`)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/tenant-migrations/tenant-migrations.controller.ts` — endpoint `status`, `deploy`, `deploy/stream`, `resolve`, และ `resolvePreStreamErrorStatus()` (§4.4)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/tenant-migrations/tenant-migrations.service.ts` — RPC proxy บาง ๆ ของ gateway ไปยัง micro-business
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/tenant-migration.guard.ts` — guard super-admin-หรือ-deploy-token (§4.2); `../carmen-turborepo-backend-v2/apps/backend-gateway/src/libs/config.env.ts:222` — `TENANT_MIGRATION_API_ENABLED`/`TENANT_DEPLOY_TOKEN` (§3.4)
- `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/tenant_migration/tenant_migration.service.ts` — `status`, `deploy`, `deployStream`, `deployAllStream`, `resolve`, `resolveConnection`, lock `runningBuIds`/`isBatchRunning` (§3.3)
- `../carmen-turborepo-backend-v2/apps/micro-business/src/tenant/tenant.service.ts` — `resolveConnectionForBusinessUnit()` / `resolveConnection()`, ตัวสร้าง connection string จาก pool+schema (§4.3)
- `../carmen-turborepo-backend-bruno/collections/carmen-inventory/platform/tenant-migrations/` — Bruno request สำหรับ `status`, `deploy`, `deploy-stream`, `resolve`

## 7. หน้าย่อยของโมดูลนี้

- [Data Model](/th/platform/tenant-migrations/data-model) — เหตุผลที่ไม่มี entity สถานะ migration ที่ persist, ฟิลด์ `tb_business_unit`/`tb_database_pool` ที่ใช้ resolve tenant connection, และ edge case ในการ resolve นั้น
