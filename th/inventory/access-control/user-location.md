---
title: location ของผู้ใช้ (User Location, tb_location_user)
description: Scope ของ location ต่อผู้ใช้ภายใน tenant — จำกัด user ให้เห็นเฉพาะบาง location สต๊อก ตาราง tb_location_user (เดิม tb_user_location) แก้ไขผ่าน PATCH /api/config/:bu_code/users/:user_id
published: true
date: '2026-10-27T15:00:00.000Z'
tags: access-control, user-location, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# location ของผู้ใช้ (User Location, `tb_location_user`)

> **At a Glance**
> **เจ้าของ:** Sysadmin / BU Admin &nbsp;·&nbsp; **ตาราง:** `tb_location_user` (tenant; **เปลี่ยนชื่อจาก `tb_user_location` เมื่อ 2026-09-04**) &nbsp;·&nbsp; **แก้ไขผ่าน:** `PATCH /api/config/:bu_code/users/:user_id { location_id: { add[], remove[] } }` (2026-09-04) หรือ `PUT /api/config/:bu_code/locations-users/:userId` (แทนที่ทั้ง list) &nbsp;·&nbsp; **อ่านโดย:** [inventory](/th/inventory/inventory), [store-requisition](/th/inventory/store-requisition), [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check) และ picker product-location ของ workflow &nbsp;·&nbsp; Filter location ระดับ row — จำกัด row สต๊อกที่ user มองเห็น

![location ของผู้ใช้ (User Location, tb_location_user) screen](/screenshots/access-control/user-location.png)

## ประกาศการเปลี่ยนชื่อ (2026-09-04)

Tenant migration `20260904131500_rename_shelf_and_user_location` (BE `d49a81b34`) เปลี่ยนชื่อ `tb_user_location` → `tb_location_user` (และ `tb_shelf` → `tb_location_shelf`) เพื่อให้ชื่อตารางอ่านว่า "ผู้ใช้ของ location" เหมือนตารางพี่น้อง `tb_location_shelf`, `tb_location_product` migration เป็น metadata อย่างเดียว (`ALTER TABLE … RENAME`, constraint `tb_user_location_pkey` → `tb_location_user_pkey`, FK `…_location_id_fkey` ถูกเปลี่ยนชื่อ, index `user_location_*` → `location_user_*`) Prisma model คือ `tb_location_user` (`schema.prisma`, `@@unique([user_id, location_id, deleted_at]) map "location_user_user_id_location_id_u"`) path ของ gateway **ไม่** เปลี่ยน: `api/config/:bu_code/locations-users` (api name `locationUser.*`) ยังมีอยู่ **แก้ไข 2026-10-27:** `api/config/:bu_code/user-locations` ที่เป็นพี่น้อง (`userLocation.getUsersByLocationId` / `managerUserLocation`) ซึ่งหน้านี้เคยระบุว่า "ยังมีอยู่" เป็น gateway module ที่ **ไม่เคยถูก register** ในแอปและถูกลบทิ้งเป็น dead code แล้ว (BE `d5829efd3`, 2026-10-05; Bruno `config/user-location/` ถูก archive ไว้ที่ `_archived/2026-10-07`) — สองการเรียกนั้นไม่เคยไปถึง handler scope ของผู้เรียกเองคือ `GET api/:bu_code/user-locations` (`application/user-locations/`) ซึ่งไม่ได้รับผลกระทบ slug ของหน้า wiki นี้ (`user-location`) คงไว้

## สถานะการ implement (ตรวจสอบซ้ำ 2026-10-27)

- **พฤติกรรมไม่เปลี่ยน** ในตาราง, endpoint หรือ error code ตั้งแต่ 2026-09-22 `tb_location_user` ไม่เปลี่ยนใน `schema.prisma` (`:5594`); `config_users.controller.ts`, location-user service และรายการ `USER_ACCESS_LOCATION_*` ในแคตตาล็อกต่างจากรอบก่อนเพียงการเปลี่ยนชื่อ `platform` → `backstage` ทั้งโปรเจกต์ (BE `cb78788a6`, `c820b5064`)
- **ทะเบียนในโหมด edit โหลดผ่าน `useLocationAll`** (FE `0bac08d4`): ส่วน Locations ยังคงดึง location ทั้ง BU เมื่อกด **Edit** เท่านั้น (`enabled: !isDisabled`) แต่ตอนนี้ผ่าน helper "list all" ที่ใช้ร่วมกันแทน `perpage=-1` โหมด view แสดง location ที่มาพร้อมกับผู้ใช้ (`GET …/users/:user_id`) filter ประเภท location, checkbox grid และ `PATCH` แบบ diff อย่างเดียวไม่เปลี่ยน
- **Layout:** ฟอร์มผู้ใช้ตอนนี้อยู่ใน `FormPageShell` + `FormToolbar` (FE `7c9bc0ae`); ปุ่ม Save อยู่นอก `<form>` และอ้างถึงด้วย `form="user-assigned-form"` สิ่งที่บันทึกไม่เปลี่ยน

