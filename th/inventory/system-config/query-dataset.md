---
title: Query Dataset
description: SQL Workbench — รัน SELECT แบบ ad-hoc และสร้าง / browse / drop view, stored procedure และ function ของ tenant ที่ใช้เป็นแหล่งข้อมูลใช้ซ้ำได้สำหรับรายงานและ dashboard
published: true
date: 2026-05-19T23:55:00.000Z
tags: system-config, query, dataset, sql, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Query Dataset

> **At a Glance**
> **เจ้าของ:** Sysadmin เท่านั้น (`sql-query.*` App IDs) &nbsp;·&nbsp; **การจัดเก็บ:** PostgreSQL catalog (`pg_class`, `pg_proc`) ใน tenant schema — **ไม่มี `tb_query_dataset`** &nbsp;·&nbsp; **ใช้โดย:** [reporting-audit/report](/th/inventory/reporting-audit/report), [reporting-audit/widget](/th/inventory/reporting-audit/widget), [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) &nbsp;·&nbsp; **Run เป็น read-only; timeout 30 วินาที**

![Query Dataset screen](/screenshots/system-config/query-dataset.png)

## 1. คืออะไรและใครใช้

Query Dataset (แสดงเป็น **SQL Workbench** ใน UI) คือหน้าจอเฉพาะ Sysadmin ที่ `/system-admin/query-dataset` สำหรับการรัน query แบบ ad-hoc read-only และการสร้าง / browse / drop object ฐานข้อมูลที่ใช้ซ้ำได้ — **view**, **stored procedure** และ **function** — โดยตรงภายในฐานข้อมูล tenant ผลลัพธ์กลายเป็นแหล่งข้อมูลสำหรับ template รายงานและ tile dashboard

**กลุ่มเป้าหมาย:** Sysadmin เท่านั้น — role ที่ไม่ใช่ admin ไม่เห็นรายการ navigation ไม่เหมือนตาราง Carmen ส่วนใหญ่ **ไม่มี row `tb_query_dataset`** สำหรับแต่ละ object ที่บันทึก — registry คือ PostgreSQL catalog ที่ live scope ตาม tenant schema Workbench เองไม่มี state; การแก้ไข commit ตรงไปยัง catalog และ reload-from-catalog คือเส้นทาง recovery

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| บันทึก `SELECT` เป็น view | Editor → ใส่ SELECT เปล่า + ชื่อ, **Type:** View → **Save** | Server auto-wrap เป็น `CREATE OR REPLACE VIEW "<name>" AS …` |
| ทดสอบ query ก่อนบันทึก | Editor → **Run** | Read-only; อนุญาตเฉพาะ `SELECT`, `WITH`, `SHOW`, `EXPLAIN`, `DESCRIBE`; timeout 30 วินาที |
| Promote query widget ที่บันทึกแล้วเป็นรายงาน | สร้าง SQL ที่นี่ใหม่เป็น view, จากนั้น bind จาก [reporting-audit/report](/th/inventory/reporting-audit/report) | Widget เก็บ SQL แบบ ad-hoc ใน `tb_widget_workspace` (scope ตาม author); view เป็นระดับ tenant |
| Browse object ที่มีอยู่ | Sidebar ซ้าย (`DbObjectTree`) → Tables / Views / Procedures / Functions | คลิกเพื่อโหลด definition เข้า editor |
| แก้ view ที่มีอยู่ | คลิกใน tree → โหลด `pg_get_viewdef` เป็น `CREATE OR REPLACE VIEW …` | แก้ + บันทึก commit ข้อความใหม่ |
| สร้าง stored procedure / function | Editor → DDL เต็ม (`CREATE OR REPLACE PROCEDURE/FUNCTION …`) → **Type:** Stored Procedure / Function → **Save** | Body เปลือยถูก reject — ต้องการ DDL เต็ม |
| Drop object | โหลด object ใน tree → **Drop** (มองเห็นเฉพาะเมื่อโหลด) | Dialog `confirm()` ของ browser; **ไม่มี undo**; รายงานที่ผูกจะ error |

## 3. การตรวจสอบและ Error

