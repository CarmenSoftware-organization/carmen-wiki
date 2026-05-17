---
title: สินค้า (Product) — User Flow
description: วงจรชีวิตของข้อมูลหลักของสินค้าและไฟล์ flow เฉพาะ persona
published: true
date: 2026-05-17T12:00:00.000Z
tags: product, user-flow, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:30:00.000Z
---

# สินค้า (Product) — User Flow

> **At a Glance**
> **โมดูล:** [[product]] &nbsp;·&nbsp; **Persona:** Product Administrator (เจ้าของ CRUD) &nbsp;·&nbsp; Purchaser (อ่านอย่างเดียว) &nbsp;·&nbsp; Store Keeper (อ่านอย่างเดียว)
> **วงจรชีวิตของ workflow:** Master-data — ไม่มี `doc_status` ไม่มี period lock `(none) → active ↔ inactive → soft-deleted (restore ได้)` `is_active = false` ซ่อนจาก picker ทุกการเปลี่ยนตรวจสอบได้และเป็นทันที
> **เจาะลงในมุมมองต่อ persona ด้านล่างสำหรับรายละเอียดระดับ action**

## 1. ภาพรวม

หน้านี้เป็น **จุดเข้าภาพรวม** สำหรับชุด user-flow ของโมดูล `product` Product เป็น **master-data** ไม่ใช่ธุรกรรม — ไม่มี event การ post ไม่มี journal-entry fan-out ไม่มี period boundary ที่ล็อก record วงจรชีวิตที่ persona เดินคือ **วงจรชีวิตของแถวแคตตาล็อก**: ถูกสร้างโดย Product Administrator (มักผ่าน import สำหรับการโหลดแคตตาล็อกเริ่มต้น จากนั้นทีละรายการสำหรับ SKU ใหม่และการเปิดตัวเมนู) อยู่ในสถานะ `active` ขณะที่ procurement และ operation ใช้ อาจถูกปิดใช้เมื่อเลิกใช้ (subject ต่อ in-use guard) และ soft-delete เมื่อเลิกใช้จริง (subject ต่อ in-use guard ที่เข้มกว่า) Persona ทั้งสามที่โมดูลให้บริการมีความสัมพันธ์กับวงจรชีวิตนี้ต่างกันมาก — Product Administrator **เป็นเจ้าของ** มัน Purchaser และ Store Keeper เป็น **ผู้บริโภค** ที่ค้นหาและอ่านแคตตาล็อกระหว่าง workflow เอกสารของตนเอง

Section 2 ด้านล่างอธิบาย **state machine ของ record สินค้า** — ชุด canonical ของการเปลี่ยนที่ถูกกฎหมายโดยไม่ขึ้นกับว่าใครเป็นคนทำ Section 3 จัดดัชนีไฟล์ drill-down ต่อ persona สามตัว Section 4 สรุป handoff ข้าม persona — ซึ่งจงใจให้เบาในโมดูลนี้: งานของ Product Administrator ป้อนให้ผู้บริโภคแต่ผู้บริโภคไม่ป้อนกลับเข้าสู่การเปลี่ยนวงจรชีวิตของสินค้า (นอกเหนือจาก comment / feedback) handoff ที่มีอยู่ส่วนใหญ่คือ Purchaser → Product Administrator (flag entry แคตตาล็อกเก่า ขอสินค้าใหม่) และ Store Keeper → Product Administrator (flag barcode ไม่ตรง ขอการปรับนโยบาย location)

หมายเหตุ Master-data: เนื่องจาก Purchaser และ Store Keeper เป็นผู้บริโภค lookup-only ไฟล์ persona ของพวกเขา **มีขอบเขตที่แคบกว่ามาก** กว่าไฟล์ persona ของโมดูลธุรกรรมที่เทียบเท่า ไม่มี workflow draft → submit → approve ที่พวกเขาขับเคลื่อน มีเพียงค้นหา filter scan อ่าน และ (เมื่อใช้ได้) comment ในทางตรงกันข้าม ไฟล์ persona ของ Product Administrator คือไฟล์ที่กว้าง — ครอบคลุม surface CRUD เต็ม ห่วงโซ่การจำแนก หน่วยและการแปลง location mapping vendor mapping การเปลี่ยนวงจรชีวิต และ bulk import / export

