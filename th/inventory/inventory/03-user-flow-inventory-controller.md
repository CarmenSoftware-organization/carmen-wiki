---
title: คลังสินค้า (Inventory) — User Flow — Inventory Controller
description: Flow ของ Inventory Controller ในโมดูล inventory — การ run review และปิดงวด (period-end)
published: true
date: '2026-09-23T01:30:00.000Z'
tags: inventory, user-flow, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# คลังสินค้า (Inventory) — User Flow — Inventory Controller

> **At a Glance**
> **Persona:** Inventory Controller (ผู้ดำเนินการปิดงวด) &nbsp;·&nbsp; **โมดูล:** [inventory](/th/inventory/inventory) &nbsp;·&nbsp; **Surface ในโมดูลนี้:** หน้าจอ Period End (`/inventory-management/period-end` + `/review`, สิทธิ์ `inventory_management.period_end.view` / `.execute`) และ Transaction Log แบบอ่านอย่างเดียว &nbsp;·&nbsp; **การกระทำสำคัญ:** **Start Period Close** (เปิดรอบการนับ — มี gate จากเอกสารเคลื่อนไหวสต๊อกที่ยังเปิดอยู่) และ **Close Period** (มี gate จาก SR/GRN/CN/SI/SO กลางทาง + physical count ที่ต้องเสร็จ)
> **การแก้ไข (2026-07-15):** approval queue, count-variance commit console, stock-policy dashboard และ threshold routing ที่เคยเอกสารไว้ในหน้านี้ **ไม่มี source รองรับ** — ไม่มีหน้าจอเหล่านั้นอยู่จริง สิ่งที่เหลือสำหรับ persona นี้ในโมดูลนี้คือการ review/ปิดงวด และการตรวจสอบ ledger

## 1. บทบาทในโมดูลนี้

Persona **Inventory Controller** เป็นเจ้าของความถูกต้องของยอด ณ ขอบเขตงวด (period boundary) ในโมดูลนี้หมายถึง flow ที่เป็นรูปธรรมเพียงหนึ่งเดียว: ขับเคลื่อนเดือนไปสู่สถานะที่ปิดได้ แล้ว run การปิด ระบบบังคับใช้ gate ทั้งหมดฝั่ง server (`validatePeriodEnd` และ re-check อีกครั้งภายใต้ row lock ตอนปิด); หน้าที่ของ Controller คือไล่เคลียร์ review checklist ให้เขียวทั้งหมด ในโมดูลนี้ไม่มี adjustment-approval queue, ไม่มี variance dashboard และไม่มีตัวแก้ไข policy `tb_product_location` ใน routes ของโมดูลนี้ — adjustment เป็นเอกสารที่จบในตัวเองใน [inventory-adjustment](/th/inventory/inventory-adjustment) และการ review การนับอยู่ใน [physical-count](/th/inventory/physical-count)

## 2. จุดเริ่มต้นและ flow หลัก

**จุดเริ่มต้น:** Inventory Management → Period End (`/inventory-management/period-end`)

**Flow หลัก (ปิดงวด, 7 ขั้นตอน):**

1. **เปิดหน้า Period End** การ์ดงวดปัจจุบันแสดงรหัสงวด (YYMM), fiscal year/month, วันเริ่ม/สิ้นสุด, status badge และ note (ถ้ามี) "Current" คืองวดที่เก่าที่สุดที่ `status ∈ {open, locked}` ใต้การ์ดคือ history list ของงวดที่ปิดไปแล้ว
2. **เริ่มรอบการนับ** คลิก **Start Period Close** บนการ์ดแล้วยืนยัน dialog การกระทำที่ย้อนกลับไม่ได้ → `POST /period-ends/start-counting` ถ้ามี GRN ที่ลงวันที่ในงวดใดไม่ใช่ `committed`/`voided`, stock-in / stock-out ใดไม่ใช่ `completed`/`cancelled`/`voided` หรือ SR ที่มีเลขที่ใดยังเป็น `draft`/`in_progress` การเรียกจะคืน 422 และ dialog **"Finish these documents first"** จะ list เอกสารเหล่านั้นพร้อมลิงก์; มิฉะนั้น `tb_physical_count_period` ของงวดจะกลายเป็น `counting` และแอป navigate ไป `/inventory-management/period-end/review` (`GET /period-ends/review`) เมื่อรอบเปิดแล้ว ปุ่มเดียวกันจะอ่านว่า **Continue Counting** และแค่ navigate
3. **ไล่เคลียร์การ์ดเอกสาร** หนึ่งการ์ดต่อโมดูล — PR, PO, GRN, CN, SR, SI, SO — แต่ละการ์ดแสดงจำนวนเอกสารของงวดและ badge Complete/Incomplete คลิกการ์ดเปิด dialog แสดงรายการเอกสาร (ลิงก์ไปหน้าจอต้นทาง) เพื่อให้ Controller ตามเจ้าของเอกสารได้ Complete หมายถึง: PR `approved/completed/voided`; PO `completed/closed/voided`; SR `completed/cancelled/voided`; GRN `committed/voided`; CN `completed/cancelled/voided`; SI/SO `completed/cancelled/voided` เฉพาะ SR / GRN / CN / SI / SO เท่านั้นที่ป้อน gate ของการปิด — การ์ด PR และ PO เป็นเพียงข้อมูล
4. **ไล่เคลียร์ section physical-count** หนึ่งการ์ดต่อ location ที่ต้องนับ (`location_type ∈ {inventory, consignment}`, `physical_count_type = yes`, active) พร้อมความคืบหน้า counted/total; คลิกการ์ดเปิดการนับของ location นั้น — สร้างให้ (`POST /physical-counts`) ถ้ายังไม่มี — ที่ `/inventory-management/physical-count/{id}/entry` การ์ดคง disable ("Counting has not started for this period yet.") จนกว่าขั้นที่ 2 จะรันแล้ว spot check **ไม่** เป็นส่วนหนึ่งของ gate นี้
5. **ปิดงวด** เมื่อ payload ของ review รายงาน `can_close: true` ปุ่ม **Close Period** (สไตล์ destructive, มี confirm dialog) จะเปิดใช้งาน; การคลิก fire `POST /period-ends`
6. **การปิด execute แบบ atomic** ภายใน transaction เดียว: lock `FOR UPDATE` + re-validate; lot carry-over (rows `close` ที่ zero ยอดทุก lot ที่งวดมี `end_at ≤` งวดนี้ และ rows `open` ที่สร้างใหม่ในงวดถัดไปที่ auto-provision ภายใต้ lot ใหม่ `{location_code}{YYMM}{seq4}`; บน tenant ที่ใช้ average method ยังรวม bucket `tb_inventory_period_snapshot` ด้วย); `tb_inventory_period.status = closed`; rows `tb_physical_count_period` ของงวดถูก mark เป็น `completed`
7. **ตรวจสอบบน ledger** filter Transaction Log ด้วย `inventory_doc_type IN ('close','open')` — การปิดงวดเองคือคู่ ledger event ที่ audit ได้

