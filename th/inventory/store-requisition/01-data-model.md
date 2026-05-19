---
title: ใบเบิกของสโตร์ (Store Requisition) — Data Model
description: เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum ของโมดูล store-requisition
published: true
date: 2026-05-20T00:00:00.000Z
tags: store-requisition, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:30:00.000Z
---

# ใบเบิกของสโตร์ (Store Requisition) — Data Model

> **At a Glance**
> **ตาราง:** `tb_store_requisition` &nbsp;·&nbsp; `tb_store_requisition_detail` &nbsp;·&nbsp; `tb_store_requisition_comment` &nbsp;·&nbsp; `tb_store_requisition_detail_comment`
> **กลุ่มผู้ใช้:** Developer / Auditor (เอกสารอ้างอิงสำหรับ dev)
> **FK สำคัญ:** ส่วนหัว `→ tb_location` ×2 (`from_location_id` + `to_location_id`, named relations) และ `→ tb_workflow` (มี `@relation` ระบุชัด ต่างจาก PR/PO/GRN); รายการ `→ tb_product` และ `→ tb_inventory_transaction` (ถูกบรรจุค่าตอน commit — ข้อมูล lot / cost / expiry ที่เป็น canonical อยู่ฝั่ง inventory)
> **รูปแบบ audit:** `created_*` / `updated_*` / `deleted_*` มาตรฐาน; ปริมาณสามค่าต่อบรรทัด (`requested` / `approved` / `issued`); คอลัมน์ลายเซ็น approval / review / reject ต่อบรรทัด; **ไม่มียอดเงิน roll-up บนส่วนหัว** (SR เป็นเอกสารเชิงปริมาณ)

