---
title: แคตตาล็อกไลเซนส์ (License Catalog)
description: หน้าจอเดียว สองแท็บ สอง nav row — แคตตาล็อก feature ที่ขายได้ (Features) และชุดที่จัดไว้ล่วงหน้าที่ขายจากมัน (Bundles) — แต่ละแท็บมีคู่ permission และ feature flag ของตัวเอง
published: true
date: '2026-09-06T09:00:00.000Z'
tags: book/platform, license-catalog
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# แคตตาล็อกไลเซนส์ (License Catalog)

โมดูล **License Catalog** คือหน้าจอเดียว `LicenseCatalog` ที่ render อยู่หลังสอง route แยกกัน สลับด้วย prop `tab`: `/license-features` (แท็บ **Features**, `FeatureCatalogPanel`) และ `/license-feature-groups` (แท็บ **Bundles**, `GroupCatalogPanel`) นี่คือการรวมเอกสาร ไม่ใช่การรวมผลิตภัณฑ์ — สองแท็บนี้ยังถือ nav row, คู่ permission และ feature-flag key ของตัวเองเหมือนเดิมทุกประการ และหน้านี้เอกสารทั้งคู่ไว้เป็นโมดูลเดียวเพราะทั้งสองตอบคำถามเดียวกัน: *Carmen ขายอะไร และจัดแพ็กเกจมันยังไง* **Features** คือแคตตาล็อกดิบของความสามารถที่ขายได้ สร้างจาก permission map แก้ได้แค่ `state` (ขายได้ / ยังขายไม่ได้ / ซ่อน) **Bundles** คือชุดที่จัดไว้ล่วงหน้าโดยผู้ดูแล — ข้าม module ได้อย่างอิสระ — ที่ subscription หยิบไปใช้จริงบนหน้าจอขายของโมดูล [Licenses](/th/platform/licenses) route ที่สาม `/license-feature-groups/{new,:id/edit}` render component แยกต่างหาก `LicenseFeatureGroupEdit` สำหรับสร้าง/แก้ไขหนึ่งชุด

> **At a Glance**
> **Component:** `LicenseCatalog` (component เดียว, prop `tab: 'bundles' | 'features'`) &nbsp;·&nbsp; **Route:** `/license-features` → แท็บ Features, `/license-feature-groups` → แท็บ Bundles, `/license-feature-groups/new` และ `/license-feature-groups/:id/edit` → `LicenseFeatureGroupEdit` &nbsp;·&nbsp; **Permission key — สองคู่แยกจากกัน:** แท็บ Features `license_feature.read` (nav/อ่าน) + `license_feature.manage` (แก้ `state`); แท็บ Bundles `license_feature_group.read` (nav/อ่าน) + `license_feature_group.manage` (สร้าง/แก้/ลบ/ตั้ง feature) &nbsp;·&nbsp; **Feature-flag key:** `license_features` และ `license_feature_groups` แท็บละหนึ่ง &nbsp;·&nbsp; **Nav group:** `navGroup.licenseManagement` — สองแถว "License Feature Groups" กับ "License Features" (ป้ายบน sidebar) ซึ่งพาไปแท็บที่ตัว shell เองเรียกว่า "Bundles" กับ "Features" &nbsp;·&nbsp; **ขนาดแคตตาล็อก (ยืนยันจากข้อมูล generator ไม่ใช่จากคอมเมนต์ในซอร์ส):** 89 แถว ใน 11 module ราก — ขายได้ (`active`) 79, สำรองไว้ (`inactive`) 10 คีย์ (`accounting.*` ที่จองไว้ล่วงหน้ารอ endpoint จริง) &nbsp;·&nbsp; **ด่านข้ามโมดูลที่ต้องรู้:** ตัวหารของแถบสัดส่วนบนแท็บ Bundles และตัวเลือก feature ทั้งชุดในหน้าแก้ไขกลุ่ม ต่างโหลดผ่าน `GET /api-system/platform/license-features` (ไม่มี `/all`) ซึ่งกั้นด้วย `subscription.read` — permission key ของ**อีกโมดูลหนึ่ง**โดยสิ้นเชิง (§4) &nbsp;·&nbsp; **e2e suite:** **ไม่มี** — ทุกคำกล่าวอ้างในหน้าของโมดูลนี้มาจากการอ่าน implementation ของ `../carmen-platform` และ `../carmen-turborepo-backend-v2` โดยตรง &nbsp;·&nbsp; **หน้าย่อย:** 2

