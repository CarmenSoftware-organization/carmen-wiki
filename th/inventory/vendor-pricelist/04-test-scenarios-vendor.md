---
title: รายการราคาผู้ขาย (Vendor Pricelist) — Test Scenarios — Vendor
description: Test case ของ Vendor สำหรับ vendor-pricelist External party — เปิด / save / submit / หมดอายุของ portal; section Permission / Authorization ลดลงเป็นแถว N/A เดียว
published: true
date: '2026-09-23T01:30:00.000Z'
tags: vendor-pricelist, test-scenarios, vendor, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — Test Scenarios — Vendor

> **At a Glance**
> **Persona:** Vendor (external party — portal ที่ authenticate ด้วย token เท่านั้น) &nbsp;·&nbsp; **โมดูล:** [vendor-pricelist](/th/inventory/vendor-pricelist)
> **Executable coverage (2026-09-22):** ไม่มี Playwright spec สำหรับ portal; catalog แบบเอกสารเท่านั้น `../carmen-inventory-frontend-e2e/docs/test-cases/1002-external-price-list.md` (42 case `TC-EPL-*`: โหลด, header, ตารางสินค้า, sub-table MOQ, ตัวเลือก tax-profile / unit, save, Excel import, submit, หน้าจอหมดอายุ) เป็น oracle ที่ใกล้ที่สุด หน้านี้ไม่ mirror มัน
> **Re-sync 2026-09-22:** ข้อค้นพบ "Save/Submit ยืนยันแล้วว่าไม่ทำงาน" ของรอบ 2026-07-16 ล้าสมัยแล้ว — `PATCH /api/pricelist-external/:url_token` และ `POST …/submit` มีอยู่จริง; ลิงก์หมดอายุที่ `end_date` ของ RFQ

หน้านี้จับ test scenario ที่ exercise การ interact ของ persona **Vendor** กับ `/pl/:url_token` เพราะ vendor ไม่มี Carmen login section Permission / Authorization จึงลดลงเป็นแถว N/A เดียว

## 1. Happy Path

| # | Scenario | Pre-condition | ขั้นตอน | คาด |
| - | -------- | ------------- | ----- | -------- |
| VPL-VND-HP-01 | เปิดลิงก์ portal เป็นครั้งแรก | RFQ ถูกสร้างพร้อมเชิญ vendor `V1` (ดู `VPL-PUR-HP-04`), `end_date` อยู่ในอนาคต; ทราบ `pricelist_url_token` ของ `V1` | Vendor เปิด `/pl/:url_token` | `POST /api/external/api/check-pricelist/:url_token` ผ่าน `UrlTokenGuard`; draft `tb_pricelist` ราคาศูนย์ (หนึ่งแถวต่อสินค้าของ template × unit/MOQ tier เติม tax profile ไว้ล่วงหน้า `effective_from/to` = วันที่ของ RFQ) ถูกสร้างและ return; `pricelist_id` / `pricelist_no` ของแถว invitation ถูก populate; activity `create` ถูก log |
| VPL-VND-HP-02 | เปิดลิงก์ portal ซ้ำหลังมี pricelist อยู่แล้ว | ต่อจาก VPL-VND-HP-01 | Vendor เปิดลิงก์เดิมอีกครั้ง | การเรียกเดิม return pricelist ที่มีอยู่แทนที่จะสร้างตัวที่สอง |
| VPL-VND-HP-03 | เลือก tax profile และ order unit ต่อบรรทัด | ต่อจาก HP-01; BU มี tax profile ≥ 2; สินค้าหนึ่งมี order unit ≥ 2 | Toggle โหมด Edit; เปลี่ยน tax profile และ unit บนหนึ่งบรรทัด | ตัวเลือกมาจาก `GET …/check-pricelist/:url_token/tax-profiles` และ `…/units` (unit default มี flag); `tax_rate` / `tax_amt` ของบรรทัดคำนวณใหม่ฝั่ง client |
| VPL-VND-HP-04 | Save draft | ต่อจาก HP-03; พิมพ์ราคาบนสองบรรทัด | คลิก **Save** | `PATCH …/pricelist-external/:url_token` พร้อม `{ note, pricelist_detail: { update: [...] } }` → 200; pricelist ยังคง `draft`; reload ลิงก์แสดงราคาที่บันทึก; `tb_activity` มี entry `vendor.pricelist.draft_saved` พร้อม snapshot ก่อน/หลัง |
| VPL-VND-HP-05 | เพิ่ม MOQ tier อีกอันสำหรับสินค้า | ต่อจาก HP-04 | ใน sub-table MOQ เพิ่ม tier (`moq_qty = 50` ราคาต่ำกว่า); Save | `pricelist_detail.add[]` สร้างแถว `(product, unit, moq_qty)` ใหม่; unique key อนุญาต |
| VPL-VND-HP-06 | Import ราคาจาก Excel | ต่อจาก HP-01; sheet ในรูปแบบ download ของ portal | **Import** → เลือกไฟล์ → ยืนยัน | `price-list-external-excel.ts` parse sheet เข้าฟอร์ม; แถว match ด้วย product code + unit + MOQ; แถวที่ไม่ match ถูกรายงานใน dialog; ไม่มีอะไร persist จนกว่าจะ **Save** |
| VPL-VND-HP-07 | Submit | ต่อจาก HP-04; หนึ่งบรรทัดยังเป็น `price = 0` | คลิก **Submit** → ยืนยัน | `POST …/pricelist-external/:url_token/submit` → `status = submitted`, `submitted_at = now()`; บรรทัดราคาศูนย์ถูกลบ; activity `submit` ถูก log; หน้าเปลี่ยนเป็นอ่านอย่างเดียว; แถว RFQ ของ Purchaser แสดง `has_submitted = true`, `pricelist.status = submitted` |

