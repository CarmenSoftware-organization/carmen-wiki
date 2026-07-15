---
title: รายการราคาผู้ขาย (Vendor Pricelist) — Test Scenarios — Purchaser
description: Test case ของ Purchaser (happy path, validation, edge case) สำหรับ vendor-pricelist ยึดตามสี่หน้าจอ CRUD จริง
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, test-scenarios, purchaser, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — Test Scenarios — Purchaser

> **At a Glance**
> **Persona:** Purchaser &nbsp;·&nbsp; **โมดูล:** [vendor-pricelist](/th/inventory/vendor-pricelist)
> **E2E coverage:** `150-vendor.spec.ts` (Vendor, จริง), `159-pl.spec.ts` (Price List, จริง), `160-pl-template.spec.ts` (Price List Template, จริง); ยังไม่มี spec สำหรับ Request for Pricing
> **ยืนยันแล้ว 2026-07-16:** ไม่มี tier ยกระดับ Manager, ไม่มีขีดจำกัด high-value, ไม่มี quality-score gate — ไม่มีตัวไหนมี code ตรงกัน

หน้านี้จับ test scenario ที่ Purchaser ขับข้ามสี่หน้าจอของโมดูล ไม่มี tier Manager ที่แยกต่างหาก — ทุก scenario ด้านล่างเข้าถึงได้โดย user ใดก็ตามที่ถือสิทธิ์ edit ของหน้าจอที่เกี่ยวข้อง

## 1. Happy Path

| # | Scenario | ขั้นตอน | คาด |
| - | -------- | ----- | -------- |
| VPL-PUR-HP-01 | สร้าง vendor พร้อม code + name + business type | Sidebar → **Vendor** → **New** กรอก code, name, เลือก business type Save | แถว Vendor ถูกสร้าง; พบใน list โดยชื่อ ตรงกับ `TC-VEN-030003` |
| VPL-PUR-HP-02 | สร้าง Price List Template พร้อมสินค้า + MOQ tier | Sidebar → **Price List Template** → **New** กรอกชื่อ, สกุลเงินตั้งต้น, validity period เพิ่มสินค้าพร้อม default order unit + MOQ tier Save | แถว `tb_pricelist_template` + แถว `tb_pricelist_template_detail` หนึ่งแถวถูกสร้างที่ `status = draft` ตรงกับ `160-pl-template.spec.ts` |
| VPL-PUR-HP-03 | Flip สถานะของ template ผ่าน status endpoint เฉพาะ | เปิด template ที่ save แล้ว เปลี่ยน `status` เป็น `active` | `PATCH :id/status` fire; `status = active` ไม่มี validation รัน (ไม่มี gate "≥1 สินค้า") — ยืนยันผ่าน `updateStatus()` ของ `pricelist-templates.service.ts` |
| VPL-PUR-HP-04 | สร้าง Request for Pricing ระบุ template + vendor สองราย | Sidebar → **Request Price List** → **New** เลือก template เพิ่มแถว vendor สำหรับ `V1` + `V2` Save | แถว `tb_request_for_pricing` + แถว `tb_request_for_pricing_detail` สองแถวถูกสร้างในการเรียกเดียวกัน แต่ละแถวมี `pricelist_url_token` ใหม่ ไม่มี action "launch" แยกต่างหาก |
| VPL-PUR-HP-05 | Vendor เปิดลิงก์ portal; Purchaser กรอก draft ที่สร้าง auto | 1. เปิด `/pl/:url_token` สำหรับ `V1` (auto-create draft ราคาศูนย์) 2. Purchaser เปิด pricelist เดียวกันบนหน้าจอ **Price List** กรอกราคาจริงต่อสินค้า/MOQ tier 3. ตั้ง `status = active` | Pricelist กลายเป็น queryable ในสถานะ `active`; `price-compare` สำหรับสินค้า/สกุลเงิน/วันที่ที่ครอบคลุมตอนนี้ return แถวนี้ |
| VPL-PUR-HP-06 | สร้าง Price List โดยตรง ไม่ผ่าน RFQ | Sidebar → **Price List** → **New** เลือก vendor + สกุลเงิน ตั้งวันที่ validity เพิ่มแถว detail save ที่ `status = active` | Pricelist ถูกสร้างโดยตรง; ตรงกับ `TC-PL-020001` นี่คือเส้นทางที่ใช้จริงเมื่อ vendor จะไม่ใช้ portal (ที่ตอนนี้เสีย) |
| VPL-PUR-HP-07 | Toggle `is_preferred` บนแถวของ pricelist ตนเอง | เปิด pricelist active → grid **Products** → toggle checkbox Crown บนแถวเดียว Save | `tb_pricelist_detail.is_preferred = true` บนแถวนั้น ไม่มีหน้าจอ cross-vendor เกี่ยวข้อง — นี่คือฟิลด์ต่อแถวบน pricelist นี้ลำพัง |
| VPL-PUR-HP-08 | Bulk-load price sheet ของ vendor ผ่าน CSV | Price List → Import CSV พร้อมแถว `pricelist_no`/`vendor_id`/`currency_id`/สินค้า | Grouped upsert ตาม `pricelist_no`: pricelist ใหม่ถูกสร้าง, ที่มีอยู่ถูกอัปเดตด้วยการแทนที่แถว detail เต็ม ตรงกับ `PriceListService.importCsv()` |
| VPL-PUR-HP-09 | แก้แถว detail ของ pricelist active โดยตรง | เปิด pricelist active → แก้ราคาของแถว → Save | Save สำเร็จโดยไม่มี immutability guard — ยืนยันว่าไม่มี branch ที่บล็อกตามสถานะใน `update()` |