## 1. ภาพรวม

- **`/license-features` → `LicenseCatalog` (`tab="features"`) → `FeatureCatalogPanel`** — หน้าจอแคตตาล็อกที่เน้นอ่าน ทุกแถว feature ที่ยังไม่ถูกลบ รวมแถวที่ซ่อนไว้ จัดเป็น "ชั้นวาง" ต่อ module ราก พร้อมเยื้องเป็นชั้น n ระดับสำหรับลูกและหลาน พื้นที่แก้ไขมีแค่สวิตช์สถานะต่อแถว (`active` / `inactive` / `hide`) ตัวแถวเองเป็นของ generator ฝั่ง backend (`scripts/generate-license-catalog/run.ts`) ไม่ใช่ของหน้านี้
- **`/license-feature-groups` → `LicenseCatalog` (`tab="bundles"`) → `GroupCatalogPanel`** — รายการชุดที่จัดไว้ล่วงหน้า: หนึ่งแถวต่อหนึ่งชุด แถบสัดส่วน Features ที่ใช้ตัวหารร่วมทั้งหน้า คอลัมน์จำนวนสัญญา สถานะ active/inactive และปุ่มแก้ไข/ลบต่อแถว
- **`/license-feature-groups/new`, `/license-feature-groups/:id/edit` → `LicenseFeatureGroupEdit`** — route แยกต่างหาก (ไม่ใช่แท็บใน `LicenseCatalog`) สำหรับสร้างหรือแก้ไขหนึ่งชุด: ตัวตนของมัน ตำแหน่งบนฟอร์มขาย สถานะ active/inactive และชุด feature ที่มันให้สิทธิ์

ทั้ง route ของสองแท็บและ route ของ `LicenseFeatureGroupEdit` ถูกกั้นด้วย `PrivateRoute` ที่มี `requiredPermission` และ flag `feature` (`App.tsx:290-321`) ดูเมทริกซ์เต็มที่ §4 รวมถึง route เดียว (`:id/edit`) ที่ต้องการแค่คีย์อ่าน

## 2. บริบททางธุรกิจ

การขาย feature ของ Carmen inventory ให้ business unit หนึ่งเกิดเป็นสองขั้นตอนที่แยกจากกัน และโมดูลนี้เป็นเจ้าของทั้งคู่:

1. **ตัดสินว่าอะไรขายได้บ้าง** ทุก route ในผลิตภัณฑ์ผูกกับ permission resource หนึ่งตัว และทุก resource ที่ควร*ขายได้* — ไม่ใช่แค่ควบคุมการเข้าถึง — จะมีแถวคู่กันใน `tb_license_feature` สร้างอัตโนมัติจาก permission map (`permission.route-map.ts` + `seed.permission.data.ts`) ผู้ดูแลแพลตฟอร์มเพิ่ม feature ด้วยมือไม่ได้ คันโยกเดียวที่หน้านี้ให้คือปิดของที่มีอยู่แล้ว (`inactive` — หยุดขายเพิ่ม) หรือปิดสนิท (`hide` — ถอดเมนูออกจากทุกคนที่มีอยู่แล้ว)
2. **จัดของที่ขายได้ให้เป็นสิ่งที่พนักงานขายหยิบใช้ครั้งเดียว** การติ๊ก feature 89 ตัวทีละตัวทุกครั้งที่ทำสัญญาใหม่ไม่สเกลและไม่ตรงกับวิธีที่ Carmen ขายจริง — ลูกค้าซื้อแพ็กเกจ ไม่ใช่รายการติ๊ก **Bundles** (`tb_license_feature_group`) คือคำตอบที่ผู้ดูแลจัดเอง: ชุด feature key ที่ตั้งชื่อได้ จัดลำดับได้ ข้าม module ได้อย่างอิสระ ที่สัญญา subscription อ้างถึงเป็นก้อนเดียว (`tb_subscription_bu_group`) ไม่ใช่แกะออกมาเป็น feature รายตัวในสัญญา

