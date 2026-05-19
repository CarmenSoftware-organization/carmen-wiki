---
title: ใบขอซื้อ (Purchase Request) — Data Model
description: เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum ของโมดูล purchase-request
published: true
date: 2026-05-20T00:00:00.000Z
tags: purchase-request, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# ใบขอซื้อ (Purchase Request) — Data Model

> **At a Glance**
> **ตาราง:** `tb_purchase_request` &nbsp;·&nbsp; `tb_purchase_request_detail` &nbsp;·&nbsp; `tb_purchase_request_comment` &nbsp;·&nbsp; `tb_purchase_request_detail_comment` &nbsp;·&nbsp; `tb_purchase_request_template` / `_detail` (สำหรับ recurring order)
> **กลุ่มผู้ใช้:** Developer / Auditor (เอกสารอ้างอิงสำหรับนักพัฒนา)
> **FK สำคัญ:** header `→ tb_workflow`; detail `→ tb_product` / `tb_vendor` / `tb_pricelist_detail` / `tb_location` / `tb_delivery_point` / `tb_unit` ×3 (requested + approved + FOC); bridge แบบ many-to-many ไปยัง PO ผ่าน `tb_purchase_order_detail_tb_purchase_request_detail`
> **Audit pattern:** มาตรฐาน `created_*` / `updated_*` / `deleted_*`; สามจำนวนต่อบรรทัด (`requested` / `approved` / FOC); JSON `history` / `stages_status` ต่อบรรทัดสำหรับ workflow

