---
title: แคตตาล็อกไลเซนส์ — โมเดลข้อมูล (Data Model)
description: tb_license_feature (เป็นของ generator ต้นไม้ n ชั้นตั้งแต่การปรับโครงแคตตาล็อกเมื่อ 2026-09-03) และ tb_license_feature_group / tb_license_feature_group_item (bundle ที่ผู้ดูแลจัดเอง) พร้อมจำนวนแคตตาล็อกปัจจุบันที่ยืนยันแล้ว
published: true
date: '2026-09-06T09:00:00.000Z'
tags: book/platform, license-catalog, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# แคตตาล็อกไลเซนส์ — โมเดลข้อมูล (Data Model)

> **At a Glance**
> **`tb_license_feature`** — แคตตาล็อกความสามารถที่ขายได้ แถวมาจาก generator ฝั่ง backend**เท่านั้น** ผู้ดูแลแพลตฟอร์มแก้ได้แค่ `state` &nbsp;·&nbsp; **`tb_license_feature_group`** — bundle ที่ผู้ดูแลจัดเอง ข้าม module ได้อย่างอิสระ &nbsp;·&nbsp; **`tb_license_feature_group_item`** — ตารางเชื่อม `feature_key` อ้างอิง**ด้วยค่า ไม่มี FK** โดยเจตนา &nbsp;·&nbsp; **โครงต้นไม้:** n ชั้นตั้งแต่ 2026-09-03 (`parent_key` = prefix ที่ยาวที่สุดที่มีอยู่จริง ไม่ใช่ "ข้อความก่อนจุดแรก") &nbsp;·&nbsp; **ขนาดแคตตาล็อกที่ยืนยันแล้ว:** 89 แถว / 11 module ราก / active 79 / inactive 10 — แก้ไขคอมเมนต์ในซอร์สที่ล้าสมัยซึ่งอ้าง 76/10/66 (§3) &nbsp;·&nbsp; **Concurrency:** `doc_version Int @default(0)` บนทั้งสองตาราง ล็อกแบบ optimistic บนทุกการเขียน

