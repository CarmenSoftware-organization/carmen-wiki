---
title: รายการราคาผู้ขาย (Vendor Pricelist) — Test Scenarios — Vendor
description: Test case ของ Vendor สำหรับ vendor-pricelist External party — section Permission / Authorization ลดลงเป็นแถว N/A เดียว; Save/Submit ยืนยันแล้วว่าไม่ทำงานกับ backend ปัจจุบัน
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, test-scenarios, vendor, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — Test Scenarios — Vendor

> **At a Glance**
> **Persona:** Vendor (external party — portal ที่ authenticate ด้วย token เท่านั้น) &nbsp;·&nbsp; **โมดูล:** [vendor-pricelist](/th/inventory/vendor-pricelist)
> **ยืนยันแล้ว 2026-07-16:** มีเพียงการเรียก "เปิดลิงก์" เท่านั้นที่ทำงาน; Save และ Submit ชี้ไปยัง backend route ที่ไม่มีอยู่จริง

หน้านี้จับ test scenario ที่ exercise การ interact ของ persona **Vendor** กับ `/pl/:url_token` เพราะ vendor ไม่มี Carmen login section Permission / Authorization จึงลดลงเป็นแถว N/A เดียว

## 1. Happy Path

| # | Scenario | Pre-condition | ขั้นตอน | คาด |
| - | -------- | ------------- | ----- | -------- |
| VPL-VND-HP-01 | เปิดลิงก์ portal เป็นครั้งแรก | RFQ ถูกสร้างพร้อมเชิญ vendor `V1` (ดู `VPL-PUR-HP-04`); ทราบ `pricelist_url_token` ของ `V1` | Vendor เปิด `/pl/:url_token` | `POST /api/check-pricelist/:url_token` fire; draft `tb_pricelist` ราคาศูนย์ (หนึ่งแถวต่อสินค้าของ template) ถูกสร้างและ return; `pricelist_id` ของแถว invitation ถูก populate |
| VPL-VND-HP-02 | เปิดลิงก์ portal ซ้ำหลังมี pricelist อยู่แล้ว | ต่อจาก VPL-VND-HP-01 | Vendor เปิดลิงก์เดิมอีกครั้ง | การเรียกเดิม return pricelist ที่มีอยู่แทนที่จะสร้างตัวที่สอง |
| VPL-VND-HP-03 | ดูราคาของ draft ที่สร้าง auto | ต่อจาก VPL-VND-HP-01 | Vendor toggle โหมด View | ทุกแถวแสดง `price = 0` / `price_without_tax = 0` จนกว่า Purchaser จะกรอกบนหน้าจอ Price List ภายใน |

## 2. Action ที่ยืนยันแล้วว่าเสีย (Confirmed-Broken)

| # | Scenario | ขั้นตอน | คาด |
| - | -------- | ----- | -------- |
| VPL-VND-BRK-01 | Vendor แก้ราคาแล้วคลิก Save | Toggle โหมด Edit, พิมพ์ราคา, คลิก **Save** | `PATCH /api/external/api/pricelist-external/:url_token` fire **ยืนยันแล้ว:** ไม่มี backend route ที่ตรงกันอยู่จริงที่ไหนใน `carmen-turborepo-backend-v2` — การเรียกล้มเหลว; UI แสดง error message จาก backend ผ่าน toast หรือ fallback เป็น "Failed to save changes" สำหรับ failure ที่ไม่ใช่ `HttpError` |
| VPL-VND-BRK-02 | Vendor คลิก Submit | คลิก **Submit** | `POST /api/external/api/pricelist-external/:url_token/submit` fire **ยืนยันแล้ว:** gap เดียวกัน — ไม่มี backend route ที่ตรงกันอยู่จริง |

## 3. Permission / Authorization

| # | Scenario | พฤติกรรมที่คาด |
| - | -------- | ------------------ |
| VPL-VND-PERM-01 | Vendor เป็น external party ที่ไม่มี Carmen login; RBAC ใน-ระบบเป็น N/A | N/A — ไม่มี login, ไม่มี role และไม่มี permission matrix ให้ test ความถูกต้องของ token คือ gate เดียวบนการเรียกที่ทำงานได้ตัวเดียว และแม้แต่การเรียกนั้นก็ไม่มีการตรวจ expiration, IP หรือ session ใด ๆ (ดู [02-business-rules](/th/inventory/vendor-pricelist/02-business-rules) § 4) |

## 4. Validation / Error

| # | Scenario | Trigger | คาด |
| - | -------- | ------- | -------- |
| VPL-VND-VAL-01 | เปิด portal ด้วย token ที่ไม่ตรงกับแถว invitation ใดเลย | `url_token` ที่ผิดรูปแบบหรือไม่รู้จัก | `checkPricelist()` return not-found error (`Request for pricing detail not found`) |
| VPL-VND-VAL-02 | เปิด portal สำหรับ invitation ที่ template ที่ link ถูก soft-delete | Template `deleted_at IS NOT NULL` | `checkPricelist()` return not-found error สำหรับ template (`Pricelist template not found`) — ยืนยันใน `check-price-list.service.ts` |

## 5. Edge Cases

| # | Scenario | เงื่อนไข | คาด |
| - | -------- | --------- | -------- |
| VPL-VND-EDGE-01 | เปิดลิงก์ portal หลังจาก `end_date` ของ RFQ ผ่านไปแล้ว | `end_date < now()` | **ไม่พบการบังคับใช้** `checkPricelist()` ไม่เคยอ่าน `end_date`; draft ยัง auto-create/return ตามปกติ |
| VPL-VND-EDGE-02 | เปิดลิงก์ portal จาก IP address ใดก็ได้ | ไม่มี allowlist | **ไม่พบการบังคับใช้** ไม่มี IP check ที่ไหนใน call path นี้ |
| VPL-VND-EDGE-03 | ลิงก์เดียวกันถูกเปิดในหลาย browser tab พร้อมกัน | ไม่มี code จำกัด session | **ไม่พบการบังคับใช้** การเรียกของแต่ละ tab สำเร็จอย่างอิสระหรือ return pricelist เดิมที่มีอยู่; ไม่มีขีดจำกัด concurrent-session |

## 6. แหล่งอ้างอิง

- ภาพรวม parent: [04-test-scenarios.md](./04-test-scenarios.md)
- User flow: [03-user-flow-vendor.md](./03-user-flow-vendor.md) — รายละเอียดเต็มของ gap ที่ยืนยันแล้ว
- กติกาทางธุรกิจ: [02-business-rules.md](./02-business-rules.md) § 5.4
- Backend: `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/pricelists/check-pricelist.controller.ts`; `apps/micro-business/src/master/check-price-list/`
- Frontend: `../carmen-inventory-frontend-react/routes/external/pl/`, `hooks/use-price-list-external.ts`
- Sibling: [04-test-scenarios-purchaser.md](./04-test-scenarios-purchaser.md) — วิธีที่ Purchaser แปลง draft ที่สร้าง auto ให้กลายเป็น pricelist ที่มีราคาจริงและ active ในวันนี้
