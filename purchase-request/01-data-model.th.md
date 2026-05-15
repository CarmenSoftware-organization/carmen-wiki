---
title: ใบขอซื้อ — แบบจำลองข้อมูล
description: เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum ของโมดูล purchase-request (อิงจาก Prisma schema)
published: true
date: 2026-05-15T09:00:00.000Z
tags: purchase-request, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# ใบขอซื้อ — แบบจำลองข้อมูล

> **แหล่งข้อมูลอ้างอิงหลัก (Source of truth):** Prisma schema ฝั่ง backend อ่านไฟล์เหล่านี้ก่อนเสมอเมื่อเขียนหรือปรับปรุงหน้านี้
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` ในแต่ละ package เป็นไฟล์ที่ถูกสร้างขึ้นอัตโนมัติ ไม่ใช่แหล่งอ้างอิง

## 1. ภาพรวม

โมดูล purchase-request เป็นเจ้าของเอนทิตีจำนวน 6 รายการในสคีมาฝั่ง tenant ได้แก่ ส่วนหัวเอกสาร (`tb_purchase_request`), บรรทัดรายการ (`tb_purchase_request_detail`), คอมเมนต์ / activity log ทั้งระดับหัวเอกสารและระดับบรรทัด (`tb_purchase_request_comment`, `tb_purchase_request_detail_comment`), และคู่ template ที่นำกลับมาใช้ใหม่ได้ (`tb_purchase_request_template`, `tb_purchase_request_template_detail`) สำหรับคำขอที่เกิดขึ้นซ้ำ เช่น รายการตลาดประจำเดือน ทั้งนี้การติดตามขั้นตอน workflow ไม่ได้แยกออกเป็นตารางต่างหาก แต่เก็บแบบ inline บนหัวเอกสารในรูปคอลัมน์ JSON (`workflow_history`, `workflow_current_stage`, `stages_status`) ร่วมกับ foreign key ไปยังตารางตั้งค่ากลาง `tb_workflow` ส่วนไทม์ไลน์เหตุการณ์ submit / approve / reject / send-back ที่ persist ลงฐานข้อมูลจะถูกเก็บผ่านตารางคอมเมนต์

PR อยู่ต้นน้ำของ [[purchase-order]] ในห่วงโซ่ procure-to-pay บรรทัด PR ที่อนุมัติแล้วจะถูกเชื่อมกับบรรทัด PO ผ่านตารางสะพาน `tb_purchase_order_detail_tb_purchase_request_detail` (บรรทัด PO หนึ่งสามารถรวมจากบรรทัด PR หลายรายการเพื่อ consolidate; บรรทัด PR หนึ่งสามารถกระจายไปหลาย PO เพื่อแปลงบางส่วน) บรรทัด PR ยังอ้างอิง [[product]], [[vendor-pricelist]], `tb_tax_profile`, `tb_currency`, `tb_unit`, `tb_location`, `tb_delivery_point`, และ `tb_vendor` โดย denormalise ข้อมูล lookup (โค้ด ชื่อ ราคาที่ snapshot) ลงบนบรรทัด ณ เวลาส่งเอกสาร เพื่อให้ข้อมูล PR ในอดีตคงที่แม้ master record จะถูกแก้ไขในภายหลัง เอนทิตี PR ทั้งหมดอยู่ในสคีมา Prisma ฝั่ง tenant — สคีมาฝั่ง platform ไม่มีโมเดล purchase-request

## 2. เอนทิตี

### 2.1 tb_purchase_request

ส่วนหัวเอกสาร PR เก็บเลขที่อ้างอิง บริบทผู้ขอและแผนก ภาพรวม workflow ยอดรวมในสกุลเงินฐาน และคอลัมน์ audit หนึ่งหัวเอกสารมีบรรทัดรายการและคอมเมนต์ได้หลายรายการ

| ฟิลด์ | Prisma Type | ค่าว่างได้ | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | ไม่ | คีย์หลัก สร้างผ่าน `gen_random_uuid()` |
| `pr_no` | `String @db.VarChar` | ไม่ | เลขที่อ้างอิง PR แบบมนุษย์อ่านได้ (เช่น `PR-2301-0001`) |
| `pr_date` | `DateTime @db.Timestamptz(6)` | ใช่ | วันที่เอกสารที่ผู้ขอเลือกตอนส่ง |
| `description` | `String @db.VarChar` | ใช่ | คำอธิบาย / เหตุผลแบบ free-text บนหัวเอกสาร |
| `workflow_id` | `String @db.Uuid` | ใช่ | FK ไป `tb_workflow` — กำหนด workflow chain ที่ PR นี้ใช้ |
| `workflow_name` | `String @db.VarChar` | ใช่ | snapshot ชื่อ workflow ณ ตอนส่ง |
| `workflow_history` | `Json @db.JsonB` | ใช่ | ไทม์ไลน์เปลี่ยน stage แบบ append-only; default `[]` แต่ละรายการมี `stage`, `action`, `message`, `by`, `at` |
| `workflow_current_stage` | `String @db.VarChar` | ใช่ | slug ของ stage ที่ถือ PR อยู่ในขณะนี้ |
| `workflow_previous_stage` | `String @db.VarChar` | ใช่ | slug ของ stage ก่อนหน้า |
| `workflow_next_stage` | `String @db.VarChar` | ใช่ | slug ของ stage ถัดไป |
| `user_action` | `Json @db.JsonB` | ใช่ | metadata ของ action ที่ค้างอยู่; default `{}` ปกติเป็น `{ "execute": [{ "id": "<user-id>" }, ...] }` ระบุผู้ที่ทำต่อได้ |
| `last_action` | `enum_last_action` | ใช่ | action ล่าสุดที่กระทำกับเอกสาร; default `submitted` |
| `last_action_at_date` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาของ `last_action` |
| `last_action_by_id` | `String @db.Uuid` | ใช่ | user id ที่กระทำ `last_action` |
| `last_action_by_name` | `String @db.VarChar` | ใช่ | snapshot ชื่อผู้กระทำ |
| `pr_status` | `enum_purchase_request_doc_status` | ใช่ | สถานะเอกสาร; default `draft` |
| `requestor_id` | `String @db.Uuid` | ใช่ | user id ของผู้ร้องขอ |
| `requestor_name` | `String @db.VarChar` | ใช่ | snapshot ชื่อผู้ร้องขอ |
| `department_id` | `String @db.Uuid` | ใช่ | แผนกที่ PR สังกัด |
| `department_name` | `String @db.VarChar` | ใช่ | snapshot ชื่อแผนก |
| `base_net_amount` | `Decimal @db.Decimal(15, 5)` | ไม่ | roll-up ของ `base_net_amount` ระดับบรรทัด; default `0` |
| `base_total_amount` | `Decimal @db.Decimal(15, 5)` | ไม่ | roll-up ของ `base_total_price` ระดับบรรทัด (net + tax); default `0` |
| `note` | `String @db.VarChar` | ใช่ | บันทึก free-text บนหัวเอกสาร |
| `info` | `Json @db.JsonB` | ใช่ | extension bag สำหรับฟิลด์เฉพาะ tenant; default `{}` |
| `dimension` | `Json @db.JsonB` | ใช่ | array ของ cost dimension (project, cost-centre, job code ฯลฯ); default `[]` |
| `doc_version` | `Int @db.Integer` | ไม่ | ตัวนับเวอร์ชันสำหรับ optimistic concurrency; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาสร้าง; default `now()` |
| `created_by_id` | `String @db.Uuid` | ใช่ | user id ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาที่อัปเดตล่าสุด; default `now()` |
| `updated_by_id` | `String @db.Uuid` | ใช่ | user id ของผู้อัปเดตล่าสุด |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลา soft-delete; ค่าที่ไม่ใช่ null หมายถึงถูกลบเชิงตรรกะ |
| `deleted_by_id` | `String @db.Uuid` | ใช่ | user id ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FK `workflow_id → tb_workflow.id` (`NoAction` ทั้ง delete/update)
**Indexes:** `@@unique([pr_no, deleted_at])` ชื่อ `PR0_pr_no_u`; `@@index([pr_no])` ชื่อ `PR0_pr_no_idx`; `@@index([requestor_id])` ชื่อ `PR0_requestor_id_idx`

### 2.2 tb_purchase_request_detail

บรรทัดรายการของ PR เก็บการอ้างอิง product, ชุด qty / unit สามชุด (requested, approved, FOC), snapshot ของ vendor และ pricelist, ภาษีและส่วนลด, ยอดบรรทัดทั้งในสกุลเงินทำรายการและสกุลเงินฐาน รวมถึงประวัติ stage ระดับบรรทัด

| ฟิลด์ | Prisma Type | ค่าว่างได้ | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | ไม่ | คีย์หลัก |
| `purchase_request_id` | `String @db.Uuid` | ใช่ | FK ไป `tb_purchase_request.id` รองรับบรรทัดร่างที่ยังไม่ผูกหัวเอกสารได้ |
| `sequence_no` | `Int` | ใช่ | ลำดับบรรทัดใน PR; default `1` |
| `location_id` | `String @db.Uuid` | ใช่ | คลัง / สถานที่ที่ต้องการสินค้า |
| `location_code` | `String @db.VarChar` | ใช่ | snapshot โค้ดสถานที่ |
| `location_name` | `String @db.VarChar` | ใช่ | snapshot ชื่อสถานที่ |
| `delivery_point_id` | `String @db.Uuid` | ใช่ | จุดส่งของเฉพาะ |
| `delivery_point_name` | `String @db.VarChar` | ใช่ | snapshot |
| `delivery_date` | `DateTime @db.Timestamptz(6)` | ใช่ | วันที่ต้องการส่งสำหรับบรรทัดนี้ |
| `product_id` | `String @db.Uuid` | ไม่ | FK ไป `tb_product.id` (จำเป็น) |
| `product_code` | `String @db.VarChar` | ใช่ | snapshot โค้ดสินค้า |
| `product_name` | `String @db.VarChar` | ใช่ | snapshot |
| `product_local_name` | `String @db.VarChar` | ใช่ | snapshot ชื่อสินค้าภาษาท้องถิ่น |
| `product_sku` | `String @db.VarChar` | ใช่ | snapshot SKU |
| `inventory_unit_id` | `String @db.Uuid` | ใช่ | หน่วยฐานของ inventory ณ ตอนส่ง |
| `inventory_unit_name` | `String @db.VarChar` | ใช่ | snapshot |
| `description` | `String @db.VarChar` | ใช่ | คำอธิบายบรรทัด (มักใช้แทนชื่อสินค้าในกรณี free-text) |
| `comment` | `String @db.VarChar` | ใช่ | คอมเมนต์ระดับบรรทัด |
| `vendor_id` | `String @db.Uuid` | ใช่ | FK ไป `tb_vendor.id` — vendor ที่ถูก allocate ให้บรรทัดนี้ |
| `vendor_name` | `String @db.VarChar` | ใช่ | snapshot |
| `pricelist_detail_id` | `String @db.Uuid` | ใช่ | FK ไป `tb_pricelist_detail.id` — แถว pricelist ที่ดึงราคามาใช้ |
| `pricelist_no` | `String @db.VarChar` | ใช่ | snapshot เลขที่ pricelist |
| `pricelist_unit` | `String @db.VarChar` | ใช่ | snapshot หน่วยใน pricelist |
| `pricelist_price` | `Decimal @db.Decimal(20, 5)` | ใช่ | snapshot ราคาต่อหน่วยจาก pricelist; default `0` |
| `pricelist_type` | `enum_pricelist_compare_type` | ใช่ | วิธีที่ราคานี้ถูกเลือก (`automatic` เป็นค่า default) |
| `currency_id` | `String @db.Uuid` | ใช่ | FK ไป `tb_currency.id` — สกุลเงินทำรายการ |
| `currency_code` | `String @db.VarChar` | ใช่ | snapshot |
| `exchange_rate` | `Decimal @db.Decimal(15, 5)` | ใช่ | อัตราแลกเปลี่ยนทำรายการ-ฐาน; default `1` |
| `exchange_rate_date` | `DateTime @db.Timestamptz(6)` | ใช่ | วันที่ของ snapshot exchange rate |
| `requested_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | จำนวนในหน่วยที่ขอ; default `0` |
| `requested_unit_id` | `String @db.Uuid` | ใช่ | หน่วยที่ผู้ขอเลือก |
| `requested_unit_name` | `String @db.VarChar` | ใช่ | snapshot |
| `requested_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | ใช่ | conversion factor ไปหน่วยฐาน inventory |
| `requested_base_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | `requested_qty × requested_unit_conversion_factor` |
| `approved_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | จำนวนในหน่วยที่อนุมัติ อาจต่างจาก `requested_qty` |
| `approved_unit_id` | `String @db.Uuid` | ใช่ | หน่วยที่ใช้กับ qty อนุมัติ |
| `approved_unit_name` | `String @db.VarChar` | ใช่ | snapshot |
| `approved_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | ใช่ | conversion factor ไปหน่วยฐาน |
| `approved_base_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | `approved_qty × approved_unit_conversion_factor` |
| `foc_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | qty แถมในหน่วย FOC; default `0` |
| `foc_unit_id` | `String @db.Uuid` | ใช่ | หน่วยของ FOC qty |
| `foc_unit_name` | `String @db.VarChar` | ใช่ | snapshot |
| `foc_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | ใช่ | conversion factor ไปหน่วยฐาน |
| `foc_base_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | `foc_qty × foc_unit_conversion_factor` |
| `tax_profile_id` | `String @db.Uuid` | ใช่ | FK ไป `tb_tax_profile.id` |
| `tax_profile_name` | `String @db.VarChar` | ใช่ | snapshot |
| `tax_rate` | `Decimal @db.Decimal(15, 5)` | ใช่ | อัตราภาษีที่มีผล; default `0` |
| `tax_amount` | `Decimal @db.Decimal(20, 5)` | ใช่ | จำนวนภาษีในสกุลเงินทำรายการ |
| `base_tax_amount` | `Decimal @db.Decimal(20, 5)` | ใช่ | จำนวนภาษีในสกุลเงินฐาน |
| `is_tax_adjustment` | `Boolean` | ใช่ | `true` เมื่อผู้ใช้ override จำนวนภาษีเองด้วยมือ; default `false` |
| `discount_rate` | `Decimal @db.Decimal(15, 5)` | ใช่ | อัตราส่วนลด %; default `0` |
| `discount_amount` | `Decimal @db.Decimal(20, 5)` | ใช่ | จำนวนส่วนลดในสกุลเงินทำรายการ |
| `base_discount_amount` | `Decimal @db.Decimal(20, 5)` | ใช่ | จำนวนส่วนลดในสกุลเงินฐาน |
| `is_discount_adjustment` | `Boolean` | ใช่ | `true` เมื่อผู้ใช้ override ส่วนลดเองด้วยมือ; default `false` |
| `sub_total_price` | `Decimal @db.Decimal(20, 5)` | ใช่ | `pricelist_price × approved_qty` (สกุลเงินทำรายการ) |
| `net_amount` | `Decimal @db.Decimal(20, 5)` | ใช่ | `sub_total_price − discount_amount` |
| `total_price` | `Decimal @db.Decimal(20, 5)` | ใช่ | `net_amount + tax_amount` |
| `base_price` | `Decimal @db.Decimal(20, 5)` | ใช่ | `pricelist_price × exchange_rate` |
| `base_sub_total_price` | `Decimal @db.Decimal(20, 5)` | ใช่ | `base_price × approved_qty` |
| `base_net_amount` | `Decimal @db.Decimal(20, 5)` | ใช่ | `base_sub_total_price − base_discount_amount` |
| `base_total_price` | `Decimal @db.Decimal(20, 5)` | ใช่ | `base_net_amount + base_tax_amount` |
| `history` | `Json @db.JsonB` | ใช่ | ไทม์ไลน์ stage ระดับบรรทัด (`seq`, `name`, `status`, `to_stage`, `message`, `by_id`, `by_name`, `at_date`); default `[]` |
| `stages_status` | `Json @db.JsonB` | ใช่ | cursor stage ระดับบรรทัด — array ของ `{ seq, name, status }`; default `{}` |
| `current_stage_status` | `String @db.VarChar` | ใช่ | working copy ของสถานะ stage ปัจจุบัน |
| `info` | `Json @db.JsonB` | ใช่ | extension bag; default `{}` |
| `dimension` | `Json @db.JsonB` | ใช่ | dimension ระดับบรรทัด; default `[]` |
| `doc_version` | `Int @db.Integer` | ไม่ | เวอร์ชันสำหรับ optimistic concurrency; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาสร้าง |
| `created_by_id` | `String @db.Uuid` | ใช่ | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | ใช่ | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลา soft-delete |
| `deleted_by_id` | `String @db.Uuid` | ใช่ | id ผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FK: `purchase_request_id → tb_purchase_request.id`; `product_id → tb_product.id` (จำเป็น); `vendor_id → tb_vendor.id`; `pricelist_detail_id → tb_pricelist_detail.id`; `tax_profile_id → tb_tax_profile.id`; `currency_id → tb_currency.id`; `location_id → tb_location.id`; `delivery_point_id → tb_delivery_point.id`; และ `@relation` ตั้งชื่อ 3 ชุดไปยัง `tb_unit` สำหรับ requested / approved / FOC unit
**Indexes:** `@@unique([purchase_request_id, product_id, location_id, dimension, deleted_at])` ชื่อ `PR1_purchase_request_product_location_dimension_u`; `@@index([product_id])` ชื่อ `PRD1_product_id_idx`; `@@index([location_id])` ชื่อ `PRD1_location_id_idx`; `@@index([location_id, product_id])` ชื่อ `PRD1_location_product_idx`; `@@index([purchase_request_id])` ชื่อ `PRD1_purchase_request_id_idx`

