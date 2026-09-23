---
title: ใบเบิกของสโตร์ (Store Requisition)
description: เอกสารคำขอภายในเพื่อเบิกสต๊อกจากคลังหรือสโตร์กลางไปยังจุดที่บริโภค (ครัว บาร์ เอาท์เลต)
published: true
date: '2026-09-23T01:30:00.000Z'
tags: store-requisition, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# ใบเบิกของสโตร์ (Store Requisition)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** เอกสารเคลื่อนย้ายสต๊อกภายใน — `Issue` (ไปยังปลายทางแบบลงค่าใช้จ่ายตรง) หรือ `Transfer` (เคลื่อนย้ายระหว่างสถานที่) พร้อม workflow อนุมัติและการติดตามปริมาณสามค่า (ขอ / อนุมัติ / จ่ายจริง) &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Outlet Manager / Requester, Approver, Store Keeper / Fulfiller &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_store_requisition`, `tb_store_requisition_detail`, `tb_inventory_transaction`, `enum_doc_status`, `enum_sr_type` &nbsp;·&nbsp; **หน้าย่อย:** 16
> **Re-sync 2026-09-22 เทียบกับ backend HEAD (`cd2e07f60`) และ frontend HEAD (`8cf47f87`):** `sr_type` ตอนนี้ถูก *derive* ฝั่ง server จาก `location_type` ของสองสถานที่ (`sr-type.helper.ts`), วันที่ของใบเบิกถูก **freeze ตอน submit** และวันที่ issue ถูก resolve เทียบกับ inventory period ที่เปิดอยู่ (`sr-date.helper.ts`, 2026-09-18), แผนกถูก derive จาก requester เมื่อฟอร์มไม่ได้ส่งมา, workflow action ทั้งหมดเป็น `PATCH` (ไม่ใช่ `POST`), มี read model `GET .../stock-movements` รองรับแท็บ Stock Movement, draft สามารถลบแบบ batch ได้ (`DELETE .../store-requisitions/batch`) และลบได้เฉพาะเจ้าของ, และ [Stock Replenishment](/th/inventory/store-requisition/stock-replenishment) เป็น API จริงแล้ว ส่วน invariant ปริมาณสามค่า (`issued ≤ approved ≤ requested`) กลายเป็นว่าเป็น **เจตนาที่บันทึกไว้เท่านั้น** — ไม่มี DTO หรือ service ใดบังคับใช้ (ดู [02-business-rules](/th/inventory/store-requisition/02-business-rules) `SR_VAL_008`)
> ⚠️ **รอบ 2026-07-15 พบว่า `StockMovement` และ `JournalEntry` เคยถูกบันทึกไว้ว่าเป็นตารางที่ SR เป็นเจ้าของ — ทั้งสองไม่มีอยู่จริงใน Prisma; ข้อมูล stock movement และ journal-entry อยู่บนตระกูล `tb_inventory_transaction` ที่ใช้ร่วมกัน (ดู [01-data-model.md](/th/inventory/store-requisition/01-data-model) §5) นอกจากนี้ยังพบว่า persona "Receiver", การ post GL/journal-entry, การบังคับ segregation-of-duties, การ delegate การอนุมัติ/value-threshold, และการเลือก lot โดย store keeper ไม่มี code รองรับ — ดูหน้า persona ที่แก้ไขแล้วและ Discrepancy entry ใน progress-log ของโมดูล

![ใบเบิกของสโตร์ (Store Requisition) screen](/screenshots/store-requisition/index.png)

![ใบเบิกของสโตร์ (Store Requisition) detail screen](/screenshots/store-requisition/detail.png)

## 1. ภาพรวม

