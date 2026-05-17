---
title: สูตรอาหาร (Recipe) — Test Scenarios — Procurement F&B Ops
description: test case ของ Procurement และ F&B Ops (การขนาด PO, การทดแทน, การอนุมัติ menu-item linkage, menu engineering) สำหรับโมดูล recipe
published: true
date: 2026-05-17T12:00:00.000Z
tags: recipe, test-scenarios, procurement-fb-ops, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# สูตรอาหาร (Recipe) — Test Scenarios — Procurement F&B Ops

> **At a Glance**
> **Persona:** Procurement / F&B Ops (Procurement Department + F&B Operations Manager) &nbsp;·&nbsp; **โมดูล:** [[recipe]] &nbsp;·&nbsp; **scenario:** ~25
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **การครอบคลุม E2E:** ไม่มีสำหรับภายในสูตร; การ automate ใกล้เคียงใน [[purchase-order]] ครอบคลุมด้าน PO ของ flow PF-HP-02 ใน `../carmen-inventory-frontend-e2e/`

หน้านี้บันทึก test scenario ที่ persona Procurement / F&B Ops ขับเคลื่อนตรงในโมดูล `recipe` Procurement เป็น read-only บนสูตร (`recipe:read` ตาม `REC_AUTH_010`) — พวกเขาบริโภค demand สูตรเพื่อขนาด PO และแสดงคำขอทดแทน แต่ไม่เขียนกับสูตร F&B Ops เพิ่มถือ `recipe:approve-menu-link` ตาม `REC_AUTH_011` — พวกเขาอนุมัติ menu-item linkage บนสูตรที่ Chef ได้ publish และเป็นเจ้าของการตัดสินใจ menu engineering scenario จัดกลุ่มเป็น **happy path** (Procurement รวม demand สูตร portfolio → ขนาด PO; ช่องคำขอทดแทน; การอนุมัติ menu-item linkage ของ F&B Ops; review menu engineering รายไตรมาส) **RBAC** (Procurement พยายามแก้สูตร; F&B Ops พยายามแก้วัตถุดิบ) **validation** (negative test รอบ pricing สูตรไม่ครบที่อนุมัติ menu-link วัตถุดิบขาดที่ขนาด PO) และ **edge case** รอบ cost drift portfolio-wide menu item หลายสูตร menu cycle ตามฤดูกาล handoff ข้าม persona ที่ pivot จาก persona นี้ (Scenario 1, 4 ใน parent overview) อยู่ใน [04-test-scenarios.md](./04-test-scenarios.md) ไม่ใช่ที่นี่

## 1. Happy Path

