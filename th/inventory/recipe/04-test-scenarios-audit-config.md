---
title: สูตรอาหาร (Recipe) — Test Scenarios — Audit & Config
description: test case ของ System Administrator และ Auditor (config, RBAC, audit versioning, audit pricing-history, สุขภาพ integration) สำหรับโมดูล recipe
published: true
date: 2026-05-19T23:55:00.000Z
tags: recipe, test-scenarios, audit-config, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# สูตรอาหาร (Recipe) — Test Scenarios — Audit & Config

> **At a Glance**
> **Persona:** Audit / Config (System Administrator config + Auditor read-only) &nbsp;·&nbsp; **โมดูล:** [recipe](/th/inventory/recipe) &nbsp;·&nbsp; **scenario:** ~31
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **การครอบคลุม E2E:** ไม่มีสำหรับภายในสูตร; การตรวจสอบสุขภาพ integration แยกจาก E2E สูตรใน `../carmen-inventory-frontend-e2e/`

หน้านี้บันทึก test scenario ที่ persona Audit / Config — ประกอบด้วย **System Administrator** (หมวดหมู่ cuisine equipment master, RBAC, นโยบาย tenant บน publish gate / un-publish / co-approval, การ wire integration กับ `[product](/th/inventory/product)` / `[inventory](/th/inventory/inventory)` / `[store-requisition](/th/inventory/store-requisition)`) และ **Auditor** (versioning / pricing-history / signature trace อ่านอย่างเดียว; compliance review) — ขับเคลื่อนตรงในโมดูล `recipe` ต่างจาก 4 persona ปฏิบัติการ (Chef, Cost Controller, Outlet Manager, Procurement / F&B Ops) ที่ทำงานวงจรชีวิต happy-path sub-role Audit / Config ทำ action บน **periphery**: ก่อนสูตรใดอยู่ (config) ระหว่างวงจรชีวิต (การบังคับใช้ RBAC สุขภาพ integration) และหลัง publish (audit trace การ verify signature) Sysadmin มี read / write เต็มบนตาราง config และการ map RBAC; Auditor เป็น read-only บน `tb_recipe_version`, `tb_recipe_pricing_history` และคอลัมน์ audit ต่อแถว ไม่มีเส้นทาง "void" หรือ "admin-cancel" บนสูตร — สุขภาพข้อมูลบนสูตรที่ archive หลังช่วงเวลาการเก็บข้อมูลเป็นอำนาจ delete เดียว และอยู่กับ Sysadmin ตาม `REC_AUTH_014` scenario จัดกลุ่มเป็น **happy path** (master หมวดหมู่ / cuisine / อุปกรณ์; RBAC; นโยบาย tenant; สุขภาพ integration; auditor sample; auditor compliance review; soft-delete archived) **RBAC** (อำนาจ Sysadmin; auditor read-only) **validation** (negative test รอบ master ไม่ครบ orphan reference in-flight) และ **edge case** รอบ config multi-tenant soft-delete ที่ช่วงเวลาการเก็บข้อมูล การ reconstruct chain versioning handoff ข้าม persona ที่ pivot จาก persona นี้ (Scenario 10, 11 ใน parent overview) อยู่ใน [04-test-scenarios.md](./04-test-scenarios.md) ไม่ใช่ที่นี่

## 1. Happy Path

