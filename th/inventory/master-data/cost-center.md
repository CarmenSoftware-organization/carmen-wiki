---
title: ศูนย์ต้นทุน (Cost Center)
description: กลุ่มศูนย์ต้นทุน ศูนย์ต้นทุน และ allow-list ผังบัญชีต่อศูนย์ (tb_cost_center_group / tb_cost_center / tb_cost_center_account) — มีเฉพาะ API และ Bruno ยังไม่มี route บน frontend
published: true
date: '2026-09-23T01:30:00.000Z'
tags: master-data, cost-center, general-ledger, configuration, carmen-software
editor: markdown
dateCreated: '2026-09-22T18:00:00.000Z'
---

# ศูนย์ต้นทุน (Cost Center)

> **At a Glance**
> **เจ้าของ:** Sysadmin / Finance &nbsp;·&nbsp; **ตาราง:** `tb_cost_center_group` → `tb_cost_center` → `tb_cost_center_account` &nbsp;·&nbsp; **ใช้โดย:** บรรทัด JV ของ [general-ledger](/en/inventory/general-ledger) บนบัญชีที่ flag `is_require_cost_center` &nbsp;·&nbsp; **Permissions:** `configuration.cost_center_group.*`, `configuration.cost_center.*` &nbsp;·&nbsp; **Licence keys:** `configuration.cost_center_group`, `configuration.cost_center` &nbsp;·&nbsp; **UI:** ไม่มี — API + Bruno เท่านั้น ณ 2026-09-22

## 1. คืออะไร / ใครใช้

**ศูนย์ต้นทุน (Cost Center)** คือมิติทางบัญชีที่บรรทัด GL journal ถูกคิดค่าใช้จ่ายไป — outlet, ครัว, ศูนย์รายได้ มันตั้งใจให้**ไม่ใช่**สิ่งเดียวกับ [department](/th/inventory/master-data/department): `tb_department` คือหน่วยองค์กรที่ผู้ใช้สังกัดและเอกสาร PR/SR ถูกออกจาก; `tb_cost_center` คือมิติ GL (comment ใน schema: "ศูนย์ต้นทุน/ศูนย์รายได้ทางบัญชี — คนละความหมายกับ tb_department") ศูนย์ต้นทุนถูกจัดกลุ่มใน `tb_cost_center_group` (พร้อม `color_tag` สำหรับแสดงผล) และแต่ละศูนย์ต้นทุนอาจมี **allow-list บัญชี** — subset ของ[ผังบัญชี](/th/inventory/master-data/chart-of-accounts)ที่อนุญาตให้ post ไป allow-list ว่างหมายถึงอนุญาตทุกบัญชี

เพิ่มเมื่อ 2026-09-04 (`20260904103000_add_cost_center`, design spec ของ backend `docs/superpowers/specs/2026-09-04-cost-center-schema-design.md` ในรีโป backend) เป็นส่วนหนึ่งของการสร้าง GL-core controller ของ gateway, service ของ micro-business, seed ของ permission และ licence และ Bruno collection มีครบทั้งหมด; **ไม่มี route บน frontend** (`grep -r cost-center routes types hooks constant` → 0 hit ไม่มีอะไรใต้ `/config/*` ใน `module-list.ts`) **บริหารจัดการโดย** Sysadmin / Finance ผ่าน API **อ่านโดย** การตรวจสอบ GL JV posting

## 2. งานที่พบบ่อย

