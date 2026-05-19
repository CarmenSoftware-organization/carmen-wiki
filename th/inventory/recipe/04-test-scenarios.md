---
title: สูตรอาหาร (Recipe) — Test Scenarios
description: test case ตาม persona, scenario ข้าม persona และ mapping Playwright สำหรับโมดูล recipe
published: true
date: 2026-05-17T12:00:00.000Z
tags: recipe, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# สูตรอาหาร (Recipe) — Test Scenarios

> **At a Glance**
> **โมดูล:** [[recipe]] &nbsp;·&nbsp; **scenario รวม:** ~14 ข้าม persona + drill-down ต่อ persona ข้ามทุก persona &nbsp;·&nbsp; **Persona ที่ครอบคลุม:** Chef, Cost Controller, Outlet Manager, Procurement / F&B Ops, Audit / Config
> **ลำดับการรัน:** การตั้งค่า Audit / Config → happy path ของ persona หลัก → scenario ข้าม persona
> **drill-down ของแต่ละ persona อยู่ที่ `04-test-scenarios-<role>.md`**

## 1. ภาพรวม

หน้านี้เป็น **จุดเข้าภาพรวม** สำหรับชุด test-scenario ของโมดูล `recipe` รวบรวมการครอบคลุม recipe ตาม 5 persona ที่โต้ตอบกับ recipe library ข้ามวงจรชีวิตของมัน (Chef, Cost Controller, Outlet Manager, Procurement / F&B Ops, Audit / Config) จัดทำคลังไฟล์ test ต่อ persona จับ scenario handoff ข้าม persona ที่เย็บเส้นทางบุคคลเข้าด้วยกัน และระบุสถานะการครอบคลุม E2E ขอบเขตจงใจกว้างกว่า functional pass บริสุทธิ์: ไฟล์แต่ละ persona รวม **happy path เชิงฟังก์ชัน** (create / save / publish / archive; การแก้ cost-only; flow การทดแทน; การอนุมัติ menu-item linkage; config admin) **RBAC / กรณีปฏิเสธ permission** (chef ที่ไม่มี `recipe:publish`; cost controller พยายามแก้วัตถุดิบ; outlet manager พยายามเขียน; auditor พยายามเขียน) **edge case** (recipe ใหญ่ — วัตถุดิบและขั้นตอนมาก; sub-recipe ซ้อนลึก; yield variant ด้วยปริมาณขั้น; การแก้พร้อมกัน; กรณีมุมความแม่นยำทศนิยม) และ **trace versioning / pricing-history** (ทุกการเปลี่ยนต่อ recipe ที่ `PUBLISHED` เขียนแถว `tb_recipe_version`; การแก้ cost-only เขียนแถว `tb_recipe_pricing_history`; chain audit verify ได้จากตารางเหล่านั้น)

scenario ข้าม persona ใน Section 4 เป็นชั้น integration เหนือ suite ต่อ persona พวกเขาอธิบาย journey end-to-end ที่ข้าม boundary ของ handoff ที่บันทึกใน [03-user-flow.md](./03-user-flow.md) Section 4 — เช่น *Chef สร้าง → Cost Controller co-approve การ publish off-target → Chef publish → F&B Ops อนุมัติ menu-item linkage → สูตรขับเคลื่อน theoretical consumption* Section 5 ระบุ **สถานะการครอบคลุมอัตโนมัติ** — ในเวลาที่เขียน **ไม่มีไฟล์ `recipe.spec.ts` Playwright เฉพาะใน suite carmen-inventory-frontend-e2e** (verify โดย `ls ../carmen-inventory-frontend-e2e/tests/ | grep -i 'recipe\|menu'` return ว่าง) ดังนั้นไฟล์ test ต่อ persona อธิบาย scenario ที่ปัจจุบันเป็น **manual / planned** สำหรับการ automate E2E การ automate ที่อยู่ใกล้เคียงมีอยู่ใน `[[store-requisition]]` (`701-sr.spec.ts`) ซึ่งครอบคลุมเส้นทาง recipe-driven SR auto-create ทางอ้อม (`info.recipe_id` back-reference) แต่การครอบคลุม E2E ภายในสูตรเป็นช่องว่าง