| # | Scenario | Pre-condition | ขั้นตอน | คาดหวัง |
| - | -------- | ------------- | ----- | -------- |
| PF-HP-01 | Procurement รวม demand สูตร portfolio | Tenant มี 50 outlet, 200 สูตร `PUBLISHED`, ยอดขายคาดการณ์สำหรับ 7 วันถัดไป | 1. Procurement เปิดมุมมองการรวม demand 2. เลือกขอบเขต (7 วันถัดไป) ทุก outlet 3. ระบบ trigger explosion demand ข้ามทุก outlet × ยอดขายคาดการณ์ × สูตรที่ link ตาม `REC_CALC_014` 4. Net demand ต่อสินค้า (gross − on-hand ที่คลังกลาง − PO in-flight − สต๊อกความปลอดภัย) | demand วัตถุดิบระดับ portfolio คำนวณ; recursion จัดการ sub-recipe; แสดง net demand per-product; พื้นฐานสำหรับการขนาด PO ประสิทธิภาพ: การรวมเสร็จในเวลาที่ tenant ยอมรับได้แม้มี 200 สูตร × 50 outlet |
| PF-HP-02 | Procurement ยก PO ขนาดด้วย demand สูตร | PF-HP-01 ผลิต net demand บน `Premium Beef` สำหรับ 200 kg ใน 7 วัน | 1. Procurement สร้าง PO เทียบกับ `Vendor-Premium-Meats` สำหรับ 200 kg + buffer ความปลอดภัย 2. PO ตาม flow procurement ปกติ (นอกโมดูล recipe ตาม [[purchase-order]]) | PO สร้างพร้อม rationale การขนาด recipe-driven; โมดูล recipe เป็น input demand; วงจรชีวิตของ PO อยู่ในโมดูล procurement |
| PF-HP-03 | คำขอทดแทน → Chef revise | Vendor flag stock-out ที่จะเกิดบนข้าวพิเศษสำหรับ 30 วันถัดไป; ข้าวใช้ใน 5 สูตรที่ publish Procurement เสนอทดแทน jasmine rice ที่ +5% cost | 1. Procurement เปิดช่องคำขอทดแทน 2. Log: "Vendor X ไม่สามารถ supply ข้าวพิเศษ 30 วัน; ทดแทน jasmine rice มีที่ +5% สูตรที่ได้รับผลกระทบ: A, B, C, D, E" 3. Chef รับคำขอ 4. Chef ประเมินและอย่างใดอย่างหนึ่ง revise แต่ละสูตรตาม `REC_POST_004` (in-place ด้วย versioning, swap วัตถุดิบ) หรือประสานการหยุดเมนูชั่วคราว | คำขอทดแทน log ในช่องปฏิบัติการ; การเป็นเจ้าของของ Chef บนการ revise สูตร; สูตรที่ได้รับผลกระทบอย่างใดอย่างหนึ่ง swap (พร้อมแถว `tb_recipe_version` ใหม่และแถว `tb_recipe_pricing_history` สำหรับการเปลี่ยน cost) หรือหยุด (ไม่มีการเปลี่ยนสถานะของสูตร; ผลกระทบเมนู) |
| PF-HP-04 | F&B Ops อนุมัติ menu-item linkage บนสูตรใหม่ | Chef ได้ publish สูตร `Wagyu Burger` (`PUBLISHED`); F&B Ops review สำหรับการเพิ่มเมนู | 1. F&B Ops เปิดรายละเอียดสูตร 2. Review cost (`cost_per_portion = ฿380`), margin (`gross_margin_percentage = 31%` กับ `selling_price = ฿550`), fit ของเมนู (fit niche burger premium complement House Burger ที่มีอยู่), fit ของ brand (aligned กับ concept dining upscale ของโรงแรม) 3. คลิก **Approve Menu Linkage** 4. Menu-item สร้างใน POS-integration layer link กับสูตร | ตาม `REC_AUTH_011` Linkage อนุมัติ; บันทึกนอก schema สูตร (ตาม `REC_XMOD_008`); สูตรไม่เปลี่ยนจาก action ของ F&B Ops; สูตรขับเคลื่อน theoretical OUT บนการขายเมนูของ `Wagyu Burger` แล้ว |
| PF-HP-05 | F&B Ops ปฏิเสธ menu-item linkage | Chef ได้ publish `Experimental Dish`; F&B Ops review และตัดสินใจว่าไม่ fit เมนู | 1. F&B Ops เปิดรายละเอียดสูตร 2. Review: cost ดี margin OK แต่ fit cuisine ผิด (จาน fusion บนเมนูที่ italian อย่างเข้มงวด) 3. คลิก **Reject Menu Linkage** พร้อมโน้ต feedback "ไม่ fit concept เมนู Italian; พิจารณาใหม่เป็นจานพิเศษ / banquet" 4. Chef รับ feedback | สูตรยังคง `PUBLISHED` แต่ไม่มี menu-item linkage สร้าง; Chef อาจ submit อีกครั้งพร้อมการ revise หรือยอมรับการปฏิเสธ |
| PF-HP-06 | F&B Ops review menu engineering รายไตรมาส | จบไตรมาส; 200 menu item × สูตร; ข้อมูลยอดขายและ margin มี | 1. F&B Ops เปิด dashboard menu engineering 2. รวมข้อมูล per-recipe: ปริมาณการขาย `actual_food_cost_percentage`, `gross_margin_percentage`, variance 3. มุมมอง matrix: high-margin/high-volume (star) high-margin/low-volume (puzzle) low-margin/high-volume (workhorse) low-margin/low-volume (dog) 4. การตัดสินใจต่อ quadrant: star รักษา workhorse cost-engineer (escalate ไปยัง Chef + Cost Controller) dog drop (คำขอ archive ไปยัง Chef) | การตัดสินใจ menu engineering บันทึกใน dashboard ปฏิบัติการ; สูตรที่ได้รับผลกระทบได้ action ติดตาม: Chef revise workhorse สำหรับ cost วัตถุดิบ Cost Controller ปรับราคาบน star Chef archive dog ตาม `REC_POST_007` |

