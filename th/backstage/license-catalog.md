---
title: แคตตาล็อกไลเซนส์ (License Catalog)
description: หน้าจอเดียว สองแท็บ สอง nav row — แคตตาล็อก feature ที่ขายได้ (Features) และโมดูลที่จัดไว้ล่วงหน้า (Modules บนจอ, bundles ในโค้ด) — แต่ละแท็บมีคู่ permission และ feature flag ของตัวเอง
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, license-catalog
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# แคตตาล็อกไลเซนส์ (License Catalog)

โมดูล **License Catalog** คือหน้าจอเดียว `LicenseCatalog` ที่ render อยู่หลังสอง route แยกกัน สลับด้วย prop `tab`: `/license-features` (แท็บ **Features**, `FeatureCatalogPanel`) และ `/license-modules` (แท็บ **Modules**, `GroupCatalogPanel`) นี่คือการรวมเอกสาร ไม่ใช่การรวมผลิตภัณฑ์ — สองแท็บนี้ยังถือ nav row, คู่ permission และ feature-flag key ของตัวเองเหมือนเดิมทุกประการ และหน้านี้เอกสารทั้งคู่ไว้เป็นโมดูลเดียวเพราะทั้งสองตอบคำถามเดียวกัน: *Carmen Blue ขายอะไร และจัดแพ็กเกจมันยังไง* **Features** คือแคตตาล็อกดิบของความสามารถที่ขายได้ สร้างจาก permission map แก้ได้แค่ `state` (ขายได้ / ยังขายไม่ได้ / ซ่อน) **Bundles** คือชุดที่จัดไว้ล่วงหน้าโดยผู้ดูแล — ข้าม module ได้อย่างอิสระ — ที่ subscription หยิบไปใช้จริงบนหน้าจอขายของโมดูล [Licenses](/th/backstage/licenses) route ที่สาม `/license-modules/{new,:id/edit}` render component แยกต่างหาก `LicenseFeatureGroupEdit` สำหรับสร้าง/แก้ไขหนึ่งชุด

> **เปลี่ยนคำเรียก 2026-10-27:** SPA ตอนนี้เรียก license feature group ว่า **Module** (sidebar "License Modules", แท็บ "Modules", editor "New module") และเรียกราก (root) เดิมของ feature tree ว่า **Feature area** (`../carmen-backstage` commit `e848573c` เปลี่ยนเฉพาะข้อความ i18n) ตาราง, API path, i18n key, ชื่อในโค้ด และค่า `tab: 'bundles'` ของ component ไม่เปลี่ยน หน้านี้และหน้าย่อยจึงยังใช้คำว่า *bundle* / *group* เมื่อหมายถึงโค้ดหรือข้อมูล และใช้ *แท็บ Modules* เมื่อหมายถึงหน้าจอ "Module" ฝั่งขาย (Procurement, Inventory, Recipe, GL, AP, AR, Asset, Income) ก็คือแถว `tb_license_feature_group` หนึ่งแถวพอดี

> **At a Glance**
> **Component:** `LicenseCatalog` (component เดียว, prop `tab: 'bundles' | 'features'`) &nbsp;·&nbsp; **Route:** `/license-features` → แท็บ Features, `/license-modules` → แท็บ Modules, `/license-modules/new` และ `/license-modules/:id/edit` → `LicenseFeatureGroupEdit` &nbsp;·&nbsp; **Permission key — สองคู่แยกจากกัน:** แท็บ Features `license_feature.read` (nav/อ่าน) + `license_feature.manage` (แก้ `state`); แท็บ Modules `license_feature_group.read` (nav/อ่าน) + `license_feature_group.manage` (สร้าง/แก้/ลบ/ตั้ง feature) &nbsp;·&nbsp; **Feature-flag key:** `license_features` และ `license_feature_groups` แท็บละหนึ่ง &nbsp;·&nbsp; **Nav group:** `navGroup.licenseManagement` — สองแถว "License Modules" กับ "License Features" (ป้ายบน sidebar) ซึ่งพาไปแท็บที่ตัว shell เองเรียกว่า "Modules" กับ "Features" &nbsp;·&nbsp; **ขนาดแคตตาล็อก (ยืนยันจากข้อมูล generator ไม่ใช่จากคอมเมนต์ในซอร์ส):** 112 แถว ใน 13 feature area ราก — ขายได้ (`active`) 105, สำรองไว้ (`inactive`) 7 คีย์ (`accounting.*` ที่จองไว้ล่วงหน้ารอ endpoint จริง); root ที่ 12 คือ `interface` มาเมื่อ 2026-09-08 และที่ 13 คือ `ai` ในเดือนตุลาคม 2026 &nbsp;·&nbsp; **Kind ของกลุ่ม:** ตั้งแต่ 2026-09-10 ทุก bundle มี `kind` (`standard` | `interface`) ตั้งได้ตอนสร้างเท่านั้น — bundle ชนิด `interface` ขายบน interface licence เท่านั้น ไม่เคยขายบน subscription &nbsp;·&nbsp; **ด่านข้ามโมดูลที่ต้องรู้:** ตัวหารของแถบสัดส่วนบนแท็บ Modules และตัวเลือก feature ทั้งชุดในหน้าแก้ไขกลุ่ม ต่างโหลดผ่าน `GET /api-system/backstage/license-features` (ไม่มี `/all`) ซึ่งกั้นด้วย `subscription.read` — permission key ของ**อีกโมดูลหนึ่ง**โดยสิ้นเชิง (§4) &nbsp;·&nbsp; **e2e suite:** smoke เท่านั้น — `tests/license-features/license-features-smoke.spec.ts` และ `tests/license-modules/license-modules-smoke.spec.ts` (หน้า render ได้, มี sidebar entry; ตัวหลังอัปเดตเมื่อ 2026-10-27 ให้ตรง `/license-modules` และคำว่า "License Modules") — ทุกคำกล่าวอ้างในหน้าของโมดูลนี้มาจากการอ่าน implementation ของ `../carmen-backstage` และ `../carmen-turborepo-backend` โดยตรง &nbsp;·&nbsp; **หน้าย่อย:** 2

