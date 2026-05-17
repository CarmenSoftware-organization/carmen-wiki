---
title: ใบเบิกของสโตร์ (Store Requisition)
description: เอกสารคำขอภายในเพื่อเบิกสต๊อกจากคลังหรือสโตร์กลางไปยังจุดที่บริโภค (ครัว บาร์ เอาท์เลต)
published: true
date: 2026-05-17T07:00:36.000Z
tags: store-requisition, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# ใบเบิกของสโตร์ (Store Requisition)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** เอกสารเคลื่อนย้ายสต๊อกภายใน — `Issue` (ไปยังปลายทางแบบลงค่าใช้จ่ายตรง) หรือ `Transfer` (เคลื่อนย้ายระหว่างสถานที่) พร้อม workflow อนุมัติและการติดตามปริมาณสามค่า (ขอ / อนุมัติ / จ่ายจริง) &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Outlet Manager / Requester, Approver, Store Keeper / Fulfiller, Receiver, Inventory Controller, Finance &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_store_requisition`, `tb_store_requisition_detail`, `StockMovement`, `JournalEntry`, `enum_doc_status`, `enum_sr_type` &nbsp;·&nbsp; **หน้าย่อย:** 15

![ใบเบิกของสโตร์ (Store Requisition) screen](/assets/screenshots/store-requisition/index.png)

## 1. ภาพรวม

**ใบเบิกของสโตร์ (Store Requisition — SR)** คือเอกสารภายในที่สถานที่หนึ่งใช้เบิกสต๊อกจากอีกสถานที่หนึ่ง — โดยทั่วไปคือเอาท์เลตที่บริโภค (ครัว บาร์ ภัตตาคาร แบงเควต) ขอสินค้าจากสโตร์กลางหรือสโตร์หลัก SR แต่ละใบประกอบด้วยส่วนหัว (เลขที่อ้างอิง วันที่ สถานที่ต้นทาง/ที่ขอเบิก สถานที่ปลายทาง ประเภทการเคลื่อนย้าย คำอธิบาย สถานะ ยอดรวม) และรายการสินค้าหนึ่งรายการขึ้นไปที่ระบุสินค้า หน่วยนับ ปริมาณที่ขอ ปริมาณที่อนุมัติ ปริมาณที่จ่ายจริง ราคาต้นทุนต่อหน่วย และยอดรวมต่อบรรทัด ประเภทการเคลื่อนย้าย — `Issue` (การบริโภคไปยังปลายทางแบบลงค่าใช้จ่ายตรง) หรือ `Transfer` (การเคลื่อนย้ายสต๊อกระหว่างสถานที่) — เป็นตัวกำหนดทั้ง stock-movement records และ journal entries ที่ถูกสร้างจากการ post

SR ดำเนินผ่านวงจรชีวิตที่ควบคุม: `Draft` (แก้ไขได้ ยังไม่กระทบใด ๆ) → `In Process` (submit เพื่อขออนุมัติ) → `Approved` (ผู้อนุมัติอาจลดปริมาณที่ขอหรือ reject รายการ) → `Issued` (สถานที่ต้นทาง commit สต๊อก OUT และระบบเขียน stock-movement record) → `Received` / `Complete` ที่ปลายทาง หรือ `Reject` / `Void` สำหรับการยกเลิกที่จุดสิ้นสุด flow รองรับการ fulfill บางส่วนที่ระดับบรรทัด ดังนั้นคำขอ 10 หน่วยอาจถูกจ่ายเพียง 8 ส่วนที่เหลือถูก reject หรือ back-order และทุก transition จะถูก log พร้อมผู้ใช้ timestamp และโน้ตสำหรับการตรวจสอบ

โมดูล SR คือ system of record สำหรับการเคลื่อนย้ายสต๊อกภายในระหว่างสถานที่ บังคับใช้ approval routing, จองสต๊อกหลังอนุมัติ, ตรวจสอบความพร้อมที่ต้นทางก่อนจ่าย, บันทึกการเคลื่อนย้าย OUT ที่ต้นทางและ IN ที่ปลายทางในกรณี transfer และสร้าง cost-allocation journal entries ที่ย้ายค่าใช้จ่ายจากบัญชีสต๊อกของสโตร์กลางไปยัง cost centre ของเอาท์เลตที่บริโภค

## 2. บริบททางธุรกิจ