> **Source of truth:** Prisma schema ฝั่ง backend ให้อ่านสิ่งเหล่านี้ก่อนเสมอเมื่อจะเขียนหรือแก้หน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` ในแต่ละ package เป็นสำเนาที่ถูก generate อัตโนมัติและไม่ใช่ของจริง

## 1. ภาพรวม

โมดูล store-requisition เป็นเจ้าของเอนทิตีบน tenant-schema สี่ตัว: ส่วนหัวเอกสาร SR (`tb_store_requisition`), รายการในเอกสาร (`tb_store_requisition_detail`) และตาราง comment สำหรับ workflow / activity-log ที่ระดับส่วนหัวและระดับบรรทัด (`tb_store_requisition_comment`, `tb_store_requisition_detail_comment`) การติดตามขั้น workflow ไม่ได้อยู่ในตารางเฉพาะ — คอลัมน์ JSON บนส่วนหัว (`workflow_history`, `workflow_current_stage`, `workflow_previous_stage`, `workflow_next_stage`, `user_action`) บวกกับตาราง comment รวมกันคือบันทึกถาวรของ timeline ของ workflow การตั้งค่า `tb_workflow` ที่ใช้ร่วมกันถูกอ้างผ่าน Prisma `@relation` ที่ระบุชัดบน `workflow_id` ไม่มีตาราง `tb_store_requisition_workflow` แยกต่างหาก — `enum_inventory_doc_type` ระบุ `store_requisition` เป็นหนึ่งในเจ็ดประเภทเอกสารที่ขับเคลื่อน journal entries ของการเคลื่อนย้ายสต๊อก แต่สถานะของตัวเอกสาร SR ใช้ `enum_doc_status` ร่วม (`draft / in_progress / completed / cancelled / voided`) ไม่ใช่ enum เฉพาะของ SR

SR วางตัว **ระหว่าง [inventory](/th/inventory/inventory) และฝั่ง cost-centre ที่บริโภค** สถานที่ต้นทาง (`from_location_id` → `tb_location`) โดยทั่วไปคือสโตร์กลางหรือคลัง; สถานที่ปลายทาง (`to_location_id` → `tb_location`) คือเอาท์เลตที่บริโภค (ครัว บาร์ แบงเควต) — ค่า `tb_location.location_type` (`direct` สำหรับการบริโภคที่ cost-centre, `inventory` สำหรับการเก็บสต๊อกต่อ) คือสิ่งที่ควบคุม `sr_type` ที่อนุญาต: `enum_sr_type.issue` ต้องการปลายทางแบบ direct-cost, `enum_sr_type.transfer` ต้องการปลายทางแบบ inventory ตอน commit (`in_progress → completed`) ผลกระทบปลายน้ำของ SR กระจายออก: ทุกบรรทัดเขียน — ผ่าน `tb_store_requisition_detail.inventory_transaction_id` — ลงใน `tb_inventory_transaction` / `tb_inventory_transaction_detail` ซึ่งเป็นที่ที่ stock-OUT จริง (และในกรณี `transfer` คือ stock-IN ที่ปลายทางคู่กัน) ถูกบันทึกพร้อมข้อมูล lot, expiry และ cost-layer; โมดูล `[costing](/th/inventory/costing)` รับผิดชอบราคาต้นทุนต่อหน่วยของแต่ละบรรทัด (weighted-average หรือ FIFO ของสถานที่ต้นทาง); และส่วนหัว SR เปลี่ยนสถานะ `draft → in_progress → completed` (พร้อม `cancelled` และ `voided` เป็นเส้นทางยกเลิกที่จุดสิ้นสุดสองทาง)

จุดทางโครงสร้างที่น่าสังเกต: โมเดลบรรทัดของ SR มี **ปริมาณสามค่าต่อแถว** — `requested_qty`, `approved_qty`, `issued_qty` (ทั้งหมดเป็น `Decimal(20, 5)`) — ซึ่งร่วมกันเล่าเรื่องราวทั้งหมดข้ามวงจรชีวิตสี่สถานะ `requested_qty` คือสิ่งที่ผู้ขอขอ; `approved_qty` คือสิ่งที่ผู้อนุมัติอนุญาต (`≤ requested_qty`); `issued_qty` คือสิ่งที่ store keeper ปล่อยจริงตอน fulfillment (`≤ approved_qty`) ต่างจาก `detail_item` ที่แยกเป็น event-row ของ GRN บรรทัดของ SR เป็นแถวเดียวที่คอลัมน์ของมันเปลี่ยนค่าตามที่เอกสารดำเนินไปในวงจรชีวิต — ไม่มี nested event table ลายเซ็น approval / review / rejection ต่อบรรทัด (`approved_by_id`, `review_by_id`, `reject_by_id` และคอลัมน์ name / date / message ที่ตรงกัน) ถูกเก็บโดยตรงบนบรรทัดสำหรับการตรวจสอบ ควบคู่กับ JSON array `history` ของรายการ actor + decision ทีละขั้น และ JSON object `stages_status` ที่สรุปสถานะปัจจุบันต่อขั้น PRD ของ carmen/docs อธิบายวงจรชีวิตหกสถานะ (`Draft → Submitted → UnderReview → Approved/PartiallyApproved → InProcess → Fulfilled → Completed`) และ enum `RequisitionItem.approvalStatus` (`Accept / Reject / Review`) — ทั้งคู่ต่างจาก `enum_doc_status` ห้าสถานะ canonical บน Prisma และการไม่มี enum สถานะต่อบรรทัด ดูส่วนที่ 5

## 2. เอนทิตี

### 2.1 tb_store_requisition

ส่วนหัวเอกสาร SR บรรจุเลขที่อ้างอิง วันที่ สถานที่ต้นทาง/ปลายทาง ประเภทการเคลื่อนย้าย workflow snapshot บริบทผู้ขอ/แผนก dimension ระดับส่วนหัว (cost-centre / project / job code) และคอลัมน์ audit มาตรฐาน หนึ่งส่วนหัวมีหลาย detail rows และหลาย comments

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key สร้างผ่าน `gen_random_uuid()` |
| `sr_no` | `String @db.VarChar` | No | เลขที่อ้างอิง SR สำหรับมนุษย์อ่าน บังคับ (หมายเหตุ: GRN ของคู่กันยอม null; SR ไม่ยอม) |
| `sr_date` | `DateTime @db.Timestamptz(6)` | Yes | วันที่ requisition — เมื่อเอาท์เลตตั้งคำขอ |
| `expected_date` | `DateTime @db.Timestamptz(6)` | Yes | วันที่เอาท์เลตต้องการของ ใช้สำหรับลำดับความสำคัญในการ fulfill |
| `description` | `String @db.VarChar` | Yes | คำอธิบายแบบอิสระบนส่วนหัว |
| `doc_status` | `enum_doc_status` | No | สถานะเอกสาร; default `draft` enum 5 ค่าที่ใช้ร่วมกัน (ดูส่วนที่ 4) |
| `from_location_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_location.id` — สถานที่ต้นทาง (คลัง/สโตร์หลักที่ปล่อยสต๊อก) named relation `store_requisition_from_location` ยอม null ในช่วง draft แรก |
| `from_location_code` | `String @db.VarChar` | Yes | Snapshot ของรหัสสถานที่ต้นทาง |
| `from_location_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อสถานที่ต้นทาง |
| `to_location_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_location.id` — สถานที่ปลายทาง (เอาท์เลตที่บริโภคหรือสโตร์สต๊อกต่อ) named relation `store_requisition_to_location` ยอม null ในช่วง draft แรก |
| `to_location_code` | `String @db.VarChar` | Yes | Snapshot ของรหัสสถานที่ปลายทาง |
| `to_location_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อสถานที่ปลายทาง |
| `sr_type` | `enum_sr_type` | No | ประเภทการเคลื่อนย้าย; default `transfer` เป็น `issue` (การบริโภคไปยังปลายทางแบบ direct-cost) หรือ `transfer` (การเคลื่อนย้ายสต๊อกระหว่างสถานที่) |
| `workflow_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_workflow.id` ผ่าน named relation `workflow` ต่างจากโมดูล GRN ส่วนหัว SR **ประกาศ** Prisma `@relation` ระบุชัดบน `workflow_id` |
| `workflow_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อ workflow |
| `workflow_history` | `Json @db.JsonB` | Yes | Timeline การเปลี่ยนขั้นแบบ append-only; default `{}` แต่ละ entry เก็บ `stage`, `action`, `message`, `by` (`{id, name}`), `at` |
| `workflow_current_stage` | `String @db.VarChar` | Yes | Slug ของขั้นที่ถือ SR อยู่ปัจจุบัน |
| `workflow_previous_stage` | `String @db.VarChar` | Yes | Slug ของขั้นที่เพิ่งปล่อย SR ออก |
| `workflow_next_stage` | `String @db.VarChar` | Yes | Slug ของขั้นถัดไปในสาย |
| `user_action` | `Json @db.JsonB` | Yes | metadata ของ action ที่รอ default `{}` โดยทั่วไป `{ "execute": [{ "id": "<user-id>" }, ...] }` |
| `last_action` | `enum_last_action` | Yes | Action ล่าสุดที่ทำกับเอกสาร; default `submitted` |
| `last_action_at_date` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp ของ `last_action` |
| `last_action_by_id` | `String @db.Uuid` | Yes | user id ที่ทำ `last_action` |
| `last_action_by_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อผู้กระทำ |
| `requestor_id` | `String @db.Uuid` | Yes | user id ของผู้ขอ (outlet manager ที่ตั้ง SR) ไม่ประกาศ Prisma `@relation` |
| `requestor_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อแสดงผู้ขอ |
| `department_id` | `String @db.Uuid` | Yes | department id ของเอาท์เลตผู้ขอ ไม่ประกาศ Prisma `@relation` |
| `department_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อแผนก |
| `info` | `Json @db.JsonB` | Yes | Extension bag สำหรับ attribute ส่วนหัวเฉพาะ tenant; default `{}` |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array (project, cost-centre, job code, ฯลฯ); default `[]` |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency version counter; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp สร้าง default `now()` |
| `created_by_id` | `String @db.Uuid` | Yes | user id ที่สร้างแถว |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp อัปเดตล่าสุด default `now()` |
| `updated_by_id` | `String @db.Uuid` | Yes | user id ที่อัปเดตล่าสุด |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete; ถ้าไม่ null แปลว่าถูกลบเชิงตรรกะ |

**Constraints:** `@id` บน `id` FKs: `from_location_id → tb_location.id` (`NoAction`, named relation `store_requisition_from_location`); `to_location_id → tb_location.id` (`NoAction`, named relation `store_requisition_to_location`); `workflow_id → tb_workflow.id` (`NoAction`) หมายเหตุ: `requestor_id` และ `department_id` ถูกเก็บเป็น UUID แต่ไม่มี Prisma `@relation` บนโมเดลนี้ — resolve ในชั้น application Back-relations: many `tb_store_requisition_detail`, many `tb_store_requisition_comment`
**Indexes:** `@@unique([sr_no, deleted_at])` ในชื่อ `sr_no_u`; `@@index([sr_no])` ในชื่อ `sr_no_idx`; `@@index([sr_type])` ในชื่อ `sr_type_idx` ต่างจาก `grn_no` (nullable) ของ GRN `sr_no` เป็น `NOT NULL`

### 2.2 tb_store_requisition_comment

รายการ workflow / activity-log ที่ผูกกับส่วนหัว SR ไม่มีตาราง `tb_store_requisition_workflow` เฉพาะ — ตาราง comment นี้ รวมกับคอลัมน์ JSON ของ workflow บนส่วนหัว คือบันทึกถาวรของ timeline ของ workflow แต่ละแถวคือ user comment (`type = user`) หรือ system event (`type = system`) เช่นการเปลี่ยนขั้น

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `store_requisition_id` | `String @db.Uuid` | No | FK ไปยัง `tb_store_requisition.id` |
| `type` | `enum_comment_type` | No | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | Yes | user id ผู้เขียน (null สำหรับ entry แบบ `system`) |
| `message` | `String` | Yes | เนื้อหา comment แบบอิสระ |
| `attachments` | `Json @db.JsonB` | Yes | Array ของ `{ originalName, fileToken, contentType }`; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp สร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp อัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `store_requisition_id → tb_store_requisition.id` (`NoAction` on delete/update)
**Indexes:** ไม่มีประกาศนอกเหนือจาก primary key

### 2.3 tb_store_requisition_detail

รายการของ SR ระบุสินค้าที่ขอเบิกและบรรจุเรื่องราวของปริมาณสามค่า (`requested_qty / approved_qty / issued_qty`) บวกลายเซ็น approval / review / rejection ต่อบรรทัด JSON timeline `history` ต่อบรรทัด และลิงก์ไปยัง inventory transaction ที่บันทึก stock movement จริงตอน commit หมายเหตุ: ต่างจาก GRN บรรทัดของ SR เป็น **แถวเดียว** ตลอดวงจรชีวิต — ไม่มีการแยก event-row แบบ `detail_item`; คอลัมน์ของแถวเปลี่ยนค่าตามที่เอกสารดำเนินจาก `draft → in_progress → completed`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `inventory_transaction_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_inventory_transaction.id` (ประกาศ Prisma `@relation`) ถูกบรรจุค่าตอน commit (`in_progress → completed`); children `tb_inventory_transaction_detail` ของแถวที่ลิงก์เก็บ `lot_no`, `expiry_date` และ `cost_per_unit` |
| `store_requisition_id` | `String @db.Uuid` | No | FK ไปยัง `tb_store_requisition.id` |
| `sequence_no` | `Int` | Yes | ลำดับบรรทัดภายใน SR; default `1` |
| `description` | `String @db.VarChar` | Yes | คำอธิบายบรรทัดแบบอิสระ |
| `comment` | `String @db.VarChar` | Yes | comment แบบอิสระบนบรรทัด (แยกจากตาราง `_detail_comment`) |
| `product_id` | `String @db.Uuid` | No | FK ไปยัง `tb_product.id` บังคับ |
| `product_code` | `String @db.VarChar` | Yes | Snapshot ของรหัสสินค้า |
| `product_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อสินค้า |
| `product_local_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อสินค้าแบบ localised |
| `product_sku` | `String @db.VarChar` | Yes | Snapshot ของ SKU |
| `requested_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณที่เอาท์เลตขอ; default `0` ตั้งบน `draft`; ล็อกตอน submit |
| `approved_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณที่ผู้อนุมัติอนุญาต; default `0` `approved_qty ≤ requested_qty` ตั้งระหว่างการอนุมัติ; ล็อกตอน issue |
| `issued_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณที่ store keeper ปล่อยจริงตอน fulfill; default `0` `issued_qty ≤ approved_qty` ตั้งตอน commit |
| `last_action` | `enum_last_action` | Yes | Action ล่าสุดบนบรรทัด; default `submitted` |
| `approved_message` | `String @db.VarChar` | Yes | โน้ตของผู้อนุมัติแบบอิสระ |
| `approved_by_id` | `String @db.Uuid` | Yes | user id ที่อนุมัติบรรทัด |
| `approved_by_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อผู้อนุมัติ |
| `approved_date_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp อนุมัติ |
| `review_message` | `String @db.VarChar` | Yes | โน้ตของผู้ review แบบอิสระ (สำหรับ send-back) |
| `review_by_id` | `String @db.Uuid` | Yes | user id ที่ review บรรทัด |
| `review_by_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อผู้ review |
| `review_date_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp review |
| `reject_message` | `String @db.VarChar` | Yes | ข้อความเหตุผลบังคับเมื่อ reject |
| `reject_by_id` | `String @db.Uuid` | Yes | user id ที่ reject บรรทัด |
| `reject_by_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อผู้ reject |
| `reject_date_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp reject |
| `history` | `Json @db.JsonB` | Yes | Log การกระทำต่อบรรทัดแบบ append-only ทีละขั้น; default `[]` แต่ละ entry: `{ seq, name, status, message, to_stage?, by_id, by_name, at_date }` |
| `stages_status` | `Json @db.JsonB` | Yes | Snapshot สถานะต่อขั้น; default `{}` แต่ละ entry: `{ seq, name, status }` |
| `current_stage_status` | `String @db.VarChar` | Yes | ฟิลด์ชั่วคราวเก็บสตริงสถานะขั้นปัจจุบัน Prisma schema ประกาศ `enum_stage_action { submit, approve, reject, review, pending }` (pass enum-cleanup พฤษภาคม 2026) ที่เจตนาใช้ type คอลัมน์นี้; ตัวคอลัมน์ยังเป็น `String?` จนกว่า migration ที่วางแผนไว้จะ validate ค่าประวัติและ retype ถือว่าค่านอก `enum_stage_action` เป็นข้อมูล legacy ที่ migration จะ normalise |
| `info` | `Json @db.JsonB` | Yes | Extension bag สำหรับ attribute บรรทัดเฉพาะ tenant; default `{}` |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array (project, cost-centre, job code); default `[]` ใช้ใน unique index |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency version counter; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp สร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp อัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FKs: `store_requisition_id → tb_store_requisition.id` (`NoAction`); `product_id → tb_product.id` (`NoAction`); `inventory_transaction_id → tb_inventory_transaction.id` (`NoAction`, nullable) Back-relations: many `tb_store_requisition_detail_comment`
**Indexes:** `@@unique([store_requisition_id, product_id, dimension, deleted_at])` ในชื่อ `SRT1_store_requisition_product_location_dimension_u` — product+cost-dimension เดียวสามารถปรากฏได้ครั้งเดียวบน SR ที่ยังไม่ถูก soft-delete; แถวที่ถูก soft-delete ปล่อย slot ออก `@@index([store_requisition_id, product_id])` ในชื่อ `SRT2_store_requisition_product_location_idx`