| # | Scenario | Pre-condition | ขั้นตอน | คาดหวัง |
| - | -------- | ------------- | ----- | -------- |
| AC-HP-01 | Sysadmin ตั้งค่า category master | Tenant onboarding; Sysadmin มีอำนาจ config เต็ม | 1. เปิด Sysadmin → Recipe Category Master 2. สร้างหมวด `Mains` (ไม่มี parent, level 1) 3. เพิ่ม sub-category `Premium Mains`, `Standard Mains` (parent = Mains, level 2) 4. ตั้ง `default_cost_settings` per category (% food-cost เป้าหมาย % labor / overhead) 5. Save | แถว `tb_recipe_category` persist พร้อมลำดับชั้นผ่าน `parent_id`; `level` populate ถูกต้อง; สูตรใหม่ในแต่ละหมวดจะสืบทอด `default_cost_settings` ที่เวลา create |
| AC-HP-02 | Sysadmin ตั้งค่า cuisine master | Tenant มี cuisine `Thai`, `Italian`, `French` | 1. เปิด Cuisine Master 2. สร้างแต่ละ cuisine ด้วย tag `region` (`ASIA` / `EUROPE`), `popular_dishes`, `key_ingredients` 3. Save | แถว `tb_recipe_cuisines` persist; constraint `@@unique([name, deleted_at])` ป้องกันซ้ำ; region-tag เปิดใช้การ filter ตาม region |
| AC-HP-03 | Sysadmin ตั้งค่า RBAC | Sysadmin กำหนด Executive Chef `recipe:create / edit / publish / archive / edit-published` บนทุกหมวดหมู่; Pastry Chef บน Desserts เท่านั้น; Cost Controller `recipe:read / edit-cost / read-history` บนทั้งหมด; Outlet Manager `recipe:read` เท่านั้น | 1. เปิด matrix RBAC 2. สำหรับแต่ละ role × category ตั้ง permission 3. กำหนด user ให้ role 4. Save | RBAC mapping persist; permission บังคับใช้บน API call ภายหลังต่อ scope role / category; session in-flight refresh ที่ request ถัดไป |
| AC-HP-04 | Sysadmin ตั้งนโยบาย tenant (publish gate, edit-published, co-approval) | การตัดสินใจนโยบาย tenant: เปิดใช้ `REC_AUTH_007` co-approval ที่ tolerance 2-pp; เปิดใช้ `edit_published_with_versioning = true` (in-place edit บน `PUBLISHED`) | 1. เปิด Tenant Policy 2. Toggle `publish_gate_off_target_co_approval = true`; ตั้ง `off_target_tolerance_percentage_points = 2` 3. Toggle `edit_published_with_versioning = true` 4. Save | ค่านโยบาย persist; การ publish / แก้ภายหลัง gate ตามนโยบาย; สูตรที่มีอยู่ใน flight อาจต้องการการประเมินใหม่ภายใต้นโยบายใหม่ (การประสานด้วยมือ) |
| AC-HP-05 | Sysadmin wire integration | ยืนยันว่าการ coupling ต้นน้ำและปลายน้ำปฏิบัติการ | 1. เปิด Integration Health dashboard 2. Verify: chain vendor pricelist → product cost → recipe cost-drift (`REC_XMOD_005` / `REC_XMOD_006`); recipe → SR auto-create (`REC_XMOD_007`); recipe → inventory theoretical OUT fan-out (`REC_XMOD_003`); recipe → menu-item linkage (`REC_XMOD_008`) 3. รัน probe health-check integration | ทุก chain รายงานสุขภาพดี; ความล้มเหลวใดแสดง alert; Sysadmin สอบสวนต่อ chain (เช่น event listener พังบน cost-drift POS endpoint mis-wire บน menu-item linkage) |
| AC-HP-06 | Auditor sample — verify chain versioning | Sample 30 สูตร `PUBLISHED` สำหรับ period audit | 1. เปิด Auditor → Recipe History view 2. สำหรับแต่ละสูตรที่ sample: verify chain `tb_recipe_version` (v1 ที่ publication; v_n สำหรับแต่ละการแก้ภายหลัง); verify `published_at` match v1; verify การ publish off-target มี co-approval บันทึกใน `change_summary`; verify การเปลี่ยน cost / ราคามีแถว `tb_recipe_pricing_history`; verify คอลัมน์ audit (`created_by_id` / `updated_by_id`) สอดคล้องกัน | ตาม `REC_AUTH_013` Auditor พบ chain สะอาดบน 28 จาก 30 sample; 2 sample มี audit findings (เช่น `change_summary` ขาดบนการแก้; แถว pricing-history ขาดบนการแก้ cost-only) ซึ่ง log และ escalate ไปยัง Sysadmin / Cost Controller สำหรับการสอบสวน |
| AC-HP-07 | Auditor compliance review บน sub-recipe cascade | Sample 10 สูตรที่ `tb_recipe_pricing_history.change_reason` บ่งบอก sub-recipe cascade | 1. สำหรับแต่ละสูตรที่ sample: trace chain cascade จาก entry pricing-history ของสูตร parent กลับไปยังการเปลี่ยน cost ของ sub-recipe กลับไปยังการ update cost ของสินค้าใบไม้ต้นกำเนิด 2. Verify ว่า math cascade สอดคล้องภายใน 3. Verify ว่า margin post-cascade เคลื่อนนอก tolerance trigger การ review ของ Cost Controller / Chef (signoff หรือการ revise ใน `tb_recipe_version`) | Trace cascade สอดคล้องภายในบนทั้ง 10 sample; 3 sample ที่ margin post-cascade เกิน tolerance มี action review ของ Cost Controller ที่เหมาะสมใน chain audit |
| AC-HP-08 | Sysadmin soft-delete สูตรที่ archive หลังการเก็บข้อมูล | สูตร `ARCHIVED` `Holiday 2022 Special` ถูก archive 3 ปี (นโยบายการเก็บข้อมูล tenant: 2 ปี) | 1. เปิดรายการสูตรที่ archive 2. Filter ตาม `archived_at < 2024-01-01` 3. เลือกสูตรสำหรับ soft-delete 4. Bulk soft-delete | `deleted_at` populate บนแถวที่เลือก; แถวยังคงใน database (audit ได้); หายจาก query default; แถว `tb_recipe_version` รักษา (cascade-on-delete ไม่ soft-aware) |