### 2.3 tb_purchase_request_comment

รายการ workflow / activity log ที่ผูกกับหัวเอกสาร PR — สคีมา Prisma ไม่มีตาราง `tb_purchase_request_workflow` โดยเฉพาะ ตารางคอมเมนต์นี้ ประกอบกับคอลัมน์ JSON workflow บนหัวเอกสาร คือบันทึกถาวรของไทม์ไลน์ workflow แต่ละแถวเป็นคอมเมนต์ของผู้ใช้ (`type = user`) หรือเหตุการณ์ของระบบ (`type = system`) เช่น การเปลี่ยน stage

| ฟิลด์ | Prisma Type | ค่าว่างได้ | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | ไม่ | คีย์หลัก |
| `purchase_request_id` | `String @db.Uuid` | ไม่ | FK ไป `tb_purchase_request.id` |
| `type` | `enum_comment_type` | ไม่ | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | ใช่ | user id ผู้เขียน (เป็น null สำหรับรายการ `system`) |
| `message` | `String` | ใช่ | เนื้อหาคอมเมนต์ free-text |
| `attachments` | `Json @db.JsonB` | ใช่ | array ของ `{ originalName, fileToken, contentType }`; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาสร้าง |
| `created_by_id` | `String @db.Uuid` | ใช่ | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | ใช่ | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลา soft-delete |
| `deleted_by_id` | `String @db.Uuid` | ใช่ | id ผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FK `purchase_request_id → tb_purchase_request.id` (`NoAction` ทั้ง delete/update)
**Indexes:** ไม่มี index เพิ่มเติมนอกจากคีย์หลัก

