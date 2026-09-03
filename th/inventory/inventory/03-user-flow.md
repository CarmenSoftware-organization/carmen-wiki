---
title: คลังสินค้า (Inventory) — User Flow
description: วงจรชีวิตของ movement และไฟล์ flow เฉพาะ persona สำหรับ inventory
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, user-flow, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# คลังสินค้า (Inventory) — User Flow

> **At a Glance**
> **โมดูล:** [inventory](/th/inventory/inventory) &nbsp;·&nbsp; **Personas:** Store Keeper (ตรวจสอบ ledger) &nbsp;·&nbsp; Inventory Controller (ปิดสิ้นงวด) &nbsp;·&nbsp; Finance + Audit / Config (หน้าแก้ไข — ไม่มี surface เหล่านั้นอยู่จริง)
> **วงจรชีวิต workflow:** ขับเคลื่อนด้วย movement — แต่ละ `tb_inventory_transaction` ถูกเขียนแบบ posted แล้วโดยโมดูล source ของมัน (ไม่มี draft → committed บน movement) วงจรชีวิตต่องวดอยู่บน `tb_period.status`: `open` → `closed` ผ่าน action Close ที่นี่ (`locked` ถูก set ที่อื่น) การแก้ไขคือ transaction ใหม่ผ่านเอกสาร source ใหม่; row ไม่เคยถูกแก้ไข

## 1. ภาพรวม

หน้านี้คือ **จุดเข้าภาพรวม** สำหรับชุด user-flow ของโมดูล `inventory` Inventory ไม่ปกติเมื่อเทียบกับโมดูลเอกสารพี่น้อง — ไม่มีเอกสาร workflow ที่วงจรชีวิต draft → saved → committed เล่นบน พื้นผิว UI ของโมดูลมีเพียงสองหน้าจอพอดี: **Transaction Log** แบบ read-only (`/inventory-management/transaction`) และ **Period End** (`/inventory-management/period-end` + `/review`) ทุก ledger row ถูกเขียนโดยโมดูล source ต้นน้ำ ณ posting event ของมัน — GRN **save**, การ approve SR ที่ stage สุดท้าย, การ complete ของ inventory-adjustment, การ complete ของ credit-note — และการปิดงวดเองก็เขียน row `close`/`open` ลง ledger เดียวกัน

Section 2 อธิบาย state machine สองอัน (ระดับ movement — degenerate; ระดับ period — อันที่มีสาระ) Section 3 เป็นสารบัญไฟล์ persona: สองไฟล์อธิบาย flow จริงเหนือสองหน้าจอ; อีกสองไฟล์เป็นหน้าแก้ไข (correction page) สำหรับ persona ที่ surface ที่เคยบันทึกไว้ก่อนหน้าได้รับการยืนยันแล้วว่าไม่มีอยู่ในผลิตภัณฑ์

## 2. วงจรชีวิตของ Movement และ Period

### 2.1 Transitions ระดับ Movement

| From state | Action | To state | อนุญาตสำหรับ | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | post จากเอกสาร source | `posted` | Posting event ของโมดูล source (GRN save, การ approve SR ที่ stage สุดท้าย, Submit ของ inventory-adjustment, การ complete ของ credit-note, การปิดงวด) | เอกสาร source ไปถึงสถานะ posting ของมัน; การบริโภคขาออกผ่านการตรวจ balance (`Insufficient stock…` ยกเว้น path ของ credit-note ซึ่งบันทึก `diff_amount`); `at_period`/`period_id` ถูก stamp จาก **งวด open ปัจจุบัน** โดยไม่สนวันที่เอกสาร |
| `posted` | (ไม่มี action ต่อ) | `posted` | — | ปลายทางและ immutable ไม่มี endpoint reversal, ไม่มี endpoint แก้ไข; โค้ดปัจจุบันไม่เคย set `deleted_at` การแก้ไขคือ transaction **ใหม่** ที่ post โดยเอกสาร source ใหม่ (credit note, stock-in/stock-out) |

### 2.2 Transitions ระดับ Period