**ใบเบิกของสโตร์ (Store Requisition — SR)** คือเอกสารภายในที่สถานที่หนึ่งใช้เบิกสต๊อกจากอีกสถานที่หนึ่ง — โดยทั่วไปคือเอาท์เลตที่บริโภค (ครัว บาร์ ภัตตาคาร แบงเควต) ขอสินค้าจากสโตร์กลางหรือสโตร์หลัก SR แต่ละใบประกอบด้วยส่วนหัว (เลขที่อ้างอิง วันที่ สถานที่ต้นทาง/ที่ขอเบิก สถานที่ปลายทาง ประเภทการเคลื่อนย้าย คำอธิบาย สถานะ) และรายการสินค้าหนึ่งรายการขึ้นไปที่ระบุสินค้า หน่วยนับ ปริมาณที่ขอ ปริมาณที่อนุมัติ และปริมาณที่จ่ายจริง ไม่มีคอลัมน์การเงินบนส่วนหัวหรือบรรทัดของ SR — ราคาต้นทุนต่อหน่วยและยอดรวมต่อบรรทัดถูกอ่านจาก inventory transaction ที่ลิงก์ในเวลาแสดงผล (ดู [01-data-model.md](/th/inventory/store-requisition/01-data-model) §5) ประเภทการเคลื่อนย้าย — `Issue` (การบริโภคไปยังปลายทางแบบลงค่าใช้จ่ายตรง) หรือ `Transfer` (การเคลื่อนย้ายสต๊อกระหว่างสถานที่) — เป็นตัวกำหนดว่า stock-movement records แบบใดจะถูกเขียน

SR ดำเนินผ่านวงจรชีวิตที่ยืนยันแล้ว: `draft` → `in_progress` → `completed` draft ถูกสร้างด้วยเลขที่ placeholder (`draft-<6 hex>`); เลขที่ running-code จริงและ `sr_date` ที่ freeze แล้วถูกกำหนดตอน submit (`StoreRequisitionService.submit()` → `resolveSubmitSrDate()` + `generateSRNo()`) SR ดำเนินผ่านสถานะ (`enum_doc_status` ที่ใช้ร่วมกับโมดูลอื่นอีกหลายตัว) การกระทำเดียวที่ผู้อนุมัติ/ผู้ issue ใช้จบเอกสารก่อนกำหนดคือการตั้ง `doc_status = voided` โดยตรง — ไม่มีผลลัพธ์ `cancelled` แยกต่างหากที่ code path ปัจจุบันใด ๆ เข้าถึงได้ (enum นิยามค่า `cancelled` ไว้ก็จริง แต่ไม่มี service method ใดของ SR ที่ตั้งค่านี้ — ดู [01-data-model.md](/th/inventory/store-requisition/01-data-model) §5 และ [02-business-rules.md](/th/inventory/store-requisition/02-business-rules) §5) flow รองรับการ fulfill บางส่วนที่ระดับบรรทัด ดังนั้นคำขอ 10 หน่วยอาจถูกจ่ายเพียง 8 และทุก transition จะถูก log พร้อมผู้ใช้ timestamp และโน้ตสำหรับการตรวจสอบ

โมดูล SR คือ system of record สำหรับการเคลื่อนย้ายสต๊อกภายในระหว่างสถานที่ เมื่อขั้น workflow สุดท้ายเดินหน้า (ไม่ว่าจะเป็นขั้นใดก็ตาม — action `PATCH .../approve` แบบเดียวกันถูกใช้ในทุกขั้น รวมถึงขั้นที่ store keeper กระทำ) ระบบจะ resolve วันที่ issue เทียบกับ inventory period ที่เปิดอยู่ (`resolveIssueDate()` — วันที่ของใบเบิกเองต้องอยู่ใน period ที่เปิด มิฉะนั้นได้ `SR_DATE_OUTSIDE_OPEN_PERIOD`), stamp `issue_at` / `issue_by_id` บนส่วนหัว, ปล่อยให้การบริโภค cost-layer ปฏิเสธการจ่ายเกิน (`Insufficient stock` ถูก throw โดย `createFifoConsumption` / `createAverageConsumption`), บันทึกการเคลื่อนย้าย OUT ที่ต้นทาง และในกรณี `Transfer` คือการเคลื่อนย้าย IN คู่กันที่ปลายทาง ผ่านตระกูล `tb_inventory_transaction` ที่ใช้ร่วมกัน ไม่มีตาราง `JournalEntry` หรือ `StockMovement` อยู่ในโมดูลนี้ — ดู correction note ที่ด้านบนของหน้านี้