| อาการ / ข้อความ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Only SELECT/WITH/SHOW/EXPLAIN allowed" ตอน Run | Multi-statement script หรือ write keyword | ลบ `INSERT`/`UPDATE`/`DELETE`/`DROP`/`TRUNCATE`; `allowMultiple: false` |
| "Name is required" ตอน save | `SELECT` เปล่า + Type `View` โดยไม่มีชื่อ | ระบุชื่อ view (ใส่ quote เพื่อความปลอดภัย injection) |
| Procedure / function บันทึกถูก reject | Body เปลือยที่ส่งมา | Wrap ใน DDL `CREATE OR REPLACE PROCEDURE/FUNCTION …` |
| `statement_timeout` หลัง 30 วินาที | Query เกิน budget | เพิ่ม filter / index; transaction budget 35 วินาที, max-wait 8 วินาที |
| "Database is busy" | Connection pool หมด; ลองซ้ำหนึ่งครั้งแล้วหลัง 500 ms | ลองใหม่ทีหลัง; ตรวจสอบ load พร้อมกัน |
| คอลัมน์ `BigInt` ส่งคืนเป็น string ในผลลัพธ์ | คาดหวัง — JSON ไม่สามารถพา `bigint` แบบดั้งเดิม | Cast ใน SQL ถ้าจำเป็นต้องจัดการเชิงตัวเลขปลายทาง |
| รายงาน error หลัง drop | View / procedure ที่ผูกถูกลบจาก catalog | สร้าง object ใหม่หรืออัปเดต binding ของรายงาน |
| 403 / route มองไม่เห็น | User ไม่มี `sql-query.execute` / `.save` / `.drop` App IDs | Grant ผ่าน [access-control/application-role](/th/inventory/access-control/application-role) |

## 4. กรณีพิเศษ

- **Run read-only, Save CREATE-only** `validateSqlSafety` บังคับ leading keyword ฝั่ง client และ re-check ฝั่ง server Mixed script (เริ่มด้วย `CREATE` มี `DROP` ภายหลัง) ถูกบล็อกโดยการตรวจสอบ multi-statement
- **Credentials scope ตาม tenant** `prismaTenantInstance(bu_code, user_id)` ให้ connection — ทุก query และ DDL รันภายใต้ role / schema ของ tenant; **การเข้าถึง cross-tenant เป็นไปไม่ได้ที่ชั้นฐานข้อมูล**
- **ไม่มีประวัติเวอร์ชันใน Carmen** `CREATE OR REPLACE` ทิ้งข้อความก่อนหน้า Version-control DDL ภายนอก (git) และ re-apply ผ่าน Workbench
- **Drop เป็นการทำลายและทันที** Entry catalog ที่ drop ทำลายรายงานหรือ widget ที่ผูกในการรันครั้งถัดไป
- **Bare-SELECT auto-wrap เฉพาะสำหรับ view** Procedure และ function ต้องการ DDL เต็ม
- **BigInt safety** Row ผลลัพธ์ post-process ให้คอลัมน์ `bigint` เป็น string; ลำดับคอลัมน์รักษาจาก row แรก

---

## 5. Backing Service / Data Shape (Dev)

**ไม่มีตารางเฉพาะ** "แบบจำลองข้อมูล" คือ PostgreSQL catalog ที่ live บวกชุด API endpoint บางๆ

### 5.1 PostgreSQL catalog projections (sidebar tree)

Catalog query 4 ตัว scope ตาม `current_schema()`:

```
tables     → pg_class    WHERE relkind = 'r'   (ยกเว้น extension-owned)
views      → pg_class    WHERE relkind = 'v'   (ยกเว้น extension-owned)
procedures → pg_proc     WHERE prokind IN ('p','f')
columns    → pg_attribute joined to pg_class for table/view/materialised-view cols
```

Shape `DbObjectsResponse`:

```jsonc
{
  "tables":     [{ "schema": "tenant_t01", "name": "tb_purchase_request" }, ...],
  "views":      [{ "schema": "tenant_t01", "name": "v_pr_summary" }, ...],
  "procedures": [{ "schema": "tenant_t01", "name": "sp_close_period", "kind": "procedure" }, ...],
  "columns":    [{ "table": "tb_purchase_request", "column": "id", "data_type": "uuid" }, ...]
}
```

### 5.2 Object definition (edit flow)

คลิก view / procedure / function ที่มีอยู่ → fetch `pg_get_viewdef` หรือ `pg_get_functiondef` → โหลดเข้า editor เป็น `CREATE OR REPLACE …` พร้อม re-save

### 5.3 Save / Drop contract

`POST /api/config/:bu_code/sql-query/save`:

