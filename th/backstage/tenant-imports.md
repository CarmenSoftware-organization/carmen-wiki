---
title: การนำเข้าเทแนนต์ (Tenant Imports)
description: TenantImportWizard ที่ /tenant-imports — sidebar ใช้ป้าย "Data Import" gate ด้วย data_import.manage — นำข้อมูลหลักจาก Preconfig.xlsx เข้าฐานข้อมูล tenant ทีละขั้นตอน
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, tenant-imports
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# การนำเข้าเทแนนต์ (Tenant Imports)

> **At a Glance**
> **Component:** `TenantImportWizard` ที่ `/tenant-imports` เพิ่มโดย `../carmen-backstage` commit `80d6872` (2026-08-03) &nbsp;·&nbsp; **สามชื่อ หนึ่งหน้า:** รายการ sidebar เขียนว่า **"Data Import"** (`labelKey: 'nav.dataImport'`, `backstageNav.ts:19`), route คือ `/tenant-imports`, ส่วนหัวข้อ `PageHeader` ของหน้าเองเขียนว่า **"Tenant Data Import"** (`pages.tenantImport.title`, `src/i18n/en.ts:3589`) — ไม่ว่าจะค้นด้วยชื่อไหนในสามชื่อนี้ก็ควรเจอหน้านี้ &nbsp;·&nbsp; **Nav gate:** `permission: 'data_import.manage'` — เป็นคีย์ **`manage`** ไม่ใช่ `.read` เหมือนทุกแถวอื่นในกลุ่ม Organization (Clusters, Business Units, Tenant Migrations, Tenant Seed Data และ Users ล้วน gate ด้วยคีย์ `.read`) ผู้ดูแลที่มีแค่สิทธิ์อ่านในโมดูลอื่นของหนังสือเล่มนี้จะไม่เห็นรายการเมนูนี้เลย &nbsp;·&nbsp; **Backend gate:** คีย์ `data_import.manage` เดียวกัน ถูกตรวจแยกอิสระที่ทุก endpoint ทั้งสี่ของตัวนำเข้าผ่าน `@RequireBackstagePermission` (`preconfig-imports.controller.ts:129,148,175,209`) — เป็นการตรวจ RBAC จริงบน server ไม่ใช่แค่ซ่อนแถวเมนู &nbsp;·&nbsp; **Feature flag:** `tenant_imports`, `groupKey: 'navGroup.organization'` วาดเป็น sub-row ใต้ Business Units (`parentPath: '/business-units'`) ไม่ใช่ `superAdminOnly` &nbsp;·&nbsp; **ขอบเขต:** หนึ่ง business unit ต่อการรัน wizard หนึ่งครั้ง &nbsp;·&nbsp; **e2e suite:** ไม่มี — `../carmen-backstage-e2e/tests/` ไม่มีโฟลเดอร์ `tenant-imports` (หรือ `preconfig-import`) ทุกข้อความในหน้านี้มาจากการอ่าน source ของ `../carmen-backstage` และ `../carmen-turborepo-backend` โดยตรง &nbsp;·&nbsp; **หน้าย่อย:** 1

![การนำเข้าเทแนนต์ (Tenant Imports) screen](/screenshots/platform/tenant-imports/index.png)

## 1. ภาพรวม

Tenant Imports เป็น wizard หน้าจอเดียว คือ `TenantImportWizard` (`../carmen-backstage/src/pages/TenantImportWizard.tsx`) ที่นำไฟล์คงที่ชื่อ "Preconfig.xlsx" ซึ่งเป็นข้อมูลหลักตั้งต้น เข้าสู่ฐานข้อมูล tenant ของ business unit **เดียว**: สกุลเงิน หน่วยนับ โปรไฟล์ภาษี จุดส่งของ แผนก สถานที่จัดเก็บ โครงสร้างหมวดหมู่สินค้าสามระดับ (category → subcategory → item group) สินค้า (พร้อมการแปลงหน่วย) ผู้ขาย (พร้อมผู้ติดต่อและที่อยู่หนึ่งชุด) และฟิลด์โปรไฟล์โรงแรม/บริษัทของ business unit เอง มีไว้เพื่อให้การ onboard business unit ใหม่ไม่ต้องให้ operator กรอกแต่ละแถวเองทีละหน้าจอ CRUD — ชุดข้อมูลทั้งหมดเตรียมไว้ครั้งเดียวในสเปรดชีต แล้วเดินผ่านเป็นลำดับ preview-แล้ว-import ทีละขั้นตอน

การเข้าถึงหน้านี้ต้องมี `data_import.manage` — ไม่ใช่คีย์ `cluster.read` ที่ gate แถวข้างเคียงอย่าง [Clusters](/th/backstage/clusters) และ [Business Units](/th/backstage/business-units) และไม่ใช่คีย์ `tenant_migration.read` ที่อยู่เบื้องหลัง [Tenant Migrations](/th/backstage/tenant-migrations) ในกลุ่ม sidebar Organization เดียวกัน นี่คือแถวเดียวในกลุ่มนั้นที่ operator อาจถูกปฏิเสธได้อิสระจากการที่เขาดู cluster/business unit ได้ตามปกติหรือไม่ — และเพราะคีย์เป็น `.manage` ไม่ใช่ `.read` จึงไม่มีระดับ "เห็นว่ามีอยู่แต่รันไม่ได้" เลย: การถือคีย์นี้แปลว่าใช้ได้ทุกขั้นตอนของทุกการนำเข้า รวมถึงตัวเลือกทำลายข้อมูล `clear_existing` ด้วย (§3.3)

