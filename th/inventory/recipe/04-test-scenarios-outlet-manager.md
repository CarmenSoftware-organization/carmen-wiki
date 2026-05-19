---
title: สูตรอาหาร (Recipe) — Test Scenarios — Outlet Manager
description: test case ของ Outlet Manager (การบริโภค read-only, explosion demand, variance, feedback) สำหรับโมดูล recipe
published: true
date: 2026-05-19T23:55:00.000Z
tags: recipe, test-scenarios, outlet-manager, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# สูตรอาหาร (Recipe) — Test Scenarios — Outlet Manager

> **At a Glance**
> **Persona:** Outlet Manager (read-only บน recipe library) &nbsp;·&nbsp; **โมดูล:** [recipe](/th/inventory/recipe) &nbsp;·&nbsp; **scenario:** ~23
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **การครอบคลุม E2E:** ไม่มีสำหรับภายในสูตร; `tests/701-sr.spec.ts` ครอบคลุมด้าน SR ของ recipe-driven auto-create ใน `../carmen-inventory-frontend-e2e/`

หน้านี้บันทึก test scenario ที่ persona Outlet Manager ขับเคลื่อนตรงในโมดูล `recipe` Outlet Manager เป็น **read-only บน recipe library** (`recipe:read` ตาม `REC_AUTH_009`); การโต้ตอบของ persona กับสูตรเป็นปลายน้ำ — ใช้ recipe explosion เพื่อวางแผนการดึงวัตถุดิบ ติดตาม variance ของ outlet ที่ขับเคลื่อนบางส่วนโดยความถูกต้องของสูตร และส่ง feedback issue การควบคุม portion / ความถูกต้องให้ Chef revise scenario จัดกลุ่มเป็น **happy path** (อ่านรายละเอียดสูตรในมุมมอง outlet; explosion การผลิตที่วางแผน; auto-create SR จาก demand สูตร; review variance ของ outlet; การ submit recipe-feedback) **RBAC** (Outlet Manager พยายามเขียน scope การอ่านข้าม outlet) **validation** (negative test รอบความถูกต้องของ forecast สูตร demand-zero) และ **edge case** รอบ event banquet demand รูปแบบ par-level top-up การใช้สูตรหลาย outlet handoff ข้าม persona ที่ pivot จาก Outlet Manager (Scenario 5, 6 ใน parent overview) อยู่ใน [04-test-scenarios.md](./04-test-scenarios.md) ไม่ใช่ที่นี่

## 1. Happy Path