## 3. ทางแยกการตัดสินใจ (Decision Branches)

- **การ์ดโมดูลใดยัง incomplete** — เปิด dialog ของการ์ดนั้น ระบุเอกสารที่ block แล้วตามเจ้าของเอกสารในโมดูลต้นทาง; โมดูลนี้ไม่มี bulk action สำหรับเอกสารเหล่านั้น
- **การ์ดแสดงเอกสารเป็นศูนย์และอ่านว่า Incomplete** — เป็นเพียงเรื่อง cosmetic: `is_complete` คือ `count > 0 && …` แต่ตั้งแต่ 2026-08-27 ปุ่มถูกขับด้วย `can_close` ของ backend ดังนั้นโมดูลที่ว่างเปล่าไม่ block การปิดอีกต่อไป
- **`Cannot close period: {total} document(s) are incomplete`** (`PERIOD_END_CLOSE_BLOCKED`, 422) — มีเอกสาร block โผล่ขึ้นระหว่างการโหลดหน้า review กับการคลิก; refresh แล้วแก้ไข
- **`Cannot start counting: {total} document(s) in this period are still open`** (`PERIOD_END_START_COUNTING_BLOCKED`, 422) — render เป็น dialog "Finish these documents first"; commit/void GRN / SI / SO / SR ที่ list ไว้ก่อน
- **`Counting cannot be started for this period`** (`PERIOD_END_COUNTING_NOT_ALLOWED`, 409) — ตอนปิด: session อื่นชนะ race การปิด; ตอนเริ่ม: งวดไม่ `open` อีกต่อไปหรือรอบ `completed` ไปแล้ว refresh
- **งวดปัจจุบันแสดง `locked`** — การ lock มาจาก service [system-config/period](/th/inventory/system-config/period); หน้าจอนี้ยังถือว่างวดนั้นเป็น current และปิดได้

## 4. จุดสิ้นสุด / การส่งต่อ

- **ปิดงวดสำเร็จ** — งวดถัดไปเปิดอยู่แล้ว (`ensureNextPeriod`); เอกสารที่ลงวันที่ในงวดนั้น post เข้างวดนั้น เอกสารที่ยังลงวันที่ในงวดที่ปิดแล้วถูก reject ตอน create/commit ของ SI/SO/GRN ส่งต่อกลับสู่งานประจำวัน
- **การเริ่มหรือการปิดถูก block** — ส่งต่อไปยังเจ้าของโมดูลต้นทาง (ผู้ process GRN/CN, ผู้เขียน SI/SO, approver ของ SR, ผู้นับ) จนกว่า gate จะเคลียร์

## 5. แหล่งอ้างอิง

- ภาพรวม parent: [03-user-flow](/th/inventory/inventory/03-user-flow)
- Sibling: [period-end](/th/inventory/inventory/period-end) — ตาราง gate เต็ม, error strings และรายละเอียดกระบวนการระดับ dev
- Sibling: [02-business-rules](/th/inventory/inventory/02-business-rules) — `INV_POST_009` / `INV_POST_010` (close/open), `INV_CALC_008` / `INV_CALC_009` (การปิดแบบ FIFO vs average), `INV_AUTH_008` (gate `period_end.execute`)
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/period-end/` (`pe-component.tsx`, `pe-review.tsx`, `pe-documents-dialog.tsx`, `pe-start-blocked-dialog.tsx`, `pe-history.tsx`, `use-period-end.ts`)
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/`
- ที่เกี่ยวข้อง: [physical-count](/th/inventory/physical-count) (gate การนับ), [inventory-adjustment](/th/inventory/inventory-adjustment) (การแก้ไขยอด), [system-config/period](/th/inventory/system-config/period) (นิยามงวดและการ lock)
