---
title: การสุ่มตรวจ (Spot Check)
description: การนับแบบเฉพาะจุดของสินค้าที่สุ่มเลือก ณ ตำแหน่งเดียว — ไม่มีการ post อัตโนมัติไปที่ใดเลย
published: true
date: 2026-07-15T18:38:42.000Z
tags: spot-check, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# การสุ่มตรวจ (Spot Check)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** การนับแบบเฉพาะจุด ไม่ผูกกับงวด ของสินค้าที่สุ่ม/เลือกมูลค่าสูง/เลือกเองในตำแหน่งเดียว บันทึกและ review โดย role เดียวที่ไม่แยกย่อย &nbsp;·&nbsp; **ผู้ใช้งาน:** ผู้ใช้ที่มีสิทธิ์ `inventory_management.spot_check` — ไม่พบการแยก persona ในโค้ด &nbsp;·&nbsp; **เอนทิตี/ตารางสำคัญ:** `tb_spot_check`, `tb_spot_check_detail`, ตาราง comment สองตาราง (`tb_spot_check_comment` มีแค่ schema — ไม่มี hook ฝั่ง frontend เรียกใช้เลย; `tb_spot_check_detail_comment` คือตัวที่ใช้งานจริง สำหรับ note/รูปต่อบรรทัด), `enum_spot_check_status` (4 ค่า), `enum_spot_check_method` (3 ค่า) &nbsp;·&nbsp; **หน้าย่อย:** 10

![Spot Check screen](/screenshots/spot-check/index.png)

![Spot Check review screen](/screenshots/spot-check/review.png)

## 1. ภาพรวม

**Spot check** คือการนับแบบเฉพาะจุด ไม่ผูกกับงวด ของสินค้าที่สุ่มเลือกในตำแหน่งเดียว — เป็นลูกพี่ลูกน้องที่เบากว่าของ [physical-count](/th/inventory/physical-count) ซึ่งนับทุกรายการในตำแหน่งภายใต้งวดบัญชี การ implement จริง (`../carmen-inventory-frontend-react/routes/inventory-management/spot-check/`) เป็น flow ต่อเนื่องเดียวไม่มีการส่งต่อระหว่างบุคคล: ผู้ใช้เปิดรายการตำแหน่ง (`spot-check`) เริ่มการตรวจใหม่สำหรับตำแหน่งที่ยังไม่มีการตรวจค้าง (`spot-check/location/:location_id`) โดยเลือกตำแหน่งที่ล็อกไว้ วิธีการสุ่ม (`method`: random / high-value / manual) และขนาดตัวอย่าง กรอก `actual_qty` ต่อสินค้าที่สุ่มได้ในหน้า entry (`spot-check/:id`) review ผลต่างที่คำนวณได้ (`spot-check/:id/review`) และยืนยัน submit ขั้นสุดท้าย ทุก action ถูกกำหนดสิทธิ์ด้วย permission key CRUD เดียว คือ `inventory_management.spot_check` (`constant/permissions.ts`) ไม่พบ role ผู้อนุมัติ ผู้ตรวจสอบ หรือ configuration แยกต่างหาก ไม่ว่าจะเป็น route permission ใน frontend, backend หรือ Bruno collection สำหรับโมดูลนี้

**ข้อค้นพบหลักของโมดูลนี้: ไม่มีอะไรจาก spot check ถูก post ไปที่ไหนเลย** การ submit ขั้นสุดท้าย (`spot-check.service.ts` `submit()`) ทำเพียงสองอย่าง — ตั้ง `doc_status = completed` และประทับเวลา `end_date` — และ doc-comment ของตัวมันเองก็ระบุไว้ตรง ๆ ว่า *"Does not create stock-in/stock-out — any follow-up adjustments are user-driven."* การค้นทั้ง repo ในฝั่ง frontend และ backend ของ spot-check สำหรับ `stock_in`, `stock_out`, `executeAdjustment`, `journal`, `ledger`, `threshold`, `tolerance`, และ `recount` ไม่พบผลลัพธ์ใดเลย นี่เป็นกลไกที่ต่างและง่ายกว่า rollup ของ [physical-count](/th/inventory/physical-count) เองอย่างมาก (ซึ่งอย่างน้อยยังสร้างแถว `tb_stock_in`/`tb_stock_out` ดิบที่ไม่ post) — spot check บันทึกผลต่างแล้วจบตรงนั้น หากผลต่างต้องแก้ไขใน ledger ผู้ใช้ต้องไปสร้างเอกสาร [inventory-adjustment](/th/inventory/inventory-adjustment) Stock In/Out แยกต่างหากเอง — ไม่มีลิงก์อัตโนมัติ ไม่มี reason code หรือแม้แต่ description string ที่เชื่อมสองเอกสารเข้าด้วยกัน