## 2. Permission / Authorization

| # | Scenario | คาด |
| - | -------- | -------- |
| VPL-PUR-PERM-01 | Purchaser ที่ไม่มีสิทธิ์ view/edit ของโมดูลพยายามเข้าหน้าจอใดในสี่หน้าจอ | ถูกปฏิเสธตาม module-level permission gate ทั่วไป — ไม่มีการแยกละเอียด (create-vs-approve) ให้ test |
| VPL-PUR-PERM-02 *(removed)* | High-value / multi-currency approval gate | **ถูกลบออก — ไม่ได้ implement** ไม่มี approve endpoint แยกและไม่มี `threshold` ที่ไหนในโมดูลนี้ |
| VPL-PUR-PERM-03 *(removed)* | สิทธิ์ token-revocation | **ถูกลบออก — ไม่ได้ implement** ไม่มี action revoke อยู่จริง |

## 3. Validation / Error

| # | Scenario | Trigger | Error ที่คาด | Confirmed? |
| - | -------- | ------- | -------------- | ---------- |
| VPL-PUR-VAL-01 | สร้าง template ที่มีชื่อซ้ำ | ใช้ `tb_pricelist_template.name` ที่มีอยู่และไม่ถูก soft-delete ซ้ำ | ถูก reject ผ่าน DB constraint `pricelist_template_name_deletedat_u` | **Confirmed** |
| VPL-PUR-VAL-02 | สร้าง pricelist ที่ `effective_from_date` เป็นวันที่ในอดีต | ตั้ง `effective_from_date` ย้อนหลัง | ถูก reject — `PRICE_LIST_FROM_IN_PAST` | **Confirmed** |
| VPL-PUR-VAL-03 | สร้าง pricelist ที่ `effective_from_date > effective_to_date` | วันที่สลับกัน | ถูก reject — `PRICE_LIST_FROM_AFTER_TO` | **Confirmed** |
| VPL-PUR-VAL-04 | สร้าง RFQ ที่ `start_date > end_date` | วันที่สลับกัน | ถูก reject — `RFP_INVALID_DATE_RANGE` | **Confirmed** |
| VPL-PUR-VAL-05 | เพิ่ม vendor เดียวกันสองครั้งใน RFQ เดียว | แถว `vendors.add` ครั้งที่สองใช้ `vendor_id` เดียวกัน | ถูก reject ผ่าน `request_for_pricing_detail_request_for_pricing_id_vendor_id_u` | **Confirmed** |
| VPL-PUR-VAL-06 | Activate template ที่ไม่มีแถวสินค้าเลย | Template ไม่มีแถว `tb_pricelist_template_detail`; flip `status` เป็น `active` | **ไม่ถูก reject** — `updateStatus()` ไม่มี check แบบนี้; นี่คือ gap ที่ยืนยันแล้วเทียบกับ claim `VPL_VAL_002` ในฉบับ draft ก่อนหน้า | **Confirmed gap** |
| VPL-PUR-VAL-07 | Save แถว pricelist ที่ราคา MOQ-tier ลดหลั่นผิดทิศทาง (MOQ สูงกว่ากลับราคาสูงกว่า) | Tier 1 `qty 1 @ ฿10`, Tier 2 `qty 50 @ ฿12` | **ไม่ถูก reject** — ไม่มี non-increasing check ที่ไหนในโมดูลนี้; gap ที่ยืนยันแล้วเทียบกับ claim `VPL_VAL_020` ในฉบับ draft ก่อนหน้า | **Confirmed gap** |
| VPL-PUR-VAL-08 | แก้แถวที่ doc-version ล้าสมัย (optimistic concurrency) | สอง session โหลด pricelist เดียวกัน; ตัวที่สอง save ด้วย `doc_version` ที่ล้าสมัย | ถูก reject — `update()` scope `where` clause ด้วย `{id, doc_version}` ดังนั้นการเขียนที่ล้าสมัยจะจับคู่ได้ศูนย์แถว | **Confirmed** |