![แคตตาล็อกไลเซนส์ (License Catalog) screen](/screenshots/platform/license-catalog/index.png)

## 1. ภาพรวม

- **`/license-features` → `LicenseCatalog` (`tab="features"`) → `FeatureCatalogPanel`** — หน้าจอแคตตาล็อกที่เน้นอ่าน ทุกแถว feature ที่ยังไม่ถูกลบ รวมแถวที่ซ่อนไว้ จัดเป็น "ชั้นวาง" ต่อ module ราก พร้อมเยื้องเป็นชั้น n ระดับสำหรับลูกและหลาน พื้นที่แก้ไขมีแค่สวิตช์สถานะต่อแถว (`active` / `inactive` / `hide`) ตัวแถวเองเป็นของ generator ฝั่ง backend (`scripts/generate-license-catalog/run.ts`) ไม่ใช่ของหน้านี้
- **`/license-modules` → `LicenseCatalog` (`tab="bundles"`) → `GroupCatalogPanel`** — รายการโมดูล (bundle) ที่จัดไว้ล่วงหน้า: หนึ่งแถวต่อหนึ่งชุด แถบสัดส่วน Features ที่ใช้ตัวหารร่วมทั้งหน้า คอลัมน์จำนวนสัญญา สถานะ active/inactive และปุ่มแก้ไข/ลบต่อแถว
- **`/license-modules/new`, `/license-modules/:id/edit` → `LicenseFeatureGroupEdit`** — route แยกต่างหาก (ไม่ใช่แท็บใน `LicenseCatalog`) สำหรับสร้างหรือแก้ไขหนึ่งชุด: ตัวตนของมัน ตำแหน่งบนฟอร์มขาย สถานะ active/inactive และชุด feature ที่มันให้สิทธิ์

ทั้ง route ของสองแท็บและ route ของ `LicenseFeatureGroupEdit` ถูกกั้นด้วย `PrivateRoute` ที่มี `requiredPermission` และ flag `feature` (`App.tsx:319-350`) ดูเมทริกซ์เต็มที่ §4 รวมถึง route เดียว (`:id/edit`) ที่ต้องการแค่คีย์อ่าน

## 2. บริบททางธุรกิจ

การขาย feature ของ Carmen Blue inventory ให้ business unit หนึ่งเกิดเป็นสองขั้นตอนที่แยกจากกัน และโมดูลนี้เป็นเจ้าของทั้งคู่:

1. **ตัดสินว่าอะไรขายได้บ้าง** ทุก route ในผลิตภัณฑ์ผูกกับ permission resource หนึ่งตัว และทุก resource ที่ควร*ขายได้* — ไม่ใช่แค่ควบคุมการเข้าถึง — จะมีแถวคู่กันใน `tb_license_feature` สร้างอัตโนมัติจาก permission map (`permission.route-map.ts` + `seed.permission.data.ts`) ผู้ดูแลแพลตฟอร์มเพิ่ม feature ด้วยมือไม่ได้ คันโยกเดียวที่หน้านี้ให้คือปิดของที่มีอยู่แล้ว (`inactive` — หยุดขายเพิ่ม) หรือปิดสนิท (`hide` — ถอดเมนูออกจากทุกคนที่มีอยู่แล้ว)
2. **จัดของที่ขายได้ให้เป็นสิ่งที่พนักงานขายหยิบใช้ครั้งเดียว** การติ๊ก feature กว่าร้อยตัวทีละตัวทุกครั้งที่ทำสัญญาใหม่ไม่สเกลและไม่ตรงกับวิธีที่ Carmen Blue ขายจริง — ลูกค้าซื้อแพ็กเกจ ไม่ใช่รายการติ๊ก **Bundles** (`tb_license_feature_group`) คือคำตอบที่ผู้ดูแลจัดเอง: ชุด feature key ที่ตั้งชื่อได้ จัดลำดับได้ ข้าม module ได้อย่างอิสระ ที่ subscription ของโมดูล [Licenses](/th/backstage/licenses) อ้างถึงเป็นก้อนเดียว (`tb_subscription_bu_group`) ไม่ใช่แกะออกมาเป็น feature รายตัวในสัญญา

