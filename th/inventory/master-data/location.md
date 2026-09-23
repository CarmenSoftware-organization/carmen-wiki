---
title: ที่ตั้ง / สถานที่ (Location)
description: สถานที่จัดเก็บและบริโภคที่จำแนกเป็น inventory, direct หรือ consignment — ขับเคลื่อนการ post สต๊อกและพฤติกรรมการ physical count
published: true
date: '2026-09-23T01:30:00.000Z'
tags: master-data, location, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ที่ตั้ง / สถานที่ (Location)

> **At a Glance**
> **เจ้าของ:** Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_location` &nbsp;·&nbsp; **ใช้โดย:** inventory, GRN, SR, physical count, spot check, PR/PO &nbsp;·&nbsp; `location_type` (`inventory` / `direct` / `consignment`) ตัดสินพฤติกรรมการ posting

![ที่ตั้ง / สถานที่ (Location) screen](/screenshots/master-data/location.png)

![ที่ตั้ง / สถานที่ (Location) detail screen](/screenshots/master-data/location-detail.png)

## 1. คืออะไร / ใครใช้

**สถานที่** เป็นที่อยู่ทางกายภาพหรือทางตรรกะที่สต๊อกอยู่หรือถูกบริโภค — main warehouse, kitchen pass, bar, housekeeping cart, ชั้น consignment ที่ supplier เป็นเจ้าของ ฟิลด์ `location_type` ตัดสินพฤติกรรมการ posting (ยืนยันจาก `inventory-transaction.service.ts` โดยรอบ resync ของโมดูล [inventory](/th/inventory/inventory) เอง — ไม่มีโค้ด GL/journal-posting อยู่เลยในโค้ดเบส ดังนั้นภาษาแบบ "post ไป GL" ด้านล่างอธิบายชั้น inventory-transaction ไม่ใช่รายการบัญชี):

- **`inventory`** — มียอดสต๊อก; receipt และ issue เขียนแถว cost-layer in/out ตามปกติ
- **`direct`** — receipt เขียน layer ขาเข้าตามปกติ **บวก** layer ขาออกที่หักล้างกันโดยอัตโนมัติในต้นทุนเดียวกัน (net zero, ไม่รวมใน average) — ไม่ใช่ "ไม่มีแถว cost-layer" ตามที่ draft ก่อนหน้าบอกไว้
- **`consignment`** — ถือสินค้าที่ supplier เป็นเจ้าของ; ไม่มี code path แยกจาก `inventory` ใน filter การทำธุรกรรม/period-end/นับสต๊อกที่ตรวจสอบ

ระเบียนเดียวกันตั้งค่าพฤติกรรมการนับสิ้นงวด (`physical_count_type` = `yes` / `no`) และจุดส่งของ default ที่ส่งเข้ามายัง location นี้ **บริหารจัดการโดย** Product Admin **อ่านโดย** ทุกเส้นทางการ post inventory

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่ม location | Configuration → Master Data → Location → **New** | บังคับ: `code`, `name`, `location_type` |
| Tag จุดส่งของ default | Location detail | ตั้ง `delivery_point_id` + denormalised `delivery_point_name` |
| ตั้งพฤติกรรมการนับ | Toggle `physical_count_type` | `no` ข้าม period-end count; spot check ยังบังคับใช้ |
| ยกเลิกการใช้งาน | Toggle `is_active` | ซ่อนจาก picker; การ post ประวัติยังเก็บไว้ |
| เปลี่ยน `location_type` | Edit dialog | **ไม่ได้ถูกบล็อกจริง** — `update()` ยอมรับค่าใหม่โดยไม่พบการเช็คการเคลื่อนไหวก่อนหน้า (guard ยังไม่ยืนยัน ดู Edge Cases); การเปลี่ยนหลังมี posting แล้วยังจะทำให้ความหมายของรายงานประวัติเสียหาย |
| กำหนด inventory tree | หน้า location detail | จำกัดว่าสินค้าใดที่มองเห็นได้ที่ location นี้ |
| วางสินค้าบนชั้นวางที่ location นี้ | API เท่านั้น — `products.add[] / products.update[]` มี `shelf_id` (`config_locations/swagger/request.ts:112-139`) | ตั้ง `tb_product_location.shelf_id` + `shelf_code` / `shelf_name` แบบ denormalised; `null` ล้างค่า transfer list สินค้าบนฟอร์ม location (`CreateLocationDto.products: TransferPayload`) ไม่มี shelf picker — picker อยู่บนแท็บ **Location Assignment** ของฟอร์มสินค้าแทน ([product/03-user-flow-product-admin](/th/inventory/product/03-user-flow-product-admin)) |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Code already in use" | `code` ซ้ำในแถว active | เลือก code อื่น |
| **ยังไม่ยืนยัน** — ไม่พบ guard สำหรับการลบหรือเปลี่ยน location_type | `locations.service.ts`'s `delete()` เป็น soft-delete แบบไม่มีเงื่อนไข ไม่มีการเช็คยอด non-zero หรือ SR/GRN ที่เปิดอยู่; `update()` ยอมรับ `location_type` ใหม่โดยไม่เช็คการเคลื่อนไหวก่อนหน้า | เดิมหน้านี้ระบุว่า "cannot delete — non-zero balance", "cannot delete — referenced by open SR/GRN" และ "cannot change location_type after first movement" เป็น error ที่บังคับใช้จริง — ไม่พบทั้งสามในรอบนี้; ให้ถือว่า**ยังไม่ถูกบังคับใช้**จนกว่าจะตรวจสอบซ้ำ |
| ชื่อจุดส่งของในรายงาน | snapshot `delivery_point_name` อาจไม่ตรงหากไม่ได้ sync | Query `delivery_point.name` ผ่าน join สำหรับค่าที่ถูกต้อง |
| `404 SHELF_NOT_FOUND` ตอน update location | รายการ `products.add[]` / `products.update[]` ระบุ `shelf_id` ที่ไม่มีอยู่หรือถูก soft-delete (`locations.service.ts` → `resolveShelfAssignments`, `~1290`) | เลือกชั้นวางที่ยังใช้งานจาก `GET /api/config/:bu_code/shelves` หรือส่ง `shelf_id: null` |

## 4. Edge Cases

- **การเปลี่ยน `location_type` ไม่ถูกบล็อกในปัจจุบัน** ไม่มีโค้ดใน `locations.service.ts` เช็คการเคลื่อนไหวก่อนหน้าก่อนยอมรับ `location_type` ใหม่ใน `update()` การสลับ `inventory` → `direct` หลังมี posting แล้วยังจะทำให้ความหมายของรายงาน inventory-transaction ประวัติเสียหาย — ถือว่าข้ออ้างเดิม "ระบบปฏิเสธ" ยังไม่ยืนยัน/เป็นแค่ design intent
- **ยกเว้นการนับ** — `physical_count_type = no` ข้าม period count แต่ **ไม่** ข้าม spot check
- **Consignment ไม่มี code path แยก (ยืนยันโดยรอบ resync ของโมดูล inventory เอง)** ถูกจัดกลุ่มกับ `inventory` ใน filter ทุกตัวที่ตรวจสอบ (transaction, period-end validate/review, physical-count-period, spot-check, SR from-location) — ถือว่าข้ออ้างเดิม "recognise ตอนบริโภค ไม่ใช่ตอนรับ" ยังไม่ยืนยัน ไม่ใช่พฤติกรรมจริง
- **การจับคู่กับจุดส่งของ** — ฟอร์มอ่าน `delivery_point.name` จาก nested API object ดังนั้นจุดส่งของที่ inactive ที่ผูกไว้กับ location จะยังแสดงชื่อทั้งในโหมดดูและแก้ไข (ฟอร์มแก้ไขส่งชื่อนั้นเป็น `defaultLabel` ให้ lookup widget ซึ่ง list เฉพาะจุดส่งของที่ active เท่านั้น) ฟิลด์ snapshot `delivery_point_name` ยังคงอยู่ในระเบียนสำหรับการอ้างอิง legacy
- **Code uniqueness บังคับใช้ระดับ app** (ไม่มี DB unique constraint)
- **การลบยังไม่ยืนยันว่าถูก guard** `delete()` ตั้ง `is_active: false` + `deleted_at` แบบไม่มีเงื่อนไข — ไม่พบการเช็คยอด on-hand ที่ไม่เป็นศูนย์ หรือการอ้างอิง SR/GRN ที่เปิดอยู่

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_location`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `code` | `String @db.VarChar` | No | รหัสสั้น เช่น `INV1`, `KIT` |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล |
| `location_type` | `enum_location_type` | No | `inventory` (default), `direct` หรือ `consignment` |
| `description` | `String?` | Yes | Free text |
| `delivery_point_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_delivery_point` (เลือกได้) |
| `delivery_point_name` | `String? @db.VarChar` | Yes | สำเนาแสดงผลแบบ denormalised |
| `physical_count_type` | `enum_physical_count_type` | No | `no` (default) — ข้าม; `yes` — รวม |
| `department_account_code` | `String? @db.VarChar` | Yes | รหัสบัญชีแบบ free-text ที่ echo กลับตอน update (`locations.service.ts` `locationData`); ไม่พบผู้บริโภคในโค้ด GL ในรอบนี้ |
| `is_active` | `Boolean?` | Yes | Active flag |
| `note`, `info`, `dimension` | — | Yes | Metadata มาตรฐาน |
| `doc_version` | `Int` | No | เวอร์ชัน optimistic-lock (default `0`) |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** primary key บน `id` FK บน `delivery_point_id` → `tb_delivery_point` `onDelete: NoAction` Uniqueness บน `code` บังคับใช้ที่ app layer

