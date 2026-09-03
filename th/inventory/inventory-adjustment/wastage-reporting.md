---
title: รายงานของเสีย (Wastage Reporting)
description: หน้าจอ Store Operations สำหรับบันทึกการสูญเสีย spoilage/breakage/expiry — ปัจจุบันขับเคลื่อนด้วย mock data เท่านั้น ไม่มี backend implementation
published: true
date: 2026-07-15T17:02:22.000Z
tags: inventory-adjustment, wastage, loss, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# รายงานของเสีย (Wastage Reporting)

> **At a Glance**
> **ตำแหน่ง:** Store Operations → Wastage Reporting (`/store-operation/wastage-reporting`) — **ไม่ใช่** ส่วนหนึ่งของ route ของโมดูล Inventory Adjustment เอง &nbsp;·&nbsp; **สถานะ:** mock data เท่านั้น — `hooks/use-wastage-report.ts` มี comment ตรงตัว `// ── TODO: เปลี่ยนเป็น API จริงเมื่อ backend พร้อม ──` ทุกการเรียก list/create/update/delete ทำงานกับ fixture array ในหน่วยความจำ (`wr-mock-data.ts`) พร้อม delay จำลอง &nbsp;·&nbsp; **Backend:** ไม่มีโมเดล Prisma แบบ `tb_wastage_report`, service หรือ controller ที่ไหนใน `carmen-turborepo-backend-v2` เลย

![Wastage Reporting screen](/screenshots/inventory-adjustment/wastage-reporting.png)

## 1. คืออะไรและใครใช้

หน้านี้เวอร์ชันก่อนหน้าบรรยาย Wastage Reporting ว่าเป็น "แถว `tb_stock_out` ที่ `adjustment_type_id` resolve เป็น reason แบบ wastage" — นั่นไม่ถูกต้อง Wastage Reporting เป็น type ของ frontend ของตัวเอง (`WastageReport` ใน `types/wastage-reporting.ts`) มี enum สถานะของตัวเอง (`pending`/`approved`/`rejected` — **ไม่ใช่** `enum_doc_status`), มีฟิลด์เลขที่เอกสารของตัวเอง (`wr_no`) และมีรูปทรง item ของตัวเอง (`unit_id`/`unit_name`/`unit_cost`/`loss_value` — ไม่มี `cost_per_unit`, ไม่มี lot reference, ไม่มี `adjustment_type_id` เลย) ไม่ได้แชร์ schema, service หรือ endpoint ใด ๆ กับ `tb_stock_in`/`tb_stock_out` ของโมดูล Inventory Adjustment ถูกอ้างอิงไขว้จากโมดูลนี้เพื่อความสะดวก (เป็นหน้าจอบันทึกการสูญเสีย ใกล้เคียงเชิงแนวคิดกับ write-off ของ Stock-Out) แต่ไม่ใช่ variant ของมัน

ที่สำคัญกว่านั้น: **feature ทั้งหมดในปัจจุบันเป็น mock data** `useWastageReport()`, `useWastageReportById()`, `useCreateWastageReport()`, `useUpdateWastageReport()` และ `useDeleteWastageReport()` ทั้งหมดอ่านจากและ "เขียน" ไปยัง array `wrMockData` ที่ hardcode ในหน่วยความจำ จำลอง network delay (`await new Promise((r) => setTimeout(r, 300))`) แทนที่จะเรียก API จริง Mutation Create/Update/Delete resolve `{ success: true }` และ invalidate query cache แต่ไม่ persist อะไรเลย — การรีเฟรชหน้าเว็บกลับไปเป็นข้อมูล fixture เดิม รูปแบบนี้เหมือนกับ "หน้าจอขับเคลื่อนด้วย mock data พร้อม TODO comment ภาษาไทย" ที่พบแล้วบนหน้าจอ Stock Replenishment ของ Store Requisition ในรอบ resync ก่อนหน้า

## 2. งานทั่วไป

| งาน | ตำแหน่ง | หมายเหตุ |
|---|---|---|
| บันทึกรายการของเสีย | Store Operation → Wastage Reporting → **New** | เลือกตำแหน่ง, reason (ฟิลด์ `reason` แบบข้อความอิสระ ไม่ใช่การอ้างอิง `tb_adjustment_type`), บรรทัดสินค้า (`qty`, `unit_id`, `unit_cost`) |
| แสดงรายการ / ค้นหา wastage report | Store Operation → Wastage Reporting | ค้นหาฝั่ง client บน `wr_no`/`location_name`/`reason`/`reportor_name` และตัวกรอง `status` ทั้งคู่รันกับ array mock ในหน่วยความจำ |
| ดูรายละเอียด report | คลิกแถว | อ่านจาก `wrMockData` ตาม id ไม่ใช่เอกสารที่ live |