สองขั้นตอนนี้เป็นบทบาทที่แยกกันโดยตั้งใจ: ตัดสินว่าอะไร*ขายได้* (โมดูลนี้) กับตัดสินว่าลูกค้ารายหนึ่ง*ซื้ออะไรจริง* (โมดูล [Licenses](/th/platform/licenses)) เป็นงานคนละอย่าง กั้นด้วย permission resource คนละตัวกันโดยสิ้นเชิง

## 3. แนวคิดสำคัญ

### 3.1 component เดียว สองแท็บ สามการตัดสินใจที่ตั้งใจ

คอมเมนต์ใน `LicenseCatalog.tsx` เองระบุสามอย่างที่ผู้ทดสอบจะเข้าใจผิดว่าเป็นบั๊กถ้าไม่รู้ที่มา:

- **สลับแท็บคือการ navigate ไม่ใช่การเปลี่ยน state** `onChange` ของ `TabStrip` เรียก `navigate(TAB_PATH[next])` ซึ่งเปลี่ยน route ทำให้ panel ลูกของ `LicenseCatalog` remount และดึงข้อมูลใหม่ ไม่มีการแคชข้ามแท็บเลย นี่คือความตั้งใจ: ทั้งสอง panel ดึงครั้งเดียวและมีเพดานเชิงโครงสร้างอยู่แล้ว (ทั้งแคตตาล็อก feature และรายการ bundle เป็นข้อมูลที่จัดเอง ไม่ได้งอกตามการใช้งาน) ต้นทุนของการดึงใหม่ทุกครั้งที่สลับแท็บจึงต่ำมากจนไม่คุ้มที่จะเลี่ยง และการทำแคชที่ต้องครอบคลุมสอง route ที่มี permission ต่างกันคือความซับซ้อนที่ไม่มีใครขอ
- **ชื่อหัวหน้าคงที่เสมอ มีแค่ subtitle ที่เปลี่ยน** `title` ของ `PageHeader` เป็น `t('pages.licenseCatalog.title')` เสมอ — "License Catalog" ตรงตัว — ไม่ว่าแท็บไหนกำลังเปิดอยู่ มีแค่ `subtitle` ที่สลับระหว่าง `pages.licenseFeatureGroups.subtitle` ("Curated bundles of licence features, used when selling a subscription") กับ `pages.licenseFeatures.subtitle` ("Choose which features can still be sold. The catalog itself is generated — only the state is yours to set.") นี่คือการตัดสินใจเรื่องตัวตนโดยตั้งใจ ไม่ใช่ความพลาด: ชื่อที่เปลี่ยนตามแท็บจะทำให้การรวมนี้อ่านเป็นสองหน้าจอที่บังเอิญใช้ URL prefix เดียวกัน ซึ่งทำลายเหตุผลทั้งหมดที่เอกสารนี้ถือว่ามันเป็นโมดูลเดียว
- **แถบแท็บหายไปเมื่อเข้าถึงได้แค่แท็บเดียว** `tabs` คำนวณโดยกรอง `TAB_ORDER` (`['bundles', 'features']`) ผ่านด่านของแต่ละแท็บเอง (`TAB_GATE`, §4) — `hasPermission(gate.permission) && flagOf(gate.feature) === 'active'` — และ `<TabStrip>` จะ render ก็ต่อเมื่อ `tabs.length > 1` เท่านั้น นี่คือ**การตรวจซ้ำฝั่ง client** ของสิ่งที่ route guard ตรวจไปแล้วก่อนที่ panel จะ mount ได้เลย (ดู §4 ของ[หน้าลงจอด](/th/platform/license-catalog)) — มันมีอยู่เพราะทั้งสองแท็บใช้ shell เดียวกัน shell เองจึงต้องเป็นคนตัดสินว่าจะวาดตัวควบคุมที่ชี้ไปแท็บที่ session ปัจจุบันเข้าไม่ได้หรือไม่ session ที่เข้าถึงได้แค่แท็บเดียวจึงเห็น panel เดียวไม่มีแท็บ ไม่มีแถบเปล่าอยู่ข้างบน