Wizard เป็นลำดับสี่หน้าจอที่เดินหน้าทางเดียว — เลือก business unit, อัปโหลดไฟล์, ทบทวนผลตรวจไฟล์ทีละขั้นตอน, แล้วทำงานทีละขั้นตอนที่พร้อม — อธิบายทีละหน้าจอ พร้อมสิ่งที่แต่ละขั้นตอนตรวจสอบและสิ่งที่เกิดขึ้นเมื่อล้มเหลว ไว้ที่ [UI Screens](/th/backstage/tenant-imports/ui-screens) หน้านี้ครอบคลุมกลไกที่ตัดผ่านทั้ง wizard: แคตตาล็อกขั้นตอน โมเดลตรวจสอบสามชั้น (check → preview → import) สิ่งที่ถูกบังคับแค่ในเบราว์เซอร์เทียบกับสิ่งที่ server บังคับเอง กลไกแบตช์/audit ของการ import แบบ stream และช่องโหว่ที่ยังมีอยู่จริงในวิธีหนึ่งใน endpoint ทั้งสี่รายงานความล้มเหลว

## 2. บริบททางธุรกิจ

แคตตาล็อกสิบสองขั้นตอน (§3.1) ถูกประกาศไว้ครั้งเดียวทั้งหมดที่ backend (`PRECONFIG_STEPS` ใน `../carmen-turborepo-backend/apps/micro-business/src/preconfig-import/preconfig-catalog.ts`) — ชีตไหนแมปกับตารางไหน คอลัมน์ไหนจำเป็น ค่าไหนถูกกฎหมาย คอลัมน์ไหน resolve คีย์นอก และแถวลูกไหนถูกสร้างเพิ่ม frontend ไม่เคยเห็นมากกว่าที่แคตตาล็อกฉาย client-facing ออกมา (`GET /steps`, `toStepMetadata()`) และไม่มีทางสั่งให้การนำเข้าไปเขียนตารางหรือคอลัมน์ที่ตัวเองเลือกเองได้ การแยกส่วนนี้เองที่ทำให้ wizard ปลอดภัยพอจะเปิดไว้หลังคีย์หยาบเพียงคีย์เดียวคือ `data_import.manage` — สิ่งเลวร้ายที่สุดที่ session ซึ่งถือคีย์นี้ทำได้คือรันขั้นตอนคงที่ที่แคตตาล็อกกำหนดไว้ กับ business unit เดียวที่เลือกไว้เท่านั้น

สิบเอ็ดในสิบสองขั้นตอนเขียนเข้าฐานข้อมูล **tenant** ที่เลือกผ่านตัวเลือก business unit ของ wizard ขั้นตอนที่สิบสอง Company Profile ต่างออกไปโดยธรรมชาติ: มันแก้ไขแถว `tb_business_unit` ของฐานข้อมูล **Backstage** (admin) สำหรับ business unit นั้น และทำโดยเรียก `businessUnitService.update()` ตัวเดียวกับที่หน้าแก้ไข [Business Units](/th/backstage/business-units) ปกติใช้ — ไม่ได้ผ่านสาย streaming ของตัวนำเข้าเลย (§3.5)

## 3. แนวคิดสำคัญ

### 3.1 แคตตาล็อกสิบสองขั้นตอน

แต่ละขั้นตอนคือหนึ่งชีต Excel ที่แมปกับหนึ่งตารางฐานข้อมูล (หรือสำหรับ Company Profile คือเรกคอร์ด business unit) `duplicate_key` คือคีย์ธรรมชาติแบบผสมที่แถวหนึ่งจะถูกเทียบเพื่อจัดการ skip/upsert/error (§3.3); `default_duplicate_mode` คือค่าที่ client ได้เมื่อละเว้น `options.duplicate_mode`

| Step id | Sheet | Table | Target | Duplicate key | Default mode | ล้างได้? | Lookup / แถวลูกที่น่าสังเกต |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `company-profile` | Company Profile (แนวตั้ง) | `tb_business_unit` | **backstage** | `code` (เทียบอย่างเดียว ไม่เขียน) | upsert | ไม่ | คอลัมน์เสมือน `default_currency_code` แปลงที่ client (§3.5) |
| `currency` | Currency | `tb_currency` | tenant | `code` | skip | ได้ | — |
| `unit` | Unit | `tb_unit` | tenant | `name` | skip | ได้ | — |
| `tax-profile` | Tax Profile | `tb_tax_profile` | tenant | `name` | skip | ได้ | — |
| `delivery-point` | Delivery Point | `tb_delivery_point` | tenant | `name` | skip | ได้ | — |
| `department` | Department | `tb_department` | tenant | `code` | skip | ได้ | — |
| `location` | Store Location | `tb_location` | tenant | `code` | skip | ได้ | Lookup (สร้างอัตโนมัติได้) `tb_delivery_point.name` |
| `product-category` | Item Group | `tb_product_category` | tenant | `code` | skip | ได้ | อ่านชีต "Item Group" เดียวกับอีกสองขั้นตอนถัดไป |
| `product-subcategory` | Item Group | `tb_product_sub_category` | tenant | `code, name` | skip | ได้ | Lookup `tb_product_category.code` (จำเป็น) |
| `item-group` | Item Group | `tb_product_item_group` | tenant | `code, name, product_subcategory_id` | skip | ได้ | Lookup `tb_product_sub_category.code` (จำเป็น) |
| `product` | Product list | `tb_product` | tenant | `code` | skip | ได้ | Lookup/สร้าง `tb_unit`; lookup `tb_product_item_group`, `tb_tax_profile`; เขียนแถวลูก `tb_unit_conversion` ได้สูงสุดสองแถว (order unit, recipe unit) |
| `vendor` | Vendor | `tb_vendor` | tenant | `code` | skip | ได้ | Lookup `tb_tax_profile.name`; เขียนแถวลูก `tb_vendor_contact` หนึ่งแถวและ `tb_vendor_address` หนึ่งแถว |

