---
title: Company Profile & Default Setting
description: สองหน้าจอ system-admin ที่แก้ไขกลุ่มฟิลด์ที่แยกกันของแถว tb_business_unit เดียวกัน — Company Profile (identity, address, branding, date/time/number format) และ Default Setting (config การทำงาน PR/SI/PO + การเลือก print-form template) /system-admin/business-setting คือ redirect ที่ตายแล้วไปยัง Company Profile
published: true
date: 2026-07-29T10:30:00.000Z
tags: system-config, business-unit, company-profile, default-setting, carmen-software
editor: markdown
dateCreated: 2026-07-29T10:30:00.000Z
---

# Company Profile & Default Setting

> **สรุปโดยย่อ**
> **Routes:** `/system-admin/company-profile`, `/system-admin/default-setting` &nbsp;·&nbsp; **Redirect:** `/system-admin/business-setting` → `/system-admin/company-profile` (`<Navigate replace>` ฝั่ง client ไม่มีหน้าจอของตัวเอง) &nbsp;·&nbsp; **ตาราง:** `tb_business_unit` (platform schema) — แถวเดียวกับ [master-data/business-unit](/th/inventory/master-data/business-unit) แต่กลุ่มฟิลด์แยกกัน &nbsp;·&nbsp; **Endpoint:** `GET`/`PATCH /api/business-units` (ไม่มี id ใน URL — resolve ฝั่ง server จาก token/BU context ของผู้เรียก) &nbsp;·&nbsp; **Permission:** `system_configuration.view` (ทั้งสองหน้าจอ; ไม่มี key เฉพาะของตัวเอง)

## 1. คืออะไรและใครใช้

นี่คือสองหน้าจอแยกกันที่ทั้งคู่อ่านและแก้ไข **แถว `tb_business_unit` ของ business unit ปัจจุบันเอง** — ตารางเดียวกับที่ [master-data/business-unit](/th/inventory/master-data/business-unit) บันทึกไว้จากมุมของ platform admin console หน้านั้นครอบคลุมฟอร์ม edit ของ `carmen-platform` (identity, สกุลเงิน, costing method, module enablement, tenant DB connection) ส่วนสองหน้าจอนี้คือ**ฝั่ง tenant ภายในแอป** ที่ Sysadmin เข้าถึงได้จากใน Carmen Inventory เอง และแก้ไข subset ของฟิลด์ในแถวเดียวกันที่**ไม่ทับซ้อนกัน**:

- **Company Profile** (`/system-admin/company-profile`) — identity (ชื่อ, alias, description, info), ฟิลด์ costing/licensing แบบ read-only, สกุลเงิน default, ที่อยู่ hotel property, ที่อยู่ company legal, branding (logo/avatar, read-only), และค่า default ของ date/time/number-format
- **Default Setting** (`/system-admin/default-setting`) — array JSONB `config` ในแถวเดียวกัน: toggle การทำงานของ PR, SI, และ PO บวก selector ของ print-form template ต่อประเภทเอกสาร

หน้าจอทั้งสองใช้ pattern view/edit toggle เดียวกันเป๊ะ, hook `useBusinessUnit`/`useUpdateBusinessUnit` เดียวกันเป๊ะ, และ endpoint `PATCH /api/business-units` เดียวกันเป๊ะ — ต่างกันแค่ *ฟิลด์ไหน* ของ `BusinessSettingFormValues` ที่แต่ละหน้าจอ render และ diff module ที่ใช้ร่วมกันหนึ่งตัว (`company-profile-form-schema.ts`, `company-profile-config-registry.ts`, `company-profile-ui.tsx`) รองรับฟอร์มของทั้งสองหน้าจอ แม้ `default-setting-component.tsx` จะอยู่ใน route folder ของตัวเอง — ยืนยันจาก import โดยตรง (`../company-profile/company-profile-ui`, `../company-profile/company-profile-form-schema`)

**`/system-admin/business-setting` เป็น route ที่ตายแล้ว** — `router.tsx` ลงทะเบียนมันเป็น `{ path: "business-setting", element: <Navigate to="/system-admin/company-profile" replace /> }` เป็น redirect ฝั่ง client เปล่า ๆ ไม่มี component ของตัวเอง น่าจะเป็นร่องรอยจากการ rename: เอกสาร planning ก่อนหน้าในโปรเจกต์นี้ (`docs/superpowers/plans/2026-07-09-business-setting-*-config-section.md`, `docs/superpowers/specs/2026-07-10-default-setting-page-split-design.md`) อธิบายหน้า "Business Setting" เดียวที่ภายหลังถูกแยกเป็นสองหน้าจอนี้ โดยทิ้ง redirect ไว้สำหรับ link/bookmark เก่า