ในธุรกิจโรงแรม สโตร์กลางซื้อและถือสต๊อกแบบ bulk แต่ต้นทุนสินค้าที่บริโภคจริงต้องลงที่เอาท์เลตที่บริโภค — ครัว บาร์ ฝ่ายแบงเควต ใบเบิกของสโตร์คือกลไกควบคุมที่ทำให้สโตร์กลางสามารถปล่อยสต๊อกออกไปยังสถานที่ที่บริโภคได้พร้อมสร้าง paper trail ที่ผูกต้นทุนเข้ากับ cost centre ที่ถูกต้อง หากไม่มีกลไกควบคุมนี้ การรายงาน food cost ต่อเอาท์เลตจะเป็นไปไม่ได้ เมื่อมีแล้ว วัตถุดิบทุกหน่วยที่จ่ายออกไปสามารถสืบย้อนได้จากชั้นสโตร์จนถึงจาน และผู้จัดการเอาท์เลตทุกคนสามารถถูกตรวจสอบความรับผิดชอบต่อต้นทุนที่เบิกเทียบกับงบประมาณได้

Approval workflow มีอยู่เพราะสต๊อกภายในคือเงินจริง เอาท์เลตจะดึงจากสโตร์กลางตามใจไม่ได้ — คำขอถูก review เทียบกับความจำเป็นเชิงปฏิบัติการ par level สต๊อกคงเหลือที่ต้นทาง และงบประมาณ ผู้อนุมัติสามารถลดปริมาณที่ขอก่อนจ่าย, reject รายการที่ไม่มีเหตุผลรองรับ หรือส่งเอกสารกลับพร้อมความคิดเห็น ซึ่งทั้งป้องกันการจ่ายเกิน (ซึ่งทำให้ต้นทุนเอาท์เลตพอง หรือทำให้สโตร์ขาดสำหรับเอาท์เลตอื่น) และสร้าง segregation of duties ระหว่างพนักงานที่ขอสต๊อกกับพนักงานที่ปล่อยสต๊อก

ทางการเงิน การ post issuance ทุกครั้งสร้าง journal entries ที่ credit บัญชีสต๊อกของสถานที่ต้นทาง และ debit บัญชีสต๊อกของสถานที่ปลายทาง (สำหรับ `Transfer`) หรือ debit บัญชีค่าใช้จ่ายในการบริโภคของปลายทางบน cost-centre (สำหรับ `Issue`) Costing ใช้วิธีปัจจุบันของสถานที่ต้นทาง — weighted-average หรือ FIFO — ดังนั้นมูลค่าที่เคลื่อนย้ายสอดคล้องกับวิธีที่ต้นทางประเมินสต๊อกที่เหลือ และการรายงาน food-cost ต่อเอาท์เลต roll up ได้สะอาดจาก journal entries ที่ขับเคลื่อนโดย SR

## 3. แนวคิดสำคัญ