## 2. บริบททางธุรกิจ

ในธุรกิจโรงแรม สโตร์กลางซื้อและถือสต๊อกแบบ bulk แต่ต้นทุนสินค้าที่บริโภคจริงต้องลงที่เอาท์เลตที่บริโภค — ครัว บาร์ ฝ่ายแบงเควต ใบเบิกของสโตร์คือกลไกควบคุมที่ทำให้สโตร์กลางสามารถปล่อยสต๊อกออกไปยังสถานที่ที่บริโภคได้พร้อมสร้าง paper trail ที่ผูกต้นทุนเข้ากับ cost centre ที่ถูกต้อง หากไม่มีกลไกควบคุมนี้ การรายงาน food cost ต่อเอาท์เลตจะเป็นไปไม่ได้ เมื่อมีแล้ว วัตถุดิบทุกหน่วยที่จ่ายออกไปสามารถสืบย้อนได้จากชั้นสโตร์จนถึงจาน

Approval workflow มีอยู่เพราะสต๊อกภายในคือเงินจริง เอาท์เลตจะดึงจากสโตร์กลางตามใจไม่ได้ — คำขอถูก review เทียบกับความจำเป็นเชิงปฏิบัติการและสต๊อกคงเหลือที่ต้นทาง ผู้อนุมัติสามารถลดปริมาณที่ขอก่อนจ่าย, reject รายการที่ไม่มีเหตุผลรองรับ หรือส่งเอกสารกลับพร้อมความคิดเห็น การออกแบบนี้มีเจตนาเพื่อป้องกันการจ่ายเกินและแยกพนักงานที่ขอสต๊อกออกจากพนักงานที่ปล่อยสต๊อก — แต่ไม่พบการตรวจสอบ segregation-of-duties (requester ≠ approver, approver ≠ issuer) ใด ๆ ใน backend หรือ frontend code ปัจจุบัน ให้ถือว่า SoD เป็นเพียงเจตนาที่บันทึกไว้ ไม่ใช่การควบคุมที่บังคับใช้จริง จนกว่าจะมีการยืนยันเป็นอย่างอื่น

Costing ใช้วิธีปัจจุบันของสถานที่ต้นทาง — weighted-average หรือ FIFO — ดังนั้นมูลค่าที่เคลื่อนย้ายสอดคล้องกับวิธีที่ต้นทางประเมินสต๊อกที่เหลือ การ post GL/journal-entry จากการ issue SR ยังไม่ได้ถูกต่อสาย: ตอนนี้ backend มี GL core แล้ว (`apps/micro-business/src/gl/gl-posting`, migration `20260914030000_gl_core_jv_ledger`) แต่ `grep -rn store_requisition apps/micro-business/src/gl/` ได้ศูนย์ผลลัพธ์ ดังนั้นไม่มีสิ่งใดใน commit path ของ SR ที่ post journal

## 3. แนวคิดสำคัญ