`enum_location_type` values: `inventory`, `direct`, `consignment`
`enum_physical_count_type` values: `no`, `yes`

### 5.2 `tb_location_user` (เปลี่ยนชื่อ 2026-09-04)

junction ผู้ใช้-กับ-location ถูกเปลี่ยนชื่อจาก `tb_user_location` เป็น `tb_location_user` โดย migration `20260904131500_rename_shelf_and_user_location` (index `location_user_user_id_location_id_u` / `_idx`; คอลัมน์ไม่เปลี่ยน: `user_id`, `location_id`, `note`, `info`, `doc_version`, audit) gateway ยังเปิดให้ใช้ผ่านสอง path — `api/config/:bu_code/locations-users` และ `api/config/:bu_code/user-locations` แบบเก่า — และ response ของ location detail ยังฝังมันเป็น `user_location[]` (`common/dto/location/location.serializer.ts:66`) ดังนั้นมีแค่ชื่อตารางเท่านั้นที่ย้าย

### 5.3 คอลัมน์ shelf บน `tb_product_location`

migration `20260814150000_add_location_shelf` เพิ่ม `shelf_id` (FK → `tb_location_shelf`, `onDelete: NoAction`, index `product_location_shelf_id_idx`), `shelf_code` และ `shelf_name` ลงบน junction product-location ชั้นวางเป็นข้อมูลหลักระดับ BU (ไม่ scope ตาม location) — ดู [master-data/shelf](/th/inventory/master-data/shelf)