### 2.4 tb_purchase_request_detail_comment

คู่ขนานระดับบรรทัดของ `tb_purchase_request_comment` ใช้บันทึกคอมเมนต์และเหตุการณ์ระบบที่ผูกกับบรรทัด PR เดียว — ปกติใช้ระหว่าง approval เพื่อบันทึกการตัดสินใจระดับ stage และเหตุผลการปฏิเสธรายบรรทัด

| ฟิลด์ | Prisma Type | ค่าว่างได้ | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | ไม่ | คีย์หลัก |
| `purchase_request_detail_id` | `String @db.Uuid` | ไม่ | FK ไป `tb_purchase_request_detail.id` |
| `type` | `enum_comment_type` | ไม่ | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | ใช่ | user id ผู้เขียน |
| `message` | `String` | ใช่ | เนื้อหาคอมเมนต์ free-text |
| `attachments` | `Json @db.JsonB` | ใช่ | array ของไฟล์แนบ; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาสร้าง |
| `created_by_id` | `String @db.Uuid` | ใช่ | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | ใช่ | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลา soft-delete |
| `deleted_by_id` | `String @db.Uuid` | ใช่ | id ผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FK `purchase_request_detail_id → tb_purchase_request_detail.id`
**Indexes:** ไม่มี index เพิ่มเติมนอกจากคีย์หลัก

