---
title: สินค้า (Product) — User Flow — Product Administrator
description: flow ของ Product Administrator ในโมดูลสินค้า — CRUD เต็มบนข้อมูลหลัก การจำแนก หน่วย การแปลง location และ vendor mapping วงจรชีวิต และ bulk import/export
published: true
date: 2026-05-17T12:00:00.000Z
tags: product, user-flow, product-admin, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:30:00.000Z
---

# สินค้า (Product) — User Flow — Product Administrator

> **At a Glance**
> **Persona:** Product Administrator &nbsp;·&nbsp; **โมดูล:** [[product]] &nbsp;·&nbsp; **ขั้นตอน workflow:** สร้าง / แก้ `tb_product` (`active`) &nbsp;·&nbsp; ห่วงโซ่การจำแนก (category / sub-category / item-group) &nbsp;·&nbsp; หน่วยและการแปลง &nbsp;·&nbsp; location และ vendor mapping &nbsp;·&nbsp; bulk import / export &nbsp;·&nbsp; ปิดใช้ / re-activate / soft-delete / restore &nbsp;·&nbsp; ตอบ comment ขาเข้า &nbsp;·&nbsp; **สิทธิ์สำคัญ:** CRUD เต็มบนข้อมูลหลัก (`PRD_AUTH_001` / `PRD_AUTH_003` / `PRD_AUTH_004`); SoD บนการเปลี่ยน `standard_cost` เกินเกณฑ์ tenant (`PRD_AUTH_012` — Cost Controller / Finance signature ที่สอง)
> **persona นี้ทำอะไร:** เป็นเจ้าของแคตตาล็อก — สร้าง / ดูแลสินค้า การจำแนก หน่วย mapping และรันวงจรชีวิตของ record สินค้า

## 1. บทบาทในโมดูลนี้

persona **Product Administrator** เป็น **เจ้าของแคตตาล็อก** ในโมดูล product พวกเขามี **อำนาจ CRUD เต็ม** บนทุก surface ข้อมูลหลัก: แถว `tb_product` (สร้าง แก้ ปิดใช้ soft-delete restore) ห่วงโซ่การจำแนก (`tb_product_category → tb_product_sub_category → tb_product_item_group`) นิยามหน่วย (`tb_unit`) conversion factor (`tb_unit_conversion` สำหรับขอบเขตทั้ง `order_unit` และ `ingredient_unit`) นโยบายสต๊อกต่อ location mapping (`tb_product_location`) และ vendor mapping (`tb_product_tb_vendor`) พวกเขารัน bulk import และ export สำหรับ surface ของสินค้า / หมวดหมู่ / หน่วย / conversion จัดการวงจรชีวิตของสินค้า (`active ↔ inactive ↔ soft-deleted`) และตอบ comment ขาเข้าจาก Purchaser (feedback แคตตาล็อกเก่า ขอสินค้าใหม่) และ Store Keeper (barcode ไม่ตรง การ update โน้ตการจัดการ) Product Administrator **ไม่** อนุมัติเอกสารธุรกรรม (PR / PO / GRN / SR) **ไม่** แก้ค่านโยบายสต๊อกต่อ location สำหรับการเติมสต๊อก (`tb_product_location.min_qty / max_qty / re_order_qty / par_qty` เขียนได้ทางเทคนิคโดย Product Administrator แต่อำนาจ **นโยบาย** อยู่ที่ Inventory Controller ตาม [[inventory/02-business-rules]] `INV_AUTH_004` — ในทางปฏิบัติ Product Administrator สร้างแถว `tb_product_location` เพื่อเปิด location สำหรับสินค้า และ Inventory Controller fine-tune ค่านโยบาย) และ **ไม่** มีส่วนร่วมในการปิด period หรือการกระทบยอดทางการเงิน Segregation of duties (`PRD_AUTH_012`) จำกัด Product Administrator จากการอนุมัติการเปลี่ยน `standard_cost` ของตนเองเกินเกณฑ์ SoD ของ tenant — Cost Controller / Finance คือ signature ที่สอง

## 2. Entry Point และ Primary Flow

**Entry point:** เส้นทางหลักห้าทางสู่งานประจำวันของ Product Administrator — หนึ่งสำหรับแต่ละ surface หลักที่พวกเขาเป็นเจ้าของ