สองขั้นตอนนี้เป็นบทบาทที่แยกกันโดยตั้งใจ: ตัดสินว่าอะไร*ขายได้* (โมดูลนี้) กับตัดสินว่าลูกค้ารายหนึ่ง*ซื้ออะไรจริง* (โมดูล [Licenses](/th/backstage/licenses)) เป็นงานคนละอย่าง กั้นด้วย permission resource คนละตัวกันโดยสิ้นเชิง

## 3. แนวคิดสำคัญ

### 3.1 component เดียว สองแท็บ สามการตัดสินใจที่ตั้งใจ

คอมเมนต์ใน `LicenseCatalog.tsx` เองระบุสามอย่างที่ผู้ทดสอบจะเข้าใจผิดว่าเป็นบั๊กถ้าไม่รู้ที่มา:

- **สลับแท็บคือการ navigate ไม่ใช่การเปลี่ยน state** `onChange` ของ `TabStrip` เรียก `navigate(TAB_PATH[next])` ซึ่งเปลี่ยน route ทำให้ panel ลูกของ `LicenseCatalog` remount และดึงข้อมูลใหม่ ไม่มีการแคชข้ามแท็บเลย นี่คือความตั้งใจ: ทั้งสอง panel ดึงครั้งเดียวและมีเพดานเชิงโครงสร้างอยู่แล้ว (ทั้งแคตตาล็อก feature และรายการ bundle เป็นข้อมูลที่จัดเอง ไม่ได้งอกตามการใช้งาน) ต้นทุนของการดึงใหม่ทุกครั้งที่สลับแท็บจึงต่ำมากจนไม่คุ้มที่จะเลี่ยง และการทำแคชที่ต้องครอบคลุมสอง route ที่มี permission ต่างกันคือความซับซ้อนที่ไม่มีใครขอ
- **ชื่อหัวหน้าคงที่เสมอ มีแค่ subtitle ที่เปลี่ยน** `title` ของ `PageHeader` เป็น `t('pages.licenseCatalog.title')` เสมอ — "License Catalog" ตรงตัว — ไม่ว่าแท็บไหนกำลังเปิดอยู่ มีแค่ `subtitle` ที่สลับระหว่าง `pages.licenseFeatureGroups.subtitle` ("Curated bundles of licence features, used when selling a subscription") กับ `pages.licenseFeatures.subtitle` ("Choose which features can still be sold. The catalog itself is generated — only the state is yours to set.") นี่คือการตัดสินใจเรื่องตัวตนโดยตั้งใจ ไม่ใช่ความพลาด: ชื่อที่เปลี่ยนตามแท็บจะทำให้การรวมนี้อ่านเป็นสองหน้าจอที่บังเอิญใช้ URL prefix เดียวกัน ซึ่งทำลายเหตุผลทั้งหมดที่เอกสารนี้ถือว่ามันเป็นโมดูลเดียว
- **แถบแท็บหายไปเมื่อเข้าถึงได้แค่แท็บเดียว** `tabs` คำนวณโดยกรอง `TAB_ORDER` (`['bundles', 'features']`) ผ่านด่านของแต่ละแท็บเอง (`TAB_GATE`, §4) — `hasPermission(gate.permission) && flagOf(gate.feature) === 'active'` — และ `<TabStrip>` จะ render ก็ต่อเมื่อ `tabs.length > 1` เท่านั้น นี่คือ**การตรวจซ้ำฝั่ง client** ของสิ่งที่ route guard ตรวจไปแล้วก่อนที่ panel จะ mount ได้เลย (ดู §4) — มันมีอยู่เพราะทั้งสองแท็บใช้ shell เดียวกัน shell เองจึงต้องเป็นคนตัดสินว่าจะวาดตัวควบคุมที่ชี้ไปแท็บที่ session ปัจจุบันเข้าไม่ได้หรือไม่ session ที่เข้าถึงได้แค่แท็บเดียวจึงเห็น panel เดียวไม่มีแท็บ ไม่มีแถบเปล่าอยู่ข้างบน

### 3.2 แคตตาล็อกเป็นต้นไม้ n ชั้นที่เป็นของ generator ไม่ใช่รายการแบน

แถวของ `tb_license_feature` มาจาก `scripts/generate-license-catalog/run.ts` **เท่านั้น** — `licenseFeatureService` ไม่มี create หรือ delete โดยเจตนา สิ่งเดียวที่ผู้ดูแลเป็นเจ้าของคือ `state` นับตั้งแต่งาน "license feature tree" เมื่อ 2026-09-03 (`docs/superpowers/specs/2026-09-03-license-feature-tree-design.md` เฟส A–C ขึ้นวันเดียวกันหมด) `parent_key` คือ**prefix ที่ยาวที่สุดที่มีอยู่จริงในแคตตาล็อก** ไม่ใช่แค่ข้อความก่อนจุดแรก — คีย์จึงอยู่ลึกได้ถึงสามชั้นจริง (`accounting.config.ap` มีพ่อเป็น `accounting.config` ซึ่งมีพ่อเป็น `accounting`) `moduleOf()` (`featureSelection.ts:26`) ยังตัดที่จุดแรกเหมือนเดิมและใช้ได้ถูกต้องเฉพาะการหา module **ราก** เท่านั้น — การไต่สายบรรพบุรุษจริงต้องใช้ `ancestorsOf()`/`descendantKeys()`/`flattenDescendants()` (`utils/featureTree.ts`) ไม่ใช่การหั่นสตริงที่จุดแรก