### 2.5 tb_purchase_request_template

ส่วนหัวของ template PR ที่นำกลับมาใช้ใหม่ (เช่น ชุดรายการตลาดรายสัปดาห์) Template เองไม่เข้า workflow — ใช้เพื่อ seed PR ใหม่เท่านั้น

| ฟิลด์ | Prisma Type | ค่าว่างได้ | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | ไม่ | คีย์หลัก |
| `name` | `String @db.VarChar` | ไม่ | ชื่อ template |
| `description` | `String @db.VarChar` | ใช่ | คำอธิบาย free-text |
| `workflow_id` | `String @db.Uuid` | ใช่ | FK ไป `tb_workflow` — workflow default ของ PR ที่เกิดจาก template นี้ |
| `workflow_name` | `String @db.VarChar` | ใช่ | snapshot ชื่อ workflow |
| `is_active` | `Boolean` | ใช่ | template นี้ถูกเลือกใช้ได้หรือไม่; default `true` |
| `note` | `String @db.VarChar` | ใช่ | บันทึก free-text |
| `info` | `Json @db.JsonB` | ใช่ | extension bag; default `{}` |
| `dimension` | `Json @db.JsonB` | ใช่ | dimension default; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาสร้าง |
| `created_by_id` | `String @db.Uuid` | ใช่ | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | ใช่ | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลา soft-delete |
| `deleted_by_id` | `String @db.Uuid` | ใช่ | id ผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FK `workflow_id → tb_workflow.id`
**Indexes:** `@@unique([name, workflow_id, deleted_at])` ชื่อ `PRT1_name_workflow_id_u`; `@@index([workflow_id])` ชื่อ `PRT1_workflow_id_idx`; `@@index([name])` ชื่อ `PRT1_name_idx`