- **Product Management → Products → New** — สร้างสินค้าใหม่เดี่ยว (ปกติสำหรับ SKU ใหม่หรือการเปิดตัวเมนู)
- **Product Management → Products → Import** — bulk import สำหรับการโหลดแคตตาล็อกเริ่มต้น การ roll-out หลาย property หรือการ update ชุดใหญ่จาก supplier feed
- **Product Management → Categories** — สร้างหรือแก้ node การจำแนก (category, sub-category, item-group) การเปลี่ยน cascading-default กระจายไปยังลูกที่การอ่านครั้งต่อไปตาม `PRD_CALC_002` / `PRD_CALC_003`
- **Product Management → Units** — สร้างหน่วยหรือนิยามการแปลงหน่วย จำเป็นก่อนที่สินค้าใด ๆ ที่ใช้หน่วยนั้นจะสามารถถูกสร้างหรือแก้
- **คิว Comment (ต่อสินค้าหรือ global)** — review และตอบ feedback ขาเข้าของ Purchaser / Store Keeper บนแคตตาล็อก

**Primary flow (สร้างสินค้าใหม่เดี่ยว 10 ขั้นตอน — เป็นตัวอย่างของรูปแบบ full-CRUD):**

1. **ตรวจสอบเงื่อนไขเบื้องต้น** ก่อนสร้างสินค้า ยืนยันห่วงโซ่การจำแนก (item-group เป้าหมาย sub-category parent ของมัน และ category ระดับบนสุด) มีอยู่และ `active` ถ้าไม่ สร้าง node หมวดหมู่ก่อน ยืนยันหน่วยฐานคลัง (`tb_unit`) มีอยู่และ conversion factor หน่วยสั่งซื้อ / หน่วยสูตรอาหารจะนิยามได้ ยืนยัน tax profile ตั้งบนอย่างน้อยหนึ่งระดับของห่วงโซ่การจำแนก (ตามการสืบทอด `PRD_CALC_002`) — มิฉะนั้นสินค้าจะสืบทอดอัตราภาษีที่มีผล 0%
2. **เปิด Products → New** Product Management → Products → New form เปิดที่ `tb_product` create mode พร้อมฟิลด์ว่างและ preview การสืบทอดปิด
3. **กรอก code และ name (และ local name)** `code` ต้องไม่ซ้ำภายใน `(code, name, deleted_at)` ตาม `PRD_VAL_001`; การตรวจสอบ blur-time ของ form เตือนความขัดแย้งก่อน submit `name` คือชื่อแสดงผลภาษาอังกฤษ / หลัก; `local_name` คือการแสดงผลท้องถิ่น (ไทย ฯลฯ) Description อิสระ
4. **เลือกหน่วยคลังฐาน** `inventory_unit_id` อ้างอิง `tb_unit` ที่ active สิ่งนี้ขับเคลื่อนทุกการคำนวณปลายน้ำ (balance, cost, valuation) และ **ไม่สามารถเปลี่ยนได้เมื่อสินค้ามีประวัติคลัง** ตาม `PRD_VAL_003` ดังนั้นทางเลือกมีผลกระทบ — คำเตือนแสดงบน form
5. **กำหนดการจำแนก** เลือก `tb_product_item_group` ที่เป็นใบไม้ form render เส้นทางการจำแนกที่ resolve ("Beverages / Hot / Coffee Beans") และแสดง tax profile ที่สืบทอดและค่าความคลาดเคลื่อนตาม `PRD_CALC_002` / `PRD_CALC_003` Product Administrator อาจ override ค่าที่สืบทอดที่ระดับสินค้าโดยกรอกค่าเฉพาะบน header ของสินค้า
6. **ตั้ง flag ของสินค้า** `is_used_in_recipe` และ `is_sold_directly` default ตามการสืบทอดของการจำแนก (`PRD_CALC_004`); override ถ้าสินค้าเฉพาะเบี่ยงจากธรรมเนียมหมวดหมู่ `barcode` และ `sku` เป็นทางเลือก; ถ้าตั้ง ความไม่ซ้ำของ `barcode` บังคับใช้ตาม `PRD_VAL_005`
7. **ตั้งฟิลด์ cost reference** `standard_cost` คือต้นทุน reference / มาตรฐานในหน่วยคลังฐาน (ตาม `PRD_VAL_007` ต้อง ≥ 0) ใช้โดยวิธี count-costing `standard` และโดย recipe baselining `price_deviation_limit` และ `qty_deviation_limit` ถูก bound `[0, 100]` ค่าความคลาดเคลื่อนเป็นเปอร์เซ็นต์ (ตาม `PRD_VAL_006`) และสืบทอดจากห่วงโซ่การจำแนกถ้าเป็นศูนย์; override ถ้าจำเป็น **ค่า standard-cost เกินเกณฑ์อาจ route ไปยัง Cost Controller สำหรับการอนุมัติตาม `PRD_AUTH_012`** — form ระบุสิ่งนี้ด้วยประกาศ
8. **นิยามการแปลงหน่วย** Conversion → New สำหรับแต่ละหน่วยสั่งซื้อ (`unit_type = order_unit` เช่น `1 CASE = 12 EACH`) และแต่ละหน่วยสูตรอาหาร (`unit_type = ingredient_unit` เช่น `1 TBSP = 15 ML`) ที่สินค้าต้องการ ตาม `PRD_VAL_010` แต่ละแถวมี qty บวกทั้งสองด้านและ from/to unit ต่างกัน; ตาม `PRD_VAL_011` ความสอดคล้องสองทิศทาง validate ข้ามชุด flag "default" (`is_default`) เลือก conversion ที่แสดงก่อนบน picker PR/PO/recipe
9. **ตั้งค่า location และ vendor mapping**
   - **Location mapping (`tb_product_location`):** ต่อ location ตั้ง `min_qty` / `max_qty` / `re_order_qty` / `par_qty` ตาม constraint `PRD_VAL_012` (max ≥ min ทั้งหมด ≥ 0) Product Administrator สร้างแถวเพื่อ **เปิดใช้** สินค้าที่ location; **การ fine-tune นโยบาย** (ค่าตัวเลขเฉพาะ) โดยทั่วไปมอบหมายให้ Inventory Controller ตาม `PRD_AUTH_008` ค่าศูนย์หมายถึง "ไม่ได้ตั้งค่า" และ location จะไม่แสดง alert การเติมสต๊อกสำหรับสินค้า
   - **Vendor mapping (`tb_product_tb_vendor`):** เลือก vendor หนึ่งหรือหลายรายที่ supply สินค้า; กรอก `vendor_product_code` และ `vendor_product_name` สำหรับ cross-reference บน PO และ pricelist ตาม `PRD_VAL_013` แต่ละคู่ (`vendor_id`, `product_id`) ไม่ซ้ำ การ map คือสิ่งที่ทำให้สินค้าปรากฏบน picker ของ vendor-pricelist และ vendor-defaulting ของ PR / PO