**ดูแลโดย** Sysadmin ในแอป **อ่านโดย** ทุก module ที่ใช้ฟิลด์ของ `BusinessUnitDetail` (costing engine อ่าน `calculation_method`; หน้าจอ PR/SI/PO อ่าน config item ที่ Default Setting แก้ — ดู §6)

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| แก้ identity, ที่อยู่, หรือค่า format default ของ business unit | Company Profile → **Edit** → แก้ฟิลด์ → **Save** | ส่งเฉพาะฟิลด์ที่เปลี่ยนเป็น `PATCH` (diff กับ snapshot ล่าสุดที่โหลด) |
| แก้ toggle การทำงานของ PR/SI/PO | Default Setting → **Edit** → เปลี่ยนค่า → **Save** | กลไก diff-and-`PATCH` เดียวกัน จำกัดเฉพาะ array `config` |
| เลือก print form สำหรับประเภทเอกสาร | Default Setting → section Print Forms → เลือก template ต่อประเภท | Dropdown มาจาก catalog report-template ของ [reporting-audit](/th/inventory/reporting-audit) กรองตาม `report_group` ของเอกสารนั้น; ดู §6 |
| ดู (ไม่แก้) costing method หรือ license cap | Company Profile → section General | `calculation_method` และ `max_license_users` render เป็น `SettingField` read-only — ไม่มี input ไม่ว่าจะอยู่โหมด edit หรือไม่ |
| ยกเลิกการแก้ไขที่ยังไม่บันทึก | **Cancel** ตอนกำลังแก้ | แสดง confirm dialog (`useDiscardConfirm`) เฉพาะเมื่อฟอร์ม dirty |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | ยืนยันแล้วหรือไม่ |
|---|---|---|
| Save ล้มเหลวด้วย error แบบ version-conflict | payload ของ `PATCH` แนบ `doc_version` จากการโหลดล่าสุดเสมอ (`{ ...patch, doc_version: data.doc_version }`) | **ยืนยันแล้ว** — ทั้งสองหน้าจอแนบ `doc_version` กับทุกการ save; การแก้พร้อมกันจากที่อื่นทำให้ `doc_version` ของการ save ครั้งที่สองล้าสมัย |
| Company email / hotel email ถูก reject | Zod refinement `optionalEmail` — ต้องเป็นอีเมลที่ถูกต้องหรือ `""` เท่านั้น | **ยืนยันแล้ว** จาก `company-profile-form-schema.ts` |
| `code` แก้ไม่ได้จากหน้าจอทั้งสอง | `code` เป็นฟิลด์ required ใน `BusinessSettingFormValues` และใน Zod schema แต่**ไม่มี input ใดใน `company-profile-component.tsx` ผูกกับมัน** | **ยืนยันแล้ว** — ฟิลด์นี้วิ่งผ่านกลไก `toFormValues`/`buildPatch` แต่ไม่เคยถูก render; ฟอร์มจึงคงค่าที่โหลดไว้เสมอ validation จึงผ่านโดยปริยาย และ `code` ไม่สามารถถูกแก้จากหน้าจอนี้ได้จริง |
| Dropdown print-form แสดง "⚠ Unknown template (…)" หรือ placeholder loading/unavailable | ค่า config ที่เก็บไว้ในสไตล์ notification อ้างอิง id ของ report template ที่ไม่อยู่ใน list template ของ [reporting-audit](/th/inventory/reporting-audit) ที่โหลดไว้สำหรับ `report_group` นั้นในตอนนี้ (template ถูกลบ, โหลดล้มเหลว, หรือกำลังโหลด) | **ยืนยันแล้ว** — `buildPrintFormOptions()` สร้าง option placeholder เสมอ เพื่อไม่ให้ค่าที่เก็บไว้หายไปจาก list เงียบ ๆ ตอน save |

## 4. กรณีพิเศษ