## 2. วงจรชีวิตของ Record สินค้า

State machine เดียวควบคุม record สินค้า:

| จากสถานะ | Action | ไปสถานะ | อนุญาตให้ | เงื่อนไขเบื้องต้น |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | create (UI form หรือ bulk import) | `active` | Product Administrator (`PRD_AUTH_001`, `PRD_AUTH_003` สำหรับ bulk) | กฎ validation `PRD_VAL_001`–`PRD_VAL_016` ผ่านทั้งหมด การจำแนก (`tb_product_item_group_id`), หน่วยฐาน (`inventory_unit_id`) และ code/name จำเป็น Tax-profile และค่าความคลาดเคลื่อนอาจสืบทอดจากห่วงโซ่การจำแนกตาม `PRD_CALC_002`–`PRD_CALC_003` เขียน `tb_product` ด้วย `product_status_type = active`, `is_active = true` Activity log บันทึก create |
| `active` | แก้ฟิลด์ (name, description, classification, units mapping, location policy, vendor mapping, deviation tolerances, standard_cost, tax-profile override, info JSON, certification JSON) | `active` | Product Administrator | กฎ validation รันใหม่ตามฟิลด์ที่แก้ `inventory_unit_id` **ไม่สามารถเปลี่ยนได้** เมื่อสินค้ามีประวัติคลังใด ๆ (`PRD_VAL_003`) การเปลี่ยน classification เป็น prospective ตาม `PRD_LIFE_010` Activity log บันทึกการเปลี่ยนระดับฟิลด์แต่ละครั้ง |
| `active` | ปิดใช้ | `inactive` | Product Administrator (`PRD_AUTH_004`) | lifecycle guard `PRD_LIFE_002`: ไม่มีบรรทัด PR / PO / SR เปิดอาจอ้างอิงสินค้า Soft-block ถ้าถูกอ้างอิงโดยสูตรที่ publish (override option มีพร้อมเหตุผลใน activity log) ใน override สูตรที่ได้รับผลกระทบอาจถูก flag สำหรับ review อัตโนมัติ ตั้ง `product_status_type = inactive`; `is_active` ไม่เปลี่ยน Picker exclusion มีผลทันที |
| `inactive` | re-activate | `active` | Product Administrator (`PRD_AUTH_004`) | lifecycle guard `PRD_LIFE_003`: ห่วงโซ่การจำแนกยังถูกต้อง ค่าการสืบทอดคำนวณใหม่ที่การอ่านครั้งต่อไป Recipe-review flag จาก `PRD_LIFE_002` ถูกล้าง |
| `active | inactive` | hard-disable (`is_active = false`) | `(hidden — ไม่ปรากฏใน picker ที่ไหน)` | Product Administrator | lifecycle guard `PRD_LIFE_005`: เหมือนกับ guard ของการปิดใช้บวกกฎที่ `is_active = false` หมายถึง `product_status_type = inactive` ใช้สำหรับสินค้าที่ควรหายไปจาก admin view (เช่น true end-of-life หรือการลบที่บังคับโดย compliance) |
| `active | inactive` | soft-delete | `soft-deleted` | Product Administrator (`PRD_AUTH_001`) | Hard guard `PRD_LIFE_004`: on-hand ปัจจุบันเป็นศูนย์ (derive) ที่ทุก location; ไม่มีบรรทัดเอกสารที่ไม่ใช่ terminal อ้างอิงสินค้า (PR / PO / GRN / SR / count / spot-check / credit-note / pricelist / recipe-ingredient); ไม่มีวัตถุดิบสูตรที่ไม่ถูกลบ ตั้ง `deleted_at`, `deleted_by_id` `(code, name)` ใช้งานได้ใหม่ |
| `soft-deleted` | restore | `active` | Product Administrator (พิเศษ) | lifecycle guard `PRD_LIFE_009`: `(code, name)` ต้องไม่ซ้ำในสินค้า live (ปฏิเสธถ้าสินค้าใหม่เอา code/name ที่ปล่อยมาในระหว่างนั้น) ล้าง `deleted_at` / `deleted_by_id` |