> **Source of truth:** Prisma schema ฝั่ง backend อ่านไฟล์เหล่านี้ก่อนเขียนหรือแก้ไขหน้านี้ทุกครั้ง:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` ใต้ package แต่ละตัวเป็น copy ที่ generate อัตโนมัติและไม่ถือว่าเป็นต้นฉบับ

## 1. ภาพรวม

โมดูล purchase-request เป็นเจ้าของหก entity ใน tenant schema ได้แก่ ส่วนหัวของเอกสาร (`tb_purchase_request`), รายการสินค้า (`tb_purchase_request_detail`), comment ของ workflow / activity-log ทั้งระดับ header และระดับบรรทัด (`tb_purchase_request_comment`, `tb_purchase_request_detail_comment`), และคู่ template ที่นำกลับมาใช้ใหม่ได้ (`tb_purchase_request_template`, `tb_purchase_request_template_detail`) สำหรับคำขอที่ทำซ้ำเป็นประจำ เช่น order market-list รายเดือน การติดตาม stage ของ workflow ไม่ได้แยกเป็นตารางต่างหาก — มันอยู่ inline บน header เป็นคอลัมน์ JSON (`workflow_history`, `workflow_current_stage`, `stages_status`) บวกกับ FK ไปยังตารางตั้งค่า `tb_workflow` ที่ใช้ร่วมกัน ส่วน timeline ของ event submit/approve/reject/send-back ที่ persist ไว้จะถูกบันทึกผ่านตาราง comment

PR อยู่ต้นน้ำของ [purchase-order](/th/inventory/purchase-order) ในห่วงโซ่ procure-to-pay บรรทัดของ PR ที่อนุมัติแล้วจะถูก link ไปยังบรรทัด PO ที่เกิดขึ้นผ่านตาราง bridge `tb_purchase_order_detail_tb_purchase_request_detail` (PO line หนึ่งสามารถรวมจาก PR line หลายบรรทัดเพื่อ consolidate, PR line หนึ่งสามารถกระจายไปหลาย PO สำหรับการแปลงบางส่วน) แถวรายละเอียดของ PR ยังอ้างอิงถึง [product](/th/inventory/product), [vendor-pricelist](/th/inventory/vendor-pricelist), `tb_tax_profile`, `tb_currency`, `tb_unit`, `tb_location`, `tb_delivery_point`, และ `tb_vendor` โดย denormalize ฟิลด์ lookup (รหัส, ชื่อ, snapshot ของราคา) ลงบนบรรทัดตอน submit เพื่อให้ข้อมูล PR ในอดีตคงที่แม้ master record จะเปลี่ยน entity ของ PR ทั้งหมดอยู่ใน tenant Prisma schema ส่วน platform schema ไม่มี model ของ purchase-request

## 2. เอนทิตี

### 2.1 tb_purchase_request

ส่วนหัวของเอกสาร PR เก็บหมายเลขอ้างอิง, บริบทของ requestor และแผนก, snapshot ของ workflow, ยอดรวมในสกุลเงินฐาน และคอลัมน์ audit ส่วนหัวหนึ่งมีหลายแถว detail และหลาย comment

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key สร้างผ่าน `gen_random_uuid()` |
| `pr_no` | `String @db.VarChar` | No | หมายเลขอ้างอิง PR ที่อ่านง่าย (เช่น `PR-2301-0001`) |
| `pr_date` | `DateTime @db.Timestamptz(6)` | Yes | วันที่เอกสารที่ requestor เลือกตอน submit |
| `description` | `String @db.VarChar` | Yes | คำอธิบาย / เหตุผลประกอบแบบ free-text ที่ใส่บน header |
| `workflow_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_workflow` — เลือกนิยามสายอนุมัติที่ PR ใบนี้ใช้ |
| `workflow_name` | `String @db.VarChar` | Yes | snapshot ของชื่อ workflow ตอน submit |
| `workflow_history` | `Json @db.JsonB` | Yes | timeline แบบ append-only ของการ transition stage; default `[]` แต่ละ entry มี `stage`, `action`, `message`, `by`, `at` |
| `workflow_current_stage` | `String @db.VarChar` | Yes | slug ของ stage ที่ PR อยู่ปัจจุบัน |
| `workflow_previous_stage` | `String @db.VarChar` | Yes | slug ของ stage ที่เพิ่งปล่อย PR ออกมา |
| `workflow_next_stage` | `String @db.VarChar` | Yes | slug ของ stage ถัดไปบน chain |
| `user_action` | `Json @db.JsonB` | Yes | metadata ของ action ที่ค้างอยู่; default `{}` โดยทั่วไปเป็น `{ "execute": [{ "id": "<user-id>" }, ...] }` บอกว่าใครลงมือถัดไปได้ |
| `last_action` | `enum_last_action` | Yes | action ล่าสุดที่ทำกับเอกสาร; default `submitted` |
| `last_action_at_date` | `DateTime @db.Timestamptz(6)` | Yes | timestamp ของ `last_action` |
| `last_action_by_id` | `String @db.Uuid` | Yes | user id ที่ทำ `last_action` |
| `last_action_by_name` | `String @db.VarChar` | Yes | snapshot ของชื่อผู้ทำ |
| `pr_status` | `enum_purchase_request_doc_status` | Yes | สถานะเอกสาร; default `draft` |
| `requestor_id` | `String @db.Uuid` | Yes | user id ที่ตั้ง PR |
| `requestor_name` | `String @db.VarChar` | Yes | snapshot ของชื่อ requestor ที่แสดง |
| `department_id` | `String @db.Uuid` | Yes | แผนกที่ PR สังกัด |
| `department_name` | `String @db.VarChar` | Yes | snapshot ของชื่อแผนก |
| `base_net_amount` | `Decimal @db.Decimal(15, 5)` | No | roll-up ของ `base_net_amount` ของแต่ละ line; default `0` |
| `base_total_amount` | `Decimal @db.Decimal(15, 5)` | No | roll-up ของ `base_total_price` ของ line (net + tax); default `0` |
| `note` | `String @db.VarChar` | Yes | note แบบ free-text แนบกับ header |
| `info` | `Json @db.JsonB` | Yes | extension bag สำหรับ attribute เฉพาะ tenant ที่ header; default `{}` |
| `dimension` | `Json @db.JsonB` | Yes | array ของ cost-dimension (project, cost-centre, job code ฯลฯ); default `[]` |
| `doc_version` | `Int @db.Integer` | No | ตัวนับ version สำหรับ optimistic-concurrency; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง default เป็น `now()` |
| `created_by_id` | `String @db.Uuid` | Yes | user id ที่สร้างแถว |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดตล่าสุด default เป็น `now()` |
| `updated_by_id` | `String @db.Uuid` | Yes | user id ที่อัปเดตล่าสุด |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การ soft-delete; non-null = ถูกลบเชิง logic |
| `deleted_by_id` | `String @db.Uuid` | Yes | user id ที่ soft-delete |

**Constraints:** `@id` บน `id` FK `workflow_id → tb_workflow.id` (`NoAction` ตอน delete/update)
**Indexes:** `@@unique([pr_no, deleted_at])` ชื่อ `PR0_pr_no_u`; `@@index([pr_no])` ชื่อ `PR0_pr_no_idx`; `@@index([requestor_id])` ชื่อ `PR0_requestor_id_idx`

### 2.2 tb_purchase_request_detail

รายการสินค้าของ PR เก็บ reference สินค้า, จำนวน / หน่วยสามชุด (requested, approved, FOC), snapshot ของ vendor และ pricelist, ภาษีและส่วนลด, ยอดรวมต่อบรรทัดทั้งในสกุลเงินธุรกรรมและสกุลเงินฐาน และประวัติ stage ของ workflow ต่อบรรทัด

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `purchase_request_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_purchase_request.id` Nullable เพื่อรองรับ draft line ที่ยังไม่ผูกกับ header |
| `sequence_no` | `Int` | Yes | ลำดับของบรรทัดภายใน PR; default `1` |
| `location_id` | `String @db.Uuid` | Yes | คลัง / สถานที่ที่ต้องการของ |
| `location_code` | `String @db.VarChar` | Yes | snapshot ของรหัส location |
| `location_name` | `String @db.VarChar` | Yes | snapshot ของชื่อ location |
| `delivery_point_id` | `String @db.Uuid` | Yes | จุดส่งของเฉพาะ |
| `delivery_point_name` | `String @db.VarChar` | Yes | snapshot |
| `delivery_date` | `DateTime @db.Timestamptz(6)` | Yes | วันที่ต้องการส่งของของบรรทัดนี้ |
| `product_id` | `String @db.Uuid` | No | FK ไปยัง `tb_product.id` Required |
| `product_code` | `String @db.VarChar` | Yes | snapshot ของรหัสสินค้า |
| `product_name` | `String @db.VarChar` | Yes | snapshot |
| `product_local_name` | `String @db.VarChar` | Yes | snapshot ของชื่อสินค้าภาษาท้องถิ่น |
| `product_sku` | `String @db.VarChar` | Yes | snapshot ของ SKU |
| `inventory_unit_id` | `String @db.Uuid` | Yes | หน่วยฐานของ inventory ตอน submit |
| `inventory_unit_name` | `String @db.VarChar` | Yes | snapshot |
| `description` | `String @db.VarChar` | Yes | คำอธิบายบรรทัด (มัก override product_name สำหรับ free-text line) |
| `comment` | `String @db.VarChar` | Yes | comment ระดับบรรทัด |
| `vendor_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_vendor.id` — vendor ที่ถูกจัดสรรให้บรรทัดนี้ |
| `vendor_name` | `String @db.VarChar` | Yes | snapshot |
| `pricelist_detail_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_pricelist_detail.id` — แถว pricelist ที่ราคามาจาก |
| `pricelist_no` | `String @db.VarChar` | Yes | snapshot ของหมายเลขอ้างอิง pricelist |
| `pricelist_unit` | `String @db.VarChar` | Yes | snapshot ของ UoM บน pricelist |
| `pricelist_price` | `Decimal @db.Decimal(20, 5)` | Yes | snapshot ของราคาต่อหน่วยจาก pricelist; default `0` |
| `pricelist_type` | `enum_pricelist_compare_type` | Yes | วิธีที่ราคานี้ถูกเลือก (default `automatic`) |
| `currency_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_currency.id` — สกุลเงินธุรกรรม |
| `currency_code` | `String @db.VarChar` | Yes | snapshot |
| `exchange_rate` | `Decimal @db.Decimal(15, 5)` | Yes | อัตราแลกเปลี่ยนจากสกุลธุรกรรมเป็นสกุลฐาน; default `1` |
| `exchange_rate_date` | `DateTime @db.Timestamptz(6)` | Yes | วันที่มีผลของ snapshot อัตราแลกเปลี่ยน |
| `requested_qty` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนในหน่วยที่ขอ; default `0` |
| `requested_unit_id` | `String @db.Uuid` | Yes | UoM ที่ requestor ใส่ |
| `requested_unit_name` | `String @db.VarChar` | Yes | snapshot |
| `requested_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | Yes | factor การแปลงไปยังหน่วยฐาน inventory |
| `requested_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | `requested_qty × requested_unit_conversion_factor` |
| `approved_qty` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนในหน่วยที่อนุมัติ อาจต่างจาก `requested_qty` |
| `approved_unit_id` | `String @db.Uuid` | Yes | UoM ที่ใช้สำหรับจำนวนที่อนุมัติ |
| `approved_unit_name` | `String @db.VarChar` | Yes | snapshot |
| `approved_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | Yes | factor การแปลงไปยังหน่วยฐาน |
| `approved_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | `approved_qty × approved_unit_conversion_factor` |
| `foc_qty` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวน FOC ในหน่วย FOC; default `0` |
| `foc_unit_id` | `String @db.Uuid` | Yes | UoM ของจำนวน FOC |
| `foc_unit_name` | `String @db.VarChar` | Yes | snapshot |
| `foc_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | Yes | factor การแปลงไปยังหน่วยฐาน |
| `foc_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | `foc_qty × foc_unit_conversion_factor` |
| `tax_profile_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_tax_profile.id` |
| `tax_profile_name` | `String @db.VarChar` | Yes | snapshot |
| `tax_rate` | `Decimal @db.Decimal(15, 5)` | Yes | อัตราภาษีที่มีผล; default `0` |
| `tax_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนภาษีในสกุลเงินธุรกรรม |
| `base_tax_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนภาษีในสกุลเงินฐาน |
| `is_tax_adjustment` | `Boolean` | Yes | `true` เมื่อผู้ใช้ override จำนวนภาษีด้วยมือ; default `false` |
| `discount_rate` | `Decimal @db.Decimal(15, 5)` | Yes | อัตราส่วนลด %; default `0` |
| `discount_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนส่วนลดในสกุลเงินธุรกรรม |
| `base_discount_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนส่วนลดในสกุลเงินฐาน |
| `is_discount_adjustment` | `Boolean` | Yes | `true` เมื่อผู้ใช้ override ส่วนลดด้วยมือ; default `false` |
| `sub_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `pricelist_price × approved_qty` (สกุลเงินธุรกรรม) |
| `net_amount` | `Decimal @db.Decimal(20, 5)` | Yes | `sub_total_price − discount_amount` |
| `total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `net_amount + tax_amount` |
| `base_price` | `Decimal @db.Decimal(20, 5)` | Yes | `pricelist_price × exchange_rate` |
| `base_sub_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `base_price × approved_qty` |
| `base_net_amount` | `Decimal @db.Decimal(20, 5)` | Yes | `base_sub_total_price − base_discount_amount` |
| `base_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `base_net_amount + base_tax_amount` |
| `history` | `Json @db.JsonB` | Yes | timeline stage ต่อบรรทัด (`seq`, `name`, `status`, `to_stage`, `message`, `by_id`, `by_name`, `at_date`); default `[]` |
| `stages_status` | `Json @db.JsonB` | Yes | cursor stage ต่อบรรทัด — array ของ `{ seq, name, status }`; default `{}` |
| `current_stage_status` | `String @db.VarChar` | Yes | สำเนาที่ใช้งานของ stage status ปัจจุบัน Prisma schema ประกาศ `enum_stage_action { submit, approve, reject, review, pending }` (pass enum-cleanup พฤษภาคม 2026) ที่เจตนาใช้ type คอลัมน์นี้; ตัวคอลัมน์ยังเป็น `String?` จนกว่า migration ที่วางแผนไว้จะ validate ค่าประวัติและ retype ถือว่าค่านอก `enum_stage_action` เป็นข้อมูล legacy ที่ migration จะ normalise |
| `info` | `Json @db.JsonB` | Yes | extension bag; default `{}` |
| `dimension` | `Json @db.JsonB` | Yes | cost dimension ต่อบรรทัด; default `[]` |
| `doc_version` | `Int @db.Integer` | No | version สำหรับ optimistic-concurrency; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การ soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK: `purchase_request_id → tb_purchase_request.id`; `product_id → tb_product.id` (required); `vendor_id → tb_vendor.id`; `pricelist_detail_id → tb_pricelist_detail.id`; `tax_profile_id → tb_tax_profile.id`; `currency_id → tb_currency.id`; `location_id → tb_location.id`; `delivery_point_id → tb_delivery_point.id`; FK ที่ตั้งชื่อด้วย `@relation` สาม FK ไปยัง `tb_unit` สำหรับหน่วย requested / approved / FOC
**Indexes:** `@@unique([purchase_request_id, product_id, location_id, dimension, deleted_at])` ชื่อ `PR1_purchase_request_product_location_dimension_u`; `@@index([product_id])` ชื่อ `PRD1_product_id_idx`; `@@index([location_id])` ชื่อ `PRD1_location_id_idx`; `@@index([location_id, product_id])` ชื่อ `PRD1_location_product_idx`; `@@index([purchase_request_id])` ชื่อ `PRD1_purchase_request_id_idx`

### 2.3 tb_purchase_request_comment

รายการของ workflow / activity-log ที่ผูกกับ header ของ PR Prisma schema ไม่มีตาราง `tb_purchase_request_workflow` โดยเฉพาะ — ตาราง comment นี้ผสมกับคอลัมน์ JSON ของ workflow บน header คือ record persist ของ timeline ของ workflow แต่ละแถวเป็น user comment (`type = user`) หรือ system event (`type = system`) เช่นการ transition stage

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `purchase_request_id` | `String @db.Uuid` | No | FK ไปยัง `tb_purchase_request.id` |
| `type` | `enum_comment_type` | No | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | Yes | user id ผู้เขียน (null สำหรับ entry แบบ `system`) |
| `message` | `String` | Yes | เนื้อ comment แบบ free-text |
| `attachments` | `Json @db.JsonB` | Yes | array ของ `{ originalName, fileToken, contentType }`; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การ soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `purchase_request_id → tb_purchase_request.id` (`NoAction` ตอน delete/update)
**Indexes:** ไม่มีประกาศนอกเหนือจาก primary key

### 2.4 tb_purchase_request_detail_comment

ตารางคู่ขนานระดับบรรทัดของ `tb_purchase_request_comment` จับ comment และ system event ที่ผูกกับบรรทัด PR เพียงบรรทัดเดียว — โดยทั่วไปใช้ระหว่างการอนุมัติเพื่อบันทึกการตัดสินใจระดับ stage และเหตุผลการ reject ต่อบรรทัด

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `purchase_request_detail_id` | `String @db.Uuid` | No | FK ไปยัง `tb_purchase_request_detail.id` |
| `type` | `enum_comment_type` | No | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | Yes | user id ผู้เขียน |
| `message` | `String` | Yes | เนื้อ comment แบบ free-text |
| `attachments` | `Json @db.JsonB` | Yes | array ของ attachment; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การ soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `purchase_request_detail_id → tb_purchase_request_detail.id`
**Indexes:** ไม่มีประกาศนอกเหนือจาก primary key

### 2.5 tb_purchase_request_template

ส่วนหัวของ PR template ที่นำกลับมาใช้ใหม่ได้ (เช่นชุด market-list รายสัปดาห์) Template เองไม่เข้าสู่ workflow — มัน seed PR ใบใหม่

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อ template |
| `description` | `String @db.VarChar` | Yes | คำอธิบายแบบ free-text |
| `workflow_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_workflow` — workflow default สำหรับ PR ที่เกิดจาก template นี้ |
| `workflow_name` | `String @db.VarChar` | Yes | snapshot ของชื่อ workflow |
| `is_active` | `Boolean` | Yes | template ถูกเลือกได้หรือไม่; default `true` |
| `note` | `String @db.VarChar` | Yes | note แบบ free-text |
| `info` | `Json @db.JsonB` | Yes | extension bag; default `{}` |
| `dimension` | `Json @db.JsonB` | Yes | cost dimension default; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การ soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `workflow_id → tb_workflow.id`
**Indexes:** `@@unique([name, workflow_id, deleted_at])` ชื่อ `PRT1_name_workflow_id_u`; `@@index([workflow_id])` ชื่อ `PRT1_workflow_id_idx`; `@@index([name])` ชื่อ `PRT1_name_idx`

### 2.6 tb_purchase_request_template_detail

รายการสินค้าที่เป็นของ PR template Schema เลียนแบบ `tb_purchase_request_detail` ในส่วนของฟิลด์ที่ template ต้องใช้ในการ seed — product, location, requested qty / unit, FOC, tax, discount, currency — แต่ตั้งใจตัดฟิลด์ฝั่งอนุมัติออก (`approved_qty`, `approved_unit_*`, workflow `history`, `stages_status`) และตัดคอลัมน์ `vendor_id` / `pricelist_detail_id` ออก ฟิลด์เหล่านั้นถูก set ตอนสร้าง PR ไม่ใช่เก็บไว้ใน template

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `purchase_request_template_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_purchase_request_template.id` |
| `location_id` | `String @db.Uuid` | Yes | คลัง / สถานที่ |
| `location_code` | `String @db.VarChar` | Yes | snapshot |
| `location_name` | `String @db.VarChar` | Yes | snapshot |
| `delivery_point_id` | `String @db.Uuid` | Yes | จุดส่งของ |
| `delivery_point_name` | `String @db.VarChar` | Yes | snapshot |
| `product_id` | `String @db.Uuid` | No | FK ไปยัง `tb_product.id` Required |
| `product_code` | `String @db.VarChar` | Yes | snapshot |
| `product_name` | `String @db.VarChar` | Yes | snapshot |
| `product_local_name` | `String @db.VarChar` | Yes | snapshot |
| `product_sku` | `String @db.VarChar` | Yes | snapshot |
| `inventory_unit_id` | `String @db.Uuid` | Yes | หน่วยฐานของ inventory |
| `inventory_unit_name` | `String @db.VarChar` | Yes | snapshot |
| `description` | `String @db.VarChar` | Yes | คำอธิบายบรรทัด |
| `comment` | `String @db.VarChar` | Yes | comment บรรทัด |
| `currency_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_currency.id` |
| `currency_code` | `String @db.VarChar` | Yes | snapshot |
| `exchange_rate` | `Decimal @db.Decimal(15, 5)` | Yes | อัตราแลกเปลี่ยน default; default `1` |
| `exchange_rate_date` | `DateTime @db.Timestamptz(6)` | Yes | วันที่มีผล |
| `requested_qty` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนที่ขอ default; default `0` |
| `requested_unit_id` | `String @db.Uuid` | Yes | UoM ที่ขอ |
| `requested_unit_name` | `String @db.VarChar` | Yes | snapshot |
| `requested_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | Yes | factor การแปลง |
| `requested_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนฐาน default |
| `foc_qty` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวน FOC default |
| `foc_unit_id` | `String @db.Uuid` | Yes | UoM ของ FOC |
| `foc_unit_name` | `String @db.VarChar` | Yes | snapshot |
| `foc_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | Yes | factor การแปลง |
| `foc_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนฐาน FOC default |
| `tax_profile_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_tax_profile.id` |
| `tax_profile_name` | `String @db.VarChar` | Yes | snapshot |
| `tax_rate` | `Decimal @db.Decimal(15, 5)` | Yes | อัตราภาษี default |
| `tax_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนภาษี default |
| `base_tax_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนภาษีฐาน default |
| `is_tax_adjustment` | `Boolean` | Yes | flag การปรับภาษี default |
| `discount_rate` | `Decimal @db.Decimal(15, 5)` | Yes | อัตราส่วนลด default |
| `discount_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนส่วนลด default |
| `base_discount_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนส่วนลดฐาน default |
| `is_discount_adjustment` | `Boolean` | Yes | flag การปรับส่วนลด default |
| `is_active` | `Boolean` | Yes | template line นี้เปิดใช้งานหรือไม่; default `true` |
| `info` | `Json @db.JsonB` | Yes | extension bag; default `{}` |
| `dimension` | `Json @db.JsonB` | Yes | dimension ต่อบรรทัด default; default `[]` |
| `doc_version` | `Int @db.Integer` | No | version สำหรับ optimistic-concurrency; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การ soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK: `purchase_request_template_id → tb_purchase_request_template.id`; `product_id → tb_product.id` (required); `currency_id → tb_currency.id`; `tax_profile_id → tb_tax_profile.id`; `location_id → tb_location.id`; FK ที่ตั้งชื่อด้วย `@relation` สอง FK ไปยัง `tb_unit` สำหรับหน่วย requested และ FOC
**Indexes:** `@@unique([purchase_request_template_id, product_id, location_id, dimension, deleted_at])` ชื่อ `PRT1_purchase_request_template_product_location_dimension_u`; `@@index([purchase_request_template_id, product_id, location_id])` ชื่อ `PRT2_purchase_request_template_product_location_idx`; `@@index([purchase_request_template_id])` ชื่อ `PRT2_purchase_request_template_idx`

## 3. ความสัมพันธ์

```
tb_workflow
    │  1
    │
    │ * workflow_id
    ▼