## 1. คืออะไรและใครใช้

`user-location` ทำให้ effective scope ของ user แคบลงจาก "ทุก location" เป็น "subset นี้" Storekeeper ที่มอบหมายให้สอง storeroom ควรเห็นเฉพาะสองที่ใน location picker, เอกสาร count และหน้าจอ adjustment ของตน ตารางเป็น many-to-many ง่ายๆ ระหว่าง [access-control/user](/th/inventory/access-control/user) และ [master-data/location](/th/inventory/master-data/location) พร้อม pattern soft-delete แบบ active-only

ไม่เหมือน [access-control/application-role](/th/inventory/access-control/application-role) (ซึ่ง gate **action**) และ [access-control/business-unit-user](/th/inventory/access-control/business-unit-user) (ซึ่ง gate **การเข้า BU**) `user-location` เป็น **filter ข้อมูลระดับ row** — จำกัด row ที่มองเห็นโดยไม่เปลี่ยน role หรือ permission ชุดว่างถูกตีความตามข้อตกลงว่า "ไม่มีข้อจำกัด"

ตอนนี้มี consumer หนึ่งตัวที่ชัดเจนใน code: `GET api/config/:bu_code/workflows/:workflow_id/products/:product_id/locations` (2026-09-03) คืน location ที่ product ใช้ได้ภายใต้ workflow *สำหรับผู้ใช้ที่เรียก* — intersection ของ `tb_workflow.data.products`, `tb_product_location` และ row `tb_location_user` ของผู้เรียก; "ผู้เรียกไม่ถือ location ใดเลย" ได้ array ว่าง ไม่ใช่ error (Bruno `GET-find-product-locations-config-workflows.bru`) ดู [system-config/workflow](/th/inventory/system-config/workflow)

**บำรุงรักษาโดย** Sysadmin และ BU admin **อ่านโดย** ทุก list/picker ในโมดูลที่มีสต๊อก

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| มอบหมาย user ให้ location | หน้าจอ User Assign (`/system-admin/user/:id`) → **Edit** → ส่วน **Locations** (`user-assigned-locations.tsx`) → ติ๊ก location → Save | ตั้งแต่ 2026-08-27 (`96e569ad`) ส่วนนี้เป็น `DataGrid` ที่มี checkbox ต่อ row, ค้นหา, sort และ filter ตามประเภท (Inventory / Direct / Consignment) ไม่ใช่ Transfer control แบบสองแผงที่หน้านี้เคยอธิบาย; ฟอร์ม diff ชุดที่ติ๊กและส่งแค่ `{ location_id: { add, remove } }` (`buildUserPatch`, `user-assigned-form-schema.ts:63-77`) |
| Reassign storekeeper | เอาติ๊ก A ออก ติ๊ก B → Save | `PATCH` เดียว; เอกสารที่เปิดยังทำงาน (FK target `tb_location`) |
| ดู effective scope ของ user | หน้าจอเดียวกัน โหมดดู | `GET /api/config/:bu_code/users/:user_id` → `locations[{ id, location_id, location_code, location_name, location_type, is_active }]` |
| แทนที่ location ทั้ง list ของผู้ใช้หนึ่งคน | `PUT /api/config/:bu_code/locations-users/:userId` (`locationUser.managerLocationUser`) | Bruno `config/locations-user/`; ไม่มีหน้าจอเฉพาะ **ไม่มี** variant ที่ keyed ด้วย location (route `…/user-locations/:locationId` ที่เคยระบุไว้ที่นี่ไม่เคยถูก register และถูกลบแล้ว) |
| ลบ scope ทั้งหมด (full access) | เอาติ๊กออกทุก location แล้ว Save | ชุดว่าง = "ไม่มีข้อจำกัด" ตามข้อตกลง (ยืนยันกับ service ที่ consume ก่อนพึ่งพาสิ่งนี้ในเส้นทางที่ sensitive) |
| ตรวจสอบการเปลี่ยน scope | [reporting-audit/activity](/th/inventory/reporting-audit/activity) log | Filter ตาม entity type |