## 2. Permission / Authorization

| # | Scenario | พฤติกรรมที่คาดหวัง (allow/deny + เหตุผล) |
| - | -------- | --------------------------------------- |
| AC-PERM-01 | Sysadmin แก้ master หมวดหมู่ / cuisine / อุปกรณ์ | **Allow** ตาม `REC_AUTH_012` การเขียนเต็มบนตารางข้อมูลหลัก |
| AC-PERM-02 | Sysadmin แก้ matrix RBAC | **Allow** ตาม `REC_AUTH_012` RBAC เป็น Sysadmin-only |
| AC-PERM-03 | Sysadmin แก้นโยบาย tenant (publish gate, edit-published, tolerance co-approval) | **Allow** ตาม `REC_AUTH_012` |
| AC-PERM-04 | Sysadmin พยายามแก้วัตถุดิบ / ขั้นตอนของสูตร | **Allow (โดยทั่วไป) แต่ผิดปกติ** Sysadmin มี permission ทั้งหมดในเชิงเทคนิคใน role ที่มีสิทธิ์เต็ม; ในทางปฏิบัติพวกเขาไม่แก้วัตถุดิบ (เป็นอำนาจของ Chef) Audit findings flag การเขียนของ Sysadmin บนฟิลด์ปฏิบัติการของสูตรเป็น anomaly |
| AC-PERM-05 | Auditor อ่านประวัติ `tb_recipe_version` | **Allow** ตาม `REC_AUTH_013` permission `recipe:read-history` |
| AC-PERM-06 | Auditor อ่าน `tb_recipe_pricing_history` | **Allow** ตาม `REC_AUTH_013` |
| AC-PERM-07 | Auditor พยายามเขียน | **Deny — read-only** ทุก endpoint เขียนปฏิเสธด้วย `"Auditor role is read-only on the recipe library."` |
| AC-PERM-08 | Sysadmin soft-delete สูตร `PUBLISHED` | **Deny — ต้อง archive ก่อน** สูตร `PUBLISHED` ไม่สามารถ soft-delete; ต้อง archive ตาม `REC_AUTH_014` |
| AC-PERM-09 | Sysadmin soft-delete สูตร `ARCHIVED` ภายในช่วงเวลาการเก็บข้อมูล | **Deny — การละเมิดการเก็บข้อมูล** นโยบายการเก็บข้อมูล tenant บล็อก soft-delete ของสูตรที่ archive ภายในช่วงเวลาการเก็บข้อมูล; UI บล็อก operation; API call ตรง return `"Cannot soft-delete recipe within retention period (archived less than N days ago)."` |

## 3. Validation / Error