- **Source Location (Requested From)**: สถานที่ที่ถือสต๊อกที่ถูกเบิก — โดยทั่วไปคือสโตร์หลักหรือคลังกลาง เก็บที่ส่วนหัวเป็น `movement.source` / `movement.sourceName` วิธี costing ของต้นทาง (weighted-average หรือ FIFO) เป็นตัวกำหนดต้นทุนต่อหน่วยที่ใช้กับทุกรายการที่จ่ายออก และความพร้อมที่ต้นทางถูกตรวจสอบทั้งตอนสร้าง (`SR_CRT_006`) และอีกครั้งตอนจ่ายเพื่อป้องกัน negative stock
- **Destination Location (Request To)**: สถานที่ที่บริโภคหรือรับ — ครัว บาร์ เอาท์เลต หรือสโตร์สต๊อกอีกแห่ง เก็บเป็น `movement.destination` / `movement.destinationName` ค่า `locationType` ของปลายทาง (`direct` สำหรับการบริโภคที่ cost-centre, `inventory` สำหรับการเก็บสต๊อกต่อ) คือสิ่งที่ควบคุมประเภทการเคลื่อนย้ายที่อนุญาต: `Issue` ต้องการปลายทางแบบ direct-cost, `Transfer` ต้องการปลายทางแบบ inventory
- **Movement Type (Issue vs Transfer)**: `Issue` post stock OUT ครั้งเดียวที่ต้นทางและส่งมูลค่าไปยังบัญชีค่าใช้จ่ายการบริโภคของปลายทาง — ใช้เมื่อสต๊อกออกจากคลังและถูกบริโภคทันที (เบิกครัว เบิกบาร์) `Transfer` post stock OUT ที่ต้นทางและ stock IN ที่ปลายทางคู่กัน — ใช้เมื่อสต๊อกเคลื่อนย้ายระหว่างสองสถานที่ที่ถือสต๊อกโดยยังไม่ถูกบริโภค การเลือกประเภทกำหนดทั้ง journal entries ที่ถูกเขียนและเอกสารปลายน้ำ (เช่น GRN คู่กัน) ที่อาจเกี่ยวข้อง
- **Approval Workflow**: SR ถูกจัดเส้นทางอนุมัติตามกฎที่ตั้งค่าได้ (role, threshold มูลค่า, location) ผู้อนุมัติสามารถ `Approve`, `Reject` (พร้อมเหตุผลบังคับ), `Split & Reject` (อนุมัติบางส่วน) หรือ `Send Back` เพื่อให้แก้ไข ผู้อนุมัติอาจแก้ `qtyApproved` ลดลงจาก `qtyRequired` แต่ไม่เกิน ประวัติการอนุมัติ — ผู้กระทำ การกระทำ timestamp ความคิดเห็น — ถูกเก็บไว้สำหรับการตรวจสอบ และการอนุมัติสามารถ delegate ได้
- **Requested vs Approved vs Issued Quantity**: ปริมาณสามค่าต่อบรรทัดเล่าเรื่องราวทั้งหมด `qtyRequired` คือสิ่งที่เอาท์เลตขอ; `qtyApproved` คือสิ่งที่ผู้อนุมัติอนุญาต (≤ `qtyRequired`); `qtyIssued` คือสิ่งที่ store keeper ปล่อยจริงตอน fulfill (≤ `qtyApproved`) ตัวเลขสามตัวนี้เมื่อรวมจาก SR หลาย ๆ ใบ ขับเคลื่อนการวิเคราะห์ variance และการตัดสินใจ supply-planning
- **Variance (Requested − Issued)**: ช่องว่างระหว่างสิ่งที่ขอกับสิ่งที่จ่ายจริง บันทึกต่อบรรทัด variance เกิดจากการที่ผู้อนุมัติตัดลง, สต๊อกขาดที่ต้นทางตอนจ่าย หรือการ fulfill บางส่วน การติดตาม variance ตามเวลาเผยให้เห็นการขอเกินเรื้อรัง การขาดแคลนใน supply และเอาท์เลตที่ระเบียบการเบิกของควรถูก review
- **Cost Center**: บัญชีกลุ่มที่ต้นทุนที่จ่ายออกตกลงที่ปลายทาง — โดยทั่วไปผูกกับเอาท์เลตปลายทาง (Kitchen, Banquet, Bar XYZ) cost-centre ถูก stamp บนทุกบรรทัด journal entry ดังนั้นรายงาน food-cost รายเดือนต่อเอาท์เลต roll up จากการ post SR ได้โดยไม่ต้องจัดสรรด้วยมือ
- **Stock Movement Record**: ทุกบรรทัดที่จ่ายเขียนแถว `StockMovement` หนึ่งแถวที่บันทึก `commitDate`, `postingDate`, สถานที่ต้นทางและปลายทาง, ประเภทการเคลื่อนย้าย, `inQty` / `outQty`, `unitCost`, `totalCost`, รายละเอียด lot (สำหรับสินค้าที่ติดตาม lot) และการอ้างอิงกลับไปยัง SR ต้นกำเนิด นี่คือบันทึก immutable ที่ inventory sub-ledger ใช้กระทบยอด
- **Journal Entry / Cost Allocation**: การ post SR สร้างแถว `JournalEntry` ที่ credit บัญชี GL สต๊อกของต้นทางและ debit ทั้งบัญชีสต๊อกของปลายทาง (Transfer) หรือบัญชีค่าใช้จ่ายการบริโภคของปลายทางบน cost-centre (Issue) entries ต้องบาลานซ์ (debits = credits) และถูกบล็อกหากวันที่ post อยู่ในงวดที่ปิดแล้ว
- **Lot Tracking**: สำหรับสินค้าที่ควบคุม lot SR บันทึกว่าจ่าย lot ใดบ้าง เพื่อรักษา expiry, recall และ lot-cost traceability ตั้งแต่รับสินค้าจนถึงการบริโภค

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| Outlet Manager / Requester | ระบุความต้องการสต๊อกที่สถานที่บริโภค สร้าง SR เพิ่มรายการสินค้าพร้อมปริมาณที่ขอและวันที่ต้องการ แนบโน้ตประกอบ และ submit เอกสารเพื่อขออนุมัติ ติดตามสถานะจนกระทั่งรับของที่เอาท์เลต |
| Approver / Department Head | review คำขอที่ submit แล้วเทียบกับความจำเป็นเชิงปฏิบัติการ par level และความพร้อมที่ต้นทาง อนุมัติ ตัด `qtyApproved` ลงจาก `qtyRequired` reject รายการพร้อมเหตุผล split คำขอ หรือส่งกลับเพื่อแก้ไข ลายเซ็นอนุมัติถูกเก็บไว้สำหรับการตรวจสอบ |
| Store Keeper / Fulfiller | รับคำขอที่อนุมัติแล้วที่สถานที่ต้นทาง หยิบสินค้า บันทึก `qtyIssued` ต่อบรรทัด (ซึ่งอาจน้อยกว่า `qtyApproved` หากสต๊อกขาด) commit stock-movement และปล่อยสินค้า อาจเลือก lot เฉพาะสำหรับสินค้าที่ควบคุม lot |
| Receiver | ยืนยันการรับสินค้าจริงที่ปลายทาง flag ความคลาดเคลื่อนระหว่างปริมาณที่จ่ายและที่รับ และปิดคำขอ |
| Inventory Controller / Manager | กำกับดูแล SR flow ทั้งหมด ตรวจสอบ variance และรูปแบบการ fulfill บางส่วน กระทบยอด inventory sub-ledger กับการ post GL บริหาร threshold การอนุมัติ และเซ็นรับรองกิจกรรมปลายงวด |
| Finance Team | ตรวจสอบการ map cost-centre และ journal entries กระทบยอดรายงาน food-cost ของเอาท์เลตกับการ post SR และมั่นใจว่า cost allocation ระหว่างแผนกถูกต้องตอนปิดงวด |