| # | Scenario | Pre-condition | ขั้นตอน | คาดหวัง |
| - | -------- | ------------- | ----- | -------- |
| OM-HP-01 | อ่านรายละเอียดสูตร `PUBLISHED` ที่ outlet | Recipe `House Burger` เป็น `PUBLISHED`; Outlet Manager มี `recipe:read` scope ไปยังสูตรที่ใช้ใน outlet `Main-Kitchen` | 1. Outlet Manager เปิด recipe library filter ไปยัง outlet 2. ค้นหา `House Burger` 3. เปิดรายละเอียดสูตร 4. Review list วัตถุดิบ วิธี อุปกรณ์ การจัดจาน yield | รายละเอียดสูตรแสดงใน read-only mode; ทุกฟิลด์มองเห็น (วัตถุดิบพร้อมปริมาณ ขั้นตอนวิธีพร้อมสื่อ yield สารก่อภูมิแพ้ tag ตัวเลข cost); ไม่มีการควบคุมแก้; UI สะท้อน scope `recipe:read` sub-role Kitchen Staff มี surface เดียวกันสำหรับการ execute บริการ |
| OM-HP-02 | Explosion demand สำหรับการผลิตประจำวัน | Outlet มี forecast สำหรับพรุ่งนี้: 50 House Burger + 30 Caesar Salad + 20 Pasta Carbonara; แต่ละ link กับสูตร `PUBLISHED` หนึ่งตัว | 1. เปิดมุมมองการวางแผนการผลิตสำหรับ outlet 2. Trigger explosion demand 3. ระบบอ่านบรรทัดวัตถุดิบของสูตร × ปริมาณคาดการณ์ตาม `REC_CALC_014`; รวมต่อสินค้า 4. แสดง list การดึง (หนึ่งแถวต่อสินค้า ปริมาณรวมในหน่วยสต๊อก on-hand ปัจจุบันที่ outlet net demand) | Explosion demand รวมปริมาณวัตถุดิบอย่างถูกต้องข้ามสูตร; บรรทัด sub-recipe ซ้อนไปยังสินค้าใบไม้ตาม `REC_XMOD_004`; ใช้ wastage; ใช้การ conversion UoM; net demand = คาดการณ์ − on-hand − ที่ reserve list การดึงเป็นพื้นฐานสำหรับการสร้าง SR |
| OM-HP-03 | Auto-create SR `draft` จาก demand event banquet | Outlet มี event banquet book สำหรับ 200 cover ศุกร์หน้า; menu item link กับ 4 สูตร `PUBLISHED`; tenant มีการ wire auto-create เปิดใช้ตาม `REC_XMOD_007` | 1. รายละเอียด event banquet persist พร้อมจำนวน cover menu item recipe linkage 2. โมดูล Recipe คำนวณ demand วัตถุดิบ × 200 cover 3. โมดูล Recipe post SR `draft` ที่ outlet `Main-Kitchen` เทียบกับ source `Central Store` ด้วย `info.recipe_id = "EVENT-2026-05-22-001"` 4. Outlet Manager เปิด draft SR review ปริมาณ ปรับ และ submit | SR `draft` สร้างด้วยปริมาณวัตถุดิบที่คำนวณ; `info.recipe_id` รักษา end-to-end; flow Outlet Manager ดำเนินต่อตาม [store-requisition](/th/inventory/store-requisition) (`SR_POST_001` ขึ้นไป); variance ที่ปิด period เทียบกับ demand ที่ recipe-compute ปรากฏใน dashboard variance ของ outlet |
| OM-HP-04 | Review variance ของ outlet | สูตร `PUBLISHED` ทั้งหมดที่ใช้ใน outlet `Main-Kitchen` ขับเคลื่อน OUT movement เชิงทฤษฎีระหว่าง period `2026-05`; SR / physical-count / adjustment post movement จริง | 1. เปิด dashboard variance ของ outlet 2. Filter ไปยัง outlet `Main-Kitchen`, period `2026-05` 3. ดู per-ingredient ทฤษฎี vs จริง; sort ตามจำนวน variance 4. Drill เข้า variance ที่ใหญ่ที่สุด | Dashboard แสดง variance per-ingredient สำหรับ outlet; drill-down per-recipe (สูตรไหนมีส่วนร่วมใน variance ไหน); drill-down per-ingredient (สินค้าไหนมี over/under consumption) Outlet Manager ประเมินว่า variance เป็นการควบคุม portion (action ของตัวเอง) หรือ recipe-attributable (escalate ไปยัง Chef) |
| OM-HP-05 | Submit recipe-feedback ไปยัง Chef | Outlet Manager สังเกต variance บวกที่ยังคงอยู่บน `Premium Steak` (kitchen จัดจาน 250g สูตรระบุ 220g) | 1. เปิดสูตร `Premium Steak` ใน read-only mode 2. คลิก **Submit Feedback** (ช่อง feedback — UI ต่างกัน นอก schema สูตร) 3. กรอก: "Variance ที่ยังคงอยู่บน portion steak — kitchen จัดจาน 250g vs สูตร 220g อย่างใดอย่างหนึ่ง revise สูตรเป็น 250g หรือเสริมสร้างการจัดจาน 220g กับพนักงานครัว" 4. Submit | Feedback log ในช่องปฏิบัติการ (in-app comment, ticket หรือการแจ้งเตือน); Chef รับ feedback; สูตรไม่เปลี่ยนจาก action ของ Outlet Manager (chef อาจ revise ภายหลังตาม `REC_POST_004`); Outlet Manager ติดตาม variance ของ period ถัดไปสำหรับการ resolve |

