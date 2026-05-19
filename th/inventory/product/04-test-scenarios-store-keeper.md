---
title: สินค้า (Product) — Test Scenarios — Store Keeper
description: test case ของ Store Keeper (happy-path barcode scan, RBAC scope, validation ด้าน read, comment / feedback, edge case) สำหรับโมดูลสินค้า
published: true
date: 2026-05-17T12:00:00.000Z
tags: product, test-scenarios, store-keeper, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:30:00.000Z
---

# สินค้า (Product) — Test Scenarios — Store Keeper

> **At a Glance**
> **Persona:** Store Keeper (ผู้บริโภค floor read-only; การ lookup barcode-scan) &nbsp;·&nbsp; **โมดูล:** [[product]] &nbsp;·&nbsp; **scenario:** ~35
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **การครอบคลุม E2E:** ทางอ้อม — exercise ผ่าน `501-grn.spec.ts`, `701-sr.spec.ts` ใน `../carmen-inventory-frontend-e2e/`

หน้านี้บันทึก test scenario ที่ persona Store Keeper ขับเคลื่อนในโมดูล `product` พวกเขาเป็น **ผู้บริโภค read-only** ที่ระดับ floor / location — พวกเขาสแกนบาร์โค้ดสำหรับการระบุสินค้าที่รวดเร็วระหว่างการรับ / หยิบ / นับ ดูคำแนะนำการจัดการและนโยบายสต๊อกต่อ location และ post comment สำหรับ barcode ไม่ตรงและปัญหาเชิงปฏิบัติการ อำนาจของพวกเขาบน product master คือ **read + comment เท่านั้น**; พวกเขาไม่สร้าง แก้ หรือลบฟิลด์ข้อมูลหลักใด ๆ scenario รวมไปที่ **พฤติกรรม lookup barcode-scan** **การอ้างอิงโน้ตการจัดการและนโยบายต่อ location** ระหว่างการรันการนับ **RBAC scope** (อะไรที่พวกเขาเห็นและไม่เห็นได้) และ **เส้นทาง comment / feedback** สำหรับ barcode ไม่ตรงและการแก้ไขโน้ตการจัดการ งานธุรกรรมของพวกเขา (การรัน GRN ที่ dock การรันการนับ / spot count การยก stock-in / stock-out การ dispatch SR) อยู่ในไฟล์ persona ของโมดูลตามลำดับ handoff ข้าม persona ที่ pivot จาก Store Keeper (Scenario 1, 9 ใน parent overview) อยู่ใน [04-test-scenarios.md](./04-test-scenarios.md) ไม่ใช่ที่นี่

## 1. Happy Path

