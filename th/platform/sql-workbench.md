---
title: SQL Workbench
description: คอนโซล admin (/sql-workbench เพิ่มเมื่อ 2026-07-09) ที่รัน SQL ใด ๆ ก็ได้ และ browse/สร้าง/drop view, stored procedure, function กับฐานข้อมูลของ tenant ที่เลือก — ยืนยันว่าเป็น frontend ของ carmen-platform สำหรับ backend service ที่บันทึกไว้ในหน้า Query Dataset ของ Inventory book
published: true
date: 2026-07-29T09:46:00.000Z
tags: platform/sql-workbench, carmen-software
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# SQL Workbench

> **At a Glance**
> **หน้าจอ:** `SqlWorkbench` (`/sql-workbench` เพิ่มเมื่อ 2026-07-09) &nbsp;·&nbsp; **Route gate:** `sql_workbench.read` &nbsp;·&nbsp; **Write gate:** `sql_workbench.manage` — ควบคุมแยกว่า Run/Save/Drop จะ render หรือไม่ &nbsp;·&nbsp; **Sidebar:** รายการ "SQL Workbench" ในกลุ่ม Platform &nbsp;·&nbsp; **Backend:** controller family `config_sql-query` ตัวเดียวกับที่บันทึกไว้ฝั่ง backend ใน [Query Dataset](/th/inventory/system-config/query-dataset) — หน้านี้คือ frontend ที่ยืนยันแล้วของ service นั้น

## 1. ภาพรวม

SQL Workbench คือคอนโซล SQL ต่อ tenant: เลือก business unit หนึ่งตัว, browse table/view/procedure/function ที่มีอยู่จริง, โหลด definition ของ object ที่มีอยู่แล้วเข้า editor, รัน SQL ใด ๆ กับมัน, และ save เนื้อหาใน editor กลับเป็น view/procedure/function ใหม่หรือแทนที่ของเดิม เข้าถึงได้จากกลุ่ม Platform ใน sidebar และเป็นหนึ่งในหน้าจอใหม่ล่าสุดของ carmen-platform (เพิ่มเมื่อ 2026-07-09 พร้อมกับ [Tenant Migrations](/th/platform/business-units/tenant-migrations) และ [Report Form Groups](/th/platform/report-templates/form-groups) ในฐานะสามหน้าจอ Bucket-A ล่าสุดที่รอบ resync นี้ครอบคลุม)

นี่ไม่ใช่ความสามารถ backend ใหม่ — แต่เป็น **frontend** ใหม่ของ backend เดิม หน้า [Query Dataset](/th/inventory/system-config/query-dataset) ของ Inventory book บันทึก backend controller family เดียวกันเป๊ะ (`config_sql-query.controller.ts` เรียก `SqlQueryService.execute/saveDdl/listDbObjects/getDbObjectDefinition/dropDbObject` ใน `micro-business`) และในรอบตรวจสอบล่าสุดของหน้านั้นสรุปว่า "no frontend screen that calls it" — การค้นหานั้น scope อยู่ที่ `carmen-inventory-frontend-react` ซึ่งยังจริงอยู่ แต่ไม่ได้ตรวจสอบ Platform admin product ที่แยกออกไปต่างหาก service layer ของ `SqlWorkbench.tsx` (`sqlQueryService.ts`) เรียก route `/api/config/:bu_code/sql-query/*` เดียวกันเป๊ะ ยืนยันว่าหน้าจอนี้คือคำตอบในโลกจริงของข้อค้นพบ "no confirmed frontend screen" ของหน้านั้น — เพียงแต่สร้างในอีก repository หนึ่งจากที่หน้านั้นค้นหาไว้

## 2. บริบททางธุรกิจ

backend service ถูกออกแบบมาให้ผู้เขียน report และ dashboard สร้าง view/function/procedure ที่ reusable ได้โดยตรงใน schema ของ tenant สำหรับให้ [Report Templates](/th/platform/report-templates) และ dashboard widget ใช้ในภายหลัง ก่อนที่หน้าจอนี้จะมี การทำแบบนั้นหมายถึงการเรียก API ตรง ๆ (เช่นผ่าน Bruno) โดยไม่มี UI ให้ browse SQL Workbench เปลี่ยนสิ่งนั้นให้เป็น workflow admin ธรรมดา: เลือก BU ดูว่ามีอะไรอยู่ใน schema แล้วบ้าง และวนซ้ำบน view/procedure/function โดยไม่ต้องออกจาก browser — ในขณะเดียวกันก็ทำหน้าที่เป็นคอนโซล SQL สำหรับ emergency-access ทั่วไปให้วิศวกร support ด้วย เพราะ `execute` รับ statement ได้ทุกชนิด