## 4. Edge Cases

| # | Scenario | คาด |
| - | -------- | -------- |
| VPL-PUR-EDGE-01 | การแก้พร้อมกันบน pricelist เดียวกันจากสอง session | Save แรกชนะ (จับคู่ตาม `doc_version`); การเรียก `update()` ของตัวที่สองส่งผลต่อศูนย์แถว ตรงกับ pattern optimistic-lock `doc_version` ทั่วไปของ Carmen ที่ใช้ข้ามทุกโมดูลในรอบนี้ |
| VPL-PUR-EDGE-02 | ราคาแบบ multi-MOQ-tier บนสินค้าเดียว หลายแถว | ยอมรับ — `@@unique([pricelist_id, product_id, unit_id, moq_qty, deleted_at])` อนุญาตหนึ่งแถวต่อ `moq_qty` ที่แตกต่างกัน |
| VPL-PUR-EDGE-03 | Soft-delete pricelist แล้วสร้างใหม่โดยใช้ `pricelist_no` เดิมซ้ำ | ยอมรับ — unique index รวม `deleted_at` |
| VPL-PUR-EDGE-04 | Vendor สองรายถูก mark `is_preferred = true` พร้อมกันสำหรับสินค้า/สกุลเงินเดียวกัน | ทั้งสองแถว persist อย่างอิสระ — ไม่มีอะไรบังคับ "แถว preferred เดียวเท่านั้น"; การเรียง (`is_preferred desc, price asc`) ของ `price-compare` เลือกตัวที่ราคาต่ำกว่าเป็น `selected` เมื่อทั้งคู่เป็น preferred |
| VPL-PUR-EDGE-05 | Vendor เข้าลิงก์ portal สองครั้ง | การเข้าครั้งแรกสร้าง draft pricelist; การเรียก `checkPricelist()` ครั้งที่สอง return pricelist ที่มีอยู่แทนที่จะสร้างซ้ำ (แยกตามว่า `pricelist_id` ถูก populate บนแถว invitation แล้วหรือไม่) |

## 5. แหล่งอ้างอิง

- ภาพรวม parent: [04-test-scenarios.md](./04-test-scenarios.md)
- User flow: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md)
- กติกาทางธุรกิจ: [02-business-rules.md](./02-business-rules.md) § 2 (confirmed-vs-design-target validation), § 5 (กติกาสถานะ)
- E2E: `../carmen-inventory-frontend-e2e/tests/150-vendor.spec.ts`, `159-pl.spec.ts`, `160-pl-template.spec.ts`
- Cross-link: [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [product](/th/inventory/product)
