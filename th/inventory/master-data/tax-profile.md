---
title: Profile ภาษี (Tax Profile)
description: นิยามอัตราภาษีแบบมีชื่อที่ถูกอ้างอิงโดยผู้ขาย สินค้า และทุกบรรทัดเอกสารที่มีราคา ตอนนี้จัดประเภท VAT หรือภาษีหัก ณ ที่จ่าย (WHT) พร้อมบัญชี GL และแบบ PND ที่ไม่บังคับ
published: true
date: '2026-10-27T15:00:00.000Z'
tags: master-data, tax-profile, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Profile ภาษี (Tax Profile)

> **At a Glance**
> **เจ้าของ:** Product Admin (หรือ Sysadmin) &nbsp;·&nbsp; **ตาราง:** `tb_tax_profile` &nbsp;·&nbsp; **ใช้โดย:** vendor, product, PR / PO / GRN / pricelist / credit note &nbsp;·&nbsp; อัตรามีชื่อ (`VAT 7%`, `Zero-rated`) — โหมดภาษีของบรรทัดตัดสินวิธีนำไปใช้

![Profile ภาษี (Tax Profile) screen](/screenshots/master-data/tax-profile.png)

## 1. คืออะไร / ใครใช้

**Tax profile** คือนิยามแบบมีชื่อที่จับคู่ label (เช่น `VAT 7%`, `Zero-rated`, `Service Charge`) กับ `tax_rate` แบบ decimal Tax profile ถูกอ้างอิงจาก **ผู้ขาย, ข้อมูลหลักสินค้า และบรรทัดเอกสารที่มีราคาส่วนใหญ่** (PR, PO, GRN, pricelist, credit note) การแยกออกจากกันสำคัญ: อัตราเปลี่ยนแปลงตามเวลาและหลาย property ปฏิบัติงานภายใต้หลายระบบพร้อมกัน

ตั้งแต่ 2026-09-23 profile ยังมี **การจัดประเภทภาษีฝั่ง AP** (`tax_type` = `vat` \| `wht`, `chart_of_accounts_id` ที่ไม่บังคับ และสำหรับ WHT มี `wht_pnd_form` กับ `wht_income_type`) ที่ใช้โดยงาน AP-invoice ขณะนี้ **มีเฉพาะ API**: dialog Tax Profile ไม่ส่งฟิลด์ทั้งสี่นี้ ดังนั้น profile ที่สร้างผ่าน UI จึงเป็น `vat` และไม่มีบัญชี

การคำนวณภาษีระดับบรรทัดเอกสารอ่านสามอย่าง: **tax profile ที่เลือก**, **โหมดภาษี** ของเอกสาร (`none` / `included` / `add` ผ่าน `enum_tax_type`) และ **base amount ของบรรทัด** Tax profile ให้ *อัตรา*; โหมดตัดสินวิธีนำไปใช้ **บริหารจัดการโดย** Product Admin; **อ่านโดย** ทุก flow ของเอกสารที่มีราคา

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่ม profile | Configuration → Master Data → Tax Profile → **New** | บังคับ: `name`, `tax_rate` (decimal — `0.07` = 7%) |
| ยกเลิกการใช้งาน | Toggle `is_active` | ซ่อนจาก picker ของเอกสารใหม่; บรรทัดประวัติไม่เปลี่ยน |
| อัตราใหม่จาก regulator | **สร้าง profile ใหม่** | เช่น `VAT 9%` — อย่าแก้อัตราของ profile เก่า |
| ย้าย vendor/product | Bulk update reference fields | หลังสร้าง profile ใหม่ ย้ายการอ้างอิงไปข้างหน้า |
| จัดประเภทเป็น VAT / WHT, ลิงก์บัญชี GL (API) | `tax_type`, `chart_of_accounts_id`, `wht_pnd_form`, `wht_income_type` บน `POST/PUT` tax-profiles | `chart_of_accounts_id` ต้องเป็นแถว [chart-of-accounts](/th/inventory/master-data/chart-of-accounts) ที่ active และ **postable** (type ไม่ใช่ `header` / `summary`) การส่ง `tax_type = vat` จะ null ค่า `wht_pnd_form` และ `wht_income_type` (`normalizeWhtFields`) |
| ตรวจสอบอัตราที่ใช้บนบรรทัด | เปิดบรรทัดเอกสาร | อัตรา snapshot, ไม่ resolve จากตารางนี้ |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| `409 TAX_PROFILE_NAME_ALREADY_EXISTS` — "Tax profile name already exists" | `name` ซ้ำบนแถว non-deleted (dialog แสดงใต้ **Name**) | เลือกชื่ออื่นหรือ reactivate แถวที่มี |
| `422 GL_ACCOUNT_NOT_POSTABLE` — "Account is inactive or is a header/summary account that cannot be posted to" | `chart_of_accounts_id` ไม่รู้จัก, ถูกลบ, inactive หรือเป็น type `header` / `summary` (ทั้ง create และ update) | เลือกบัญชีที่ postable |
| **ยังไม่ยืนยัน** — ไม่พบ guard สำหรับอัตราหรือการลบ | `TaxProfileCreateSchema`/`TaxProfileUpdateSchema` (`tax-profile.dto.ts`) ประกาศ `tax_rate` เป็น `z.number()` เฉย ๆ ไม่มีขั้นต่ำ และ `tax_profile.service.ts`'s `delete()` เป็น soft-delete แบบไม่มีเงื่อนไข ไม่มีการเช็คการอ้างอิง | เดิมหน้านี้ระบุว่า "rate must be >= 0" และ "cannot delete — referenced by documents/vendors/products" เป็น error ที่บังคับใช้จริง; ให้ถือว่าทั้งคู่**ยังไม่ถูกบังคับใช้**จนกว่าจะตรวจสอบซ้ำ |
| บรรทัดแสดงอัตราเก่าหลังแก้ profile | บรรทัด snapshot อัตราต้นทาง | คาดหวัง — snapshot คือ contract |