## 2. Permission / Authorization

| # | Scenario | พฤติกรรมที่คาดหวัง (allow/deny + เหตุผล) |
| - | -------- | --------------------------------------- |
| OM-PERM-01 | Outlet Manager อ่านสูตร `PUBLISHED` ที่ใช้ใน outlet | **Allow** ตาม `REC_AUTH_009` UI แสดงรายละเอียดสูตรใน read-only mode |
| OM-PERM-02 | Outlet Manager พยายามแก้ header / วัตถุดิบ / ขั้นตอนของสูตร | **Deny — read-only** ทุก endpoint แก้ปฏิเสธด้วย `"Outlet Manager role is read-only on the recipe library; submit feedback to the Chef instead."` |
| OM-PERM-03 | Outlet Manager พยายาม publish หรือ archive | **Deny** endpoint การเปลี่ยนสถานะปฏิเสธด้วย `"You are not authorized to change recipe status; this authority is the Chef's."` |
| OM-PERM-04 | Outlet Manager อ่านสูตร `DRAFT` | **Deny — ตาม default** นโยบาย tenant โดยทั่วไปจำกัดการอ่านของ Outlet Manager เป็นสูตร `PUBLISHED` เท่านั้น (draft เป็น author-in-progress และยังไม่พร้อมสำหรับมุมมอง outlet) บาง tenant อนุญาตการอ่านทุกสถานะ; default คือ `PUBLISHED` เท่านั้น |
| OM-PERM-05 | Outlet Manager อ่านสูตรที่ใช้ที่ outlet ต่าง | **Allow (โดยทั่วไป)** Recipe library โดยทั่วไป library-wide read; มุมมอง outlet-scope เป็น filter ไม่ใช่การจำกัด บาง tenant อาจจำกัดการอ่าน cross-outlet (เช่น สำหรับโรงแรมที่มีครัว brand-segmented); default คือเปิดอ่าน |
| OM-PERM-06 | Outlet Manager สร้าง SR จาก demand auto-create | **Allow** SR อยู่ในโมดูล [store-requisition](/th/inventory/store-requisition) ไม่ใช่โมดูล recipe; อำนาจการสร้าง SR ของ Outlet Manager ควบคุมโดย `SR_AUTH_001` ของ SR |
| OM-PERM-07 | sub-role Kitchen Staff พยายามเขียน | **Deny — read-only** Kitchen Staff มี `recipe:read` เท่านั้น UI ซ่อนการควบคุมแก้ทั้งหมด; ความพยายามเขียน API ตรงถูกปฏิเสธ |

## 3. Validation / Error

