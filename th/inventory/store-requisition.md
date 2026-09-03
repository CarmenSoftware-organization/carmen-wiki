---
title: ใบเบิกของสโตร์ (Store Requisition)
description: เอกสารคำขอภายในเพื่อเบิกสต๊อกจากคลังหรือสโตร์กลางไปยังจุดที่บริโภค (ครัว บาร์ เอาท์เลต)
published: true
date: 2026-07-15T12:00:00.000Z
tags: store-requisition, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# ใบเบิกของสโตร์ (Store Requisition)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** เอกสารเคลื่อนย้ายสต๊อกภายใน — `Issue` (ไปยังปลายทางแบบลงค่าใช้จ่ายตรง) หรือ `Transfer` (เคลื่อนย้ายระหว่างสถานที่) พร้อม workflow อนุมัติและการติดตามปริมาณสามค่า (ขอ / อนุมัติ / จ่ายจริง) &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Outlet Manager / Requester, Approver, Store Keeper / Fulfiller &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_store_requisition`, `tb_store_requisition_detail`, `tb_inventory_transaction`, `enum_doc_status`, `enum_sr_type` &nbsp;·&nbsp; **หน้าย่อย:** 16
> ⚠️ **รอบนี้พบว่า `StockMovement` และ `JournalEntry` เคยถูกบันทึกไว้ว่าเป็นตารางที่ SR เป็นเจ้าของ — ทั้งสองไม่มีอยู่จริงใน Prisma; ข้อมูล stock movement และ journal-entry อยู่บนตระกูล `tb_inventory_transaction` ที่ใช้ร่วมกัน (ดู [01-data-model.md](/th/inventory/store-requisition/01-data-model) §5) นอกจากนี้ยังพบว่า persona "Receiver", การ post GL/journal-entry, การบังคับ segregation-of-duties, การ delegate การอนุมัติ/value-threshold, และการเลือก lot โดย store keeper ไม่มี code รองรับ — ดูหน้า persona ที่แก้ไขแล้วและ Discrepancy entry ใน progress-log ของโมดูล

![ใบเบิกของสโตร์ (Store Requisition) screen](/screenshots/store-requisition/index.png)

![ใบเบิกของสโตร์ (Store Requisition) detail screen](/screenshots/store-requisition/detail.png)

## 1. ภาพรวม

**ใบเบิกของสโตร์ (Store Requisition — SR)** คือเอกสารภายในที่สถานที่หนึ่งใช้เบิกสต๊อกจากอีกสถานที่หนึ่ง — โดยทั่วไปคือเอาท์เลตที่บริโภค (ครัว บาร์ ภัตตาคาร แบงเควต) ขอสินค้าจากสโตร์กลางหรือสโตร์หลัก SR แต่ละใบประกอบด้วยส่วนหัว (เลขที่อ้างอิง วันที่ สถานที่ต้นทาง/ที่ขอเบิก สถานที่ปลายทาง ประเภทการเคลื่อนย้าย คำอธิบาย สถานะ) และรายการสินค้าหนึ่งรายการขึ้นไปที่ระบุสินค้า หน่วยนับ ปริมาณที่ขอ ปริมาณที่อนุมัติ และปริมาณที่จ่ายจริง ไม่มีคอลัมน์การเงินบนส่วนหัวหรือบรรทัดของ SR — ราคาต้นทุนต่อหน่วยและยอดรวมต่อบรรทัดถูกอ่านจาก inventory transaction ที่ลิงก์ในเวลาแสดงผล (ดู [01-data-model.md](/th/inventory/store-requisition/01-data-model) §5) ประเภทการเคลื่อนย้าย — `Issue` (การบริโภคไปยังปลายทางแบบลงค่าใช้จ่ายตรง) หรือ `Transfer` (การเคลื่อนย้ายสต๊อกระหว่างสถานที่) — เป็นตัวกำหนดว่า stock-movement records แบบใดจะถูกเขียน

