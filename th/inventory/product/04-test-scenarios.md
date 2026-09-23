---
title: สินค้า (Product) — Test Scenarios
description: test case ตาม persona, scenario ข้าม persona และ mapping ไปยัง E2E สำหรับ product
published: true
date: '2026-09-23T01:30:00.000Z'
tags: product, test-scenarios, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:30:00.000Z
---

# สินค้า (Product) — Test Scenarios

> **At a Glance**
> **โมดูล:** [product](/th/inventory/product) &nbsp;·&nbsp; **scenario รวม:** ~17 ข้าม persona + ~127 ต่อ persona &nbsp;·&nbsp; **Persona ที่ครอบคลุม:** Product Administrator, Purchaser, Store Keeper
> **ลำดับการรัน:** การตั้งค่า Audit / Config → happy path ของ persona หลัก → scenario ข้าม persona
> **drill-down ของแต่ละ persona อยู่ที่ `04-test-scenarios-<role>.md`**

> **ความครอบคลุมที่รันได้จริง (2026-09-22):** รีโป e2e **ไม่มี `100-product.spec.ts`** — `/product-management/product` เป็นแถวแบบ catalog เท่านั้น (`📄 catalog`) ใน `../carmen-inventory-frontend-e2e/docs/test-cases/COVERAGE.md:148` หนุนด้วย `docs/test-cases/100-product.md` (52 กรณี ตรวจสอบซ้ำกับฟอร์ม React เมื่อ 2026-09-20) หน้าจอข้างเคียงมี spec: `tests/101-product-category.spec.ts` (23 กรณี; gap report `docs/test-cases/gaps/101-product-category-gap.md` ยังไม่ครอบคลุม 39) และ `tests/044-eco.spec.ts` (19 กรณี; `gaps/044-eco-gap.md` ยังไม่ครอบคลุม 29) หน้านี้ไม่ได้ mirror catalog เหล่านั้น

## 1. ภาพรวม

หน้านี้เป็น **จุดเข้าภาพรวม** สำหรับชุด test-scenario ของโมดูล `product` รวบรวมการครอบคลุมตาม persona สามตัว (Product Administrator, Purchaser, Store Keeper) และแสดง scenario ข้าม persona / integration ขอบเขตถูกกำหนดโดย **ลักษณะ master-data** ของโมดูล — ไม่มี workflow เอกสาร `doc_status` พร้อม gate draft / submit / approve ไม่มี event posting พร้อม journal-entry fan-out ไม่มีหน้าต่าง period-end Test scenario จึงรวมไปที่ **CRUD + lifecycle** สำหรับ Product Administrator (persona ที่กว้าง) และ **lookup + กฎด้าน read** สำหรับ Purchaser และ Store Keeper (persona ผู้บริโภคที่แคบ)

การครอบคลุม E2E สำหรับโมดูลนี้ **บางส่วนและทางอ้อม** Playwright spec ตรงคือ `101-product-category.spec.ts` (23 กรณี — browse ต้นไม้ บวก CRUD หมวดหมู่ / หมวดหมู่ย่อย / กลุ่มสินค้า ตาม `docs/user-stories/101-product-category.md`) และ `044-eco.spec.ts` (ข้อมูลหลัก eco-label ตอนนี้อยู่ใต้ `/product-management/eco`); การจัดการหน่วยถูกครอบคลุมจากฝั่ง Configuration โดย `020-unit.spec.ts` ยังคงไม่มี `100-product.spec.ts` ครอบคลุม CRUD ของสินค้า (catalog `docs/test-cases/100-product.md` 52 กรณีเป็นเอกสารเท่านั้น) และไม่มี spec ครอบคลุม location-policy / การกำหนดชั้นวาง การใช้งานส่วนใหญ่ของโมดูล product เป็นทางอ้อม — ทุก spec ของโมดูลธุรกรรม (PR, PO, GRN, SR, count, recipe, pricelist) บริโภค product picker และอ่านแถว `tb_product` ดังนั้น scenario ด้านผู้บริโภคถูก validate ผ่าน spec ต้นน้ำเหล่านั้น Surface CRUD ของ Product Administrator ส่วนใหญ่เป็น manual / planned testing Section 5 map การครอบคลุมที่เรามี

