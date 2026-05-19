---
title: สูตรอาหาร (Recipe) — User Flow — Cost Controller
description: flow ของ Cost Controller ในโมดูลสูตร — review ต้นทุนสูตร margin เป้าหมาย ราคาขาย gross margin; ติดตาม drift; เซ็นอนุมัติการเปลี่ยนแปลง
published: true
date: 2026-05-17T12:00:00.000Z
tags: recipe, user-flow, cost-controller, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# สูตรอาหาร (Recipe) — User Flow — Cost Controller

> **At a Glance**
> **Persona:** Cost Controller (+ Cost Control Department) &nbsp;·&nbsp; **โมดูล:** [[recipe]] &nbsp;·&nbsp; **ขั้นตอน workflow:** DRAFT / PUBLISHED (การแก้ cost-only + co-approve การ publish off-target) &nbsp;·&nbsp; **สิทธิ์สำคัญ:** edit-cost (% เป้าหมาย, labor / overhead, ราคาขาย), co-approve publish (off-target), อ่านข้าม library
> **persona นี้ทำอะไร:** Review rollup cost และ margin ของสูตร แก้คอลัมน์ cost / pricing ติดตาม drift และ co-approve การ publish off-target

## 1. บทบาทในโมดูลนี้

persona **Cost Controller** ครอบคลุมสอง role ที่ทับซ้อนกัน: **Cost Controller** (เชิงธุรกรรม — review rollup cost ของแต่ละสูตร % food-cost เป้าหมาย ราคาขายที่แนะนำ gross margin; ติดตาม cost drift เมื่อราคาวัตถุดิบเคลื่อน; flag margin นอก tolerance; เซ็นอนุมัติการเปลี่ยน cost ที่กระทบราคาเมนู; รันรายงาน variance ทฤษฎี-vs-จริง) และ **Cost Control Department** (ระดับ portfolio — เป็นเจ้าของกระบวนการ recipe-costing ที่ scale ตั้ง % food-cost เป้าหมายระดับหมวดหมู่ผ่าน `tb_recipe_category.default_cost_settings` ขับเคลื่อนการอนุมัติ versioning เมื่อราคาวัตถุดิบเลื่อนอย่างมีนัยสำคัญ กระทบยอด variance ของ outlet กับ GL ที่ปิด period) Surface อำนาจของ Cost Controller คือ **อ่านข้าม recipe library และเขียนคอลัมน์ cost / pricing เท่านั้น** — ตาม `REC_AUTH_006` Cost Controller อาจแก้ `target_food_cost_percentage`, `labor_cost`, `overhead_cost`, `labor_cost_percentage`, `overhead_percentage`, `selling_price` และ `suggested_price` บนสูตร `DRAFT` และ `PUBLISHED`; การแก้วัตถุดิบ / ขั้นตอน / variant ยังคงอยู่กับ Chef Cost Controller ยังเป็น **co-approver ของการ publish** สำหรับการ publish margin off-target ตาม `REC_AUTH_007` (เมื่อ `actual_food_cost_percentage > target + tenant tolerance` การ publish ถูก gate บน co-approval ของ Cost Controller); co-approval ถูกบันทึกใน `tb_recipe_version.change_summary` หรือ log signoff ระดับ application นอกเหนือจากงานต่อสูตร Cost Controller เป็นเจ้าของ **dashboard cost-drift** (สูตรที่ margin ตกนอก tolerance เนื่องจากการเคลื่อนของราคาวัตถุดิบหรือ sub-recipe cascade ตาม `REC_XMOD_006`) และ **dashboard variance ทฤษฎี-vs-จริง** (variance food-cost ระดับ outlet ที่คำนวณจาก OUT เชิงทฤษฎีที่ recipe-driven vs movement สต๊อกจริง)

## 2. Entry Point และ Primary Flow

**Entry point:** สี่เส้นทางสู่งาน Cost Controller