**คอมเมนต์ในซอร์สโค้ดนี้ล้าสมัย — ยืนยันจำนวนกับข้อมูล generator ไม่ใช่กับคอมเมนต์** คอมเมนต์ของ `FeatureCatalogPanel.tsx` เองและของ `ModuleShelf.tsx` ต่างพูดถึง "76 แถว" / "10 module + 66 ลูก" — ทั้งคู่มาก่อนงานปรับโครงสร้างเมื่อ 2026-09-03 การนับรายการ `"key":`/`"parent_key": null` ตรงในไฟล์ผลลัพธ์ของ generator เอง (`seed.license-feature.data.ts`, `../carmen-turborepo-backend` HEAD `c9d788829`, 2026-10-27) ได้ **112 แถว ใน 13 feature area ราก** — `accounting`, `ai`, `configuration`, `dashboard`, `interface`, `inventory_management`, `operation_plan`, `procurement`, `product_management`, `report`, `store_operations`, `system_admin`, `vendor_management` — โดย **105 แถวถูก seed เป็น `active`** (ขายได้วันนี้) และ **7 แถวถูก seed เป็น `inactive`** (ทั้งหมดเป็นคีย์ `accounting.*` ที่จองไว้ล่วงหน้าก่อนมี endpoint จริง ตามเฟส C ของสเปก — seed เป็น not-active โดยตั้งใจ ด้วยเหตุผลเดียวกับที่ generator เขียนเตือนตัวเองว่าเคยเกิดบั๊กแบบนี้มาแล้วกับ `report.schedule`) จำนวนขยับจาก 107/12/100/7 (ฐาน 2026-09-22) เป็น 112/13/105/7 หรือ +5 คีย์สุทธิ เทียบกับไฟล์ seed ฉบับ 2026-09-22: **root `ai` ใหม่** (`ai`, `ai.mcp` — licence ของ MCP-token ย้ายมาอยู่ใต้ `ai` ด้วย migration `20261014230000_move_mcp_license_under_ai`), `configuration.customer` และการจัด interface-brand ใหม่ — `interface.accounting.external` กลายเป็น `interface.export.external` ใต้หมวดใหม่ `interface.export` (migration `20261018120000_move_external_interface_under_export` ซึ่ง rename แถวแคตตาล็อกและเขียนทุก group item ใหม่เพื่อไม่ให้ BU ใดเสีย licence) และ `interface.pos.micros` ถูกแทนใน seed ด้วยสองคีย์ `interface.pos.micros3700` กับ `interface.pos.simphony` (commit `2cfc4c04f`; ไม่มี SQL migration เขียน group item `interface.pos.micros` เดิมใหม่ — ดูหมายเหตุ ticket ในรายงาน) ก่อนหน้านั้นจำนวนขยับจาก 89/11/79/10 (ฐานเมื่อ 2026-09-06) เป็น +19/−2 คีย์ diff ตรงกับไฟล์ seed ฉบับ 2026-09-05: **module `interface`** (ตอนเพิ่มครั้งแรก 12 คีย์: `interface`, แถวหมวดสามแถว `interface.{accounting,pos,pms}` และใบ brand แปดใบ; **วันนี้ 14 คีย์**: `interface`, สี่หมวด `interface.{accounting,export,pos,pms}` และใบเก้าใบ — `accounting.{carmen_gl,blueledgers}`, `export.external`, `pos.{infrasys,micros3700,simphony,square}`, `pms.{opera,protel}`) เพิ่มเมื่อ 2026-09-08 ตอน interface entitlement กลายเป็น licence feature; คีย์ `configuration.*` ห้าตัว (`chart_of_account_mapping`, `email_profile`, `email_template`, `cost_center`, `cost_center_group`); คีย์ `accounting.gl.*` สองตัว (`budget`, `jv_template` สำหรับ endpoint GL budget/JV-template ใหม่); และการเปลี่ยนชื่อ `system_admin.period` → `system_admin.inventory_period` (2026-09-16, `20260916140000_rename_period_to_inventory_period` — migration เดียวกันเปลี่ยนชื่อ permission resource และ `api_name` ของ `period.*` ด้วย และ `20260916150000` ที่ตามมาแก้ `tb_license_feature_group_item.feature_key` ซึ่ง migration แรกพลาดไปเพราะตารางเชื่อมนั้นเป็น soft string reference ไม่มี FK ทำให้กลุ่มของทุก BU ชี้ไปคีย์ที่ไม่มีอยู่แล้ว และ `LicenseInterceptor` ตอบ `403 LICENSE_REQUIRED` กับทุกการเรียก `/inventory-periods`) `system_admin.query_dataset` ถูกลบออก คีย์ `interface.*`, `ai`/`ai.mcp` และคีย์ `configuration.*` สองตัว (`email_profile`, `email_template`; `chart_of_account_mapping` ไม่อยู่ในชุดอีกต่อไป) เข้ามาผ่าน **ชุดต้นทางใหม่ของ generator ชื่อ `LICENSE_ONLY_RESOURCES`** (`permission.route-map.ts:472`): คีย์ที่มีจริงและขายอยู่แล้วแต่**ไม่มี permission และไม่มี route** รองรับ ซึ่ง generator ปล่อยออกเป็น `active` และยกเว้นจาก `assert_planned_sets_agree()` มันผ่านชุด `PLANNED_LICENSE_RESOURCES` เดิมไม่ได้ เพราะชุดนั้นบังคับ `inactive` (กลุ่มเก็บคีย์แบบนั้นไว้ได้แต่เพิ่มใหม่ไม่ได้ จึงไม่มีใครขาย interface ให้ BU ใหม่ได้เลย) และยังต้องเป็นสมาชิกของ `PLANNED_RESOURCES` ด้วย ซึ่งจะหลอก `check-endpoint-permission` ไม่มีคีย์ `interface.*` ตัวใดปรากฏใน map route→feature ของ `license-catalog.generated.ts` ดังนั้น `LicenseInterceptor` ไม่เคยกั้น route ของ interface — การบังคับใช้อยู่ที่ inventory frontend ที่อ่าน `GET /api/license` ([Licenses](/th/backstage/licenses) §3.6) ดู [Data Model](/th/backstage/license-catalog/data-model) §3 สำหรับโครงเต็มและความเสี่ยงของการ hide ชั้นกลาง