10. **Save และเปิดใช้** Submit Validation รันตาม `PRD_VAL_*`; แถวที่ผ่านเขียน `tb_product` ด้วย `product_status_type = active`, `is_active = true` พร้อมแถว `tb_unit_conversion`, `tb_product_location`, `tb_product_tb_vendor` ที่เกี่ยวข้อง Activity log บันทึก create ตาม `PRD_LIFE_001` สินค้าปรากฏทันทีบนทุก picker ปลายน้ำ (ตาม `PRD_AUTH_009`); ไม่มีการแจ้งเตือนปล่อย (picker อ่านเมื่อต้องการ)

flow **bulk-import** คือเส้นทาง create หลักสำหรับการโหลดแคตตาล็อกเริ่มต้น (การเปิดหลาย property supplier feed ใหญ่) Product Administrator upload Excel / CSV ด้วยรูปทรงคอลัมน์เดียวกัน รัน **dry-run mode** ก่อนเพื่อแสดง error validation ต่อแถว download error report fix source file รัน dry-run ใหม่จนสะอาด แล้วรัน **strict-mode commit** ที่ insert / update แถวใน transaction เดียว (หรือ partial-success mode, default, ที่แถวที่ผ่าน commit และแถวที่ fail ถูกรายงาน) Bulk import subject ต่อกฎ validation เดียวกันต่อแถว

flow **classification-change** (สร้างหรือแก้ category / sub-category / item-group) ตามขั้นตอน 2–10 แต่ที่ระดับต้นไม้ที่เกี่ยวข้อง ผลกระทบ cascading-default preview ก่อน save: การเปลี่ยน `tax_profile_id` ของ category เช่นกัน แสดงว่ามี sub-category / item-group / สินค้ากี่ตัวจะสืบทอดค่าใหม่ ตาม `PRD_LIFE_010` การเปลี่ยนเป็น **prospective** — เอกสารเปิดที่ snapshot tax-profile เก่าเก็บ snapshot

flow **lifecycle-transition** (เปิดใช้ ปิดใช้ soft-delete restore) ตาม state diagram ใน [03-user-flow.md](./03-user-flow.md) Section 2 Guard หลักคือ **การตรวจสอบ in-use**:

- **ปิดใช้** (`active → inactive`) — soft-block ถ้าถูกอ้างอิงโดยสูตรที่ publish (override ด้วยข้อความเหตุผล) Hard-block ถ้าบรรทัด PR / PO / SR เปิดใด ๆ อ้างอิงสินค้า
- **Soft-delete** (`active | inactive → soft-deleted`) — hard-block ถ้าบรรทัดเอกสารใด ๆ อ้างอิงสินค้า (รวมประวัติที่เสร็จ) ถ้าสูตรที่ไม่ถูกลบใด ๆ อ้างอิงมัน หรือถ้า on-hand ปัจจุบันที่ location ใด ๆ ไม่เป็นศูนย์ (derive ตาม `PRD_CALC_009`) สินค้าต้องถูก **drain** (คลังถูก write off / consume / transfer) ก่อนการลบ
- **Restore** (`soft-deleted → active`) — ปฏิเสธถ้า `(code, name)` ถูก re-use โดยสินค้า live ในระหว่างนั้น

## 3. Decision Branch

- **สืบทอด vs override ที่ระดับการจำแนก** ธรรมเนียม default คือตั้ง tax profile และค่าความคลาดเคลื่อนที่ระดับ **category** และให้ item-group / สินค้าสืบทอด การ override ที่ระดับสินค้าสำรองไว้สำหรับข้อยกเว้นจริง (เช่นสินค้าเฉพาะมีอัตราภาษีต่างเนื่องจากกฎระเบียบท้องถิ่น หรือมี tolerance ราคาเข้มกว่าเนื่องจากปัญหาคุณภาพ vendor) form แสดงค่าที่สืบทอดในรูปแบบที่ grey-out; การแตะ override ทำให้พวกเขาแก้ได้
- **หน่วยใหม่ vs หน่วยที่มีอยู่** เมื่อสินค้าใหม่ต้องการหน่วยที่ไม่มีใน `tb_unit` (เช่น `PUNNET` สำหรับ SKU ผลผลิตใหม่) สร้างหน่วยก่อน (Units → New) แล้วสร้าง conversion factor ไปยังหน่วยคลังฐาน หลีกเลี่ยงหน่วย one-off ที่จะไม่ถูก reuse — ธรรมเนียมคือเก็บ `tb_unit` ให้บางและ reuse หน่วยมาตรฐาน (KG, LITRE, EACH, CASE, DOZEN, BOTTLE, BAG)
- **การแปลง order-unit vs ingredient-unit** ขอบเขตทั้งสองแชร์ตาราง `tb_unit_conversion`; แยกแยะผ่าน `enum_unit_type` การแปลง Order-unit อ่านโดย procurement / receiving / pricelist (การแปล qty บรรทัด PR / PO / GRN → หน่วยฐาน); การแปลง ingredient-unit อ่านโดย recipe (qty วัตถุดิบสูตร → หน่วยฐานสำหรับ theoretical consumption) การแปลงทางกายภาพเดียวกัน (`1 CASE = 12 EACH`) อาจมีเป็น **ทั้งสอง** แถว `order_unit` และแถว `ingredient_unit` ถ้าหน่วยเดียวกันใช้ในทั้งสองบริบท — นั่นจงใจเพื่อให้ namespace ทั้งสองเป็นอิสระ
- **Soft-delete vs hard-disable** flag สองตัวบรรลุผลลัพธ์คล้ายแต่ต่างกัน (ตาม `PRD_LIFE_005`):
  - `product_status_type = inactive` — สินค้าถูกลบจาก picker ธุรกรรมใหม่; admin ยังเห็น; **reversible** ผ่าน re-activation ใช้สำหรับ "ไม่ใช้ชั่วคราว" (item ตามฤดูกาลออกจากเมนู recall รอการเปิดตัวใหม่)
  - `is_active = false` — สินค้าซ่อนทุกที่รวม admin view; reversible โดยตั้ง flag ใหม่ ใช้สำหรับ "ควรมองไม่เห็นทุกคน" โดยไม่ soft-delete (เช่น compliance hold)
  - `soft-delete` (`deleted_at` ตั้ง) — terminal ในการใช้งานปกติ; เฉพาะ Auditor เห็นแถวที่ soft-deleted ใช้เมื่อสินค้าเลิกใช้จริงและ `(code, name)` ควรใช้งานได้ใหม่