SR ดำเนินผ่านวงจรชีวิตที่ยืนยันแล้ว: `draft` → `in_progress` → `completed` (`enum_doc_status` ที่ใช้ร่วมกับโมดูลอื่นอีกหลายตัว) การกระทำเดียวที่ผู้อนุมัติ/ผู้ issue ใช้จบเอกสารก่อนกำหนดคือการตั้ง `doc_status = voided` โดยตรง — ไม่มีผลลัพธ์ `cancelled` แยกต่างหากที่ code path ปัจจุบันใด ๆ เข้าถึงได้ (enum นิยามค่า `cancelled` ไว้ก็จริง แต่ไม่มี service method ใดของ SR ที่ตั้งค่านี้ — ดู [01-data-model.md](/th/inventory/store-requisition/01-data-model) §5 และ [02-business-rules.md](/th/inventory/store-requisition/02-business-rules) §5) flow รองรับการ fulfill บางส่วนที่ระดับบรรทัด ดังนั้นคำขอ 10 หน่วยอาจถูกจ่ายเพียง 8 และทุก transition จะถูก log พร้อมผู้ใช้ timestamp และโน้ตสำหรับการตรวจสอบ

โมดูล SR คือ system of record สำหรับการเคลื่อนย้ายสต๊อกภายในระหว่างสถานที่ เมื่อขั้น workflow สุดท้ายเดินหน้า (ไม่ว่าจะเป็นขั้นใดก็ตาม — action "approve" แบบเดียวกันถูกใช้ในทุกขั้น รวมถึงขั้นที่ store keeper กระทำ) ระบบจะตรวจสอบความพร้อมสด ๆ ที่ต้นทาง บันทึกการเคลื่อนย้าย OUT ที่ต้นทาง และในกรณี `Transfer` คือการเคลื่อนย้าย IN คู่กันที่ปลายทาง ผ่านตระกูล `tb_inventory_transaction` ที่ใช้ร่วมกัน ไม่มีตาราง `JournalEntry` หรือ `StockMovement` อยู่ในโมดูลนี้ — ดู correction note ที่ด้านบนของหน้านี้

## 2. บริบททางธุรกิจ

ในธุรกิจโรงแรม สโตร์กลางซื้อและถือสต๊อกแบบ bulk แต่ต้นทุนสินค้าที่บริโภคจริงต้องลงที่เอาท์เลตที่บริโภค — ครัว บาร์ ฝ่ายแบงเควต ใบเบิกของสโตร์คือกลไกควบคุมที่ทำให้สโตร์กลางสามารถปล่อยสต๊อกออกไปยังสถานที่ที่บริโภคได้พร้อมสร้าง paper trail ที่ผูกต้นทุนเข้ากับ cost centre ที่ถูกต้อง หากไม่มีกลไกควบคุมนี้ การรายงาน food cost ต่อเอาท์เลตจะเป็นไปไม่ได้ เมื่อมีแล้ว วัตถุดิบทุกหน่วยที่จ่ายออกไปสามารถสืบย้อนได้จากชั้นสโตร์จนถึงจาน

Approval workflow มีอยู่เพราะสต๊อกภายในคือเงินจริง เอาท์เลตจะดึงจากสโตร์กลางตามใจไม่ได้ — คำขอถูก review เทียบกับความจำเป็นเชิงปฏิบัติการและสต๊อกคงเหลือที่ต้นทาง ผู้อนุมัติสามารถลดปริมาณที่ขอก่อนจ่าย, reject รายการที่ไม่มีเหตุผลรองรับ หรือส่งเอกสารกลับพร้อมความคิดเห็น การออกแบบนี้มีเจตนาเพื่อป้องกันการจ่ายเกินและแยกพนักงานที่ขอสต๊อกออกจากพนักงานที่ปล่อยสต๊อก — แต่ไม่พบการตรวจสอบ segregation-of-duties (requester ≠ approver, approver ≠ issuer) ใด ๆ ใน backend หรือ frontend code ปัจจุบัน ให้ถือว่า SoD เป็นเพียงเจตนาที่บันทึกไว้ ไม่ใช่การควบคุมที่บังคับใช้จริง จนกว่าจะมีการยืนยันเป็นอย่างอื่น

Costing ใช้วิธีปัจจุบันของสถานที่ต้นทาง — weighted-average หรือ FIFO — ดังนั้นมูลค่าที่เคลื่อนย้ายสอดคล้องกับวิธีที่ต้นทางประเมินสต๊อกที่เหลือ การ post GL/journal-entry จากการ issue SR ยังไม่ได้รับการยืนยัน: การค้นหาทั่ว repo สำหรับ `journal`, `ledger` และคำที่เกี่ยวข้องในโมดูล SR และ dependency ของ inventory-transaction ไม่พบผลลัพธ์ใด ๆ