| # | Scenario | Pre-condition | ขั้นตอน | คาดหวัง |
| - | -------- | ------------- | ----- | -------- |
| SK-HP-01 | Barcode scan resolve เป็นสินค้า active เดียว | Store Keeper `sk@blueledgers.com` login บนมือถือ; บนหน้าจอการรับ GRN สำหรับ GRN in-progress; สินค้า `COF-001` มีอยู่ด้วย `barcode = '8851234567890'` active | 1. แตะปุ่ม scan → camera อ่าน barcode 2. Lookup endpoint รับ `8851234567890` → query `tb_product.barcode = '8851234567890'` filter เป็นสินค้า active 3. Return การ์ดสินค้าที่ resolve พร้อม code, name, รูป (ถ้าแนบ), หน่วยฐาน, เส้นทางการจำแนก 4. ยืนยัน "เพิ่มไปยังบรรทัด GRN นี้" | match resolve เดี่ยวตาม `PRD_VAL_005` (ความไม่ซ้ำของบาร์โค้ดบังคับใช้ที่ app) บรรทัด GRN populate ด้วย `product_id` ไม่มีการเปลี่ยนสถานะบน product master Map ไปยัง parent Scenario 1 (Store Keeper เห็นสินค้าใหม่ระหว่างการรับ) |
| SK-HP-02 | ค้นหาด้วย code (การค้นหาด้วยมือบนมือถือ) | ไม่มี barcode label มองเห็น; Store Keeper ค้นหาด้วยมือ | 1. แตะ search → กรอก `COF-001` ในฟิลด์ search 2. Picker แสดงสินค้าที่ match 3. แตะเพื่อเลือก | ผลลัพธ์เหมือน SK-HP-01 — สินค้า resolve ผ่าน code lookup ตาม `PRD_AUTH_007` scope คือแคตตาล็อก live active |
| SK-HP-03 | อ้างอิงโน้ตการจัดการก่อนเปิด shipment เน่าเสีย | รับ shipment ของผลผลิตสด; สินค้า `P-BERRY` มี JSON `info` `{ "storage": "Refrigerate 2-4°C", "shelfLifeDays": 7, "perishable": true }` | 1. สแกน barcode → การ์ดสินค้า 2. แตะ "ดูรายละเอียด" → panel โน้ตการจัดการ render ค่า info JSON | flag การจัดเก็บ / อายุการเก็บรักษา / เน่าเสีย render สำหรับการอ้างอิงของ Store Keeper Shipment จากนั้น route ไปยัง station cold-chain ตาม ไม่มีการเปลี่ยน master |
| SK-HP-04 | อ้างอิงนโยบายสต๊อกต่อ location ระหว่างการนับ | รันการนับสต๊อกที่ LOC-A; สินค้า `COF-001` มีแถว `tb_product_location` ที่ LOC-A ด้วย `par_qty = 20`, `min_qty = 5`, `max_qty = 50` qty ที่นับคือ 18 | 1. สแกน barcode → การ์ดสินค้า 2. แตะ "ดูรายละเอียด" → panel นโยบายแสดง par/min/max สำหรับ location การนับ 3. ผู้นับเห็น qty ที่นับ 18 vs par 20 → ต่ำกว่า par เล็กน้อย; สูงกว่า min มาก — ภายในช่วงที่คาดหวัง | ค่านโยบายแสดงตาม `PRD_AUTH_008` Store Keeper ดำเนินการกับบรรทัดการนับ; ไม่มีการเปลี่ยน master เอกสารการนับจับบรรทัดการนับใน [[physical-count]] |
| SK-HP-05 | ใช้ barcode สำหรับการยืนยันการหยิบ SR dispatch | Dispatch ต่อ SR ที่อนุมัติ; สินค้า `COF-001`; ตำแหน่งถัง pre-map ผ่าน SR Store Keeper สแกน barcode ถังเพื่อยืนยัน | 1. หน้าจอ SR dispatch แสดง `product_id = COF-001` ที่คาดหวังและตำแหน่งถัง 2. Store Keeper หยิบถุงจากถังและสแกน barcode ของถุง 3. มือถือ resolve เป็น `COF-001` — match ที่คาดหวัง 4. ยืนยันการหยิบ | การยืนยันการหยิบจากถังสำเร็จ Product master เป็น read-only; SR dispatch ดำเนินต่อใน [[store-requisition]] |
| SK-HP-06 | Post comment สำหรับ barcode ไม่ตรง | ระหว่างการรับ barcode ที่สแกน `8851234567890` resolve เป็น "Spring Water 500ml" แต่ขวดทางกายภาพคือ "Spring Water 1L" | 1. แตะ "สินค้าผิด" บนการ์ดสินค้าที่ resolve 2. หน้าจอ comment เปิดด้วย barcode ที่สแกนและ reference สินค้าที่ resolve pre-fill 3. Store Keeper เพิ่ม: "ขวดทางกายภาพคือ 1L master บอก 500ml รูปแนบ" แนบรูป 4. Save | แถว `tb_product_comment` insert บนสินค้าที่ได้รับผลกระทบด้วย `user_id = sk@blueledgers.com`, `type = user`, message, attachment Product Administrator หยิบจากคิวตาม parent Scenario 9 Store Keeper อาจดำเนินการ GRN ต่อผ่านการค้นหาด้วยมือเพื่อหาสินค้าที่ถูก (1L) หรือถือบรรทัดจนกว่า master จะ update |
| SK-HP-07 | Post comment สำหรับการแก้ไขโน้ตการจัดการ | คำแนะนำการจัดเก็บใน `tb_product.info` บอก "Ambient" แต่ถุง supplier บอก "Refrigerate 2-4°C" | 1. ดูรายละเอียดสินค้า → tab Comments 2. comment ใหม่: "คำแนะนำการจัดเก็บผิด — ถุง supplier ระบุการแช่เย็น 2-4°C รูปของถุงแนบ" 3. Save | Comment route ไปยัง Product Administrator ตาม parent Scenario 9 (การ handoff ไม่ตรง / การแก้ไข) การแก้ไขที่เกี่ยวกับความปลอดภัยสำคัญ (การละเว้นสารก่อภูมิแพ้ flag อันตราย) escalate out-of-band นอกเหนือจาก comment |
| SK-HP-08 | Post feedback บนนโยบายสต๊อกต่อ location | การนับประจำที่ LOC-B; under-stock คงที่ที่ `min_qty = 5` สำหรับสินค้า `MILK-002`; re-order รีบคงที่ Store Keeper เชื่อว่า `min_qty` ควรเป็น 10 | 1. เปิดสินค้า `MILK-002` → tab Location Assignment → คลิกแถว LOC-B 2. panel comment: "Min qty 5 ที่ LOC-B ต่ำเกินไป — stock-out คงที่ แนะนำ 10" 3. Save | Comment route ไปยัง **Inventory Controller** (ไม่ใช่ Product Administrator) ตาม [[inventory/02-business-rules]] `INV_AUTH_004` (อำนาจนโยบายเติมสต๊อก) handoff ข้าม persona ครอบคลุมใน [[product/03-user-flow]] Section 4 |
| SK-HP-09 | ตรวจสอบรายละเอียดสินค้าออฟไลน์ / cached | มือถือในการเชื่อมต่อแย่ที่ dock; ข้อมูลสินค้าล่าสุด cached | 1. เปิดรายละเอียดสินค้า; มือถือ render จาก cache 2. ฟิลด์บางตัวอาจ stale (ต้นทุนรับล่าสุด on-hand ปัจจุบัน); flag เป็น "ออฟไลน์ / cached" | offline mode read-only ตามธรรมเนียม mobile-PWA Caveat stale data แสดง; re-fetch เต็มเมื่อการเชื่อมต่อกลับมา |