## 2. Persona ในขอบเขต

- **Chef**: Chef / Kitchen Manager (+ subset Kitchen Staff read-only); author สูตร; publish, archive; ดูแล sub-recipe; revise ตอบสนอง feedback / cost drift
- **Cost Controller**: Cost Controller (+ Cost Control Department); review rollup cost, margin เป้าหมาย, ราคาขาย; ติดตาม drift; co-approve การ publish off-target; รันรายงาน variance
- **Outlet Manager**: Outlet Manager; ผู้บริโภคด้าน demand; ยก SR จาก demand สูตร; ติดตาม variance ของ outlet; ส่ง feedback issue ให้ Chef
- **Procurement / F&B Ops**: Procurement Department (การขนาด PO การมีอยู่ของวัตถุดิบ คำขอทดแทน) + F&B Operations Manager (การอนุมัติ menu-item linkage เชิงกลยุทธ์, menu engineering)
- **Audit / Config**: Sysadmin (หมวดหมู่ cuisine อุปกรณ์ RBAC นโยบาย tenant การ wire integration) + Auditor (versioning / pricing-history / signature trace อ่านอย่างเดียว)

## 3. ไฟล์ Test ของ Persona

- [Chef scenarios](./04-test-scenarios-chef.md)
- [Cost Controller scenarios](./04-test-scenarios-cost-controller.md)
- [Outlet Manager scenarios](./04-test-scenarios-outlet-manager.md)
- [Procurement / F&B Ops scenarios](./04-test-scenarios-procurement-fb-ops.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. scenario ข้าม Persona / Handoff

ตารางด้านล่างเป็นชั้น integration แต่ละแถวคลุมอย่างน้อยหนึ่ง handoff จาก [03-user-flow.md](./03-user-flow.md) Section 4 และจบด้วยสูตรในสถานะ terminal หรือ steady "Personas in order" รายการ actor ในลำดับการ execute; "Pre-condition" จับสถานะระบบที่ต้องการเพื่อเริ่ม; "Expected end state" anchor `status` ของสูตรและผลกระทบปลายน้ำ (แถว versioning แถว pricing-history menu-item linkage theoretical-consumption fan-out)

| # | Scenario | Persona ตามลำดับ | Pre-condition | สถานะสิ้นสุดที่คาดหวัง |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | Happy path เต็ม — recipe ใหม่จาก create ถึง menu-item linkage | Chef → F&B Ops | Tenant มีหมวดหมู่ `Mains` ตั้งค่าด้วย % food-cost เป้าหมาย 32; chef มี `recipe:create / edit / publish` บน `Mains`; F&B Ops มี `recipe:approve-menu-link` | Recipe `PUBLISHED`; แถว `tb_recipe_version` v1 ด้วย `published = true`; แถว `tb_recipe_pricing_history` ที่ snapshot การ publish; menu-item linkage อนุมัติใน POS-integration layer; สูตรเริ่มขับเคลื่อน theoretical OUT บนการขายเมนูตาม `REC_XMOD_003` |
| 2 | การ publish margin off-target ต้องการ co-approval ของ Cost Controller | Chef → Cost Controller → Chef | Recipe ใน `DRAFT` ด้วย `actual_food_cost_percentage = 38%` vs `target_food_cost_percentage = 32%` เกิน tolerance 2-percentage-point ของ tenant; นโยบาย tenant เปิดใช้ `REC_AUTH_007` | การ publish เริ่มต้นบล็อก; Cost Controller review และ co-approve พร้อมโน้ตใน `change_summary`; chef publish; แถว `tb_recipe_version` v1 ด้วย `change_summary = "co-approved off-target by Cost Controller: signature dish, accept lower margin"` |
| 3 | การ cascade cost ของ sub-recipe trigger re-cost บนสูตร parent | (System-driven แสดงต่อ Cost Controller) | Sub-recipe `Burger Sauce` เป็น `PUBLISHED` และใช้เป็นวัตถุดิบบนสามสูตร parent; cost mayonnaise (สินค้าบน sub-recipe) เพิ่ม 40% ผ่านการ update pricelist vendor ไหลผ่านไปยัง costing | `cost_per_portion` ของ Sub-recipe คำนวณใหม่; สูตร parent 1–3 คิดต้นทุนใหม่ atomically ตาม `REC_POST_006`; แต่ละ parent ได้แถว `tb_recipe_pricing_history` ด้วย `change_reason = "sub-recipe cost cascade from Burger Sauce"`; dashboard Cost Controller แสดง parent ที่ `actual_food_cost_percentage` ตอนนี้เกิน tolerance |
| 4 | คำขอทดแทนของ Procurement → Chef revise | Procurement → Chef | วัตถุดิบ high-volume (เช่น ข้าวพิเศษ) flag โดย Procurement ว่าไม่มีใน 30 วันถัดไป; กระทบ 5 สูตรที่ publish; ทดแทนเสนอที่ +5% cost | Chef รับคำขอทดแทน; อย่างใดอย่างหนึ่ง (a) swap วัตถุดิบบนแต่ละสูตรที่ได้รับผลกระทบผ่าน `REC_POST_004` (in-place ด้วย versioning; แต่ละสูตรได้แถว `tb_recipe_version` ใหม่ + `tb_recipe_pricing_history` สำหรับการเปลี่ยน cost) หรือ (b) ประสานการหยุดเมนูชั่วคราวบนจานที่ได้รับผลกระทบ; Cost Controller ติดตามผลกระทบ margin หลัง swap |
| 5 | Outlet Manager feedback บน issue การควบคุม portion | Outlet Manager → Chef | Recipe `Premium Steak` เป็น `PUBLISHED`; dashboard variance ของ outlet แสดง variance บวกที่ยังคงอยู่บนวัตถุดิบ steak — kitchen จัดจาน 250g แต่สูตรระบุ 220g | Outlet Manager log feedback ผ่านช่องปฏิบัติการ; Chef สอบสวนกับ kitchen ตัดสินใจว่าจะ (a) revise สูตรเป็น 250g (สูตร under-spec; `REC_POST_004` ด้วยเวอร์ชันใหม่) หรือ (b) เสริมสร้างวินัยการจัดจานกับ Kitchen Staff (สูตรถูก; action แก้ไขเป็นปฏิบัติการ) variance ของ outlet ปิดใน period ถัดไป |
| 6 | การ auto-create SR ที่ recipe-driven สำหรับ event banquet | โมดูล Recipe (auto-create) → Outlet Manager → flow SR | Outlet มี event banquet สำหรับ 200 cover book ศุกร์หน้า; menu item link กับ 4 สูตร; สูตรเป็น `PUBLISHED` | โมดูล Recipe คำนวณ demand วัตถุดิบ × 200 cover ตาม `REC_CALC_014`; post SR `draft` ด้วย `info.recipe_id` (หรือ `info.event_id`) ที่ outlet; Outlet Manager review ปรับ และ submit ตาม flow [[store-requisition]]; SR เคลื่อนผ่านการอนุมัติและ fulfilment ปกติ; variance ที่ปิด period vs demand ที่ auto-compute ปรากฏใน dashboard variance |
| 7 | การแก้ in-place บนสูตร `PUBLISHED` ด้วย versioning | Chef | Recipe `House Burger` เป็น `PUBLISHED` ที่เวอร์ชัน 1; chef revise ปริมาณ patty จาก 1 เป็น 1.2 เพื่อ address feedback portion | การแก้ใช้ in-place ตาม `REC_POST_004`; rollup cost คำนวณใหม่; `tb_recipe_version` v2 เขียนด้วย `published = true`, `change_summary = "increased patty qty to 1.2 per outlet feedback"`; แถว `tb_recipe_pricing_history` เขียนด้วย `change_reason = "ingredient qty revision"`; theoretical consumption จากการขายเมนูถัดไปไปใช้สูตร v2 |
| 8 | Un-publish round-trip สำหรับการ overhaul ใหญ่ | Chef | Recipe `Seasonal Curry` เป็น `PUBLISHED`; chef วางแผน overhaul ครอบคลุม (rebalance วัตถุดิบ เขียนวิธีใหม่ pricing ใหม่); นโยบาย tenant: ต้องการ un-publish สำหรับการแก้ใหญ่ | Chef un-publish (`PUBLISHED → DRAFT` ตาม `REC_POST_008`); ทำการแก้ในสัปดาห์หน้า; re-publish ตาม `REC_POST_003` (เขียนแถว `tb_recipe_version` ใหม่ v2 ด้วย `published = true`, `change_summary = "seasonal refresh — Q3 2026"`); menu item ที่ link จัดการตามนโยบาย POS-integration ระหว่างหน้าต่าง `DRAFT` |
| 9 | Archive ที่การปลดประจำการเมนู | F&B Ops → Chef | Recipe `Holiday Special` เป็น menu item เวลาจำกัด; ฤดูกาลวันหยุดจบ; F&B Ops ตัดสินใจปลดประจำการ | Chef archive สูตรตาม `REC_POST_007`: `PUBLISHED → ARCHIVED`, `archived_at = now()`; แถว `tb_recipe_version` สุดท้ายเขียนด้วย `change_summary = "archived — limited-time menu retired"`; menu-item linkage ตัด; สูตรไม่ขับเคลื่อน theoretical consumption บนการขายใหม่; event theoretical-consumption ประวัติใน inventory ledger รักษาสำหรับ audit |
| 10 | การเปลี่ยน RBAC ของ Sysadmin กระทบงาน chef in-flight | Sysadmin → persona ทั้งหมด | Tenant ตัดสินใจจำกัด Pastry Chef ไปยังหมวด Desserts เท่านั้น (ก่อนเป็น library เต็ม); 3 สูตร `DRAFT` in-flight โดย Pastry Chef อยู่ใน `Mains` | Sysadmin commit การเปลี่ยน RBAC; กฎใหม่ใช้ prospectively; สูตร `DRAFT` in-flight โดย Pastry Chef ใน `Mains` กลายเป็น read-only ต่อพวกเขา (ต้องการ Executive Chef เข้ามา edit); Sysadmin ประสานกับ Cost Controller / F&B Ops บน transition; งานที่ได้รับผลกระทบอย่างใดอย่างหนึ่ง re-assign หรือเสร็จผ่าน override |
| 11 | Audit sample — verify chain versioning | Auditor | Sample 30 สูตร `PUBLISHED` ข้าม period สำหรับ compliance review | แต่ละสูตรมี chain `tb_recipe_version` จาก v1 (publication) ผ่านแต่ละการแก้; `published_at` match timestamp v1; การ publish off-target มี co-approval บันทึกใน `change_summary`; การเปลี่ยน cost / ราคามีแถว `tb_recipe_pricing_history` ที่สอดคล้องด้วย `change_reason` populate; คอลัมน์ audit (`created_by_id` / `updated_by_id`) สอดคล้องกัน Audit findings log |
| 12 | Sub-recipe ซ้อนลึก (3 ระดับ) | Chef | Recipe `Composite Plate` ใช้ sub-recipe `Sauce Au Poivre` ซึ่งเองใช้ sub-recipe `Brown Stock` ซึ่งใช้สินค้าใบไม้ `Beef Bones` | Theoretical-consumption fan-out บนการขายเมนูซ้อน 3 ระดับลึกตาม `REC_XMOD_004`: สูตร parent → sub-recipe Sauce Au Poivre → sub-recipe Brown Stock → สินค้า `Beef Bones`; OUT movement post เทียบกับ `Beef Bones` ที่ outlet การ cascade cost ก็ซ้อน: การเปลี่ยน cost บน `Beef Bones` ไหลขึ้นผ่าน `Brown Stock` → `Sauce Au Poivre` → `Composite Plate`; แต่ละระดับได้แถว `tb_recipe_pricing_history` |
| 13 | Cost-drift cascade บนวัตถุดิบ high-fanout | Cost Controller | สินค้าเดียว `Premium Olive Oil` ใช้ใน 25 สูตร; cost เพิ่ม 18%; tolerance ของ tenant สำหรับ trigger cost-drift คือ ±5% | โมดูล Costing emit event cost-drift ตาม `REC_XMOD_006`; โมดูล recipe refresh `cost_per_unit` บนทุกบรรทัดที่อ้างอิงสินค้า (ข้ามทั้ง 25 สูตร); เขียนแถว `tb_recipe_pricing_history` ต่อสูตรที่ได้รับผลกระทบด้วย `change_reason = "cost-drift update from costing module"`; 8 สูตรที่ `actual_food_cost_percentage` ใหม่เกิน target+tolerance flag สำหรับการ review ของ Cost Controller |
| 14 | การแก้พร้อมกันโดยสอง chef บน `DRAFT` เดียวกัน | Chef + deputy | สอง chef (Executive Chef + Sous Chef เป็น deputy) แก้สูตร `DRAFT` เดียวกันพร้อมกัน; ทั้งคู่พยายาม save | Optimistic-concurrency: save แรกชนะ (เขียน `updated_at` / `updated_by_id`); save ที่สองถูกปฏิเสธบนการตรวจจับ conflict (server return 409); chef ที่สอง refresh เห็นการแก้ของ save แรก ตัดสินใจว่าจะ merge หรือ override Schema สูตรไม่มีคอลัมน์ `doc_version` บน `tb_recipe` โดยตรงแต่นโยบาย tenant อาจใช้ timestamp `updated_at` สำหรับการตรวจสอบ concurrency |

## 5. การ Map Test E2E

ในเวลาที่เขียน **ไม่มีไฟล์ `recipe.spec.ts` Playwright เฉพาะใน `../carmen-inventory-frontend-e2e/tests/`** (verify โดย `ls ../carmen-inventory-frontend-e2e/tests/ | grep -i 'recipe\|menu'` return ว่าง) scenario ภายในสูตรในหน้านี้และไฟล์ test ต่อ persona จึงเป็น **manual / planned** สำหรับการ automate E2E; การครอบคลุมที่ automate ใกล้เคียงที่สุดคือ:

| spec E2E ใกล้เคียง | การครอบคลุมที่เกี่ยวข้องกับสูตร |
| ----------------- | ----------------------- |
| `701-sr.spec.ts` (store-requisition) | Scenario 6 (recipe-driven SR auto-create) ครอบคลุมบางส่วน — ด้าน SR ของ flow (`info.recipe_id` back-reference วงจรชีวิต SR ปกติ) ถูก exercise; trigger ด้านสูตร (โมดูล recipe post SR draft) ถูก mock หรือข้ามที่ boundary ของ test |
| (None) | Scenario 1–5, 7–14 document เป็น manual / planned |

ช่องว่างเทียบกับ Section 4: ทั้ง 14 scenario ข้าม persona เป็นช่องว่างสำหรับการ automate E2E เต็ม ไฟล์ test ระดับ persona document scenario ด้วยรายละเอียดเพียงพอสำหรับการ execute manual หรือการพัฒนา spec Playwright ในอนาคต Priority สำหรับการ automate อนาคต: Scenario 1 (happy path เต็ม), Scenario 2 (co-approval off-target), Scenario 7 (การแก้ in-place ด้วย versioning), Scenario 3 (sub-recipe cascade), Scenario 9 (archive)

## 6. แหล่งอ้างอิง

- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4 — handoff ข้าม persona ที่ขับเคลื่อน scenario integration ด้านบน
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 — กฎ posting ที่อ้างที่ทุกการเปลี่ยนสถานะและผลกระทบปลายน้ำ (publish, edit-published, cost cascade, archive)
- รายละเอียดต่อ persona: [Chef](./04-test-scenarios-chef.md), [Cost Controller](./04-test-scenarios-cost-controller.md), [Outlet Manager](./04-test-scenarios-outlet-manager.md), [Procurement / F&B Ops](./04-test-scenarios-procurement-fb-ops.md), [Audit / Config](./04-test-scenarios-audit-config.md)
- การครอบคลุม E2E ใกล้เคียง: `../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts` (ครอบคลุมด้าน SR ของ recipe-driven auto-create ทางอ้อมผ่าน `info.recipe_id`)
- โมดูลที่เกี่ยวข้อง: [[product]] (feed วัตถุดิบ), [[inventory]] (เป้าหมาย theoretical-consumption fan-out), [[costing]] (cost-drift ต้นน้ำ), [[store-requisition]] (auto-create ปลายน้ำ)