### 3.3 `state` ที่นี่ไม่ใช่แนวคิดเดียวกับ `state` บนหน้า Feature Flags

`FeatureCatalogPanel.tsx` ประกาศชุดคีย์ `LICENSE_STATE_LABEL`/`LICENSE_STATE_HINT` ของตัวเองโดยเฉพาะ เพื่อไม่ให้ใครหยิบชุดของ `/backstage/features` (โมดูล **Feature Flags** ที่ไม่เกี่ยวข้องกัน, `feature_flag.manage`) มาใช้ซ้ำ — สองหน้าจอใช้ค่าสตริงเดียวกัน (`active`/`inactive`/`hide`) แต่หมายความต่างกัน บนหน้า Feature Flags `hide` ทำให้ทั้งหน้าจอและ route หายไปจาก SPA เลย ส่วนที่นี่ `hide` แปลว่า "ไม่มี business unit ไหนได้คีย์นี้เพิ่มอีก และทุก BU ที่มีอยู่แล้วเสียเมนูนั้นไป" — เป็นการตัดสินใจเชิงพาณิชย์ ไม่ใช่เรื่อง routing

### 3.4 Bundle เป็นของที่จัดเอง ไม่ได้มาจากโครงต้นไม้ของ module — และตั้งแต่ 2026-09-10 มี kind

หนึ่ง bundle (`tb_license_feature_group`) คือชุด feature key ที่เลือกเองอย่างอิสระ — ข้าม `inventory.count` กับ `report.daily` มาอยู่กลุ่มเดียวกันได้ ต่างจาก "module" ที่เป็นกิ่งต่อเนื่องของต้นไม้เสมอ (§3.2) ตั้งแต่ migration `20260910000000_license_feature_group_kind` ทุก bundle ยังถือ `kind` ด้วย: `standard` (ขายบน subscription หลัก — ค่า default) หรือ `interface` (ขายหนึ่งกลุ่มต่อหนึ่ง licence บน interface licence, `INF`) kind เลือกด้วยปุ่ม segmented บนฟอร์มสร้าง และ**ล็อกหลังจากนั้น** — ฟอร์มแก้ไขแสดงแบบอ่านอย่างเดียวพร้อมคำใบ้ "Set when the group is created — changing it would move sold entitlements between license kinds" และ DTO update ของ backend ไม่รับมัน รายการ Bundles ทำเครื่องหมาย bundle ชนิด `interface` ด้วย badge และส่งออก kind ใน CSV kind ไม่ได้ derive จากคีย์ข้างใน (backfill เมื่อ 2026-09-10 derive ครั้งเดียว โดยทำเครื่องหมาย `interface` ให้ทุกกลุ่มที่ item ที่ยังอยู่*ทั้งหมด*เป็น `interface`/`interface.*` ส่วนกลุ่มผสมและกลุ่มว่างยังเป็น `standard`) — คอลัมน์คือ source of truth และ backend ปฏิเสธด้วย 400 ทั้งกลุ่ม `interface` บน subscription และกลุ่ม `standard` บน interface licence เหตุผลการออกแบบ — ทำไมเป็นคอลัมน์ ไม่ใช่ prefix ของ code หรือการตรวจคีย์ — อยู่ใน `../carmen-backstage/docs/superpowers/specs/2026-09-09-interface-license-split-design.md` §2 มีสองกฎที่ควบคุมว่า bundle หนึ่งจะถืออะไรได้บ้าง: **server บังคับ "เลือกลูกแล้วต้องลากสายบรรพบุรุษทั้งหมดมาด้วย"** บนทุกการเรียก `PUT .../features` (ไต่ `parent_key` จนสุดสายก่อนตรวจ ไม่ใช่แค่ชั้นแรก) — bundle จึงไม่มีวันถูกบันทึกโดยถือ feature ตัวหนึ่งแต่ขาด module แม่ตัวใดตัวหนึ่งไป ซึ่ง evaluator ของสิทธิ์จะมองว่าเป็นสิทธิ์ที่ไม่ครบสาย UI ตัวเลือก (`FeatureSelectionCard` ซึ่งตอนนี้ใช้**เฉพาะ** [UI Screens](/th/backstage/license-catalog/ui-screens) §5 — มันถูกถอดออกจากขั้นตอนขาย/subscription ทั้งหมดในเฟส 4 ของ License Catalog เอง ตามสเปกฉบับเดียวกัน) บังคับกฎเดียวกันฝั่ง client แต่ด่านฝั่ง server คือด่านจริง เพราะ `PUT` ถูกยิงตรงได้