- **`config` ไม่มี schema ตายตัว และ frontend เป็นผู้ seed** `tb_business_unit.config` เป็นคอลัมน์ `Json?` เปล่า ๆ — ไม่มี schema ตายตัวสำหรับเนื้อหาของมัน หน้าจอ Default Setting แสดงเฉพาะ **4 section ที่รู้จัก** (`CONFIG_SECTIONS` ใน `company-profile-config-registry.ts`: PR, SI, PO, Print Forms — รวม 15 item, 12 อันในนั้นคือ print-form selector ต่อประเภทเอกสาร) entry ใด ๆ ใน `config` ที่ backend มีแต่ไม่อยู่ใน registry นี้จะ**ไม่ถูก render เลย**โดยทั้งสองหน้าจอ (ไม่มี UI "other settings" แบบ catch-all แม้โค้ดของ registry จะมี bucket type `other` ภายในไว้รองรับกรณีนี้ แต่ component ไม่เคย render มัน)
- **Config ของ print-form เป็นของ frontend-seed ไม่ใช่ backend-required** ถ้า array `config` ของ tenant ไม่มี entry สำหรับ print-form key ใดตัวหนึ่ง (เช่น `print_form.pr`) หน้าจอยังแสดงแถวนั้นอยู่ (ผ่าน `mergeSeededConfig` โดย default เป็น `""` = "Use the system default") — การเปิดและ save หน้านี้ครั้งแรกคือสิ่งที่เขียนค่า default ที่ seed ไว้จริงลงในแถว backend
- **`si.cost-from` มี option ที่มีเงื่อนไขจาก calculation-method** option `average` ใน dropdown "Default price for added items" ของ Stock-In จะแสดงเมื่อ `data.calculation_method === "average"` เท่านั้น (`visibleWhenCalcMethod`) — **ยกเว้น** ถ้าค่าที่เก็บไว้ของ BU เป็น `average` อยู่แล้วบน tenant ที่ใช้ method `fifo` ซึ่งกรณีนี้มันจะยังแสดงอยู่ เพื่อไม่ให้ค่าที่เก็บไว้หายไปเงียบ ๆ (`resolveConfigOptions()`)
- **Branding เป็น read-only ทั้งสองหน้าจอ** Logo/avatar render ผ่าน `<img>` ธรรมดา ไม่มีปุ่ม upload — flow upload จริงอยู่ที่อื่น (หน้า profile ของผู้ใช้เอง ตาม code comment ของ component เอง) ไม่ใช่ที่นี่
- **ฟิลด์ number-format มีโครงสร้าง ไม่ใช่ string ดิบ** `amount_format`/`quantity_format`/`perpage_format`/`recipe_format` แต่ละตัวเป็น `{ locales, minimumIntegerDigits }` — UI แสดงเป็น locale string สไตล์ `Intl` บวกจำนวนหลัก ไม่ใช่ pattern แบบ free-text เหมือนฟิลด์ `date_format`/`time_format` (ซึ่งเป็น string ที่ enumerate ไว้แล้วจาก `company-profile-options.ts`)
- **การแสดงฟิลด์ที่อยู่ของ `master-data/business-unit.md` ล้าสมัยเทียบกับการอ่าน source ของหน้านี้เอง** หน้านั้น §5.1 (แก้ไขล่าสุดโดย resync pass ก่อนหน้า) ยังคงระบุคอลัมน์เดี่ยว `hotel_address`/`company_address`/`*_zip_code` — แต่ type `BusinessUnitDetail` จริงและฟอร์มของหน้าจอนี้ยืนยันว่ามี 10 คอลัมน์แบบมีโครงสร้างต่อที่อยู่ (`*_address_line1/line2/sub_district/district/city/province/postal_code/country/latitude/longitude`) บวก `*_postal_code` (ไม่ใช่ `*_zip_code`) — ตรงกับสิ่งที่ resync pass ของ Platform book พบเองอย่างเป็นอิสระสำหรับ `BusinessUnitEdit.tsx` กำลัง flag ไว้สำหรับรอบแก้ไขในอนาคตของ `master-data/business-unit.md` เอง ไม่ได้แก้ในที่นี้ (อยู่นอกขอบเขตของหน้านี้)

---

## 5. กลุ่มฟิลด์ (Dev)

Source: `types/business-unit.ts` (`BusinessUnitDetail`) เทียบกับ `tb_business_unit` (platform schema) — ดู [master-data/business-unit](/th/inventory/master-data/business-unit) §5.1 สำหรับตาราง field Prisma ที่เป็นทางการ section นี้แค่บอกว่าฟิลด์ไหนเป็นของหน้าจอไหน

### 5.1 Section ของ Company Profile

