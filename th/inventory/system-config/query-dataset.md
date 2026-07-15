---
title: Query Dataset
description: SQL Workbench — backend admin-SQL-console service ที่มีจริง แต่ไม่มีหน้าจอ frontend ที่ยืนยันได้ และ endpoint execute รัน SQL อะไรก็ได้ (รวมถึง DROP/ALTER/multi-statement) แทนที่จะเป็นพื้นผิว read-only ที่เอกสารเดิมเคยระบุไว้
published: true
date: 2026-07-16T05:00:00.000Z
tags: system-config, query, dataset, sql, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Query Dataset

> **At a Glance**
> **เจ้าของ:** Gate ด้วย platform permission เดียวคือ `sql_workbench.manage` — แต่ **เฉพาะ endpoint `execute` เท่านั้น** &nbsp;·&nbsp; **การจัดเก็บ:** PostgreSQL catalog (`pg_class`, `pg_proc`) ใน tenant schema — **ไม่มี `tb_query_dataset`** &nbsp;·&nbsp; **ไม่มีหน้าจอ frontend ที่ยืนยันได้** — backend service มีจริง แต่ไม่พบ route/component/hook ที่ตรงกันใน `carmen-inventory-frontend-react` &nbsp;·&nbsp; **`execute` ไม่ใช่ read-only** — รัน SQL อะไรก็ได้ รวมถึง DDL และ multi-statement

## สถานะการ implement (ตรวจสอบ 2026-07-16)

สอง claim ในเวอร์ชันก่อนหน้าของหน้านี้ไม่ตรงกับ backend source ปัจจุบัน และถูกแก้ไขด้านล่าง:

1. **ไม่พบ frontend implementation ใดๆ** ไฟล์ที่เคยอ้างถึง `routes/system-admin/query-dataset/page.tsx`, `_components/query-dataset-component.tsx`, `hooks/use-sql-query.ts` และ `lib/sql-validator.ts` (frontend mirror) **ไม่มีอยู่จริงเลยใน `carmen-inventory-frontend-react`** — การค้นทั่ว repo หา `query-dataset` และ `sql-query` ใน repo นั้นคืนค่าศูนย์ไฟล์ และ `routes/router.tsx` ไม่มี path `query-dataset` ใต้ `/system-admin` เลย backend service และ endpoint ของมัน (ด้านล่าง) มีจริง — แต่ปัจจุบันไม่มี Sysadmin UI ที่จะเข้าถึงมันได้
2. **`execute` คือ admin SQL console ที่ไม่จำกัด ไม่ใช่ Run แบบ read-only** `SqlQueryService.execute()` เรียก `validateSqlSafety(sql_text, { allowMultiple: true, allowDangerous: true })` — `allowDangerous: true` ข้าม blocklist keyword ต้องห้ามทั้งหมด (`DROP`, `TRUNCATE`, `ALTER`, `GRANT`, `REVOKE`, `COPY`, `VACUUM`, `CLUSTER`, `REASSIGN`, `REINDEX`) และไม่มีการส่งข้อจำกัด `allowedLeading` เลย ดังนั้น `INSERT`/`UPDATE`/`DELETE`/`CREATE`/`DROP`/`ALTER` ผ่านหมด และ `allowMultiple: true` อนุญาต multi-statement script คำอธิบาย Swagger ของ controller เองบอกไว้ตรงๆ: *"Runs any SQL against the tenant DB — SELECT, DML (INSERT/UPDATE/DELETE) and DDL (CREATE/ALTER/DROP/…), one or more statements."* คอมเมนต์ในโค้ดอธิบายเหตุผลไว้ชัดเจน: *"Access is gated by the `sql_workbench.manage` platform permission at the gateway; this validator only rejects empty/unparseable input here — it is not the security boundary."* มีแค่ `saveDdl()` (สัญญา "Save" ใน §5.3) ที่ยังคง validation แบบเข้มงวด (`SELECT`/`WITH` เท่านั้น หรือ `CREATE`-only) ที่หน้านี้เคยระบุไว้ผิดว่าเป็นของ `execute`

**การ gate permission ก็แคบกว่าที่เคยระบุไว้เช่นกัน** มีแค่ route `POST .../execute` ที่มี `@UseGuards(PlatformPermissionGuard)` + `@RequirePlatformPermission('sql_workbench.manage')` ใน `config_sql-query.controller.ts` route `save`, `db-objects` (list), `db-objects/definition` (get) และ `db-objects` (drop, `DELETE`) **ไม่มี permission guard ใดเลยนอกเหนือจาก `KeycloakGuard`** ระดับ controller (authentication เท่านั้น) — ไม่มี App-ID สามตัว `sql-query.execute` / `.save` / `.drop` ตามที่เคยระบุไว้ — มีแค่ permission เดียว (`sql_workbench.manage`) และครอบคลุมแค่ `execute`

ส่วนที่เหลือของหน้านี้ (catalog projections, save/DDL contract, response shapes) ยังตรงกับ backend source และไม่มีการเปลี่ยนแปลงด้านล่าง

## 1. คืออะไรและใครใช้

