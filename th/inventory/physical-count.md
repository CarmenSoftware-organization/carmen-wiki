---
title: การนับสต๊อกประจำงวด (Physical Count)
description: การนับสต๊อกแบบเต็มทุกรายการที่สถานที่จัดเก็บตามรอบกำหนด เพื่อกระทบยอดระบบกับของจริงบนชั้น
published: true
date: 2026-07-15T17:56:09.000Z
tags: physical-count, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# การนับสต๊อกประจำงวด (Physical Count)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** นับทุกรายการที่สถานที่หนึ่งสำหรับงวดนับปัจจุบัน ป้อนและ submit โดย role เดียวแบบไม่แยกกลุ่ม แล้วกระทบยอด variance เข้าสู่เอกสาร stock-in/stock-out โดยตรงตอน submit สุดท้าย &nbsp;·&nbsp; **กลุ่มผู้ใช้:** ผู้ใช้ที่ถือสิทธิ์ `inventory_management.physical_count` — ไม่มี role อนุมัติ ตรวจสอบ หรือ config แยกในโค้ด &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_physical_count_period`, `tb_physical_count`, `tb_physical_count_detail`, ตาราง comment สามระดับ, enum `enum_physical_count_*` สี่ตัว &nbsp;·&nbsp; **หน้าย่อย:** 10

![Physical Count screen](/screenshots/physical-count/index.png)

![Physical Count detail screen](/screenshots/physical-count/detail.png)

## 1. ภาพรวม

**การนับสต๊อกประจำงวด (Physical Count)** คือการนับทุกรายการที่สถานที่หนึ่งสำหรับงวดนับปัจจุบัน ใช้กระทบยอด book balance ของระบบเข้ากับของจริงบนชั้น การ implement จริง (`../carmen-inventory-frontend-react/routes/inventory-management/physical-count/`) เป็น flow ต่อเนื่องเดียวโดยไม่มีการส่งต่อระหว่าง persona: ผู้ใช้เปิดรายการสถานที่ของงวดปัจจุบัน (`physical-count`) เริ่มหรือทำต่อการนับที่สถานที่หนึ่ง (`physical-count/:id/entry`) ป้อน `actual_qty` ทีละบรรทัดสินค้า submit sheet เพื่อ review (`physical-count/:id/review`) แล้วยืนยัน submit สุดท้าย — ซึ่งเป็นขั้นตอนเดียวกันกับที่กระทบยอดทุกบรรทัดที่มี variance ไม่เป็นศูนย์เข้าสู่เอกสาร stock-in/stock-out คู่หนึ่ง ทุก action ใน flow นี้ถูก gate ด้วย permission key เดียว `inventory_management.physical_count` (`constant/permissions.ts`) — ไม่พบ role, route, หรือ permission แยกสำหรับผู้อนุมัติ ผู้ตรวจสอบ หรือผู้ตั้งค่า configuration ใด ๆ ทั้งใน frontend, backend หรือ Bruno collection สำหรับโมดูลนี้