## 3. แนวคิดสำคัญ

- **BU switcher (`⌘/Ctrl+B`)**: workbench ทำงานกับฐานข้อมูล tenant ของ business unit เดียวเท่านั้นต่อครั้ง เลือกจาก dialog switcher ที่ค้นหาได้ (`BuSwitcher`) การสลับ BU จะทิ้ง object ที่โหลดอยู่ เนื้อหาใน editor และ result panel ใด ๆ — ไม่มีอะไรพกข้ามระหว่าง tenant
- **Connection bar**: แถบ header ที่แสดง code/name/cluster ของ BU ที่เลือกอยู่ตลอด, สีประจำ tenant ที่คงที่ (`buHueColor`), และ badge **read-only** / **read / write** ที่ขับเคลื่อนโดยว่า session ถือ `sql_workbench.manage` อยู่หรือไม่ — เพื่อให้ operator เห็นได้ทันทีว่าตนแก้ไข tenant ที่ชี้อยู่ได้หรือไม่ ไม่ใช่แค่ว่าชี้ไป tenant ไหน
- **DB object tree**: sidebar แสดงรายการ table, view, และ procedure/function ของ tenant ที่เลือก (จาก `GET .../sql-query/db-objects` ซึ่งอิง catalog query `pg_class`/`pg_proc` — ไม่มีตาราง registry แบบ `tb_*` ของตัวเองสำหรับโดเมนนี้ ดู [Query Dataset](/th/inventory/system-config/query-dataset) §5 สำหรับ catalog projection ที่แน่นอน) การคลิกแถว **table** จะ pre-fill editor ด้วย `SELECT * FROM <name> LIMIT 100;`; การคลิก **view/procedure/function** จะโหลด definition จริง (`pg_get_viewdef`/`pg_get_functiondef`) เข้า editor เป็น DDL `CREATE OR REPLACE …` พร้อม save ซ้ำได้ทันที
- **SQL editor**: editor แบบ CodeMirror (`SqlEditor`) ผูก `Ctrl/⌘+Enter` กับ Run ปุ่ม Run (และ shortcut Ctrl/⌘+Enter) จะถูกตัดออกทั้งหมด — ไม่ใช่แค่ disable — เมื่อ session ไม่มี `sql_workbench.manage` เพราะ frontend ไม่สามารถแยก `SELECT` แบบอ่านอย่างเดียวออกจาก DML/DDL ได้อย่างน่าเชื่อถือฝั่ง client (`sqlValidator.ts` ตัวเดียวกับที่ใช้ที่อื่นระบุชัดว่าเป็น UI-feedback เท่านั้น ไม่ใช่ security boundary) จึง gate ทั้ง executor แทนที่จะแสร้งเปิด path แบบอ่านอย่างเดียวที่ปลอดภัย
- **ฟิลด์ Object Name + Type**: เหนือ editor มี input ชื่อและ select View/Stored Procedure/Function ที่บอกว่า Save จะสร้างอะไร — จำเป็นสำหรับ `SELECT` เปล่าที่ save เป็น view; ถูกละเว้น (DDL `CREATE ... name` ของตัวเองชนะ) เมื่อ editor มี DDL `CREATE OR REPLACE` เต็มอยู่แล้ว
- **Result panel**: แสดงจำนวนแถว เวลาที่ใช้รัน (ms) และจำนวนคอลัมน์ใน header, ตารางที่ scroll ได้ (paginate ฝั่ง client ที่ 50/100/200/500 แถวต่อหน้า) พร้อมการตัดข้อความยาวต่อ cell และเครื่องหมาย `NULL` แบบ italic, ปุ่ม export CSV, และ — เมื่อ error — ข้อความ error ดิบพร้อม hint "error referenced line N" ที่ parse แบบ best-effort จากรูปแบบ error ทั่วไปของ Postgres
- **การยืนยัน statement ที่ทำลายข้อมูล**: ก่อนรัน `classifyStatements()` ฝั่ง client จะ flag keyword นำหน้าใด ๆ ที่เป็น `DROP`/`TRUNCATE`/`DELETE`/`UPDATE`/`ALTER`/`GRANT`/`REVOKE` ว่าทำลายข้อมูล และ flag เพิ่มเติมสำหรับ `UPDATE`/`DELETE` ที่ไม่มี `WHERE` clause ว่า "unguarded" — ทั้งสองแบบเปิด confirm dialog ที่ระบุ keyword ที่พบชัดเจน (และสำหรับ unguarded write เพิ่มคำเตือนว่าจะกระทบทุกแถว) ก่อนส่ง request นี่คือ friction ฝั่ง UI เท่านั้น ไม่ใช่ safety net ดู §4
- **Drop**: เมื่อโหลด object อยู่และมี `sql_workbench.manage` ปุ่ม **Drop** ใน header ของหน้าจะลบ object นั้นออกจาก schema แบบถาวรหลัง confirm dialog — การทำงานทางเดียวแบบเดียวกับที่ `DELETE .../sql-query/db-objects` ทำเมื่อเรียกตรง (บันทึกไว้ใน [Query Dataset](/th/inventory/system-config/query-dataset) §2/§4)