### 3.2 แคตตาล็อกเป็นต้นไม้ n ชั้นที่เป็นของ generator ไม่ใช่รายการแบน

แถวของ `tb_license_feature` มาจาก `scripts/generate-license-catalog/run.ts` **เท่านั้น** — `licenseFeatureService` ไม่มี create หรือ delete โดยเจตนา สิ่งเดียวที่ผู้ดูแลเป็นเจ้าของคือ `state` นับตั้งแต่งาน "license feature tree" เมื่อ 2026-09-03 (`docs/superpowers/specs/2026-09-03-license-feature-tree-design.md` เฟส A–C ขึ้นวันเดียวกันหมด) `parent_key` คือ**prefix ที่ยาวที่สุดที่มีอยู่จริงในแคตตาล็อก** ไม่ใช่แค่ข้อความก่อนจุดแรก — คีย์จึงอยู่ลึกได้ถึงสามชั้นจริง (`accounting.config.ap` มีพ่อเป็น `accounting.config` ซึ่งมีพ่อเป็น `accounting`) `moduleOf()` (`featureSelection.ts:26`) ยังตัดที่จุดแรกเหมือนเดิมและใช้ได้ถูกต้องเฉพาะการหา module **ราก** เท่านั้น — การไต่สายบรรพบุรุษจริงต้องใช้ `ancestorsOf()`/`descendantKeys()`/`flattenDescendants()` (`utils/featureTree.ts`) ไม่ใช่การหั่นสตริงที่จุดแรก

**คอมเมนต์ในซอร์สโค้ดนี้ล้าสมัย — ยืนยันจำนวนกับข้อมูล generator ไม่ใช่กับคอมเมนต์** คอมเมนต์ของ `FeatureCatalogPanel.tsx` เองและของ `ModuleShelf.tsx` ต่างพูดถึง "76 แถว" / "10 module + 66 ลูก" — ทั้งคู่มาก่อนงานปรับโครงสร้างเมื่อ 2026-09-03 การนับรายการ `"key":`/`"parent_key": null` ตรงในไฟล์ผลลัพธ์ของ generator เอง (`seed.license-feature.data.ts`, `../carmen-turborepo-backend-v2` HEAD `937cf5ac4`) ได้ **89 แถว ใน 11 module ราก** — `accounting`, `configuration`, `dashboard`, `inventory_management`, `operation_plan`, `procurement`, `product_management`, `report`, `store_operations`, `system_admin`, `vendor_management` — โดย **79 แถวถูก seed เป็น `active`** (ขายได้วันนี้) และ **10 แถวถูก seed เป็น `inactive`** (สิบคีย์ `accounting.*` ที่จองไว้ล่วงหน้าก่อนมี endpoint จริง ตามเฟส C ของสเปก — seed เป็น not-active โดยตั้งใจ ด้วยเหตุผลเดียวกับที่ generator เขียนเตือนตัวเองว่าเคยเกิดบั๊กแบบนี้มาแล้วกับ `report.schedule`) ดู [Data Model](/th/platform/license-catalog/data-model) §3 สำหรับโครงเต็มและความเสี่ยงของการ hide ชั้นกลาง

### 3.3 `state` ที่นี่ไม่ใช่แนวคิดเดียวกับ `state` บนหน้า Feature Flags