## 2. Permission / Authorization

| # | Scenario | พฤติกรรมที่คาดหวัง (allow/deny + เหตุผล) |
| - | -------- | --------------------------------------- |
| SK-PERM-01 | Store Keeper ทำ barcode lookup | **Allow** ตาม `PRD_AUTH_007` endpoint barcode lookup มีให้ Store Keeper Scope คือแคตตาล็อก active (`product_status_type = active`, `is_active = true`, `deleted_at IS NULL`) |
| SK-PERM-02 | Store Keeper อ่านนโยบายสต๊อกต่อ location | **Allow read-only** ตาม `PRD_AUTH_008` ไม่สามารถแก้ |
| SK-PERM-03 | Store Keeper พยายามแก้นโยบาย `tb_product_location` | **Deny — ต้องการ Inventory Controller** ตาม `INV_AUTH_004` เส้นทางของ Store Keeper คือ post feedback ตาม SK-HP-08 route ไปยัง Inventory Controller |
| SK-PERM-04 | Store Keeper พยายามสร้างสินค้าใหม่ | **Deny — ต้องการ Product Administrator** ตาม `PRD_AUTH_001` UI มือถือไม่มี affordance "create new product" การส่ง API ตรง return `403 Forbidden` เส้นทาง: post comment ขอให้ Product Administrator สร้างสินค้า |
| SK-PERM-05 | Store Keeper พยายามแก้ฟิลด์ `tb_product` (รวม barcode) | **Deny** Write authority เป็น Product Administrator เส้นทาง barcode-mismatch ของ Store Keeper คือ **comment** ไม่ใช่แก้ตรง |
| SK-PERM-06 | Store Keeper พยายามลบสินค้าหรือแถวย่อยของมัน (conversion, vendor mapping) | **Deny** Delete authority เป็น Product Administrator `403 Forbidden` |
| SK-PERM-07 | Store Keeper post comment บนสินค้า | **Allow** ตาม `PRD_XMOD_011` Comment route ไปยัง Product Administrator สำหรับ review (หรือ Inventory Controller สำหรับ comment ที่เกี่ยวกับนโยบาย) |
| SK-PERM-08 | Store Keeper ดู activity log บนสินค้า | **Allow read-only** ตาม `PRD_XMOD_011` เห็นประวัติของการเปลี่ยน master |
| SK-PERM-09 | Store Keeper ดูสินค้า inactive / deleted | **Allow read** ถ้า filter toggle — แต่ **ไม่สามารถเลือก** สำหรับธุรกรรมใหม่ตาม `PRD_XMOD_001` ใช้สำหรับ research "อะไรอยู่ที่นี่ก่อน" ระหว่างการสอบสวนการนับ |
| SK-PERM-10 | Store Keeper export แคตตาล็อก | **จำกัด** — โดยทั่วไปไม่มีบนมือถือ การเข้าถึง desktop subject ต่อนโยบาย tenant; Store Keeper โดยทั่วไปไม่ export |