## 4. บทบาทและ Persona

route `/sql-workbench` ถือ `requiredPermission="sql_workbench.read"` บน `PrivateRoute` — session ที่ไม่มี grant นี้จะเห็น `<Forbidden>` ภายใน shell `<Layout>` ปกติ ตรงกับทุก route ที่ gate ไว้อื่น ๆ ใน Platform ภายในหน้า `hasPermission('sql_workbench.manage')` (`canManage`) เป็น gate เดียวที่ตัดสินว่า Run, Save, และ Drop จะ render หรือไม่ — ไม่มี tier ที่สามและไม่มีการแยก action ต่อ action ระหว่างสองสิ่งนี้ session จะมีทั้งความสามารถอ่าน (browse) และเขียน (แก้ไข) หรือมีแค่การ browse แบบอ่านอย่างเดียวเท่านั้น

| Surface | Gate | Key |
|---|---|---|
| Route `/sql-workbench` | `requiredPermission` | `sql_workbench.read` |
| รายการ sidebar "SQL Workbench" | `permission` filter | `sql_workbench.read` |
| ปุ่ม Run + shortcut Ctrl/⌘+Enter | render เฉพาะเมื่อ `canManage` | `sql_workbench.manage` |
| ปุ่ม Save | render เฉพาะเมื่อ `canManage` | `sql_workbench.manage` |
| ปุ่ม Drop | render เฉพาะเมื่อ `canManage` (และมี object โหลดอยู่) | `sql_workbench.manage` |

ทั้งสอง key ถูก seed ไว้ใน permission catalog ของ platform (`seed.platform-permission.data.ts`): `sql_workbench.read` — "Open the SQL Workbench, browse database objects, and run read-only queries against a business unit's database" — และ `sql_workbench.manage` — "Run write/DDL SQL … and create/drop views, stored procedures, and functions" ใน role bundle ที่มากับตัวผลิตภัณฑ์ของ platform (`seed.platform-role-permission.data.ts`) มีเพียง `platform_admin` (ผ่าน `sql_workbench.*`) และ `cluster_admin` (ผ่าน `*` แบบครอบคลุมทั้งหมด) ที่ถือ key ใดก็ตามโดย default — `support_manager`, `support_staff`, และ `security_officer` ไม่มีทั้งคู่ ดังนั้น SQL Workbench (ไม่ว่าระดับใด) จึงไม่อยู่ใน role set ระดับ support เริ่มต้น