`product-category`, `product-subcategory` และ `item-group` ตั้งใจอ่านชีต "Item Group" **เดียวกัน** ถึงสามครั้งเข้าสามตาราง ตามลำดับการพึ่งพา — ไม่ใช่ bug ที่ซ้ำกัน (คอมเมนต์ในแคตตาล็อก, `preconfig-catalog.ts:212-214`) หัวคอลัมน์ของชีต Vendor เป็นตัวพิมพ์เล็ก/snake_case (`code`, `name`, `active`, `payee`, …) ต่างจากชีตอื่นทั้งหมดในไฟล์เดียวกันที่ใช้ Title Case (`preconfig-catalog.ts:442-444`) การจับคู่หัวคอลัมน์ไม่สนช่องว่าง/ตัวพิมพ์อยู่แล้วไม่ว่ากรณีใด (`normalizeKey()`, `preconfig-workbook.ts`)

### 3.2 สามชั้น: Check, Preview, Import — และแต่ละชั้นแตะอะไรบ้าง

Wizard รันไฟล์ผ่านการเรียก backend สามแบบที่ต่างกัน เรียงลำดับ แต่ละอันทำมากกว่าอันก่อนหน้าอย่างเคร่งครัด:

1. **`POST /:bu_id/check`** (`preconfigImportService.check()`) แปลงไฟล์และรายงานทีละขั้นตอนว่าชีตของมันมีอยู่หรือไม่ และคอลัมน์จำเป็น/ไม่บังคับใดขาดไป — **ไม่มีการอ่านอะไรเกี่ยวกับ business unit ที่เลือกเลย** พารามิเตอร์ path `:bu_id` ถูกตรวจรูปแบบเป็น UUID แต่ตั้งใจไม่ถูกส่งต่อไปยัง service call เลย (`preconfig-imports.controller.ts:138-142`, คอมเมนต์) — มีไว้แค่ให้ frontend ใช้รูปแบบ URL เดียวกันกับ endpoint ทั้งสี่ ขั้นตอนหนึ่งรายงานเป็น `sheet_missing`, `columns_missing`, หรือ `ready` (`buildCheckReport()`, `preconfig-workbook.ts`) มีเฉพาะขั้นตอนที่ `ready` เท่านั้นที่ไปถึง step rail ของ wizard
2. **`POST /:bu_id/:step_id/preview`** เปิดการเชื่อมต่อ tenant (ยกเว้น Company Profile, §3.5) แล้ว dry-run หนึ่งขั้นตอน: ทุกแถวถูกแปลงค่า ตรวจสอบ และจัดกลุ่มเป็น `new` / `duplicate` / `error` เทียบกับเนื้อหาปัจจุบันของตาราง — **ไม่มีการเขียนใด ๆ**
3. **`POST /:bu_id/:step_id/import/stream`** ทำการจัดกลุ่มแบบเดียวกับ preview ซ้ำ และเขียนจริง สตรีมความคืบหน้าเป็น NDJSON (§3.4)

ขั้นตอนที่ผ่าน Check แปลว่าชีตและคอลัมน์จำเป็นมีอยู่เท่านั้น — ไม่ได้บอกอะไรว่าค่าของแต่ละเซลล์จะตรวจผ่านหรือไม่ กฎการแปลงค่าต่อคอลัมน์ (`coerceValue()`, `preconfig-workbook.ts`): คอลัมน์ `required` ที่เซลล์ว่างทำให้แถวล้มเหลว; ค่าที่เกิน `maxLength` ทำให้แถวล้มเหลว; คอลัมน์ที่มี `allowedValues` เทียบแบบไม่สนตัวพิมพ์และปรับให้เป็นตัวสะกดของแคตตาล็อกเอง (`Average` ในไฟล์กลายเป็น enum member `average`); เซลล์ `number`/`decimal` ที่แปลงไม่ได้ทำให้แถวล้มเหลว; เซลล์ `boolean` รับ `true/1/yes/y/active` หรือ `false/0/no/n/inactive` (ไม่สนตัวพิมพ์) เท่านั้น

### 3.3 สิ่งที่เบราว์เซอร์บังคับ กับสิ่งที่ server บังคับเองอิสระ

ตัวเลือกสองตัวมีการรับประกันต่างกันมาก และผู้ทดสอบที่จะจำลองความล้มเหลวต้องรู้ว่าอันไหนเป็นอันไหน:

- **`clear_existing`** (soft-delete ทุกแถวปัจจุบันของตารางขั้นตอน รวมถึงแถวลูก ก่อนนำเข้า) ถูกกั้นไว้**เฉพาะในเบราว์เซอร์**: checkbox เองถูก `disabled` จนกว่าจะมี preview อย่างน้อยหนึ่งครั้งสำหรับขั้นตอนนั้น (`!preview && !clearExisting`, `StepPanel.tsx`) และการติ๊กจะเปิดกล่องโต้ตอบที่ต้องพิมพ์รหัส business unit ให้ตรงเป๊ะก่อนปุ่ม "Confirm" จะเปิดใช้ (`Dialog` ของ clear-existing ใน `StepPanel.tsx`) ทั้งสองเงื่อนไขไม่มีอยู่ที่ server เลย: `POST /import/stream` รับ `options.clear_existing: true` ได้ตั้งแต่การเรียกครั้งแรกของขั้นตอน โดยไม่ต้อง preview และไม่ต้องพิมพ์ยืนยัน — ลำดับของเบราว์เซอร์เป็นมาตรการความปลอดภัยของ UI ไม่ใช่สิ่งที่ API พึ่งพาหรือตรวจสอบ
- **`accept_lookup_creation`** (อนุญาตให้สร้างแถวอ้างอิงที่ขาดโดยอัตโนมัติ เช่น จุดส่งของใหม่ที่ระบุไว้ในชีต Store Location) ถูกบังคับโดย server จริง ๆ อิสระจาก client: `validateRowLookups()` (`preconfig-import.service.ts:259-309`) ปฏิเสธค่า lookup ที่ขาดและสร้างได้**ต่อแถว**ด้วยข้อความ `Unaccepted new lookup value: "<value>"` ทุกครั้งที่ตัวเลือกนี้ไม่ถูกตั้งในคำขอนั้น ๆ — ไม่ว่า client จะเคย preview แล้วเห็นรายการที่รอสร้างหรือไม่ก็ตาม แถวที่ตรวจไม่ผ่านนี้ทำให้แถวนั้นล้มเหลวเท่านั้น ไม่ใช่ทั้งการรัน

`clear_will_soft_delete`/`clear_will_soft_delete_related` (ตัวเลขที่กล่องยืนยันแสดง) ถูกคำนวณโดย `preview` เสมอ ไม่ว่าจะขอ `clear_existing` หรือไม่ (คอมเมนต์ของ `PreviewResult`, `preconfig-types.ts`) — กล่องยืนยันแสดงตัวเลขจริงได้ก็เพราะ preview รู้ตัวเลขนี้อยู่แล้วก่อนที่ operator จะเลือกยอมรับ

`parseOptions()` ของ gateway (`preconfig-imports.controller.ts:42,70-112`) ตรวจ `duplicate_mode` เทียบกับสตริงที่ถูกกฎหมายสามค่า และ `clear_existing`/`accept_lookup_creation` เทียบกับ `boolean` โดยปฏิเสธชนิดผิดด้วย 400 — แต่คอมเมนต์ของฟังก์ชันเอง ("anything else … is a 400") กล่าวเกินจริงกว่าที่โค้ดทำจริง: **คีย์พิเศษที่ไม่รู้จัก**ใน JSON ของ `options` ที่ส่งมาจะถูกทิ้งอย่างเงียบ ๆ ไม่ใช่ถูกปฏิเสธ ควรอ่านฟังก์ชัน ไม่ใช่คอมเมนต์ หากจะทดสอบ payload ที่ผิดรูปแบบ

### 3.4 การนำเข้าแบบ stream: การแบตช์ การ retry บางส่วน และแถว audit ที่เขียนเสมอ

`import/stream` เขียนแถวเป็นแบตช์ละ 200 แถวในหนึ่งทรานแซกชัน Prisma ต่อแบตช์ (`IMPORT_BATCH_SIZE`, `preconfig-import.service.ts`) ถ้าทรานแซกชันทั้งแบตช์ล้มเหลว — ส่วนใหญ่มาจากหนึ่งแถวที่ละเมิด constraint ที่ duplicate key ของแคตตาล็อกเองจับไม่ได้ — ตัวนำเข้าจะไม่ทำให้อีกราว 199 แถวที่เหลือล้มเหลวไปด้วย: มันจะย้อนตัวนับในหน่วยความจำกลับไปที่ snapshot ก่อนแบตช์ แล้ว **เล่นแบตช์ซ้ำทีละแถว แต่ละแถวในทรานแซกชันของตัวเอง** เพื่อให้เฉพาะแถวที่เสียจริงเท่านั้นที่จบด้วยสถานะ `failed` (`preconfig-import.service.ts:993-1010`, คอมเมนต์: "this intentionally makes a failed batch non-atomic") `summary.errors` เก็บได้สูงสุด 100 รายการ; `summary.failed` ยังนับทุกความล้มเหลว และ `errors_truncated: true` จะถูกบันทึกเมื่อถึงเพดานนั้น (`MAX_SUMMARY_ERRORS`)

การ soft-delete ของ `clear_existing` รันรวมอยู่ในทรานแซกชันของแบตช์แรกเมื่อมีแบตช์ให้รวม หรือรันแยกผ่าน `ensureCleared()` สำหรับชีตที่ไม่มีแถวเลยหรือหลังแบตช์แรก rollback (`preconfig-import.service.ts:910-923`)