| # | Scenario | Trigger | Error ที่คาดหวัง |
| - | -------- | ------- | -------------- |
| AC-VAL-01 | Sysadmin พยายาม soft-delete หมวดหมู่ที่ถูกอ้างอิงโดยสูตร | หมวด `Mains` ถูกอ้างอิงโดย 50 สูตร `PUBLISHED`; Sysadmin พยายาม soft-delete | **Reject (FK Restrict + การตรวจสอบ soft-delete ของ application)** Server return `"Cannot delete category 'Mains' — it is referenced by 50 active recipes. Reassign recipes to a different category first."` |
| AC-VAL-02 | Sysadmin พยายามลบ cuisine ที่ถูกอ้างอิงโดยสูตร | คล้าย AC-VAL-01 สำหรับ `tb_recipe_cuisines` | **Reject** Server return error analog |
| AC-VAL-03 | การเปลี่ยน RBAC orphan งาน chef in-flight | Sysadmin ลบ `recipe:edit` สำหรับ Pastry Chef บน `Mains` ขณะ 3 สูตร `DRAFT` โดย Pastry Chef อยู่ใน `Mains` | **Warn ที่ save** UI แสดง: "การเปลี่ยนนี้ orphan 3 สูตร DRAFT in-flight โดย Pastry Chef ใน Mains ดำเนินการ?" Sysadmin อย่างใดอย่างหนึ่งยอมรับ (สูตร orphan กลายเป็น read-only ต่อ Pastry Chef; ต้องการ Executive Chef takeover) หรือยกเลิก |
| AC-VAL-04 | การเปลี่ยนนโยบาย tenant สร้างสูตรไม่สอดคล้อง | Sysadmin เปิดใช้ `publish_gate_off_target_co_approval = true` กับ tolerance 2pp; สูตร `PUBLISHED` บางตัว off-target ที่ 5pp drift | **Warn — สูตรเดิม grandfather** สูตร `PUBLISHED` ที่มีอยู่ไม่ถูก gate retroactively; การ publish / แก้ใหม่ใช้นโยบายใหม่ Sysadmin ประสานกับ Cost Control Department ว่าจะ review สูตร off-target retroactively หรือไม่ |
| AC-VAL-05 | การตรวจสอบสุขภาพ integration ล้มเหลวบน theoretical-consumption fan-out | chain recipe → inventory theoretical OUT พัง (event listener crash) | **Alert** Health dashboard แสดง "Theoretical-consumption fan-out FAILING; การขายเมนูไม่ขับเคลื่อน recipe-explosion movement" Sysadmin สอบสวนและ restart listener / fix integration |
| AC-VAL-06 | Auditor finding — แถวเวอร์ชันขาดบนการแก้ | Auditor พบสูตรที่ `updated_at` เปลี่ยนหลายครั้งตั้งแต่ `published_at` แต่ chain `tb_recipe_version` มีแถวเดียว | **Audit finding — สอบสวน** Finding บ่งบอกอย่างใดอย่างหนึ่ง (a) gap ระบบ versioning (การแก้ใช้โดยไม่เขียนแถวเวอร์ชัน — Sysadmin สอบสวน service code) หรือ (b) พฤติกรรมที่ตั้งใจ (เช่น การแก้ pricing-only ไม่ trigger แถวเวอร์ชัน — verify การแก้ทั้งหมดเป็น pricing-only ผ่าน `tb_recipe_pricing_history`) |

## 4. Edge Cases