- **Dashboard cost-drift** — มุมมอง list ข้ามสูตร `PUBLISHED` ที่ `actual_food_cost_percentage` เกิน `target_food_cost_percentage` เกิน tolerance ของ tenant จัดอันดับตามขนาด drift แต่ละแถว link ไปยังรายละเอียดสูตรและไปยังวัตถุดิบที่ได้รับผลกระทบที่ cost เคลื่อน
- **คิว co-approval ก่อน publish** — มุมมอง list ของสูตร `DRAFT` ที่ Chef mark ว่าพร้อม publish แต่ margin จริง off-target; Cost Controller เข้าคิวเพื่อ co-approve หรือขอการปรับปรุงตาม `REC_AUTH_007`
- **รายละเอียดสูตร → tab Costing** — drill ตรงเข้าสูตรเดียว; Cost Controller สามารถปรับ `target_food_cost_percentage`, `selling_price`, `labor_cost_percentage`, `overhead_percentage` ตาม `REC_AUTH_006`
- **Dashboard variance (ทฤษฎี-vs-จริง)** — dashboard variance food-cost ระดับ outlet; การคลิกเข้า outlet drill เข้าสูตรที่มีส่วนร่วมใน variance

**Primary flow (10 ขั้นตอน — ทำซ้ำต่อ period และต่อ event drift):**

1. **เปิด dashboard cost-drift** Dashboard แสดงสูตร `PUBLISHED` ที่ `actual_food_cost_percentage` ปัจจุบันเกิน `target_food_cost_percentage` เกิน tolerance ของ tenant (เช่น > 2 percentage points) Filter ตามหมวดหมู่ ประเภทอาหาร outlet (ถ้าตั้งค่าการ map recipe-outlet) ขนาด drift วันที่เปลี่ยนล่าสุด
2. **Drill เข้าสูตรที่ flag** เปิดรายละเอียดสูตร; review tab Costing: rollup `total_ingredient_cost` พร้อม `net_cost` และ `wastage_cost` per-line, `labor_cost`, `overhead_cost`, `cost_per_portion`, `selling_price`, `actual_food_cost_percentage`, `gross_margin`, `gross_margin_percentage` อ่าน timeline pricing-history (`tb_recipe_pricing_history`) เพื่อดูว่า cost เคลื่อนตลอดเวลาอย่างไร
3. **ระบุสาเหตุของ drift** drift เกิดจากอะไร: (a) การ update pricelist vendor บนสินค้าที่สูตรใช้ (มองเห็นใน `tb_recipe_pricing_history.change_reason = "cost-drift update from costing module"`); (b) การ cascade cost ของ sub-recipe (`change_reason = "sub-recipe cost cascade from <name>"`); (c) วัตถุดิบที่ revise (Chef update `qty` หรือ wastage ตาม `REC_POST_004`); หรือ (d) การเปลี่ยนเป้าหมาย (tenant ลด % food-cost เป้าหมาย)?
4. **ตัดสินใจเส้นทางแก้ไข** สี่ option:
   - **Revise วัตถุดิบ** — escalate ไปยัง Chef เพื่อ revise (swap เป็นวัตถุดิบที่ถูกกว่า ลด portion หา vendor ต่าง) Cost Controller ไม่แก้วัตถุดิบโดยตรง; Chef ทำ Cost Controller log คำขอเป็น trigger
   - **ปรับราคา** — แก้ `selling_price` ขึ้นตาม `REC_AUTH_006` และ `REC_POST_010`; ระบบคำนวณ `actual_food_cost_percentage`, `gross_margin`, `gross_margin_percentage` ใหม่; แถว `tb_recipe_pricing_history` เขียนด้วย `change_reason = "price increase to restore margin"` ประสานกับ F&B Ops บนการสื่อสารด้านเมนู
   - **ปรับเป้าหมาย** — แก้ `target_food_cost_percentage` ขึ้นตาม `REC_AUTH_006`; margin ของสูตรอยู่ใน target ใหม่แล้ว นี่คือเส้นทาง "ยอมรับความเป็นจริงของ cost ใหม่"; สำรองสำหรับสถานการณ์ที่การเพิ่ม cost เป็นทั้งอุตสาหกรรมและหลีกเลี่ยงไม่ได้ พร้อมการปรับที่ระดับหมวดหมู่ผ่าน `tb_recipe_category.default_cost_settings`
   - **Co-approve off-target** — ถ้า Chef เสนอ publish หรือดูแลสูตรที่ margin off-target โดยจงใจ (loss leader signature dish strategic-priced) Cost Controller co-approve ตาม `REC_AUTH_007`; สถานะ off-target document ใน `tb_recipe_version.change_summary` สำหรับ audit
