---
title: การ map ผังบัญชี (Chart of Account Mapping)
description: ตาราง location x item group x movement ที่กำหนดบัญชี GL และ cost center ที่การเคลื่อนไหว inventory (GRN, CN, adjustment, SR) ถูก export ไป — ลำดับ resolve, override, generate, review, API
published: true
date: '2026-10-27T15:00:00.000Z'
tags: master-data, account-mapping, chart-of-accounts, general-ledger, configuration, carmen-software
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# การ map ผังบัญชี (Chart of Account Mapping)

> **At a Glance**
> **เจ้าของ:** Sysadmin / Finance &nbsp;·&nbsp; **ตาราง:** `tb_account_mapping` + `enum_account_mapping_{type,movement,origin}` &nbsp;·&nbsp; **Route:** `/config/chart-of-account-mapping` (แท็บ **AP** / **GL**) &nbsp;·&nbsp; **API:** `api/:bu_code/account-mapping` &nbsp;·&nbsp; **Permission:** `configuration.chart_of_account_mapping.*` &nbsp;·&nbsp; **Licence key:** `configuration.chart_of_account_mapping` &nbsp;·&nbsp; แทนที่หน้าจอ mock แบบอ่านอย่างเดียวเดิม (หมายเหตุ "ไม่มี gateway endpoint" บนหน้า landing ของโมดูลนี้เวอร์ชันก่อนล้าสมัยแล้ว)

## 1. คืออะไรและใครใช้

เอกสาร inventory ไม่มีบัญชี GL **account mapping** คือ lookup ที่บอกว่า สำหรับการเคลื่อนไหวสต๊อกที่ *location* ของสินค้าใน *item group* ควร debit/credit บัญชีใด และคิดเข้า cost center ใด มีหนึ่งแถวต่อ **location x item group x movement** (บวก **adjustment type** สำหรับ adjustment) แถวเก็บเฉพาะสิ่งที่ผู้ใช้ *override*; บัญชีและ cost center ที่แสดงจะถูก **resolve** ใหม่ทุกครั้งจากต้นไม้การจัดประเภทสินค้าและ location

| แท็บ (`mapping_type`) | Movement | แถวกำหนดอะไร |
|---|---|---|
| **AP** | `grn`, `cn` | บัญชีฝั่งเจ้าหนี้ของ goods-receipt / credit-note (อีกด้านของ debit inventory) |
| **GL** | `grn`, `cn`, `sr_in`, `sr_out`, `adjustment` | บัญชีฝั่ง inventory/direct ของ movement เดียวกัน, ขา in/out ของ store-requisition และหนึ่งแถวต่อ adjustment type สำหรับ adjustment แบบ stock-in/out |

consumer ที่ใช้งานจริงเพียงตัวเดียวที่พบคือ external export API (`GET api/ext/v1/gl-journals` สำหรับ SR / stock-in / stock-out, `GET api/ext/v1/ap-invoices` สำหรับ GRN / CN) ซึ่งเรียก `AccountMappingService.resolveKeys` ผ่าน `export-core.service.ts` - **อ่านอย่างเดียว ไม่สร้างแถว** `resolveForPosting` (แทรก key ที่ขาดด้วย `origin = auto_posting`, `is_reviewed = false`) มีอยู่แต่ comment ของมันเองระบุว่า **ยังไม่มีผู้เรียก** การ posting inventory ในแอปยังไม่เขียน ledger entry ใดๆ (ดู [general-ledger/gl-posting](/th/inventory/general-ledger/gl-posting))