## 6. กติกาทางธุรกิจ

- **Uniqueness** `code` unique ในแถว active (app-enforced)
- **Deletion guards — ยังไม่ยืนยัน** ไม่พบการเช็ค FK ใน `delete()`; soft-delete สำเร็จโดยไม่มีเงื่อนไขแม้ยอด on-hand ไม่เป็นศูนย์หรือมีการอ้างอิง SR/GRN ที่เปิดอยู่
- **Validation — ยังไม่ยืนยัน** ไม่พบโค้ดที่บล็อกการเปลี่ยน `location_type` หลังการเคลื่อนไหวครั้งแรก; `update()` ยอมรับได้อย่างอิสระ
- **Lifecycle** `is_active = false` ซ่อนจาก picker; รักษาการ post ประวัติ จุดส่งของที่ผูกไว้แล้วและถูก deactivate ในภายหลัง ยังคงแสดงชื่อในฟอร์มดู/แก้ไข location (ฟอร์มอ่าน `delivery_point.name` จาก nested object ไม่ใช่ snapshot field)
- **ยกเว้นการนับ** `physical_count_type = no` ข้าม period count ไม่ใช่ spot check
- **การจับคู่กับจุดส่งของ** ฟอร์ม location แสดงชื่อ live จาก `delivery_point.name` (nested object) ดังนั้น label ที่แสดงจึงเป็นปัจจุบันเสมอ คอลัมน์ `delivery_point_name` เป็น legacy snapshot field ที่ UI ไม่ได้ใช้สำหรับการแสดงผลอีกต่อไป
- **Optimistic lock** PATCH location ต้องส่ง `doc_version`; client ต้อง echo `doc_version` ปัจจุบันตอน save มิฉะนั้นจะได้ `409 Conflict` และ version จะเพิ่มขึ้นเมื่อสำเร็จ ขอบเขตคือ header `tb_location` เท่านั้น — ตาราง junction sub-tables (`tb_location_user`, `tb_product_location`) ไม่ถูก guard
- **การกำหนดชั้นวางถูกตรวจสอบ ไม่ใช่พิมพ์อิสระ** ทุก `shelf_id` ใน `products.add[]` / `products.update[]` ต้อง resolve ไปยังแถว `tb_location_shelf` ที่ยังใช้งาน มิฉะนั้น update ทั้งก้อนล้มเหลวด้วย `SHELF_NOT_FOUND` (`resolveShelfAssignments`, `master/shelf/shelf.helper.ts:109`); `code`/`name` ที่ resolve ได้ถูกคัดลอกลงแถว junction โดย `shelfColumns()`
- **Default sort** `GET /locations` ที่ไม่มี `?sort=` คืน `code:asc, name:asc, id:asc` (`locations.service.ts`, `withDefaultSort`, 2026-09-13)

