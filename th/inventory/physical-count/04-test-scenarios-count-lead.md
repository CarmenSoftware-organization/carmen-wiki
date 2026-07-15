---
title: การนับสต๊อกประจำงวด (Physical Count) — Test Scenarios — หน้ารายการ
description: Test case ของหน้ารายการสำหรับโมดูลการนับสต๊อกประจำงวด
published: true
date: 2026-07-15T17:56:09.000Z
tags: physical-count, test-scenarios, count-lead, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# การนับสต๊อกประจำงวด (Physical Count) — Test Scenarios — หน้ารายการ

> **At a Glance**
> **หน้าจอ:** `physical-count` (`pc-component.tsx`) &nbsp;·&nbsp; **โมดูล:** [physical-count](/th/inventory/physical-count) &nbsp;·&nbsp; **Role:** ผู้ใช้ใดก็ตามที่ถือ `inventory_management.physical_count` (role เดียวกับ [04-test-scenarios-counter.md](/th/inventory/physical-count/04-test-scenarios-counter))
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **ความครอบคลุม E2E:** ไม่มี Playwright spec ของ `physical-count`; scenario เป็น manual/planned

## 1. ขอบเขต

Scenario ด้านล่างใช้ action ของหน้ารายการที่ catalogue ใน [physical-count/03-user-flow-count-lead](/th/inventory/physical-count/03-user-flow-count-lead) § 3 — การ auto-provision period, การ filter, และการเริ่ม/ทำต่อการนับ

## 2. Functional — Happy Path

| # | Scenario | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------------- | ---------------- |
| L-F-01 | โหลดหน้ารายการสำหรับงวดบัญชีใหม่เอี่ยม | ยังไม่มี `tb_physical_count_period` สำหรับ `tb_period` ที่เปิดอยู่ปัจจุบัน | `GET /physical-count-periods/current` auto-create ที่ `status: draft`; รายการสถานที่ render |
| L-F-02 | เริ่มการนับสำหรับสถานที่ที่ยังไม่เริ่มและจำเป็น | สถานที่มี `location_type ∈ {inventory, consignment}`, `physical_count_type = yes`, `is_active = true`; ไม่มี `tb_physical_count` สำหรับ period นี้; period ของ physical-count เป็น `counting` แล้ว | `POST /physical-counts` สำเร็จ; เอกสารสร้างที่ `in_progress`; navigate ไป `/:id/entry` |
| L-F-03 | ทำต่อสถานที่ที่ in-progress | สถานที่มี `tb_physical_count` ที่ `in_progress` อยู่แล้ว | Navigate ตรงไป `/:id/entry`; ไม่มีเอกสารใหม่สร้าง |
| L-F-04 | Filter ด้วย KPI tile | คลิก tile "In Progress" | เหลือเฉพาะการ์ดสถานที่ที่ in-progress ที่มองเห็น |
| L-F-05 | Search ด้วยชื่อหรือรหัส | พิมพ์ชื่อ/รหัสสถานที่บางส่วน | รายการแคบลงตามที่ตรงกัน ฝั่ง client |
| L-F-06 | รวมสถานที่ที่ไม่นับ | เช็ค "Include not-counted locations" | สถานที่ที่ flag `physical_count_type = no` ถูกเพิ่มเข้ารายการ ยังคงจำกัดที่สถานที่ inventory/consignment ที่ active |
| L-F-07 | สลับไป period ก่อนหน้า | เลือก period ที่ปิดแล้วจาก dropdown period | ป้ายแสดง "Previous Period"; สถานที่ของ period นั้น render โดยผลจริงคืออ่านอย่างเดียว (การเริ่มการนับ *ใหม่* กับชุดเอกสารของ period ที่ปิดแล้วไม่ใช่ส่วนของ flow ปกติของหน้านี้) |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------------- | ---------------- |
| L-R-01 | ผู้ใช้ที่ไม่มี `inventory_management.physical_count` เปิดหน้ารายการ | Permission ไม่ได้รับ | การเข้าถึงถูก reject ตามกลไก permission-gate ทั่วไปที่ใช้ร่วมกันทั่วผลิตภัณฑ์; ไม่มี override เฉพาะโมดูล |

## 4. Validation — Negative Test

| # | กฎ | Scenario | Error ที่คาดหวัง |
| - | ---- | -------- | -------------- |
| L-V-01 | `PHC_VAL_001` | เริ่มการนับขณะ period ของ physical-count ยังเป็น `draft` (สถานะที่ถูก auto-provision ไว้) | `POST /physical-counts` reject ด้วย `"Physical Count Period is not in counting status"` — ดูช่องว่างที่ยืนยันแล้วใน [03-user-flow.md](./03-user-flow.md) § 2 (ไม่พบ code path ที่เปลี่ยน period จาก `draft` เป็น `counting`) |
| L-V-02 | `PHC_VAL_002` | เริ่มการนับสำหรับสถานที่ที่ถูก soft-delete ไปแล้ว | Reject ด้วย error location-not-found |

## 5. Edge Case

| # | Scenario | ผลที่คาดหวัง |
| - | -------- | ---------------- |
| L-E-01 | คลิกการ์ดสถานที่ที่ completed | ไม่มี action ทำงาน — การ์ด render เป็นป้ายธรรมดา ไม่ใช่ปุ่ม เมื่อ `physical_count_status = completed`; ปัจจุบันไม่มี route จากหน้านี้เข้าไปดู detail ของการนับที่ completed |
| L-E-02 | เริ่มการนับสองครั้งติดกันสำหรับสถานที่เดียวกัน (double-click) | Path resume แบบ idempotent ของ `create()` (`PHC_VAL_003`) หมายความว่า call ที่สองคืน `id`/`doc_version` ของเอกสารเดียวกันแทนที่จะสร้างซ้ำ |
| L-E-03 | สถานที่ที่ไม่มีสินค้าเข้าเงื่อนไขเลย | `product_total = 0` ตอนสร้าง; การนับยังถึง `completed` ได้ทันทีเพราะไม่มีอะไรต้องนับและไม่มีบรรทัดใดบล็อก `PHC_VAL_004` |

## 6. แหล่งอ้างอิง

- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/physical-count/pc-component.tsx`
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count/physical-count.service.ts` (`create`), `.../physical-count-period/physical-count-period.service.ts` (`findCurrent`)
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec physical-count
- ที่เกี่ยวข้อง: [physical-count/03-user-flow-count-lead](/th/inventory/physical-count/03-user-flow-count-lead), [physical-count/02-business-rules](/th/inventory/physical-count/02-business-rules) (`PHC_VAL_001`–`003`, `PHC_AUTH_001`), [physical-count/04-test-scenarios](/th/inventory/physical-count/04-test-scenarios) (scenario end-to-end)