## 2. Permission / Authorization

| # | Scenario | พฤติกรรมที่คาด |
| - | -------- | ------------------ |
| VPL-VND-PERM-01 | Vendor เป็น external party ที่ไม่มี Carmen login; RBAC ใน-ระบบเป็น N/A | N/A — ไม่มี login, ไม่มี role และไม่มี permission matrix ให้ test gate เดียวคือ `UrlTokenGuard` (`VPL_VAL_027`): token ที่ถูกต้องและยังไม่หมดอายุ → scope `{ bu, vendor_id, rfp_detail_id }` ของ JWT; guard ไม่มีการตรวจ IP หรือ session |

## 3. Validation / Error

| # | Scenario | Trigger | คาด |
| - | -------- | ------- | -------- |
| VPL-VND-VAL-01 | เปิด portal ด้วย token ที่ไม่ตรงกับแถว `tb_shot_url` ใดเลย | `url_token` ที่ผิดรูปแบบหรือไม่รู้จัก | 401 `Invalid or expired url_token` จาก `UrlTokenGuard`; หน้าแสดง *This link has expired* |
| VPL-VND-VAL-02 | เปิด portal สำหรับ invitation ที่ template ที่ link ถูก soft-delete | Template `deleted_at IS NOT NULL` | `checkPriceList()` return 404 `Pricelist template not found` |
| VPL-VND-VAL-03 | Save หรือ Submit หลังจาก pricelist เป็น `submitted` แล้ว | ต่อจาก HP-07; replay `PATCH` / `POST` | ถูกปฏิเสธ — `saveDraft()` / `submit()` ต้องการ `status = draft` (`Price list is not in draft status and cannot be submitted`); UI ซ่อน control (`data.status !== "submitted"`) |
| VPL-VND-VAL-04 | Submit โดยทุกบรรทัดไม่มีราคา | ทุกแถว `price = 0` | **ยอมรับ** — ทุกแถวถูกลบและเหลือ pricelist `submitted` ว่างเปล่า (`VPL_VAL_023`); ไม่มีการตรวจ "อย่างน้อยหนึ่งแถวที่มีราคา" |

## 4. Edge Cases

| # | Scenario | เงื่อนไข | คาด |
| - | -------- | --------- | -------- |
| VPL-VND-EDGE-01 | เปิดลิงก์ portal หลังจาก `end_date` ของ RFQ ผ่านไปแล้ว | `tb_shot_url.expired_at < now()` | **ถูกปฏิเสธ** — 401 `url_token has expired` บนทุก call รวมถึงการเปิดครั้งแรก; portal render หน้าจอหมดอายุ การขยาย `end_date` ภายหลังไม่ฟื้น token ที่มีอยู่ |
| VPL-VND-EDGE-02 | เปิดลิงก์ portal จาก IP address ใดก็ได้ | ไม่มี allowlist | **ไม่มีการบังคับใช้** ไม่มี IP check ที่ไหนใน guard หรือ service |
| VPL-VND-EDGE-03 | ลิงก์เดียวกันถูกเปิดในหลาย browser tab พร้อมกัน | ไม่มี code จำกัด session | **ไม่มีการบังคับใช้** แต่ละ tab ทำงานอย่างอิสระ; การ save พร้อมกัน race บนแถวเดียวกัน (last write wins — `saveDraft()` ไม่ใช้ `doc_version`) |
| VPL-VND-EDGE-04 | Vendor save หลังจาก Purchaser แก้ draft เดียวกันภายใน | Purchaser เปลี่ยนราคาบนหน้าจอ Price List | Last write wins; ไม่มี conflict detection ฝั่ง portal |

## 5. แหล่งอ้างอิง

- ภาพรวม parent: [04-test-scenarios.md](./04-test-scenarios.md)
- User flow: [03-user-flow-vendor.md](./03-user-flow-vendor.md) — flow ของ portal ทีละขั้นตอน
- กติกาทางธุรกิจ: [02-business-rules.md](./02-business-rules.md) § 5.4, `VPL_VAL_023`, `VPL_VAL_027`, `VPL_VAL_028`
- Backend: `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/pricelists/check-pricelist.controller.ts`, `pricelist-external.controller.ts`, `apps/backend-gateway/src/auth/guards/url-token.guard.ts`; `apps/micro-business/src/master/check-price-list/check-price-list.service.ts`
- Frontend: `../carmen-inventory-frontend-react/routes/external/pl/` (`use-price-list-external.ts`, `price-list-external-import-dialog.tsx`, `price-list-external-expired.tsx`)
- Sibling: [04-test-scenarios-purchaser.md](./04-test-scenarios-purchaser.md) — วิธีที่ Purchaser ส่ง email ลิงก์และ activate pricelist ที่ submit แล้ว