5. **Co-approve การ publish off-target (เส้นทาง Chef-initiated)** เมื่อ Chef เตรียมสูตร `DRAFT` ที่ margin จริง off-target ที่เวลา publish การ publish ถูก gate บน co-approval ของ Cost Controller Cost Controller review สูตร (วัตถุดิบ input costing pricing ที่ตั้งใจ) และตัดสินใจ: (a) co-approve (publish ดำเนินการ; off-target document); (b) ขอการปรับปรุง (publish ยังคง gate จนกว่า Chef revise และ re-submit); (c) ปฏิเสธ (Chef revise หรือทิ้งสูตร)
6. **แก้ฟิลด์ cost-only ที่เหมาะสม** ตาม `REC_AUTH_006` Cost Controller อาจแก้ `target_food_cost_percentage`, `selling_price`, `labor_cost_percentage`, `overhead_percentage`, `suggested_price` โดยตรง การแก้เหล่านี้ trigger `REC_POST_010` — คำนวณ rollup pricing ใหม่ เขียนแถว `tb_recipe_pricing_history` สูตรยังคงในสถานะปัจจุบัน; ไม่ต้องการ snapshot `tb_recipe_version` เต็มสำหรับการเปลี่ยน pricing-only
7. **รันรายงาน variance ทฤษฎี-vs-จริง** ที่ปิด period (หรือ on-demand) รันรายงาน variance ระดับ outlet การใช้เชิงทฤษฎีคำนวณจากการขายเมนู × บรรทัดวัตถุดิบของสูตรตาม `REC_CALC_014`; การใช้จริงจากข้อมูล physical-count + SR + adjustment Variance ต่อวัตถุดิบต่อ outlet คือ KPI headline Variance บวกที่ยังคงอยู่ (ทฤษฎี < จริง; over-consumption) ชี้ไปที่ over-portioning การโจรกรรม การเสีย หรือช่องว่างความถูกต้องของสูตร; variance ลบที่ยังคงอยู่ชี้ไปที่ under-portioning หรือสูตรผิด
8. **สอบสวน variance ที่มีนัยสำคัญ** Drill เข้า outlet ที่มี variance มีนัยสำคัญ Cost Controller **ไม่** แก้สูตร — พวกเขายก issue กับ Chef (ความถูกต้องของสูตร) และ Outlet Manager (วินัยการควบคุม portion shrinkage ที่เป็นไปได้) การสอบสวน variance เป็น collaborative; สูตรเป็น input หนึ่ง
9. **ตั้ง / ปรับเป้าหมายระดับหมวดหมู่ (ระดับ portfolio, Cost Control Department)** แต่ละไตรมาส (หรือ cadence ของ tenant) review เป้าหมาย food-cost ระดับหมวดหมู่ สำหรับแต่ละ `tb_recipe_category` ปรับ `default_cost_settings` (% food-cost เป้าหมาย % labor / overhead) ตามประสิทธิภาพ portfolio สภาพตลาด และทิศทางกลยุทธ์ สูตรใหม่ในหมวดหมู่จะสืบทอด; สูตรเดิมสามารถ apply ใหม่ทางเลือก (operation ด้วยมือ; ไม่อัตโนมัติ)
10. **Signoff ที่ปิด period** ที่ปิด period Cost Control Department เซ็นอนุมัติรายงาน food-cost ที่ recipe-driven ของ period — ยืนยันว่า variance ทฤษฎี-vs-จริงต่อ outlet ถูกสอบสวนสำหรับช่องว่างมีนัยสำคัญ ทุก event cost-drift ใน period มีการแก้หรือ co-approval ที่สอดคล้องใน audit trail และ snapshot pricing-history กระทบยอดกับสถานะ recipe library ที่ boundary period

## 3. Decision Branch