scenario ข้าม persona ใน Section 4 เป็นชั้น integration เหนือ suite ต่อ persona พวกเขาอธิบาย journey end-to-end ที่ข้าม boundary ของ handoff ที่บันทึกใน [03-user-flow.md](./03-user-flow.md) Section 4 — เช่น *Product Administrator สร้างสินค้าใหม่ → Purchaser พบบน PR picker → Store Keeper สแกนบาร์โค้ดระหว่างการรับ → Product Administrator update barcode mismatch ที่ flag ผ่าน comment* Section 5 map spec E2E กลับไปยัง journey เหล่านั้น; หมายเหตุว่า scenario ด้าน product หลายตัวถูก exercise ผ่าน spec โมดูลต้นน้ำเท่านั้น

## 2. Persona ในขอบเขต

- **Product Administrator**: เจ้าของแคตตาล็อกพร้อม CRUD เต็มบน `tb_product`, ห่วงโซ่การจำแนก, หน่วย, conversion, location mapping, vendor mapping และการเปลี่ยนวงจรชีวิต รัน bulk import / export Persona ที่กว้าง
- **Purchaser**: ผู้บริโภค read-only ที่ค้นหาสินค้าสำหรับการจัดทำ PR / PO อ้างอิง standard cost, ต้นทุนรับล่าสุด (derive), การแปลงหน่วย และ vendor mapping Post comment สำหรับ entry ที่เก่าหรือคำขอสินค้าใหม่ Persona ผู้บริโภคที่แคบที่ชั้น procurement
- **Store Keeper**: ผู้บริโภค read-only ที่สแกนบาร์โค้ดระหว่างการรับ / หยิบ / นับ และอ้างอิงนโยบายสต๊อกต่อ location และโน้ตการจัดการ Post comment สำหรับ barcode ไม่ตรงและปัญหาเชิงปฏิบัติการ Persona ผู้บริโภคที่แคบที่ floor เชิงปฏิบัติการ

## 3. ไฟล์ Test ของ Persona

- [Product Administrator scenarios](./04-test-scenarios-product-admin.md)
- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Store Keeper scenarios](./04-test-scenarios-store-keeper.md)

## 4. scenario ข้าม Persona / Handoff

ตารางด้านล่างเป็นชั้น integration แต่ละแถวคลุมอย่างน้อยหนึ่ง handoff จาก [03-user-flow.md](./03-user-flow.md) Section 4 และจบด้วยระบบในสถานะ steady "Personas in order" รายการ actor ในลำดับการ execute; "Pre-condition" จับสถานะที่ต้องการเพื่อเริ่ม; "Expected end state" anchor สถานะแคตตาล็อกและผลกระทบด้านผู้บริโภค