Query Dataset (เรียกภายในว่า "SQL Workbench") คือ **backend admin-SQL-console service** สำหรับการรัน SQL ใดๆ ก็ได้ และการสร้าง / browse / drop object ฐานข้อมูลที่ใช้ซ้ำได้ — **view**, **stored procedure** และ **function** — โดยตรงภายในฐานข้อมูล tenant ปัจจุบัน **ไม่มีหน้าจอ frontend ที่เรียกมันเลย** (ดูสถานะการ implement) ผลลัพธ์มีเจตนาให้กลายเป็นแหล่งข้อมูลสำหรับ template รายงานและ tile dashboard consume ณ run time โดย service **micro-data** ที่แยกต่างหาก

**กลุ่มเป้าหมายวันนี้:** ใครก็ตามที่เรียก API ได้โดยตรง (เช่นผ่าน Bruno) พร้อม grant `sql_workbench.manage` สำหรับ `execute` หรือผู้เรียกที่ authenticated พร้อม `x-app-id` ถูกต้องสำหรับ `save`/list/get-definition/drop — ไม่มีกลุ่มเป้าหมายระดับ UI เพราะไม่มี UI ไม่เหมือนตาราง Carmen ส่วนใหญ่ **ไม่มี row `tb_query_dataset`** สำหรับแต่ละ object ที่บันทึก — registry คือ PostgreSQL catalog ที่ live scope ตาม tenant schema

view, stored procedure และ function ที่สร้างที่นี่มีเจตนาเป็นแหล่งข้อมูลที่ service **micro-data** เรียกใช้งานจริง ณ run time: รายงานหรือ dashboard ควรระบุชื่อ object นั้น (ผ่าน `builder_key` หรือ template `name`) และ micro-data จะ resolve ผ่าน `POST /api/datasets/execute`, ประกอบ WHERE clause จาก filter ที่ส่งมา, กระจาย query ไปยัง business unit ที่ร้องขอ, และส่งคืน `Dataset` (columns + rows + totals + summary) ดู [reporting-audit/report](/th/inventory/reporting-audit/report) สำหรับฝั่งการแสดงผล ความเชื่อมโยงนี้ยังไม่ได้ re-verify แยกในรอบนี้

## 2. งานทั่วไป

ไม่มี UI (ดูสถานะการ implement) — นี่คือ API operation ที่อยู่เบื้องหลัง ซึ่งเรียกได้โดยตรงวันนี้ (เช่นผ่าน Bruno)

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
| 401 ตอน `execute` | ผู้เรียกไม่มี platform permission `sql_workbench.manage` | Grant ผ่านระบบ permission ของแพลตฟอร์ม — นี่คือ route เดียวใน service นี้ที่มี guard |
| `save` / list / get-definition / drop สำเร็จสำหรับผู้เรียกที่ authenticated ใครก็ได้ | ช่องโหว่ที่ยืนยันแล้ว — route เหล่านี้ไม่มี permission guard เลยนอกเหนือ auth พื้นฐาน | Flag ไว้สำหรับติดตามผลต่อ ไม่ได้แก้ในรอบนี้ |

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

- **`execute` gate ด้วย `sql_workbench.manage`** (platform permission เดียว) — route เดียวใน service นี้ที่มี guard
- **`execute` อนุญาต statement ประเภทใดก็ได้ รวมถึง DDL/DML และหลาย statement** (`allowDangerous: true`, `allowMultiple: true`) — ยืนยันว่า **ไม่ใช่** read-only ต่างจากเวอร์ชันก่อนหน้าของหน้านี้
- **`save` คือ `CREATE`-only:** DDL เต็ม (`allowedLeading: ['CREATE']`) หรือ SELECT เปล่าสำหรับ view (`['SELECT', 'WITH']`) และ **ไม่มี permission guard** เลยนอกเหนือ authentication พื้นฐาน
- **`db-objects` (list/get-definition) และ `db-objects` (drop) ก็ไม่มี permission guard เช่นกัน** นอกเหนือ authentication พื้นฐาน
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
- **Backend gateway controller:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_sql-query/config_sql-query.controller.ts` — ยืนยัน `PlatformPermissionGuard` + `RequirePlatformPermission('sql_workbench.manage')` เฉพาะ `POST .../execute` เท่านั้น; ไม่มี guard บนอีก 4 route
- **SQL safety validator:** `../carmen-turborepo-backend-v2/apps/micro-business/src/sql-query/sql-validator.ts` — blocklist `FORBIDDEN_LEADING`, flag `allowDangerous` สำหรับ bypass
- **Frontend:** ไม่พบเลย ไม่มีไฟล์ `query-dataset` หรือ `sql-query` ที่ไหนใน `../carmen-inventory-frontend-react` (ยืนยันด้วยการค้นทั่ว repo); ไม่มี route ใน `routes/router.tsx`
- **Prisma ที่เกี่ยวข้อง:** `tb_report_job` (line ~6101), `tb_report_schedule` (line ~6135), `tb_dashboard_bu_widget` (line ~6185), `tb_dashboard_personal_widget` (line ~6205)