- **Source Location (Requested From)**: สถานที่ที่ถือสต๊อกที่ถูกเบิก — โดยทั่วไปคือสโตร์หลักหรือคลังกลาง เก็บที่ส่วนหัวเป็น `from_location_id` / `from_location_name`; ต้องเป็นสถานที่แบบ `inventory` หรือ `consignment` (`deriveSrType()` throw `from_location must be inventory or consignment, not direct`) วิธี costing ของต้นทาง (weighted-average หรือ FIFO) เป็นตัวกำหนดต้นทุนต่อหน่วยที่ใช้กับทุกรายการที่จ่ายออก ความพร้อมที่ต้นทาง **ไม่ได้** ถูกตรวจสอบตอน submit (ไม่มีการอ่าน on-hand ใน submit path — ดู `SR_VAL_009`); ถูกบังคับใช้เฉพาะที่ขั้นสุดท้าย ซึ่งการบริโภค cost-layer จะ throw `Insufficient stock` หาก on-hand ไม่พอ
- **Destination Location (Request To)**: สถานที่ที่บริโภคหรือรับ — ครัว บาร์ เอาท์เลต หรือสโตร์สต๊อกอีกแห่ง เก็บเป็น `to_location_id` / `to_location_name` ค่า `location_type` ของปลายทาง **เป็นตัวตัดสิน** ประเภทการเคลื่อนย้าย: `direct` → `issue`, `inventory` หรือ `consignment` → `transfer` (`sr-type.helper.ts` `deriveSrType()` ถูกเรียกจาก `StoreRequisitionService.create()`); client ไม่เคยส่ง `sr_type` ตอน submit สินค้าของทุกบรรทัดต้องถูกเปิดใช้ที่ปลายทาง (`tb_product_location`) มิฉะนั้นได้ `The following products are not allowed in the destination location: …`
- **Movement Type (Issue vs Transfer)**: ถูก derive ไม่ใช่เลือกเอง (ดูด้านบน) `Issue` post stock OUT ครั้งเดียวที่ต้นทาง — ใช้เมื่อสต๊อกออกจากคลังและถูกบริโภคทันที (เบิกครัว เบิกบาร์) `Transfer` post stock OUT ที่ต้นทางและ stock IN ที่ปลายทางคู่กัน — ใช้เมื่อสต๊อกเคลื่อนย้ายระหว่างสองสถานที่ที่ถือสต๊อกโดยยังไม่ถูกบริโภค
- **Approval Workflow**: SR ถูกจัดเส้นทางผ่านหนึ่งขั้นหรือมากกว่าตามการตั้งค่า `tb_workflow` ของ tenant (workflow engine แบบเดียวกับที่ PR/PO/GRN ใช้) ผู้อนุมัติสามารถอนุมัติบรรทัดแบบเต็ม ตัดลง reject (รวมอยู่ใน approve call เดียวกันกับบรรทัดที่อนุมัติอื่น ๆ) หรือส่งเอกสารทั้งใบกลับเพื่อแก้ไข ยังมี action reject ทั้งเอกสารแยกต่างหาก ซึ่งในฟอร์มปัจจุบันถูกเปิดใช้ก็ต่อเมื่อ "ทุกบรรทัดถูกทำเครื่องหมาย reject" — action นี้ตั้ง `doc_status = voided` โดยตรง ไม่ใช่สถานะ `cancelled` แยกต่างหาก ไม่พบการจัดเส้นทางตาม value-threshold, การ delegate, หรือ SLA-timeout escalation ใด ๆ ใน source ปัจจุบัน — ให้ถือว่าข้อกล่าวอ้างเหล่านี้ยังไม่ได้รับการยืนยัน
- **Requested vs Approved vs Issued Quantity**: ปริมาณสามค่าต่อบรรทัดเล่าเรื่องราวทั้งหมด `requested_qty` คือสิ่งที่เอาท์เลตขอ (ต้อง `> 0` ตอน submit — `ValidateSRBeforeSubmitSchema` `positive()`; create DTO รับตัวเลขใดก็ได้); `approved_qty` คือสิ่งที่ผู้อนุมัติอนุญาต (ถูกตั้งค่าเริ่มต้นเป็น `requested_qty` ตอน submit); `issued_qty` คือสิ่งที่ถูกปล่อยจริงตอนขั้นสุดท้าย ลำดับ `issued ≤ approved ≤ requested` เป็นเจตนาที่บันทึกไว้ — **ไม่มี DTO, service หรือการตรวจสอบในฟอร์มใดบังคับใช้** (`saveStageRoleDetails()` และ `approve()` บันทึกค่าใดก็ตามที่ payload ส่งมา; `sr-form-schema.ts` จำกัดเพียง `requested_qty ≥ 0`) ตัวเลขสามตัวนี้เมื่อรวมจาก SR หลาย ๆ ใบ ขับเคลื่อนการวิเคราะห์ variance
- **Variance (Requested − Issued)**: ช่องว่างระหว่างสิ่งที่ขอกับสิ่งที่จ่ายจริง บันทึกต่อบรรทัด variance เกิดจากการที่ผู้อนุมัติตัดลงหรือการ fulfill บางส่วน การติดตาม variance ตามเวลาอาจเผยให้เห็นการขอเกินเรื้อรังหรือปัญหา supply ขาดแคลน แม้ว่ารอบนี้จะไม่พบหน้าจอ variance-dashboard เฉพาะทางก็ตาม
- **Lot Tracking**: สำหรับสินค้าที่ควบคุม lot การเลือก lot ตอนบริโภคถูกคำนวณโดยอัตโนมัติผ่าน FIFO (`getAvailableFifoLots` / `consumeFifoLots` ใน inventory-transaction service) — ไม่พบ lot-selection UI ใน SR frontend ดังนั้นนี่ไม่ใช่ action ที่ store keeper เลือกด้วยมือ lot ที่ถูกบริโภคจริงดูได้ภายหลังบนแท็บ **Stock Movement** (`GET .../store-requisitions/:id/stock-movements`, 2026-08-27) ซึ่งคืน preview ที่สร้างจากบรรทัด SR (`is_posted = false`, lot `-`, cost `0`) จนกว่าเอกสารจะ complete
- **วันที่เอกสารกับ open period** (2026-09-18): `sr_date` ของ draft เป็นเพียง placeholder ตอน submit backend จะเก็บวันที่วันนี้ไว้หากวันนี้อยู่ใน inventory period ที่เปิด; มิฉะนั้นคืน `SR_DATE_PATTERN_REQUIRED` (422) และ client ส่งใหม่พร้อม `sr_date_pattern = "open-period"` (วันสุดท้ายของ open period ปัจจุบัน) หรือ `"today"` ขั้น issue ทำซ้ำกฎเดียวกันด้วย `issue_date_pattern` แต่ `"today"` ที่อยู่นอกทุก open period จะถูกปฏิเสธ (`SR_ISSUE_DATE_TODAY_OUTSIDE_PERIOD`) เพราะ stock movement ต้องลงใน period ที่เปิด frontend แสดงทั้งสองกรณีเป็น dialog สองปุ่ม (`sr-date-pattern-dialog.tsx`)

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| Outlet Manager / Requester | ระบุความต้องการสต๊อกที่สถานที่บริโภค สร้าง SR เพิ่มรายการสินค้าพร้อมปริมาณที่ขอและวันที่ต้องการ แนบโน้ตประกอบ และ submit เอกสารเพื่อขออนุมัติ (ปุ่ม Submit ใช้ได้บนฟอร์มใหม่ที่ยังไม่บันทึก — client จะ create แล้ว submit ในคราวเดียว) ติดตามสถานะจนกระทั่ง fulfil สามารถ Duplicate SR ที่บันทึกแล้ว (`/new?duplicate_id=`) และลบ / batch-delete ได้เฉพาะ draft ของตนเอง |
| Approver / Department Head | review คำขอที่ submit แล้วเทียบกับความจำเป็นเชิงปฏิบัติการและความพร้อมที่ต้นทาง อนุมัติ ตัด `approved_qty` ลงจาก `requested_qty` reject รายการ หรือส่งกลับเพื่อแก้ไข ลายเซ็นต่อบรรทัดถูกเก็บไว้สำหรับการตรวจสอบ |
| Store Keeper / Fulfiller | กระทำที่ขั้น workflow ใดก็ตามที่ถูกแท็กไว้สำหรับการ issue — เป็น action approve แบบเดียวกับที่ Approver ใช้ — และบันทึก `issued_qty` ต่อบรรทัด (ซึ่งอาจน้อยกว่า `approved_qty` หากสต๊อกขาด) ไม่มี endpoint "commit" เฉพาะที่แยกจาก approve และไม่มี lot-selection UI (lot ถูกเลือกอัตโนมัติโดย FIFO) |