`FeatureCatalogPanel.tsx` ประกาศชุดคีย์ `LICENSE_STATE_LABEL`/`LICENSE_STATE_HINT` ของตัวเองโดยเฉพาะ เพื่อไม่ให้ใครหยิบชุดของ `/platform/features` (โมดูล **Feature Flags** ที่ไม่เกี่ยวข้องกัน, `feature_flag.manage`) มาใช้ซ้ำ — สองหน้าจอใช้ค่าสตริงเดียวกัน (`active`/`inactive`/`hide`) แต่หมายความต่างกัน บนหน้า Feature Flags `hide` ทำให้ทั้งหน้าจอและ route หายไปจาก SPA เลย ส่วนที่นี่ `hide` แปลว่า "ไม่มี business unit ไหนได้คีย์นี้เพิ่มอีก และทุก BU ที่มีอยู่แล้วเสียเมนูนั้นไป" — เป็นการตัดสินใจเชิงพาณิชย์ ไม่ใช่เรื่อง routing

### 3.4 Bundle เป็นของที่จัดเอง ไม่ได้มาจากโครงต้นไม้ของ module

หนึ่ง bundle (`tb_license_feature_group`) คือชุด feature key ที่เลือกเองอย่างอิสระ — ข้าม `inventory.count` กับ `report.daily` มาอยู่กลุ่มเดียวกันได้ ต่างจาก "module" ที่เป็นกิ่งต่อเนื่องของต้นไม้เสมอ (§3.2) มีสองกฎที่ควบคุมว่า bundle หนึ่งจะถืออะไรได้บ้าง: **server บังคับ "เลือกลูกแล้วต้องลากสายบรรพบุรุษทั้งหมดมาด้วย"** บนทุกการเรียก `PUT .../features` (ไต่ `parent_key` จนสุดสายก่อนตรวจ ไม่ใช่แค่ชั้นแรก) — bundle จึงไม่มีวันถูกบันทึกโดยถือ feature ตัวหนึ่งแต่ขาด module แม่ตัวใดตัวหนึ่งไป ซึ่ง evaluator ของสิทธิ์จะมองว่าเป็นสิทธิ์ที่ไม่ครบสาย UI ตัวเลือก (`FeatureSelectionCard` ซึ่งตอนนี้ใช้**เฉพาะ** [UI Screens](/th/platform/license-catalog/ui-screens) §5 — มันถูกถอดออกจากขั้นตอนขาย/subscription ทั้งหมดในเฟส 4 ของ License Catalog เอง ตามสเปกฉบับเดียวกัน) บังคับกฎเดียวกันฝั่ง client แต่ด่านฝั่ง server คือด่านจริง เพราะ `PUT` ถูกยิงตรงได้

## 4. บทบาทและสิทธิ์

โมดูลนี้ไม่มีหน้า Permissions แยกต่างหาก — ทั้งสองคู่ permission มีขนาดเล็กพอที่จะเอกสารไว้ในหน้านี้ครบถ้วน

### 4.1 เมทริกซ์การกั้น route ฝั่ง frontend

ทุก route ผ่าน `PrivateRoute` ซึ่งตรวจ `requiredPermission` ก่อน (ไม่ผ่าน → `<Forbidden>` อยู่กับที่) แล้วตรวจ flag `feature` ทีหลังเสมอ (ไม่ผ่าน → `NotFound` เมื่อเป็น `hide`, `ComingSoon` เมื่อเป็น `inactive`) — ดู [Platform RBAC — Permissions](/th/platform/rbac/permissions) สำหรับ resolver ที่ใช้ร่วมกัน