### 2.6 tb_purchase_request_template_detail

บรรทัดรายการของ template PR สคีมาคล้ายกับ `tb_purchase_request_detail` ในฟิลด์ที่ template ต้องใช้ seed — product, location, requested qty / unit, FOC, ภาษี, ส่วนลด, สกุลเงิน — แต่ตั้งใจตัดฟิลด์ฝั่ง approval (`approved_qty`, `approved_unit_*`, workflow `history`, `stages_status`) รวมถึงคอลัมน์ `vendor_id` / `pricelist_detail_id` ออกไป เพราะข้อมูลเหล่านั้นจะตั้งค่าตอนสร้าง PR จริง ไม่เก็บลง template

| ฟิลด์ | Prisma Type | ค่าว่างได้ | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | ไม่ | คีย์หลัก |
| `purchase_request_template_id` | `String @db.Uuid` | ใช่ | FK ไป `tb_purchase_request_template.id` |
| `location_id` | `String @db.Uuid` | ใช่ | คลัง / สถานที่ |
| `location_code` | `String @db.VarChar` | ใช่ | snapshot |
| `location_name` | `String @db.VarChar` | ใช่ | snapshot |
| `delivery_point_id` | `String @db.Uuid` | ใช่ | จุดส่งของ |
| `delivery_point_name` | `String @db.VarChar` | ใช่ | snapshot |
| `product_id` | `String @db.Uuid` | ไม่ | FK ไป `tb_product.id` (จำเป็น) |
| `product_code` | `String @db.VarChar` | ใช่ | snapshot |
| `product_name` | `String @db.VarChar` | ใช่ | snapshot |
| `product_local_name` | `String @db.VarChar` | ใช่ | snapshot |
| `product_sku` | `String @db.VarChar` | ใช่ | snapshot |
| `inventory_unit_id` | `String @db.Uuid` | ใช่ | หน่วยฐาน inventory |
| `inventory_unit_name` | `String @db.VarChar` | ใช่ | snapshot |
| `description` | `String @db.VarChar` | ใช่ | คำอธิบายบรรทัด |
| `comment` | `String @db.VarChar` | ใช่ | คอมเมนต์บรรทัด |
| `currency_id` | `String @db.Uuid` | ใช่ | FK ไป `tb_currency.id` |
| `currency_code` | `String @db.VarChar` | ใช่ | snapshot |
| `exchange_rate` | `Decimal @db.Decimal(15, 5)` | ใช่ | อัตราแลกเปลี่ยน default; default `1` |
| `exchange_rate_date` | `DateTime @db.Timestamptz(6)` | ใช่ | วันที่มีผล |
| `requested_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | requested qty default; default `0` |
| `requested_unit_id` | `String @db.Uuid` | ใช่ | หน่วยที่ขอ |
| `requested_unit_name` | `String @db.VarChar` | ใช่ | snapshot |
| `requested_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | ใช่ | conversion factor |
| `requested_base_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | base qty default |
| `foc_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | FOC qty default |
| `foc_unit_id` | `String @db.Uuid` | ใช่ | หน่วย FOC |
| `foc_unit_name` | `String @db.VarChar` | ใช่ | snapshot |
| `foc_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | ใช่ | conversion factor |
| `foc_base_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | base FOC qty default |
| `tax_profile_id` | `String @db.Uuid` | ใช่ | FK ไป `tb_tax_profile.id` |
| `tax_profile_name` | `String @db.VarChar` | ใช่ | snapshot |
| `tax_rate` | `Decimal @db.Decimal(15, 5)` | ใช่ | อัตราภาษี default |
| `tax_amount` | `Decimal @db.Decimal(20, 5)` | ใช่ | จำนวนภาษี default |
| `base_tax_amount` | `Decimal @db.Decimal(20, 5)` | ใช่ | จำนวนภาษีฐาน default |
| `is_tax_adjustment` | `Boolean` | ใช่ | ค่า flag ปรับภาษี default |
| `discount_rate` | `Decimal @db.Decimal(15, 5)` | ใช่ | อัตราส่วนลด default |
| `discount_amount` | `Decimal @db.Decimal(20, 5)` | ใช่ | จำนวนส่วนลด default |
| `base_discount_amount` | `Decimal @db.Decimal(20, 5)` | ใช่ | จำนวนส่วนลดฐาน default |
| `is_discount_adjustment` | `Boolean` | ใช่ | ค่า flag ปรับส่วนลด default |
| `is_active` | `Boolean` | ใช่ | บรรทัด template นี้เปิดใช้งานหรือไม่; default `true` |
| `info` | `Json @db.JsonB` | ใช่ | extension bag; default `{}` |
| `dimension` | `Json @db.JsonB` | ใช่ | dimension ระดับบรรทัด default; default `[]` |
| `doc_version` | `Int @db.Integer` | ไม่ | เวอร์ชันสำหรับ optimistic concurrency; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาสร้าง |
| `created_by_id` | `String @db.Uuid` | ใช่ | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | ใช่ | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลา soft-delete |
| `deleted_by_id` | `String @db.Uuid` | ใช่ | id ผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FK: `purchase_request_template_id → tb_purchase_request_template.id`; `product_id → tb_product.id` (จำเป็น); `currency_id → tb_currency.id`; `tax_profile_id → tb_tax_profile.id`; `location_id → tb_location.id`; และ `@relation` ตั้งชื่อ 2 ชุดไปยัง `tb_unit` สำหรับ requested และ FOC unit
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
    (po_detail_id, pr_detail_id) — บรรทัด PR หลายรายการสามารถรวมเป็น
    บรรทัด PO เดียว (consolidation); บรรทัด PR หนึ่งบรรทัดสามารถ
    กระจายไปหลายบรรทัด PO (การแปลงบางส่วน)

