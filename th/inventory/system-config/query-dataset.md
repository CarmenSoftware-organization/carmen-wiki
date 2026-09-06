---
title: Query Dataset
description: SQL Workbench — backend admin-SQL-console service ที่มีจริง หน้าจอของมันอยู่ใน Platform SPA ไม่ใช่ผลิตภัณฑ์นี้ และ endpoint execute รัน SQL อะไรก็ได้ (รวมถึง DROP/ALTER/multi-statement) แทนที่จะเป็นพื้นผิว read-only ที่เอกสารเดิมเคยระบุไว้
published: true
date: 2026-09-06T06:45:00.000Z
tags: system-config, query, dataset, sql, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Query Dataset

> **At a Glance**
> **เจ้าของ:** Gate ด้วย platform permission สองตัว — `sql_workbench.read` (เรียกดู) และ `sql_workbench.manage` (รัน / บันทึก / drop) ครบ **ทั้ง 5 route** ตั้งแต่ 2026-08-20 &nbsp;·&nbsp; **การจัดเก็บ:** PostgreSQL catalog (`pg_class`, `pg_proc`) ใน tenant schema — **ไม่มี `tb_query_dataset`** &nbsp;·&nbsp; **ไม่มีหน้าจอใน*ผลิตภัณฑ์นี้*** — console อยู่ที่หน้าจอ [SQL Workbench](/th/platform/sql-workbench) ของ Platform SPA ไม่มี route/component/hook ที่ตรงกันใน `carmen-inventory-frontend-react` &nbsp;·&nbsp; **`execute` ไม่ใช่ read-only** — รัน SQL อะไรก็ได้ รวมถึง DDL และ multi-statement

## สถานะการ implement (ตรวจสอบ 2026-07-16; ตรวจสอบ permission และ UI ใหม่ 2026-09-06)

สาม claim ในเวอร์ชันก่อนหน้าของหน้านี้ไม่ตรงกับ source ปัจจุบัน และถูกแก้ไขด้านล่าง ข้อ 1 และ 2 แก้เมื่อ 2026-07-16 ข้อ 3 แก้เมื่อ 2026-09-06:

1. **ไม่พบ frontend implementation ใดๆ** ไฟล์ที่เคยอ้างถึง `routes/system-admin/query-dataset/page.tsx`, `_components/query-dataset-component.tsx`, `hooks/use-sql-query.ts` และ `lib/sql-validator.ts` (frontend mirror) **ไม่มีอยู่จริงเลยใน `carmen-inventory-frontend-react`** — การค้นทั่ว repo หา `query-dataset` และ `sql-query` ใน repo นั้นคืนค่าศูนย์ไฟล์ และ `routes/router.tsx` ไม่มี path `query-dataset` ใต้ `/system-admin` เลย backend service และ endpoint ของมัน (ด้านล่าง) มีจริง และ **มี UI อยู่ — เพียงแต่ไม่ได้อยู่ในผลิตภัณฑ์นี้** Platform SPA (`carmen-platform`) มีหน้าจอ [SQL Workbench](/th/platform/sql-workbench) เต็มรูปแบบที่ `/sql-workbench` (เพิ่มเมื่อ 2026-07-09) ซึ่ง `sqlQueryService.ts` ของมันเรียก `/api/config/${buCode}/sql-query` — endpoint ชุดเดียวกันทั้ง 5 ตัวที่หน้านี้บันทึกไว้ ให้อ่านว่า "ไม่มีหน้าจอใน Carmen Inventory" ไม่ใช่ "ไม่มีหน้าจอที่ไหนเลย"; ข้อความเดิมเขียนก่อนที่จะมีใครไปตรวจ SPA อีกตัว
2. **`execute` คือ admin SQL console ที่ไม่จำกัด ไม่ใช่ Run แบบ read-only** `SqlQueryService.execute()` เรียก `validateSqlSafety(sql_text, { allowMultiple: true, allowDangerous: true })` — `allowDangerous: true` ข้าม blocklist keyword ต้องห้ามทั้งหมด (`DROP`, `TRUNCATE`, `ALTER`, `GRANT`, `REVOKE`, `COPY`, `VACUUM`, `CLUSTER`, `REASSIGN`, `REINDEX`) และไม่มีการส่งข้อจำกัด `allowedLeading` เลย ดังนั้น `INSERT`/`UPDATE`/`DELETE`/`CREATE`/`DROP`/`ALTER` ผ่านหมด และ `allowMultiple: true` อนุญาต multi-statement script คำอธิบาย Swagger ของ controller เองบอกไว้ตรงๆ: *"Runs any SQL against the tenant DB — SELECT, DML (INSERT/UPDATE/DELETE) and DDL (CREATE/ALTER/DROP/…), one or more statements."* คอมเมนต์ในโค้ดอธิบายเหตุผลไว้ชัดเจน: *"Access is gated by the `sql_workbench.manage` platform permission at the gateway; this validator only rejects empty/unparseable input here — it is not the security boundary."* มีแค่ `saveDdl()` (สัญญา "Save" ใน §5.3) ที่ยังคง validation แบบเข้มงวด (`SELECT`/`WITH` เท่านั้น หรือ `CREATE`-only) ที่หน้านี้เคยระบุไว้ผิดว่าเป็นของ `execute`

