---
title: ช่วงงวดสินค้าคงคลัง (Inventory Period — เดิมชื่อ Period)
description: ช่วงงวดสินค้าคงคลัง (บัญชี) และ snapshot ต้นทุนต่องวด เปลี่ยนชื่อจาก Period เมื่อ 2026-09-16 — tb_inventory_period*, /system-admin/inventory-period, api/:bu_code/inventory-periods, key system_admin.inventory_period CRUD ธรรมดา
published: true
date: '2026-09-23T01:30:00.000Z'
tags: system-config, period, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ช่วงงวดสินค้าคงคลัง (Inventory Period — เดิมชื่อ Period)

> **At a Glance**
> **เจ้าของ:** Sysadmin / Finance Manager &nbsp;·&nbsp; **ตาราง:** `tb_inventory_period` (+ `tb_inventory_period_snapshot`, `tb_inventory_period_comment`) — เปลี่ยนชื่อจาก `tb_period*` เมื่อ 2026-09-16 &nbsp;·&nbsp; **Route:** `/system-admin/inventory-period` (`/system-admin/period` เดิม redirect) &nbsp;·&nbsp; **Endpoint:** `api/:bu_code/inventory-periods` (`api/:bu_code/periods` เดิมคงไว้เป็น alias ที่ซ่อน) &nbsp;·&nbsp; **Permission / licence key:** `system_admin.inventory_period` &nbsp;·&nbsp; **ใช้โดย:** GRN, stock-in, stock-out/การจ่าย SR, physical count, engine ต้นทุน, status bar ที่ footer &nbsp;·&nbsp; **หน้าจอ admin คือรายการธรรมดา + dialog สร้าง/แก้ไข — ไม่มี action Close/Lock/Reopen เฉพาะ หรือ tab Snapshot เลย**

![ช่วงงวด (Period) screen](/screenshots/system-config/period.png)

## ประกาศการเปลี่ยนชื่อ (2026-09-16)

โมดูลถูกเปลี่ยนชื่อจาก **Period** เป็น **Inventory Period** ในสาม backend commit แบบ breaking เมื่อ 2026-09-16 (`7601e6e83` เปลี่ยนชื่อภายใน, `a92151730` HTTP path, `c8de2fa76` key ของ permission/licence/`api_name`, `3933277dc` ตาราง) เพื่อแยกจากงวดบัญชี GL (`tb_gl_period`, `config/gl-periods` — แนวคิดของโมดูลบัญชีที่อยู่นอกเล่มนี้) และจาก `tb_physical_count_period` หน้านี้คง slug ของ wiki (`period`) ไว้เพื่อให้ลิงก์เดิมยังใช้ได้; ทุกชื่อฝั่งโค้ดด้านล่างเป็นชื่อใหม่