> **ช่องว่างที่ยืนยันแล้ว คล้ายกับข้อค้นพบของ Inventory book** คำอธิบายของ `sql_workbench.read` ข้างต้นสัญญาว่าเป็น "read-only queries" และ frontend บังคับใช้คำสัญญานั้นด้วยการซ่อน Run/Save/Drop สำหรับ session แบบอ่านอย่างเดียว — แต่ที่ backend มีเพียง route `POST .../execute` เท่านั้นที่ถือ `@RequirePlatformPermission('sql_workbench.manage')` จริง ๆ อีกสี่ route ที่หน้านี้พึ่งพา (`GET db-objects`, `GET db-objects/definition`, `POST save`, `DELETE db-objects`) **ไม่มี permission guard ใด ๆ นอกจากการ authenticate** ยืนยันแล้วใน [Query Dataset](/th/inventory/system-config/query-dataset) (Implementation status, §3, §6) กล่าวคือ: session ที่มีแค่ `sql_workbench.read` ไม่สามารถ Save หรือ Drop จาก UI นี้ได้ แต่ไม่มีอะไรกันไม่ให้ session เดียวกันนั้นเรียก `POST .../sql-query/save` หรือ `DELETE .../sql-query/db-objects` ตรง ๆ (เช่นผ่าน Bruno) — การแบ่ง read/write ของ UI ไม่ได้ถูกหนุนหลังด้วยการแบ่งฝั่ง server ที่ตรงกันบนสอง route นั้น ตัว `execute` เอง ซึ่งเป็น route เดียวที่ **ถูก** guard จริง ก็เป็น route เดียวที่ **ไม่ใช่** read-only ด้วยแม้ชื่อ permission จะบอกอย่างนั้น: `validateSqlSafety(sql_text, { allowMultiple: true, allowDangerous: true })` ข้าม blocklist คำต้องห้ามทั้งหมด ดังนั้น grant `sql_workbench.manage` (ไม่ใช่ `.read`) ต่างหากที่ทำให้ operator รัน `DROP`/`ALTER`/multi-statement script ผ่าน Run ได้จริง — ตรงกับการ gate ปุ่ม Run ของหน้านี้เอง แต่ทำให้คำอธิบายใน permission catalog ของ `.read` ว่าเป็น "read-only queries" ไม่ตรงกับสิ่งที่ caller แบบ `.read` อย่างเดียวเข้าถึงได้นอก UI นี้ทั้งหมด

## 5. โมดูลที่เกี่ยวข้อง

- [Query Dataset](/th/inventory/system-config/query-dataset) — เอกสารของ Inventory book สำหรับ backend service ตัวเดียวกันนี้จากฝั่ง API/data-shape: catalog projection, สัญญาของ `execute`/`save`/`db-objects`, ข้อค้นพบ validator `allowDangerous`, และช่องว่าง permission-guard ที่ยืนยันแล้วบนสี่ในห้า route อ่านหน้านั้นสำหรับ request/response shape ฝั่ง backend; หน้านี้ครอบคลุมหน้าจอ carmen-platform ที่เรียกมันแล้วตอนนี้
- [Business Units](/th/platform/business-units) — เป็นแหล่งของรายการ BU ที่ switcher ค้นหา (`businessUnitService.getAll`) และ `db_connection` ของแต่ละ BU ซึ่งเป็นสิ่งที่ทำให้ฐานข้อมูล tenant เข้าถึงได้เลย
- [Report Templates](/th/platform/report-templates) — ผู้บริโภคปลายทางที่ตั้งใจไว้ของ view/function ที่สร้างที่นี่ ผ่านการผูก data source `source_name`/`source_params` ยังไม่ได้ยืนยัน linkage นี้ซ้ำในรอบนี้
- [Platform RBAC](/th/platform/rbac) — เป็นเจ้าของ permission key `sql_workbench.read`/`.manage` และการ assign role bundle ที่สรุปไว้ใน §4

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/pages/sqlWorkbench/SqlWorkbench.tsx` และ component ย่อย (`ConnectionBar`, `BuSwitcher`, `DbObjectTree`, `SqlEditor`, `ResultPanel`) — หน้าและส่วนประกอบ
- `../carmen-platform/src/services/sqlQueryService.ts` — `getDbObjects`, `getDefinition`, `executeSql`, `saveDdl`, `dropObject`; doc comment เรื่องทำไมการ abort `executeSql` ถึงไม่ยกเลิก query ฝั่ง tenant
- `../carmen-platform/src/utils/sqlValidator.ts` — `extractTopLevelStatements`, `classifyStatements` ระบุชัดว่าเป็น UI feedback ฝั่ง client เท่านั้น ไม่ใช่ security boundary
- `../carmen-platform/src/App.tsx:297` — route `/sql-workbench` (`requiredPermission="sql_workbench.read"`); `src/components/Layout.tsx:67` — รายการ sidebar
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts` — รายการ catalog `sql_workbench.read`/`.manage`; `seed.platform-role-permission.data.ts` — การ assign role bundle
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_sql-query/config_sql-query.controller.ts` และ `../carmen-turborepo-backend-v2/apps/micro-business/src/sql-query/{sql-query.service.ts,sql-validator.ts}` — backend ที่หน้านี้เรียก บันทึกไว้ครบถ้วนจากมุมมองฝั่ง backend-only ของ `../carmen-inventory-frontend-react` ใน [Query Dataset](/th/inventory/system-config/query-dataset)

## 7. หน้าในโมดูลนี้

โมดูลนี้เป็นหน้าเดียว ดู [ดัชนี Platform book](/th/platform)