| # | Scenario | Trigger | Error ที่คาดหวัง |
| - | -------- | ------- | -------------- |
| OM-VAL-01 | Explosion demand เทียบกับสูตร `ARCHIVED` | มุมมองการวางแผนของ outlet manager อ้างอิง menu item ที่ link กับสูตรที่ถูก archive ตั้งแต่นั้น | **Warn / fallback** โมดูล recipe return สถานะ archive พร้อมคำเตือน; production-planning layer อย่างใดอย่างหนึ่ง fall back ไปเวอร์ชัน publish ก่อน (ผ่าน `tb_recipe_version`) หรือยกเว้น menu item จาก explosion; Outlet Manager แจ้งเตือนให้ update linkage menu |
| OM-VAL-02 | Explosion demand เทียบกับสูตร `DRAFT` | สูตรถูก un-publish กลาง planning-cycle (เช่น สำหรับการ revise) | **Warn / fallback** คล้าย OM-VAL-01; สูตรไม่มีสิทธิ์สำหรับการขับเคลื่อน theoretical-consumption ขณะใน `DRAFT`; production-planning layer fall back หรือยกเว้น |
| OM-VAL-03 | Forecast พองตัว → SR ขนาดใหญ่ | Outlet Manager กรอก forecast 500 cover (capacity จริง 200) ผิดพลาด; explosion demand ผลิต SR ขนาดใหญ่ | **ความกังวลปฏิบัติการ ไม่ใช่ system error** ระบบคำนวณถูกต้องเมื่อให้ input; SR อาจถูกปฏิเสธที่อนุมัติ (ตามกฎ `[store-requisition](/th/inventory/store-requisition)`) เนื่องจากข้อจำกัด on-hand ของ source หรืองบประมาณ Outlet Manager แก้ไข forecast ในรอบถัดไป |
| OM-VAL-04 | สูตรที่ `cost_per_portion = 0` | สูตร `PUBLISHED` มี cost ศูนย์โดยบังเอิญ (anomaly ข้อมูล) | **การคำนวณ variance flag anomaly** Theoretical consumption ยิงถูกต้อง (issue บนมิติ cost ไม่ใช่ปริมาณ) Outlet Manager เห็นสูตรใน review variance ด้วย cost = 0 และ escalate ไปยัง Cost Controller / Chef |

## 4. Edge Cases

| # | Scenario | เงื่อนไข | คาดหวัง |
| - | -------- | --------- | -------- |
| OM-EDGE-01 | event Banquet ด้วยแหล่งสูตรผสม (บางใหม่ บาง legacy) | banquet 200-cover ใช้ 5 menu item: 3 จากเมนูปัจจุบัน (สูตร `PUBLISHED`) 2 จากสูตรพิเศษ / one-off | Explosion demand จัดการทั้ง 5; auto-create SR (หรือ list การดึงปฏิบัติการ) รวมอย่างถูกต้อง; วัตถุดิบ sub-recipe ข้าม 5 deduplicate ที่สินค้าเดียวกันปรากฏ (`Σ qty` ต่อสินค้าข้ามสูตร) |
| OM-EDGE-02 | Par-level top-up vs SR ที่ recipe-driven | Outlet ใช้ par-level top-up สำหรับ commodity fast-moving (น้ำตาล แป้ง น้ำมัน) และ SR ที่ recipe-driven สำหรับ item high-value (เนื้อพรีเมียม ชีสพิเศษ) | สอง flow SR coexist: SR par-level (ขนาดด้วย par − on-hand วัตถุดิบทีละตัว) และ SR ที่ recipe-driven (ขนาดด้วย demand × สูตร) Outlet Manager ตัดสินใจต่อวัตถุดิบ / ต่อ outlet |
| OM-EDGE-03 | สูตรที่แชร์ multi-outlet — variance เฉพาะ outlet | Recipe `House Burger` เป็น `PUBLISHED` และใช้ที่ 3 outlet; outlet A มี variance outlet B และ C ไม่มี | Dashboard variance แสดง variance per-outlet; สูตรเหมือนกันข้าม outlet ดังนั้น variance เป็นปฏิบัติการ (การควบคุม portion ที่ outlet A) ไม่ใช่ recipe-attributable Outlet Manager A เป็นเจ้าของ action แก้ไข; Chef อาจรับ feedback แต่ไม่น่า revise สูตร (จะกระทบ B และ C) |
| OM-EDGE-04 | SR ที่ recipe-driven ด้วย sub-recipe recursion | Recipe `Composite Plate` ใช้ sub-recipe `Sauce Au Poivre` ที่ใช้ sub-recipe `Brown Stock` Banquet demand สำหรับ 200 cover | Explosion demand ซ้อนผ่าน sub-recipe ตาม `REC_XMOD_004`; list การดึงสุดท้ายมีปริมาณสินค้าใบไม้; SR ขนาดถูกต้องแม้มีการซ้อน 3 ระดับ |
| OM-EDGE-05 | การ explode สูตรเมื่อวัตถุดิบหนึ่งบนสูตร inactive | บรรทัดบนสูตร `PUBLISHED` อ้างอิงสินค้าที่ถูก soft-delete ตั้งแต่นั้น (anomaly ข้อมูล; ควรถูกบล็อกที่เวลา recipe-edit) | **Warn** Production-planning แสดง issue: "Recipe `X` อ้างอิงสินค้า inactive `Y`; บรรทัดยกเว้นจาก explosion demand" Outlet Manager escalate ไปยัง Chef สำหรับการ revise สูตร; chef swap วัตถุดิบหรือสูตรหยุด |
| OM-EDGE-06 | สูตรที่มี yield variant — demand variant-specific | สูตรที่มี variant `Small`, `Medium`, `Large`; outlet มี forecast: 30 Small + 50 Medium + 20 Large = 100 burger (demand variant-specific) | Explosion demand เคารพ variant scope: บรรทัดวัตถุดิบ variant-scope (`tb_recipe_ingredient.tb_recipe_yield_variantId`) ใช้เฉพาะ variant ของพวกเขา; บรรทัดที่ไม่ scope scale ต่อ `conversion_rate` ของ variant; list การดึงสุดท้ายสะท้อนปริมาณ variant-specific ถูกต้อง |
| OM-EDGE-07 | มุมมองมือถือ Kitchen Staff ระหว่างบริการ | Kitchen Staff บนอุปกรณ์มือถือ กลางบริการ อ่านขั้นตอนสูตร | มุมมอง recipe มือถือ load สูตร `PUBLISHED` ด้วยรูป ขั้นตอนวิธี คำแนะนำการจัดจาน; read-only; การแสดงขั้นตอนตามลำดับ; ไม่มีการควบคุมแก้ ตาม spec mobile-app |

