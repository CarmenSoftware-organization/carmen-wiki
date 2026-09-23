---
title: ชั้นวาง (Shelf)
description: ข้อมูลหลักชั้นวางระดับ BU (ลำดับการเดินนับ) กำหนดต่อแถว product-location — เพิ่มเมื่อ 2026-08 และแยกออกจาก location เมื่อ 2026-08-20
published: true
date: '2026-09-23T01:30:00.000Z'
tags: master-data, shelf, location, configuration, carmen-software
editor: markdown
dateCreated: '2026-09-22T18:00:00.000Z'
---

# ชั้นวาง (Shelf)

> **At a Glance**
> **เจ้าของ:** Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_location_shelf` &nbsp;·&nbsp; **ใช้โดย:** การกำหนด product ↔ location (`tb_product_location.shelf_*`) &nbsp;·&nbsp; **Permission:** `configuration.location_shelf.{view,create,update,delete}` &nbsp;·&nbsp; **Licence key:** `configuration.location_shelf` &nbsp;·&nbsp; รายการชั้นวาง / rack ระดับ BU พร้อมลำดับการเดินนับ `sequence_no`; **ไม่ได้** scope ตาม location แม้ชื่อตารางจะบอกอย่างนั้น

## 1. คืออะไร / ใครใช้

**ชั้นวาง (Shelf)** ตั้งชื่อ rack, bin หรือช่องทางกายภาพที่สินค้าวางอยู่ภายใน location จัดเก็บ — "Dry Rack A1", "Walk-in door shelf", "Bar back-shelf 3" master เป็นรายการแบนหนึ่งชุดต่อหน่วยธุรกิจ; ส่วน *การกำหนด* ชั้นวางให้สินค้าที่ location หนึ่งอยู่บนแถว junction `tb_product_location` (`shelf_id` + `shelf_code` / `shelf_name` แบบ denormalised) `sequence_no` คือลำดับที่ผู้นับเดินผ่านชั้นวาง เพื่อให้ count sheet เดินตามเส้นทางจริงในสโตร์ได้

เอนทิตีนี้มีประวัติสั้น ๆ สามขั้นที่อธิบายชื่อแปลก ๆ ของมัน:

| Date | Change | Migration |
| --- | --- | --- |
| 2026-08-14 | สร้างแบบ **scope ตาม location** เป็น `tb_location_shelf` พร้อม FK `location_id` และ uniqueness `(location_id, code)` / `(location_id, name)`; เพิ่มคอลัมน์ `shelf_*` ลง `tb_product_location` | `20260814150000_add_location_shelf` |
| 2026-08-20 | Backend "แยก shelf เป็น master ของตัวเอง" — ตัด `location_id` ออก uniqueness กลายเป็นระดับ BU ตารางเปลี่ยนชื่อเป็น `tb_shelf`; frontend ตัดคอลัมน์/picker ของ location ออกในสัปดาห์เดียวกัน (`d447559f`) | `20260820120000_rename_location_shelf_to_shelf` |
| 2026-09-04 | ตารางเปลี่ยนชื่อ **กลับ** เป็น `tb_location_shelf` (ชื่อ index `location_shelf_*`) โดยไม่มีการเปลี่ยนคอลัมน์; HTTP path ยังคงเป็น `/shelves` permission/licence key ยังคงเป็น `configuration.location_shelf` | `20260904131500_rename_shelf_and_user_location` |

ดังนั้นวันนี้: **รายการชั้นวางหนึ่งชุดต่อ BU ใช้ซ้ำได้ที่ทุก location** แท็บ Location Assignment ของ frontend ยังล้างชั้นวางที่เลือกเมื่อ location เปลี่ยน (`pd-tab-locations.tsx:197-198`, comment "shelf ผูกกับ location") — นั่นเป็นความสะดวกของ UI ไม่ใช่กติกาฝั่ง backend **บริหารจัดการโดย** Product Admin ใต้ Configuration → Shelf (`/config/shelf`) **อ่านโดย** ฟอร์มสินค้า, payload `products[]` ของ location และ (ตามเจตนา ยังไม่ใช่ตามโค้ด) physical count / spot check

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มชั้นวาง | Configuration → Shelf → **New** (dialog) | บังคับ: `code`, `name`; เลือกได้ `description`, `sequence_no` (จำนวนเต็ม ≥ 1 ใน Zod schema ของ frontend; จำนวนเต็ม nullable บน API), `is_active` (default `true`) |
| วางสินค้าบนชั้นวาง | Product → แท็บ **Location Assignment** → คอลัมน์ **Shelf** (`LookupShelf` แสดงเฉพาะชั้นวางที่ active) | ส่ง `locations.add[] / update[].shelf_id`; backend คัดลอก `code`/`name` ลงแถว junction |
| แบบเดียวกัน จากฝั่ง location | API เท่านั้น — `PATCH /locations/:id` `products.add[] / update[].shelf_id` | transfer list สินค้าบนฟอร์ม location ไม่มี shelf picker |
| ล้างการกำหนดชั้นวาง | ส่ง `shelf_id: null` บนแถว product-location | ไม่ส่งฟิลด์นี้เพื่อคงค่าเดิม |
| ดูว่าอะไรอยู่บนชั้นวาง | `GET /api/config/:bu_code/shelves/:id` | detail เพิ่ม `product_count` + `products[]` (`product_code`, `product_name`, `product_local_name`, `product_sku`, `location_code`, `location_name`) เรียงตามรหัสสินค้า (`shelf.helper.ts:16-70`); endpoint แบบ list ไม่มีรายการสินค้า |
| ยกเลิกการใช้งาน | Toggle `is_active` | ซ่อนจาก lookup ของฟอร์มสินค้า (`lookup-shelf.tsx:41` filter `is_active`); การกำหนดที่มีอยู่ยังเก็บ snapshot ไว้ |
| ลบ | action **Delete** | **ถูกบล็อก** ขณะที่ยังมีแถว `tb_product_location` ที่ยังใช้งานอ้างอิงชั้นวางนี้ — เป็นหนึ่งใน delete guard ของข้อมูลหลักไม่กี่ตัวที่มีอยู่จริง |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| `409 SHELF_ALREADY_EXISTS` — "Shelf with this code or name already exists" | ชั้นวางอื่นที่ยังไม่ถูกลบมี `code` เดียวกัน **หรือ** `name` เดียวกัน (ไม่สนตัวพิมพ์เล็กใหญ่, `shelf.service.ts` `create()` / `update()`) | เลือก code *และ* name ที่ต่างออกไป |
| `404 SHELF_NOT_FOUND` | id ที่ไม่รู้จักหรือถูก soft-delete ตอน update/delete — หรือจาก endpoint ของ product / location มี `shelf_id` ใน `locations[]` / `products[]` ที่ resolve ไม่ได้ (`resolveShelfAssignments`) | ใช้ id ชั้นวางที่ยังใช้งานหรือ `null` |
| `409 SHELF_IN_USE` — "Shelf is still assigned to products and cannot be deleted" | `delete()` นับแถว `tb_product_location` ที่ `shelf_id = id AND deleted_at IS NULL` | ย้ายหรือล้างการกำหนดก่อน |
| `409` ตอน PATCH/PUT ด้วย `doc_version` ที่เก่า | Optimistic lock — `update({ where: { id, doc_version } })` | โหลดใหม่แล้วส่งอีกครั้ง |
| "Sequence must be at least 1" | Zod ของ frontend (`shelf-form-schema.ts`) — ค่าว่างถูกส่งเป็น `undefined` ไม่ใช่ `0` | ปล่อยว่างเพื่อให้ default ของ backend (`1`) ทำงาน |

## 4. Edge Cases

- **Uniqueness ของชื่อเข้มงวดเท่ากับของ code** ทั้ง `location_shelf_code_u` และ `location_shelf_name_u` เป็น DB-unique (ร่วมกับ `deleted_at`) และ service เช็คทั้งคู่แบบไม่สนตัวพิมพ์ก่อน insert — สอง location ไม่สามารถต่างมีชั้นวางชื่อ "Top shelf" ได้; ให้ตั้งชื่อ "KIT Top shelf" / "BAR Top shelf"
- **`sequence_no` ไม่ unique** และ default เป็น `1` ดังนั้นรายการที่เพิ่งสร้างใหม่จะมีทุกชั้นวางอยู่ที่ตำแหน่ง 1; list เรียง `sequence_no:asc, code:asc, id:asc` (`withDefaultSort`) ทำให้ code เป็น tiebreaker ที่มีผลจริง
- **body ตัวอย่างใน Bruno ล้าสมัย** `config/location-shelves/POST-create-config-location-shelves.bru` ยังแสดง `location_id` ใน `body:json` จาก contract 2026-08-14; request DTO (`common/dto/shelf/shelf.dto.ts`) ไม่มีฟิลด์นี้ และ docs block ในไฟล์เดียวกันบอกถูกต้องว่าชั้นวางเป็นระดับ BU
- **โค้ดการนับยังไม่อ่านชั้นวาง** grep `apps/micro-business/src/inventory/` หา `shelf` พบแค่ serializer ของ stock-card / wastage ที่ echo `shelf_code`; ทั้ง physical-count และ spot-check ไม่เรียงบรรทัดตาม `sequence_no` ถือว่า "count sheet เดินตาม walk order" เป็น design intent
- **Snapshot vs. ชื่อ live** `tb_product_location.shelf_name` ถูกคัดลอก ณ เวลากำหนด; การเปลี่ยนชื่อชั้นวางไม่ refresh แถวที่มีอยู่ (ไม่พบโค้ด backfill — รูปแบบเดียวกับ `delivery_point_name` บน location)
- **E2E ส่วนใหญ่ถูกเลื่อน** `tests/083-shelf.spec.ts` รัน 2 กรณี smoke/error-state; บล็อก CRUD (`TC-SHLF-030001…`) เป็น `test.fixme` "deferred until backend endpoint is live" แม้ว่า endpoint จะมีแล้วตอนนี้

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`, line ~1441)