## 3. รูปทรงข้อมูล (type ของ frontend ไม่มี backend model)

ที่มา: `types/wastage-reporting.ts` ไม่มี Prisma schema สำหรับสิ่งนี้เลย — รูปทรงด้านล่างมีอยู่เฉพาะใน TypeScript type ของ frontend และ fixture mock

| ฟิลด์ | Type | หมายเหตุ |
|---|---|---|
| `id` | `string` | id ของ mock fixture (เช่น `wr-001`) ไม่ใช่ UUID ของฐานข้อมูล |
| `wr_no` | `string` | เลขที่เอกสารที่แสดง (เช่น `WR-2602-0001`) เขียนด้วยมือใน fixture ไม่ได้สร้างโดย running-code service ใด |
| `date`, `location_id`, `location_name` | `string` | ฟิลด์ธรรมดา ไม่มีการบังคับ FK (ไม่มี backend ให้บังคับ) |
| `reason` | `string` | ข้อความอิสระ — ไม่ได้อ้างอิง `tb_adjustment_type` หรือตาราง master data ใด |
| `reportor_id`, `reportor_name` | `string` | ผู้ใช้ที่บันทึกรายการ |
| `status` | `"pending" \| "approved" \| "rejected"` | enum สามค่าที่แยกต่างหาก ไม่เกี่ยวข้องกับ `enum_doc_status` |
| `qty_sum`, `loss_value` | `number` | ยอด roll-up ที่คำนวณจาก fixture |
| `items[]` (`WastageReportItem`) | — | `product_id`, `product_name`, `product_code`, `qty`, `unit_id`, `unit_name`, `unit_cost`, `loss_value` — ไม่มีชื่อ `cost_per_unit`/`total_cost` ไม่มี lot reference |
| `attachments[]` (`WastageReportAttachment`) | — | `id`, `name`, `url` — array ฟิลด์ธรรมดาบน report ไม่ใช่ตาราง comment แยกต่างหาก |

## 4. Edge Cases

- **ไม่มีอะไร persist** ทุก mutation (`useCreateWastageReport`, `useUpdateWastageReport`, `useDeleteWastageReport`) resolve ความสำเร็จปลอมหลัง delay คงที่ และ invalidate เพียง query cache ฝั่ง client — ไม่มี round-trip ไปยัง server และไม่มีการเขียนฐานข้อมูลจริง
- **ไม่ใช่ variant ของ Stock-Out** ไม่แชร์ schema, endpoint หรือการตรวจสอบใดกับ `tb_stock_out` — อย่านำกฎของ Inventory Adjustment (§ [02 — กติกาทางธุรกิจ](/th/inventory/inventory-adjustment/02-business-rules)) มาใช้กับหน้าจอนี้
- **Permission gate เป็นของจริง แต่ไม่เกี่ยวข้องกับข้อมูลของ feature** nav entry ของหน้าจอนี้ถูก gate ด้วย `PERMISSIONS.inventory_management.stock_out.view` (`constant/module-list.ts`) — การตรวจสอบสิทธิ์จริง — แต่ permission key นั้นไม่มีการใช้อื่นที่ไหนใน route ของโมดูล Inventory Adjustment เองเลย (ดู [02 — กติกาทางธุรกิจ](/th/inventory/inventory-adjustment/02-business-rules) § 4)

## 5. ส่วนอ้างอิง

- [inventory-adjustment](/th/inventory/inventory-adjustment) — โมดูลที่อ้างอิงไขว้; ไม่แชร์ schema หรือโค้ดกับหน้าจอนี้
- [master-data/adjustment-type](/th/inventory/master-data/adjustment-type) — master ของ reason code จริงที่หน้าจอนี้**ไม่ได้**ใช้

## 6. แหล่งอ้างอิง

- **Frontend:** `../carmen-inventory-frontend-react/routes/store-operation/wastage-reporting/` (`wr-form.tsx`, `wr-form-schema.ts`, `wr-mock-data.ts`), `hooks/use-wastage-report.ts`, `types/wastage-reporting.ts`
- **Backend:** ไม่พบ — ไม่มีโมเดล Prisma `tb_wastage_report` (หรือชื่อใกล้เคียง), service หรือ controller ที่ไหนใน `../carmen-turborepo-backend-v2/` เลย
- **Permission:** `constant/module-list.ts` gate nav entry ด้วย `PERMISSIONS.inventory_management.stock_out.view`