### 2.4 tb_store_requisition_detail_comment

ตาราง counterpart ระดับบรรทัดของ `tb_store_requisition_comment` เก็บ comment และ system events ที่ผูกกับบรรทัด SR เดียว — โดยทั่วไปใช้ระหว่างการอนุมัติเพื่อบันทึกการตัดสินใจต่อบรรทัด (โดย `approved_message` / `review_message` / `reject_message` บรรจุลายเซ็นเป็นทางการบนตัวบรรทัดเอง) และระหว่าง issue เพื่อ log การตัดสินใจ fulfillment

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `store_requisition_detail_id` | `String @db.Uuid` | No | FK ไปยัง `tb_store_requisition_detail.id` |
| `type` | `enum_comment_type` | No | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | Yes | user id ผู้เขียน (null สำหรับ entry แบบ `system`) |
| `message` | `String` | Yes | เนื้อหา comment แบบอิสระ |
| `attachments` | `Json @db.JsonB` | Yes | Array ของไฟล์แนบ; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp สร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp อัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `store_requisition_detail_id → tb_store_requisition_detail.id` (`NoAction` on delete/update)
**Indexes:** ไม่มีประกาศนอกเหนือจาก primary key

## 3. ความสัมพันธ์

```
tb_workflow
    │  (workflow_id เก็บพร้อม Prisma @relation ระบุชัดบน tb_store_requisition,
    │   ต่างจาก PR / PO / GRN ที่ลิงก์ workflow resolve ในชั้น application เท่านั้น)
    ▼
tb_store_requisition ──1──*──► tb_store_requisition_comment
    │  1
    │
    │ FK references (denormalised snapshots บนแถว)
    ├──► tb_location  (from_location_id, named relation store_requisition_from_location)
    └──► tb_location  (to_location_id,   named relation store_requisition_to_location)
    │
    │ * store_requisition_id
    ▼
tb_store_requisition_detail ──1──*──► tb_store_requisition_detail_comment
    │  1
    │
    │ FK references
    ├──► tb_product                   (required, product_id)
    └──► tb_inventory_transaction     (optional, inventory_transaction_id;
                                       บรรจุค่าตอน commit; children _detail ของแถวที่ลิงก์
                                       เก็บ lot, expiry, cost)

tb_store_requisition_detail ──1──*──► tb_inventory_transaction_detail
    ผ่าน tb_store_requisition_detail.inventory_transaction_id โดยทางอ้อม
    inventory transaction คือที่เก็บ canonical ของ lot_no, expiry_date
    และข้อมูล cost layer แบบ FIFO / average-cost — และในกรณี sr_type = transfer
    คือแถว stock-IN คู่กันที่สถานที่ปลายทาง
```

