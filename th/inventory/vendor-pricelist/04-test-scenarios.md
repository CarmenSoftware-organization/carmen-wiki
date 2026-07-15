---
title: รายการราคาผู้ขาย (Vendor Pricelist) — Test Scenarios
description: Test case ตาม persona, scenario ข้าม persona และ E2E mapping สำหรับ vendor-pricelist
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — Test Scenarios

> **At a Glance**
> **โมดูล:** [vendor-pricelist](/th/inventory/vendor-pricelist) &nbsp;·&nbsp; **Persona ครอบคลุม:** Purchaser, Vendor (external, confirmed-broken submit path)
> **มี E2E coverage จริง:** `150-vendor.spec.ts`, `159-pl.spec.ts`, `160-pl-template.spec.ts` ใน `../carmen-inventory-frontend-e2e/tests/` — claim เดิมที่ว่า "ไม่มี spec dedicated" ผิด
> **Drill-down ของแต่ละ persona คือ `04-test-scenarios-<role>.md`**

## 1. ภาพรวม

หน้านี้เป็นจุดเข้า overview สำหรับชุด test-scenario ของโมดูล `vendor-pricelist` เวอร์ชันก่อนหน้าของหน้านี้อธิบายสี่ persona (Purchaser, Vendor, Finance, Audit/Config) และ scenario ข้าม persona ~12 ตัวที่สร้างขึ้นรอบ workflow campaign แบบ multi-status ที่มี quality-score gate และ threshold-gate การตรวจสอบซ้ำกับ frontend/backend จริงในรอบนี้พบว่า workflow นั้นไม่มีอยู่จริง — โมดูลนี้คือหน้าจอ CRUD ธรรมดาสี่หน้า (Vendor, Price List, Price List Template, Request for Pricing) บวก vendor portal ภายนอกที่การเรียก Save/Submit ชี้ไปยัง backend route ที่ไม่มีอยู่จริง Test coverage ด้านล่าง re-anchor กับความเป็นจริงนั้น

Scope ของการ test บนโมดูล vendor-pricelist: **coverage functional** ของ create/edit/delete บนทั้งสี่หน้าจอบวก endpoint status-flip เฉพาะของ template; **gap ของ vendor portal ที่ยืนยันแล้ว** (วันนี้เป็น view-only); **validation** ของ check ที่ implement จริง (ดู [02-business-rules](/th/inventory/vendor-pricelist/02-business-rules) § 2 ว่า rule ID ไหน confirmed เทียบกับ design-target); และ **กลไก `price-compare`** ที่ PR/PO ปลายน้ำใช้อ้างอิงราคา

## 2. Persona ใน Scope

- **Purchaser** — เป็นเจ้าของทั้งสี่หน้าจอ CRUD end-to-end: Vendor, Price List, Price List Template, Request for Pricing ไม่มี tier ยกระดับ Manager (ไม่มีอะไรให้ gate) ดู [04-test-scenarios-purchaser.md](./04-test-scenarios-purchaser.md)
- **Vendor** — External party; portal ที่ authenticate ด้วย token เฉพาะการเรียก "เปิดลิงก์" เริ่มต้นเท่านั้นที่ทำงาน; Save และ Submit ยืนยันแล้วว่าไม่ทำงาน section Permission ลดลงเป็นแถว N/A เดียว (ไม่มี Carmen login) ดู [04-test-scenarios-vendor.md](./04-test-scenarios-vendor.md)

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
| X-VPL-02 | RFQ → vendor เปิด portal → draft สร้าง auto → Purchaser กรอกราคาบนหน้าจอภายใน → activate | Purchaser → Vendor (view only) → Purchaser | **Confirmed** โดย step ของ portal จำกัดแค่การดู — vendor ไม่สามารถ persist การแก้ไขหรือ submit ผ่าน `/pl/:url_token` ได้ในวันนี้ |
| X-VPL-03 | Vendor พยายาม Save / Submit บน portal | Vendor | **Confirmed failure** — backend route เป้าหมายไม่มีอยู่จริง |
| X-VPL-04 | การเลือกแถว preferred ป้อนเข้า `price-compare` สำหรับราคา PR/PO ปลายน้ำ | Purchaser → (PR/PO ปลายน้ำ, out of scope ที่นี่) | **Confirmed** — endpoint จริง, flag ต่อแถวจริง |

Scenario ที่อธิบาย high-value approval เฉพาะ Manager, co-signoff ของ Finance Manager, การ revoke token ของ Sysadmin, auto-expiry cron, การ pause/cancel campaign หรือ quality-score gate ถูกลบออกแล้ว — ไม่มีตัวไหนมี code ตรงกัน (ดู [02-business-rules](/th/inventory/vendor-pricelist/02-business-rules))

## 5. E2E Test Mapping

มี Playwright spec จริงสำหรับสามในสี่หน้าจอ:

- `../carmen-inventory-frontend-e2e/tests/150-vendor.spec.ts` (~875 บรรทัด) — CRUD เต็ม, การนำทาง tab (address/contact/info), validation (required field, max-length, duplicate code) และ coverage admin-BU สำหรับหน้าจอ **Vendor**
- `../carmen-inventory-frontend-e2e/tests/159-pl.spec.ts` — list/search/filter, create, view detail, edit และ Export สำหรับ **Price List** section Duplicate และ "Mark as Expired" ของมันใช้ assertion แบบ loose/best-effort (`.catch(() => {})`, `expect(true).toBe(true)`) และอ้างอิง action ที่ไม่พบใน list component จริง (row action ของ `use-pl-table.tsx` มีแค่ Edit + Delete บวกปุ่ม Export ฝั่ง client) — ถือว่าสองส่วนนี้เป็น test-plan scaffolding เชิงคาดหวัง ไม่ใช่ feature ที่ยืนยันแล้ว
- `../carmen-inventory-frontend-e2e/tests/160-pl-template.spec.ts` — coverage ของ **Price List Template**
- **ยังไม่มี spec** สำหรับ Request for Pricing หรือสำหรับ vendor portal ภายนอก

การบริโภคปลายน้ำถูก exercise ทางอ้อมโดย:

- `../carmen-inventory-frontend-e2e/tests/402-po-purchaser-journey.spec.ts` (TC-PO-060205..TC-PO-060208) — wizard PO From-Price-List

## 6. แหล่งอ้างอิง

- Sibling: [03-user-flow.md](./03-user-flow.md) § 4 (แหล่ง handoff)
- Sibling: [02-business-rules.md](./02-business-rules.md) — สถานะ confirmed-vs-design-target ต่อ rule
- Sibling: [01-data-model.md](./01-data-model.md) — เอนทิตี, enum, ข้อจำกัด unique