- **การแก้ standard-cost route สำหรับการอนุมัติเกินเกณฑ์** ตาม `PRD_AUTH_012` การเปลี่ยน `standard_cost` เกินเกณฑ์ SoD ของ tenant (โดยทั่วไป 10–20% การเคลื่อนไหว ตั้งค่าได้) route การ update ไปยัง Cost Controller / Finance review ใต้เกณฑ์ การแก้เป็นทันที form แสดง threshold และการตัดสินใจ routing ก่อน submit
- **Bulk import — dry-run ก่อน** รัน dry-run ก่อน strict-commit เสมอสำหรับการ import ที่ไม่เล็ก dry-run ผลิตการ validate report โดยไม่เขียนแถว; iterate บน source file จนสะอาด สำหรับ roll-out หลาย property dry-run เป็นบังคับโดยธรรมเนียม
- **ผลกระทบการจัดระเบียบการจำแนก** การย้ายสินค้าระหว่าง item-group (เปลี่ยน `product_item_group_id`) update default ที่สืบทอด prospectively (`PRD_LIFE_010`) เอกสารเปิดเก็บค่าที่ snapshot Product Administrator review preview ผลกระทบก่อน commit — สำหรับสินค้าบนเอกสาร active หลายตัวนี่หายากและรบกวน
- **การ escalation in-use guard** เมื่อการลบถูก hard-block โดย in-use guard Product Administrator ประสานกับเจ้าของเอกสาร (Purchaser สำหรับ PR / PO; Store Keeper สำหรับ SR / count; Chef สำหรับสูตร) เพื่ออย่างใดอย่างหนึ่งยกเลิก / void เอกสาร drain คลัง หรือยอมรับว่าสินค้าไม่สามารถลบได้ในขณะนี้ ไม่มีเส้นทาง override — guard เป็น absolute (`PRD_LIFE_004`)

## 4. Exit Point / Handoff

การมีส่วนร่วมของ Product Administrator บน surface แคตตาล็อกใดจบที่หนึ่งใน boundary เหล่านี้:

- **สินค้าสร้างและ active — handoff ไปยังผู้บริโภค** สินค้าใหม่ปรากฏบนทุก picker ปลายน้ำ; Purchaser และ Store Keeper เห็นทันที ไม่มีการแจ้งเตือนปล่อย; picker อ่านเมื่อต้องการ Product Administrator อาจ post comment "สินค้าใหม่พร้อมใช้" บนสินค้าหรือผ่านช่องการสื่อสารระดับ tenant เพื่อ flag ผู้บริโภคถ้าการเปิดตัวมีนัยสำคัญเชิงปฏิบัติการ
- **การเปลี่ยน standard-cost route สำหรับการอนุมัติ Cost Controller / Finance** การแก้เกินเกณฑ์ stage ใน activity log ตาม `PRD_AUTH_012`; Product Administrator รอ signature ที่สอง ในการอนุมัติ การเปลี่ยนเป็นสุดท้าย; ในการปฏิเสธ `standard_cost` เดิม restore และ Administrator iterate
- **การเปลี่ยนการจำแนก commit แล้ว — การกระจาย prospective** การกระจาย cascading-default เกิดที่เวลา next-read บนผู้บริโภคปลายน้ำแต่ละราย (line save ของ PR อ่าน tax profile ใหม่ที่มีผลตาม `PRD_CALC_002`); งานของ Product Administrator เสร็จที่ commit เอกสารเปิดที่ snapshot ค่าเก่าไม่ถูกแก้ retroactively
- **Soft-delete commit แล้ว — terminal** เมื่อ `deleted_at` ตั้ง สินค้าถูกลบจากทุกมุมมอง live Audit log เก็บ event การลบ; restore เป็นไปได้แต่โดยทั่วไปไม่ใช้ การมีส่วนร่วมของ Product Administrator จบ
- **Comment ขาเข้า resolve แล้ว** เมื่อ comment ของ Purchaser หรือ Store Keeper ได้รับ Product Administrator สอบสวน ทำ action ที่เหมาะสม (update master สร้างสินค้าใหม่ fix barcode ปรับ location-mapping) และตอบบน thread comment การ resolve ปิด thread
- **Bulk import commit แล้ว** `created_by_id` ของ import job บันทึก Administrator; error report ครอบคลุมแถวที่ fail การ re-run iterate จน source file สะอาด; commit สุดท้ายจบการมีส่วนร่วมของ Administrator
- **Lifecycle handoff ไปยัง Inventory Controller (สำหรับนโยบายการเติมสต๊อก)** — Product Administrator สร้าง `tb_product_location` เพื่อเปิด location สำหรับสินค้า; Inventory Controller เอามาตั้งนโยบาย min / max / par / reorder ตาม `INV_AUTH_004` การ map บริสุทธิ์ (location เปิดหรือไม่) อยู่กับ Product Administrator; ตัวเลขนโยบายไปที่ Inventory Controller