- **Cost drift attributable to ingredient เดียว vs portfolio drift**: เมื่อ cost spike ของวัตถุดิบหนึ่งทำให้เกิด drift Cost Controller สามารถ target การตอบสนอง (swap วัตถุดิบ เจรจากับ vendor การปรับ price-only บนสูตรที่ได้รับผลกระทบ) เมื่อ drift เป็น portfolio-wide (เช่น การเคลื่อนราคา commodity ตามฤดูกาลที่กระทบวัตถุดิบหลายตัว) การตอบสนองกว้างกว่า — การปรับเป้าหมายระดับหมวดหมู่ การ review menu engineering กับ F&B Ops
- **การปรับราคา vs การ revise วัตถุดิบ**: เมื่อ restore margin การปรับราคาเร็วกว่าและ Cost-Controller-owned (`REC_AUTH_006`) แต่สร้างการรบกวนด้านเมนู การ revise วัตถุดิบช้ากว่าและ Chef-owned แต่รักษาราคาเมนู ทางเลือกขึ้นอยู่กับ (a) ความกดดันราคาเชิงแข่งขัน (b) วัตถุดิบทดแทน meet มาตรฐานคุณภาพหรือไม่ (c) การเพิ่ม cost เปรียบเทียบกับคู่แข่งอย่างไร
- **Co-approve vs ขอการปรับปรุงสำหรับการ publish off-target**: Cost Controller co-approve การ publish off-target เมื่อ (a) สูตรเป็น strategic-priced โดยจงใจ (signature dish, loss leader), (b) ทางเลือก (บังคับการ compliance ของ margin) จะกระทบคุณภาพหรือ brand หรือ (c) การวิเคราะห์ตลาดแสดงราคาคู่แข่งสนับสนุนราคาที่เลือกแม้ margin ต่ำกว่า มิฉะนั้น ขอการปรับปรุง
- **แก้ตรง vs escalate Chef**: การแก้ cost-only (% เป้าหมาย, ราคา, % labor / overhead) เป็น Cost-Controller-owned; การแก้วัตถุดิบ / ขั้นตอน / variant เป็น Chef-owned เมื่อ boundary blur (เช่น การเปลี่ยนขนาด portion จะ fix margin แต่เป็นการเปลี่ยนปริมาณวัตถุดิบ) Cost Controller escalate ไปยัง Chef แทนการเอื้อมเข้าวัตถุดิบ
- **การปรับเป้าหมาย vs ยอมรับ variance**: ที่ระดับ portfolio เมื่อ drift ที่ยังคงอยู่กระทบสูตรหลายตัวในหมวดหมู่ Cost Control Department ตัดสินใจว่าจะเพิ่ม % food-cost เป้าหมายของหมวดหมู่ (ยอมรับความเป็นจริงของ cost ใหม่) หรือถือเป้าหมายและไล่ตามการเปลี่ยนวัตถุดิบ / pricing ข้าม portfolio การตัดสินใจเป็นกลยุทธ์และ document ใน record การเปลี่ยนระดับหมวดหมู่
- **ความลึกของการสอบสวน variance**: variance ที่มีนัยสำคัญที่ยังคงอยู่ trigger การสอบสวน; variance ชั่วคราวหรือเล็กถูกสังเกตแต่ไม่สอบสวนลึก Threshold ตั้งค่าโดย tenant (เช่น > ฿X ต่อ outlet ต่อ period หรือ > N% ของทฤษฎีสำหรับ period)

## 4. Exit Point / Handoff

การมีส่วนร่วมของ Cost Controller บนสูตร / ความกังวลด้าน cost จบที่หนึ่งในหลาย boundary:

- **Co-approval บันทึก** — handoff กลับไปยัง **Chef** เพื่อดำเนินการกับ publish ตาม `REC_POST_003`; สถานะ off-target document ใน `tb_recipe_version.change_summary`
- **คำขอการ revise ออกให้ Chef** — handoff ไปยัง **Chef** พร้อมความกังวลเฉพาะ (cost วัตถุดิบ ปัญหา sub-recipe margin off-target); Chef revise และ re-submit Cost Controller re-review ที่การ re-submit
- **การแก้ cost-only ใช้** — สูตรยังคงในสถานะปัจจุบัน; แถว `tb_recipe_pricing_history` เขียน; menu item ที่ได้รับผลกระทบอาจต้องการการสื่อสารราคาผ่าน F&B Ops Cost Controller ติดตามสูตรสำหรับ drift เพิ่มเติม
- **Issue variance escalate ไปยัง Chef / Outlet Manager** — Cost Controller ยก issue; การสอบสวนและ action แก้ไขภายหลังอยู่ที่ Chef (ความถูกต้องของสูตร) และ / หรือ Outlet Manager (วินัยการควบคุม portion) Cost Controller ติดตามเพื่อการ resolve แต่ไม่ขับเคลื่อนโดยตรง
- **เป้าหมายหมวดหมู่ปรับ** — handoff ไปยัง **Audit / Config (Sysadmin)** เพื่อ update `tb_recipe_category.default_cost_settings`; สูตรใหม่สืบทอด Cost Controller (หรือ Cost Control Department) เซ็นอนุมัติการตัดสินใจระดับหมวดหมู่
- **Signoff ที่ปิด period ออก** — handoff ไปยัง **Audit / Config (Finance + Auditor)** สำหรับการปิด period; signoff เป็นส่วนของ package การปิด period ทางการเงิน