**การยกเลิกไม่ย้อนแบตช์ที่คอมมิตไปแล้ว** การปิดสตรีมของ wizard (สลับ business unit, อัปโหลดไฟล์ใหม่, หรือออกจากหน้า) ตั้งแฟล็ก `cancelled` ที่ลูปการรันตรวจสอบเฉพาะ*ระหว่าง*แบตช์ และระหว่างการ retry ทีละแถว (`preconfig-import.service.ts:917-920, 991-995`) — ทรานแซกชันแบตช์ที่กำลังทำอยู่ตอนที่การยกเลิกมาถึงจะรันจนจบและคอมมิตตามปกติ มีเพียงแบตช์ที่ยังไม่เริ่มเท่านั้นที่ถูกข้าม guard `useUnsavedChanges(runInProgress)` ของ frontend เอง (`TenantImportWizard.tsx`) เตือนเฉพาะตอนปิดหรือรีเฟรช**แท็บเบราว์เซอร์**เท่านั้น (listener `beforeunload`) — ไม่ได้กั้นหรือเตือนตอนนำทางไปหน้าอื่นภายใน SPA ขณะที่การนำเข้ากำลังทำงานอยู่

ทุกการรัน — เสร็จสมบูรณ์ ถูกยกเลิก หรือล้มเหลว — เขียนแถว `tb_activity` หนึ่งแถวบนฐานข้อมูล **tenant** เสมอ (`writeActivity()`, `preconfig-import.service.ts:1051-1058,1085-1120`): `action: 'import'`, `entity_type: 'preconfig_import'`, พร้อม `meta_data` ที่บรรจุ `step_id`, `file_name`, `options`, `summary` เต็ม, `outcome`, และ `errors_truncated` เมื่อเข้าเงื่อนไข การเขียนนี้เองก็เป็น best-effort — ความล้มเหลวในการเขียนแถว audit จะถูก log และกลืนไว้ ไม่เคยแสดงเป็นความล้มเหลวของการนำเข้า (`preconfig-import.service.ts:1113-1119`) สำหรับผู้ทดสอบ แถวนี้คือบันทึกฝั่ง server ที่คงอยู่จริงเพียงแหล่งเดียวว่าการรันนั้นทำอะไรไปจริง ๆ ไม่ว่าจะมีใครดูสตรีม NDJSON อยู่ตอนนั้นหรือไม่

### 3.5 Company Profile: ขั้นตอนเดียวที่อยู่นอกตัวนำเข้า และรอยต่อสิทธิ์ที่ควรรู้

ชีตของ Company Profile เป็นแนวตั้ง (ป้ายกำกับอยู่คอลัมน์ A ค่าอยู่คอลัมน์ B — `isVerticalSheet()`, `preconfig-workbook.ts`) ไม่ใช่ตารางแบบมีหัวคอลัมน์ และ `target` ของมันคือ `backstage` (เปลี่ยนชื่อจาก `platform` ใน Backstage rename เมื่อ 2026-10-26) ไม่ใช่ `tenant` `import/stream` ปฏิเสธมันทันทีก่อนเปิดการเชื่อมต่อใด ๆ (`step.target !== 'tenant'` → การรัน error ทันที, `preconfig-import.service.ts:703-710`) มันจะถูก preview เท่านั้น ผ่าน endpoint `preview()` เดียวกัน ซึ่งสำหรับขั้นตอนเป้าหมาย backstage จะรัน**ก่อน**ที่การเชื่อมต่อ tenant ใด ๆ จะถูก resolve (`previewVerticalStep()`, `preconfig-import.service.ts:470-476`) — ดังนั้น business unit ที่ยังไม่มีฐานข้อมูล tenant เลยก็ยัง diff ได้

`CompanyProfilePanel` (`../carmen-backstage/src/pages/tenantImport/CompanyProfilePanel.tsx`) แสดงผล diff และ apply ตรงผ่าน `businessUnitService.update()` — เรียก `PUT /api-system/business-units/:id` ตัวเดียวกับที่ปุ่ม Save ของหน้าแก้ไข [Business Units](/th/backstage/business-units) ปกติใช้ พร้อม `doc_version` optimistic locking (`409` จะโหลดเรกคอร์ดใหม่และ diff ซ้ำแทนการเขียนทับ) "BU Code" แสดงแบบอ่านอย่างเดียวพร้อมแบนเนอร์เตือนเมื่อรหัสในชีตไม่ตรงกับ BU ที่เลือก และไม่ถูกส่งไปใน payload การอัปเดตเลย; "BU Name" ถูกระบุว่า "Not applied" ด้วยเหตุผลเรื่องข้อมูลระบุตัวตนเดียวกัน

**การเขียนนี้ไม่ได้ถูก gate ด้วย `cluster.update` ซึ่งเป็นคีย์ที่ route ของหน้าแก้ไขปกติเองต้องการ** `PUT /api-system/business-units/:business_unit_id` ถูกป้องกันด้วย `AppIdGuard('businessUnit.update')` เท่านั้น (`backstage_business-units.controller.ts:402-403`) — เป็นการ**ตรวจ allowlist ตัวตนของแอปพลิเคชัน**ผ่าน header `x-app-id` (`app-id.guard.ts`) ไม่ใช่การตรวจ permission RBAC ระดับแพลตฟอร์มของผู้ใช้ที่เรียก guard ระดับคลาสของ endpoint นี้คือ `KeycloakGuard` เท่านั้น (ตรวจแค่การยืนยันตัวตน) ไม่มี `BackstagePermissionGuard`/`@RequireBackstagePermission` อยู่บน route นี้เลย