tb_workflow
    │
    │ * workflow_id
    ▼
tb_purchase_request_template ──1──*──► tb_purchase_request_template_comment
    │  1
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

ข้อสังเกต:

- **หัวเอกสาร → บรรทัด** เป็น 1-to-many ฟิลด์ `purchase_request_id` ของบรรทัดเป็น nullable จึงอนุญาตให้มีบรรทัด orphan / scratch ได้ แต่ในทางปฏิบัติ application layer บังคับให้เป็น 1-to-many
- **หัวเอกสาร → คอมเมนต์** และ **บรรทัด → คอมเมนต์** เป็น 1-to-many ทั้งคู่ ตารางคอมเมนต์คือบันทึกถาวรของกิจกรรม workflow ส่วนคอลัมน์ JSON บนหัวเอกสาร (`workflow_history`, `stages_status`) ทำหน้าที่เป็น cursor ในที่
- **PR → PO** เป็น many-to-many ผ่าน `tb_purchase_order_detail_tb_purchase_request_detail` เพื่อรองรับทั้งการ consolidate PR (PR หลายฉบับ → PO เดียว) และการแปลงบางส่วน (PR หนึ่ง → PO หลายฉบับ)
- **Template → template_detail** มีโครงสร้างคู่ขนานกับหัวเอกสาร → บรรทัด เป็น one-to-many เพื่อใช้ seed เท่านั้น template ไม่มี approval chain ของตัวเอง
- การประกาศ FK `@relation` ทั้งหมดใช้ `onDelete: NoAction, onUpdate: NoAction` ดังนั้น referential integrity จึงรักษาด้วย soft-delete ระดับแอปพลิเคชัน (`deleted_at`) แทน cascade