## 5. แหล่งอ้างอิง

- Parent overview: [03-user-flow.md](./03-user-flow.md) — canonical state machine ของ record สินค้า (Section 2) ที่เส้นทางของ persona นี้ traverse และตาราง handoff ข้าม persona ที่ anchor boundary Product Administrator → Cost Controller / Finance / Inventory Controller
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — persona ผู้บริโภคปลายน้ำที่อ่านแคตตาล็อกสำหรับการจัดทำ PR / PO
- Sibling: [03-user-flow-store-keeper.md](./03-user-flow-store-keeper.md) — persona ผู้บริโภคปลายน้ำที่อ่านแคตตาล็อก (barcode scan การอ้างอิงนโยบาย location) ระหว่างการรับ / หยิบ / นับ
- Sibling: [01-data-model.md](./01-data-model.md) — รูปทรง canonical `tb_product` (ขั้นตอน 3–7 ของ primary flow), ห่วงโซ่การจำแนก (`tb_product_category` / `tb_product_sub_category` / `tb_product_item_group`, ขั้นตอน 5), รูปทรง `tb_unit` และ `tb_unit_conversion` (ขั้นตอน 4 และ 8), `tb_product_location` / `tb_product_tb_vendor` (ขั้นตอน 9) และ `enum_product_status_type` (การเปลี่ยนวงจรชีวิต)
- Sibling: [02-business-rules.md](./02-business-rules.md) — กฎ validation (`PRD_VAL_001`–`PRD_VAL_018`) อ้างในขั้นตอน 3–10 ของ primary flow; กฎ calculation / inheritance (`PRD_CALC_001`–`PRD_CALC_010`) อ้างในขั้นตอน 1 (ตรวจสอบเงื่อนไขเบื้องต้น) และขั้นตอน 5 (การสืบทอดการจำแนก); กฎ authorization (`PRD_AUTH_001`–`PRD_AUTH_004`, `PRD_AUTH_012`) gate อำนาจของ Product Administrator; กฎ lifecycle (`PRD_LIFE_001`–`PRD_LIFE_010`) ควบคุมการเปลี่ยนสถานะที่ Section 1 ของหน้านี้อธิบาย; กฎข้ามโมดูล (`PRD_XMOD_001`–`PRD_XMOD_012`) นิยามวิธีที่แคตตาล็อกเชื่อมกับผู้บริโภค
- โมดูลที่เกี่ยวข้อง: [[inventory]] — การ map `tb_product_location` เปิดสินค้าที่ location; ตัวเลขนโยบายการเติมสต๊อกเป็นของ Inventory Controller (`INV_AUTH_004`) On-hand qty derive จาก cost-layer ledger (`PRD_CALC_009`) และแสดงบน tab location ของมุมมองรายละเอียดสินค้า
- ที่เกี่ยวข้อง: [[costing]] — `tb_product.standard_cost` คือแหล่งของ reference-cost; วิธี FIFO / WA cost-pick อยู่ที่ `tb_business_unit.calculation_method` ไม่ใช่บนสินค้า (ตาม [[product/01-data-model]] § 5 รายการ 7) การเปลี่ยน standard-cost เกินเกณฑ์ SoD route สำหรับการอนุมัติ Cost Controller / Finance (`PRD_AUTH_012`)
- ที่เกี่ยวข้อง: [[vendor-pricelist]] — การ map `tb_product_tb_vendor` ทำให้สินค้าปรากฏบน vendor pricelist; บรรทัด pricelist อ้างอิง `tb_product` ผ่าน `product_id`
- ที่เกี่ยวข้อง: [[recipe]] — สูตรที่ publish ที่อ้างอิงสินค้าบล็อกการปิดใช้ตาม `PRD_LIFE_002` (soft-block, override มี) และบล็อก soft-delete ตาม `PRD_LIFE_004` (hard-block, ไม่มี override)
- ที่เกี่ยวข้อง: [[purchase-request]] / [[purchase-order]] / [[good-receive-note]] / [[store-requisition]] — เอกสารเปิดที่อ้างอิงสินค้าบล็อกการปิดใช้ / ลบตาม in-use guard