**ข้อค้นพบที่สอง ซึ่งไม่เคยถูกบันทึกมาก่อน: ฟอร์มสร้าง/แก้ไขของโมดูล (`sc-form.tsx`) มี code path view/edit/delete ที่ตายแล้ว** `ScForm` ถูก render จากที่เดียวในแอปคือ `spot-check-by-location-content.tsx` และเสมอโดยไม่ส่ง entity `spotCheck` เข้าไป — จึงอยู่ในโหมด "add" เสมอ branch `isView`/`isEdit` ของ component, ปุ่ม Edit/Delete และ hook `useUpdateSpotCheck`/`useDeleteSpotCheck` ที่ปุ่มเหล่านั้นเรียก จึงเข้าถึงไม่ได้ผ่าน navigation จริงใด ๆ; `spot-check/:id` (route เดียวที่พอจะเป็นไปได้ที่จะเปิดเอกสารที่มีอยู่) render หน้า entry/counting เสมอ (`ScEntryComponent`) ไม่เคย render `ScForm` เลย มี `update()`/`delete()` ฝั่ง backend อยู่จริงและจะทำงานได้ถ้าเรียกตรง (เช่นจาก Bruno) แต่ไม่มีปุ่มใดใน UI ที่ shipped ไปถึงมันได้

## 2. บริบททางธุรกิจ

ในการดำเนินงานโรงแรม spot check ให้ **การยืนยันที่รวดเร็วและไม่รบกวน** สำหรับสินค้าเสี่ยงสูง — สุราพรีเมียม เนื้อชั้นดี amenity แบรนด์ ของควบคุม — โดยไม่มีภาระงานของการนับ physical count เต็มรูปแบบ เพราะ spot check สุ่มสินค้าเพียงไม่กี่รายการในตำแหน่งเดียวแทนที่จะเป็นทุกสินค้าทุกที่ จึงสามารถเริ่มและจบได้ภายในกะเดียว

คุณค่าที่แท้จริงของฟีเจอร์นี้ ตามที่ implement ไว้ แคบกว่าที่กรอบ "โปรแกรม loss-prevention" จะบ่งบอก: มันเป็น **เครื่องมือนับและบันทึกผลต่าง** ไม่ใช่ workflow การ post หรืออนุมัติ ผู้ใช้สุ่มสินค้า นับ แล้วเห็นสรุป matches/variances/overages/shortages สิ่งที่เกิดขึ้นต่อจากนั้น — การสืบสวนของขาด การยกระดับเป็น inventory adjustment อย่างเป็นทางการ การรายงานความสงสัยว่ามีการขโมย — เป็นกระบวนการ manual นอกระบบที่โมดูลนี้ไม่ได้ orchestrate หรือติดตามให้

## 3. แนวคิดสำคัญ