## 4. บทบาทและสิทธิ์

โมดูลนี้ไม่มีหน้า Permissions แยกต่างหาก — ทั้งสองคู่ permission มีขนาดเล็กพอที่จะเอกสารไว้ในหน้านี้ครบถ้วน

### 4.1 เมทริกซ์การกั้น route ฝั่ง frontend

ทุก route ผ่าน `PrivateRoute` ซึ่งตรวจ `requiredPermission` ก่อน (ไม่ผ่าน → `<Forbidden>` อยู่กับที่) แล้วตรวจ flag `feature` ทีหลังเสมอ (ไม่ผ่าน → `NotFound` เมื่อเป็น `hide`, `ComingSoon` เมื่อเป็น `inactive`) — ดู [Backstage RBAC — Permissions](/th/backstage/rbac/permissions) สำหรับ resolver ที่ใช้ร่วมกัน

| Route | Permission | Feature flag | Component | แหล่งที่มา |
|---|---|---|---|---|
| `/license-features` | `license_feature.read` | `license_features` | `LicenseCatalog` (`tab="features"`) | `../carmen-backstage/src/App.tsx:319-326` |
| `/license-modules` (legacy `/license-feature-groups/*` redirect มาที่นี่ผ่าน `LegacyLicenseModuleRedirect`, `App.tsx:656`) | `license_feature_group.read` | `license_feature_groups` | `LicenseCatalog` (`tab="bundles"`) | `App.tsx:327-334` |
| `/license-modules/new` | `license_feature_group.manage` | `license_feature_groups` | `LicenseFeatureGroupEdit` | `App.tsx:335-342` |
| `/license-modules/:id/edit` | **`license_feature_group.read`** | `license_feature_groups` | `LicenseFeatureGroupEdit` | `App.tsx:343-350` |
| Sidebar "License Modules" (nav key `nav.licenseFeatureGroups`) | `license_feature_group.read` | `license_feature_groups` | — | `../carmen-backstage/src/components/nav/backstageNav.ts:25` |
| Sidebar "License Features" | `license_feature.read` | `license_features` | — | `backstageNav.ts:26` |

**Route แก้ไขต้องการแค่คีย์อ่าน ตรงกับรูปแบบที่โมดูล [Licenses](/th/backstage/licenses) เอกสารไว้สำหรับ route แก้ไขของฟอร์มซื้อของตัวเอง** session ที่มีแค่ `license_feature_group.read` เปิด `/license-modules/:id/edit` ได้และเห็นรายละเอียดชุดเต็ม ๆ `LicenseFeatureGroupEdit.tsx:104`'s `canManage = hasPermission('license_feature_group.manage')` คือตัวที่ตัดสินจริงว่าฟิลด์ไหนแก้ได้ ตัวเลือก feature เป็น `readOnly` หรือไม่ และแถบบันทึกท้ายจอจะ render หรือไม่ (`{canManage && (...)}` — session ที่มีแค่ `read` จะไม่เห็นแถบบันทึกเลย ไม่ใช่เห็นแบบกดไม่ได้)