## 7. การอ้างอิงข้ามโมดูล

- [inventory](/th/inventory/inventory) — ทุกยอดสต๊อก keyed ด้วย location; type ตัดสินว่าจะ track balance หรือไม่
- [good-receive-note](/th/inventory/good-receive-note) — บรรทัด detail ของ GRN เป้าหมาย location ปลายทาง; `location_type` ตัดสินพฤติกรรมการ post ของ inventory-transaction (ไม่มีโค้ด GL/journal-posting อยู่เลยในโค้ดเบส — ยืนยันโดยรอบ resync ของโมดูล [inventory](/th/inventory/inventory) เอง)
- [store-requisition](/th/inventory/store-requisition) — `from_location` / `to_location` ในทุก issue/transfer
- [physical-count](/th/inventory/physical-count) — การนับ scope ไปยัง location ที่ `physical_count_type = yes`
- [spot-check](/th/inventory/spot-check) — เซสชัน enumerate location
- [master-data/shelf](/th/inventory/master-data/shelf) — ลำดับการเดินนับของชั้นวางต่อแถว product-location
- [purchase-request](/th/inventory/purchase-request) และ [purchase-order](/th/inventory/purchase-order) — บรรทัด detail อาจบรรจุ location ปลายทาง

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_location` (line ~1354), `tb_location_shelf` (~1441), `tb_location_user` (~5428), `tb_product_location` (~5334), `enum_location_type` (~229), `enum_physical_count_type` (~51)
- **Migrations:** `20260814150000_add_location_shelf`, `20260904131500_rename_shelf_and_user_location`
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/master/locations/locations.service.ts`; gateway `apps/backend-gateway/src/config/config_locations/` (+ `config_locations-users/`, `config_user-locations/`)
- **E2E:** `../carmen-inventory-frontend-e2e/tests/080-location.spec.ts` (17 กรณี) + `docs/test-cases/gaps/080-location-gap.md` (45 กรณีที่ยังไม่ครอบคลุม)
- **Frontend:** `../carmen-inventory-frontend-react/routes/config/location/`
- **carmen/docs:** `../carmen/docs/settings/locations.md` — wireframes