| Route | Permission | Feature flag | Component | แหล่งที่มา |
|---|---|---|---|---|
| `/license-features` | `license_feature.read` | `license_features` | `LicenseCatalog` (`tab="features"`) | `../carmen-platform/src/App.tsx:290-297` |
| `/license-feature-groups` | `license_feature_group.read` | `license_feature_groups` | `LicenseCatalog` (`tab="bundles"`) | `App.tsx:298-305` |
| `/license-feature-groups/new` | `license_feature_group.manage` | `license_feature_groups` | `LicenseFeatureGroupEdit` | `App.tsx:306-313` |
| `/license-feature-groups/:id/edit` | **`license_feature_group.read`** | `license_feature_groups` | `LicenseFeatureGroupEdit` | `App.tsx:314-321` |
| Sidebar "License Feature Groups" | `license_feature_group.read` | `license_feature_groups` | — | `../carmen-platform/src/components/nav/platformNav.ts:21` |
| Sidebar "License Features" | `license_feature.read` | `license_features` | — | `platformNav.ts:22` |

**Route แก้ไขต้องการแค่คีย์อ่าน ตรงกับรูปแบบที่โมดูล [Licenses](/th/platform/licenses) เอกสารไว้สำหรับ route แก้ไขของฟอร์มซื้อของตัวเอง** session ที่มีแค่ `license_feature_group.read` เปิด `/license-feature-groups/:id/edit` ได้และเห็นรายละเอียดชุดเต็ม ๆ `LicenseFeatureGroupEdit.tsx:104`'s `canManage = hasPermission('license_feature_group.manage')` คือตัวที่ตัดสินจริงว่าฟิลด์ไหนแก้ได้ ตัวเลือก feature เป็น `readOnly` หรือไม่ และแถบบันทึกท้ายจอจะ render หรือไม่ (`{canManage && (...)}` — session ที่มีแค่ `read` จะไม่เห็นแถบบันทึกเลย ไม่ใช่เห็นแบบกดไม่ได้)