หมายเหตุ:

- **ส่วนหัว → รายการ** เป็น 1-to-many บน `store_requisition_id` (non-nullable บน detail)
- **ส่วนหัว → comment** และ **รายการ → comment** ทั้งคู่เป็น 1-to-many ตาราง comment คือบันทึกถาวรของกิจกรรม workflow; คอลัมน์ JSON บนส่วนหัว (`workflow_history`, `user_action`) คือ cursor in-place ลายเซ็น approval / review / rejection ต่อบรรทัดอยู่บน `tb_store_requisition_detail` โดยตรง (`approved_by_*`, `review_by_*`, `reject_by_*`) — ไม่ได้อยู่ในตาราง comment; ตาราง comment ใช้สำหรับ thread สนทนาแบบอิสระ
- **SR → inventory** เข้าถึงผ่าน `tb_store_requisition_detail.inventory_transaction_id` ซึ่งมี Prisma `@relation` ระบุชัด (ต่างจาก `detail_item.inventory_transaction_id` ของ GRN ซึ่งเป็น UUID เพียงอย่างเดียว) inventory transaction ที่ลิงก์คือ canonical store ของข้อมูล lot, expiry และ cost-layer; ในกรณี `sr_type = transfer` transaction เดียวกัน (หรือคู่กัน) บันทึก stock-IN ที่ปลายทาง
- **การ resolve location** ระบุชัดทั้งสองฝั่ง — `from_location_id` และ `to_location_id` ต่างประกาศ named Prisma `@relation` เข้า `tb_location` ค่า `tb_location.location_type` บนแต่ละฝั่งควบคุม `sr_type` ที่ถูกต้อง (`issue` ต้องการ `to_location.location_type = 'direct'`; `transfer` ต้องการ `to_location.location_type = 'inventory'`)
- **ไม่มียอดเงิน roll-up ที่ระดับส่วนหัว** ต่างจาก GRN ส่วนหัว SR **ไม่มี** คอลัมน์ `net_amount` / `total_amount` Cost roll-up คำนวณ on demand จาก inventory transactions ที่ลิงก์ (`tb_inventory_transaction.total_cost` × บรรทัด รวมต่อ SR) ไม่ได้ persist; SR เป็นเอกสารเชิงปริมาณ ไม่ใช่เชิงราคา
- การประกาศ FK แบบ `@relation` ทั้งหมดใช้ `onDelete: NoAction, onUpdate: NoAction` ดังนั้น referential integrity ถูกรักษาโดย soft-delete ระดับ application (`deleted_at`) แทนการ cascade