| # | Scenario | เงื่อนไข | คาดหวัง |
| - | -------- | --------- | -------- |
| AC-EDGE-01 | Config multi-tenant — หมวดหมู่และนโยบาย per-tenant | Tenant A มีหมวด `Appetiser / Main / Dessert`; Tenant B มี `Starter / Course / Sweet` | การ scope per-tenant ผ่าน header `x-app-id`; ข้อมูลหลักสูตรเป็น tenant-scope; query filter ตาม tenant; การรั่ว config cross-tenant ถูกบล็อกที่ boundary auth |
| AC-EDGE-02 | การเปลี่ยน RBAC bulk ข้าม user หลายคน | Sysadmin reassign 50 chef ให้ category scope ใหม่ (เช่น เปิด 3 outlet ใหม่ด้วยทีม chef แยก) | operation bulk เสร็จ; RBAC per-user save; session in-flight ทั้งหมดได้รับผลกระทบ; การประสานกับ HR / operation เพื่อสื่อสารการเปลี่ยน |
| AC-EDGE-03 | Chain versioning long-tail | สูตรมีแถว `tb_recipe_version` 200+ ตลอด 5 ปี | ทุกแถวรักษา; UI จัดหน้า / lazy-load ประวัติเวอร์ชัน; query sample ของ Auditor indexed อย่างเหมาะสมบน `recipe_id` + `version_number`; การ test regression ประสิทธิภาพยืนยันการ browse เวอร์ชันภายในเวลาที่ยอมรับได้ |
| AC-EDGE-04 | Auditor reconstruct สถานะประวัติ | Auditor ต้องการรู้ว่า `House Burger` หน้าตาอย่างไร 18 เดือนก่อนสำหรับการพิพาท compliance | Auditor เปิดประวัติเวอร์ชัน; เลือกเวอร์ชัน active 18 เดือนก่อน (ตาม `created_at`); อ่าน snapshot JSON (`recipe_data`, `ingredients_data`, `steps_data`, `variants_data`); สถานะสูตรประวัติเต็ม reconstruct โดยไม่กระทบสถานะปัจจุบัน |
| AC-EDGE-05 | การ clean equipment master | Sysadmin ปลดประจำการอุปกรณ์เก่า (เช่น sous-vide rig ที่ปลดประจำการ); อ้างอิงใน JSON prep-step บน 12 สูตร | Sysadmin soft-delete แถวอุปกรณ์ (การอ้างอิง prep-step เป็น JSON ไม่ใช่ FK ดังนั้นไม่มีการบล็อกระดับ schema); Sysadmin ประสานกับ Chef เพื่อ update prep step ที่ได้รับผลกระทบ; หรือเหลือการอ้างอิงไว้เป็น record ประวัติ |
| AC-EDGE-06 | การบังคับใช้นโยบายการเก็บข้อมูลที่ scale | การเก็บข้อมูล tenant: archive 2 ปี แล้ว soft-delete; 500 สูตร archive 2 ปีก่อน | operation bulk soft-delete ตาม `REC_POST_009`; UI อนุญาตการเลือก batch; แถว `tb_recipe_version` รักษา (ไม่ cascade-delete โดย soft-delete); สูตรหายจาก query default; ข้อมูล audit รักษา |
| AC-EDGE-07 | Auditor cross-reference เวอร์ชันสูตรกับประวัติ menu-item linkage | Auditor ต้องการรู้ว่า menu item ไหน link กับสูตร X ที่วันที่ประวัติเฉพาะ | chain `tb_recipe_version` ของสูตรเป็น input หนึ่ง; ประวัติ linkage ของ POS-integration layer เป็นอีก (นอก schema สูตรตาม `REC_XMOD_008`); Auditor join ทั้งสองสำหรับการ reconstruct ประวัติ; ถ้า POS layer ไม่รักษาประวัติ linkage นั่นคือ audit gap ที่ escalate |
| AC-EDGE-08 | Sysadmin สอบสวน alert integration — `[store-requisition](/th/inventory/store-requisition)` auto-create failure | Recipe-driven SR auto-create ล้มเหลว 3 วัน; event ที่วางแผนไม่มี SR draft | Sysadmin สอบสวน integration: ยืนยันโมดูล recipe กำลังยิง event; ยืนยันโมดูล SR กำลังรับแต่ล้มเหลวที่ create (เช่น issue permission location ปลายทาง mis-config) Fix ใช้; backfill SR draft ที่หายด้วยมือถ้าต้องการ |

## 5. แหล่งอ้างอิง

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — handoff ข้าม persona ที่ pivot จาก Audit / Config: Scenario 10 (การเปลี่ยน RBAC กระทบงาน in-flight), Scenario 11 (audit sample verify chain versioning)
- User flow: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — แหล่ง happy-path สำหรับ Section 1 ด้านบน; อธิบาย primary flow 10 ขั้นตอน (Sysadmin: config → RBAC → นโยบาย → integration → วงจรชีวิต master; Auditor: sample → review cascade → findings)
- กฎทางธุรกิจที่ verify: [02-business-rules.md](./02-business-rules.md) Section 4 — `REC_AUTH_012` (อำนาจ Sysadmin), `REC_AUTH_013` (Auditor read-only), `REC_AUTH_014` (อำนาจ delete ผ่าน soft-delete); Section 5 — `REC_POST_009` (ผลกระทบ posting soft-delete); Section 6 — `REC_XMOD_009` (audit versioning), `REC_XMOD_010` (RBAC mapping)
- spec E2E: **ไม่มีสำหรับภายในสูตร**; การตรวจสอบสุขภาพ integration โดยทั่วไปแยกจาก E2E สูตร
- Cross-link: [product](/th/inventory/product) — Sysadmin เป็นเจ้าของ flag `is_used_in_recipe` บนสินค้าที่ gate สิทธิ์สูตร
- Cross-link: [costing](/th/inventory/costing) — Sysadmin ดูแล chain integration cost-drift
- Cross-link: [inventory](/th/inventory/inventory) — Sysadmin ดูแล chain integration theoretical-consumption
- Cross-link: [store-requisition](/th/inventory/store-requisition) — Sysadmin ดูแลการ wire recipe → SR auto-create