หมายเหตุ:

- **ไม่มี workflow `doc_status`** ต่างจากโมดูลธุรกรรม สินค้าไม่มีการ progression `draft → in_progress → completed` ทุกการ save เป็นทันที; ทุกการเปลี่ยนตรวจสอบได้แต่ทันที
- **ไม่มี period boundary** Product master ไม่ถูก period-lock การแก้ไขยังคงเป็นไปได้แม้เมื่อ accounting period รอบนอกเป็น `closed` หรือ `locked` — เฉพาะโมดูล **ธุรกรรม** ที่เคารพ period lock
- **Bulk import คือเส้นทาง create หลัก** สำหรับการโหลดแคตตาล็อกเริ่มต้นและสำหรับการเปิด property ใหม่ Product Administrator รัน import ใน dry-run mode review การ validate report แก้ error แล้วรัน strict-mode commit state machine ด้านบนใช้ต่อแถว; แถวที่ผ่านเข้าสู่ `active` แถวที่ fail ถูกรายงาน
- **Audit log เป็น surface ของบทสนทนาสำหรับ event วงจรชีวิต** ทุกการเปลี่ยนบันทึก actor / timestamp / เหตุผล ตาราง comment (`tb_product_comment`) มีการอภิปรายของมนุษย์ (โดยทั่วไป feedback ขาเข้าจาก Purchaser / Store Keeper); activity log มี event ของระบบ

## 3. สารบัญ Persona

แต่ละ persona ด้านล่างมีไฟล์ drill-down เฉพาะอธิบาย entry point, primary flow, decision branch และ exit point Slug ตรงกับ role ของ persona; การคลิกลิงก์เปิดมุมมองต่อ persona

- [Product Administrator](./03-user-flow-product-admin.md) — เจ้าของแคตตาล็อก สร้างและดูแลสินค้า หมวดหมู่ หมวดหมู่ย่อย กลุ่มสินค้า หน่วย ตั้งค่า conversion factor, คุณสมบัติ (ผ่าน JSON `info`), location mapping (`tb_product_location`), vendor mapping (`tb_product_tb_vendor`) รัน import / export จัดการวงจรชีวิตของสินค้า (เปิดใช้ ปลดประจำการ ลบ) Persona ที่กว้าง — surface ส่วนใหญ่ของโมดูลอยู่ใน flow ของพวกเขา
- [Purchaser](./03-user-flow-purchaser.md) — ค้นหาสินค้าเพื่อจัดทำ PR และ PO Read-only consumer อ้างอิง `standard_cost` และต้นทุนรับล่าสุดที่ derive (`PRD_CALC_008`) สำหรับการอ้างอิงงบประมาณ-vs-จริง; ตรวจสอบการแปลงหน่วยสั่งซื้อ (`tb_unit_conversion` พร้อม `unit_type = order_unit`) และ vendor mapping (`tb_product_tb_vendor`) ก่อนเพิ่มบรรทัดไปยัง PR / PO; comment บน entry แคตตาล็อกที่เก่าหรือขาดเพื่อ route กลับไปยัง Product Administrator การเป็นเจ้าของวงจรชีวิตของพวกเขาคือไม่มี — พวกเขาอ่าน
- [Store Keeper](./03-user-flow-store-keeper.md) — ค้นหาสินค้าระหว่างการรับ การหยิบ การโอน การนับ Read-only consumer สแกนบาร์โค้ด (`tb_product.barcode`) สำหรับการระบุที่รวดเร็ว; อ้างอิงนโยบายสต๊อกต่อ location (`tb_product_location.min_qty` / `max_qty` / `par_qty`) และโน้ตการจัดการต่อสินค้า (คำแนะนำการจัดเก็บ อายุการเก็บรักษาจาก JSON `tb_product.info`) การเป็นเจ้าของวงจรชีวิตของพวกเขาก็คือไม่มี — พวกเขาอ่านและ comment