## 4. Enum

- **`enum_doc_status`** (ใช้ร่วมกับโมดูลอื่น — ไม่ใช่เฉพาะ SR): ห้าค่าที่ใช้โดย `tb_store_requisition.doc_status` default `draft`
  - `draft` — สถานะเริ่มต้นที่แก้ไขได้; ผู้ขอยังคงป้อนข้อมูลบรรทัด; ยังไม่กระทบสต๊อกหรือ GL
  - `in_progress` — submit เพื่อขออนุมัติและ/หรือ fulfillment; อยู่ภายใต้การควบคุมของ workflow SR ออกจากมือผู้ขอแล้วแต่ยังไม่ถูก issue ทั้ง action approve-line และ fulfil-line เกิดขึ้นในขณะที่เอกสารเป็น `in_progress`; ขั้น workflow (`workflow_current_stage`) คือสิ่งที่แยก "รออนุมัติ" กับ "รอ issue"
  - `completed` — fulfillment ถูก post: stock-OUT ที่ต้นทาง (และในกรณี `transfer` คือ stock-IN ที่ปลายทาง) ถูกเขียนผ่าน `tb_store_requisition_detail.inventory_transaction_id`; on-hand ที่ต้นทางถูกลด; cost-layer ถูกใช้; journal entries ถูกเขียน เอกสารถูกล็อก; การแก้ไขต้องทำผ่าน compensating adjustment ใน `[inventory-adjustment](/th/inventory/inventory-adjustment)`
  - `cancelled` — คำขอถูกถอนก่อน commit (เช่น ผู้ขอถอน, ผู้อนุมัติ reject ทั้ง SR, สต๊อกขาดที่ต้นทางตอน fulfillment ทำให้ fill ไม่ได้) ไม่กระทบสต๊อกหรือ GL
  - `voided` — ถูก void เชิงบริหาร (เส้นทางสำหรับ audit / data-hygiene) ไม่กระทบสต๊อกหรือ GL จุดสิ้นสุด