| งาน | ที่ไหน (API) | หมายเหตุ |
|---|---|---|
| สร้างกลุ่ม | `POST /api/config/:bu_code/cost-center-groups` | บังคับ `code`, `name`; เลือกได้ `description`, `color_tag` (free text เช่น `#FF8800`), `is_active` |
| สร้างศูนย์ต้นทุน | `POST /api/config/:bu_code/cost-centers` | บังคับ `code`, `name`, `cost_center_group_id`; เลือกได้ `description`, `is_active`, `chart_of_accounts_ids[]` (allow-list เริ่มต้น สร้างใน transaction เดียวกัน) |
| แทนที่ allow-list | `PUT /api/config/:bu_code/cost-centers/:id/accounts` `{ chart_of_accounts_ids: [] }` | แทนที่ทั้งชุด: id ที่ไม่ต้องการแล้วถูก soft-delete, id ใหม่ถูก insert, ตัวซ้ำใน request ถูกยุบรวม รายการว่าง = อนุญาตทุกบัญชี |
| ย้ายศูนย์ต้นทุนไปกลุ่มอื่น | `PATCH …/cost-centers/:id` พร้อม `cost_center_group_id` | กลุ่มต้องมีอยู่และยังใช้งาน |
| List | `GET …/cost-centers`, `GET …/cost-center-groups` | แถวมีข้อมูลกลุ่ม**แบบแบน** เป็น `cost_center_group_code` / `cost_center_group_name` (`cost-center.service.ts:31-33`) — คู่นี้ถูกเขียนก่อนธรรมเนียม nested-object 2026-09-17 และยังไม่ได้ถูกแปลง |
| ยกเลิกการใช้งาน | `is_active = false` ที่ระดับใดก็ได้ | — |
| ลบกลุ่ม | `DELETE …/cost-center-groups/:id` | **ถูกบล็อก** ขณะที่ยังมีศูนย์ต้นทุนที่ใช้งานอ้างอิงอยู่ |
| ลบศูนย์ต้นทุน | `DELETE …/cost-centers/:id` | soft-delete ศูนย์ **และ** แถว `tb_cost_center_account` ทั้งหมดของมันใน transaction เดียว; ไม่มีการเช็คบรรทัด JV |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| `409 COST_CENTER_GROUP_DUPLICATE_CODE` / `409 COST_CENTER_DUPLICATE_CODE` | แถวอื่นที่ยังไม่ถูกลบมี `code` เดียวกัน (pre-check ใน service + partial unique index `costcentergroup_code_live_u` / `costcenter_code_live_u`) | เลือก code อื่น |
| `404 COST_CENTER_GROUP_NOT_FOUND` | id กลุ่มที่ไม่รู้จักตอน read/update/delete กลุ่ม **หรือ** `cost_center_group_id` ที่ไม่รู้จัก / ถูกลบตอน create/update ศูนย์ต้นทุน (`assertGroupExists`) | ใช้กลุ่มที่ยังใช้งาน |
| `404 COST_CENTER_NOT_FOUND` | id ศูนย์ต้นทุนที่ไม่รู้จัก | — |
| `404 COST_CENTER_ACCOUNT_NOT_FOUND` — "One or more chart of accounts entries in the mapping do not exist" | id ใดใน `chart_of_accounts_ids` ไม่ใช่แถว `tb_chart_of_accounts` ที่ยังใช้งาน (`assertAccountsExist`) | เอา id ที่ผิดออก |
| `409 COST_CENTER_GROUP_IN_USE` — "Cost center group is still referenced by cost centers" | `delete()` บนกลุ่มนับแถว `tb_cost_center` ที่ยังใช้งาน (`{ cost_centers: n }` ใน payload ของ error) | ย้ายหรือลบศูนย์ต้นทุนก่อน |
| `409` ตอน PATCH/PUT ด้วย `doc_version` ที่เก่า | Optimistic lock | โหลดใหม่ |

## 4. Edge Cases

- **ความหมายของ allow-list คือ "แทนที่" ไม่ใช่ "เพิ่ม"** `setAccounts` diff แถวที่ยังใช้งานปัจจุบันกับชุดที่ร้องขอ; การส่ง `[]` ล้างรายการ (ซึ่ง*ขยาย*สิ่งที่ศูนย์ post ได้ — ทุกบัญชีกลายเป็นอนุญาต) ทดสอบทั้งสองทิศทาง
- **การลบศูนย์ต้นทุนไม่ถูก guard** เฉพาะกลุ่มเท่านั้นที่มีการเช็ค in-use; ศูนย์ต้นทุนที่ถูกอ้างอิงโดยบรรทัด JV soft-delete ได้อย่างอิสระ (`cost-center.service.ts:266-290`) — ถือว่า "cannot delete — used on journals" **ไม่ถูกบังคับใช้**
- **partial unique index อยู่ใน SQL เท่านั้น** index `*_live_u` ทั้งสาม (`WHERE deleted_at IS NULL`) ไม่อยู่ใน Prisma model; model แสดง unique แบบหลวมกว่า `(code, deleted_at)` / `(cost_center_id, chart_of_accounts_id, deleted_at)` การเปลี่ยนชื่อตารางต้องเขียน `ALTER INDEX … RENAME` ด้วยมือ (comment ใน schema)
- **`color_tag` เป็นข้อความที่ไม่ถูกตรวจสอบ** string ใดก็เก็บได้; รูปแบบ `#RRGGBB` ในตัวอย่าง Bruno เป็นแค่ธรรมเนียม
- **allow-list มีผลตรงไหน** กติกา "บรรทัด JV บนบัญชี `is_require_cost_center` ต้องมีศูนย์ต้นทุนที่อยู่ใน allow-list ของบัญชีนั้น" ถูกบันทึกไว้บน `tb_chart_of_accounts.is_require_cost_center` และบังคับใช้โดย GL JV service — ดู [general-ledger](/en/inventory/general-ledger); ไม่มีอะไรใน service ของโมดูลนี้ตรวจสอบบรรทัด JV

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`, lines ~2976-3063)

### 5.1 `tb_cost_center_group`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `code` | `String @db.VarChar` | No | เช่น `FB` |
| `name` | `String @db.VarChar` | No | เช่น `Food & Beverage` |
| `description` | `String? @db.VarChar` | Yes | Free text |
| `color_tag` | `String? @db.VarChar` | Yes | สีสำหรับแสดงผล |
| `is_active` | `Boolean?` | Yes | Default `true` |
| `note`, `info` | — | Yes | Metadata มาตรฐาน (ตารางนี้ไม่มี `dimension`) |
| `doc_version` | `Int` | No | เวอร์ชัน optimistic-lock |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([code, deleted_at])` map `costcentergroup_code_u`; partial unique `costcentergroup_code_live_u`; index บน `code`, `name` Reverse relation `tb_cost_center[]`