ด่านในหน้าจอ ทั้งคู่บน `license_feature_group.manage`: ปุ่ม **New module** และปุ่มใน empty state และรายการ **Edit**/**Delete** ในเมนู row (ทั้งหมดเป็น `<Can permission="license_feature_group.manage">` ใน `GroupCatalogPanel.tsx`) — session ที่มีแค่ `.read` เห็นรายการและแถบสัดส่วนได้ แต่ไม่มีทางสร้าง แก้ หรือลบ bundle จากหน้ารายการเอง (ยังเปิด `:id/edit` ผ่าน URL ตรงและเห็นรายละเอียดแบบอ่านอย่างเดียวได้ ตามย่อหน้าก่อนหน้า)

### 4.2 การบังคับใช้ฝั่ง backend

path ทั้งหมดด้านล่างคือ `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/` HEAD `c9d788829` (2026-10-27) Route อยู่ภายใต้ `@Controller('api-system/backstage')` (เปลี่ยนชื่อจาก `api-system/platform`)

| Endpoint | Guard | แหล่งที่มา |
|---|---|---|
| `GET license-features/all` | `AppIdGuard` + `BackstagePermissionGuard`, `license_feature.read` | `backstage_license_features/backstage_license_features.controller.ts:74-76` |
| `PATCH license-features/:id` | เหมือนกัน, `license_feature.manage` | `backstage_license_features.controller.ts:106-108` |
| `GET license-feature-groups` | `license_feature_group.read` | `backstage_license_feature_groups/backstage_license_feature_groups.controller.ts:85-87` |
| `GET license-feature-groups/:id` | `license_feature_group.read` | `backstage_license_feature_groups.controller.ts:119-121` |
| `POST license-feature-groups` | `license_feature_group.manage` | `backstage_license_feature_groups.controller.ts:159-161` |
| `PATCH license-feature-groups/:id` | `license_feature_group.manage` | `backstage_license_feature_groups.controller.ts:197-199` |
| `PUT license-feature-groups/:id/features` | `license_feature_group.manage` | `backstage_license_feature_groups.controller.ts:253-255` |
| `DELETE license-feature-groups/:id` | `license_feature_group.manage` | `backstage_license_feature_groups.controller.ts:312-314` |

ต่างจากโมดูล [Licenses](/th/backstage/licenses) (ที่ทุก `GET` บนบัญชี licence ไม่มี `@RequireBackstagePermission` เลย อาศัย cluster scope ตรวจแทน) **ทุก route ของโมดูลนี้ — รวมการอ่าน — มี `@RequireBackstagePermission` decorator ชัดเจน** ไม่มี fallback ที่อิง scope ที่นี่: แคตตาล็อกและ bundle ของมันเป็นของระดับแพลตฟอร์มทั้งชุด ไม่ผูกกับ cluster ใด จึงไม่มี scope ที่แคบกว่าให้ guard ถอยไปใช้

### 4.3 ด่านข้ามโมดูล ไม่ใช่คีย์ของโมดูลนี้เอง

**ยืนยันเรื่องนี้ก่อนจะเข้าใจว่าแท็บ Bundles ปิดครบในตัวเองด้านสิทธิ์** ตัวหารของแถบสัดส่วน Features ใน `GroupCatalogPanel` และตัวเลือก feature ทั้งชุดใน `LicenseFeatureGroupEdit` ต่างโหลดแคตตาล็อกผ่าน `subscriptionService.getFeatureCatalog()` ซึ่งเรียก `GET /api-system/backstage/license-features` — **ไม่ใช่** `/license-features/all` route เปล่านั้นถูกประกาศอยู่ใน controller คนละตัวเลย คือ `backstage_subscriptions/backstage_subscriptions.controller.ts:251-253` และต้องการ **`subscription.read`** — เป็นคีย์ของโมดูล [Licenses](/th/backstage/licenses) เอง ไม่ใช่ `license_feature.read` หรือ `license_feature_group.read`

ผลที่ตามมา: session ที่มี `license_feature_group.read` + `license_feature_group.manage` แต่**ไม่มี** `subscription.read` เปิด `/license-modules` และแสดงรายการ bundle ได้เต็มที่ เปิด `/license-modules/:id/edit` เพื่อแก้ชื่อ ลำดับ หรือสถานะ active ของ bundle ได้ด้วย — แต่แถบสัดส่วน Features บนรายการจะหายไปเงียบ ๆ (`catalogTotal` ค้างที่ `null` ไม่มีตัวหารให้วาดแถบ) และตัวเลือก feature บนหน้าแก้ไขจะล้มเหลวตรง ๆ (`catalog.failed === true` แสดงปุ่ม retry แทนตัวเลือก) — บล็อกสิ่งเดียวที่หน้านั้นมีไว้ทำ โดยที่ route เองไม่เคยปฏิเสธเลย นี่คือความสัมพันธ์ข้ามโมดูลจริงที่พิสูจน์แล้ว ไม่ใช่บั๊กของโมดูลใดโมดูลหนึ่ง: endpoint ที่ใช้ร่วมกันมีเหตุผลเพราะแคตตาล็อก "อะไรขายได้ตอนนี้" ชุดเดียวกันคือสิ่งที่ตัวเลือก feature ของ subscription ก็ต้องการเหมือนกัน การใช้ endpoint เดียวหลีกเลี่ยงการมีตรรกะ "กรอง `hide` ออก" สองชุดที่อาจไม่ตรงกันเอง

## 5. โมดูลที่เกี่ยวข้อง

- [Licenses](/th/backstage/licenses) — ผู้*บริโภค*ของ bundle ในโมดูลนี้: การ์ด "Purchased Groups" ของ subscription หนึ่งใบหยิบจาก bundle ที่จัดไว้ที่นี่ และตัวเลือกกลุ่มของมันเองพึ่งพา endpoint ข้ามโมดูลที่เอกสารไว้ใน §4.3
- [Backstage RBAC](/th/backstage/rbac) — เป็นเจ้าของ UI แคตตาล็อกสิทธิ์ (`/backstage/category-permissions`) ที่ `license_feature.*`/`license_feature_group.*` ปรากฏอยู่ข้าง ๆ ทุก resource อื่น โมดูลนี้เองไม่ได้นิยามหรือแก้ permission key
- [Feature Flags](/th/backstage/feature-flags) — คนละหน้าจอกันเลย (`feature_flag.manage`) ที่คอมเมนต์ในซอร์สของโมดูลนี้เตือนไว้ตรง ๆ ว่าอย่าเอาไปปนกับค่า `state` ที่เอกสารไว้ใน §3.3

## 6. แหล่งข้อมูลอ้างอิง

path ทั้งหมดด้านล่างคือ `../carmen-backstage` (Backstage admin SPA, HEAD `8405788f`, 2026-10-27) ยกเว้นที่ขึ้นต้นด้วย `../carmen-turborepo-backend` (backend monorepo, HEAD `c9d788829`, 2026-10-27)

- `../carmen-backstage/src/App.tsx` (บรรทัด 319–350) — ทั้งสี่ route ของโมดูลนี้
- `../carmen-backstage/src/components/nav/backstageNav.ts` (บรรทัด 25–26) — สองรายการ sidebar
- `../carmen-backstage/src/pages/LicenseCatalog.tsx` — shell ที่ใช้ร่วมกัน, การกั้นแท็บ, และสามพฤติกรรมใน §3.1
- `../carmen-backstage/src/pages/licenseCatalog/FeatureCatalogPanel.tsx`, `src/pages/licenseFeatures/{CatalogStateBar,ModuleShelf}.tsx` — แท็บ Features
- `../carmen-backstage/src/pages/licenseCatalog/GroupCatalogPanel.tsx` — แท็บ Bundles
- `../carmen-backstage/src/pages/LicenseFeatureGroupEdit.tsx`, `src/pages/licenses/subscriptionEdit/FeatureSelectionCard.tsx`, `src/pages/licenses/GroupCompositionPanel.tsx`, `src/pages/licenses/FeatureCompositionBar.tsx` — ตัวแก้ไข bundle และส่วนประกอบร่วม
- `../carmen-backstage/src/services/licenseFeatureService.ts`, `src/services/licenseFeatureGroupService.ts`, `src/services/subscriptionService.ts` (`getFeatureCatalog`, §4.3) — REST client
- `../carmen-backstage/src/utils/featureTree.ts`, `src/pages/licenses/subscriptionEdit/featureSelection.ts` — ตัวช่วยเดินต้นไม้ (§3.2, §3.4)
- `../carmen-backstage/docs/superpowers/specs/2026-09-03-license-feature-tree-design.md` — บันทึกการออกแบบการปรับโครงแคตตาล็อกเป็น n ชั้น (§3.2)
- `../carmen-turborepo-backend/scripts/generate-license-catalog/run.ts` — ผู้เขียนแถว `tb_license_feature` เพียงรายเดียว
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/seed.license-feature.data.ts` — ผลลัพธ์ของ generator เอง ที่มาของจำนวน 112/13/105/7 ที่ยืนยันแล้วใน §3.2
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/permission.route-map.ts:472` — `LICENSE_ONLY_RESOURCES` ชุดต้นทางของคีย์ `interface.*`, `ai.*` และ `configuration.*` สองตัว (§3.2); `prisma/migrations/20260910000000_license_feature_group_kind/migration.sql` — คอลัมน์ `kind` ของกลุ่มและ backfill ของมัน (§3.4)
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma` — `tb_license_feature` (บรรทัด 1540), `tb_license_feature_group` (บรรทัด 1610), `tb_license_feature_group_item` (บรรทัด 1644), `enum_license_feature_state` (บรรทัด 956), `enum_license_feature_group_kind` (บรรทัด 962)
- `../carmen-turborepo-backend/apps/micro-business/src/license-feature/license-feature.service.ts`, `apps/micro-business/src/license-feature-group/license-feature-group.service.ts` — ตรรกะธุรกิจชั้น RPC (`affected_bu_count`, กฎ "ลูกลากพ่อ", การป้องกันลบ bundle ที่ยังใช้งานอยู่)
- `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/{backstage_license_features,backstage_license_feature_groups,backstage_subscriptions}/*.controller.ts` — การบังคับใช้สิทธิ์ (§4)

## 7. หน้าในโมดูลนี้

- [Data Model](/th/backstage/license-catalog/data-model) — `tb_license_feature`, `tb_license_feature_group`, `tb_license_feature_group_item`; โครงต้นไม้ n ชั้นและความเสี่ยงของการ hide ชั้นกลาง; จำนวนแคตตาล็อกที่ยืนยันแล้ว
- [UI Screens](/th/backstage/license-catalog/ui-screens) — กลไกแท็บของ shell `LicenseCatalog` แบบละเอียด, `FeatureCatalogPanel`, `GroupCatalogPanel`, `LicenseFeatureGroupEdit`, และส่วนประกอบตัวเลือก feature/แถบสัดส่วนที่ใช้ร่วมกัน