- **`enum_sr_type`**: ประเภทการเคลื่อนย้าย SR สำหรับ `tb_store_requisition.sr_type` default `transfer` สองค่า:
  - `issue` — สต๊อกออกจาก inventory และถูกบริโภคทันทีที่ cost-centre ของปลายทาง (เบิกครัว เบิกบาร์) ต้องการ `to_location.location_type = 'direct'` stock-OUT ครั้งเดียวที่ต้นทาง; มูลค่าส่งไปยังบัญชีค่าใช้จ่ายการบริโภคของปลายทางบน cost-centre
  - `transfer` — สต๊อกเคลื่อนย้ายระหว่างสองสถานที่ที่ถือ inventory โดยยังไม่ถูกบริโภค ต้องการ `to_location.location_type = 'inventory'` stock-OUT ที่ต้นทางและ stock-IN ที่ปลายทางคู่กัน; มูลค่าย้ายจากบัญชี inventory หนึ่งไปอีกบัญชี ยังไม่รับรู้ค่าใช้จ่าย
- **`enum_inventory_doc_type`** (ใช้ร่วม ไม่ได้อยู่บน `tb_store_requisition` โดยตรง แต่อยู่บน `tb_inventory_transaction.inventory_doc_type` ที่ลิงก์): ระบุ `store_requisition` เป็นหนึ่งในเจ็ดค่า (`good_received_note`, `credit_note`, `store_requisition`, `stock_in`, `stock_out`, `close`, `open`) inventory transaction ที่สร้างตอน commit จะ stamp `store_requisition` ที่นี่ ดังนั้น query ปลายน้ำสามารถ filter inventory movement ตามประเภทเอกสารต้นกำเนิด
- **`enum_comment_type`** (ใช้ร่วมกับ PR / PO / GRN): `user` (comment ที่มนุษย์เขียน), `system` (รายการ activity-log ที่ workflow engine สร้างอัตโนมัติ) ใช้โดยทั้ง `tb_store_requisition_comment.type` และ `tb_store_requisition_detail_comment.type`
- **`enum_last_action`** (ใช้ร่วมกับ PR / PO / GRN): `submitted`, `approved`, `reviewed`, `rejected` — ใช้โดย `tb_store_requisition.last_action` และ `tb_store_requisition_detail.last_action` เพื่อจับ action workflow ล่าสุด

## 5. จุดที่ต่างจาก carmen/docs

ไฟล์ `SR-Overview.md`, `SR-Technical-Specification.md`, `SR-User-Experience.md` และ `Store Requisitions.md` อธิบายโมเดล interface แบบ TypeScript (พร้อม `Requisition`, `RequisitionItem`, `StockMovement`, `StockMovementItem`, `LotInfo`, `JournalEntry`) และ enum สถานะหลายตัวที่ไม่ตรงกับ Prisma schema canonical ความแตกต่างต่อไปนี้ถูกรวบรวมจากแหล่งเหล่านั้น

