---
title: การนับสต๊อกประจำงวด (Physical Count) — Test Scenarios
description: Test case ต่อ persona, scenario end-to-end และการ map ไปยัง E2E สำหรับการนับสต๊อกประจำงวด
published: true
date: 2026-07-15T17:56:09.000Z
tags: physical-count, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# การนับสต๊อกประจำงวด (Physical Count) — Test Scenarios

> **At a Glance**
> **โมดูล:** [physical-count](/th/inventory/physical-count) &nbsp;·&nbsp; **ขอบเขต:** role permission-gated จริงหนึ่งเดียว แบ่งตามสองหน้าจอ (list; entry/review) บวกกลุ่มที่สามที่ยืนยันแล้วว่าไม่มีอยู่จริง
> **ลำดับการรัน:** ตรวจสอบ period/การ provision period → scenario หน้ารายการ → scenario หน้า entry/review → scenario end-to-end ด้านล่าง
> **ความครอบคลุม E2E:** ไม่มี Playwright spec ของ `physical-count` ที่ `../carmen-inventory-frontend-e2e/tests/`; มีเอกสารระดับวางแผนสามฉบับใน repo นั้น (`docs/persona-doc/System Process/tx-08-physical-stocktake.md`, `docs/test-cases/750-physical-count.md`, `docs/user-stories/750-physical-count.md`) แต่อธิบายการออกแบบที่ต่างออกไปอย่างมากและยังไม่ถูกสร้างจริง — ดู [02-business-rules.md](/th/inventory/physical-count/02-business-rules) § 5.1

## 1. ภาพรวม

หน้านี้เป็นจุดเริ่ม overview สำหรับชุด test-scenario ของโมดูล `physical-count` ความครอบคลุมจัดตาม role permission-gated จริงหนึ่งเดียวของโมดูล มองจากสองหน้าจอ — รายการสถานที่ (`04-test-scenarios-count-lead.md`) และ flow entry/review (`04-test-scenarios-counter.md`) — บวกหน้า correction (`04-test-scenarios-audit-config.md`) ที่บันทึกกลุ่ม persona ที่สามที่ยืนยันแล้วว่าไม่มีอยู่จริง หัวข้อ 4 ด้านล่างครอบคลุม scenario end-to-end ที่ข้ามทั้งสองหน้าจอในหนึ่งวงจรชีวิตเอกสาร

## 2. ขอบเขต

- **หน้ารายการ** — เริ่มหรือทำต่อการนับสำหรับสถานที่หนึ่ง; ตาม [physical-count/03-user-flow-count-lead](/th/inventory/physical-count/03-user-flow-count-lead)
- **หน้า Entry / Review** — ป้อนบรรทัด, note, import/export, Submit for Review และ Submit สุดท้าย; ตาม [physical-count/03-user-flow-counter](/th/inventory/physical-count/03-user-flow-counter)
- **ยืนยันแล้วว่าไม่มีอยู่จริง** — surface ของ Approver/Finance, Auditor หรือ Sysadmin; ตาม [physical-count/03-user-flow-audit-config](/th/inventory/physical-count/03-user-flow-audit-config)

## 3. ไฟล์ Test ของ Persona

- [Scenario ของหน้ารายการ](./04-test-scenarios-count-lead.md)
- [Scenario ของหน้า Entry/Review](./04-test-scenarios-counter.md)
- [กลุ่มที่ยืนยันแล้วว่าไม่มีอยู่จริง (หน้า correction)](./04-test-scenarios-audit-config.md)

## 4. Scenario End-to-End

แต่ละ row ด้านล่างเป็นวงจรชีวิตเอกสารเต็ม anchor กับ state machine จริงใน [03-user-flow.md](./03-user-flow.md) § 2