## 4. Handoff ข้าม Persona

ตารางด้านล่างจับช่วงเวลาที่งาน product ย้ายจากความรับผิดชอบของ persona หนึ่งไปยังอีกตัว เพราะ Purchaser และ Store Keeper เป็น read-only handoff ส่วนใหญ่เป็น unidirectional — Product Administrator ผลักสถานะแคตตาล็อกไปยังผู้บริโภค และผู้บริโภคบางครั้งดึง update กลับผ่านช่อง comment / feedback

| จาก persona | Trigger | ไป persona | สถานะระบบที่ handoff |
| ------------ | ------- | ---------- | ----------------------- |
| Product Administrator | สินค้าใหม่สร้างและ `active`; การจำแนก หน่วย การแปลง location mapping vendor mapping ตั้งค่าแล้ว | Purchaser, Store Keeper | `tb_product.product_status_type = active`, `is_active = true` Picker บนทุกโมดูลปลายน้ำแสดงสินค้าใหม่ทันที ไม่มีการแจ้งเตือนชัดเจน — picker อ่านเมื่อต้องการ |
| Product Administrator | `standard_cost` ของสินค้า update เกินเกณฑ์ SoD ของ tenant | Cost Controller / Finance (ผ่าน SoD gate `PRD_AUTH_012`) | Activity log บันทึกการเปลี่ยน ถ้า workflow ต้องการการอนุมัติชัดเจน การเปลี่ยนอาจถูก stage (ธรรมเนียม application) จนกว่า Cost Controller / Finance รับทราบ — สำหรับ installation ที่ไม่มี hard approval workflow การเปลี่ยนเป็นทันทีและ audit log เป็นการควบคุมแบบ soft |
| Product Administrator | สินค้าถูกปิดใช้ | Purchaser, Store Keeper | Picker filter สินค้าออกจาก default เอกสารใหม่ บรรทัดที่มีอยู่บนเอกสาร active ยังคงถูกต้อง การอ้างอิงของสูตร (ถ้ามี) ได้รับ recipe-review flag ถ้าการปิดใช้ถูก override ตาม `PRD_LIFE_002` |
| Purchaser | พบ entry แคตตาล็อกที่เก่าหรือขาดขณะจัดทำ PR / PO | Product Administrator | Purchaser post comment (`tb_product_comment`) บนสินค้าที่ได้รับผลกระทบ (หรือสำหรับสินค้าที่ขาด post "ขอสินค้าใหม่" ผ่าน comment บนสินค้าที่ใกล้ที่สุดที่มีอยู่หรือผ่านช่องคำขอแยก) Product Administrator หยิบ comment ตรวจสอบ update master หรือสร้างสินค้าใหม่ ตอบบน thread comment |
| Store Keeper | Barcode ไม่ตรงระหว่างการรับหรือการนับ (บาร์โค้ดที่สแกน resolve เป็นสินค้าผิด หรือ resolve ไม่ได้เลย) | Product Administrator | Store Keeper post comment บนสินค้าที่ได้รับผลกระทบด้วยบาร์โค้ดที่สแกนและฉลากสินค้าทางกายภาพ Product Administrator validate รายงาน (โดยทั่วไปโดยตรวจสอบ pricelist ของผู้ขายหรือ GRN) และ update `tb_product.barcode` Store Keeper สแกนใหม่เพื่อยืนยัน |
| Store Keeper | นโยบายสต๊อกต่อ location ต้องปรับ (min / max / par / reorder รู้สึกผิดสำหรับ location) | Inventory Controller (ตาม [[inventory/02-business-rules]] `INV_AUTH_004`) | Store Keeper post comment บนสินค้าหรือบน `tb_product_location` (ผ่าน tab location-policy ของสินค้า) Inventory Controller — **ไม่ใช่** Product Administrator — เป็นเจ้าของการแก้ไขนโยบายเติมสต๊อก ดังนั้น routing ไปที่ inventory Product Administrator อาจมีส่วนร่วมถ้าต้องการการเปลี่ยนเชิงโครงสร้างใน location-mapping เอง (เช่นการเพิ่ม location ใหม่ให้สินค้า) |
| Product Administrator | งาน bulk import เสร็จ | Product Administrator (ตัวเอง — review error report) | `created_by_id` ของ import job คือ Product Administrator; error report ดาวน์โหลดได้ ไม่มี handoff ภายนอก — Administrator iterate import จนสำเร็จ |
| System Administrator | การตั้งค่า RBAC role สำหรับโมดูล product ถูกเปลี่ยน | Persona ทั้งหมด | ขอบเขต persona อาจเลื่อน (เช่น approver role เพิ่มเติมเพิ่มเข้ากับเกณฑ์ SoD ตาม `PRD_AUTH_012`) ไม่มีการเปลี่ยนสถานะธุรกรรม; กฎใหม่ใช้ prospectively |
| Auditor | การ query audit เสร็จ | (ไม่มี action ปลายน้ำ) | Read-only handoff — Auditor บริโภคสถานะ product master ประวัติ comment และ activity log โดยไม่เขียนกลับ |