## 3. Validation / Error

| # | Scenario | Trigger | Error ที่คาดหวัง |
| - | -------- | ------- | -------------- |
| SK-VAL-01 | Scan resolve เป็นไม่มีสินค้า (`PRD_VAL_005` complement) | Barcode `9999999999999` ไม่อยู่ใน `tb_product.barcode`; barcode lookup | **empty resolve-set** — UI แสดง "ไม่พบสินค้าสำหรับ barcode <X> ค้นหาด้วยมือหรือขอสินค้าใหม่" Store Keeper ใช้การค้นหาด้วยมือหรือ post comment คำขอสินค้าใหม่ ไม่ใช่ error การ validate อย่างเข้มงวด — ผลลัพธ์ว่าง |
| SK-VAL-02 | Scan resolve เป็นสินค้า inactive | index barcode active return match; `product_status_type = inactive` | **ปฏิเสธที่ line save** ตาม `PRD_XMOD_001`: `"Product <code> is inactive or deleted and cannot be added to new transactions."` UI มือถือแสดง flag inactive บนการ์ดสินค้าที่ resolve; ปุ่ม "เพิ่มไปยังบรรทัด" ปิด Store Keeper สอบสวน — โดยทั่วไปสินค้าต้องถูก re-activate โดย Product Administrator ก่อนดำเนินการต่อ |
| SK-VAL-03 | Scan resolve เป็นสินค้าที่ soft-deleted (หายาก) | สินค้าที่ soft-deleted ยังมี barcode ใน DB; lookup return | **ปฏิเสธที่ line save** — `"Product <code> is inactive or deleted and cannot be added to new transactions."` endpoint barcode-lookup ควรปกติ filter เป็น non-deleted; การตรวจสอบ backend ป้องกันจับ edge case |
| SK-VAL-04 | match barcode หลายตัว (ปัญหาคุณภาพข้อมูล) | สินค้าสองตัว live ด้วย barcode เดียวกัน (ไม่ควรเกิดตาม `PRD_VAL_005` app-enforcement; race / bug หายาก) | UI แสดง picker ผลลัพธ์คลุมเครือ — Store Keeper เลือก active ที่ถูก (หรือ "สินค้าผิด" ถ้าไม่ match ทางกายภาพ) Post comment เพื่อให้ Product Administrator ลบซ้ำ |
| SK-VAL-05 | เลือกหน่วยที่ไม่ตั้งค่าบน stock-in / stock-out | ทำ stock-in ด้วยมือ; สินค้าไม่มี order-unit `BAG`; Store Keeper พยายามกรอก qty ใน `BAG` | **ปฏิเสธ** ตาม `PRD_XMOD_006`: `"No conversion factor defined for unit BAG → <base unit> on product <code>."` รูปแบบเดียวกับ flow ของ Purchaser การ resolve: post comment ขอให้ Product Administrator เพิ่ม conversion |
| SK-VAL-06 | Attachment ของ Comment เกินขีดจำกัด | Attachment รูปคือ 20MB; ขีดจำกัด tenant คือ 5MB | **ปฏิเสธที่ submit** — `"Attachment exceeds maximum size (5MB)."` Store Keeper ปรับขนาด / ถ่ายรูปใหม่และส่งใหม่ |
| SK-VAL-07 | Submit stock-in เน่าเสียโดยไม่มีวันหมดอายุ | Stock-in สำหรับสินค้าเน่าเสีย; ฟิลด์วันหมดอายุว่าง | **ปฏิเสธที่ submit** ตาม `INV_VAL_006` ที่ขยายสำหรับสินค้าเน่าเสีย flag เน่าเสียอยู่บน `tb_product.info` การ validate ด้าน product ป้อนกฎด้าน inventory; เส้นทาง document ใน [[inventory/04-test-scenarios-store-keeper]] SK-HP-06 |