**บำรุงรักษาโดย** Sysadmin / Finance **อ่านโดย** การ export ทางบัญชี; cost center เริ่มต้นมาจาก [location](/th/inventory/master-data/location) และบัญชีเริ่มต้นมาจาก [ต้นไม้ category ของสินค้า](/th/inventory/product/category)

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้างแถว | ปุ่ม **Generate** (dialog) -> `POST /generate` `{ mode: used \| all, mapping_type? }` | `used` = เฉพาะคู่ (location, item group) ที่ปรากฏบน product-location, GRN, CN, stock-in/out หรือบรรทัด SR แล้ว; `all` = ทุก location ที่ active และไม่ใช่ consignment x ทุก item group ที่ active ถ้าไม่ส่ง `mapping_type` จะ generate ทั้งสองแท็บ แถวที่มีอยู่แล้วไม่ถูกแตะ (`ON CONFLICT DO NOTHING`); response `{ created, existing }` ต่อแท็บ แถวที่ generate เริ่มด้วย `is_reviewed = true` |
| หาช่องว่าง | chip สถานะ: **Incomplete**, **Unreviewed**, **Overridden**, **Default** | จำนวนครอบคลุมทั้งแท็บ ไม่ใช่เฉพาะหน้า; badge ของแท็บแสดงจำนวน incomplete |
| Override หนึ่งแถว | แถว -> edit sheet -> `PATCH :id` `{ account_code?, cost_center_id?, doc_version }` | `null` = ล้าง override และถอยกลับไปใช้ค่าเริ่มต้น; ไม่ส่ง = ไม่เปลี่ยน การบันทึกทำให้แถวเป็น reviewed |
| Override หลายแถว | เลือกแถว -> **Edit selected** -> `POST /batch-update` | ค่าเดียวใช้กับได้สูงสุด 100 แถว; บันทึกเท่าที่ทำได้ (ดู § 3) |
| Mark reviewed | เลือกแถว -> **Mark reviewed** -> `POST /review` `{ ids }` (1-100) | พลิกเฉพาะแถวที่ยังไม่ reviewed |
| Dry-run key | `POST /resolve` `{ lines: [...] }` (1-500 key) | อ่านอย่างเดียว; key ที่ไม่มีแถวจะถูก resolve แบบ virtual |

ตัวกรองของ list: location (หลายค่า), ประเภท location (`inventory` / `direct`), category, sub-category, item group, movement, adjustment type (หลายค่า), status, ค้นหาข้อความอิสระบนรหัสบัญชีที่ resolve แล้ว, รหัส/ชื่อ location และรหัส/ชื่อ item group คอลัมน์ที่ sort ได้: `location`, `location_type`, `category`, `sub_category`, `item_group`, `movement`, `adjustment_type`, `cost_center`, `account` (ค่า `sort` อื่นได้ 400) `perpage` ถูก clamp เป็น 1-100 แถบตัวกรองไม่ซ่อน location / category ที่ inactive (แถวอาจชี้ไปยังสิ่งที่ถูกปิดไปแล้ว)

## 3. การตรวจสอบและ Error

| อาการ / ข้อความ | สาเหตุ | การดำเนินการ |
|---|---|---|
| `422 ACCOUNT_MAPPING_ACCOUNT_INVALID` | `account_code` ไม่ใช่รหัส [chart-of-accounts](/th/inventory/master-data/chart-of-accounts) ที่ active (`is_active` เป็น true หรือ null) | เลือกบัญชีที่ใช้งานอยู่ |
| `422 ACCOUNT_MAPPING_COST_CENTER_INVALID` | `cost_center_id` ไม่รู้จักหรือ inactive | เลือก [cost center](/th/inventory/master-data/cost-center) ที่ใช้งานอยู่ |
| `404 ACCOUNT_MAPPING_NOT_FOUND` | id ของแถวที่ไม่รู้จักบน `PATCH` | Reload list |
| `COMMON_DOC_VERSION_REQUIRED` / `409` | `PATCH` ไม่มี `doc_version` ที่เป็นตัวเลข หรือเป็นค่าเก่า (optimistic lock) | Reload แล้วลองใหม่ |
| ผล batch `{ updated, conflicts, not_found }` | `doc_version` ของแถวไม่ตรง -> `conflicts`; ถูกลบ -> `not_found` ค่าเป้าหมายที่ไม่ถูกต้องทำให้ **ทั้ง** batch ล้มเหลวด้วย 422 ก่อนเขียนแถวใดๆ | UI คงแถวที่ล้มเหลวไว้ในการเลือกและรายงานผลบางส่วน |
| แถวแสดง badge **issue** | `missing_inventory_account`, `missing_direct_account` (ไม่มีบัญชีที่ item group, sub-category หรือ category สำหรับประเภท location นั้น), `missing_ap_account`, `missing_adjustment_account` (แถว AP และ adjustment *ไม่มี* ค่าเริ่มต้น), `account_not_in_coa` (รหัสที่ resolve ไม่มีอยู่ใน COA), `missing_cost_center` (ไม่มี override และ location ไม่มี) | ตั้งบัญชีบน category tree, ตั้ง cost center บน location หรือ override แถว |