**ประวัติ:** ระหว่าง 2026-09-03 (`2ee5b2c1` location ถูกทำให้ดูอย่างเดียวบนหน้าจอ user) ถึง 2026-09-07 (`39ae1bba` เปิดให้แก้ไขอีกครั้งผ่าน endpoint ผู้ใช้แบบ request เดียวตัวใหม่) หน้าจอ user เปลี่ยน location ไม่ได้; `PUT` ของ `locations-users` เป็นเส้นทางเดียว

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| User ไม่เห็น location ที่คาดหวัง | Row `tb_location_user` ขาดหาย หรือข้อตกลงชุดว่างไม่ถูก apply | เพิ่ม row หรือยืนยันพฤติกรรม service code |
| `USER_ACCESS_LOCATION_ADD_REMOVE_CONFLICT` | location id เดียวกันอยู่ทั้งใน `add` และ `remove` | แก้ payload |
| `USER_ACCESS_LOCATIONS_TO_ADD_NOT_FOUND` / `…_TO_REMOVE_NOT_FOUND` | location id ไม่รู้จัก หรือลบการมอบหมายที่ไม่มีอยู่ | Reload แล้วลองใหม่ (`packages/error-catalog/src/catalog.ts:366-386`; `…_ADD_REMOVE_CONFLICT` เป็น HTTP 400) |
| `USER_ACCESS_LOCATION_WRITE_FAILED` | การเขียนฝั่ง tenant ล้มเหลวหลังฝั่ง backstage สำเร็จ | ลองใหม่; รายงานถ้าเกิดซ้ำ |
| `USER_ACCESS_NO_CHANGES` | Body ของ `PATCH` ไม่มีการเปลี่ยนแปลงที่มีผล | ไม่ต้องทำอะไร |
| Orphan `user_id` หลังการลบ backstage-user | Cross-schema, ไม่มีการบังคับ FK | รัน maintenance job เพื่อ clean row เก่า |

## 4. กรณีพิเศษ

- **Empty-set semantics** ตามข้อตกลง "ไม่มีข้อจำกัดระดับ row" — ยืนยันกับ service code ถ้าพึ่งพา default นี้สำหรับเส้นทาง sensitive
- **Cross-schema integrity** `user_id` อ้างอิง backstage `tb_user.id` (`prisma-shared-schema-backstage` เปลี่ยนชื่อจาก platform schema ใน BE `c820b5064`) แต่ **ไม่ใช่** Prisma FK — แอป validate ตอน insert
- **สองเส้นทางเขียน ตารางเดียว** `PATCH` ฝั่ง user (diff add/remove) และ `PUT` ของ `locations-users/:userId` (แทนที่ทั้ง list) เขียน `tb_location_user` ทั้งคู่; `PATCH` เป็น transaction ข้ามการเขียน backstage (role) และ tenant (location) และรายงานความล้มเหลวฝั่ง tenant เป็น `USER_ACCESS_LOCATION_WRITE_FAILED`
- **การ override ต่อเอกสาร** ตารางนี้เป็น **scope default** สำหรับ picker; เวิร์กโฟลว์เฉพาะอาจขยาย (เช่น ผู้อนุมัติใน [store-requisition](/th/inventory/store-requisition) ต้องการทั้งต้นทางและปลายทาง)
- **Reassignment เป็นสอง op** Soft-delete row A, insert row B — เอกสารที่เปิดยังทำงาน

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_location_user`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `user_id` | `String @db.Uuid` | No | อ้างอิง backstage `tb_user.id`; ไม่ใช่ Prisma FK (cross-schema) |
| `location_id` | `String @db.Uuid` | No | FK ไปยัง tenant `tb_location` |
| `note` | `String? @db.VarChar` | Yes | บริบทการมอบหมาย |
| `info` | `Json? @db.JsonB` | Yes | Default `{}` Metadata ที่สงวนไว้ |
| `doc_version` | `Int` | No | Default `0` Optimistic-lock version |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([user_id, location_id, deleted_at])` (`location_user_user_id_location_id_u`) Index `location_user_user_id_location_id_idx` FK ไปยัง `tb_location` `onDelete: NoAction` `user_id` บังคับฝั่งแอปพลิเคชัน

