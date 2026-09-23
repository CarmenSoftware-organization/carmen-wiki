---
title: รายการราคาผู้ขาย (Vendor Pricelist) — Test Scenarios
description: Test case ตาม persona, scenario ข้าม persona และ E2E mapping สำหรับ vendor-pricelist
published: true
date: '2026-09-23T01:30:00.000Z'
tags: vendor-pricelist, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — Test Scenarios

> **At a Glance**
> **โมดูล:** [vendor-pricelist](/th/inventory/vendor-pricelist) &nbsp;·&nbsp; **Persona ครอบคลุม:** Purchaser, Vendor (portal ภายนอก — save/submit ทำงานได้ตั้งแต่ 2026-08/09)
> **Drill-down ของแต่ละ persona คือ `04-test-scenarios-<role>.md`**
> **Executable coverage (2026-09-22):** `../carmen-inventory-frontend-e2e/tests/150-vendor.spec.ts` (31 case, 2 fixme) + `docs/test-cases/gaps/150-vendor-gap.md` (54), `tests/159-pl.spec.ts` (28, 4 fixme) + `gaps/159-pl-gap.md` (65), `tests/160-pl-template.spec.ts` (33) + `gaps/160-pl-template-gap.md` (58), `tests/043-certification.spec.ts` (6) + `gaps/043-certification-gap.md` (29); vendor portal: catalog แบบเอกสารเท่านั้น `docs/test-cases/1002-external-price-list.md` (42 ไม่มี spec); Request for Pricing: ไม่มี spec หน้านี้ไม่ mirror case เหล่านั้น

## 1. ภาพรวม

หน้านี้เป็นจุดเข้า overview สำหรับชุด test-scenario ของโมดูล `vendor-pricelist` เวอร์ชันก่อนหน้าของหน้านี้อธิบายสี่ persona (Purchaser, Vendor, Finance, Audit/Config) และ scenario ข้าม persona ~12 ตัวที่สร้างขึ้นรอบ workflow campaign แบบ multi-status ที่มี quality-score gate และ threshold-gate การตรวจสอบซ้ำกับ frontend/backend จริง (2026-07-16 ตรวจซ้ำ 2026-09-22) พบว่า workflow นั้นไม่มีอยู่จริง — โมดูลนี้คือหน้าจอ CRUD ธรรมดาห้าหน้า (Vendor, Certification, Price List, Price List Template, Request for Pricing) บวก vendor portal ภายนอกที่ตั้งแต่ 2026-08/09 save และ submit ได้จริง (gap เรื่อง Save/Submit ที่รายงานเมื่อ 2026-07-16 ปิดแล้ว) Test coverage ด้านล่าง re-anchor กับความเป็นจริงนั้น

Scope ของการ test บนโมดูล vendor-pricelist: **coverage functional** ของ create/edit/delete บนทั้งห้าหน้าจอบวก endpoint status-flip เฉพาะของ template; **round-trip ของ vendor portal** (เปิด → save → submit → `submitted` และการหมดอายุที่ `end_date`); **action send-email ของ RFQ**; **validation** ของ check ที่ implement จริง (ดู [02-business-rules](/th/inventory/vendor-pricelist/02-business-rules) § 2 ว่า rule ID ไหน confirmed เทียบกับ design-target); และ **กลไก `price-compare`** ที่ PR/PO ปลายน้ำใช้อ้างอิงราคา

## 2. Persona ใน Scope

- **Purchaser** — เป็นเจ้าของทั้งสี่หน้าจอ CRUD end-to-end: Vendor, Price List, Price List Template, Request for Pricing ไม่มี tier ยกระดับ Manager (ไม่มีอะไรให้ gate) ดู [04-test-scenarios-purchaser.md](./04-test-scenarios-purchaser.md)
- **Vendor** — External party; portal ที่ authenticate ด้วย token (เปิด, ตัวเลือก tax-profile/unit, save, Excel import, submit; 401 หลัง `end_date` ของ RFQ) section Permission ลดลงเป็นแถว N/A เดียว (ไม่มี Carmen login) ดู [04-test-scenarios-vendor.md](./04-test-scenarios-vendor.md)

Finance และ Audit/Config ถูกบันทึกเป็นหน้า correction ([04-test-scenarios-finance.md](./04-test-scenarios-finance.md), [04-test-scenarios-audit-config.md](./04-test-scenarios-audit-config.md)) — ทั้งสองไม่ใช่ persona ที่แยกต่างหากในโมดูลนี้

## 3. ไฟล์ Test Persona

- [Purchaser scenarios](/th/inventory/vendor-pricelist/04-test-scenarios-purchaser)
- [Vendor scenarios](/th/inventory/vendor-pricelist/04-test-scenarios-vendor) — section Permission / Authorization ลดลงเป็นแถว N/A เดียว
- [Finance scenarios](/th/inventory/vendor-pricelist/04-test-scenarios-finance) — หน้า correction
- [Audit / Config scenarios](/th/inventory/vendor-pricelist/04-test-scenarios-audit-config) — หน้า correction