| # | Scenario | Persona ตามลำดับ | Pre-condition | สถานะสิ้นสุดที่คาดหวัง |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | สินค้าใหม่สร้างและพร้อมใช้สำหรับผู้บริโภคทันที | Product Administrator → Purchaser → Store Keeper | ห่วงโซ่การจำแนก (category → sub-category → item-group) มีอยู่; หน่วยคลังฐานมีอยู่; tax profile ตั้งบนอย่างน้อยหนึ่งระดับการจำแนก | แถว `tb_product` insert ด้วย `product_status_type = active`, `is_active = true` Order-unit conversion และ vendor mapping ตั้งค่าแล้ว Purchaser เห็นสินค้าบน PR picker ทันที; Store Keeper สแกนบาร์โค้ดระหว่างการรับและ resolve เป็นสินค้าใหม่ ไม่มีการแจ้งเตือนยิง; picker อ่านเมื่อต้องการ |
| 2 | Bulk import — dry-run, fix error, strict-mode commit | Product Administrator | — | **ทดสอบไม่ได้ — ไม่มี import อยู่จริง** (ยืนยัน 2026-09-22: ไม่มี route นำเข้าใน `config_products.controller.ts` ไม่มี Bruno request frontend มีแค่ export) เก็บไว้เป็น placeholder ที่มีหมายเลขเพื่อให้การอ้างอิงปลายน้ำยังคงเสถียร |
| 3 | Bulk import — partial-success mode | Product Administrator | — | **ทดสอบไม่ได้ — ไม่มี import อยู่จริง** (ดู Scenario 2) |
| 4 | การเปลี่ยน standard-cost เกินเกณฑ์ SoD route สำหรับการอนุมัติ | Product Administrator → Cost Controller / Finance | สินค้าที่ active; `standard_cost` ใหม่สูงกว่าปัจจุบัน 20% (เกินเกณฑ์ SoD ของ tenant) | การเปลี่ยน stage ใน activity log (หรือ hard-block ขึ้นอยู่กับการตั้งค่า workflow) ตาม `PRD_AUTH_012`; Cost Controller / Finance อนุมัติ การเปลี่ยน commit; activity log บันทึกทั้งผู้ submit และผู้อนุมัติ |
| 5 | ปิดใช้สินค้าถูกบล็อกโดยบรรทัด PR / PO เปิด | Product Administrator | สินค้า active; บรรทัด `tb_purchase_request_detail` เปิดหนึ่งบรรทัดที่ `doc_status = in_progress` อ้างอิงสินค้า | ปิดใช้ถูกปฏิเสธตาม `PRD_LIFE_002` ด้วย `"Product is referenced by 1 open PR line and cannot be deactivated."`; Product Administrator ประสานกับ Purchaser เพื่อยกเลิก / void PR (หรือรอการเสร็จ) หลังจาก PR ย้ายไปยัง `completed` / `cancelled` ลองใหม่สำเร็จ |
| 6 | ปิดใช้สินค้าที่ถูกอ้างอิงโดยสูตรที่ publish — soft-block พร้อม override | Product Administrator → Chef (เพื่อแจ้งให้ทราบ) | สินค้า active; สูตรที่ publish หนึ่งสูตรอ้างอิงเป็นวัตถุดิบ | ปิดใช้ soft-block ตาม `PRD_LIFE_002`; Product Administrator สามารถ override ด้วยข้อความเหตุผลใน activity log ใน override สูตรที่ได้รับผลกระทบถูก flag สำหรับ review อัตโนมัติ (Chef ได้รับการแจ้งเตือนตามโมดูล recipe) `product_status_type = inactive`; activity log บันทึก override + เหตุผล |
| 7 | Soft-delete โดยมี on-hand ไม่เป็นศูนย์ | Product Administrator → Store Keeper (เพื่อแจ้งให้ทราบ) | สินค้า inactive; on-hand ปัจจุบันที่ location หนึ่งคือ 25 หน่วย (derive ตาม `PRD_CALC_009`) | **design intent vs. พฤติกรรมจริง:** `PRD_LIFE_004` บอกให้ปฏิเสธ; `delete()` จริงไม่มี guard และ soft-delete **สำเร็จ** ทิ้ง 25 หน่วยของสินค้าที่ถูกลบไว้บน ledger (ยืนยัน 2026-09-22, [02-business-rules](/th/inventory/product/02-business-rules) § 5.1) test ที่เขียนวันนี้ต้องคาดหวังว่าสำเร็จและบันทึกยอดคงเหลือกำพร้าเป็น finding |
| 8 | Purchaser flag entry แคตตาล็อกเก่าผ่าน comment | Purchaser → Product Administrator | สินค้า active ที่ `standard_cost = ฿100`; ใบเสนอราคา vendor คือ `฿140` — เบี่ยงอย่างมีนัยสำคัญ; Purchaser หา pricelist ที่ตรงล่าสุดไม่ได้ | Purchaser post `tb_product_comment` บนสินค้าด้วย attachment ใบเสนอราคา vendor; Product Administrator หยิบจากคิว comment, validate กับ pricelist vendor ปัจจุบัน update `standard_cost` (อาจ route สำหรับการอนุมัติ SoD ตาม Scenario 4) ตอบบน thread comment Purchaser ตรวจสอบใหม่และเพิ่มบรรทัด PR |
| 9 | Store Keeper flag barcode ไม่ตรงผ่าน comment | Store Keeper → Product Administrator | สินค้าที่มีอยู่พร้อม `barcode = '8851234567890'` map กับ "Spring Water 500ml" ขวดทางกายภาพในมือคือ "Spring Water 1L" พร้อมบาร์โค้ดเดียวกัน | Store Keeper สแกน ได้สินค้าที่ resolve ผิด post comment ด้วยรูปของฉลากทางกายภาพ Product Administrator validate (กับ vendor catalog) รู้ว่ารุ่น 1L ขาดจากแคตตาล็อก สร้าง `tb_product` ใหม่พร้อมบาร์โค้ดที่ถูก (สินค้า 500ml เก่าได้ `barcode = null` หรือบาร์โค้ดใหม่ถ้าตัวเดิมผิด) ตอบบน comment; Store Keeper สแกนใหม่และ resolve ถูกต้อง |
| 10 | สินค้าใหม่ต้องการ unit conversion ที่ยังไม่ตั้งค่า — Purchaser ถูกบล็อก | Purchaser → Product Administrator | สินค้า active ที่มี order-unit conversion `1 CASE = 12 EACH` เท่านั้น; vendor ต้องการออกใบแจ้งหนี้ใน `1 PALLET = 48 CASES` PR picker แสดงเฉพาะ conversion ที่ตั้งค่า | Purchaser ไม่สามารถเลือก `PALLET` บนบรรทัด PR ตาม `PRD_XMOD_006`; post comment ขอให้เพิ่ม conversion Product Administrator เพิ่มแถว `tb_unit_conversion` (และ `tb_unit` สำหรับ `PALLET` ถ้าไม่มี) validate ตาม `PRD_VAL_010` / `PRD_VAL_011` Purchaser เปิด picker ใหม่ เห็น `PALLET` เพิ่มบรรทัด |
| 11 | การจัดระเบียบการจำแนกใหม่ — การกระจาย prospective | Product Administrator | หมวดหมู่ที่มีอยู่ "Beverages" พร้อม sub-category ลูกที่ย้ายไปยัง category parent ต่าง สินค้า 50 ตัวถูกจำแนกใต้ sub-category ที่ย้าย | การย้าย commit; การกระจาย cascading-default เกิดที่ next-read บนผู้บริโภคปลายน้ำแต่ละรายตาม `PRD_LIFE_010` เอกสารเปิดที่ snapshot tax-profile / ค่า deviation เก่าเก็บ snapshot เอกสารใหม่อ่านค่าที่มีผลใหม่ Activity log บันทึกการย้ายพร้อมจำนวนสินค้าที่ได้รับผลกระทบ |
| 12 | Restore สินค้าที่ soft-deleted ถูกบล็อกโดยการ re-use code | Product Administrator | สินค้าที่ soft-deleted ที่ `code = 'BVR-001'`; สินค้าใหม่ถูกสร้างขึ้นในระหว่างนั้นด้วย `code = 'BVR-001'` เดียวกัน | Restore ปฏิเสธตาม `PRD_LIFE_009` ด้วย `"A live product with code 'BVR-001' already exists. Restore is blocked."` Product Administrator อย่างใดอย่างหนึ่ง rename สินค้าที่มีอยู่ (หายาก — รบกวน) หรือ restore ภายใต้ code ใหม่ (โดยแก้ `code` ของแถวที่ soft-deleted ก่อน restore — รบกวนเช่นกัน) |
| 13 | Hard-disable (`is_active = false`) — สินค้าหายจากทุกมุมมอง | Product Administrator | สินค้า active; การลบที่ compliance บังคับจำเป็น (เช่น supplier ถูกถอดเนื่องจาก non-compliance) | Hard-disable ตั้ง `is_active = false` และ implicit `product_status_type = inactive` ตาม `PRD_LIFE_005` สินค้าซ่อนจากทุก picker รวม admin view; ปรากฏเฉพาะบน read scope ของ Auditor และในรายงานแถวที่ soft-deleted Reversible โดยตั้ง `is_active = true` ใหม่ |
| 14 | การลบหน่วยถูกบล็อกโดย in-use guard | Product Administrator | `tb_unit` "POUND" ที่มีอยู่กับสินค้า 12 ตัวที่ใช้เป็น `inventory_unit_id` และ 30 แถว `tb_unit_conversion` ที่อ้างอิง | การลบปฏิเสธตาม `PRD_VAL_017` ด้วย `"Unit POUND is in use by 12 products / 30 conversions / N document lines and cannot be deleted."` Product Administrator ต้อง migrate สินค้าที่ขึ้นต่อกันไปยังหน่วยอื่น (หายาก — รบกวน; โดยปกติต้องการเครื่องมือ migration ระดับ application ไม่ใช่แค่การแก้แถวเดียว) ก่อนลองใหม่ |
| 15 | การ query Audit — ดูประวัติสินค้าที่ soft-deleted | Auditor | สินค้า active และ soft-deleted ในแคตตาล็อก; Auditor ต้องสอบสวนคำถาม traceability ของการ recall สำหรับสินค้าที่ลบ | scope การอ่านของ Auditor รวมแถวที่ soft-deleted ตาม `PRD_AUTH_011`; query return audit log เต็ม (create, edit, การเปลี่ยนสถานะ, event soft-delete) Cross-reference ไปยังธุรกรรมคลังประวัติ (ซึ่งเก็บ reference `product_id` ตาม `PRD_XMOD_002`) ให้ traceability การ recall ไม่มี write authority; ไม่มีการเปลี่ยนสถานะ |
| 16 | การเปลี่ยน vendor mapping — update vendor scope filter ของ Purchaser | Product Administrator → Purchaser | สินค้า map กับ Vendor A เท่านั้น; Vendor B ถูกเพิ่มเข้ามาใน mapping | แถว `tb_product_tb_vendor` ใหม่ insert ด้วย `vendor_id = Vendor B` Purchaser ที่จัดทำ PO ต่อ Vendor B เห็นสินค้าบน picker ตาม `PRD_AUTH_006`; บรรทัด PO save ถูกต้อง |
| 17 | thread Comment — การปิด | Product Administrator | thread comment เปิดจาก Purchaser ("standard cost ล้าสมัย") | Product Administrator สอบสวน update `standard_cost` (subject ต่อเกณฑ์ SoD ตาม Scenario 4) ตอบบน thread ด้วยสรุปการเปลี่ยน ปิด thread (หรือ mark เป็น resolved ตามธรรมเนียม tenant) Activity log บันทึกการเปลี่ยนต้นทุน; สถานะ comment-thread คือ "resolved" |