### 5.2 API surface

```
GET   /api/config/:bu_code/users/:user_id                  configUser.getAccess   → locations[] (+ roles, department)
PATCH /api/config/:bu_code/users/:user_id                  configUser.patchAccess { location_id: { add[], remove[] } }
GET   /api/config/:bu_code/locations-users/:userId         locationUser.getLocationByUserId
PUT   /api/config/:bu_code/locations-users/:userId         locationUser.managerLocationUser
GET   /api/:bu_code/user-locations                         userLocation.findAll (scope ของผู้เรียกเอง)
GET   /api/:bu_code/user-locations/product/:product_id     locations.findAllByProductId
GET   /api/:bu_code/user-locations/:user_location_id       (application/user-locations, `:206`)
```

Licence route key `config:locations-users`, `config:user-locations` (ตอนนี้กำพร้า — controller ของมันถูกลบแล้ว), `app:user-locations` ทั้งหมด map ไปที่ `configuration.location` (`packages/prisma-shared-schema-backstage/prisma/permission.route-map.ts:180,190,203` — ไฟล์ย้ายตามการเปลี่ยนชื่อ package platform → backstage)

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** User มีอย่างมากที่สุดหนึ่งการมอบหมายที่ active ต่อ location
- **Empty-set semantics** ตามข้อตกลง "ไม่มีข้อจำกัดระดับ row" — code path ที่ต้องการการมอบหมายชัดเจนต้องตรวจสอบ `count > 0`
- **Cross-schema integrity** แอป validate `user_id` ตอน insert; maintenance job clean up หลังการลบ user
- **การ์ดการลบ** Hard-delete อนุญาต (ไม่มี FK target ธุรกรรม); soft-delete รักษา audit
- **Lifecycle** Reassignment เป็นสอง operation (soft-delete + insert); FK ระดับเอกสาร target `tb_location` ดังนั้นงานที่เปิดถูกรักษา
- **การ override ต่อเอกสาร** Scope default เท่านั้น — เวิร์กโฟลว์เฉพาะอาจขยายหรือแคบลง

## 7. การอ้างอิงข้าม

- [inventory](/th/inventory/inventory) — หน้าจอ list และ movement filter โดยชุดของ user
- [store-requisition](/th/inventory/store-requisition) — location การออก/ขอ validate กับ scope
- [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check) — เอกสาร count จำกัดที่ location ของ user
- [system-config/workflow](/th/inventory/system-config/workflow) — picker `…/products/:product_id/locations`
- [master-data/location](/th/inventory/master-data/location) — ฝั่ง location; shelf เป็น `tb_location_shelf` หลัง migration เดียวกัน
- [access-control/user](/th/inventory/access-control/user) — ฝั่ง user และ endpoint สิทธิ์การเข้าถึงแบบ request เดียว

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_location_user`; migration `20260904131500_rename_shelf_and_user_location`
- **Gateway:** `../carmen-turborepo-backend/apps/backend-gateway/src/config/config_users/config_users.controller.ts` (`PATCH :user_id` `:64`, `GET :user_id` `:149`; swagger `request.ts` `ConfigUserAccessPatchRequest`, `response.ts` `ConfigUserAccessLocationDto`); `config/config_locations-users/` (`GET`/`PUT :userId` `:60`/`:119`); `application/user-locations/` (`GET` `:69`, `GET product/:product_id` `:130`) `config/config_user-locations/` ไม่มีอยู่แล้ว
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/users/{GET-get-access,PATCH-patch-access}-config-users.bru`, `config/locations-user/` (โฟลเดอร์ `config/user-location/` ถูก archive)
- **Frontend:** `../carmen-frontend/routes/system-admin/user/user-assigned-locations.tsx` (DataGrid + checkbox), `user-assigned-form.tsx`, `user-assigned-form-schema.ts` (`buildUserPatch`), `types/user.ts` (`UserLocation`, `UpdateUserPayload`)