## 4. Edge Cases

- **ลำดับการ resolve (บัญชี)** แถว GL สำหรับ `grn` / `cn` / `sr_in` / `sr_out`: row override -> item group -> sub-category -> category โดยอ่านบัญชี **Inventory** สำหรับ location แบบ `inventory` และบัญชี **Direct** สำหรับ location แบบ `direct` (`tb_product_account_code_mapping`, `account_type` `inventory` / `direct`) **แถว AP และแถว GL `adjustment` ใช้เฉพาะ override** - ไม่มี fallback ไปยัง vendor, ค่าเริ่มต้นของ BU, adjustment type หรือบัญชีของสินค้า (commit `db3544c76` ถอด fallback เหล่านั้นออก) ดังนั้น `tb_adjustment_type.chart_of_accounts_id` และ `tb_vendor.ap_chart_of_accounts_id` จึงไม่ป้อนตารางนี้
- **ลำดับการ resolve (cost center)** Row override -> `cost_center_id` ของ location ไม่มี fallback เพิ่ม
- **Location แบบ consignment ถูกข้าม** โดย resolver (`skip = true`) และไม่เคยถูก generate
- **ค่าเริ่มต้นเป็นแบบ live, override เป็นแบบ sticky** การเปลี่ยนบัญชีของ category เปลี่ยนทุกแถวที่ไม่ได้ override พร้อมกัน; แถวที่ override ยังคงค่าเดิม ใช้ **Overridden** เพื่อหาข้อยกเว้น
- **Cascade จาก category tree** การบันทึกบัญชีบน category / sub-category / item group อาจเขียนทับบัญชีประเภทเดียวกันบนทุก descendant (และสินค้า) เมื่อผู้ใช้ยืนยัน dialog cascade - ดู [product/category](/th/inventory/product/category) § 2 ซึ่งเปลี่ยนสิ่งที่แถวเหล่านี้ resolve ได้
- **Generate `used` เป็น snapshot** คู่ location x item group ใหม่ที่ปรากฏทีหลังจะไม่มีแถวจนกว่าจะรัน **Generate** อีกครั้ง (หรือเมื่อ wire แล้ว จนกว่า posting จะสร้างให้อัตโนมัติ)
- **`origin`** บันทึกว่าแถวถือกำเนิดอย่างไร: `generated_all`, `generated_used`, `auto_posting`
- **ไม่กระทบ inventory costing** Cost layer, valuation และ stock ledger ไม่เคยอ่านตารางนี้

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: tenant schema, migration `20261014100100_account_mapping` และ `20261016140000_account_mapping_contra_defaults`

### 5.1 `tb_account_mapping`

| Field | Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `UUID` | No | Primary key |
| `mapping_type` | `enum_account_mapping_type` | No | `AP` \| `GL` |
| `location_id` | `UUID` FK -> `tb_location` | No | |
| `product_item_group_id` | `UUID` FK -> `tb_product_item_group` | No | |
| `movement` | `enum_account_mapping_movement` | No | `grn` \| `cn` \| `adjustment` \| `sr_in` \| `sr_out` |
| `adjustment_type_id` | `UUID` FK -> `tb_adjustment_type` | Yes | จำเป็นเมื่อ `movement = adjustment` เท่านั้น (`accountmapping_adjustment_type_ck`) |
| `account_code` | `VARCHAR` | Yes | **override**; string รหัสธรรมดา ไม่มี FK ไป `tb_chart_of_accounts` (validate ตอนเขียนเท่านั้น) |
| `cost_center_id` | `UUID` FK -> `tb_cost_center` | Yes | override ของ cost center |
| `origin` | `enum_account_mapping_origin` | No | `generated_all` \| `generated_used` \| `auto_posting` |
| `is_reviewed` | `Boolean` | No | Default `false` |
| `doc_version` | `Int` | No | Optimistic lock, default `0` |
| Audit columns | - | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `accountmapping_type_movement_ck` - AP จับคู่กับ `grn` / `cn` เท่านั้น; GL จับคู่กับ movement ทั้งห้าแบบ (ผ่อนคลายโดย `…_contra_defaults`; migration เดิมอนุญาต GL เฉพาะ `adjustment`, `sr_in`, `sr_out`) Partial unique index `accountmapping_key_live_u` บน `(mapping_type, location_id, product_item_group_id, movement, COALESCE(adjustment_type_id, nil-uuid)) WHERE deleted_at IS NULL` Index บน `(mapping_type, location_id)` และ `product_item_group_id`