3. **ช่องโหว่ permission ที่หน้านี้เคยรายงานถูกปิดแล้ว — อย่าใช้ข้อความเดิมเป็นแนวทาง** ระหว่าง 2026-07-16 ถึง 2026-08-20 หน้านี้รายงานถูกต้องว่ามีแค่ `POST .../execute` ที่มี guard และ `save`, `db-objects` (list), `db-objects/definition` (get) กับ `db-objects` (drop, `DELETE`) เข้าถึงได้โดยผู้เรียกที่ authenticated คนใดก็ได้ **ตอนนี้ไม่จริงแล้ว** commit `525597688` (2026-08-20, `carmen-turborepo-backend-v2`, *fix(security): คุมสิทธิ์ 4 endpoint ของ SQL Workbench ที่เปิดให้สมาชิก BU ทุกคน* ปิด issue #321) เพิ่ม `@UseGuards(PlatformPermissionGuard)` + `@RequirePlatformPermission(...)` ครบทั้งสี่ route:

| Route | Permission ที่ต้องมี ตั้งแต่ 2026-08-20 |
|---|---|
| `POST .../execute` | `sql_workbench.manage` (ไม่เปลี่ยน — route นี้มี guard มาตลอด) |
| `POST .../save` | `sql_workbench.manage` |
| `GET .../db-objects` | `sql_workbench.read` |
| `GET .../db-objects/definition` | `sql_workbench.read` |
| `DELETE .../db-objects` | `sql_workbench.manage` |

ความผิดพลาดที่ commit อธิบายไว้ตรงกับที่ข้อความเดิมของหน้านี้บอกให้คาดหวัง: สมาชิกคนใดก็ได้ของ business unit เป้าหมาย — "พนักงานธรรมดาที่ไม่มี platform role เลย" — เคย `CREATE OR REPLACE` หรือ `DROP` view/procedure/function ใน tenant schema ได้ ขณะที่การรัน `SELECT` ธรรมดากลับต้องมี permission ตอนนี้ทั้ง 5 route มี `@ApiResponse` 403 ที่ตรงกับการบังคับใช้จริงแล้ว

ยังไม่มี App-ID สามตัว `sql-query.execute` / `.save` / `.drop` ตามที่ข้อความเก่าบางส่วนเคยระบุ และ **ไม่มี `AppIdGuard` บน route ใดเลยใน controller นี้** — header `x-app-id` ประกาศไว้สำหรับ Swagger (`@ApiHeaderRequiredXAppId()`) แต่ไม่ได้ถูกบังคับใช้ที่นี่ สิ่งที่บังคับใช้จริงคือ platform permission `sql_workbench.*` สองตัวเท่านั้น — มีแค่ permission เดียว (`sql_workbench.manage`) และครอบคลุมแค่ `execute`

ส่วนที่เหลือของหน้านี้ (catalog projections, save/DDL contract, response shapes) ยังตรงกับ backend source และไม่มีการเปลี่ยนแปลงด้านล่าง

## 1. คืออะไรและใครใช้

Query Dataset (เรียกภายในว่า "SQL Workbench") คือ **backend admin-SQL-console service** สำหรับการรัน SQL ใดๆ ก็ได้ และการสร้าง / browse / drop object ฐานข้อมูลที่ใช้ซ้ำได้ — **view**, **stored procedure** และ **function** — โดยตรงภายในฐานข้อมูล tenant ปัจจุบัน **ไม่มีหน้าจอ frontend ที่เรียกมันเลย** (ดูสถานะการ implement) ผลลัพธ์มีเจตนาให้กลายเป็นแหล่งข้อมูลสำหรับ template รายงานและ tile dashboard consume ณ run time โดย service **micro-data** ที่แยกต่างหาก

**กลุ่มเป้าหมายวันนี้:** ผู้ปฏิบัติงานที่ถือ `sql_workbench.read` (เรียกดู) หรือ `sql_workbench.manage` (รัน / บันทึก / drop) ไม่ว่าจะทำงานผ่านหน้าจอ [SQL Workbench](/th/platform/sql-workbench) ของ Platform SPA หรือเรียก API โดยตรง (เช่นผ่าน Bruno) ไม่มีกลุ่มเป้าหมายใน*ผลิตภัณฑ์นี้* เพราะ Carmen Inventory ไม่มีหน้าจอสำหรับมัน ไม่เหมือนตาราง Carmen ส่วนใหญ่ **ไม่มี row `tb_query_dataset`** สำหรับแต่ละ object ที่บันทึก — registry คือ PostgreSQL catalog ที่ live scope ตาม tenant schema

view, stored procedure และ function ที่สร้างที่นี่มีเจตนาเป็นแหล่งข้อมูลที่ service **micro-data** เรียกใช้งานจริง ณ run time: รายงานหรือ dashboard ควรระบุชื่อ object นั้น (ผ่าน `builder_key` หรือ template `name`) และ micro-data จะ resolve ผ่าน `POST /api/datasets/execute`, ประกอบ WHERE clause จาก filter ที่ส่งมา, กระจาย query ไปยัง business unit ที่ร้องขอ, และส่งคืน `Dataset` (columns + rows + totals + summary) ดู [reporting-audit/report](/th/inventory/reporting-audit/report) สำหรับฝั่งการแสดงผล ความเชื่อมโยงนี้ยังไม่ได้ re-verify แยกในรอบนี้

## 2. งานทั่วไป

ไม่มี UI *ใน Carmen Inventory* (ดูสถานะการ implement) — นี่คือ API operation ที่อยู่เบื้องหลัง ซึ่งเข้าถึงได้ผ่านหน้าจอ [SQL Workbench](/th/platform/sql-workbench) ของ Platform SPA หรือเรียกโดยตรง (เช่นผ่าน Bruno)

| งาน | API call | หมายเหตุ |
|---|---|---|
| รัน SQL ใดๆ | `POST .../sql-query/execute` | **ไม่ใช่ read-only** — statement ประเภทใดก็ได้ หลาย statement ได้ gate ด้วย `sql_workbench.manage` |
| บันทึก `SELECT` เป็น view | `POST .../sql-query/save` พร้อม `SELECT` เปล่า + `name` + `query_type: "view"` | Server auto-wrap เป็น `CREATE OR REPLACE VIEW "<name>" AS …`; อนุญาตแค่ `SELECT`/`WITH` statement เดียว |
| สร้าง stored procedure / function | `POST .../sql-query/save` พร้อม DDL เต็ม (`CREATE OR REPLACE PROCEDURE/FUNCTION …`) | Body เปลือยถูก reject — ต้องการ DDL เต็ม |
| Browse object ที่มีอยู่ | `GET .../sql-query/db-objects` | Tables / Views / Procedures / Functions / columns |
| ดู definition ของ object | `GET .../sql-query/db-objects/definition?type=&schema=&name=` | โหลด `pg_get_viewdef` / `pg_get_functiondef` |
| Drop object | `DELETE .../sql-query/db-objects?type=&schema=&name=` | ไม่มี undo; รายงานที่ผูกจะ error |

## 3. การตรวจสอบและ Error

| อาการ / ข้อความ | สาเหตุ | การดำเนินการ |
|---|---|---|
| `execute` รัน `DROP TABLE` / `DELETE` / multi-statement script สำเร็จ | คาดหวัง — `execute` ไม่มีข้อจำกัดประเภท statement หรือ multi-statement เลย มีแค่ `sql_workbench.manage` gate ผู้เรียก | อย่าถือว่า `execute` เป็น console read-only ที่ปลอดภัย |
| "Forbidden statement" ตอน `save` | Validation แบบ `SELECT` เปล่าหรือ `CREATE`-only ของ `save` ปฏิเสธ keyword `DROP`/`TRUNCATE`/ฯลฯ | `save` (ต่างจาก `execute`) ยังคง blocklist ไว้ — เขียนใหม่เป็น DDL ที่ valid |
| "Name is required" ตอน save | `SELECT` เปล่า + Type `View` โดยไม่มีชื่อ | ระบุชื่อ view (ใส่ quote เพื่อความปลอดภัย injection) |
| Procedure / function บันทึกถูก reject | Body เปลือยที่ส่งมา | Wrap ใน DDL `CREATE OR REPLACE PROCEDURE/FUNCTION …` |
| `statement_timeout` หลัง 30 วินาที | Query เกิน budget | เพิ่ม filter / index; transaction budget 35 วินาที, max-wait 8 วินาที |
| "Database is busy" | Connection pool หมด; ลองซ้ำหนึ่งครั้งแล้วหลัง 500 ms | ลองใหม่ทีหลัง; ตรวจสอบ load พร้อมกัน |
| คอลัมน์ `BigInt` ส่งคืนเป็น string ในผลลัพธ์ | คาดหวัง — JSON ไม่สามารถพา `bigint` แบบดั้งเดิม | Cast ใน SQL ถ้าจำเป็นต้องจัดการเชิงตัวเลขปลายทาง |
| รายงาน error หลัง drop | View / procedure ที่ผูกถูกลบจาก catalog | สร้าง object ใหม่หรืออัปเดต binding ของรายงาน |
| 403 ตอน `execute`, `save` หรือ `DELETE db-objects` | ผู้เรียกไม่มี `sql_workbench.manage` | Grant ผ่านระบบ permission ของแพลตฟอร์ม — ดู [Platform RBAC](/th/platform/rbac) |
| 403 ตอน `GET db-objects` หรือ `db-objects/definition` | ผู้เรียกไม่มี `sql_workbench.read` | เช่นเดียวกัน; `.read` คือ grant สำหรับเรียกดูอย่างเดียว |
| `save` / list / get-definition / drop สำเร็จสำหรับผู้เรียกที่ authenticated ใครก็ได้ | **เป็นเรื่องในอดีตเท่านั้น — แก้แล้วเมื่อ 2026-08-20 โดย `525597688`** ถ้าพบอาการนี้วันนี้ แสดงว่าคุณอยู่บน build ที่เก่ากว่า commit นั้น | อัปเกรด อย่าถือว่าเป็นพฤติกรรมที่คาดหวัง |

## 4. กรณีพิเศษ

- **`execute` ไม่ใช่ read-only และไม่ใช่ single-statement** ยืนยันผ่าน `validateSqlSafety(sql_text, { allowMultiple: true, allowDangerous: true })` — ดูสถานะการ implement
- **`save` ยังคง validation ที่เข้มงวด** ที่หน้านี้เคยระบุผิดว่าเป็นของ `execute`: `SELECT`/`WITH` เปล่า statement เดียวสำหรับ view, `CREATE`-only (อนุญาตหลาย statement `CREATE`) สำหรับ DDL ที่เขียนมาแล้ว
- **Credentials scope ตาม tenant** `prismaTenantInstance(bu_code, user_id)` ให้ connection — ทุก query และ DDL รันภายใต้ role / schema ของ tenant; **การเข้าถึง cross-tenant เป็นไปไม่ได้ที่ชั้นฐานข้อมูล** ไม่ว่าการตรวจสอบประเภท statement จะหลวมแค่ไหน
- **ไม่มีประวัติเวอร์ชันใน Carmen** `CREATE OR REPLACE` ทิ้งข้อความก่อนหน้า
- **Drop เป็นการทำลายและทันที** Entry catalog ที่ drop ทำลายรายงานหรือ widget ที่ผูกในการรันครั้งถัดไป
- **Bare-SELECT auto-wrap เฉพาะสำหรับ view** Procedure และ function ต้องการ DDL เต็ม (ใน `save`)
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

- `tb_dashboard_bu_widget` / `tb_dashboard_personal_widget` — widget tile ของแดชบอร์ด (scope ระดับ BU / ต่อผู้ใช้); แต่ละ row เก็บการอ้างอิง `dataset_id` ไปยัง catalog ที่ลงทะเบียนในโค้ดของ [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) **ไม่ใช่** SQL text — แยกจาก catalog object (เวอร์ชันก่อนหน้าอ้างถึงตาราง `tb_widget_workspace` ที่เก็บ SQL ad-hoc ต่อผู้ใช้; ไม่มี model แบบนั้นใน Prisma schema ใดเลย)
- `tb_report_job.report_type` / `tb_report_schedule.report_type` — string key map ไปยังนิยามรายงานที่อาจ *consume* view แต่ mapping อยู่ในโมดูล reports

## 6. กฎทางธุรกิจ

- **`execute` gate ด้วย `sql_workbench.manage`** — สังเกตว่าแม้ชื่อจะเป็น `.manage` แต่มันคือสิ่งที่ทำให้ผู้ปฏิบัติงานรัน *อะไรก็ได้* ผ่าน `execute` รวมถึง `SELECT` ธรรมดา ไม่ใช่ `.read`
- **`execute` อนุญาต statement ประเภทใดก็ได้ รวมถึง DDL/DML และหลาย statement** (`allowDangerous: true`, `allowMultiple: true`) — ยืนยันว่า **ไม่ใช่** read-only ต่างจากเวอร์ชันก่อนหน้าของหน้านี้
- **`save` คือ `CREATE`-only:** DDL เต็ม (`allowedLeading: ['CREATE']`) หรือ SELECT เปล่าสำหรับ view (`['SELECT', 'WITH']`) และ gate ด้วย `sql_workbench.manage`
- **`db-objects` (list/get-definition) ต้องมี `sql_workbench.read`; `db-objects` (drop) ต้องมี `sql_workbench.manage`**
- **Timeout statement 30 วินาที** ภายใน transaction budget 35 วินาทีของ Prisma (max-wait 8 วินาที) บน `execute`
- **Credentials scope ตาม tenant** ผ่าน `prismaTenantInstance(bu_code, user_id)` — การเข้าถึง cross-tenant เป็นไปไม่ได้ที่ชั้น DB ไม่ว่าประเภท statement จะเป็นอะไร
- **Connection-pool retry** — รอ 500 ms ลองหนึ่งครั้ง แล้ว "Database is busy" (ทั้งบน `execute` และ `saveDdl`)
- **BigInt safety** ใน response ของ `execute` (stringified); ลำดับคอลัมน์รักษา
- **View แบบ SELECT เปล่าต้องการชื่อ**; ใส่ quote เพื่อความปลอดภัย injection
- **Procedure / function ต้องเป็น DDL เต็ม** (ใน `save`)
- **ไม่มีประวัติเวอร์ชัน** — `CREATE OR REPLACE` ทิ้งข้อความก่อนหน้า

## 7. การอ้างอิงข้าม

- [reporting-audit/report](/th/inventory/reporting-audit/report) — template รายงานมีเจตนา bind กับ view ที่สร้างที่นี่; ความเชื่อมโยงยังไม่ได้ re-verify แยกในรอบนี้
- [reporting-audit/widget](/th/inventory/reporting-audit/widget) — Widget dashboard อ้างอิง `dataset_id` ที่ลงทะเบียนในโค้ด (`tb_dashboard_bu_widget` / `tb_dashboard_personal_widget`) ไม่ใช่ SQL ad-hoc; claim `tb_widget_workspace` ของเวอร์ชันก่อนหน้าไม่มีแหล่งรองรับ (ไม่มีตารางนั้นอยู่จริง)
- [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) — รายงานตามตารางเวลา consume view ตัวเดียวกัน (ยังไม่ยืนยันในรอบนี้)
- [system-config/period](/th/inventory/system-config/period) — object การปิดงวด (`sp_close_period`, `v_period_snapshot`) โดยทั่วไปอยู่ที่นี่ (ยังไม่ยืนยันในรอบนี้)

## 8. แหล่งข้อมูลอ้างอิง

- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/sql-query/sql-query.service.ts` — `execute`, `saveDdl`, `listDbObjects`, `getDbObjectDefinition`, `dropDbObject`
- **Backend gateway controller:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_sql-query/config_sql-query.controller.ts` — อ่านซ้ำ 2026-09-06: มี `PlatformPermissionGuard` + `RequirePlatformPermission` ครบ **ทั้ง 5 route** (`execute` `:70-71`, `save` `:119-120`, `db-objects` `:174-175`, `db-objects/definition` `:209-210`, `DELETE db-objects` `:258-259`) ไม่มี `AppIdGuard` ที่ใดเลยในไฟล์นี้
- **SQL safety validator:** `../carmen-turborepo-backend-v2/apps/micro-business/src/sql-query/sql-validator.ts` — blocklist `FORBIDDEN_LEADING`, flag `allowDangerous` สำหรับ bypass
- **Frontend:** ไม่พบเลย ไม่มีไฟล์ `query-dataset` หรือ `sql-query` ที่ไหนใน `../carmen-inventory-frontend-react` (ยืนยันด้วยการค้นทั่ว repo); ไม่มี route ใน `routes/router.tsx`
- **Prisma ที่เกี่ยวข้อง:** `tb_report_job` (line ~6101), `tb_report_schedule` (line ~6135), `tb_dashboard_bu_widget` (line ~6185), `tb_dashboard_personal_widget` (line ~6205)