| # | ประเด็น | carmen/docs บอกว่า | Prisma มีว่า | สิ่งที่ต้องทำ |
|---|--------|-------------------|--------------|--------------|
| 1 | ค่าสถานะส่วนหัว SR | Tech Spec: `status: 'In Process' | 'Complete' | 'Reject' | 'Void' | 'Draft'` User-Experience.md state diagram: หกสถานะ `Draft → Submitted → UnderReview → Approved → InProcess → Fulfilled → Completed` บวก `PartiallyApproved`, `Rejected`, `Voided` | `tb_store_requisition.doc_status` ใช้ `enum_doc_status { draft, in_progress, completed, cancelled, voided }` ร่วม `In Process`, `Submitted`, `UnderReview`, `Approved`, `PartiallyApproved`, `InProcess`, `Fulfilled` ของ carmen/docs ยุบรวมเป็น `in_progress` ของ Prisma; `Complete` / `Fulfilled` / `Completed` ยุบเป็น `completed`; `Reject` / `Rejected` ยุบเป็น `cancelled`; `Void` / `Voided` เป็น `voided` | ให้ถือว่า Prisma เป็น canonical "ขั้น" ที่เอกสารอยู่ระหว่าง `in_progress` (รออนุมัติ vs รอ issue vs issue บางส่วน) คือสิ่งที่ `workflow_current_stage` และ `current_stage_status` ต่อบรรทัดจับ ไม่ใช่ค่า enum ส่วนหัวแยก |
| 2 | สถานะอนุมัติต่อบรรทัด | Tech Spec `RequisitionItem.approvalStatus: 'Accept' | 'Reject' | 'Review'` ระบุบน detail-view UI เป็น badge ต่อแถว | `tb_store_requisition_detail` **ไม่มี** คอลัมน์ enum `approval_status` การตัดสินใจต่อบรรทัดอนุมานจากคอลัมน์ลายเซ็น (`approved_by_id IS NOT NULL` → accepted; `reject_by_id IS NOT NULL` → rejected; `review_by_id IS NOT NULL` → ส่งกลับ review) และ JSON `history` / `stages_status` ต่อบรรทัด | ลบ enum `approvalStatus` จาก carmen/docs หรือระบุว่าเป็น field ที่ derive ในชั้น application จากคอลัมน์ลายเซ็น |
| 3 | ฟิลด์เงินบนบรรทัด | Tech Spec `RequisitionItem.costPerUnit`, `total` UI detail-view แสดงคอลัมน์ "Unit Cost" และ "Total" | `tb_store_requisition_detail` **ไม่มี** `cost_per_unit`, `total`, `unit_cost`, `total_cost` หรือคอลัมน์เงินใด ๆ unit cost ดึงตอน commit จาก `tb_inventory_transaction_cost_layer.cost_per_unit` ที่ลิงก์ (ค่าจากวิธี costing ของสถานที่ต้นทาง); total คำนวณเพื่อแสดงผลจาก `issued_qty × cost_per_unit` แต่ไม่ persist | อัปเดต carmen/docs ให้ระบุว่า SR เป็นเอกสารเชิงปริมาณ; ข้อมูล cost อยู่บน inventory transaction ที่ลิงก์และคำนวณเพื่อแสดง ไม่เก็บบนบรรทัด SR |
| 4 | ฟิลด์เงินบนส่วนหัว | Tech Spec `Requisition.totalAmount` footer ของ UI detail-view แสดง "Total: $100.00" | `tb_store_requisition` **ไม่มี** `total_amount`, `net_amount`, `subtotal` หรือคอลัมน์เงินใด ๆ บนส่วนหัว | ลบ `totalAmount` จาก interface ส่วนหัว; ระบุว่ายอดรวมส่วนหัวเป็นการ sum เพื่อแสดงเท่านั้นจาก inventory transactions ที่ลิงก์ |
| 5 | Snapshot สต๊อกบนบรรทัด | Tech Spec `RequisitionItem.inventory: { onHand, onOrder, lastPrice, lastVendor }` และ `itemInfo` (location / category / barcode / `locationType`) | `tb_store_requisition_detail` ไม่มีคอลัมน์เหล่านี้ `onHand` / `onOrder` / `lastPrice` ถูกอ่านตอนป้อนบรรทัดจาก `tb_inventory_status` / `tb_product_info` และแสดงใน UI สำหรับสนับสนุนการตัดสินใจของผู้ขอ; ไม่ persist บนบรรทัด SR | อัปเดต carmen/docs ให้ระบุว่า `inventory` และ `itemInfo` เป็น enrichment เฉพาะ UI จากโมดูล inventory ตอนแก้บรรทัด ไม่ใช่คอลัมน์ SR |
| 6 | `StockMovement` ในฐานะตารางที่ SR เป็นเจ้าของ | Tech Spec นิยาม interface `StockMovement` / `StockMovementItem` และตาราง `StockMovement` พร้อม `commitDate`, `postingDate`, `status`, `inQty`, `outQty`, `unitCost`, ข้อมูล lot | ไม่มีตาราง `tb_stock_movement` หรือ `tb_store_requisition_stock_movement` ใน Prisma stock movements อยู่บนตระกูล `tb_inventory_transaction` / `tb_inventory_transaction_detail` ที่ใช้ร่วม; บรรทัด SR เข้าถึงผ่าน `inventory_transaction_id` ในกรณี `sr_type = transfer` OUT ที่ต้นทางและ IN ที่ปลายทางเป็น inventory transactions และเข้าถึงในวิธีเดียวกัน | ปรับ carmen/docs ให้ระบุว่า stock movements เป็นบันทึกของโมดูล inventory ที่ SR ชี้ไป ไม่ใช่ children ที่ SR เป็นเจ้าของ |
| 7 | `JournalEntry` ในฐานะตารางที่ SR เป็นเจ้าของ | Tech Spec นิยาม interface `JournalEntry` พร้อมฟิลด์บัญชีระดับส่วนหัว/บรรทัด | ไม่มีตาราง journal-entry ที่ SR เป็นเจ้าของ Journal entries ถูกสร้างปลายน้ำในโมดูล finance จาก inventory transactions ที่ลิงก์; โมดูล SR มีหน้าที่ trigger แต่ไม่ได้เก็บ | อัปเดต carmen/docs ให้ระบุว่า journal entries เป็นเรื่องของโมดูล finance เข้าถึงจาก SR ผ่านการ post ปลายน้ำของ inventory transaction ที่ลิงก์ |
| 8 | รูปแบบและ nullability ของเลขที่อ้างอิง | Tech Spec validation rule: "Must be unique and follow the format 'SR-YYYY-NNN'" | `tb_store_requisition.sr_no` เป็น `NOT NULL` `VarChar` ไม่มี cap ของ length; uniqueness บังคับร่วมกับ `deleted_at` (`@@unique([sr_no, deleted_at])`) รูปแบบควบคุมในชั้น application ไม่ใช่ schema | ระบุว่ารูปแบบเป็น convention ของชั้น application; คอลัมน์เป็น `NOT NULL` (draft ไม่สามารถ save ได้ถ้าไม่มีเลขอ้างอิง — ต่างจาก `grn_no` ของ GRN ที่ยอม null บน draft) |
| 9 | Cardinality ของประเภทการเคลื่อนย้าย | User-Experience.md state diagram และ Tech Spec บรรยาย `movement.type` เป็นสตริงอิสระบนส่วนหัว | `tb_store_requisition.sr_type` เป็น enum ปิด `enum_sr_type { issue, transfer }` มีสองค่าเท่านั้น และ `transfer` เป็น default | อัปเดต carmen/docs ให้สะท้อน enum ปิดสองค่า; ลบการอ้างอิงถึงประเภท `Direct` / `Inventory` — ค่าเหล่านั้นเป็น `tb_location.location_type` ที่ควบคุมประเภท SR ไม่ใช่ประเภท SR เอง |
| 10 | Uniqueness ต่อบรรทัดที่อิง dimension | Tech Spec และ Component-Specifications บรรยายว่าบรรทัด key ด้วย `product_id` เพียงอย่างเดียว | unique index `SRT1_store_requisition_product_location_dimension_u` คือ `(store_requisition_id, product_id, dimension, deleted_at)` — สินค้าเดียวสามารถปรากฏหลายครั้งบน SR เดียวได้ตราบเท่าที่แต่ละครั้งมี `dimension` JSON ต่างกัน (การจัดสรร cost-centre แยกกัน) | ระบุ uniqueness ที่ตระหนัก dimension: การจัดสรร cost-centre แบบ split บนสินค้าเดียวกันถูก model เป็นบรรทัดแยก ไม่ใช่ aggregate |