## 5. แหล่งอ้างอิง

- `../carmen/docs/product-management/PROD-PRD.md` — PRD หลักอธิบายชุด persona ของ product-management (Product Manager, Category Manager, Inventory Manager, Finance Team, Operations Team, System Administrator, Sustainability Officer) wiki นี้รวบ persona set ของ carmen/docs เป็น persona เชิงปฏิบัติการสามตัว (Product Administrator, Purchaser, Store Keeper) ที่ match กับ reality ของผู้ใช้ ERP โรงแรม — ดู Section 3
- `../carmen/docs/product-management/product-master-prd.md` — PRD ที่ยึด UI อธิบาย Product List page, Product Detail page (พร้อม tab สำหรับ header, attribute, unit, conversion, store/location assignment, latest purchase, activity log) และ data model หลังแต่ละ tab user-flow narrative ในไฟล์ต่อ persona map ตรงกับ surface UI เหล่านี้
- Sibling: [01-data-model.md](./01-data-model.md) — canonical `enum_product_status_type` (สองค่า `active | inactive` ไม่ใช่สาม) และ `enum_unit_type` (`order_unit | ingredient_unit`); รูปทรงห่วงโซ่การจำแนก (สามระดับ ไม่ใช่ห้า); ความแตกต่างกับ carmen/docs ที่กำหนดกรอบ "ไม่มีสถานะ `discontinued`" ที่นี่
- Sibling: [02-business-rules.md](./02-business-rules.md) — validation (`PRD_VAL_*`), calculation / inheritance (`PRD_CALC_*`), authorization (`PRD_AUTH_*`), lifecycle (`PRD_LIFE_*`) และกฎข้ามโมดูล (`PRD_XMOD_*`) ที่อ้างโดยทุกการเปลี่ยนใน Section 2
- โมดูลที่เกี่ยวข้อง: [[inventory]] (ผู้บริโภคของ `product_id` บนทุกธุรกรรม; in-use guard สำหรับการลบสินค้า), [[costing]] (`PRD_XMOD_003` — แหล่ง `standard_cost`, วิธี FIFO/WA อยู่บน business-unit ไม่ใช่สินค้า), [[good-receive-note]] (ผู้บริโภค; ค่าความคลาดเคลื่อน gate variance การรับ), [[store-requisition]] (ผู้บริโภค; product–location mapping ขับเคลื่อนการกำหนดขนาด par-level), [[purchase-request]] / [[purchase-order]] (ผู้บริโภค; การแปลงหน่วยสั่งซื้อ), [[vendor-pricelist]] (ผู้บริโภค; join product–vendor), [[recipe]] (ผู้บริโภค; สินค้าเป็นวัตถุดิบ — filter `is_used_in_recipe` บน picker)