- **`method` การสุ่ม**: วิธีเลือกรายการสินค้าใน scope ตอนสร้าง สามค่าใน `enum_spot_check_method`: `random` (Fisher-Yates shuffle บนสินค้าทุกตัวที่ถูก assign ให้หรือมีสต๊อกที่ตำแหน่งนั้น เก็บ `size` ตัวแรก), `high_value` (จัดอันดับ pool เดียวกันตาม `cost_per_unit` สูงสุดที่พบใน cost-layer receipt ระหว่างงวดบัญชีที่เปิดอยู่ปัจจุบันของ tenant โดยเลือกตัดสินค้าที่ต่ำกว่า `minimum_cost` ออกได้), และ `manual` (ผู้ใช้เลือกสินค้าเฉพาะเจาะจงผ่าน transfer picker สองคอลัมน์) `high_value` ต้องมี `tb_period` อย่างน้อยหนึ่งรายการที่ `status ∈ {open, locked}` มิเช่นนั้นการสร้างจะล้มเหลวด้วย `SPOT_CHECK_NO_ACTIVE_PERIOD` ("No active period found")
- **Eligible product pool**: ใช้ union logic เดียวกับ [physical-count](/th/inventory/physical-count) — สินค้าทุกตัวที่ assign ให้ตำแหน่งผ่าน `tb_product_location` บวกสินค้าใด ๆ ที่มีปริมาณสุทธิไม่เป็นศูนย์ใน `tb_inventory_transaction_detail` ที่ตำแหน่งนั้น ทำให้สินค้า "phantom stock" มีสิทธิ์ถูกสุ่มเสมอแม้ไม่ได้ assign อย่างเป็นทางการ
- **`on_hand_qty` ถูก snapshot ตอนสร้าง** (ต่างจาก physical-count ที่เริ่มที่ `0`): `create()` seed `on_hand_qty` ของแต่ละบรรทัดจากยอดสต๊อกสดของ pool ณ ตอนสุ่มตัวอย่าง จากนั้น **ถูกเขียนทับใหม่ด้วยยอดสดอีกครั้ง** ทันทีที่ผู้ใช้กด **Submit for Review** (`reviewItems()` คำนวณ `on_hand_qty` ใหม่ทุกบรรทัดจากยอดคงเหลือ ledger ปัจจุบัน โดยไม่มี date cut-off) — ดังนั้นตัวเลขที่ถูกเทียบจริงในหน้า review คือยอด ณ เวลา review ไม่ใช่ตอนสร้าง หากมีการเคลื่อนไหวสต๊อกอื่นที่ตำแหน่งนั้นในระหว่างนั้น
- **ไม่มีการตรวจความครบถ้วนที่ server** footer ของหน้า entry จะแสดง **Submit for Review** เมื่อทุกบรรทัดมีค่าที่กรอกในเครื่อง (`uncountedCount === 0`) เท่านั้น — แต่นี่เป็น UI gate ฝั่ง client เท่านั้น ทั้ง `reviewItems()` และ `submit()` ขั้นสุดท้ายไม่ปฏิเสธเอกสารที่ไม่ครบ — spot check ที่มีบางบรรทัดยังคง `actual_qty = 0` ที่ seed ไว้ สามารถ review และ submit ไปเป็น `completed` ได้โดยไม่มี block ใด ๆ ก็ไม่มี tolerance เปอร์เซ็นต์ threshold ปริมาณสัมบูรณ์ หรือกลไก recount ใด ๆ ในทั้ง frontend และ backend ของโมดูลนี้
- **Reset = void ไม่ใช่เริ่มใหม่** ปุ่ม **Reset** ที่แสดงเฉพาะใน section "Resume" ของรายการตำแหน่ง สำหรับตำแหน่งที่มี spot check `pending`/`in_progress` เรียก `POST /spot-checks/:id/reset` ซึ่งตั้ง `doc_status = void` โดยไม่มีเงื่อนไข (ปฏิเสธเฉพาะเมื่อเป็น `void` หรือ `completed` อยู่แล้ว) และ **ไม่** แตะต้อง `tb_spot_check_detail` แถวใดเลย — แม้ Bruno collection จะมี doc comment อธิบายว่า "clears all recorded actual quantities and resets... to draft state" เมื่อ void แล้ว ตำแหน่งจะกลับไปอยู่ bucket "Not Started" (`GET /spot-check/current` คืนเฉพาะเอกสาร `pending`/`in_progress` เป็น `latest_spot_check` ของตำแหน่ง) ดังนั้น "เริ่มใหม่" หลัง Reset หมายถึงสร้าง spot check ใหม่ทั้งหมด ไม่ใช่ resume ตัวที่ void ไปแล้ว

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| ผู้ปฏิบัติงาน spot check (ผู้ใช้ใดก็ตามที่มีสิทธิ์ `inventory_management.spot_check`) | Role เดียวที่ไม่แยกย่อยของโมดูลนี้: เริ่มการตรวจจากรายการตำแหน่ง เลือกวิธีสุ่มและ scope นับสินค้าที่สุ่มได้ submit เพื่อ review และยืนยัน submit ขั้นสุดท้าย |