| From state | Action | To state | อนุญาตสำหรับ | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | สร้างงวด | `open` | `ensureNextPeriod` ระหว่างการปิดครั้งก่อน หรือหน้าจอ admin ของงวด ([system-config/period](/th/inventory/system-config/period)) | หนึ่งงวดต่อ YYMM (`@@unique([fiscal_year, fiscal_month, deleted_at])`) |
| `open` | รับ movements | `open` | Role ที่ทำธุรกรรมทั้งหมด (ผ่านโมดูล source) | ทุก movement ใหม่ stamp เข้างวดนี้ — รวมถึงแบบ "backdate" (ถูก re-date ไม่ใช่ reject) |
| `open` (หรือ `locked`) | **Close period** บน `/period-end/review` | `closed` | ผู้ใช้ใดก็ได้ที่มี `inventory_management.period_end.execute` | Gate เอกสารที่ block เคลียร์ทั้งหมด (PR/PO/SR ไม่ `in_progress` กลาง workflow; GRN อยู่ใน `{draft, committed, voided}`; CN อยู่ใน `{draft, completed, cancelled, voided}`; ทุก location ที่กำหนดนับครบ) รันแบบ atomic ภายใต้ lock `FOR UPDATE` พร้อม re-validation; เขียนการยกยอด lot (`CLOSE-…`/`OPEN-…`) และ — เฉพาะ tenant แบบ average method — row `tb_period_snapshot`; provision งวด `open` ถัดไปอัตโนมัติ; mark row `tb_physical_count_period` เป็น completed |
| `closed` | (ไม่มี transition ในโมดูลนี้) | — | — | ไม่มี endpoint reopen ที่นี่ |
| any | lock / unlock | `locked` / — | Period service ที่อยู่หลัง [system-config/period](/th/inventory/system-config/period) | นอก scope ของโมดูลนี้; หมายเหตุ `findCurrent` ถือว่า `locked` เป็นงวดปัจจุบัน งวดที่ lock จึงยังแสดงและปิดได้จากที่นี่ |

## 3. สารบัญ Persona

- [Store Keeper](/th/inventory/inventory/03-user-flow-store-keeper) — ตรวจสอบการ post บน Transaction Log แบบ read-only; ไม่ author อะไรในโมดูลนี้ (adjustment อยู่ใน [inventory-adjustment](/th/inventory/inventory-adjustment), การนับอยู่ใน [physical-count](/th/inventory/physical-count) / [spot-check](/th/inventory/spot-check))
- [Inventory Controller](/th/inventory/inventory/03-user-flow-inventory-controller) — ทำงานกับ checklist review ของการปิดสิ้นงวดจนเขียวและรันการปิด (`inventory_management.period_end.execute`)
- [Finance](/th/inventory/inventory/03-user-flow-finance) — **หน้าแก้ไข**: ไม่มี Finance role, การกระทบยอด GL หรือ flow การ lock งวดอยู่จริง
- [Audit / Config](/th/inventory/inventory/03-user-flow-audit-config) — **หน้าแก้ไข**: ไม่มี workspace audit ของ inventory หรือ console configuration อยู่จริง; configuration จริงอยู่ใน master-data / system-config / access-control

## 4. การส่งต่อข้าม Persona

| From | Trigger | To | สถานะระบบ ณ การส่งต่อ |
| ---- | ------- | -- | ----------------------- |
| ผู้ปฏิบัติงานโมดูล source (ผู้รับ GRN, ผู้อนุมัติ SR, ผู้ทำ adjustment) | Posting event fire | Store Keeper (การตรวจสอบ) | Ledger rows ถูกเขียนแล้ว; `parent_document_no` resolve ได้บน Transaction Log |
| Inventory Controller | การ์ดเอกสารที่ block บนหน้า review เป็น incomplete | เจ้าของโมดูล source | เอกสารแสดงใน dialog ต่อโมดูล; งวดคง `open` จนกว่าจะแก้เสร็จ |
| Inventory Controller | แถว physical-count เป็น incomplete | ผู้นับ | Deep-link ไป `/inventory-management/physical-count/{id}/entry` |
| Inventory Controller | **Close period** สำเร็จ | ทุกคน | `tb_period.status = closed`; งวดถัดไป `open`; movement ใหม่ stamp เข้างวดนั้นอัตโนมัติ |

## 5. แหล่งอ้างอิง

- Sibling: [01-data-model](/th/inventory/inventory/01-data-model) — enums แบบ canonical และ catalogue ของความแตกต่าง (รวมการแก้ไข no-GL และ costing-method ระดับ BU ที่หน้านี้พึ่งพา)
- Sibling: [02-business-rules](/th/inventory/inventory/02-business-rules) — `INV_VAL_005`/`INV_VAL_008` (balance และการ stamp งวด), `INV_POST_009`/`INV_POST_010` (close/open), `INV_AUTH_008` (`period_end.execute`)
- Sibling: [transaction](/th/inventory/inventory/transaction) และ [period-end](/th/inventory/inventory/period-end) — สองหน้าจอที่ persona ด้านบนใช้งาน
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/` (`transaction/`, `period-end/`); routes ลงทะเบียนใน `routes/router.tsx`
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/` (`inventory-transaction/`, `period-end/`)
- carmen/docs: `../carmen/docs/Inventory/inventory-management-prd.md`, `../carmen/docs/inventory-management/period-end-process.md` — เอกสาร concept; ที่ใดขัดแย้งกับ implementation ที่อธิบายไว้ที่นี่ ให้ implementation ชนะ