## 4. Enum

- **`enum_purchase_request_doc_status`**: `draft` (ร่าง — สถานะเริ่มต้นที่ยังแก้ไขได้ ไม่มี commitment), `in_progress` (กำลังดำเนินการ — ส่งแล้วและกำลังเดิน approval chain), `voided` (โมฆะ — ถูกทำให้เป็นโมฆะหลังส่ง), `approved` (อนุมัติ — chain ครบ พร้อมแปลงเป็น procurement), `completed` (เสร็จสิ้น — แปลงเป็น PO ครบและปิดเอกสารแล้ว), `cancelled` (ยกเลิก — ถูกยกเลิกโดยผู้ใช้หรือระบบก่อนได้รับการอนุมัติ)
- **`enum_purchase_order_type`**: `manual` (PO ที่ procurement สร้างเองโดยไม่มี PR ต้นน้ำ), `purchase_request` (PO ที่มาจาก PR หนึ่งฉบับขึ้นไปผ่าน conversion — และเป็นค่า default ของ `tb_purchase_order.po_type` ด้วย ซึ่งทำให้ PR-sourced เป็นเส้นทาง procure-to-pay มาตรฐาน)
- **`enum_last_action`**: `submitted`, `approved`, `reviewed`, `rejected` — ใช้โดย `tb_purchase_request.last_action` เพื่อบันทึก action workflow ล่าสุด
- **`enum_comment_type`**: `user` (คอมเมนต์ที่มนุษย์เขียน), `system` (รายการ activity log ที่ workflow engine สร้างอัตโนมัติ)
- **`enum_pricelist_compare_type`**: อ้างอิงโดย `tb_purchase_request_detail.pricelist_type` เพื่อบรรยายว่า snapshot ราคาถูกเลือกอย่างไร (default `automatic` — ดูค่าทั้งหมดได้ที่ [[vendor-pricelist]])
- **`enum_stage_role`**: `create`, `approve`, `purchase`, `issue`, `view_only` — ใช้โดย `tb_workflow` ส่วนกลางเพื่อระบุว่าแต่ละ stage อนุญาตอะไรได้บ้าง โผล่มาที่ PR ผ่านคอลัมน์ `workflow_*`

## 5. ความแตกต่างจาก carmen/docs

เอกสาร `data-models.md` ฉบับเดิมอธิบาย TypeScript interface ฝั่ง front-end (`PurchaseRequest`, `PurchaseRequestItem` ฯลฯ) ไม่ใช่เอนทิตี Prisma รูปร่างและการตั้งชื่อจึงต่างจากสคีมาที่ persist จริง รายการด้านล่างคือความแตกต่างที่ documentation ปลายทางต้องปรับให้ตรงกัน