## 6. แหล่งอ้างอิง

- **Primary (source of truth):** Prisma schemas ที่ระบุใน header callout — โดยเฉพาะ `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (โมเดล SR ทั้งสี่, `enum_sr_type` เฉพาะ SR, `enum_doc_status` / `enum_inventory_doc_type` / `enum_comment_type` / `enum_last_action` ที่ใช้ร่วม และตระกูล `tb_inventory_transaction*` ที่เกี่ยวข้อง) และ `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (ตรวจสอบแล้วว่าไม่มีโมเดล SR)
- **Secondary (cross-check แนวคิด):**
  - `../carmen/docs/store-requisitions/SR-Overview.md` — วัตถุประสงค์โมดูล บริบทธุรกิจ ฟีเจอร์สำคัญ user roles; จุดที่ต่างในส่วนที่ 5 (ข้อ 2, 3, 4)
  - `../carmen/docs/store-requisitions/SR-Technical-Specification.md` — โมเดล interface TypeScript, enum `RequisitionItem.approvalStatus`, interface `StockMovement` / `JournalEntry`, validation rules; จุดที่ต่างในส่วนที่ 5 (ข้อ 1, 2, 3, 4, 5, 6, 7, 8)
  - `../carmen/docs/store-requisitions/SR-User-Experience.md` — คำอธิบาย persona (Store Manager, Warehouse Supervisor, Department Head, Finance Manager), user journeys, แผนวงจรชีวิตหกสถานะ; จุดที่ต่างในส่วนที่ 5 (ข้อ 1, 9)
  - `../carmen/docs/store-requisitions/SR-Component-Specifications.md` — สัญญาของ UI component; บรรทัด key ด้วย `product_id` (จุดที่ต่างข้อ 10)
  - `../carmen/docs/store-requisitions/Store Requisitions.md` — layout listing / detail-view และ use cases UC-64..UC-69 (`Approve`, `Deny`, `Modify`, `Monitor`, `Create and Manage`, `Approve and Record Stock as Issued`); map ไปยังวงจรชีวิตในส่วนที่ 2 ของหน้า user-flow
- **เอกสารพี่น้อง:** [01-data-model.md](../good-receive-note/01-data-model.md) (good-receive-note) — บรรยายฝั่งกลับกันของรูปแบบ inventory-write; ไม่ควรซ้ำเนื้อหานั้นที่นี่
- โมดูลที่เกี่ยวข้อง: [inventory](/th/inventory/inventory) (ปลายน้ำ — inventory transaction คือที่อยู่ของข้อมูล lot, expiry และ cost-layer), [costing](/th/inventory/costing) (การประเมินค่า weighted-average หรือ FIFO ของสถานที่ต้นทาง feed unit cost ที่ issue), [recipe](/th/inventory/recipe) (ความต้องการของ recipe อาจสร้าง SR อัตโนมัติสำหรับการเบิกวัตถุดิบ), [good-receive-note](/th/inventory/good-receive-note) (การโอนระหว่างสถานที่สามารถจับคู่ SR-OUT ที่คลังต้นทางกับ GRN-IN ที่คลังปลายทาง), [inventory-adjustment](/th/inventory/inventory-adjustment) (การแก้ไขหลัง commit), [product](/th/inventory/product) (การอ้างอิงสินค้าต่อบรรทัด)