### 5.1 `tb_location_shelf`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key (`gen_random_uuid()`) |
| `code` | `String @db.VarChar` | No | รหัสสั้น เช่น `A-01` |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล เช่น `Dry Rack A1` |
| `description` | `String?` | Yes | Free text |
| `sequence_no` | `Int?` | Yes | ลำดับการเดินนับ; default `1` |
| `is_active` | `Boolean?` | Yes | Active flag, default `true` |
| `note`, `info`, `dimension` | — | Yes | Metadata มาตรฐาน (default `{}` / `[]`) |
| `doc_version` | `Int` | No | เวอร์ชัน optimistic-lock (default `0`) |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([code, deleted_at])` map `location_shelf_code_u`; `@@unique([name, deleted_at])` map `location_shelf_name_u` Index `location_shelf_code_idx`, `location_shelf_name_idx` Reverse relation `tb_product_location[]` (FK `tb_product_location.shelf_id`, `onDelete: NoAction`, index `product_location_shelf_id_idx`) ไม่มีคอลัมน์ `location_id`

### 5.2 คอลัมน์การกำหนดบน `tb_product_location`

| Field | Prisma Type | คำอธิบาย |
| --- | --- | --- |
| `shelf_id` | `String? @db.Uuid` | FK → `tb_location_shelf.id`; nullable เพราะไม่ใช่ทุก location ที่มีชั้นวาง |
| `shelf_code` / `shelf_name` | `String? @db.VarChar` | สำเนา denormalised ที่ `shelfColumns()` (`master/shelf/shelf.helper.ts:149`) เขียนทุกครั้งที่ตั้ง `shelf_id` |

## 6. กติกาทางธุรกิจ

- **Uniqueness** `code` และ `name` แต่ละตัว unique ในแถว non-deleted บังคับใช้ที่ DB และเช็คล่วงหน้าแบบไม่สนตัวพิมพ์ใน service
- **Deletion guard — ยืนยันแล้ว** `delete()` คืน `SHELF_IN_USE` ขณะที่ยังมีแถว product-location ที่ใช้งานอ้างอิงชั้นวาง; มิฉะนั้น soft-delete (`is_active: false`, `deleted_at`)
- **การเช็ค referential ตอนกำหนด** การสร้าง/แก้ไขสินค้า (`products.service.ts:2035`, `:2244`) และการแก้ไข location (`locations.service.ts:~1290`) resolve ทุก `shelf_id` ที่ส่งมาเทียบกับชั้นวางที่ยังใช้งานก่อน และทำให้ request ทั้งก้อนล้มเหลวด้วย `SHELF_NOT_FOUND` ถ้ามีตัวใดไม่รู้จัก
- **Lifecycle** `is_active = false` ซ่อนชั้นวางจาก lookup ของฟอร์มสินค้า; การกำหนดในอดีตยังเก็บ `shelf_code` / `shelf_name`
- **Default sort** `sequence_no:asc, code:asc, id:asc` เมื่อไม่ส่ง `?sort=`
- **Optimistic lock** PATCH/PUT ต้องส่ง `doc_version` ปัจจุบัน
- **การเข้าถึง** guard ของ gateway: `KeycloakGuard` + `PermissionGuard` บน controller, `AppIdGuard('shelf.*')` ต่อ handler; แถว permission `configuration.location_shelf:{view,create,update,delete}` ถูก seed ไว้ (`seed.permission.data.ts:895-910`), licence feature `configuration.location_shelf` (`seed.license-feature.data.ts:268`), route map `config:shelves → configuration.location_shelf` รายการเมนูของ frontend ต้องมี `.view`

## 7. การอ้างอิงข้ามโมดูล

- [master-data/location](/th/inventory/master-data/location) — แถว junction ที่ชั้นวางถูกกำหนดบนนั้น; § 5.3 ที่นั่น
- [product](/th/inventory/product) — แท็บ **Location Assignment** เป็น UI เดียวที่ตั้งชั้นวาง ([product/03-user-flow-product-admin](/th/inventory/product/03-user-flow-product-admin) ขั้นที่ 9)
- [physical-count](/th/inventory/physical-count) / [spot-check](/th/inventory/spot-check) — ผู้บริโภค `sequence_no` ตามเจตนา; ยังไม่มี code path
- [inventory](/th/inventory/inventory) — แถว stock card echo `shelf_code` เมื่อแถว junction มีค่า

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_location_shelf` (line ~1441), `tb_product_location` (~5334)
- **Migrations:** `20260814150000_add_location_shelf`, `20260820120000_rename_location_shelf_to_shelf`, `20260904131500_rename_shelf_and_user_location`
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/master/shelf/shelf.service.ts`, `shelf.helper.ts`; gateway `apps/backend-gateway/src/config/config_shelves/` (`@Controller('api/config/:bu_code/shelves')`), DTO `common/dto/shelf/`
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/location-shelves/*.bru` (6 request, URL `/api/config/{{bu_code}}/shelves`)
- **Frontend:** `../carmen-inventory-frontend-react/routes/config/shelf/`, `components/lookup/lookup-shelf.tsx`, `types/shelf.ts`; เมนู `constant/module-list.ts` (`/config/shelf`)
- **E2E:** `../carmen-inventory-frontend-e2e/tests/083-shelf.spec.ts` (2 กรณีที่รันได้ + CRUD ที่ถูกเลื่อน), `docs/user-stories/083-shelf.md` (8 กรณี)