หลักฐานรูปแบบที่หนักแน่นที่สุดอยู่**ใน controller เดียวกัน**: route `POST` (create) และ `DELETE` (delete) บนคลาสเดียวกันนี้เอง ทั้งคู่ซ้อน `AppIdGuard` **และ** `BackstagePermissionGuard` + `@RequireBackstagePermission('cluster.create')` / `('cluster.delete')` (`backstage_business-units.controller.ts:293-294`, `:678-679`) — เป็นแพตเทิร์นที่ route เขียนได้อื่นทุกตัวในหนังสือเล่มนี้ทำตาม `PUT` (update) เป็นตัวเดียวในสามที่ตัด `BackstagePermissionGuard`/`@RequireBackstagePermission` ออก เหลือแค่ `AppIdGuard` นี่ไม่ใช่การเทียบข้ามไฟล์ที่ไม่เกี่ยวข้องกันซึ่งอาจอธิบายได้ด้วยธรรมเนียมที่ต่างกัน — แต่เป็นคลาสเดียวที่ route ข้างเคียงสองตัวรู้วิธีเพิ่มการตรวจนี้ ในขณะที่ตัวที่สามไม่ทำ

และนี่คือการเขียนของ user session จริง ๆ ไม่ใช่การเรียกระหว่างเซอร์วิสที่ `AppIdGuard` เพียงตัวเดียวจะเป็น gate ที่สมเหตุสมผล: client `api` ที่ใช้ร่วมกันส่งทั้ง bearer token ของผู้ใช้เอง (`Authorization: Bearer ${token}` จาก `localStorage` แนบทุกคำขอโดย request interceptor) และค่า `x-app-id` เดียวที่กำหนดตอน build (`import.meta.env.REACT_APP_API_APP_ID` ค่าเดียวกันสำหรับทุกผู้ใช้ของ SPA build ที่ deploy ไว้) ในทุกคำขอ (`../carmen-backstage/src/services/api.ts:10,26`) — ดังนั้นการที่ `AppIdGuard` ผ่านบอก backend ได้แค่ว่า "มี session ของ SPA build นี้กำลังเรียกอยู่" ไม่เคยบอกอะไรเลยว่าผู้ใช้คนนั้นถือ permission อะไรบ้าง

พูดให้เป็นรูปธรรม: session ที่ถือ `data_import.manage` แต่**ไม่มี** `cluster.update` จะถูก frontend กั้นไม่ให้เปิด `/business-units/:id/edit` ได้เลย แต่**ไม่ถูกกั้น**ทั้งที่ frontend (ไม่มี `<Can>` gate ครอบปุ่ม Apply ของ `CompanyProfilePanel`) และที่ backend จากการเขียนฟิลด์เดียวกันผ่านขั้นตอน Company Profile ของ wizard นี้ — คีย์ `cluster.update` ที่ดูเหมือนควรจะ gate การเขียนนี้ด้วย ไม่เคยถูกตรวจบนเส้นทางนี้เลย นี่คือช่องว่างของ endpoint `PUT` ที่ใช้ร่วมกันเอง ไม่ใช่สิ่งที่เกิดเฉพาะกับ wizard นี้ — ดู [Business Units](/th/backstage/business-units) §4 สำหรับ pointer ย้อนกลับจากตาราง permission ของโมดูลนั้นเอง

### 3.6 ช่องโหว่ที่ยังคงอยู่จริงในการแมป error status ของ `import/stream`

`preview`, `check` และ `steps` แมป error ของ backend เป็น HTTP status ผ่านสาย `Result` → `StdStatus` → `HttpStatus` ทั่วไป (`packages/nest-result/src/base-microservice-controller.ts:194-225`) ซึ่ง `ErrorCode.VALIDATION_FAILURE` กลายเป็น `422 Unprocessable Entity` เสมอ `import/stream` ใช้สายนี้ไม่ได้ — มันสตรีม `Observable` ไม่ใช่ `Result` — จึงเขียนการแมปก่อนเริ่มสตรีมเองต่างหาก คือ `resolvePreStreamErrorStatus()` (`preconfig-imports.controller.ts:115-122`):

```
if (/not found/i.test(message)) return HttpStatus.NOT_FOUND;
if (/no database connection configured|unsupported database provider/i.test(message)) return HttpStatus.UNPROCESSABLE_ENTITY;
if (/invalid bu_id format/i.test(message)) return HttpStatus.BAD_REQUEST;
return HttpStatus.INTERNAL_SERVER_ERROR;
```