## 5. การ Map Test E2E

การครอบคลุม E2E ของโมดูล product **กระจายข้าม spec ของโมดูลต้นน้ำ** พร้อม spec ตรงเดียวสำหรับ browse หมวดหมู่ การครอบคลุมจึงประเมินตามว่า spec ต้นน้ำใด exercise ด้าน product

| Spec / describe block | scenario ข้าม persona ที่ครอบคลุม (Section 4) |
| --------------------- | ------------------------------------------- |
| `tests/101-product-category.spec.ts` (23 กรณี) | การครอบคลุมโดยตรงของ surface UI ของต้นไม้หมวดหมู่รวมถึง CRUD ทั้งสามระดับ; การครอบคลุมทางอ้อมของ Scenario 11 (ไม่มี E2E re-organisation) |
| `tests/044-eco.spec.ts` (19 กรณี) | CRUD ข้อมูลหลัก eco-label ที่ `/product-management/eco` (ไม่ใช่ scenario ด้านบน) |
| `tests/301-pr.spec.ts`, `302-…-creator`, `304-…-purchaser` | การครอบคลุมทางอ้อมของ Scenario 1 (Purchaser พบสินค้าใหม่บน picker), Scenario 10 (unit picker บนบรรทัด PR) Scenario 5 สังเกตไม่ได้ — ไม่มี guard การปิดใช้อยู่จริง |
| `tests/401-po.spec.ts`, `402-…-purchaser` | การครอบคลุมทางอ้อมของ Scenario 16 (filter vendor-scope บน PO picker) |
| `tests/501-grn.spec.ts` | การครอบคลุมทางอ้อมของ Scenario 1 (Store Keeper เห็นสินค้าใหม่ระหว่างการรับ) และของการเช็ค deviation-limit ของ GRN ที่บริโภค `price_deviation_limit` / `qty_deviation_limit` (`PRD_XMOD_007`) ไม่มีขั้นตอน barcode-scan ใน spec |
| `tests/701-sr.spec.ts` | การครอบคลุมทางอ้อมของ Scenario 1 (Store Keeper หยิบสินค้าใหม่ระหว่าง SR dispatch) |