| Section | ฟิลด์ | แก้ที่นี่ได้ไหม |
|---|---|---|
| General | `name`, `alias_name`, `cluster_name`, `description`, `info`, `default_currency_id` | ได้ (ยกเว้น `cluster_name`) |
| General (read-only) | `calculation_method`, `max_license_users` | ไม่ได้ — แสดงผลอย่างเดียว |
| Hotel | `hotel_name`, `hotel_email`, `hotel_tel`, `hotel_address_line1/2`, `hotel_sub_district`, `hotel_district`, `hotel_city`, `hotel_province`, `hotel_postal_code`, `hotel_country` | ได้ |
| Company | `company_name`, `branch_no`, `tax_no`, `company_email`, `company_tel`, `company_address_line1/2`, `company_sub_district`, `company_district`, `company_city`, `company_province`, `company_postal_code`, `company_country` | ได้ |
| Branding | `logo`, `avatar` | ไม่ได้ — preview รูปแบบ read-only |
| Date & Time | `timezone`, `date_format`, `date_time_format`, `time_format`, `short_time_format`, `long_time_format` | ได้ — ทั้งหมดเป็น `<select>` จาก option list ตายตัวใน `company-profile-options.ts` |
| Number Formats | `amount_format`, `quantity_format`, `perpage_format`, `recipe_format` | ได้ — แต่ละตัวเป็นคู่ `{ locales, minimumIntegerDigits }` |

ที่ไม่แสดงบนหน้าจอนี้เลย: `hotel_latitude/longitude`, `company_latitude/longitude`, `id`, `cluster_id`, `is_hq`, `is_active`, `db_connection`, `doc_version`, `audit` — มีอยู่ใน `BusinessUnitDetail` แต่ไม่มีฟิลด์บนหน้าจอในแอปทั้งสองเลย (บางตัวแก้ได้เฉพาะจาก platform admin console ของ `carmen-platform` — ดู [master-data/business-unit](/th/inventory/master-data/business-unit))

### 5.2 Section ของ Default Setting (registry `config[]`)

| Section id | หัวข้อ | Item | Datatype |
|---|---|---|---|
| `pr` | PR | `pr.allow-duplicate.product` — "Allow selecting duplicate products" | boolean |
| `si` | SI | `si.cost-from` — "Default price for added items" (`average`\*/`last_receiving`/`last_cost`) | enum |
| `po` | PO | `po.group-by-pr-comment` — "Group by PR comment" | boolean |
| `printForm` | Print Forms | 12 key ต่อประเภทเอกสาร: PR, PO, GRN, SR, CN, SI, SO, IA, PC, SC, RFP, EOP | enum (id ของ report-template มาจาก catalog template ของ [reporting-audit](/th/inventory/reporting-audit) กรองตาม `report_group`) |

\* option `average` แสดงเฉพาะเมื่อ `tb_business_unit.calculation_method = average` (หรือถูกเลือกอยู่แล้ว)

Print-form key แต่ละตัวสร้างจาก `printFormConfigKey(type)` (เช่น resolve เป็นอะไรทำนอง `print_form.pr`) — string constant ที่แน่นอนอยู่ใน `lib/print-form-config.ts` ไม่ขอ derive ซ้ำในที่นี้เพื่อเลี่ยงการ derive ค่าที่รวมศูนย์ไว้แล้วในไฟล์เดียว

## 6. กติกาทางธุรกิจ

