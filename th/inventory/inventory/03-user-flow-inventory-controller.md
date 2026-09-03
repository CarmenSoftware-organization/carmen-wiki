---
title: คลังสินค้า (Inventory) — User Flow — Inventory Controller
description: Flow ของ Inventory Controller ในโมดูล inventory — การ run review และปิดงวด (period-end)
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, user-flow, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# คลังสินค้า (Inventory) — User Flow — Inventory Controller

> **At a Glance**
> **Persona:** Inventory Controller (ผู้ดำเนินการปิดงวด) &nbsp;·&nbsp; **โมดูล:** [inventory](/th/inventory/inventory) &nbsp;·&nbsp; **Surface ในโมดูลนี้:** หน้าจอ Period End (`/inventory-management/period-end` + `/review`, สิทธิ์ `inventory_management.period_end.view` / `.execute`) และ Transaction Log แบบอ่านอย่างเดียว &nbsp;·&nbsp; **การกระทำสำคัญ:** **Close period** — มี gate จากเอกสารที่ block อยู่ + physical count ที่ต้องเสร็จ
> **การแก้ไข (2026-07-15):** approval queue, count-variance commit console, stock-policy dashboard และ threshold routing ที่เคยเอกสารไว้ในหน้านี้ **ไม่มี source รองรับ** — ไม่มีหน้าจอเหล่านั้นอยู่จริง สิ่งที่เหลือสำหรับ persona นี้ในโมดูลนี้คือการ review/ปิดงวด และการตรวจสอบ ledger

## 1. บทบาทในโมดูลนี้

Persona **Inventory Controller** เป็นเจ้าของความถูกต้องของยอด ณ ขอบเขตงวด (period boundary) ในโมดูลนี้หมายถึง flow ที่เป็นรูปธรรมเพียงหนึ่งเดียว: ขับเคลื่อนเดือนไปสู่สถานะที่ปิดได้ แล้ว run การปิด ระบบบังคับใช้ gate ทั้งหมดฝั่ง server (`validatePeriodEnd` และ re-check อีกครั้งภายใต้ row lock ตอนปิด); หน้าที่ของ Controller คือไล่เคลียร์ review checklist ให้เขียวทั้งหมด ในโมดูลนี้ไม่มี adjustment-approval queue, ไม่มี variance dashboard และไม่มีตัวแก้ไข policy `tb_product_location` ใน routes ของโมดูลนี้ — adjustment เป็นเอกสารที่จบในตัวเองใน [inventory-adjustment](/th/inventory/inventory-adjustment) และการ review การนับอยู่ใน [physical-count](/th/inventory/physical-count)

## 2. จุดเริ่มต้นและ flow หลัก

**จุดเริ่มต้น:** Inventory Management → Period End (`/inventory-management/period-end`)

**Flow หลัก (ปิดงวด, 7 ขั้นตอน):**

1. **เปิดหน้า Period End** การ์ดงวดปัจจุบันแสดงรหัสงวด (YYMM), fiscal year/month, วันเริ่ม/สิ้นสุด, status badge และ note (ถ้ามี) "Current" คืองวดที่เก่าที่สุดที่ `status ∈ {open, locked}` ใต้การ์ดคือ history list ของงวดที่ปิดไปแล้ว
2. **เริ่มการปิด** คลิกปุ่มเริ่มปิดบนการ์ด → `/inventory-management/period-end/review` (`GET /period-ends/review`)
3. **ไล่เคลียร์การ์ดเอกสารที่ block** หนึ่งการ์ดต่อโมดูล — PR, PO, GRN, CN, SR — แต่ละการ์ดแสดงจำนวนเอกสารของงวดและ badge complete/incomplete คลิกการ์ดเปิด dialog แสดงรายการเอกสาร เพื่อให้ Controller ตามเจ้าของเอกสารได้ Complete หมายถึง: PR `approved/completed/voided`; PO `completed/closed/voided`; SR `completed/cancelled/voided`; GRN `committed/voided` (โดย `draft` ก็ non-blocking บน gate ฝั่ง backend ด้วย); CN `completed/cancelled/voided` (โดย `draft` เป็น non-blocking)
4. **ไล่เคลียร์ section physical-count** หนึ่งแถวต่อ location ที่ต้องนับ (`location_type ∈ {inventory, consignment}`, `physical_count_type = yes`, active) พร้อมความคืบหน้า counted/total; คลิกแถวที่กำลังนับอยู่จะ deep-link ไปยัง `/inventory-management/physical-count/{id}/entry` — spot check **ไม่** เป็นส่วนหนึ่งของ gate นี้
5. **ปิดงวด** เมื่อ gate ทั้งหมดเขียว ปุ่ม **Close period** (สไตล์ destructive, มี confirm dialog) จะเปิดใช้งาน; การคลิก fire `POST /period-ends`
6. **การปิด execute แบบ atomic** ภายใน transaction เดียว: lock `FOR UPDATE` + re-validate; lot carry-over (rows `CLOSE-…` ที่ zero ยอด และ rows `OPEN-…` ที่สร้างใหม่ในงวดถัดไปที่ auto-provision; บน tenant ที่ใช้ average method ยังรวม bucket `tb_period_snapshot` ด้วย); `tb_period.status = closed`; rows `tb_physical_count_period` ของงวดถูก mark เป็น `completed`
7. **ตรวจสอบบน ledger** filter Transaction Log ด้วย `inventory_doc_type IN ('close','open')` — การปิดงวดเองคือคู่ ledger event ที่ audit ได้