ไม่พบ backend role หรือ workflow stage เฉพาะสำหรับ "Receiver", "Inventory Controller", หรือ "Finance" ในโมดูลนี้ — ดู [03-user-flow-receiver.md](/th/inventory/store-requisition/03-user-flow-receiver) และ [03-user-flow-audit-config.md](/th/inventory/store-requisition/03-user-flow-audit-config) สำหรับการแก้ไขฉบับเต็ม

## 5. โมดูลที่เกี่ยวข้อง

**การไหลข้ามโมดูล:**
- [inventory](/th/inventory/inventory) — การออก requisition post stock OUT movement ที่ต้นทางและ stock IN movement ที่ปลายทาง (หรือ OUT ครั้งเดียวสำหรับการบริโภค); การเคลื่อนย้ายลงวันที่ตามวันที่ issue ที่ resolve แล้ว (`doc_date`) และถูกวางใน period ของวันที่นั้น
- [inventory-adjustment/wastage-reporting](/th/inventory/inventory-adjustment/wastage-reporting) — หน้าจอ *Store Operation* ข้างเคียง (`/store-operation/wastage-reporting`) ที่ตัดจำหน่าย lot GRN ใกล้หมดอายุเป็น Stock Out ที่ commit แล้ว; เอกสารอยู่ใต้ inventory-adjustment ไม่ใช่ที่นี่
- [costing](/th/inventory/costing) — ปริมาณที่จ่ายถูกคิดต้นทุนตามต้นทุนปัจจุบันของสถานที่ต้นทาง
- [recipe](/th/inventory/recipe) — recipe อาจสร้าง requisition อัตโนมัติสำหรับวัตถุดิบที่ต้องการ
- [good-receive-note](/th/inventory/good-receive-note) — การโอนย้ายระหว่างสถานที่อาจใช้ SR + GRN คู่กัน