ไม่พบ permission key, route, หรือ workflow stage แยกต่างหากสำหรับ Inventory Controller, Counter, Approver/Finance, Auditor หรือ Sysadmin — การแยก persona ที่บันทึกไว้ในดราฟต์ก่อนหน้าของ wiki module นี้ไม่มีอยู่จริงใน implementation ปัจจุบัน manual test-case catalog ของ frontend เอง (`../carmen-inventory-frontend-e2e/docs/test-cases/760-spot-check.md`) ตั้ง precondition ทุก scenario ให้เป็น "Store Manager" ทั่วไปเดียว สอดคล้องกับข้อค้นพบนี้ หน้าย่อยใน § 7 ด้านล่างยังคงการแบ่ง Inventory Controller / Counter / Audit-Config ไว้เป็นเครื่องมือจัดหน้าเท่านั้น (การกระทำของหน้าจอจริงเดียวกันมองจากสองมุม); `03-user-flow-audit-config.md` และ `04-test-scenarios-audit-config.md` เป็นหน้า correction สำหรับกลุ่มที่สามที่ยืนยันแล้วว่าไม่มีอยู่จริง

## 5. โมดูลที่เกี่ยวข้อง

**กระแสข้ามโมดูล:**
- [inventory](/th/inventory/inventory) — spot check เปรียบเทียบตัวอย่างของมันกับยอด ledger นี้ แต่ไม่เคยเขียนเข้าไปโดยตรง
- [inventory-adjustment](/th/inventory/inventory-adjustment) — ปลายทางที่ตั้งใจไว้ (แต่ไม่ automate) สำหรับแก้ไขผลต่างที่ยืนยันแล้ว — ไม่มีการเชื่อมโยงใด ๆ ระหว่างเอกสารของสองโมดูล
- [physical-count](/th/inventory/physical-count) — คู่เทียบการนับเต็ม เป็น document tree แยกต่างหาก ไม่ใช่ parent หรือ child ของกันและกัน

**การกำหนดค่าหลัก:**
- [master-data/unit](/th/inventory/master-data/unit) — หน่วยนับสำหรับแต่ละบรรทัด spot-check (`inventory_unit_id`)
- [master-data/location](/th/inventory/master-data/location) — ตำแหน่งที่ถูกสุ่มตรวจ และแหล่งที่มาของ flag `physical_count_type` ที่ (โดย default) กรองว่าตำแหน่งใดปรากฏในหน้ารายการ spot-check

## 6. แหล่งอ้างอิง

- Concepts: ไม่มี source folder `carmen/docs` สำหรับโมดูลนี้; มีเอกสารระดับวางแผนใน E2E repo (`docs/persona-doc/System Process/tx-10-spot-check.md`) ซึ่งข้อกล่าวอ้างหลัก "variance posting is pending, not yet implemented" ตรงกับโค้ดจริง แต่รายละเอียด status lifecycle (`draft`/`on-hold`/`cancelled`) ไม่ตรง — ดู [spot-check/02-business-rules](/th/inventory/spot-check/02-business-rules) § 5.1
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/spot-check/` (`sc-component.tsx`, `sc-form.tsx`, `sc-entry-component.tsx`, `sc-review-component.tsx`)
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/` (`spot-check.service.ts`, `spot-check.logic.ts`)
- API contracts: `../carmen-turborepo-backend-bruno/collections/carmen-inventory/inventory/spot-check/`
- E2E tests: `../carmen-inventory-frontend-e2e/` — ยังไม่มี Playwright spec สำหรับโมดูลนี้ (`ls tests/ | grep -i 'spot\|check'`); มี manual test-case catalog ที่ `docs/test-cases/760-spot-check.md` (32 cases เขียนจาก live component — สิ่งที่ใกล้เคียง executable spec ที่สุดของโมดูลนี้ แม้สอง scenario จะบรรยายหน้าจอ view/edit/delete ที่ routing ของแอปนี้ไปไม่ถึงจริง ดู [spot-check/04-test-scenarios](/th/inventory/spot-check/04-test-scenarios) § 5)