## 2. Permission / Authorization

| # | Scenario | พฤติกรรมที่คาดหวัง (allow/deny + เหตุผล) |
| - | -------- | --------------------------------------- |
| PF-PERM-01 | Procurement อ่าน recipe library | **Allow** ตาม `REC_AUTH_010` การอ่าน library เต็มข้ามทุกสถานะ (โดยทั่วไป); ใช้สำหรับการขนาด PO และการวางแผนทดแทน |
| PF-PERM-02 | Procurement พยายามแก้ฟิลด์สูตรใด | **Deny — read-only** ตาม `REC_AUTH_010` ทุก endpoint แก้ปฏิเสธ คำขอทดแทนเป็นช่องปฏิบัติการ ไม่ใช่การเขียน schema |
| PF-PERM-03 | F&B Ops อนุมัติ menu-item linkage | **Allow** ตาม `REC_AUTH_011` การอนุมัติบันทึกใน POS-integration layer (นอก schema สูตร) |
| PF-PERM-04 | F&B Ops พยายามแก้วัตถุดิบ | **Deny — Chef-only** F&B Ops มี `recipe:approve-menu-link` แต่ไม่มี `recipe:edit` API call ตรง return `"You are not authorized to edit recipes; that authority is the Chef's."` |
| PF-PERM-05 | F&B Ops พยายามแก้ pricing | **Deny — Cost-Controller-only** F&B Ops collaborate กับ Cost Controller บนการตัดสินใจราคาแต่ไม่แก้ `selling_price` โดยตรง; เป็นอำนาจของ Cost Controller ตาม `REC_AUTH_006` |
| PF-PERM-06 | F&B Ops พยายาม publish สูตร | **Deny — Chef-only** Publish ต้องการ `recipe:publish` ที่อยู่ด้าน Chef F&B Ops อนุมัติ menu-link ไม่ใช่ publish |
| PF-PERM-07 | F&B Ops ขอ archive สูตร | **คำขอปฏิบัติการต่อ Chef** F&B Ops ไม่ archive โดยตรง (ตาม `REC_AUTH_004` — archive เป็น Chef-only); F&B Ops ตัดสินใจปลดประจำการ menu item และขอให้ Chef archive สูตร |

## 3. Validation / Error