## 5. โมดูลที่เกี่ยวข้อง

**การไหลข้ามโมดูล:**
- [[inventory]] — การออก requisition post stock OUT movement ที่ต้นทางและ stock IN movement ที่ปลายทาง (หรือ OUT ครั้งเดียวสำหรับการบริโภค)
- [[costing]] — ปริมาณที่จ่ายถูกคิดต้นทุนตามต้นทุนปัจจุบันของสถานที่ต้นทาง
- [[recipe]] — recipe อาจสร้าง requisition อัตโนมัติสำหรับวัตถุดิบที่ต้องการ
- [[good-receive-note]] — การโอนย้ายระหว่างสถานที่อาจใช้ SR + GRN คู่กัน

**Master configuration:**
- [[master-data/unit]] — หน่วยนับสำหรับแต่ละบรรทัด requisition
- [[master-data/location]] — สถานที่ต้นทาง (issuing) และปลายทาง (receiving) บนส่วนหัว requisition
- [[master-data/department]] — แผนกผู้ขอ / cost-centre ที่ต้นทุนที่จ่ายไปลง
- [[system-config/workflow]] — นิยาม workflow อนุมัติสำหรับการอนุญาต requisition
- [[system-config/dimension]] — มิติเชิงวิเคราะห์ที่ stamp บน journal entries ของ issuance
- [[system-config/running-code]] — การกำหนดลำดับเลขเอกสาร SR
- [[access-control/user-location]] — จำกัดสถานที่ต้นทางและปลายทางที่ผู้ใช้ทำธุรกรรมระหว่างกันได้
- [[reporting-audit/activity]] — log การเปลี่ยนสถานะ requisition และประวัติการอนุมัติสำหรับการตรวจสอบ

## 6. แหล่งอ้างอิง

- Concepts: `../carmen/docs/store-requisitions/`
- Frontend: `../carmen-inventory-frontend/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. หน้าในโมดูลนี้

- [01 — โมเดลข้อมูล](./01-data-model.md) — เอนทิตี Prisma (`tb_store_requisition`, `tb_store_requisition_detail`, comment tables), enum (`enum_doc_status`, `enum_sr_type`), ความสัมพันธ์ และจุดที่ต่างจาก carmen/docs
- [02 — กติกาทางธุรกิจ](./02-business-rules.md) — Validation (`SR_VAL_*`), การคำนวณ (`SR_CALC_*`, quantity invariant), การกำหนดสิทธิ์ (`SR_AUTH_*`, SoD), การ posting (`SR_POST_*`, posting event ครั้งเดียวที่ `in_progress → completed`) และกฎข้ามโมดูล (`SR_XMOD_*`)
- [03 — User Flow](./03-user-flow.md) — ภาพรวมวงจรชีวิตเอกสารและไฟล์ flow ตาม persona:
  - [Requester](./03-user-flow-requester.md) — Outlet Manager: ระบุความต้องการ สร้าง SR submit
  - [Approver](./03-user-flow-approver.md) — Department Head: review ตัด reject ส่งกลับ
  - [Fulfiller](./03-user-flow-fulfiller.md) — Store Keeper: หยิบ บันทึก `issued_qty` เลือก lot commit
  - [Receiver](./03-user-flow-receiver.md) — ผู้แทนปลายทาง: ยืนยันการรับ flag ความคลาดเคลื่อน
  - [Audit / Config](./03-user-flow-audit-config.md) — การกำกับดูแลโดย Inventory Controller, Finance, Sysadmin, Auditor
- [04 — Test Scenarios](./04-test-scenarios.md) — scenario ข้าม persona + การ mapping ไปยัง Playwright พร้อมการเจาะลึกตาม persona:
  - [Requester scenarios](./04-test-scenarios-requester.md)
  - [Approver scenarios](./04-test-scenarios-approver.md)
  - [Fulfiller scenarios](./04-test-scenarios-fulfiller.md)
  - [Receiver scenarios](./04-test-scenarios-receiver.md)
  - [Audit / Config scenarios](./04-test-scenarios-audit-config.md)