Cost Controller อยู่ในการ engage ต่อเนื่องกับโมดูล recipe — ทุกการเคลื่อนของ cost วัตถุดิบ ทุกการตัดสินใจ menu-pricing ทุกการสอบสวน variance ไหลผ่าน persona นี้ "Exit" จากสูตรที่กำหนดหายาก; engagement คือการกำกับต่อเนื่อง

## 5. แหล่งอ้างอิง

- Parent overview: [03-user-flow.md](./03-user-flow.md) — วงจรชีวิต canonical และตาราง handoff ข้าม persona; Section 4 แถว "Cost Controller → Chef (co-approve / revise)", "Cost Controller → F&B Ops (price adjustment, menu engineering)", "Cost Controller → Audit / Config (period close)" anchor exit ของ persona นี้
- `../carmen/docs/recipe-module/RECIPE-Overview.md` § Cost Control — แหล่ง carmen/docs สำหรับขอบเขตความรับผิดชอบของ Cost Controller
- `../carmen/docs/recipe-module/RECIPE-PRD.md` § Cost Control user story — user story ของ carmen/docs ("As a cost controller, I want to review recipe costs...", "...update ingredient costs and see the impact on recipe pricing...", "...set target food cost percentages...")
- `../carmen/docs/recipe-module/RECIPE-Business-Requirements.md` § Recipe Costing (`REC_CO_001`–`REC_CO_005`) — ป้อนกฎการคำนวณที่ Cost Controller review; § Logic Implementation § Cost Calculations คือชุดสูตร formal
- `../carmen/docs/recipe/recipe-management.md` § Recipe Costing Sheet — การอ้างอิงระดับ layout สำหรับ panel สรุป cost grid วัตถุดิบ section cost การเตรียม yield analysis section pricing comparative metric
- `../carmen/docs/recipe/gross-profit-dashboard-spec.md` — layout dashboard gross-profit ที่ Cost Controller ใช้สำหรับ review portfolio
- `../carmen/docs/recipe/complete-dashboard-spec.md` — layout dashboard ที่ครอบคลุมสำหรับการกำกับ cost ระดับ portfolio
- Sibling: [03-user-flow-chef.md](./03-user-flow-chef.md) — คู่ collaboration หลัก; Chef revise วัตถุดิบ Cost Controller review / co-approve; การแก้ cost-only ยังคงอยู่กับ Cost Controller
- Sibling: [03-user-flow-procurement-fb-ops.md](./03-user-flow-procurement-fb-ops.md) — F&B Ops collaborate บนการปรับด้านราคาและการตัดสินใจ menu engineering ที่ขับเคลื่อนด้วยการค้นพบ cost-drift
- Sibling: [03-user-flow-outlet-manager.md](./03-user-flow-outlet-manager.md) — collaborator การสอบสวน variance; วินัยการควบคุม portion ที่ outlet เป็น input หนึ่งของ variance ทฤษฎี-vs-จริง
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — Sysadmin ตั้ง default หมวดหมู่ที่การปรับเป้าหมายของ Cost Controller ไหลผ่าน; Auditor review timeline `tb_recipe_pricing_history` และลายเซ็น co-approval
- Sibling: [01-data-model.md](./01-data-model.md) — คอลัมน์ cost canonical บน `tb_recipe` (`total_ingredient_cost`, `labor_cost`, `overhead_cost`, `cost_per_portion`, `target_food_cost_percentage`, `actual_food_cost_percentage`, `selling_price`, `gross_margin`, `gross_margin_percentage`); `tb_recipe_pricing_history` เป็น audit trail สำหรับการเปลี่ยน cost / ราคา
- Sibling: [02-business-rules.md](./02-business-rules.md) — `REC_CALC_001`–`REC_CALC_015` (math ที่ Cost Controller review และพื้นฐานสำหรับการตรวจจับ drift), `REC_AUTH_006`–`REC_AUTH_008` (scope อำนาจของ Cost Controller), `REC_POST_010` (ผลกระทบ posting การแก้ pricing-only), `REC_XMOD_005`–`REC_XMOD_006` (การ coupling โมดูล costing), `REC_XMOD_009` (versioning / audit)
- ที่เกี่ยวข้อง: [[costing]] — ต้นน้ำของทุก feed cost per-ingredient; event cost-drift ไหลจาก `[[costing]]` ไปยังโมดูล recipe ตาม `REC_XMOD_006`
- ที่เกี่ยวข้อง: [[inventory]] — dashboard variance ทฤษฎี-vs-จริง join OUT movement เชิงทฤษฎีที่ recipe-driven กับ movement สต๊อกจริง