regex ตัวกลางตรงกับถ้อยคำความล้มเหลวการเชื่อมต่อที่มีอยู่**ก่อน** commit `af2437074` (2026-08-13, ย้าย `resolveConnection` จาก `tb_business_unit.db_connection` ไปเป็น `db_schema` + `tb_database_pool`; ยืนยันจากการอ่าน diff ของมันบน `tenant.service.ts`) การ refactor นั้นเปลี่ยนข้อความที่ throw จริงเป็นสี่แบบใหม่ (`tenant.service.ts:450-470`, the private `resolveConnection`): `"Business unit {code} is not linked to a database pool"`, `"…has no database schema configured"`, `"Database pool '{name}' … has been deleted"`, `"…is inactive"` — **ไม่มีอันไหนตรงกับ regex เลย** `resolveConnection()` ของ `preconfig-import.service.ts` เอง (บรรทัด 129) เรียก `resolveConnectionForBusinessUnit()` เวอร์ชันหลัง refactor อยู่แล้ว (ยืนยันที่บรรทัด 156) และส่งต่อข้อความใดข้อความหนึ่งในสี่แบบที่ `tenant.service.ts` throw ตรงเข้า `subscriber.error()` (บรรทัด 711-714) เมื่อการรันยังไม่เริ่มสตรีม เนื่องจาก controller ของ gateway `preconfig-imports.controller.ts` ถูกเพิ่มเมื่อ 2026-08-03 — **ก่อน** การ refactor วันที่ 13 สิงหาคม — และไม่มี commit ใดหลังจากนั้นแตะ `resolvePreStreamErrorStatus()` เลย (ตรวจแล้ว: `cc0c3b4e6`, `b188a4d80`, `d9cc3ecde`, `2f134a614` ล้วนเป็นวันเดียวกันคือ 2026-08-03 ไม่มีตัวไหนแตะฟังก์ชันนี้) นี่คือช่องโหว่ที่**ยังมีอยู่จริงในปัจจุบัน** ไม่ใช่ของเก่าที่ถูกแก้ที่อื่นแล้ว: **business unit ที่ไม่ได้ผูก database pool ไม่มี schema หรือ pool ถูกลบ/ปิดใช้งาน จะได้ `500 Internal Server Error` จาก `import/stream` แทนที่จะเป็น `422` ที่ความล้มเหลวแบบเดียวกันเป๊ะให้ผลถูกต้องจาก `preview` กับ business unit เดียวกัน** `"Business unit not found"` (→ 404) และ `"Invalid bu_id format"` (→ 400 ในทางปฏิบัติแทบเป็นไปไม่ได้เพราะ `ParseUUIDPipe` ปฏิเสธ id ที่ผิดรูปแบบไปก่อนที่ service จะรันแล้ว) ไม่ได้รับผลกระทบ หน้า [Tenant Migrations](/th/backstage/tenant-migrations) ข้างเคียง (§4.4 ที่นั่น) บันทึกช่องโหว่ regex ค้างชนิดเดียวกันบน `/deploy/stream` ที่เกิดจากการ refactor วันที่ 13 สิงหาคมชุดเดียวกัน แต่กับฟังก์ชันแมปมือคนละตัว

## 4. บทบาทและสิทธิ์

| จุด | Permission | หมายเหตุ |
| --- | --- | --- |
| รายการ sidebar, route `/tenant-imports` | `data_import.manage` | `backstageNav.ts:19`; `App.tsx:287-294` — คีย์ `manage` ที่ไม่มีระดับ `.read` แยกต่างหาก (§1) |
| `GET /steps`, `POST /:bu_id/check`, `POST /:bu_id/:step_id/preview`, `POST /:bu_id/:step_id/import/stream` | `data_import.manage` | `@RequireBackstagePermission` ถูกตรวจแยกอิสระที่ backend บนทั้งสี่ route (`preconfig-imports.controller.ts:129,148,175,209`) — คีย์เดียวกันนี้ gate ทั้ง Check/Preview ที่แค่อ่าน และ Import stream ที่เขียนจริง ไม่มีคีย์ที่ละเอียดกว่านี้อยู่ที่ไหนในโมดูลนี้เลย |
| "Apply to BU" ของ Company Profile | **ไม่มี permission RBAC เลย** — `AppIdGuard('businessUnit.update')` เป็นการตรวจ allowlist ตัวตนแอป ไม่ใช่การตรวจ permission ของผู้ใช้ (§3.5) | ทั้ง frontend (`CompanyProfilePanel.tsx` ไม่มี `<Can>` gate ครอบปุ่ม Apply) และ backend (`backstage_business-units.controller.ts:402-403`, มีแค่ `KeycloakGuard` ระดับคลาส) ไม่ตรวจ `cluster.update` บนเส้นทางนี้เลย ทั้งที่นั่นคือคีย์ที่ route แก้ไข [Business Units](/th/backstage/business-units) ปกติต้องการเพื่อเข้าถึงการเขียนเดียวกัน |

## 5. โมดูลที่เกี่ยวข้อง

- [Business Units](/th/backstage/business-units) — เป็นเจ้าของ `tb_business_unit` และ endpoint `PUT /api-system/business-units/:id` ที่ Company Profile เขียนผ่าน (§3.5); หน้าแก้ไขปกติแท็บ Technical และตัวเลือก BU ของ wizard นี้ล้วนอ่าน `businessUnitService.getAll()`
- [Clusters](/th/backstage/clusters) — คีย์ `cluster.read`/`cluster.update` ที่ถูกอ้างเปรียบเทียบตลอด §1 และ §3.5; ไม่ได้ถูกใช้โดยโมดูลนี้เอง
- [Tenant Migrations](/th/backstage/tenant-migrations) — โมดูล Organization ข้างเคียงที่ endpoint `/deploy/stream` ระดับ fleet ของมันมี regex ความล้มเหลวการเชื่อมต่อค้างชนิดเดียวกัน (§4.4 ที่นั่น) เกิดจากการ refactor pool ฐานข้อมูล `af2437074` ชุดเดียวกัน
- [Backstage RBAC](/th/backstage/rbac) — แคตตาล็อก permission ระดับแพลตฟอร์มที่ทั้ง `data_import.manage` และ `cluster.update` อาศัยอยู่; โมดูลนี้ไม่ได้ประกาศคีย์ permission ของตัวเองเลยนอกจาก `data_import.manage`