## 4. Edge Cases

| # | Scenario | เงื่อนไข | คาดหวัง |
| - | -------- | --------- | -------- |
| SK-EDGE-01 | label barcode เสียหาย / อ่านไม่ได้ | camera ไม่สามารถ decode barcode หลังหลายความพยายาม | Fallback ไปการค้นหาด้วยรหัส / ชื่อด้วยมือ flow มาตรฐานของมือถือ ไม่มีการจัดการพิเศษด้าน product; ตาม flow การรับ [[good-receive-note]] |
| SK-EDGE-02 | barcode ที่สแกน match กับสินค้าประวัติหลายตัว (soft-deleted) | สินค้า active ไม่มี barcode ชน; สินค้าที่ soft-deleted สองตัวมี barcode เดียวกัน Filter live บน lookup ยกเว้นพวกเขา | match live เดี่ยว return การ query Audit (role Auditor) เห็นซ้ำประวัติ ไม่มีผลกระทบ Store Keeper |
| SK-EDGE-03 | นโยบายต่อ location ไม่ตั้งค่า (ไม่มีแถว `tb_product_location`) | สินค้าไม่มีแถว `tb_product_location` ที่ location การนับ | มุมมองรายละเอียดแสดง "นโยบายไม่ตั้งค่าสำหรับ location นี้" แทนค่าศูนย์ ผู้นับสังเกตความแตกต่างและ post comment ไปยัง Inventory Controller (หรือไปยัง Product Administrator ถ้าแถว location-mapping เองขาด ตาม handoff persona ใน [[product/03-user-flow]]) |
| SK-EDGE-04 | standard cost เป็นศูนย์ | สินค้าฟรี / FOC มี `standard_cost = 0`; Store Keeper ที่การรับเห็นศูนย์ | แสดง `฿0.00`; ไม่มี flag ความผิดปกติ (FOC item เป็น legitimate) ตาม `PRD_VAL_007` ศูนย์ได้รับอนุญาต |
| SK-EDGE-05 | สินค้าย้ายไปยัง item-group ต่างกลางการนับ | ผู้นับมีรายละเอียดสินค้าเปิดระหว่างการรันการนับ; Product Administrator re-classify พร้อมกัน | ตาม `PRD_LIFE_010`: การเปลี่ยนเป็น prospective มุมมองรายละเอียดปัจจุบันของผู้นับอาจแสดงเส้นทางการจำแนก stale จนกว่า refresh บรรทัดการนับเองไม่ได้รับผลกระทบ (snapshot ที่ line save) |
| SK-EDGE-06 | user หลายคนบน session อุปกรณ์มือถือเดียวกัน | เปลี่ยนกะ; Store Keeper A logout, Store Keeper B login บน tablet เดียวกัน draft comment ค้างจาก A ยังใน local cache | draft comment session-scope ต่อ user; B ไม่เห็น draft ของ A รูปแบบ auth มาตรฐาน; ไม่มีความกังวลด้าน product |
| SK-EDGE-07 | thread Comment บนสินค้าสะสม reply มาก | สินค้า velocity สูงรับ comment / reply 30+ จาก Store Keeper / Purchaser ในเดือน | comment ทั้งหมดเก็บบน `tb_product_comment` Threading / pagination บน tab comment Sort ล่าสุดก่อน Audit log จับทั้งหมด |
| SK-EDGE-08 | อ่านสินค้าที่ soft-deleted ผ่าน ID ตรง (รองรับการ research ของ auditor) | role Auditor ขอ Store Keeper ตรวจสอบโน้ตการจัดการของสินค้าประวัติ | ตาม `PRD_AUTH_011` Auditor เห็นแถว soft-deleted ถ้า Store Keeper มี scope การอ่าน (ผ่าน toggle บนรายการแคตตาล็อก) พวกเขาสามารถดูรายละเอียดสินค้าที่ soft-deleted ไม่สามารถเพิ่มไปยังบรรทัดใหม่ |
| SK-EDGE-09 | Scan ระหว่างการสะดุดการเชื่อมต่อ | มือถือออฟไลน์; barcode scan พยายาม | ตาม offline mode: scan post ไปยังคิว local; lookup รันกับแคตตาล็อก cached; ถ้าพบ บรรทัดถูก stage local และ sync เมื่อ reconnect ถ้าไม่อยู่ใน cache "ออฟไลน์ — barcode ไม่อยู่ในแคตตาล็อก local"; Store Keeper บันทึกทางกายภาพและ resolve ที่ reconnect |