| Surface | ก่อน | หลัง (HEAD) | แหล่ง |
|---|---|---|---|
| ตาราง tenant | `tb_period`, `tb_period_comment`, `tb_period_snapshot` | `tb_inventory_period`, `tb_inventory_period_comment`, `tb_inventory_period_snapshot` | tenant migration `20260916141000_rename_tb_period_to_tb_inventory_period` (`ALTER TABLE … RENAME` เฉพาะ metadata; ชื่อ constraint เปลี่ยน prefix; ชื่อ index ไม่แตะเพราะ schema `map:` ไว้; `enum_period_status` **ไม่** เปลี่ยนชื่อโดยตั้งใจ) |
| HTTP path | `api/:bu_code/periods[/current|/next|/:period_id]` | `api/:bu_code/inventory-periods[/current|/next|/:period_id]` | `apps/backend-gateway/src/application/inventory-periods/inventory-periods.controller.ts:67-416`; path เดิมยัง resolve ผ่าน `inventory-periods-legacy.controller.ts` (`@ApiExcludeController`, guard เดียวกัน service เดียวกัน — alias ที่ deprecated) |
| api name ของ `AppIdGuard` | `period.*` | `inventoryPeriod.findOne` / `findAll` / `create` / `update` / `delete` | controller เดียวกัน |
| Permission resource | `system_admin.period` | `system_admin.inventory_period` (`view`/`create`/`update`/`delete`) | platform migration `20260916140000_rename_period_to_inventory_period`; `seed.permission.data.ts` |
| Licence feature | `system_admin.period` ("Period") | `system_admin.inventory_period` ("Inventory Period") | migration เดียวกัน + `20260916150000_fix_license_group_item_inventory_period_key`; `license-catalog.generated.ts` |
| Licence route map | `app:periods` | `app:inventory-periods` → `system_admin.inventory_period`; `config:period-comments` ก็ชี้ไปที่ key ใหม่ | `packages/prisma-shared-schema-platform/prisma/permission.route-map.ts` |
| Frontend | `routes/system-admin/period/`, `/system-admin/period` | `routes/system-admin/inventory-period/` (`inventory-period-component.tsx`, `-dialog.tsx`, `-card.tsx`, `-form-schema.ts`, `use-inventory-period.ts`, `use-inventory-period-table.tsx`), `/system-admin/inventory-period`; `router.tsx:640-643` คง `period` ไว้เป็น redirect `<Navigate replace>` "so old bookmarks don't break"; `constant/permissions.ts:119` `system_admin.inventory_period`; `constant/module-list.ts:611-615` | FE `06c68975`, `1caecb42` |
| Bruno | `master-data/period/*` | folder **ไม่ได้เปลี่ยนชื่อ** แต่ URL ของทุก request ข้างในชี้ไปที่ `/api/{{bu_code}}/inventory-periods…` แล้ว (Bruno PR #27); `config/period-comment/*` ยังใช้ `api/config/:bu_code/period-comments/:period_id` (controller นั้นไม่ได้เปลี่ยนชื่อ) | `carmen-turborepo-backend-bruno/collections/carmen-inventory/master-data/period/` |
| Comments | controller `config_period-comments`, `tb_period_comment` | path ของ controller ไม่เปลี่ยน (`api/config/:bu_code/period-comments`) ตารางเปลี่ยนชื่อเป็น `tb_inventory_period_comment` | `apps/backend-gateway/src/config/config_period-comments/` |

ลำดับการ deploy สำคัญ: platform migration ต้องรันก่อนหรือพร้อม gateway — gateway ที่เปลี่ยนชื่อ `api_name` ก่อนที่แถว `tb_application_api` ถูกเปลี่ยนชื่อจะตอบ 401 และเด้งผู้ใช้ไปหน้า login (commit message ของ `c8de2fa76`) การเปลี่ยนชื่อตาราง tenant เป็น hard cutover: โค้ดเก่าที่ชี้ไป `tb_period` พังทันทีที่ migration รัน

## สถานะการ implement (ตรวจสอบซ้ำ 2026-09-22)

หน้าจอ `/system-admin/inventory-period` (`inventory-period-component.tsx` + `inventory-period-dialog.tsx`) ยังคงเป็น **รายการ CRUD ทั่วไป**: ค้นหา, filter สถานะ, Add / Generate Next / Export / Print และ dialog แก้ไข row ที่มีฟิลด์ธรรมดา — `fiscal_year`, `fiscal_month`, `start_at`, `end_at` และ **`<Select>` สถานะ** ที่เสนอ `open`/`closed`/`locked` ตรงๆ (`inventory-period-form-schema.ts:17` `z.enum(["open","closed","locked"])`, dialog `:192-207`) ส่งเหมือนฟิลด์อื่นผ่าน `PATCH` สถานะ render เป็นไอคอน + label ในรายการตั้งแต่ 2026-08-24 (`26a403d4`) ยังคงไม่มี button "Close" / "Lock" / "Reopen" เฉพาะ, prompt ยืนยันหรือเหตุผล audit หรือ tab "Snapshot" ที่ไหนในโครงสร้าง component ค่า enum และความหมายของการ์ด posting (§5, §6) ไม่ได้รับผลกระทบจากการเปลี่ยนชื่อ — แต่คำอธิบายการ์ดใน §6 ถูกแก้ในรอบนี้หลังอ่าน `inventory-period.helper.ts`: **`locked` ไม่บล็อกการ post ขาเข้า; มีเพียง `closed` ที่บล็อก**

## 1. คืออะไรและใครใช้

Inventory period นิยามปฏิทินบัญชีที่ ledger สินค้าคงคลังของ Carmen ดำเนินงานบน — หนึ่ง row ต่อเดือนการเงิน ระบุโดย `YYMM` บวก integer `fiscal_year` / `fiscal_month` และช่วงวัน `[start_at, end_at]` ทุกงวดมีสถานะ (`open`, `closed`, `locked`) ที่ควบคุมว่าเอกสารที่มีวันที่ใดสามารถออกเลขและ post ได้ Period คือหน่วยที่ปิดต้นทุนสต๊อกและทำ snapshot: เมื่อ finance ปิดมกราคม จะไม่มี GRN / stock-in ของเดือนมกราคมเพิ่มเติมที่จะ post และยอดปิดกลายเป็นยอดเปิดของเดือนกุมภาพันธ์

`tb_inventory_period_snapshot` เก็บ snapshot สต๊อกต่อ location / ต่อ product / ต่อ lot ณ เวลาหนึ่ง — สร้างโดย engine ต้นทุนและใช้สำหรับ trial balance และ roll-forward ไม่มีหน้าจอใดในโมดูลนี้ render มัน (ดูสถานะการ implement) — มันถูกเขียนและอ่านโดย engine ต้นทุนเท่านั้น

**status bar ที่ footer** ของทุกหน้าจอ (`components/footer/status-bar.tsx`, FE `ad213a11`, 2026-09-18) แสดงงวดปัจจุบันเป็น `YYYY-MM` ข้างเวอร์ชันของแอปและ backend มันอ่านงวดจาก payload `/user/profile` ที่ bar โหลดอยู่แล้ว — *ไม่ใช่* จาก `inventory-periods/current` — และอ่านเวอร์ชัน backend จาก `GET /version` (`{ version, commit }`, `apps/backend-gateway/src/app.controller.ts:71-75`, BE `94b44828d`) โดย fail แบบนุ่มนวลเป็นไม่แสดงอะไรเมื่อ gateway เก่ากว่า endpoint นั้น

**บำรุงรักษาโดย** Sysadmin (โดยทั่วไปคือ Finance Manager) ผ่าน dialog แก้ไขธรรมดา **อ่านโดย** ทุกการ์ด posting และ engine ต้นทุน

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เปิดงวดถัดไป | รายการ Inventory Period → **Generate Next** (button `CalendarPlus`) | `POST api/:bu_code/inventory-periods/next` พร้อม `{ count, start_day }` (`types/inventory-period.ts` `GenerateNextInventoryPeriodDto`); `count` ต้องเป็นบวก (`COMMON_COUNT_MUST_BE_POSITIVE`); service เริ่มจากเดือนถัดจากงวด *open* ล่าสุด ไม่งั้นงวดล่าสุดไม่ว่าสถานะใด ไม่งั้นเดือนปัจจุบัน และสร้างเป็น `open` (`inventory-period.service.ts:315-470`) |
| เปลี่ยนสถานะของงวด | Row → **Edit** → dropdown **Status** → Save | Dialog แก้ไขเดียวกันกับ fiscal year/month/date — การเลือก `closed` หรือ `locked` ที่นี่คือการแก้ฟิลด์ธรรมดา ไม่ใช่ workflow action เฉพาะ; `PATCH` ต้องมี `doc_version` (`COMMON_DOC_VERSION_REQUIRED`, `:243`) |
| หางวดปัจจุบัน | `GET api/:bu_code/inventory-periods/current` | งวดแรกสุดที่สถานะเป็น `open` **หรือ `locked`** (`:478-497`) |
| ดู snapshot | ~~Period detail → Snapshot tab~~ | **ไม่มีหน้าจอนี้อยู่จริง** — snapshot เป็นเรื่องภายในของ costing engine |
| สร้าง snapshot ปิด | Job engine ต้นทุน | เขียน `tb_inventory_period_snapshot` ทุก (location, product, lot); ไม่ได้ trigger จากหน้าจอนี้ |
| Export รายการงวด | รายการ Inventory Period → **Export** | XLSX พร้อมคอลัมน์ period / fiscal year / fiscal month / dates / status |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| `GRN_DATE_OUTSIDE_OPEN_PERIOD` (GRN), error ใน catalog แบบเดียวกันของ stock-in / stock-out | วันที่เอกสาร resolve ไม่เจองวด หรือเจองวด `closed` — ดู §6 | ใช้วันที่ในงวด `open`/`locked`; สำหรับการจ่าย (stock-out / SR) วันที่ต้องอยู่ในงวด *ปัจจุบัน* |
| `PERIOD_ALREADY_EXISTS` / `PERIOD_FISCAL_COMBINATION_EXISTS` | `period` หรือ `(fiscal_year, fiscal_month)` ซ้ำในแถวที่ไม่ถูกลบ | แก้ row ที่มีอยู่ (`packages/error-catalog/src/catalog.ts:959-978`) |
| `PERIOD_NOT_FOUND` | `period_id` ไม่รู้จัก | refresh รายการ |
| `period` ไม่ตรงกับ fiscal date | `period != (fiscal_year-2000) * 100 + fiscal_month` | คำนวณใหม่และแก้ค่าใดค่าหนึ่ง |
| ความไม่ตรงกันของ roll-forward | Closing N ≠ Opening N+1 | ปรากฏใน `diff_amount`; review snapshot (ไม่แสดงใน UI ใดเลย — query โดยตรง) |
| เปลี่ยนสถานะเป็น `closed`/`locked` โดยไม่มีขั้นตอนยืนยัน | คาดหวัง — dialog แก้ไขไม่มี guard เฉพาะสำหรับฟิลด์นี้ | ไม่มีหน้าจอ undo; แก้ row กลับเป็น `open` ถ้านี่คือความผิดพลาด |
| bookmark เก่า `/system-admin/period` | route เปลี่ยนชื่อ | redirect ฝั่ง client ไป `/system-admin/inventory-period` (`router.tsx:640-643`) |
| 401 เด้งไป login ทันทีหลัง deploy | gateway deploy ก่อน platform migration `20260916140000` เปลี่ยนชื่อ `tb_application_api.api_name` | apply migration; ดูประกาศการเปลี่ยนชื่อ |

## 4. กรณีพิเศษ

- **สถานะคือฟิลด์แก้ไขได้ธรรมดา ไม่ใช่ workflow** ผู้ใช้ใดก็ตามที่มี `system_admin.inventory_period.update` สามารถตั้งค่าสถานะใดก็ได้โดยตรง — ไม่มี prompt เหตุผล audit แยกสำหรับการ reopen งวดที่ปิดแล้ว
- **`locked` ไม่ใช่ "closed" สำหรับการ์ด posting** `OPEN_STATUSES = [open, locked]` ใน `inventory-period.helper.ts:18`; ทั้ง `findOpenPeriodForDate` และ `findCurrentOpenPeriod` ยอมรับ `locked` สถานะเดียวที่บล็อกการ post คือ `closed` ถือว่า `locked` เป็น label สำหรับ Finance ที่ไม่มีผลตอน runtime ที่ HEAD
- **การเป็นสมาชิกของวันสุดท้าย** `end_at` เก็บเป็นเที่ยงคืน UTC ของวันสุดท้ายของเดือน การ์ดจึงเทียบแบบวันต่อวัน (`toValidDate` + การ normalise วัน, `:20-42`); เอกสารที่ลงวันที่วันสุดท้ายเป็นของงวดนั้น (bug จริงที่ถูกแก้หลัง baseline — ทุก tenant เคยรายงาน "no open period" ในวันที่ 31)
- **การ์ดรันตรงจุดที่ออกเลขที่เอกสาร** ไม่ใช่แค่ตอนสร้าง — draft ที่สร้างขณะงวดเปิดและ submit หลังงวดปิดจะถูกปฏิเสธตอน submit (`:167-176`)
- **การสร้าง snapshot ใหม่** การรัน close ซ้ำสำหรับงวดเดียวกันจะ overwrite หรือ append ตามนโยบาย Finance; **append ที่ `snapshot_at` ใหม่** คือรูปแบบที่แนะนำเพื่อรักษา audit (พฤติกรรมของ costing engine ยังไม่ยืนยันกับ UI ใดเพราะไม่มี UI)
- **Roll-forward integrity** Opening N+1 ต้องเท่ากับ Closing N สำหรับทุก (location, product, lot); ความไม่ตรงกัน track ใน `diff_amount`

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: tenant schema (`schema.prisma:1223-1351`)

### 5.1 `tb_inventory_period`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `period` | `String @db.VarChar` | No | `YYMM` (เช่น `2609`) |
| `fiscal_year` / `fiscal_month` | `Int @db.Integer` | No | `YYYY` + `1`-`12` |
| `start_at` / `end_at` | `DateTime @db.Timestamptz(6)` | No | เที่ยงคืน UTC ของวันแรก / วันสุดท้าย (ระดับวัน ดู §4) |
| `status` | `enum_period_status` | No | `open` (default), `closed`, `locked` ชื่อ enum ไม่เปลี่ยนจากการเปลี่ยนชื่อ |
| `doc_version` | `Int` | No | Default `0` Optimistic-concurrency token — ดู [system-config/doc-version](/th/inventory/system-config/doc-version) |
| `note` / `info` / `dimension` | — | Mixed | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([period, deleted_at])` (`period_period_u`) + `@@unique([fiscal_year, fiscal_month, deleted_at])` (`period_fiscal_year_month_u`) Index บน `[fiscal_year, fiscal_month]` และ `[period]` (ชื่อ index คงจากตารางเดิม) Reverse relations ไปยัง `tb_inventory_period_snapshot`, `tb_inventory_transaction_cost_layer`, `tb_inventory_period_comment`, `tb_physical_count_period` **`enum_period_status`:** `open`, `closed`, `locked`

### 5.2 `tb_inventory_period_snapshot`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` / `period_id` | `String @db.Uuid` | No | Keys |
| `snapshot_at` | `DateTime @db.Timestamptz(6)` | No | เวลา snapshot ที่แน่นอน (โดยทั่วไป close datetime) |
| `location_id` / `product_id` | `String @db.Uuid` | No | Position keys |
| `location_code` / `location_name` / `product_code` / `product_name` / `product_local_name` / `product_sku` | `String?` | Yes | Denormalised แสดงผล |
| `lot_no` / `lot_index` / `lot_at_date` / `lot_seq_no` | — | Yes | การระบุ lot แบบ optional |
| `opening_qty` / `opening_cost_per_unit` / `opening_total_cost` | `Decimal? @db.Decimal(20,5)` | Yes | ยกจากงวดก่อน |
| `receipt_qty` / `receipt_total_cost` | `Decimal?` | Yes | GRN ในงวด |
| `issue_qty` / `issue_total_cost` | `Decimal?` | Yes | SR / stock-out ในงวด |
| `adjustment_qty` / `adjustment_total_cost` | `Decimal?` | Yes | IA / count / spot-check ในงวด |
| `closing_qty` / `closing_cost_per_unit` / `closing_total_cost` | `Decimal?` | Yes | Position ที่ `snapshot_at` |
| `diff_amount` | `Decimal?` | Yes | Residual จากการปัดเศษ / true-up |
| `doc_version` | `Int` | No | Default `0` |
| `note` / `info` / `dimension` | — | Mixed | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([period_id, snapshot_at, deleted_at])` (`periodsnapshot_period_id_snapshot_at_u`) Index บน `[period_id, snapshot_at]` FK `onDelete: NoAction`

### 5.3 API surface

```
GET    api/:bu_code/inventory-periods            list (default sort status asc, fiscal_year asc, fiscal_month asc)
GET    api/:bu_code/inventory-periods/current    งวดแรกสุดที่ status อยู่ใน (open, locked)
GET    api/:bu_code/inventory-periods/:period_id
POST   api/:bu_code/inventory-periods            { fiscal_year, fiscal_month, start_at, end_at, status? }
POST   api/:bu_code/inventory-periods/next       { count, start_day }
PATCH  api/:bu_code/inventory-periods/:period_id { doc_version, ...fields }
DELETE api/:bu_code/inventory-periods/:period_id
```

ทุก route เป็น `KeycloakGuard` + `AppIdGuard('inventoryPeriod.<verb>')`; RBAC resource `system_admin.inventory_period` ผ่าน route map ของ licence/permission เจ็ด route เดียวกันมีอยู่ใต้ prefix `api/:bu_code/periods…` ที่ deprecated (ซ่อนจาก Swagger)

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** ทั้ง `period` และ `(fiscal_year, fiscal_month)` unique ในกลุ่มที่ไม่ถูก delete; ควรสอดคล้องกัน (`period == (fiscal_year-2000) * 100 + fiscal_month` สำหรับ 2000-2099)
- **Date integrity** `start_at < end_at`; งวด contiguous ไม่ทับซ้อน (Generate Next สร้างแบบนั้น; dialog แก้ไขไม่เช็คการทับซ้อนซ้ำฝั่ง server — ยังไม่ยืนยัน ไม่มี error การทับซ้อนใน catalog)
- **สถานะเป็นฟิลด์อิสระใน UI ไม่ใช่ state machine ที่บังคับ** `<Select>` สถานะของ dialog แก้ไขเสนอทั้งสามค่าโดยไม่มีเงื่อนไขไม่ว่าสถานะปัจจุบันของ row จะเป็นอะไร และไม่มี backend transition guard (เช่น การบล็อก `locked → open`) ใน `inventory-period.service.ts` ถือว่า `open → closed → locked` เป็นวินัยการใช้งาน *ตามเจตนา*
- **การ์ด posting ขาเข้า (GRN, stock-in): วันที่เอกสารต้องอยู่ในงวดที่สถานะเป็น `open` หรือ `locked`** `assertDateInOpenPeriod` — `good-received-note.logic.ts:113`, `good-received-note.verify-create.ts`, `stock-in.service.ts:525`
- **การ์ด posting ขาออก (stock-out, การจ่าย SR): วันที่เอกสารต้องอยู่ในงวด *ปัจจุบัน*** (งวดแรกสุดที่ยัง open/locked) เข้มกว่าโดยตั้งใจเพื่อไม่ให้การจ่ายที่ back-date กิน lot ในลำดับที่ ledger ไม่เคยเห็น — `assertDateInCurrentPeriod`, `stock-out.service.ts:400,534`, `sr-date.helper.ts`
- **`closed` เป็นสถานะเดียวที่บล็อก** หน้านี้ฉบับก่อนระบุ "closed/locked"; แก้เมื่อ 2026-09-22
- **การสร้าง snapshot** `(period_id, snapshot_at)` ต่อ `(location, product, optional lot)`; append ที่ `snapshot_at` ใหม่รักษา audit
- **Roll-forward integrity** Opening N+1 = Closing N ต่อ tuple
- **การ์ดการลบ** งวดที่มี snapshot / cost layer / posting ไม่สามารถ delete (FK เป็น `NoAction`)

## 7. การอ้างอิงข้าม

- [inventory](/th/inventory/inventory) — การเขียน current-stock ผ่านการ์ดงวด
- [costing](/th/inventory/costing) — engine อ่าน movement layer และเขียน snapshot ตอน close
- [good-receive-note](/th/inventory/good-receive-note), [inventory-adjustment](/th/inventory/inventory-adjustment) (stock-in / stock-out) — การตรวจสอบงวดของวันที่ posting
- [store-requisition](/th/inventory/store-requisition) — วันที่จ่ายต้องอยู่ในงวดปัจจุบัน; วันที่ SR ถูกตรึงตอน submit
- [physical-count](/th/inventory/physical-count) — เอกสาร count แช่แข็งกับงวดผ่าน `tb_physical_count_period` (FE อ่าน `period.tb_inventory_period.period` / `.end_at`, `pc-component.tsx:245-248`)
- [spot-check](/th/inventory/spot-check) — การ์ดงวดของการ post variance

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `enum_period_status` (line 1223), `tb_inventory_period` (1229-1261), `tb_inventory_period_comment` (1263-1296), `tb_inventory_period_snapshot` (1298-1351)
- **Migrations:** tenant `20260916141000_rename_tb_period_to_tb_inventory_period`; platform `20260916140000_rename_period_to_inventory_period`, `20260916150000_fix_license_group_item_inventory_period_key`
- **Gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/inventory-periods/inventory-periods.controller.ts` (+ alias `inventory-periods-legacy.controller.ts`)
- **Service / guards:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/inventory-period/inventory-period.service.ts`; `.../inventory/inventory-period.helper.ts` (`findOpenPeriodForDate`, `findCurrentOpenPeriod`, `assertDateInOpenPeriod`, `assertDateInCurrentPeriod`)
- **Frontend:** `../carmen-inventory-frontend-react/routes/system-admin/inventory-period/`; `types/inventory-period.ts`; footer `components/footer/status-bar.tsx`, `hooks/use-backend-version.ts`
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/master-data/period/` (URL เป็น `/inventory-periods` แล้ว), `config/period-comment/`
- **E2E:** `../carmen-inventory-frontend-e2e/docs/test-cases/1105-system-period.md` — แคตตาล็อกเท่านั้น (32 case ตรวจสอบซ้ำกับ `routes/system-admin/inventory-period` เมื่อ 2026-09-20; ไม่มี Playwright spec)