## 3. แนวคิดสำคัญ

- **Source Location (Requested From)**: สถานที่ที่ถือสต๊อกที่ถูกเบิก — โดยทั่วไปคือสโตร์หลักหรือคลังกลาง เก็บที่ส่วนหัวเป็น `from_location_id` / `from_location_name` วิธี costing ของต้นทาง (weighted-average หรือ FIFO) เป็นตัวกำหนดต้นทุนต่อหน่วยที่ใช้กับทุกรายการที่จ่ายออก และความพร้อมที่ต้นทางถูกตรวจสอบทั้งตอน submit และอีกครั้งตอนขั้น workflow สุดท้ายเดินหน้าเพื่อป้องกัน negative stock
- **Destination Location (Request To)**: สถานที่ที่บริโภคหรือรับ — ครัว บาร์ เอาท์เลต หรือสโตร์สต๊อกอีกแห่ง เก็บเป็น `to_location_id` / `to_location_name` ค่า `location_type` ของปลายทาง (`direct` สำหรับการบริโภคที่ cost-centre, `inventory` สำหรับการเก็บสต๊อกต่อ) คือสิ่งที่ควบคุมประเภทการเคลื่อนย้ายที่อนุญาต: `Issue` ต้องการปลายทางแบบ direct-cost, `Transfer` ต้องการปลายทางแบบ inventory
- **Movement Type (Issue vs Transfer)**: `Issue` post stock OUT ครั้งเดียวที่ต้นทาง — ใช้เมื่อสต๊อกออกจากคลังและถูกบริโภคทันที (เบิกครัว เบิกบาร์) `Transfer` post stock OUT ที่ต้นทางและ stock IN ที่ปลายทางคู่กัน — ใช้เมื่อสต๊อกเคลื่อนย้ายระหว่างสองสถานที่ที่ถือสต๊อกโดยยังไม่ถูกบริโภค
- **Approval Workflow**: SR ถูกจัดเส้นทางผ่านหนึ่งขั้นหรือมากกว่าตามการตั้งค่า `tb_workflow` ของ tenant (workflow engine แบบเดียวกับที่ PR/PO/GRN ใช้) ผู้อนุมัติสามารถอนุมัติบรรทัดแบบเต็ม ตัดลง reject (รวมอยู่ใน approve call เดียวกันกับบรรทัดที่อนุมัติอื่น ๆ) หรือส่งเอกสารทั้งใบกลับเพื่อแก้ไข ยังมี action reject ทั้งเอกสารแยกต่างหาก ซึ่งในฟอร์มปัจจุบันถูกเปิดใช้ก็ต่อเมื่อ "ทุกบรรทัดถูกทำเครื่องหมาย reject" — action นี้ตั้ง `doc_status = voided` โดยตรง ไม่ใช่สถานะ `cancelled` แยกต่างหาก ไม่พบการจัดเส้นทางตาม value-threshold, การ delegate, หรือ SLA-timeout escalation ใด ๆ ใน source ปัจจุบัน — ให้ถือว่าข้อกล่าวอ้างเหล่านี้ยังไม่ได้รับการยืนยัน
- **Requested vs Approved vs Issued Quantity**: ปริมาณสามค่าต่อบรรทัดเล่าเรื่องราวทั้งหมด `requested_qty` คือสิ่งที่เอาท์เลตขอ; `approved_qty` คือสิ่งที่ผู้อนุมัติอนุญาต (≤ `requested_qty`); `issued_qty` คือสิ่งที่ถูกปล่อยจริงตอนขั้นสุดท้าย (≤ `approved_qty`) ตัวเลขสามตัวนี้เมื่อรวมจาก SR หลาย ๆ ใบ ขับเคลื่อนการวิเคราะห์ variance
- **Variance (Requested − Issued)**: ช่องว่างระหว่างสิ่งที่ขอกับสิ่งที่จ่ายจริง บันทึกต่อบรรทัด variance เกิดจากการที่ผู้อนุมัติตัดลงหรือการ fulfill บางส่วน การติดตาม variance ตามเวลาอาจเผยให้เห็นการขอเกินเรื้อรังหรือปัญหา supply ขาดแคลน แม้ว่ารอบนี้จะไม่พบหน้าจอ variance-dashboard เฉพาะทางก็ตาม
- **Lot Tracking**: สำหรับสินค้าที่ควบคุม lot การเลือก lot ตอนบริโภคถูกคำนวณโดยอัตโนมัติผ่าน FIFO (`getAvailableFifoLots` / `consumeFifoLots` ใน inventory-transaction service) — ไม่พบ lot-selection UI ใน SR frontend ดังนั้นนี่ไม่ใช่ action ที่ store keeper เลือกด้วยมือ

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| Outlet Manager / Requester | ระบุความต้องการสต๊อกที่สถานที่บริโภค สร้าง SR เพิ่มรายการสินค้าพร้อมปริมาณที่ขอและวันที่ต้องการ แนบโน้ตประกอบ และ submit เอกสารเพื่อขออนุมัติ ติดตามสถานะจนกระทั่ง fulfil |
| Approver / Department Head | review คำขอที่ submit แล้วเทียบกับความจำเป็นเชิงปฏิบัติการและความพร้อมที่ต้นทาง อนุมัติ ตัด `approved_qty` ลงจาก `requested_qty` reject รายการ หรือส่งกลับเพื่อแก้ไข ลายเซ็นต่อบรรทัดถูกเก็บไว้สำหรับการตรวจสอบ |
| Store Keeper / Fulfiller | กระทำที่ขั้น workflow ใดก็ตามที่ถูกแท็กไว้สำหรับการ issue — เป็น action approve แบบเดียวกับที่ Approver ใช้ — และบันทึก `issued_qty` ต่อบรรทัด (ซึ่งอาจน้อยกว่า `approved_qty` หากสต๊อกขาด) ไม่มี endpoint "commit" เฉพาะที่แยกจาก approve และไม่มี lot-selection UI (lot ถูกเลือกอัตโนมัติโดย FIFO) |