## 7. หน้าในโมดูลนี้

- [spot-check/01-data-model](/th/inventory/spot-check/01-data-model) — เอนทิตี ฟิลด์ ความสัมพันธ์ enum (`tb_spot_check`, `tb_spot_check_detail` พร้อม comment สองตาราง; enum สองตัว `enum_spot_check_status` / `enum_spot_check_method`)
- [spot-check/02-business-rules](/th/inventory/spot-check/02-business-rules) — การตรวจสอบ การคำนวณ การกำหนดสิทธิ์ การ posting กฎข้ามโมดูล (`SPC_VAL_*` / `SPC_CALC_*` / `SPC_AUTH_*` / `SPC_POST_*` / `SPC_XMOD_*`)
- [spot-check/03-user-flow](/th/inventory/spot-check/03-user-flow) — ภาพรวมวงจรชีวิตเอกสาร + สารบัญ persona
  - [spot-check/03-user-flow-inventory-controller](/th/inventory/spot-check/03-user-flow-inventory-controller) — หน้ารายการ + สร้าง
  - [spot-check/03-user-flow-counter](/th/inventory/spot-check/03-user-flow-counter) — หน้า entry + review
  - [spot-check/03-user-flow-audit-config](/th/inventory/spot-check/03-user-flow-audit-config) — หน้า correction: ไม่มี Approver/Auditor/Sysadmin surface
- [spot-check/04-test-scenarios](/th/inventory/spot-check/04-test-scenarios) — ภาพรวม test scenarios + scenario end-to-end + การ mapping กับ manual test-case catalog
  - [spot-check/04-test-scenarios-inventory-controller](/th/inventory/spot-check/04-test-scenarios-inventory-controller) — scenarios หน้ารายการ/สร้าง
  - [spot-check/04-test-scenarios-counter](/th/inventory/spot-check/04-test-scenarios-counter) — scenarios หน้า entry/review
  - [spot-check/04-test-scenarios-audit-config](/th/inventory/spot-check/04-test-scenarios-audit-config) — หน้า correction (สะท้อนหน้า correction ของ user-flow)

> **Status:** re-sync กับ frontend จริง (`sc-component.tsx`, `sc-form.tsx`, `sc-entry-component.tsx`, `sc-review-component.tsx`), backend (`spot-check.service.ts`, `spot-check.logic.ts`), Prisma schema และ Bruno collection ดราฟต์ก่อนหน้าของโมดูลนี้บรรยาย workflow สามระดับ persona ที่แต่งขึ้นทั้งหมด (Inventory Controller / Counter / Auditor+Sysadmin) พร้อม recount escalation, variance-tolerance threshold, และ rollup อัตโนมัติเข้า `tb_stock_in`/`tb_stock_out` พร้อม GL posting — ไม่มีสิ่งใดมีอยู่ในโค้ดจริง ทุก persona กฎ และ mermaid diagram ในหน้าย่อยทั้ง 10 หน้าถูกเขียนใหม่ตาม implementation จริงที่เป็น flow เดียว permission เดียว ยังไม่มี E2E Playwright spec สำหรับโมดูลนี้; manual test-case catalog (`docs/test-cases/760-spot-check.md`) เป็นเอกสารอ้างอิงเชิง executable ที่ใกล้เคียงที่สุดที่มีอยู่ และเอกสารระดับวางแผน (`docs/persona-doc/System Process/tx-10-spot-check.md`) คาดการณ์ถูกต้องในเรื่อง "ไม่มี variance posting" แต่ไม่ตรงกับ status lifecycle ที่แท้จริง — ดู [spot-check/02-business-rules](/th/inventory/spot-check/02-business-rules) § 5.1 สำหรับการเปรียบเทียบทีละจุด