ช่องว่างเทียบกับ Section 4:

- **Scenario 1 (CRUD ของสินค้า)** — ไม่มี spec E2E ตรง; catalog `docs/test-cases/100-product.md` 52 กรณีคือ checklist แบบ manual **Scenario 2, 3 (bulk import)** — ฟีเจอร์ไม่มีอยู่จริง
- **Scenario 4, 6, 7 (gate ของ lifecycle และการเปลี่ยน cost ที่ SoD-route)** — gate เหล่านี้ยังไม่ได้ implement ([02-business-rules](/th/inventory/product/02-business-rules) § 5.1); E2E ใด ๆ จะ assert design intent เทียบกับพฤติกรรมจริงที่ขัดแย้งกัน
- **Scenario 8, 9, 17 (thread Comment — feedback และการ resolve)** — ไม่มี E2E สำหรับ comment ของสินค้า; manual / planned
- **Scenario 11, 12 (การจัดระเบียบใหม่ของการจำแนกและการ restore)** — ไม่มี E2E; manual / planned spec หมวดหมู่ครอบคลุม view-only
- **Scenario 13 (Hard-disable)** — ไม่มี E2E; manual / planned
- **Scenario 14 (in-use guard ของการลบหน่วย)** — ไม่มี E2E สำหรับการจัดการหน่วย; manual / planned
- **Scenario 15 (การ query Audit บนที่ soft-deleted)** — ไม่มี E2E; manual / planned scope ของ Auditor โดยทั่วไป test ที่ระดับโมดูล admin ไม่ใช่ต่อโมดูล content
- **Scenario 16 (การ update vendor-mapping)** — exercise บางส่วนผ่าน spec ของโมดูล PO เมื่อมี