### 5.2 `tb_cost_center`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `code` | `String @db.VarChar` | No | เช่น `FB-01` |
| `name` | `String @db.VarChar` | No | เช่น `Main Restaurant` |
| `description` | `String? @db.VarChar` | Yes | Free text |
| `cost_center_group_id` | `String @db.Uuid` | No | FK → `tb_cost_center_group` (`onDelete: NoAction`) |
| `is_active` | `Boolean?` | Yes | Default `true` |
| `note`, `info`, `dimension` | — | Yes | Metadata มาตรฐาน |
| `doc_version` | `Int` | No | เวอร์ชัน optimistic-lock |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([code, deleted_at])` map `costcenter_code_u`; partial unique `costcenter_code_live_u`; index `costcenter_code_idx`, `costcenter_name_idx`, `costcenter_group_id_idx` Reverse relation `tb_cost_center_account[]`

### 5.3 `tb_cost_center_account`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `cost_center_id` | `String @db.Uuid` | No | FK → `tb_cost_center` (`onDelete: NoAction`) |
| `chart_of_accounts_id` | `String @db.Uuid` | No | FK → `tb_chart_of_accounts` (`onDelete: NoAction`) |
| `doc_version` | `Int` | No | เวอร์ชัน optimistic-lock |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` ไม่มี `note` / `info` / `is_active` |

**Constraints:** `@@unique([cost_center_id, chart_of_accounts_id, deleted_at])` map `costcenteraccount_u`; partial unique `costcenteraccount_live_u`; index บนแต่ละ FK

## 6. กติกาทางธุรกิจ

- **Uniqueness** `code` unique ในแถว non-deleted ทั้งสองระดับ (pre-check ใน service + partial unique index) หนึ่งแถว allow-list ต่อ `(cost_center, account)`
- **การเช็ค referential ตอนเขียน** กลุ่มต้องมีอยู่ตอน create/update ศูนย์ต้นทุน; ทุกบัญชีใน allow-list ต้องมีอยู่ (`assertGroupExists`, `assertAccountsExist`)
- **Deletion guards** กลุ่ม: ถูกบล็อกขณะที่ยังมีศูนย์ต้นทุนที่ใช้งานอ้างอิง ศูนย์ต้นทุน: ไม่มี (cascade แถว allow-list ของตัวเอง) แถว allow-list: ถูกแทนที่ทั้งชุดโดย `PUT :id/accounts`
- **ความหมายของ allow-list** ว่าง = อนุญาตทุกบัญชี; ไม่ว่าง = เฉพาะบัญชีที่ลิสต์ไว้ และเฉพาะเมื่อบัญชีนั้นถูก flag `is_require_cost_center`
- **Lifecycle** `is_active = false` ที่ระดับใดก็ได้; soft-delete ตั้ง `deleted_at` (+ `is_active: false`)
- **Default sort** `code:asc, id:asc` บน list endpoint ทั้งสอง (`withDefaultSort`, 2026-09-13)
- **Optimistic lock** update / patch ต้องส่ง `doc_version`
- **การเข้าถึง** route map `config:cost-center-groups → configuration.cost_center_group`, `config:cost-centers → configuration.cost_center`; แถว permission ถูก seed ไว้ (`seed.permission.data.ts:983-1015`); licence feature `configuration.cost_center`, `configuration.cost_center_group` (`seed.license-feature.data.ts:164-172`) handler ใช้ `AppIdGuard('cost-centers.*')` รวมทั้ง `cost-centers.setAccounts`

## 7. การอ้างอิงข้ามโมดูล

- [chart-of-accounts](/th/inventory/master-data/chart-of-accounts) — เป้าหมายของ allow-list; `is_require_cost_center` คือ flag ที่ทำให้ศูนย์ต้นทุนกลายเป็นข้อบังคับ
- [general-ledger](/en/inventory/general-ledger) — การตรวจสอบและ posting บรรทัด JV
- [master-data/department](/th/inventory/master-data/department) — หน่วย*องค์กร*; ใช้แทนกันกับศูนย์ต้นทุนไม่ได้

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_cost_center_group` (line ~2976), `tb_cost_center` (~3005), `tb_cost_center_account` (~3037)
- **Migration:** `20260904103000_add_cost_center`
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/master/cost-center/cost-center.service.ts` (`setAccounts` `:221`, `delete` `:266`), `master/cost-center-group/cost-center-group.service.ts`; gateway `apps/backend-gateway/src/config/config_cost-centers/` (`@Controller('api/config/:bu_code/cost-centers')`, `PUT :cost_center_id/accounts` `:396`), `config_cost-center-groups/`
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/cost-centers/*.bru` (7 รวม `PUT-set-accounts-*`), `config/cost-center-groups/*.bru` (6)
- **Frontend:** ไม่มี
- **E2E:** ไม่มี