## 5. แหล่งอ้างอิง

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — handoff ข้าม persona ที่ pivot จาก Store Keeper: Scenario 1 (สินค้าใหม่ถึงผู้บริโภคผ่าน barcode scan), Scenario 9 (comment barcode-mismatch)
- User flow: [03-user-flow-store-keeper.md](./03-user-flow-store-keeper.md) — แหล่ง happy-path สำหรับ Section 1 ด้านบน; อธิบาย primary flow 5 ขั้นตอน (barcode scan ระหว่างการรับ) รูปแบบ count / spot-check รูปแบบ stock-in / stock-out ด้วยมือ และเส้นทาง comment / feedback Decision branch (resolve เดี่ยว vs หลายตัว vs ไม่มี fallback ด้วยมือ ลักษณะ soft-deleted) แจ้ง edge case Section 4
- กฎทางธุรกิจที่ verify: [02-business-rules.md](./02-business-rules.md) — `PRD_VAL_005` (ความไม่ซ้ำของบาร์โค้ด app-enforced); authorization `PRD_AUTH_007` (Store Keeper อ่านด้วย barcode lookup), `PRD_AUTH_008` (อ่านนโยบายต่อ location ไม่แก้); cross-module `PRD_XMOD_001` (สินค้า inactive ถูกปฏิเสธบนบรรทัดใหม่) ด้าน inventory `INV_VAL_006` (เอกลักษณ์ lot + วันหมดอายุเน่าเสีย) และ `INV_AUTH_004` (Inventory Controller เป็นเจ้าของนโยบายเติมสต๊อก) อ้างสำหรับ SK-VAL-07 และ SK-HP-08
- spec E2E: ไม่มี spec ด้าน product ของ Store Keeper บนมือถือตรง; การครอบคลุมเป็นทางอ้อมผ่าน [[good-receive-note]] (`501-grn.spec.ts`), [[physical-count]] / [[spot-check]] (spec การรันการนับ) และ [[store-requisition]] (`701-sr.spec.ts`) — ซึ่ง exercise เส้นทาง barcode-scan และ product-picker จาก flow ธุรกรรมของ Store Keeper scenario ส่วนใหญ่ด้านบนเป็น manual / planned Mobile happy-path fixture ตรงกับ `sk@blueledgers.com`
- Cross-link: [[good-receive-note]] — โมดูลหลักสำหรับ flow barcode-scan ระหว่างการรับ; product master ถูกบริโภคที่ line entry
- Cross-link: [[inventory]] — Store Keeper เขียนผ่าน `tb_stock_in` / `tb_stock_out`; อ่านนโยบาย `tb_product_location`; `INV_AUTH_004` สำรองการแก้นโยบายให้ Inventory Controller
- Cross-link: [[physical-count]] / [[spot-check]] — การรันการนับใช้ barcode scan และการอ้างอิงนโยบายตาม Section 1
- Cross-link: [[store-requisition]] — SR dispatch ใช้ barcode สำหรับการยืนยันการหยิบตาม SK-HP-05
- Cross-link: [[inventory-adjustment]] — stock-in / stock-out จากการปรับด้วยมือ; flag เน่าเสียขับเคลื่อนความต้องการวันหมดอายุที่การสร้าง lot