ด่านในหน้าจอ ทั้งคู่บน `license_feature_group.manage`: ปุ่ม **New group** และปุ่มใน empty state (`GroupCatalogPanel.tsx:349,371`) และรายการ **Edit**/**Delete** ในเมนู row (`:286`) — session ที่มีแค่ `.read` เห็นรายการและแถบสัดส่วนได้ แต่ไม่มีทางสร้าง แก้ หรือลบ bundle จากหน้ารายการเอง (ยังเปิด `:id/edit` ผ่าน URL ตรงและเห็นรายละเอียดแบบอ่านอย่างเดียวได้ ตามย่อหน้าก่อนหน้า)

### 4.2 การบังคับใช้ฝั่ง backend

path ทั้งหมดด้านล่างคือ `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/` HEAD `937cf5ac4` (2026-09-06)

| Endpoint | Guard | แหล่งที่มา |
|---|---|---|
| `GET license-features/all` | `AppIdGuard` + `PlatformPermissionGuard`, `license_feature.read` | `platform_license_features/platform_license_features.controller.ts:67-70` |
| `PATCH license-features/:id` | เหมือนกัน, `license_feature.manage` | `platform_license_features.controller.ts:99-102` |
| `GET license-feature-groups` | `license_feature_group.read` | `platform_license_feature_groups/platform_license_feature_groups.controller.ts:78-81` |
| `GET license-feature-groups/:id` | `license_feature_group.read` | `platform_license_feature_groups.controller.ts:112-115` |
| `POST license-feature-groups` | `license_feature_group.manage` | `platform_license_feature_groups.controller.ts:146-149` |
| `PATCH license-feature-groups/:id` | `license_feature_group.manage` | `platform_license_feature_groups.controller.ts:182-185` |
| `PUT license-feature-groups/:id/features` | `license_feature_group.manage` | `platform_license_feature_groups.controller.ts:226-229` |
| `DELETE license-feature-groups/:id` | `license_feature_group.manage` | `platform_license_feature_groups.controller.ts:273-276` |

ต่างจากโมดูล [Licenses](/th/platform/licenses) (ที่ทุก `GET` บนบัญชี licence ไม่มี `@RequirePlatformPermission` เลย อาศัย cluster scope ตรวจแทน) **ทุก route ของโมดูลนี้ — รวมการอ่าน — มี `@RequirePlatformPermission` decorator ชัดเจน** ไม่มี fallback ที่อิง scope ที่นี่: แคตตาล็อกและ bundle ของมันเป็นของระดับแพลตฟอร์มทั้งชุด ไม่ผูกกับ cluster ใด จึงไม่มี scope ที่แคบกว่าให้ guard ถอยไปใช้

### 4.3 ด่านข้ามโมดูล ไม่ใช่คีย์ของโมดูลนี้เอง

**ยืนยันเรื่องนี้ก่อนจะเข้าใจว่าแท็บ Bundles ปิดครบในตัวเองด้านสิทธิ์** ตัวหารของแถบสัดส่วน Features ใน `GroupCatalogPanel` และตัวเลือก feature ทั้งชุดใน `LicenseFeatureGroupEdit` ต่างโหลดแคตตาล็อกผ่าน `subscriptionService.getFeatureCatalog()` ซึ่งเรียก `GET /api-system/platform/license-features` — **ไม่ใช่** `/license-features/all` route เปล่านั้นถูกประกาศอยู่ใน controller คนละตัวเลย คือ `platform_subscriptions/platform_subscriptions.controller.ts:198-200` และต้องการ **`subscription.read`** — เป็นคีย์ของโมดูล [Licenses](/th/platform/licenses) เอง ไม่ใช่ `license_feature.read` หรือ `license_feature_group.read`

ผลที่ตามมา: session ที่มี `license_feature_group.read` + `license_feature_group.manage` แต่**ไม่มี** `subscription.read` เปิด `/license-feature-groups` และแสดงรายการ bundle ได้เต็มที่ เปิด `/license-feature-groups/:id/edit` เพื่อแก้ชื่อ ลำดับ หรือสถานะ active ของ bundle ได้ด้วย — แต่แถบสัดส่วน Features บนรายการจะหายไปเงียบ ๆ (`catalogTotal` ค้างที่ `null` ไม่มีตัวหารให้วาดแถบ) และตัวเลือก feature บนหน้าแก้ไขจะล้มเหลวตรง ๆ (`catalog.failed === true` แสดงปุ่ม retry แทนตัวเลือก) — บล็อกสิ่งเดียวที่หน้านั้นมีไว้ทำ โดยที่ route เองไม่เคยปฏิเสธเลย นี่คือความสัมพันธ์ข้ามโมดูลจริงที่พิสูจน์แล้ว ไม่ใช่บั๊กของโมดูลใดโมดูลหนึ่ง: endpoint ที่ใช้ร่วมกันมีเหตุผลเพราะแคตตาล็อก "อะไรขายได้ตอนนี้" ชุดเดียวกันคือสิ่งที่ตัวเลือก feature ของ subscription ก็ต้องการเหมือนกัน การใช้ endpoint เดียวหลีกเลี่ยงการมีตรรกะ "กรอง `hide` ออก" สองชุดที่อาจไม่ตรงกันเอง

## 5. โมดูลที่เกี่ยวข้อง

- [Licenses](/th/platform/licenses) — ผู้*บริโภค*ของ bundle ในโมดูลนี้: การ์ด "Purchased Groups" ของ subscription หนึ่งใบหยิบจาก bundle ที่จัดไว้ที่นี่ และตัวเลือกกลุ่มของมันเองพึ่งพา endpoint ข้ามโมดูลที่เอกสารไว้ใน §4.3
- [Platform RBAC](/th/platform/rbac) — เป็นเจ้าของ UI แคตตาล็อกสิทธิ์ (`/platform/category-permissions`) ที่ `license_feature.*`/`license_feature_group.*` ปรากฏอยู่ข้าง ๆ ทุก resource อื่น โมดูลนี้เองไม่ได้นิยามหรือแก้ permission key
- [Feature Flags](/th/platform/feature-flags) — คนละหน้าจอกันเลย (`feature_flag.manage`) ที่คอมเมนต์ในซอร์สของโมดูลนี้เตือนไว้ตรง ๆ ว่าอย่าเอาไปปนกับค่า `state` ที่เอกสารไว้ใน §3.3

## 6. แหล่งข้อมูลอ้างอิง

path ทั้งหมดด้านล่างคือ `../carmen-platform` (Platform admin SPA, HEAD `157a65e`, 2026-09-04) ยกเว้นที่ขึ้นต้นด้วย `../carmen-turborepo-backend-v2` (backend monorepo, HEAD `937cf5ac4`, 2026-09-06)

- `../carmen-platform/src/App.tsx` (บรรทัด 290–321) — ทั้งสี่ route ของโมดูลนี้
- `../carmen-platform/src/components/nav/platformNav.ts` (บรรทัด 21–22) — สองรายการ sidebar
- `../carmen-platform/src/pages/LicenseCatalog.tsx` — shell ที่ใช้ร่วมกัน, การกั้นแท็บ, และสามพฤติกรรมใน §3.1
- `../carmen-platform/src/pages/licenseCatalog/FeatureCatalogPanel.tsx`, `src/pages/licenseFeatures/{CatalogStateBar,ModuleShelf}.tsx` — แท็บ Features
- `../carmen-platform/src/pages/licenseCatalog/GroupCatalogPanel.tsx` — แท็บ Bundles
- `../carmen-platform/src/pages/LicenseFeatureGroupEdit.tsx`, `src/pages/licenses/subscriptionEdit/FeatureSelectionCard.tsx`, `src/pages/licenses/GroupCompositionPanel.tsx`, `src/pages/licenses/FeatureCompositionBar.tsx` — ตัวแก้ไข bundle และส่วนประกอบร่วม
- `../carmen-platform/src/services/licenseFeatureService.ts`, `src/services/licenseFeatureGroupService.ts`, `src/services/subscriptionService.ts` (`getFeatureCatalog`, §4.3) — REST client
- `../carmen-platform/src/utils/featureTree.ts`, `src/pages/licenses/subscriptionEdit/featureSelection.ts` — ตัวช่วยเดินต้นไม้ (§3.2, §3.4)
- `../carmen-platform/docs/superpowers/specs/2026-09-03-license-feature-tree-design.md` — บันทึกการออกแบบการปรับโครงแคตตาล็อกเป็น n ชั้น (§3.2)
- `../carmen-turborepo-backend-v2/scripts/generate-license-catalog/run.ts` — ผู้เขียนแถว `tb_license_feature` เพียงรายเดียว
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.license-feature.data.ts` — ผลลัพธ์ของ generator เอง ที่มาของจำนวน 89/11/79/10 ที่ยืนยันแล้วใน §3.2
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_license_feature` (บรรทัด 1214), `tb_license_feature_group` (บรรทัด 1284), `tb_license_feature_group_item` (บรรทัด 1313), `enum_license_feature_state` (บรรทัด 740)
- `../carmen-turborepo-backend-v2/apps/micro-business/src/license-feature/license-feature.service.ts`, `apps/micro-business/src/license-feature-group/license-feature-group.service.ts` — ตรรกะธุรกิจชั้น RPC (`affected_bu_count`, กฎ "ลูกลากพ่อ", การป้องกันลบ bundle ที่ยังใช้งานอยู่)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/{platform_license_features,platform_license_feature_groups,platform_subscriptions}/*.controller.ts` — การบังคับใช้สิทธิ์ (§4)

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/license-catalog/data-model) — `tb_license_feature`, `tb_license_feature_group`, `tb_license_feature_group_item`; โครงต้นไม้ n ชั้นและความเสี่ยงของการ hide ชั้นกลาง; จำนวนแคตตาล็อกที่ยืนยันแล้ว
- [UI Screens](/th/platform/license-catalog/ui-screens) — กลไกแท็บของ shell `LicenseCatalog` แบบละเอียด, `FeatureCatalogPanel`, `GroupCatalogPanel`, `LicenseFeatureGroupEdit`, และส่วนประกอบตัวเลือก feature/แถบสัดส่วนที่ใช้ร่วมกัน