ไม่พบ backend role หรือ workflow stage เฉพาะสำหรับ "Receiver", "Inventory Controller", หรือ "Finance" ในโมดูลนี้ — ดู [03-user-flow-receiver.md](/th/inventory/store-requisition/03-user-flow-receiver) และ [03-user-flow-audit-config.md](/th/inventory/store-requisition/03-user-flow-audit-config) สำหรับการแก้ไขฉบับเต็ม

## 5. โมดูลที่เกี่ยวข้อง

**การไหลข้ามโมดูล:**
- [inventory](/th/inventory/inventory) — การออก requisition post stock OUT movement ที่ต้นทางและ stock IN movement ที่ปลายทาง (หรือ OUT ครั้งเดียวสำหรับการบริโภค)
- [costing](/th/inventory/costing) — ปริมาณที่จ่ายถูกคิดต้นทุนตามต้นทุนปัจจุบันของสถานที่ต้นทาง
- [recipe](/th/inventory/recipe) — recipe อาจสร้าง requisition อัตโนมัติสำหรับวัตถุดิบที่ต้องการ
- [good-receive-note](/th/inventory/good-receive-note) — การโอนย้ายระหว่างสถานที่อาจใช้ SR + GRN คู่กัน

**Master configuration:**
- [master-data/unit](/th/inventory/master-data/unit) — หน่วยนับสำหรับแต่ละบรรทัด requisition
- [master-data/location](/th/inventory/master-data/location) — สถานที่ต้นทาง (issuing) และปลายทาง (receiving) บนส่วนหัว requisition
- [master-data/department](/th/inventory/master-data/department) — แผนกผู้ขอ / cost-centre ที่ต้นทุนที่จ่ายไปลง
- [system-config/workflow](/th/inventory/system-config/workflow) — นิยาม workflow อนุมัติสำหรับการอนุญาต requisition
- [system-config/dimension](/th/inventory/system-config/dimension) — มิติเชิงวิเคราะห์ที่ stamp บนบรรทัดของ requisition
- [system-config/running-code](/th/inventory/system-config/running-code) — การกำหนดลำดับเลขเอกสาร SR
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
- [Stock Replenishment](/th/inventory/store-requisition/stock-replenishment) — คู่ขนานที่ออกแบบให้ขับเคลื่อนด้วย policy ของ flow SR แบบ manual (threshold min/max/par บน `tb_product_location` สร้าง draft `tb_store_requisition`); **หน้าจอ frontend ปัจจุบันขับเคลื่อนด้วย mock data และไม่พบการ implement ฝั่ง backend/cron จริง** — ดู warning สถานะการ implement ในหน้านั้น