**Master configuration:**
- [master-data/unit](/th/inventory/master-data/unit) — หน่วยนับสำหรับแต่ละบรรทัด requisition
- [master-data/location](/th/inventory/master-data/location) — สถานที่ต้นทาง (issuing) และปลายทาง (receiving) บนส่วนหัว requisition
- [master-data/department](/th/inventory/master-data/department) — แผนกผู้ขอ / cost-centre ที่ต้นทุนที่จ่ายไปลง
- [system-config/workflow](/th/inventory/system-config/workflow) — นิยาม workflow อนุมัติสำหรับการอนุญาต requisition
- [system-config/dimension](/th/inventory/system-config/dimension) — มิติเชิงวิเคราะห์ที่ stamp บนบรรทัดของ requisition
- [system-config/running-code](/th/inventory/system-config/running-code) — การกำหนดลำดับเลขเอกสาร SR (type `STORE-REQUISITION`; เลขที่ถูกออกตอน submit จาก `sr_date` ที่ freeze แล้ว, draft ใช้ `draft-<hex>`)
- [system-config/inventory-period](/th/inventory/system-config/period) — การตรวจสอบ open-period เบื้องหลัง `sr_date_pattern` / `issue_date_pattern`
- [access-control/user-location](/th/inventory/access-control/user-location) — จำกัดสถานที่ต้นทางและปลายทางที่ผู้ใช้ทำธุรกรรมระหว่างกันได้
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — log การเปลี่ยนสถานะ requisition และประวัติการอนุมัติสำหรับการตรวจสอบ

## 6. แหล่งอ้างอิง