## 4. Scenario ข้าม Persona

| # | Scenario | Persona ตามลำดับ | Confirmed? |
| - | -------- | ----------------- | ---------- |
| X-VPL-01 | สร้าง pricelist ตรง (ไม่มี RFQ) — Purchaser สร้าง Price List ให้ vendor, เพิ่มแถว detail, ตั้ง `status = active` | Purchaser เท่านั้น | **Confirmed** — CRUD ธรรมดา; เป็นเส้นทางที่พบบ่อยกว่าในทางปฏิบัติเพราะ gap ของ portal ด้านล่าง |
| X-VPL-02 | RFQ → Send email → vendor เปิด portal → draft สร้าง auto → vendor ตั้งราคา save submit → Purchaser activate pricelist ที่ `submitted` | Purchaser → Vendor → Purchaser | **Confirmed (2026-09-22)** — `submit()` ตั้ง `submitted` + `submitted_at` ตัดแถวที่ไม่มีราคา; แถว vendor ของ RFQ แสดง `has_submitted` และสถานะ pricelist; Purchaser ตั้ง `active` บนหน้าจอ Price List |
| X-VPL-03 | Vendor เปิด / save / submit หลัง `end_date` ของ RFQ | Vendor | **Confirmed rejection** — `UrlTokenGuard` คืน 401 `url_token has expired`; portal แสดงหน้าจอหมดอายุ |
| X-VPL-04 | การเลือกแถว preferred ป้อนเข้า `price-compare` สำหรับราคา PR/PO ปลายน้ำ | Purchaser → (PR/PO ปลายน้ำ, out of scope ที่นี่) | **Confirmed** — endpoint จริง, flag ต่อแถวจริง |
| X-VPL-05 | Purchaser ตั้ง pricelist `draft → submitted` บนฟอร์มภายในโดยมีแถวราคาศูนย์บางแถว | Purchaser | **Confirmed** — `PriceListService.update()` stamp `submitted_at` และลบแถวราคาศูนย์หลังจาก apply add/update/remove ของ request เอง |

Scenario ที่อธิบาย high-value approval เฉพาะ Manager, co-signoff ของ Finance Manager, การ revoke token ของ Sysadmin, auto-expiry cron, การ pause/cancel campaign หรือ quality-score gate ถูกลบออกแล้ว — ไม่มีตัวไหนมี code ตรงกัน (ดู [02-business-rules](/th/inventory/vendor-pricelist/02-business-rules))

## 5. E2E Test Mapping

มี Playwright spec จริงสำหรับสี่ในห้าหน้าจอ (ดู coverage note ด้านบนสำหรับจำนวน):

- `../carmen-inventory-frontend-e2e/tests/150-vendor.spec.ts` — CRUD เต็ม, การนำทาง tab (address/contact/info), validation (required field, max-length, duplicate code) และ coverage admin-BU สำหรับหน้าจอ **Vendor**; ยังไม่มีอะไรสำหรับ section certificates หรือ `tax_no` / `branch_no` / `rating` ที่มีเฉพาะ backend
- `../carmen-inventory-frontend-e2e/tests/043-certification.spec.ts` — master **Certification** (CRUD แบบ dialog) ใต้ `/vendor-management/certification`
- `../carmen-inventory-frontend-e2e/tests/159-pl.spec.ts` — list/search/filter, create, view detail, edit และ Export สำหรับ **Price List** section Duplicate และ "Mark as Expired" ของมันใช้ assertion แบบ loose/best-effort (`.catch(() => {})`, `expect(true).toBe(true)`) และอ้างอิง action ที่ไม่พบใน list component จริง (row action ของ `use-pl-table.tsx` มีแค่ Edit + Delete บวกปุ่ม Export ฝั่ง client) — ถือว่าสองส่วนนี้เป็น test-plan scaffolding เชิงคาดหวัง ไม่ใช่ feature ที่ยืนยันแล้ว
- `../carmen-inventory-frontend-e2e/tests/160-pl-template.spec.ts` — coverage ของ **Price List Template**
- **ยังไม่มี spec** สำหรับ Request for Pricing (รวม Send email) หรือสำหรับ vendor portal ภายนอก — portal มี catalog แบบเอกสารเท่านั้น `docs/test-cases/1002-external-price-list.md` (42 case `TC-EPL-*`)

การบริโภคปลายน้ำถูก exercise ทางอ้อมโดย:

- `../carmen-inventory-frontend-e2e/tests/402-po-purchaser-journey.spec.ts` (TC-PO-060205..TC-PO-060208) — wizard PO From-Price-List

## 6. แหล่งอ้างอิง

- Sibling: [03-user-flow.md](./03-user-flow.md) § 4 (แหล่ง handoff)
- Sibling: [02-business-rules.md](./02-business-rules.md) — สถานะ confirmed-vs-design-target ต่อ rule
- Sibling: [01-data-model.md](./01-data-model.md) — เอนทิตี, enum, ข้อจำกัด unique