| # | Scenario | Trigger | Error ที่คาดหวัง |
| - | -------- | ------- | -------------- |
| PF-VAL-01 | F&B Ops พยายามอนุมัติ menu-link บนสูตร `DRAFT` | Chef ยังไม่ publish; F&B Ops พยายามอนุมัติ | **Reject — สูตรต้อง `PUBLISHED` ก่อน** Server return `"Menu-item linkage can only be approved on PUBLISHED recipes; recipe is currently DRAFT."` |
| PF-VAL-02 | F&B Ops พยายามอนุมัติ menu-link บนสูตร `ARCHIVED` | สูตรถูก archive; F&B Ops พยายาม relink | **Reject** Server return `"Archived recipes cannot be linked to menu items. Clone the recipe to a new DRAFT, re-publish, and try again."` |
| PF-VAL-03 | การ explode demand ของ Procurement เทียบกับสูตร `ARCHIVED` ที่ยัง link กับ menu item | anomaly ข้อมูล: สูตร archive แต่ menu-item linkage ไม่ตัด | **Warn / fallback** โมดูล recipe return สถานะ archive; production-planning layer อย่างใดอย่างหนึ่ง fall back ไปเวอร์ชันก่อนหรือยกเว้น menu item; Procurement แจ้งเตือนให้ประสานกับ F&B Ops บนการ clean linkage |
| PF-VAL-04 | F&B Ops พยายามอนุมัติ menu-link เมื่อ pricing สูตรไม่ครบ | สูตร `PUBLISHED` แต่ `selling_price IS NULL` (เช่น สูตร ingredients-only ตั้งใจเป็น sub-recipe) | **Warn — confirm** Server return `"Recipe has no selling price set; confirm this menu link is for a non-priced item (e.g. part of a combo)."` (Sub-recipe โดยทั่วไปไม่ link กับ menu item; นี่คือ edge case) |
| PF-VAL-05 | คำขอทดแทน submit โดยไม่มี list สูตรที่ได้รับผลกระทบ | Procurement ยกการทดแทนแต่ไม่ list สูตรไหนได้รับผลกระทบ | **Reject (การ validate ปฏิบัติการ)** UI คำขอทดแทนต้องการ list สูตรที่ได้รับผลกระทบเพื่อขับเคลื่อนการประเมินของ Chef |

## 4. Edge Cases

| # | Scenario | เงื่อนไข | คาดหวัง |
| - | -------- | --------- | -------- |
| PF-EDGE-01 | Menu item หลายสูตร (combo) | Menu item `Combo Burger Meal` ประกอบ 3 สูตร (burger, fries, drink) | F&B Ops อนุมัติ menu-item linkage ที่อ้างอิงทั้ง 3 สูตร; event การขายเมนู explode ทั้ง 3 สูตรตาม `REC_CALC_014`; OUT movement เชิงทฤษฎี fan out สำหรับวัตถุดิบทั้งหมดข้าม 3 สูตร Logic linkage อยู่ใน POS-integration layer |
| PF-EDGE-02 | Cost drift portfolio-wide trigger menu engineering | โมดูล Costing emit drift บนวัตถุดิบ staple หลายตัว (น้ำมัน แป้ง น้ำตาล); 80% ของสูตร `actual_food_cost_percentage` เกินเป้าหมาย | F&B Ops trigger การ review menu-engineering พิเศษ; collaboration กับ Cost Controller บนกลยุทธ์ราคา portfolio-wide (เพิ่มราคา ยอมรับ margin ลด drop item ที่ได้รับผลกระทบมากที่สุด); การ revise วัตถุดิบด้าน Chef เป็นการตอบสนอง cycle ที่ยาวกว่า |
| PF-EDGE-03 | Transition เมนูตามฤดูกาล | จบ Q3 transition ไปเมนู Q4; 30 สูตรที่จะปลดประจำการ (พิเศษ Q3) 30 สูตรใหม่ที่เพิ่ม (พิเศษ Q4) | Chef archive สูตร Q3 ตาม `REC_POST_007`; Chef publish สูตร Q4 ตาม `REC_POST_003`; F&B Ops batch-approve menu-item linkage สำหรับ Q4; Procurement re-size PO สำหรับ mix วัตถุดิบใหม่ |
| PF-EDGE-04 | การเปลี่ยน vendor สำหรับวัตถุดิบ high-fanout | Procurement สลับจาก Vendor A เป็น Vendor B สำหรับ `Premium Olive Oil` เนื่องจากการรวม vendor; cost เปลี่ยน +3% | การ update pricelist vendor ไหลผ่านโมดูล costing → event cost-drift ของโมดูล recipe ตาม `REC_XMOD_006`; สูตร refresh; Cost Controller flag สูตรที่ได้รับผลกระทบ; F&B Ops review ว่าจะดูดซับ (ไม่มีการเปลี่ยนเมนู) หรือส่งผ่าน (การปรับราคาบนจานที่ได้รับผลกระทบ) |
| PF-EDGE-05 | การอนุมัติสูตรใหม่ที่ margin off-target | Chef publish `Signature Dish` ที่ 38% % food-cost จริง (target 32%); Cost Controller co-approve ตาม `REC_AUTH_007`; F&B Ops ตอนนี้ตัดสินใจบน menu-item linkage | F&B Ops เห็น margin off-target ในรายละเอียดสูตร; review rationale กลยุทธ์ ("signature dish"); อนุมัติ menu linkage แม้ margin off-target การอนุมัติ document; menu item เริ่มขับเคลื่อนยอดขายที่ margin ต่ำกว่าปกติ |
| PF-EDGE-06 | ประสิทธิภาพ Demand-explosion ด้วยการซ้อน sub-recipe ลึก | การรวม portfolio ข้าม 200 สูตร; 50 สูตรใช้ sub-recipe; sub-recipe บางตัวลึก 3 ระดับ | Recursion การรวมเสร็จในเวลาที่ tenant ยอมรับได้; recursion bound โดยความลึกการซ้อน per-recipe (โดยทั่วไป < 4 ระดับในทางปฏิบัติ) การ test regression ประสิทธิภาพยืนยัน < 5s สำหรับการรวม portfolio 200-recipe |
| PF-EDGE-07 | F&B Ops ขอการปลดประจำการ batch | ที่จบของฤดูกาล 25 สูตรต้องการ archive | F&B Ops compile list การปลดประจำการ; Chef batch-archive ผ่าน UI หรือ API ตาม `REC_POST_007`; แต่ละ archive เขียนแถว `tb_recipe_version` ของตัวเองด้วย `change_summary = "batch-archived — Q3 seasonal retirement"`; menu-item linkage ตัดสำหรับแต่ละ |