ช่องว่างเป็นโครงสร้าง: **โมดูล product เป็น master-data backbone** ที่มี UI CRUD แต่ไม่ใช่ workflow document ดังนั้น spec E2E ที่ test รูปแบบ "submit → approve → post" ไม่ใช้โดยตรง การครอบคลุม E2E ด้าน product ที่ครอบคลุมจะต้องการ `100-product.spec.ts` เฉพาะที่ครอบคลุม create / edit / lifecycle / import / classification / unit-conversion / location-mapping / vendor-mapping; จนกว่านั้น ไฟล์ test ต่อ persona รวบรวมการครอบคลุม manual / planned

## 6. แหล่งอ้างอิง

- `../carmen-inventory-frontend-e2e/tests/101-product-category.spec.ts` (23 กรณี) + `docs/test-cases/gaps/101-product-category-gap.md` (39) — มุมมองต้นไม้หมวดหมู่และ CRUD สามระดับ
- `../carmen-inventory-frontend-e2e/tests/044-eco.spec.ts` (19 กรณี) + `docs/test-cases/gaps/044-eco-gap.md` (29) — ข้อมูลหลัก eco-label
- `../carmen-inventory-frontend-e2e/docs/test-cases/100-product.md` (52 กรณี catalog เท่านั้น ตรวจสอบซ้ำ 2026-09-20 — บันทึกชื่อแท็บจริง General / Unit / Location Assignment / Eco Labels, รหัสที่สร้างอัตโนมัติและถูกล็อก, ชุดฟิลด์บังคับ, toast แบบ warning ตอน submit ไม่ถูกต้อง และคอลัมน์ Shelf)
- `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` — spec GRN; การครอบคลุมด้าน product ทางอ้อมผ่าน product picker
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4 — handoff ข้าม persona ที่ขับเคลื่อน scenario integration ด้านบน
- Sibling: [02-business-rules.md](./02-business-rules.md) — กฎ validation (`PRD_VAL_*`), calculation (`PRD_CALC_*`), authorization (`PRD_AUTH_*`), lifecycle (`PRD_LIFE_*`) และข้ามโมดูล (`PRD_XMOD_*`) ที่อ้างโดยทุก scenario ด้านบน
- Sibling: [01-data-model.md](./01-data-model.md) — เอนทิตี canonical (`tb_product`, ห่วงโซ่การจำแนก, `tb_unit`, `tb_unit_conversion`, `tb_product_location`, `tb_product_tb_vendor`) และ enum (`enum_product_status_type`, `enum_unit_type`) อ้างทั่วทั้ง
- รายละเอียดต่อ persona: [Product Administrator](./04-test-scenarios-product-admin.md), [Purchaser](./04-test-scenarios-purchaser.md), [Store Keeper](./04-test-scenarios-store-keeper.md)
- ที่เกี่ยวข้อง: [purchase-request](/th/inventory/purchase-request) / [purchase-order](/th/inventory/purchase-order) / [good-receive-note](/th/inventory/good-receive-note) / [store-requisition](/th/inventory/store-requisition) / [recipe](/th/inventory/recipe) / [vendor-pricelist](/th/inventory/vendor-pricelist) — suite E2E ของโมดูลธุรกรรมทุกตัว exercise เส้นทางการอ่าน product master ทางอ้อม