- **แถวเดียว สองหน้าจอ ไม่มีการจัดการ conflict ที่ใช้ร่วมกันนอกเหนือจาก `doc_version`** ทั้งสองหน้าจอ PATCH แถว `tb_business_unit` เดียวกันอย่างเป็นอิสระต่อกัน; แต่ละหน้าแนบ `doc_version` ที่ตัวเองโหลดล่าสุด การแก้ทั้งสองหน้าจอในสอง tab แล้ว save ทั้งคู่จะทำให้ `doc_version` ของการ save ครั้งที่สองล้าสมัย — พฤติกรรม optimistic-concurrency มาตรฐาน ไม่ใช่เฉพาะหน้าจอนี้
- **การเลือก print-form ของ Default Setting ป้อนเข้าสู่ชั้น print/report** id ของ template ต่อประเภทเอกสารที่เลือกไว้ที่นี่คือสิ่งที่การพิมพ์เอกสาร default ไปใช้เมื่อผู้ใช้พิมพ์ PR/PO/GRN/ฯลฯ โดยไม่ได้เลือก template เอง — จุดที่นำไปใช้จริงคือ report/print rendering path ที่บันทึกไว้ที่ [reporting-audit](/th/inventory/reporting-audit) ไม่ได้ re-trace ในรอบนี้
- **`si.cost-from` และ `po.group-by-pr-comment` ถูกอ่านโดย module เอกสารของแต่ละตัวตอนสร้างเอกสาร/ตั้งราคา** หน้านี้บันทึกเฉพาะ config surface; การใช้งานจริงใน [purchase-request](/th/inventory/purchase-request)/[purchase-order](/th/inventory/purchase-order)/[inventory-adjustment](/th/inventory/inventory-adjustment) (Stock In) ไม่ได้ re-trace ในรอบนี้ และควรถือเป็น **ยังไม่ยืนยัน** จนกว่าจะมีการอ่านโค้ดของ module เหล่านั้นโดยเฉพาะ
- **ไม่พบข้อจำกัดฝั่ง client ที่ป้องกัน `calculation_method` ไม่ให้เพี้ยนไปจาก `si.cost-from = average`** หาก costing method ของ BU เปลี่ยนภายหลัง — ดู กรณีพิเศษ §4 สำหรับ guard ทิศทางเดียวที่มีอยู่ (คงการเลือก `average` ที่มีอยู่แล้วให้แสดงต่อไป ไม่ใช่การป้องกันไม่ให้เกิดความไม่ตรงกัน)

## 7. ความเชื่อมโยงข้ามโมดูล

- [master-data/business-unit](/th/inventory/master-data/business-unit) — โมเดลข้อมูล `tb_business_unit` ที่เป็นทางการ (platform schema) และ edit surface ของ platform admin console `carmen-platform` เองสำหรับฟิลด์ที่สองหน้าจอนี้ไม่ได้แสดง
- [system-config](/th/inventory/system-config) — module แม่; หน้าจอทั้งสองนี้อยู่ข้าง [system-config/workflow](/th/inventory/system-config/workflow), [system-config/period](/th/inventory/system-config/period) ฯลฯ ในฐานะ configuration ที่ Sysadmin ใช้
- [reporting-audit](/th/inventory/reporting-audit) — แหล่งของ catalog report-template ที่ section Print Forms ของ Default Setting เลือกจาก
- [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [inventory-adjustment](/th/inventory/inventory-adjustment) — module ที่ config item ของ Default Setting ตั้งใจจะขับพฤติกรรมการพิมพ์/ตั้งราคา (การใช้งานจริงไม่ได้ re-trace อย่างเป็นอิสระในรอบนี้)

## 8. แหล่งอ้างอิง

- **Frontend routes:** `../carmen-inventory-frontend-react/routes/system-admin/company-profile/company-profile.route.tsx` + `company-profile-component.tsx`; `routes/system-admin/default-setting/default-setting.route.tsx` + `default-setting-component.tsx`; redirect ที่ `routes/router.tsx` (`business-setting` → `<Navigate>`)
- **Form/registry ที่ใช้ร่วมกัน (import โดยทั้งสองหน้าจอ):** `../carmen-inventory-frontend-react/routes/system-admin/company-profile/company-profile-form-schema.ts`, `company-profile-config-registry.ts`, `company-profile-ui.tsx`, `company-profile-options.ts`
- **Frontend hooks:** `../carmen-inventory-frontend-react/hooks/use-business-unit.ts` — `useBusinessUnit()`, `useUpdateBusinessUnit()`
- **Frontend types:** `../carmen-inventory-frontend-react/types/business-unit.ts` — `BusinessUnitDetail`, `BusinessUnitEditable`, `BusinessUnitConfigItem`
- **API endpoint:** `../carmen-inventory-frontend-react/constant/api-endpoints.ts` — `BUSINESS_UNIT: "/api/proxy/api/business-units"`
- **ประวัติการออกแบบ:** `../carmen-inventory-frontend-react/docs/superpowers/specs/2026-07-10-default-setting-page-split-design.md`, `.../plans/2026-07-09-business-setting-{pr,si,po}-config-section-design.md` — การแยกจากหน้า "Business Setting" เดียวมาเป็นสองหน้าจอนี้
- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_business_unit` (บรรทัด ~117); ดู [master-data/business-unit](/th/inventory/master-data/business-unit) §8 สำหรับการอ้างอิงเต็ม