## 5. แหล่งอ้างอิง

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — handoff ข้าม persona ที่ pivot จาก Outlet Manager: Scenario 5 (feedback บนการควบคุม portion), Scenario 6 (recipe-driven SR auto-create สำหรับ banquet)
- User flow: [03-user-flow-outlet-manager.md](./03-user-flow-outlet-manager.md) — แหล่ง happy-path สำหรับ Section 1 ด้านบน; อธิบาย primary flow 8 ขั้นตอน (planning → explosion demand → SR → บริการ → variance → feedback)
- กฎทางธุรกิจที่ verify: [02-business-rules.md](./02-business-rules.md) Section 3 — `REC_CALC_014` (สูตร theoretical-consumption / demand-explosion); Section 4 — `REC_AUTH_009` (scope read-only ของ Outlet Manager); Section 6 — `REC_XMOD_003` (theoretical OUT fan-out trigger โดยการขายเมนู), `REC_XMOD_004` (sub-recipe recursion), `REC_XMOD_007` (auto-create SR จาก demand สูตร)
- spec E2E: **ไม่มีสำหรับภายในสูตร**; `701-sr.spec.ts` ครอบคลุมด้าน SR ของเส้นทาง recipe-driven auto-create (trigger จากสูตร → SR อยู่ที่ boundary ของ test)
- Cross-link: [store-requisition](/th/inventory/store-requisition) — เอกสารปลายน้ำหลักที่ Outlet Manager author จาก demand สูตร
- Cross-link: [inventory](/th/inventory/inventory) — การกระทบยอด on-hand ของ outlet กับการใช้เชิงทฤษฎีที่ recipe-driven คือการคำนวณ food-cost-variance
- Cross-link: [inventory-adjustment](/th/inventory/inventory-adjustment) — movement แก้ไขสำหรับ shrinkage / spoilage flag โดยการสอบสวน variance