มีสอง route ที่ยังผูกอยู่ใน router แต่ **ไม่สามารถเข้าถึงได้จากเส้นทาง navigation จริงใด ๆ**: `physical-count/new` และ `physical-count/:id` ทั้งคู่ render `PcForm` (`pc-form.tsx`) ซึ่งเป็นฟอร์มสร้าง/แก้ไขจากก่อน refactor ที่มีฟิลด์เดียวคือ `department_id` — type ที่ฟอร์มนี้แก้ไขถูก comment ไว้ชัดเจนว่า `// Legacy type (used by old form)` ใน `types/physical-count.ts` ไม่มีปุ่มใดในหน้ารายการที่ลิงก์ไป `/new` และ action สร้างจริง (`pc-component.tsx`'s `handleAction`) สร้างการนับโดยตรงผ่าน `POST /physical-counts` แล้ว navigate ตรงไป `/:id/entry` ไม่เคยไปที่ `/:id` เลย ให้ถือว่าสอง route นี้และ hook `use-pc-table.tsx` ที่รองรับอยู่เป็นโค้ดจากก่อน refactor ที่ถูกทิ้งไว้ (orphaned)

## 2. บริบททางธุรกิจ

การนับสต๊อกประจำงวดเป็นพื้นฐานเชิงกฎระเบียบและการตรวจสอบ ไม่ใช่งานที่จะทำหรือไม่ทำก็ได้ ผู้ตรวจสอบภายนอกต้องการการนับที่มีเอกสารกำกับ ณ สิ้นงวด เพื่อรับรองยอดสต๊อกบนงบดุล และกลุ่มโรงแรมส่วนใหญ่มีนโยบายภายในกำหนดให้นับเป็นรอบ (cycle count) สำหรับหมวดความเสี่ยงสูงด้วยความถี่ที่มากกว่า การนับที่ครบและเซ็นปิดงานคือหลักฐานว่ามูลค่าสินค้าคงเหลือที่บันทึกในบัญชีเป็นของจริง — หากไม่มี การประเมินมูลค่าปิดงวดจะไม่มีหลักฐานรองรับและความเห็นของผู้ตรวจสอบจะอยู่ในความเสี่ยง

ความถูกต้องทางการเงินมีผลทันที ธุรกิจโรงแรมดำเนินงานบนกำไรขั้นต้นของอาหารและเครื่องดื่มที่บางเฉียบ และ shrinkage ที่ไม่ได้นับทบขึ้นอย่างรวดเร็ว: การลักขโมย การเน่าเสีย การรินผิดปริมาณ ความผิดพลาดในการโอนย้าย และการบันทึกการบริโภคที่ผิดประเภท ทั้งหมดบ่อนทำลายความถูกต้องของบัญชีระหว่างรอบการนับ การนับสต๊อกประจำงวด ณ สิ้นงวดคือจุดที่ความคลาดเคลื่อนนี้ถูกตรวจพบและคิดเป็นจำนวน — ทำให้การนับเป็นหนึ่งในกลไกแก้ไขมูลค่าสต๊อกที่ใหญ่ที่สุดในการดำเนินงานจำนวนมาก การนับที่ล่าช้าหรือไม่ครบหมายถึงสถานะสต๊อกที่ผิด และข้อผิดพลาดต่อเนื่องในการวิเคราะห์เมนูและการพยากรณ์การจัดซื้อ

## 3. แนวคิดสำคัญ

- **Count Sheet**: เอกสารทำงานสำหรับการนับหนึ่งสถานที่ — หนึ่ง row `tb_physical_count` พร้อมบรรทัด `tb_physical_count_detail` รายการสินค้าเป็น union ของ (a) สินค้าที่ถูก assign เข้าสถานที่อย่างเป็นทางการผ่าน `tb_product_location` และ (b) สินค้าใดก็ตามที่มีปริมาณสุทธิไม่เป็นศูนย์ใน `tb_inventory_transaction_detail` ที่สถานที่นั้น ดังนั้นรายการที่มีสต๊อก "หลอน" จะถูกจับได้เสมอแม้ไม่ได้ assign อย่างเป็นทางการ Count sheet ถูกสร้างขึ้น **ที่สถานะ `in_progress` ทันที** — `start_counting_at`/`start_counting_by_id` ถูก stamp ทันทีตอนสร้าง (`physical-count.service.ts` `create()`) ไม่ใช่ตอน counter ป้อนบรรทัดแรก ปุ่ม **Refresh** บนหน้า entry (`PATCH .../physical-counts/:id/refresh`) รัน query union เดียวกันซ้ำและเพิ่มสินค้าที่เข้าเงื่อนไขใหม่เข้า sheet ที่ยัง in-progress
- **ข้อกำหนดของสถานที่ในการนับ** (ไม่ใช่ "frozen vs live"): `tb_location.physical_count_type` (`enum_physical_count_type`, `yes`/`no`, default `no`) เป็น flag ระดับสถานที่ที่ admin ตั้งค่าบนฟอร์ม config ของสถานที่เอง (`master-data/location`, filter chip "Count"/"Not Count") ระบุว่าสถานที่นั้น **จำเป็น** ต้องนับสำหรับ gate การปิดงวด (`period-end.validate.ts`'s `validatePhysicalCount` ต้องการ `location_type ∈ {inventory, consignment}`, `physical_count_type = yes`, `is_active = true`) **ไม่ใช่** โหมด frozen-vs-live ระดับเอกสาร: ฟิลด์ชื่อเดียวกันที่ระดับ *เอกสาร* (`tb_physical_count.physical_count_type`) ไม่เคยถูกตั้งค่าโดย `create()` เลย ดังนั้นทุกเอกสาร count ที่สร้างขึ้นจึงคงค่า default ของ Prisma ไว้เฉย ๆ (`yes`) ไม่มีโค้ดใดในระบบ — ทั้ง frontend หรือ backend รวมถึง service ของ good-received-note และ store-requisition — ตรวจสอบว่ามีการนับ in-progress อยู่ก่อนที่จะอนุญาตให้ post ที่สถานที่นั้น ไม่มี location lock
- **Variance**: `diff_qty = actual_qty − on_hand_qty` ต่อบรรทัด คำนวณโดย backend (ไม่ใช่ client) ที่สำคัญคือ `on_hand_qty` **ไม่ใช่** snapshot ที่จับตอนสร้าง sheet — มันคงเป็น `0` บนทุกบรรทัดจนกว่า counter จะกด **Submit for Review** ซึ่งเป็นจุดที่ `reviewItems()` คำนวณ `on_hand_qty` ใหม่สำหรับทุกบรรทัดเป็นยอดรวม **ปัจจุบัน สด** ของ `tb_inventory_transaction_detail.qty` ที่สถานที่นั้น (ไม่มี date cut-off) ปริมาณที่พิมพ์และ save ระหว่างการนับจึงแสดง variance เทียบกับ book quantity ที่เป็น `0` ค้างอยู่ จนกว่าขั้นตอน review จะรัน — มีเพียงการคำนวณใหม่ตอน review เท่านั้นที่มีความหมาย ไม่มี tolerance threshold, การ flag แบบเปอร์เซ็นต์ หรือกลไก recount ใด ๆ ในโมดูลนี้ทั้ง frontend และ backend
- **Save vs Submit for Review vs Submit**: สาม backend call ที่แยกกันขับเคลื่อนเอกสารหนึ่งฉบับไปสู่ความสมบูรณ์ **Save** (`PATCH .../save`, เวลาใดก็ได้ ทำซ้ำได้) stamp `counted_at`/`counted_by_id` บนบรรทัดที่ส่งมาและคำนวณ `diff_qty` ของแต่ละบรรทัดใหม่เทียบกับ `on_hand_qty` ที่เก็บอยู่ในขณะนั้น (ปกติยังเป็น `0` ก่อน review ครั้งแรก) **Submit for Review** (`PATCH .../review`, เมื่อทุกบรรทัดมีค่าแล้ว) คำนวณ `on_hand_qty`/`diff_qty` สดใหม่สำหรับทุกบรรทัดและพาผู้ใช้ไปหน้า `/review` แต่ **ไม่** เปลี่ยน `tb_physical_count.status` — ยังคงเป็น `in_progress` **Submit** (`PATCH .../submit`, จากหน้า review) คือ action ปลายทางที่อธิบายด้านล่าง `submit()` reject ด้วย `"<N> products have not been counted yet"` ถ้ามีบรรทัดใดที่ `counted_at` ยังเป็น null — เนื่องจากมีเพียง Save เท่านั้นที่ stamp `counted_at` บรรทัดที่ค่ามาจากการพิมพ์แล้ว Submit-for-Review ทันที (ไม่ผ่าน Save ก่อน) อาจไปถึงหน้า review ด้วย `actual_qty` จริงแต่ `counted_at` เป็น null และจะบล็อก Submit สุดท้าย — edge case นี้ยังไม่ได้ยืนยันในทางปฏิบัติ แต่เป็นการอ่านตรงจากสอง service method
- **Rollup ตอน Submit**: ที่ `submit()`, backend จัดกลุ่มทุกบรรทัดที่ variance ไม่เป็นศูนย์ตามเครื่องหมาย และใน transaction เดียว สร้าง **อย่างมากหนึ่ง** `tb_stock_in` (ทุกบรรทัด variance บวก) และ **อย่างมากหนึ่ง** `tb_stock_out` (ทุกบรรทัด variance ลบ) — ทั้งคู่ถูก insert **ที่ `doc_status = completed` ทันที** สะท้อน pattern "create() post completed แบบไม่มีเงื่อนไข" เดียวกับที่ยืนยันแล้วในหน้าจอ Stock In/Out ของโมดูล [inventory-adjustment](/th/inventory/inventory-adjustment) เอง ต่างจากหน้าจอเหล่านั้น rollup นี้ **ไม่** เรียก `InventoryTransactionService.executeAdjustmentIn`/`executeAdjustmentOut` เลย — ไม่มี import หรือเรียก helper ทั้งสองใน `physical-count.service.ts` ไม่มี row `tb_inventory_transaction` ถูกเขียนโดย action นี้ `adjustment_type_id` ถูกปล่อยเป็น `null` บน header ที่สร้างทั้งคู่ (ไม่มี reason code) และไม่มีฟิลด์ `info`/structured ใด ๆ เชื่อม stock-in/out ใหม่กลับไปยัง `tb_physical_count` ต้นทาง — ร่องรอยเดียวคือข้อความ `description`/`note` แบบ human-readable ที่ใช้ร่วมกัน ("Physical Count Adjustment - Period: …") ราคาต่อบรรทัด (`cost_per_unit`) ถูกตีมูลค่าด้วยวิธี costing เดียวระดับ tenant ที่อ่านครั้งเดียวต่อ submit (`enum_business_unit_config_key.physical_count_costing_method`, default `last_receiving`; ไม่พบหน้าจอ UI ใดที่ตั้งค่า key นี้)

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| Counter (ผู้ใช้ใดก็ตามที่ถือสิทธิ์ `inventory_management.physical_count`) | Role เดียวไม่แยกกลุ่มสำหรับโมดูลนี้: เปิดรายการสถานที่ เริ่มหรือทำต่อการนับ ป้อน `actual_qty` ทีละบรรทัด flag รายการเสียหาย/ไม่คุ้นเคยผ่าน comment submit เพื่อ review และยืนยัน submit สุดท้าย |

ไม่พบ role, permission key, route หรือ workflow stage แยกสำหรับ Count Lead, Approver/Finance Reviewer, Auditor หรือ Sysadmin ในโมดูลนี้ ทั้งใน frontend, backend หรือ Bruno collection — การแบ่ง persona ที่บันทึกไว้ใน draft ก่อนหน้าของโมดูลวิกินี้ไม่มีอยู่จริงใน implementation ปัจจุบัน หน้าย่อยใน § 7 ด้านล่างยังคงแบ่งเป็น Count Lead / Counter / Audit-Config ไว้เพียงเพื่อจัดระเบียบหน้าเท่านั้น (สะท้อน action ของหน้าจอเดียวจริงจากสองมุมมอง) `03-user-flow-audit-config.md` และ `04-test-scenarios-audit-config.md` เป็นหน้า correction สำหรับกลุ่มที่สามที่ยืนยันแล้วว่าไม่มีอยู่จริง

## 5. โมดูลที่เกี่ยวข้อง

**การไหลข้ามโมดูล:**
- [inventory](/th/inventory/inventory) — variance rollup ของการนับพุ่งเป้าไปที่ตาราง `tb_stock_in`/`tb_stock_out` เดียวกันกับที่ inventory ledger อ่าน แต่ (ตาม § 3 ข้างต้น) rollup นี้ไม่ได้เขียน row `tb_inventory_transaction` เอง
- [inventory-adjustment](/th/inventory/inventory-adjustment) — rollup สร้าง row `tb_stock_in`/`tb_stock_out` ดิบ ๆ แต่ข้าม service layer ของโมดูลนั้น (ไม่มี reason code ไม่มีฟิลด์เชื่อมโยง)
- [spot-check](/th/inventory/spot-check) — โมดูลแยกที่แคบกว่าสำหรับการนับบางส่วน; ไม่ใช่ child ของ `tb_physical_count_period`

**Master configuration:**
- [master-data/unit](/th/inventory/master-data/unit) — หน่วยนับของแต่ละบรรทัดในการนับ (`inventory_unit_id`)
- [master-data/location](/th/inventory/master-data/location) — สถานที่ที่กำลังถูกนับ และแหล่งที่มาของ flag `physical_count_type` (สถานที่ที่จำเป็นต้องนับ) ตามที่อธิบายใน § 3
- [system-config/period](/th/inventory/system-config/period) — งวดบัญชีที่การนับดำเนินอยู่ภายใต้ (`tb_period` → `tb_physical_count_period`); การปิดงวดบล็อกจนกว่าจะนับครบที่สถานที่จำเป็น (`period-end.validate.ts`)

## 6. แหล่งอ้างอิง

- Concepts: ไม่มีโฟลเดอร์ source ใน carmen/docs สำหรับโมดูลนี้; มีเอกสารวางแผนสองฉบับใน E2E repo แต่ไม่ตรงกับ implementation ปัจจุบัน — ดูรายละเอียด discrepancy ใน [physical-count/02-business-rules](/th/inventory/physical-count/02-business-rules) § 5.1
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/physical-count/` (`pc-component.tsx`, `pc-entry-component.tsx`, `pc-review-component.tsx`)
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count/` และ `physical-count-period/`
- API contracts: `../carmen-turborepo-backend-bruno/collections/carmen-inventory/inventory/physical-count*/`
- E2E tests: `../carmen-inventory-frontend-e2e/` — ยังไม่มี Playwright spec สำหรับโมดูลนี้ (`ls tests/ | grep -i 'physical\|count'`); มีเอกสารระดับวางแผนที่ `docs/persona-doc/System Process/tx-08-physical-stocktake.md`, `docs/test-cases/750-physical-count.md`, และ `docs/user-stories/750-physical-count.md`

## 7. หน้าในโมดูลนี้

- [physical-count/01-data-model](/th/inventory/physical-count/01-data-model) — เอนทิตี ฟิลด์ ความสัมพันธ์ enum (`tb_physical_count_period`, `tb_physical_count`, `tb_physical_count_detail` รวมกับตาราง comment สามตาราง enum สี่ตัว)
- [physical-count/02-business-rules](/th/inventory/physical-count/02-business-rules) — การตรวจสอบความถูกต้อง การคำนวณ การกำหนดสิทธิ์ การ post กฎข้ามโมดูล (`PHC_VAL_*` / `PHC_CALC_*` / `PHC_AUTH_*` / `PHC_POST_*` / `PHC_XMOD_*`)
- [physical-count/03-user-flow](/th/inventory/physical-count/03-user-flow) — ภาพรวมวงจรชีวิตเอกสาร + สารบัญ persona
  - [physical-count/03-user-flow-count-lead](/th/inventory/physical-count/03-user-flow-count-lead) — หน้ารายการ: สถานที่ของงวดปัจจุบัน, KPI tile, action เริ่ม/ทำต่อ
  - [physical-count/03-user-flow-counter](/th/inventory/physical-count/03-user-flow-counter) — หน้า entry + review: ป้อนบรรทัด, note, import/export, submit สุดท้าย
  - [physical-count/03-user-flow-audit-config](/th/inventory/physical-count/03-user-flow-audit-config) — หน้า correction: ไม่มี surface ของ Approver/Auditor/Sysadmin
- [physical-count/04-test-scenarios](/th/inventory/physical-count/04-test-scenarios) — ภาพรวม test scenario + scenario end-to-end + เป้าหมาย mapping ไปยัง E2E
  - [physical-count/04-test-scenarios-count-lead](/th/inventory/physical-count/04-test-scenarios-count-lead) — scenario ของหน้ารายการ
  - [physical-count/04-test-scenarios-counter](/th/inventory/physical-count/04-test-scenarios-counter) — scenario ของหน้า entry/review
  - [physical-count/04-test-scenarios-audit-config](/th/inventory/physical-count/04-test-scenarios-audit-config) — หน้า correction (สะท้อนหน้า correction ฝั่ง user-flow)

> **Status:** re-sync แล้วเทียบกับ frontend จริง (`pc-component.tsx`, `pc-entry-component.tsx`, `pc-review-component.tsx`), backend (`physical-count.service.ts`, `physical-count-period.service.ts`, `period-end.validate.ts`), Prisma schema และ Bruno collection ยังไม่มี E2E Playwright spec สำหรับโมดูลนี้; เอกสารระดับวางแผนสองฉบับใน E2E repo (`tx-08-physical-stocktake.md`, `750-physical-count.md`) อธิบายการออกแบบที่ต่างออกไปอย่างมากและยังไม่ถูกสร้างจริง (transaction type ของตัวเอง, สถานะ `FINALIZED` ที่ post GL, location transaction lock, tolerance/recount) — ดู [physical-count/02-business-rules](/th/inventory/physical-count/02-business-rules) § 5.1 สำหรับการเปรียบเทียบทีละจุด