```jsonc
{
  "name": "v_pr_summary",                       // จำเป็นเมื่อ SELECT เปล่า
  "sql_text": "SELECT id, doc_no FROM tb_pr",  // DDL เต็มหรือ SELECT เปล่า
  "query_type": "view"                          // "view" | "stored_procedure" | "function"
}
```

`DELETE /api/config/:bu_code/sql-query/db-objects?type=…&schema=…&name=…` drop object ที่ระบุชื่อ

### 5.4 ที่เกี่ยวข้อง (ไม่ใช่อันเดียวกัน)

- `tb_widget_workspace` — query dashboard ที่บันทึกแบบ scope ตาม author (`{ name, query }`); แยกจาก catalog object
- `tb_report_job.report_type` / `tb_report_schedule.report_type` — string key map ไปยังนิยามรายงานที่อาจ *consume* view แต่ mapping อยู่ในโมดูล reports

## 6. กฎทางธุรกิจ

- **Sysadmin เท่านั้น** gate โดย `sql-query.*` App IDs
- **Run read-only:** `validateSqlSafety` อนุญาต leading `SELECT`, `WITH`, `SHOW`, `EXPLAIN`, `DESCRIBE`, `DESC`; `allowMultiple: false`
- **Save CREATE-only:** DDL เต็ม (`allowedLeading: ['CREATE']`) หรือ SELECT เปล่าสำหรับ view (`['SELECT', 'WITH']`) Multi-statement script ที่มี `DROP` ภายหลังถูกบล็อก
- **Timeout statement 30 วินาที** ภายใน transaction budget 35 วินาทีของ Prisma (max-wait 8 วินาที)
- **Credentials scope ตาม tenant** ผ่าน `prismaTenantInstance(bu_code, user_id)`
- **Connection-pool retry** — รอ 500 ms ลองหนึ่งครั้ง แล้ว "Database is busy"
- **BigInt safety** ใน response (stringified); ลำดับคอลัมน์รักษา
- **Drop เป็นการทำลายและยืนยัน** ผ่าน `confirm()` native
- **View แบบ SELECT เปล่าต้องการชื่อ**; ใส่ quote เพื่อความปลอดภัย injection
- **Procedure / function ต้องเป็น DDL เต็ม**
- **ไม่มีประวัติเวอร์ชัน** — `CREATE OR REPLACE` ทิ้งข้อความก่อนหน้า

## 7. การอ้างอิงข้าม

- [reporting-audit/report](/th/inventory/reporting-audit/report) — template รายงาน bind กับ view ที่สร้างที่นี่
- [reporting-audit/widget](/th/inventory/reporting-audit/widget) — Widget dashboard execute กับ view หรือเก็บ SQL แบบ ad-hoc ใน `tb_widget_workspace`
- [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) — รายงานตามตารางเวลา consume view ตัวเดียวกัน
- [access-control/permission](/th/inventory/access-control/permission) — `sql-query.execute` / `.save` / `.drop` App IDs gate หน้าจอ
- [system-config/period](/th/inventory/system-config/period) — object การปิดงวด (`sp_close_period`, `v_period_snapshot`) โดยทั่วไปอยู่ที่นี่

## 8. แหล่งข้อมูลอ้างอิง

- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/sql-query/sql-query.service.ts` — `execute`, `saveDdl`, `listDbObjects`, `getDbObjectDefinition`, `dropDbObject`
- **Backend gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_sql-query/config_sql-query.controller.ts`
- **SQL safety validator:** `../carmen-turborepo-backend-v2/apps/micro-business/src/sql-query/sql-validator.ts` (frontend mirror: `../carmen-inventory-frontend/lib/sql-validator.ts`)
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/system-admin/query-dataset/page.tsx` และ `_components/query-dataset-component.tsx`
- **Frontend supporting components:** `_components/db-object-tree.tsx`, `_components/sql-editor.tsx`, `_components/result-panel.tsx`
- **Frontend hook:** `../carmen-inventory-frontend/hooks/use-sql-query.ts` — `useDbObjects`, `useDbObjectDefinition`, `useSqlQueryExecute`, `useSqlQuerySave`, `useSqlQueryDrop`
- **Prisma ที่เกี่ยวข้อง:** `tb_widget_workspace` (lines ~5787-5801), `tb_report_schedule` (lines ~5685-5709), `tb_report_job` (lines ~5652-5683)