## 3. ทางแยกการตัดสินใจ (Decision Branches)

- **การ์ดโมดูลใดยัง incomplete** — เปิด dialog ของการ์ดนั้น ระบุเอกสารที่ block แล้วตามเจ้าของเอกสารในโมดูลต้นทาง; โมดูลนี้ไม่มี bulk action สำหรับเอกสารเหล่านั้น
- **การ์ดแสดงเอกสารเป็นศูนย์แต่ยัง incomplete** — quirk ฝั่ง frontend: `is_complete = count > 0 && …` ดังนั้นโมดูลที่ว่างเปล่าจะอ่านเป็น incomplete แม้ gate ฝั่ง backend จะผ่าน; เป็น discrepancy ที่ทราบแล้วเมื่อทดสอบงวดว่าง
- **`Cannot close period: incomplete documents {…}`** — มีเอกสาร block โผล่ขึ้นระหว่างการโหลดหน้า review กับการคลิก; refresh แล้วแก้ไข
- **`Period already closed`** — session อื่นชนะ race การปิด; refresh
- **งวดปัจจุบันแสดง `locked`** — การ lock มาจาก service [system-config/period](/th/inventory/system-config/period); หน้าจอนี้ยังถือว่างวดนั้นเป็น current และปิดได้

## 4. จุดสิ้นสุด / การส่งต่อ

- **ปิดงวดสำเร็จ** — งวดถัดไปเปิดอยู่แล้ว (`ensureNextPeriod`); movement ใหม่จะ stamp เข้างวดนั้นโดยอัตโนมัติ ส่งต่อกลับสู่งานประจำวัน
- **การปิดถูก block** — ส่งต่อไปยังเจ้าของโมดูลต้นทาง (approver ของ PR/PO/SR, ผู้ process GRN/CN, ผู้นับ) จนกว่า gate จะเคลียร์

## 5. แหล่งอ้างอิง

- ภาพรวม parent: [03-user-flow](/th/inventory/inventory/03-user-flow)
- Sibling: [period-end](/th/inventory/inventory/period-end) — ตาราง gate เต็ม, error strings และรายละเอียดกระบวนการระดับ dev
- Sibling: [02-business-rules](/th/inventory/inventory/02-business-rules) — `INV_POST_009` / `INV_POST_010` (close/open), `INV_CALC_008` / `INV_CALC_009` (การปิดแบบ FIFO vs average), `INV_AUTH_008` (gate `period_end.execute`)
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/period-end/` (`pe-component.tsx`, `pe-review.tsx`, `pe-documents-dialog.tsx`, `pe-history.tsx`)
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/`
- ที่เกี่ยวข้อง: [physical-count](/th/inventory/physical-count) (gate การนับ), [inventory-adjustment](/th/inventory/inventory-adjustment) (การแก้ไขยอด), [system-config/period](/th/inventory/system-config/period) (นิยามงวดและการ lock)