## 5. แหล่งอ้างอิง

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — handoff ข้าม persona ที่ pivot จาก Procurement / F&B Ops: Scenario 1 (happy path เต็มรวมการอนุมัติ menu-item linkage), Scenario 4 (คำขอทดแทนของ Procurement)
- User flow: [03-user-flow-procurement-fb-ops.md](./03-user-flow-procurement-fb-ops.md) — แหล่ง happy-path สำหรับ Section 1 ด้านบน; อธิบาย primary flow 10 ขั้นตอน (Procurement: รวม → validate → ยก PO → ทดแทน; F&B Ops: review → อนุมัติ / ปฏิเสธ → menu engineering → signoff)
- กฎทางธุรกิจที่ verify: [02-business-rules.md](./02-business-rules.md) Section 3 — `REC_CALC_014` (สูตร demand-explosion ที่ Procurement ใช้); Section 4 — `REC_AUTH_010`–`REC_AUTH_011` (scope อำนาจ Procurement / F&B Ops); Section 6 — `REC_XMOD_008` (menu-item linkage เป็น application-layer ไม่อยู่ใน schema สูตร)
- spec E2E: **ไม่มีสำหรับภายในสูตร**; การ automate ใกล้เคียงใน `[[purchase-order]]` ครอบคลุมด้าน PO ของ flow PF-HP-02
- Cross-link: [[purchase-order]] — เอกสารปลายน้ำหลักของ Procurement; demand ที่ recipe-driven ขนาด PO
- Cross-link: [[vendor-pricelist]] — ข้อมูล cost ของ vendor เป็น input ต้นน้ำของ cost สินค้า แล้ว cost สูตร
- Cross-link: [[costing]] — F&B Ops review ข้อมูล cost ที่มาจากโมดูล costing