tb_purchase_request ──1──*──► tb_purchase_request_comment
    │  1
    │
    │ * purchase_request_id
    ▼
tb_purchase_request_detail ──1──*──► tb_purchase_request_detail_comment
    │
    │ FK references (denormalised snapshots on the row)
    ├──► tb_product           (required, product_id)
    ├──► tb_vendor             (vendor_id)
    ├──► tb_pricelist_detail   (pricelist_detail_id)
    ├──► tb_tax_profile        (tax_profile_id)
    ├──► tb_currency           (currency_id)
    ├──► tb_location           (location_id)
    ├──► tb_delivery_point     (delivery_point_id)
    └──► tb_unit  ×3           (requested_unit_id, approved_unit_id, foc_unit_id — named relations)

tb_purchase_request_detail ──*──*──► tb_purchase_order_detail
    via bridge tb_purchase_order_detail_tb_purchase_request_detail
    (po_detail_id, pr_detail_id) — many PR lines can fan into one PO line
    (consolidation); one PR line can fan into many PO lines (partial conversion).

tb_workflow
    │
    │ * workflow_id
    ▼
tb_purchase_request_template
    │
    │ * purchase_request_template_id
    ▼
tb_purchase_request_template_detail
    │
    ├──► tb_product           (required)
    ├──► tb_currency
    ├──► tb_tax_profile
    ├──► tb_location
    └──► tb_unit  ×2           (requested_unit_id, foc_unit_id)