คอลัมน์ที่เกี่ยวข้องซึ่งเพิ่มใน migration เดียวกัน: `tb_location.cost_center_id` (FK -> `tb_cost_center`, index `location_cost_center_id_idx`), ค่า `direct` ของ `enum_account_type`, `tb_adjustment_type.chart_of_accounts_id` (ไม่มี FK)

## 6. กฎทางธุรกิจ

- **Override ถูก validate ตอนเขียนเท่านั้น** (รหัส COA ที่ active / cost center ที่ active) บัญชีที่ถูกปิดภายหลังยังอยู่บนแถว; `account_not_in_coa` เกิดเมื่อรหัสที่ resolve ไม่มีแถวใน `tb_chart_of_accounts` เลย
- **Optimistic locking** บน `PATCH` และต่อรายการใน batch update; `review` และ `generate` ไม่มี version
- **การเข้าถึง** Gateway `@Controller('api/:bu_code/account-mapping')` ด้วย `KeycloakGuard` + `PermissionGuard` บน resource `configuration.chart_of_account_mapping` (`view` สำหรับ list/resolve, `update` สำหรับ patch/review/batch-update, `create` สำหรับ generate) และ `AppIdGuard('account-mapping.*')`; รายการ route-map `app:account-mapping`; เมนูถูก gate ด้วย licence
- **นิยามสถานะ** *Incomplete* = บัญชีหรือ cost center ที่ resolve เป็น null; *Overridden* = มี `account_code` ที่ไม่ว่างหรือ `cost_center_id` บนแถว; *Default* = ไม่มีทั้งสอง; *Unreviewed* = `is_reviewed = false` จำนวนไม่สนใจตัวกรอง status แต่ใช้ตัวกรองอื่นทั้งหมด

## 7. การอ้างอิงข้ามโมดูล

- [chart-of-accounts](/th/inventory/master-data/chart-of-accounts) - รหัสที่ override ต้องมีอยู่
- [cost-center](/th/inventory/master-data/cost-center) และ [location](/th/inventory/master-data/location) - cost center เริ่มต้นอยู่บน location
- [product/category](/th/inventory/product/category) - ที่ตั้งและ cascade ค่าเริ่มต้นของบัญชี Inventory / Direct
- [adjustment-type](/th/inventory/master-data/adjustment-type) - หนึ่งแถว GL ต่อ adjustment type
- [general-ledger/gl-posting](/th/inventory/general-ledger/gl-posting) - เอนจิน posting JV ที่ inventory ยังไม่เรียก

## 8. แหล่งอ้างอิง

- **Backend:** `../carmen-turborepo-backend/apps/micro-business/src/master/account-mapping/` (`account-mapping.resolver.ts` - กฎการ resolve และ status flag; `account-mapping.service.ts` - `findAll` `:211`, `update` `:500`, `review` `:535`, `batchUpdate` `:554`, `generate` `:615`, `resolve` `:706`, `resolveForPosting` `:720`; `dto/account-mapping.dto.ts`); gateway `apps/backend-gateway/src/application/account-mapping/account-mapping.controller.ts`; consumer `apps/micro-business/src/inventory/accounting-export/export-core.service.ts`; error catalog `ACCOUNT_MAPPING_*`
- **Migrations:** `20261014100100_account_mapping`, `20261014100000_account_type_direct`, `20261016140000_account_mapping_contra_defaults`
- **Frontend:** `../carmen-frontend/routes/config/chart-of-account-mapping/` (`coam-component.tsx`, `use-account-mapping.ts`, `coam-generate-dialog.tsx`, `coam-edit-sheet.tsx`, `coam-batch-edit-sheet.tsx`, `coam-filter-fields.ts`), `types/chart-of-account-mapping.ts`
- **E2E:** `../carmen-frontend-e2e/tests/081-chart-of-account-mapping.spec.ts` (ไม่ได้ตรวจในรอบนี้) **Bruno:** ไม่พบ request `account-mapping`