> **แหล่งความจริง:** Prisma schema ฝั่ง backend และไฟล์ผลลัพธ์ของ generator เอง ต้องอ่านสองไฟล์นี้ก่อนเสมอเวลาเขียนหรือปรับหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.license-feature.data.ts` (ไฟล์ที่ generate มา — ห้ามแก้มือ แต่เป็นเนื้อหาแคตตาล็อกปัจจุบันที่น่าเชื่อถือ)
> - `../carmen-turborepo-backend-v2/scripts/generate-license-catalog/run.ts`
>
> ยืนยันกับ `carmen-turborepo-backend-v2` HEAD `937cf5ac4` (2026-09-06) และ `carmen-platform` HEAD `157a65e` (2026-09-04)

## 1. ภาพรวม

สองตาราง ไม่มีพ่อร่วมกัน และจุดเชื่อมที่ตั้งใจให้อ่อน `tb_license_feature` เป็นตารางแบนที่จำลองเป็นต้นไม้ด้วยคอลัมน์ `parent_key` ที่ชี้กลับหาตัวเอง — มันคือแคตตาล็อกของทุกอย่างที่*ขายได้* และเป็นของ generator ทั้งหมด ไม่มีอะไรในหน้า UI ของโมดูลนี้เพิ่มหรือลบแถวได้ `tb_license_feature_group` เป็นตารางแบบตรงข้าม: ทุกแถวถูกสร้าง ตั้งชื่อ และใส่ข้อมูลโดยมนุษย์ผ่านหน้าจอแก้ไขของโมดูลนี้เอง และหนึ่งกลุ่มถือ feature key ชุดใดก็ได้ไม่ว่าจะมาจากกิ่งไหนของต้นไม้ สองตารางนี้เชื่อมกันผ่าน `tb_license_feature_group_item` เท่านั้น และการเชื่อมนั้นตั้งใจ**ไม่ใช่** foreign key — ดู §2.3

## 2. เอนทิตี

### 2.1 `tb_license_feature` — แคตตาล็อกความสามารถที่ขายได้

Schema บรรทัด 1214 หนึ่งแถวต่อหนึ่ง feature key

| ฟิลด์ | ชนิด Prisma | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | ไม่ | Primary key |
| `key` | `String @db.VarChar` | ไม่ | คีย์บนสาย เช่น `accounting.config.ap` —**คือ** permission resource ที่มันมาจาก |
| `parent_key` | `String? @db.VarChar` | ใช่ | `null` สำหรับ module ราก มิฉะนั้นเป็น **prefix ที่ยาวที่สุดที่มีอยู่จริง** ของ `key` ในแคตตาล็อก (§3) |
| `label` | `String @db.VarChar` | ไม่ | `humanize()` ของส่วนหลัง `parent_key` — generate มา ไม่ได้เขียนเอง |
| `description` | `String?` | ใช่ | generator เขียนให้ ส่วนใหญ่เป็นแค่ `"View " + label` ซึ่ง UI ซ่อนไว้โดยตั้งใจเมื่อไม่ได้พูดอะไรเพิ่ม (ดู [UI Screens](/th/platform/license-catalog/ui-screens) §3) |
| `sort_order` | `Int @default(0)` | ไม่ | ดู §3 สำหรับสูตรแบ่งแถบ module/ลูก/หลาน |
| `state` | `enum_license_feature_state @default(active)` | ไม่ | `active` \| `inactive` \| `hide` (§5) — ฟิลด์**เดียว**ที่ผู้ดูแลแก้ และแก้ผ่าน `PATCH` เท่านั้น |
| `doc_version` | `Int @default(0)` | ไม่ | ตัวนับล็อกแบบ optimistic บังคับตอน `PATCH` |
| audit trio + soft delete | — | ใช่ | มาตรฐาน `created_at`/`created_by_id`/`updated_at`/`updated_by_id`/`deleted_at`/`deleted_by_id` |

**Constraint:** `@@unique([key, deleted_at])` (map `license_feature_key_deleted_at_u`) **Index:** `(parent_key, deleted_at)`

**คอมเมนต์ใน schema บอกขอบเขตการเขียนตรง ๆ:** `state` คือฟิลด์เดียวที่ seeder ของ generator เองไม่เขียนทับแถวที่มีอยู่แล้ว (คอมเมนต์ประเภทใน `seed.license-feature.data.ts`: การ seed เขียน `state` เฉพาะตอน**สร้าง**แถวใหม่) เพราะมันเป็นค่าเดียวที่เป็นของผู้ดูแลมนุษย์ ไม่ใช่ของ generator แถวที่เพิ่งถูกสร้าง (เช่นคีย์ `accounting.*` ที่เพิ่งลงทะเบียน) จะได้ `state` ที่ seed ไว้ เพราะยังไม่มีการตัดสินใจของผู้ดูแลให้ต้องปกป้อง

### 2.2 `tb_license_feature_group` — bundle ที่ผู้ดูแลจัดเอง

Schema บรรทัด 1284 หนึ่งแถวต่อหนึ่งชุดที่ขายได้และมีชื่อ

| ฟิลด์ | ชนิด Prisma | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | ไม่ | Primary key |
| `code` | `String @db.VarChar` | ไม่ | ตั้งได้ครั้งเดียวตอนสร้าง — backend ปฏิเสธ payload ของ `PATCH` ที่มีฟิลด์นี้ เพราะการเปลี่ยน code คือการเปลี่ยนตัวตนของชุด ไม่ใช่แค่เปลี่ยนชื่อ |
| `name` | `String @db.VarChar` | ไม่ | แก้ได้ |
| `description` | `String?` | ใช่ | แก้ได้ ข้อความอิสระ |
| `sort_order` | `Int @default(0)` | ไม่ | ตำแหน่งของ bundle บนฟอร์มขาย — schema อนุญาตให้ชนกันข้ามชุด และ UI แค่แจ้งเตือน ไม่บล็อก (ดู [UI Screens](/th/platform/license-catalog/ui-screens) §4) |
| `is_active` | `Boolean @default(true)` | ไม่ | ชุดนี้ยังขายอยู่ไหม |
| `doc_version` | `Int @default(0)` | ไม่ | ตัวนับล็อกแบบ optimistic บังคับตอน `PATCH` และ `PUT .../features` |
| audit trio + soft delete | — | ใช่ | มาตรฐาน |

**Constraint:** `@@unique([code, deleted_at])` (map `license_feature_group_code_deleted_at_u`) **Index:** `(is_active, deleted_at)`

**ความสัมพันธ์:** `tb_license_feature_group_item[]` (§2.3), `tb_subscription_bu_group[]` — ตารางเชื่อมของโมดูล [Licenses](/th/platform/licenses) ที่ผูก bundle นี้เข้ากับ subscription ของ business unit หนึ่ง bundle ที่ยังมีแถว `tb_subscription_bu_group` ที่ยังไม่ถูกลบอ้างถึงอยู่จะลบไม่ได้ (ดู §4)

### 2.3 `tb_license_feature_group_item` — ตารางเชื่อม ด้วยค่า ไม่ใช่ foreign key

Schema บรรทัด 1313 หนึ่งแถวต่อคู่ (กลุ่ม, feature key)

| ฟิลด์ | ชนิด Prisma | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | ไม่ | Primary key |
| `group_id` | `String @db.Uuid` | ไม่ | FK ไปยัง `tb_license_feature_group.id` |
| `feature_key` | `String @db.VarChar` | ไม่ | **อ้างอิง `tb_license_feature.key` ด้วยค่า — ไม่มี foreign key** |
| `doc_version` | `Int @default(0)` | ไม่ | — |
| audit trio + soft delete | — | ใช่ | มาตรฐาน |

**Constraint:** `@@unique([group_id, feature_key, deleted_at])` (map `license_feature_group_item_group_key_deleted_at_u`) **Index:** `(feature_key, deleted_at)`

**การไม่มี foreign key เป็นเจตนา ตามคอมเมนต์ใน schema เอง:** แคตตาล็อก feature ถูก regenerate ทั้งชุดโดยสคริปต์ภายนอก การ regenerate นั้นต้องไม่มีวันลบสมาชิกของ bundle แบบ cascade เพียงเพราะคีย์หนึ่งหายไปชั่วขณะในรอบ generate หนึ่งครั้ง ชั้น service (`LicenseFeatureGroupService.setFeatures` ฝั่ง backend `micro-business`) เป็นจุด**เดียว**ที่ตรวจคีย์กับแคตตาล็อกจริง — ทุก `PUT` ตรวจทุกคีย์ที่ต้องการเทียบกับ `tb_license_feature` และปฏิเสธคีย์ที่ไม่รู้จักหรือเลิก `active` แล้วด้วย 400 แทนที่จะพึ่ง constraint ที่ schema ตั้งใจไม่มีให้

## 3. โครงแคตตาล็อก — ต้นไม้ n ชั้น และจำนวนปัจจุบันที่ยืนยันแล้ว

นับตั้งแต่งาน "license feature tree" เมื่อ 2026-09-03 (สเปก `docs/superpowers/specs/2026-09-03-license-feature-tree-design.md` เฟส A–C ขึ้นวันเดียวกันหมด) `parent_key` คือ**prefix ที่ยาวที่สุดที่มีอยู่จริงเป็น `key` ของแถวอื่น** ไม่ใช่แค่ข้อความก่อนจุดแรก — คีย์สามชั้นมีอยู่จริงวันนี้: `accounting.config.ap` มีพ่อเป็น `accounting.config` ซึ่งมีพ่อของตัวเองเป็น `accounting` `moduleOf()` (`featureSelection.ts:26`, ฝั่ง frontend) ยังคงตัดที่จุดแรกเหมือนเดิมและถูกต้องเฉพาะการหา module **ราก** ของคีย์เท่านั้น — การไต่สายบรรพบุรุษจริงต้องใช้ `ancestorsOf()`/`descendantKeys()`/`flattenDescendants()` (`utils/featureTree.ts`) ซึ่งไต่ `parent_key` ทีละชั้น

**`sort_order` แบ่งแถบลูกและหลานแยกกันโดยตั้งใจ (เฟส A, §4.2 ของสเปก):** แถวของ module รากเอง = `(ลำดับ module + 1) × 1000`; ลูกตรงต่อจาก `+1`; หลาน (ถ้ามี) อยู่ในแถบ `+500` เหนือฐานของ module ราก เรียงแบบ depth-first ตามลำดับพี่น้อง — ไม่ใช่ตาม `sort_order` ดิบ ซึ่งจะทำให้หลานทุกตัวไปอยู่ท้ายลูกตรงทั้งหมดของทุก module ในระบบ นี่คือเหตุผลที่ทุกจุดใน UI ที่แสดงแคตตาล็อก (`ModuleShelf` ของ `FeatureCatalogPanel`, `FeatureSelectionCard`) เรียงด้วยการเดินต้นไม้ (`flattenDescendants`) ไม่ใช่ `sort_order` เพียงอย่างเดียว

**จำนวนปัจจุบันที่ยืนยันแล้ว — อย่าเชื่อคอมเมนต์ในซอร์ส** คอมเมนต์ของ `FeatureCatalogPanel.tsx` เองและของ `ModuleShelf.tsx` ยังพูดถึง "76 แถว" และ "10 module + 66 ลูก" ซึ่งมาก่อนงานปรับโครงเมื่อ 2026-09-03 การนับผลลัพธ์ของ generator เองตรง ๆ:

```
grep -c '"key":' seed.license-feature.data.ts           → 89
grep -c '"parent_key": null' seed.license-feature.data.ts → 11
grep -c '"state": "active"' seed.license-feature.data.ts   → 79
grep -c '"state": "inactive"' seed.license-feature.data.ts → 10
```

**89 แถวทั้งหมด, 11 module ราก** (`accounting`, `configuration`, `dashboard`, `inventory_management`, `operation_plan`, `procurement`, `product_management`, `report`, `store_operations`, `system_admin`, `vendor_management`), **78 แถวที่ไม่ใช่รากกระจายอยู่ได้ถึงสามชั้น**, **79 แถวขายได้ตอนนี้** (`active`) และ **10 แถวจองไว้แต่ยังขายไม่ได้** (`inactive` — สิบคีย์ `accounting.*` ที่ลงทะเบียนในเฟส C ก่อนมี endpoint จริง §2.4 ของสเปกอธิบายไว้ตรง ๆ ว่าทำไมถึง seed เป็น `inactive` แทนค่า default `active` ของ schema เอง: feature ที่ยังไม่มี route รองรับต้องไม่ขายได้ตั้งแต่วันแรก บั๊กแบบเดียวกับที่คอมเมนต์ในโค้ดของ generator บอกว่าเคยเกิดมาแล้วกับ `report.schedule`)

**ความเสี่ยงที่โครงต้นไม้แบบนี้สร้างขึ้น — การซ่อนชั้นกลางทำลายสิทธิ์ของลูกหลานทุกตัวแบบมองไม่เห็นบนหน้านี้** evaluator สิทธิ์ตอน runtime (`license.evaluator.ts` ใน `carmen-turborepo-backend-v2` ตามสเปก §2.2/§4.5) ตัดคีย์ที่ `state='hide'` ออกจากชุด `features` ที่มีผลจริงของ business unit **ก่อน**ตรวจว่าบรรพบุรุษของคีย์ที่ถืออยู่ครบทุกตัวไหม การตั้งค่า `hide` ให้ feature ชั้นกลางจึงทำให้การตรวจบรรพบุรุษของลูกหลานทุกตัวล้มเหลวแบบเงียบ ๆ สำหรับทุก business unit ที่ถือมันอยู่ — แม้ว่าลูกหลานเหล่านั้นจะยังขึ้นเป็น `active` บนหน้าจอนี้อยู่ก็ตาม เพราะ `state` ของแถวตัวเองไม่เคยเปลี่ยน กล่องยืนยันการซ่อนของ `FeatureCatalogPanel` จึงต่อท้ายด้วยจำนวนลูกหลานก็เพราะความเสี่ยงนี้เป๊ะ (ดู [UI Screens](/th/platform/license-catalog/ui-screens) §3); นี่คือความเสี่ยงที่ตั้งใจและถูกเขียนไว้ในการออกแบบ ไม่ใช่สิ่งที่หน้านี้กำลังรายงานว่าเป็นบั๊ก

## 4. ความสัมพันธ์

```
tb_license_feature.parent_key              ──>  tb_license_feature.key       (อ้างตัวเอง ด้วยค่า)
tb_license_feature_group_item.group_id     ──>  tb_license_feature_group.id
tb_license_feature_group_item.feature_key  ──>  tb_license_feature.key       (ด้วยค่า ไม่มี FK — §2.3)
tb_subscription_bu_group.group_id          ──>  tb_license_feature_group.id  (เป็นของโมดูล Licenses)
*.created_by_id / *.updated_by_id / *.deleted_by_id  ──>  tb_user.id  (ผู้กระทำใน audit)
```

ทั้ง `tb_license_feature` และ `tb_license_feature_group` ไม่มี foreign key ชี้หากันเลย — แคตตาล็อกและ bundle ของมันเป็นชุดข้อมูลสองชุดที่ดูแลแยกกันโดยอิสระ เชื่อมกันแค่ผ่านการอ้างอิงด้วยค่าใน §2.3

## 5. Enum

`enum_license_feature_state` (schema บรรทัด 740): `active` | `inactive` | `hide` การสะกดนี้คือสัญญาสายข้อมูลกับ frontend (`FeatureState` ใน `src/constants/featureFlags.ts` เขียนไว้ตรง ๆ ว่า "สามสตริงนี้คือสัญญาสายข้อมูลกับ backend enum — ห้ามเปลี่ยนชื่อ") — แต่ดู §3.3 ของ[หน้าลงจอด](/th/platform/license-catalog) ว่าทำไมสามสตริงเดียวกันเป๊ะถึงหมายความต่างกันบนหน้า Feature Flags ที่ไม่เกี่ยวข้องกัน ไม่มี enum แยกสำหรับ `tb_license_feature_group` — `is_active` เป็น boolean ธรรมดา ไม่ใช่ฟิลด์สามสถานะ เพราะ bundle ไม่มีสิ่งที่เทียบเท่า `hide` เลย: การปิด bundle หยุดการเสนอขาย**ใหม่** แต่ subscription ที่อ้างมันอยู่แล้วยังถือสิทธิ์ต่อไป (การถอดสิทธิ์จริง ๆ ต้องแก้ชุด feature ของ bundle หรือลบ bundle ทิ้ง ทั้งสองอยู่ใน §7 ของ [UI Screens](/th/platform/license-catalog/ui-screens))

## 6. `affected_bu_count` — คำนวณสด ไม่เก็บลง DB

`LicenseFeatureAdminRow.affected_bu_count` (มีเฉพาะใน response ของ `listAll` สำหรับหน้าผู้ดูแล ไม่มีใน endpoint แคตตาล็อกธรรมดา) คำนวณฝั่ง server (`LicenseFeatureService.countAffectedBusinessUnits()`, `apps/micro-business/src/license-feature/license-feature.service.ts`) โดยเดินเส้นทาง join เดียวกับที่ evaluator ตอน runtime ใช้ประกอบสิทธิ์ของ business unit เป๊ะ: `tb_subscription_bu → tb_subscription_bu_group → tb_license_feature_group → tb_license_feature_group_item` นับ**business unit ที่ไม่ซ้ำ**ต่อ feature key (ไม่ใช่นับแถว — BU เดียวถือคีย์เดียวกันผ่านหลายกลุ่มหรือหลายสัญญาได้) **นับรวมสัญญาที่หมดอายุด้วยโดยเจตนา**: BU ที่สัญญาหมดอายุแล้วยังเห็นเมนูอยู่วันนี้ ตามคอมเมนต์ของ service เอง จึงยังจะเสียเมนูนั้นเหมือนกันถ้าคีย์ถูกซ่อน — นับน้อยไปทางฝั่ง "ปลอดภัย" เป็นทิศทางที่ผิดสำหรับคำเตือน ฟิลด์นี้เป็น `optional` และห้ามอ่าน `undefined` เป็น `0` เด็ดขาด — มันแปลว่า gateway รุ่นเก่าไม่ส่งฟิลด์นี้มาเลย ไม่ใช่ไม่มี business unit ไหนถือคีย์นี้

## 7. แหล่งข้อมูลอ้างอิง

**หลัก (แหล่งความจริง):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_license_feature` (1214), `tb_license_feature_group` (1284), `tb_license_feature_group_item` (1313), `enum_license_feature_state` (740)
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.license-feature.data.ts` — ผลลัพธ์ปัจจุบันของ generator เอง ที่มาของจำนวนที่ยืนยันแล้วใน §3
- `../carmen-turborepo-backend-v2/scripts/generate-license-catalog/run.ts` — ผู้เขียนแถว `tb_license_feature` เพียงรายเดียว
- `../carmen-turborepo-backend-v2/apps/micro-business/src/license-feature/license-feature.service.ts` — `listAll()`, `countAffectedBusinessUnits()` (§6), `setState()`
- `../carmen-turborepo-backend-v2/apps/micro-business/src/license-feature-group/license-feature-group.service.ts` — `list()`/`get()`/`create()`/`update()`/`setFeatures()`/`delete()`, กฎ "ลูกลากพ่อ", การป้องกันลบขณะยังมีสัญญาอ้างอยู่
- `../carmen-platform/docs/superpowers/specs/2026-09-03-license-feature-tree-design.md` — การออกแบบต้นไม้ n ชั้นและโพรบยืนยันของมัน (§3)

**รอง (รูปทรงฝั่งผู้ใช้):**
- `../carmen-platform/src/utils/featureTree.ts` — `ancestorsOf()`, `descendantKeys()`, `flattenDescendants()`
- `../carmen-platform/src/pages/licenses/subscriptionEdit/featureSelection.ts` — `moduleOf()`, `toggleFeature()`, `setModuleSelection()`, `groupCatalog()`
- `../carmen-platform/src/types/index.ts` — `LicenseFeature`, `LicenseFeatureAdminRow`, `LicenseFeatureGroup`, `LicenseFeatureGroupDetail`, `LicenseFeatureGroupWriteInput`
- `../carmen-platform/src/constants/featureFlags.ts` — `FeatureState`, `FEATURE_STATES` (ชนิดของสัญญาสายข้อมูลที่ใช้ร่วมกัน, §5)

**Cross-links:** [หน้าลงจอด License Catalog](/th/platform/license-catalog) &nbsp;·&nbsp; [UI Screens](/th/platform/license-catalog/ui-screens) &nbsp;·&nbsp; [Licenses](/th/platform/licenses)