```

หมายเหตุ:

- **Header → detail** เป็น 1-to-many `purchase_request_id` ของ detail เป็น nullable ซึ่งอนุญาตให้มี orphan / scratch line ได้ แต่ในทางปฏิบัติบังคับเป็น 1-to-many โดย application layer
- **Header → comment** และ **detail → comment** เป็น 1-to-many ทั้งคู่ ตาราง comment เป็น record persist ของ activity ของ workflow; คอลัมน์ JSON บน header (`workflow_history`, `stages_status`) เป็น cursor in-place
- **PR → PO** เป็น many-to-many ผ่าน `tb_purchase_order_detail_tb_purchase_request_detail` เพื่อรองรับทั้งการ consolidate PR (หลาย PR → หนึ่ง PO) และการแปลงบางส่วน (หนึ่ง PR → หลาย PO)
- **Template → template_detail** เลียนแบบ header → detail แต่เป็น one-to-many สำหรับ seed เท่านั้น template ไม่มี chain อนุมัติของตัวเอง
- การประกาศ FK ด้วย `@relation` ทั้งหมดใช้ `onDelete: NoAction, onUpdate: NoAction` ดังนั้น referential integrity ถูกรักษาด้วย soft-delete ระดับ application (`deleted_at`) แทนที่จะเป็น cascade

## 4. Enum

- **`enum_purchase_request_doc_status`**: `draft` (`ร่าง` — สถานะแก้ไขได้เริ่มต้น ไม่มี commitment), `in_progress` (`กำลังดำเนินการ` — submit แล้วและกำลังเดิน chain อนุมัติ), `voided` (`โมฆะ` / `ยกเลิก` — สถานะปลายทางที่ยุติ ครอบคลุม Requestor cancel draft ที่ยังไม่ submit, approver reject กลาง chain และ Sysadmin void หลัง submit — ดู [03-user-flow](./03-user-flow) § 2), `approved` (`อนุมัติ` — chain เสร็จ พร้อมแปลงเป็น procurement), `completed` (`เสร็จสิ้น` — แปลงเป็น PO ครบและปิด) ค่า `cancelled` ที่เคยมีถูกตัดออกใน pass enum-cleanup พฤษภาคม 2026; เส้นทาง termination ทั้งหมดตอนนี้ converge ที่ `voided`
- **`enum_purchase_order_type`**: `manual` (PO สร้างโดย procurement โดยตรงไม่มี PR ต้นน้ำ), `purchase_request` (PO ที่มาจาก PR หนึ่งใบหรือมากกว่าผ่าน flow การแปลง — และยังเป็นค่า default ของ `tb_purchase_order.po_type` ซึ่งเป็นเหตุผลที่ PR-sourced คือเส้นทาง procure-to-pay มาตรฐาน)
- **`enum_last_action`**: `submitted`, `approved`, `reviewed`, `rejected` — ใช้โดย `tb_purchase_request.last_action` เพื่อจับ action ของ workflow ล่าสุด
- **`enum_comment_type`**: `user` (comment ที่มนุษย์เขียน), `system` (entry ของ activity-log ที่ workflow engine สร้างอัตโนมัติ)
- **`enum_pricelist_compare_type`**: ถูกอ้างโดย `tb_purchase_request_detail.pricelist_type` เพื่ออธิบายว่า snapshot ราคาถูกเลือกอย่างไร (default `automatic` — ดูค่า enum ทั้งหมดได้ที่ [vendor-pricelist](/th/inventory/vendor-pricelist))
- **`enum_stage_role`**: `create`, `approve`, `purchase`, `issue`, `view_only` — ใช้โดยตารางตั้งค่า `tb_workflow` ที่ใช้ร่วมกันเพื่อ label ว่าแต่ละ stage อนุญาตอะไร; ปรากฏบน PR ผ่านคอลัมน์ `workflow_*`

## 5. จุดที่ต่างจาก carmen/docs

เอกสาร `data-models.md` รุ่นเก่าอธิบาย interface ของ front-end TypeScript (`PurchaseRequest`, `PurchaseRequestItem` ฯลฯ) ไม่ใช่ entity ของ Prisma Interface พวกนั้นมี shape และ convention การตั้งชื่อต่างจาก schema ที่ persist; รายการด้านล่างจับความต่างที่เป็นเนื้อหาที่เอกสารปลายน้ำต้องประสาน

| # | รายการ | carmen/docs บอกว่า | Prisma มี | Action |
|---|------|------------------|------------|--------|
| 1 | ค่า status ของเอกสาร | `enum DocumentStatus { Draft, Submitted, InProgress, Completed, Rejected }` | `enum_purchase_request_doc_status { draft, in_progress, voided, approved, completed }` | ถือ Prisma เป็นตามมาตรฐาน `Submitted` ใน UI map ไปยัง `in_progress`; `Rejected` ไม่ใช่ status ที่เก็บ (การ reject ยุติ chain และ PR กลายเป็น `voided`); `approved` มีใน Prisma แต่ไม่มีใน enum ของ carmen/docs; `voided` ไม่มีคู่ใน carmen/docs ค่า `cancelled` เคยปรากฏใน wiki revision เก่าและ schema iteration ก่อน แต่ถูกตัดออกใน pass enum-cleanup พฤษภาคม 2026 — เส้นทาง termination ทั้งหมดตอนนี้ converge ที่ `voided` ปรับ `02-business-rules` และ enum สถานะของ front-end ตาม |
| 2 | ประเภท PR | TypeScript `enum PRType { GeneralPurchase, MarketList, AssetPurchase, ServiceRequest }` | ไม่มีคอลัมน์ `pr_type` / `type` บน `tb_purchase_request`; schema ไม่มีประเภท PR ที่เป็น enum พฤติกรรมประเภท PR ปัจจุบันถูกตั้งค่าทางอ้อมผ่านการเลือก workflow และฟิลด์ extension `info`/`dimension` | เพิ่มคอลัมน์ `pr_type` ใน Prisma + enum (แนะนำ ต้อง migrate) หรือบันทึก workaround ว่าประเภท PR ถูก encode ใต้ `info.pr_type` ยังไม่ตัดสินใจ; flag ให้ backend architecture review |
| 3 | Stage ของ workflow | TypeScript `enum WorkflowStage { requester, departmentHeadApproval, purchaseCoordinatorReview, financeManagerApproval, generalManagerApproval, completed }` | ไม่มี enum stage ตายตัว Stage เป็นแถวที่ผู้ใช้ตั้งค่าได้ใน `tb_workflow` ที่อ้างผ่าน `tb_purchase_request.workflow_id`; slug ของ stage ปัจจุบันเก็บเป็น `workflow_current_stage` (string) และ label role-per-stage ใช้ `enum_stage_role` (`create / approve / purchase / issue / view_only`) | บันทึก workflow ที่ตั้งค่าได้เป็นตามมาตรฐาน enum ของ carmen/docs แสดงเพียงหนึ่งใน default configuration |
| 4 | สถานะของ workflow | TypeScript `enum WorkflowStatus { pending, approved, rejected }` แยกจาก document status | ไม่มีคอลัมน์ workflow-status แยกต่างหาก `tb_purchase_request.last_action` (`submitted / approved / reviewed / rejected`) ครอบคลุม intent เดียวกัน | เลิกใช้ enum `WorkflowStatus` ฝั่ง front-end แล้วใช้ `last_action` + `workflow_current_stage` แทน |
| 5 | สถานะของบรรทัด | TypeScript `PurchaseRequestItemStatus = "Pending" \| "Accepted" \| "Rejected" \| "Review"` | `tb_purchase_request_detail` ไม่มีฟิลด์ status แบบ scalar; state ต่อบรรทัดเก็บในคอลัมน์ JSON `stages_status` และ string `current_stage_status` Schema ตอนนี้ประกาศ `enum_stage_action { submit, approve, reject, review, pending }` (pass cleanup พฤษภาคม 2026) ที่เจตนา type `current_stage_status` แต่ตัวคอลัมน์ยังเป็น `String?` จนกว่า migration ที่วางแผนไว้จะ validate ค่าประวัติ — ดูแถวฟิลด์ Section 2.2 และ Section 4 สำหรับ body ของ enum | Migration เพื่อ retype `current_stage_status` เป็น `enum_stage_action` รออยู่ หลัง migration ชุด `PurchaseRequestItemStatus` ของ front-end จะ map ตรง: `Pending → pending`, `Accepted → approve`, `Rejected → reject`, `Review → review` |
| 6 | Vendor บน header | `PurchaseRequest.vendor: string; vendorId: number` (vendor ระดับ header) | Vendor เป็น **reference ระดับบรรทัด** ที่ denormalize (`tb_purchase_request_detail.vendor_id` / `vendor_name`) Header ไม่มีคอลัมน์ vendor | "header vendor" ฝั่ง front-end ต้อง derive (เช่นแสดง vendor ของบรรทัดแรกหรือ `Mixed`); ปรับ interface |
| 7 | `deliveryDate` บน header | มีบน `PurchaseRequest` | Header ไม่มี `delivery_date` แต่ละบรรทัดมี `tb_purchase_request_detail.delivery_date` ของตัวเอง | เหมือนด้านบน — เป็น field ที่ derive ไม่ได้ store |
| 8 | format ของหมายเลขอ้างอิง | บันทึกเป็น `PR-2301-0001` | `tb_purchase_request.pr_no` เป็น `VarChar` ไม่มี format constraint ที่ระดับ DB; format ถูกบังคับโดย application | สังเกตว่า format เป็น application-policy ไม่ใช่ schema-enforced |

## 6. แหล่งอ้างอิง

- **หลัก (source of truth):** Prisma schema ตามที่ระบุใน callout ส่วนหัว — โดยเฉพาะ `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (model PR ทั้งหมด) และ `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (ตรวจแล้วว่าไม่มี model ของ PR)
- **รอง (cross-check ระดับแนวคิด):** `../carmen/docs/purchase-request-management/data-models.md` — interface ของ TypeScript ฝั่ง front-end; ความต่างจับไว้ใน Section 5
- โมดูลที่เกี่ยวข้อง: [purchase-order](/th/inventory/purchase-order) (เป้าหมายของการแปลง), [product](/th/inventory/product) (reference สินค้าของบรรทัด), [vendor-pricelist](/th/inventory/vendor-pricelist) (แหล่ง snapshot ราคา + ภาษี), [inventory](/th/inventory/inventory) (บริบท on-hand สำหรับ requestor)