## 6. แหล่งอ้างอิง

ทุก path เป็น `../carmen-backstage` (HEAD `157a65e`, 2026-09-04) ยกเว้นที่ระบุ `../carmen-turborepo-backend` (HEAD `937cf5ac4`, 2026-09-06) หรือ `../carmen-backstage-e2e` (HEAD `a8e3b31`, 2026-08-25 อ้างอิงเพื่อยืนยันว่าไม่มี suite เท่านั้น)

- `src/pages/TenantImportWizard.tsx` — เชลล์ของ wizard, state machine สี่หน้าจอ, generation token ป้องกันข้อมูลค้าง, และการต่อสาย BU switcher
- `src/pages/tenantImport/{WorkbookDropzone,FileCheckPanel,StepRail,StepPanel,CompanyProfilePanel}.tsx` — ทุกหน้าจอและ panel บันทึกไว้เต็มที่ [UI Screens](/th/backstage/tenant-imports/ui-screens)
- `src/services/preconfigImportService.ts` — การเรียก REST/stream ทั้งสี่ (`getSteps`, `check`, `preview`, `importStream`)
- `src/components/nav/backstageNav.ts:19`, `src/App.tsx:287-294` — รายการ nav และการลงทะเบียน route; commit `80d6872` (2026-08-03)
- `src/i18n/en.ts:3565-3669`, `src/i18n/th.ts:2436-2532` (namespace `tenantImport`) — ทุกข้อความที่อ้างในหน้านี้และ [UI Screens](/th/backstage/tenant-imports/ui-screens); `src/i18n/en.ts:23,96` / `th.ts:22,92` (ป้าย nav `dataImport`)
- `src/types/index.ts:437-515` — `PreconfigStepMeta`, `PreconfigCheckReport`, `PreconfigPreview`, `PreconfigImportOptions`, `PreconfigImportSummary`, `PreconfigImportEvent`
- `src/utils/docVersion.ts` — helper optimistic-lock ที่ปุ่ม Apply ของ Company Profile ใช้ซ้ำ
- `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/preconfig-imports/{preconfig-imports.controller,preconfig-imports.service}.ts` — gateway proxy, decorator permission ทั้งสี่, การตรวจไฟล์อัปโหลด (`assertXlsx`), การแปลง options (`parseOptions`), และ `resolvePreStreamErrorStatus()` ที่ค้าง (บรรทัด 42, 70-112, 115-122, 257)
- `../carmen-turborepo-backend/apps/micro-business/src/preconfig-import/{preconfig-import.service,preconfig-catalog,preconfig-workbook,preconfig-lookup,preconfig-related,preconfig-types}.ts` — ตัวนำเข้าเอง: การ resolve connection, แคตตาล็อกสิบสองขั้นตอน, การแปลงไฟล์/ค่า, การ resolve lookup และการย้อน creation ที่ staged ไว้, การสร้างแถวลูก, การแบตช์/retry, และการเขียน audit `tb_activity`
- `../carmen-turborepo-backend/apps/micro-business/src/tenant/tenant.service.ts:450-481` — `resolveConnection`/`resolveConnectionForBusinessUnit`, ข้อความความล้มเหลวสี่แบบที่อ้างใน §3.6
- `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/backstage_business-units/backstage_business-units.controller.ts:62-65,293-294,402-403,678-679` — guard ระดับคลาสของ controller Business Units, ด่านเฉพาะ `AppIdGuard` ของ route `PUT`, และคู่ `BackstagePermissionGuard` + `@RequireBackstagePermission` ของ route `POST`/`DELETE` ข้างเคียง (§3.5)
- `../carmen-turborepo-backend/apps/backend-gateway/src/common/guard/app-id.guard.ts` — สิ่งที่ `AppIdGuard` ตรวจจริง (allowlist `x-app-id` ไม่ใช่ permission ของผู้ใช้)
- `../carmen-backstage/src/services/api.ts:10,26` — header `x-app-id` เริ่มต้นที่กำหนดตอน build และ interceptor ที่แนบ bearer token ต่อคำขอของ client ที่ใช้ร่วมกัน อ้างใน §3.5 เพื่อยืนยันว่านี่คือการเขียนของ user session จริง
- `../carmen-turborepo-backend/packages/nest-result/src/base-microservice-controller.ts:194-225` — การแมป `ErrorCode` → `HttpStatus` ทั่วไปที่ `check`/`preview`/`steps` ใช้ เทียบกับของ `import/stream` ที่เขียนมือเอง
- Commit `af2437074` (`../carmen-turborepo-backend`, 2026-08-13) — การ refactor connection แบบ database-pool ที่อยู่เบื้องหลังข้อค้นพบใน §3.6
- `../carmen-backstage-e2e/tests/` — ยืนยันแล้วว่าไม่มี suite `tenant-imports`/`preconfig-import`

## 7. หน้าในโมดูลนี้

- [UI Screens](/th/backstage/tenant-imports/ui-screens) — เดินผ่านหน้าจอทั้งสี่ของ wizard ทีละขั้นตอน: แต่ละหน้าจอถามอะไร ตรวจอะไร เกิดอะไรขึ้นเมื่อล้มเหลว และย้อนกลับได้หรือไม่