| # | Scenario | ขั้นตอน | สถานะปลายทางที่คาดหวัง |
| - | -------- | ----- | ------------------- |
| 1 | การนับเต็มโดยไม่มี variance | เริ่มการนับสำหรับสถานที่หนึ่ง → ป้อน `actual_qty` ให้เท่ากับสิ่งที่ขั้นตอน review คำนวณได้ทุกบรรทัด → Save → Submit for Review → Submit | `tb_physical_count.status = completed`; ไม่มี `tb_stock_in`/`tb_stock_out` สร้าง (ทุก `diff_qty = 0`) |
| 2 | การนับเต็มที่มีทั้ง overage และ shortage ผสม | เริ่มการนับ → ป้อนปริมาณที่สร้างทั้งบรรทัด variance บวกและลบ → Save แต่ละบรรทัด → Submit for Review → Submit | สร้างทั้ง `tb_stock_in` (บรรทัด overage) และ `tb_stock_out` (บรรทัด shortage) ทั้งคู่ `doc_status = completed` แล้ว; ไม่มี row `tb_inventory_transaction` ถูกเขียนโดย action นี้ (`PHC_POST_003`) |
| 3 | ทำต่อการนับที่ in-progress | Save บรรทัดบางส่วน → navigate ออก → กลับมาหน้ารายการ → คลิก Resume บนสถานที่เดียวกัน | Navigate กลับไป `/:id/entry` พร้อมบรรทัดที่ save ไว้ก่อนหน้ายังคงอยู่; ไม่มีเอกสารใหม่สร้าง |
| 4 | Refresh ระหว่างการนับจับสินค้าที่เพิ่งมีสต๊อก | สินค้าได้รับการเคลื่อนไหวสต๊อกครั้งแรกที่สถานที่หลัง count sheet ถูกสร้าง → คลิก Refresh บนหน้า entry | บรรทัดสินค้าใหม่ถูกเพิ่มเข้า sheet (`product_total` เพิ่มขึ้น); บรรทัดที่ป้อนไว้ก่อนหน้าไม่ได้รับผลกระทบ |
| 5 | ความขัดแย้งของ `doc_version` | Browser สองแท็บเปิดการนับเดียวกัน; แท็บ A save; แท็บ B save โดยใช้ `doc_version` ที่เก่าแล้ว | Save ของแท็บ B ถูก reject ด้วย conflict แบบ `409` (`PHC_VAL_007`); แท็บ B ต้อง reload แล้วลองใหม่ |
| 6 | Submit ถูกบล็อกโดยบรรทัดที่ยังไม่นับ | ทุกบรรทัดแสดงค่าบนหน้า entry จากการพิมพ์ แต่อย่างน้อยหนึ่งบรรทัดถูกป้อนและ submit-for-review ทันทีโดยไม่ผ่าน Save ก่อน | Submit สุดท้ายถูก reject ด้วย `"<N> products have not been counted yet"` เพราะ `counted_at` ของบรรทัดนั้นไม่เคยถูก stamp (`PHC_VAL_004`) — ดูข้อควรระวังใน [02-business-rules.md](./02-business-rules.md) |
| 7 | การปิดงวดถูกบล็อกโดยสถานที่จำเป็นที่นับไม่ครบ | สถานที่จำเป็น (`physical_count_type = yes`) ไม่มี count ที่ `completed` ภายใต้ period ที่กำลังปิด | การปิดงวดถูกบล็อกโดย `period-end.validate.ts`'s `validatePhysicalCount` จนกว่าการนับของสถานที่นั้นจะถึง `completed` |
| 8 | นับสถานที่ที่ไม่จำเป็นอยู่ดี | สถานที่ที่ flag `physical_count_type = no` ถูกนับและ submit จนถึง `completed` ผ่าน toggle "include not-counted" บนหน้ารายการ | การนับ complete ปกติ; ไม่มีผลต่อ gate การปิดงวด เพราะมีเพียงสถานที่ `physical_count_type = yes` เท่านั้นที่ถูกตรวจสอบ |

## 5. E2E Spec Map

ไม่มี Playwright spec ของ `physical-count` ที่ `../carmen-inventory-frontend-e2e/tests/` (ตรวจสอบโดย `ls tests/ | grep -i 'physical\|count'`) มีเอกสารระดับวางแผนสามฉบับใน repo นั้นแทน — `docs/persona-doc/System Process/tx-08-physical-stocktake.md`, `docs/test-cases/750-physical-count.md`, และ `docs/user-stories/750-physical-count.md` — แต่อธิบายการออกแบบ (transaction type ของตัวเอง, สถานะ `FINALIZED`/GL-posted, location transaction lock, tolerance/recount) ที่ implementation ปัจจุบันไม่ตรงด้วย ดู [02-business-rules.md](/th/inventory/physical-count/02-business-rules) § 5.1 สำหรับการเปรียบเทียบทีละจุด ให้ถือทุก scenario ในโมดูลนี้เป็น manual/planned จนกว่าจะมี spec อัตโนมัติ และเขียน coverage อัตโนมัติใหม่ตามกลไกจริงที่บันทึกไว้ที่นี่ — ไม่ใช่ตามเอกสารวางแผน

## 6. แหล่งอ้างอิง

- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/physical-count/`
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count/physical-count.service.ts`, `.../physical-count-period/physical-count-period.service.ts`, `.../period-end/period-end.validate.ts`
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec physical-count; เอกสารวางแผนที่ `docs/persona-doc/System Process/tx-08-physical-stocktake.md`, `docs/test-cases/750-physical-count.md`, `docs/user-stories/750-physical-count.md`
- ที่เกี่ยวข้อง: [physical-count/03-user-flow](/th/inventory/physical-count/03-user-flow) (state machine ที่หน้านี้ใช้), [physical-count/02-business-rules](/th/inventory/physical-count/02-business-rules) (`PHC_VAL_*` / `PHC_AUTH_*` / `PHC_POST_*`), [inventory-adjustment/04-test-scenarios](/th/inventory/inventory-adjustment/04-test-scenarios) (ตารางที่ rollup เขียนเข้า)