## 4. Edge Cases

- **Snapshot semantics** บรรทัดเอกสารทุกบรรทัด snapshot อัตรา ณ เวลาที่ posting; การแก้ `tax_rate` ที่นี่ ไม่ retro-edit บรรทัดที่ posted
- **วินัยการเปลี่ยนอัตรา** เมื่อ regulator เปลี่ยน headline rate ให้ **สร้าง profile ใหม่** (เช่น `VAT 9%`) แล้วย้าย vendor/product ไปข้างหน้า — อย่าแก้ profile เก่า
- **รูปแบบ decimal** — `0.07` แทน 7%; UI ต้อง validate และแปลง
- **การ inactivate** รักษาการ lookup ประวัติให้ resolve ได้
- **`enum_tax_type`** อยู่บนแต่ละบรรทัดเอกสาร ไม่ใช่บน profile — ดูหมายเหตุ schema ใน References

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_tax_profile`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล (เช่น `VAT 7%`) |
| `tax_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | อัตราในรูป decimal (default `0`) `0.07` สำหรับ 7% |
| `is_active` | `Boolean?` | Yes | Active flag |
| `tax_type` | `enum_tax_profile_tax_type` | No | `vat` (default) \| `wht` |
| `chart_of_accounts_id` | `String? @db.Uuid` | Yes | FK → `tb_chart_of_accounts` (`onDelete: NoAction`) |
| `wht_pnd_form` | `enum_tax_profile_wht_pnd_form?` | Yes | `pnd_1`, `pnd_2`, `pnd_3`, `pnd_53`, `pnd_54`; มีความหมายเฉพาะ WHT |
| `wht_income_type` | `String? @db.VarChar` | Yes | Free text; เฉพาะ WHT |
| `description` | `String? @db.VarChar` | Yes | Free text |
| `note`, `info`, `dimension` | — | Yes | Metadata มาตรฐาน |
| `doc_version` | `Int` | No | เวอร์ชัน optimistic-lock (default `0`) |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, deleted_at])` map `taxprofile_name_deletedat_u` Index บน `name` Reverse relation ที่กว้างไปยัง PR / PO / GRN / pricelist / vendor / product / credit-note / extra-cost-detail

## 6. กติกาทางธุรกิจ

- **Uniqueness** `name` unique ในแถว non-deleted (DB-enforced)
- **Deletion guards — ยังไม่ยืนยัน** ไม่พบการเช็ค FK ใน `delete()`; soft-delete สำเร็จโดยไม่มีเงื่อนไขแม้มีการอ้างอิงเอกสาร/vendor/product
- **Validation — ยังไม่ยืนยัน** ไม่พบการเช็คค่าบวกบน `tax_rate` ฝั่ง server; storage เป็นรูป decimal (`0.07` = 7%)
- **Lifecycle** profile ที่ inactive ซ่อนจาก picker ใหม่; อ่านได้บนบรรทัดประวัติ
- **Snapshot semantics** บรรทัดเอกสาร snapshot อัตรา; การแก้ที่นี่ไม่ retro-edit เอกสารประวัติ
- **วินัยการเปลี่ยนอัตรา** สร้าง profile ใหม่เสมอเมื่อ headline rate เปลี่ยน
- **Classification** `tax_type`, `chart_of_accounts_id` และฟิลด์ WHT ถูกอ่านโดยโค้ด AP-invoice ไม่ใช่โดยการคำนวณภาษีบรรทัด PR / PO / GRN; `tax_type` มี default เป็น `vat`
- **Default sort** `GET /tax-profiles` ที่ไม่มี `?sort=` คืน `name:asc, tax_rate:asc, id:asc` (`tax_profile.service.ts`, `withDefaultSort`, 2026-09-13)

## 7. การอ้างอิงข้ามโมดูล

- [master-data/vendor](/th/inventory/master-data/vendor) — ผู้ขายเก็บ default tax profile ที่ snapshot ณ เวลา link
- [product](/th/inventory/product) — ข้อมูลหลักสินค้าอ้างอิง default tax profile ต่อรายการ
- [purchase-request](/th/inventory/purchase-request) — บรรทัด detail ของ PR snapshot profile id + อัตรา
- [purchase-order](/th/inventory/purchase-order) — บรรทัด detail ของ PO snapshot; default จาก vendor/product
- [good-receive-note](/th/inventory/good-receive-note) — บรรทัด detail ของ GRN snapshot จาก PO/ด้วยมือ
- [vendor-pricelist](/th/inventory/vendor-pricelist) — บรรทัด detail ของ pricelist บรรจุการอ้างอิง tax profile

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_tax_profile` (line ~1491), `enum_tax_type` (~96) — หมายเหตุ `enum_tax_type` อยู่บนแต่ละบรรทัดเอกสาร ไม่ใช่บนเอนทิตีนี้
- **Migration / backend (classification):** `20260923060040_accounting_foundation_ap`; `apps/micro-business/src/master/tax_profile/tax_profile.service.ts` (`validateChartOfAccounts`, `normalizeWhtFields`)
- **E2E:** `../carmen-frontend-e2e/tests/042-tax-profile.spec.ts` + `docs/test-cases/gaps/042-tax-profile-gap.md`
- **Frontend:** `../carmen-frontend/routes/config/tax-profile/`