| # | Item | carmen/docs says | Prisma has | Action |
|---|------|------------------|------------|--------|
| 1 | ค่าสถานะเอกสาร | `enum DocumentStatus { Draft, Submitted, InProgress, Completed, Rejected }` | `enum_purchase_request_doc_status { draft, in_progress, voided, approved, completed, cancelled }` | ถือว่า Prisma เป็น canonical `Submitted` ใน UI map ไปยัง `in_progress`; `Rejected` ไม่ใช่สถานะที่เก็บถาวร (การปฏิเสธจบ chain แล้ว PR เปลี่ยนเป็น `cancelled` หรือ `voided`); `approved` มีใน Prisma แต่ไม่มีใน enum ของ carmen/docs; `voided` และ `cancelled` ไม่มีคู่เทียบใน carmen/docs ต้องปรับ `02-business-rules` และ enum สถานะของ front-end ให้สอดคล้อง |
| 2 | ประเภท PR | TypeScript `enum PRType { GeneralPurchase, MarketList, AssetPurchase, ServiceRequest }` | ไม่มีคอลัมน์ `pr_type` / `type` บน `tb_purchase_request` สคีมาไม่มี PR type ที่เป็น enum พฤติกรรมตามประเภท PR ปัจจุบันถูกตั้งค่าทางอ้อมผ่านการเลือก workflow และฟิลด์ส่วนขยาย `info` / `dimension` | เพิ่มคอลัมน์ `pr_type` + enum ใน Prisma (ทางเลือกที่แนะนำ ต้อง migration) หรือ document workaround ว่า PR type เก็บใน `info.pr_type` รอการตัดสินใจ — ฝากให้ทีม backend architecture review |
| 3 | ขั้น workflow | TypeScript `enum WorkflowStage { requester, departmentHeadApproval, purchaseCoordinatorReview, financeManagerApproval, generalManagerApproval, completed }` | ไม่มี enum stage ตายตัว stage เป็นแถวที่ผู้ใช้ตั้งค่าใน `tb_workflow` อ้างอิงผ่าน `tb_purchase_request.workflow_id`; slug ของ stage ปัจจุบันเก็บใน `workflow_current_stage` (string); role ต่อ stage ใช้ `enum_stage_role` (`create / approve / purchase / issue / view_only`) | document workflow แบบ configurable เป็น canonical enum ใน carmen/docs เป็นเพียงหนึ่งค่า config default |
| 4 | สถานะ workflow | TypeScript `enum WorkflowStatus { pending, approved, rejected }` แยกจากสถานะเอกสาร | ไม่มีคอลัมน์ workflow-status แยก `tb_purchase_request.last_action` (`submitted / approved / reviewed / rejected`) ครอบคลุมความหมายเดียวกัน | เลิกใช้ `WorkflowStatus` enum ฝั่ง front-end แล้วใช้ `last_action` + `workflow_current_stage` แทน |
| 5 | สถานะบรรทัด | TypeScript `PurchaseRequestItemStatus = "Pending" \| "Accepted" \| "Rejected" \| "Review"` | `tb_purchase_request_detail` ไม่มีฟิลด์ status เป็น scalar; state ระดับบรรทัดเก็บในคอลัมน์ JSON `stages_status` และ string `current_stage_status` | สร้าง enum `stage_status` เป็น typed บนแถว detail หรือ document โครงสร้าง JSON เป็น canonical |
| 6 | Vendor บนหัวเอกสาร | `PurchaseRequest.vendor: string; vendorId: number` (vendor ระดับหัว) | Vendor เป็น **อ้างอิงระดับบรรทัด** ที่ denormalise (`tb_purchase_request_detail.vendor_id` / `vendor_name`) หัวเอกสารไม่มีคอลัมน์ vendor | "header vendor" ฝั่ง front-end ต้องคำนวณเอา (เช่น แสดง vendor ของบรรทัดแรก หรือ `Mixed`) ปรับ interface ตาม |
| 7 | `deliveryDate` บนหัวเอกสาร | มีอยู่บน `PurchaseRequest` | หัวเอกสารไม่มี `delivery_date` แต่ละบรรทัดเก็บ `tb_purchase_request_detail.delivery_date` ของตัวเอง | เช่นเดียวกับข้อ 6 — เป็นฟิลด์ derived ไม่ใช่ stored |
| 8 | รูปแบบเลขที่อ้างอิง | ระบุไว้เป็น `PR-2301-0001` | `tb_purchase_request.pr_no` เป็น `VarChar` ไม่มี constraint รูปแบบที่ DB; รูปแบบบังคับโดย application | บันทึกว่ารูปแบบเป็น policy ระดับ application ไม่ใช่ schema-enforced |

## 6. แหล่งอ้างอิง

- **Primary (source of truth):** Prisma schema ในกล่อง callout ด้านบน — โดยเฉพาะ `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (โมเดล PR ทั้งหมด) และ `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (ตรวจสอบแล้วว่าไม่มีโมเดล PR)
- **Secondary (concept cross-check):** `../carmen/docs/purchase-request-management/data-models.md` — TypeScript interface ฝั่ง front-end ความแตกต่างถูกบันทึกในหัวข้อ 5
- โมดูลที่เกี่ยวข้อง: [[purchase-order]] (ปลายทางของ conversion), [[product]] (อ้างอิงสินค้าระดับบรรทัด), [[vendor-pricelist]] (แหล่ง snapshot ของราคาและภาษี), [[inventory]] (บริบทยอดคงเหลือสำหรับผู้ขอ)