- Concepts: `../carmen/docs/store-requisitions/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. หน้าในโมดูลนี้

- [01 — โมเดลข้อมูล](/th/inventory/store-requisition/01-data-model) — เอนทิตี Prisma (`tb_store_requisition`, `tb_store_requisition_detail`, comment tables), enum (`enum_doc_status`, `enum_sr_type`), ความสัมพันธ์ และจุดที่ต่างจาก carmen/docs
- [01a — โมเดลข้อมูล — ตารางคอมเมนต์](/th/inventory/store-requisition/01a-data-model-comments) — ตารางคอมเมนต์ / ไฟล์แนบระดับเอกสารและระดับบรรทัด พร้อมการแยก user/system ผ่าน `enum_comment_type`
- [02 — กติกาทางธุรกิจ](/th/inventory/store-requisition/02-business-rules) — Validation (`SR_VAL_*`), การคำนวณ (`SR_CALC_*`, quantity invariant), การกำหนดสิทธิ์ (`SR_AUTH_*`), การ posting (`SR_POST_*`, posting event ครั้งเดียวที่ขั้น workflow สุดท้ายเดินหน้า) และกฎข้ามโมดูล (`SR_XMOD_*`)
- [03 — User Flow](/th/inventory/store-requisition/03-user-flow) — ภาพรวมวงจรชีวิตเอกสารและไฟล์ flow ตาม persona:
  - [Requester](/th/inventory/store-requisition/03-user-flow-requester) — Outlet Manager: ระบุความต้องการ สร้าง SR submit
  - [Approver](/th/inventory/store-requisition/03-user-flow-approver) — Department Head: review ตัด reject ส่งกลับ
  - [Fulfiller](/th/inventory/store-requisition/03-user-flow-fulfiller) — Store Keeper: บันทึก `issued_qty` ที่ขั้น issuance (action approve แบบเดียวกัน; lot ถูกเลือกอัตโนมัติ ไม่ใช่เลือกด้วยมือ)
  - [Receiver](/th/inventory/store-requisition/03-user-flow-receiver) — **แก้ไขรอบนี้:** ไม่พบ backend role หรือกลไก discrepancy-flag ที่ตรงกัน ดูรายละเอียดในหน้านั้นว่าอะไรได้รับการยืนยันบ้าง
  - [Audit / Config](/th/inventory/store-requisition/03-user-flow-audit-config) — **แก้ไขรอบนี้:** ไม่พบ RBAC console, การตรวจสอบ GL, หรือ config การผ่อนปรน SoD ที่ตรงกัน ดูรายละเอียดในหน้านั้นว่าอะไรได้รับการยืนยันบ้าง
- [04 — Test Scenarios](/th/inventory/store-requisition/04-test-scenarios) — scenario ข้าม persona + การ mapping ไปยัง Playwright พร้อมการเจาะลึกตาม persona:
  - [Requester scenarios](/th/inventory/store-requisition/04-test-scenarios-requester)
  - [Approver scenarios](/th/inventory/store-requisition/04-test-scenarios-approver)
  - [Fulfiller scenarios](/th/inventory/store-requisition/04-test-scenarios-fulfiller)
  - [Receiver scenarios](/th/inventory/store-requisition/04-test-scenarios-receiver) — แก้ไขรอบนี้
  - [Audit / Config scenarios](/th/inventory/store-requisition/04-test-scenarios-audit-config) — แก้ไขรอบนี้
- [Stock Replenishment](/th/inventory/store-requisition/stock-replenishment) — คู่ขนานที่ขับเคลื่อนด้วย policy ของ flow SR แบบ manual: `GET /api/{bu}/stock-replenishment` แสดงรายการแถว `tb_product_location` ที่ต่ำกว่า par และ `POST .../stock-replenishment/sr` สร้าง draft SR จากรายการเหล่านั้น (API จริงตั้งแต่ 2026-08; ไม่มี cron)
