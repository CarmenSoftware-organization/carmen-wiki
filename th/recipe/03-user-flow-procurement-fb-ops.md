---
title: สูตรอาหาร (Recipe) — User Flow — Procurement / F&B Ops
description: flow ของ Procurement และ F&B Operations Manager ในโมดูลสูตร — ขนาด PO จาก demand สูตร ตรวจสอบการมีอยู่ของวัตถุดิบ อนุมัติ menu-item linkage เซ็นอนุมัติ menu engineering
published: true
date: 2026-05-17T12:00:00.000Z
tags: recipe, user-flow, procurement-fb-ops, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# สูตรอาหาร (Recipe) — User Flow — Procurement / F&B Ops

> **At a Glance**
> **Persona:** Procurement Department + F&B Operations Manager &nbsp;·&nbsp; **โมดูล:** [[recipe]] &nbsp;·&nbsp; **ขั้นตอน workflow:** off-path — กลยุทธ์ต้นน้ำ (approve menu-item linkage) + การซื้อปลายน้ำ (ขนาด PO) &nbsp;·&nbsp; **สิทธิ์สำคัญ:** อ่านสูตร, approve-menu-link (F&B Ops), ยกคำขอทดแทน (Procurement)
> **persona นี้ทำอะไร:** Procurement ขนาด PO จาก demand สูตรและแสดงคำขอทดแทน; F&B Ops อนุมัติ menu-item linkage และรัน menu engineering

## 1. บทบาทในโมดูลนี้

persona **Procurement / F&B Ops** ครอบคลุมสอง role ปฏิบัติการที่เกี่ยวข้อง: **Procurement** (บริโภค demand สูตรเพื่อแจ้งการซื้อ — ใช้ recipe explosion × ยอดขายคาดการณ์เพื่อขนาด PO ตรวจสอบว่าการมีอยู่ของวัตถุดิบ match ความต้องการของสูตร รับคำขอทดแทนเมื่อหาวัตถุดิบไม่ได้) และ **F&B Operations Manager** (เป็นเจ้าของ recipe library ที่ระดับกลยุทธ์ — อนุมัติ menu item ใหม่และ recipe linkage ของพวกเขาตาม `REC_AUTH_011` เซ็นอนุมัติ menu engineering กับข้อมูล margin และ variance ทำให้เอกสารสูตรรองรับการอบรมและ audit) ทั้งสอง role เป็น read-mostly เทียบกับ recipe library (`recipe:read` ตาม `REC_AUTH_010`); F&B Ops เพิ่มถือสิทธิ์การอนุมัติ menu-item linkage (`recipe:approve-menu-link` ตาม `REC_AUTH_011`) Procurement ไม่เขียนกับสูตร — พวกเขาอาจแสดงคำขอทดแทนต่อ Chef (ช่องปฏิบัติการ ไม่ใช่การเขียน schema); Chef ยังคงเป็น author ของการ swap วัตถุดิบหรือการ revise สูตร F&B Ops ก็ไม่เขียนกับ header สูตร / วัตถุดิบ / ขั้นตอน — อำนาจของพวกเขาเป็นต้นน้ำของสูตร (ตั้งทิศทางกลยุทธ์ อนุมัติ linkage) และปลายน้ำของการ publish สูตร (การตัดสินใจด้านราคาและด้านเมนูที่ขับเคลื่อนด้วยข้อมูล cost สูตร ใน collaboration กับ Cost Controller) จากมุมมองของโมดูล recipe persona นี้คือ **gate ต้นน้ำเชิงกลยุทธ์** (F&B Ops บน menu-item linkage) และ **ผู้บริโภคปลายน้ำด้านการซื้อ** (Procurement บนการขนาด PO)

## 2. Entry Point และ Primary Flow

**Entry point:** ห้าเส้นทางสู่งาน Procurement / F&B Ops ที่แตะโมดูล recipe

- **Procurement → explosion demand** — รวม recipe explosion ข้ามทุก outlet × ยอดขายคาดการณ์ในขอบเขตการวางแผน (สัปดาห์ / เดือน) ผลิต demand วัตถุดิบระดับ portfolio; สิ่งนี้ seed การขนาด PO สำหรับคลังกลาง
- **Procurement → การตรวจสอบการมีอยู่ของวัตถุดิบ** — สำหรับแต่ละสูตร `PUBLISHED` (หรือสูตร `DRAFT` candidate ที่กำลังขึ้นเพื่ออนุมัติ) validate ว่าวัตถุดิบสามารถหาได้อย่างน่าเชื่อถือจาก vendor list ปัจจุบันที่ cost ที่สูตรสมมุติ
- **Procurement → ช่องคำขอทดแทน** — เมื่อวัตถุดิบไม่มี (vendor stock-out, ปลดประจำการ, เปลี่ยน vendor) แสดงคำขอทดแทนต่อ Chef สำหรับการ revise สูตร
- **F&B Ops → การอนุมัติ menu-item linkage** — เมื่อ Chef publish สูตรใหม่และเสนอสำหรับ menu-item linkage F&B Ops review สูตร (cost margin fit กับเมนู brand) และอนุมัติหรือปฏิเสธ linkage
- **F&B Ops → การ review menu engineering** — review เป็นระยะ (ปกติรายไตรมาส) ของเมนู vs recipe library: จานไหน over-margin (เพิ่มราคาหรือ drop) จานไหน under-margin (cost-engineer หรือ drop) จานไหนเป็น signature (รักษาที่ margin ใดก็ตาม)

**Primary flow (10 ขั้นตอน — รันต่อเนื่องข้ามปฏิทิน procurement และการวางแผนเมนู):**

1. **(Procurement) รวม demand สูตร** สำหรับขอบเขตการวางแผน รวม recipe explosion × ยอดขายคาดการณ์ข้ามทุก outlet แต่ละ menu item → สูตรที่ link → บรรทัดวัตถุดิบ × ปริมาณที่ขายคาดการณ์ × % wastage × การแปลงหน่วย → demand วัตถุดิบระดับ portfolio บรรทัด sub-recipe ซ้อนไปยัง demand สินค้าใบไม้
2. **(Procurement) เปรียบเทียบกับ on-hand และ PO in-flight** Net demand สำหรับขอบเขต = demand วัตถุดิบคาดการณ์ − on-hand คลังกลาง − PO in-flight (การจัดส่งคาดในขอบเขต) − สต๊อกความปลอดภัย Net demand เป็นพื้นฐานสำหรับการขนาด PO ใหม่
3. **(Procurement) Validate การมีอยู่ของวัตถุดิบ** สำหรับแต่ละวัตถุดิบ high-volume ยืนยันการมีอยู่ของ vendor ที่ cost ที่สูตรสมมุติ ถ้า vendor flag stock-out ที่จะเกิด (สินค้าตามฤดูกาล การรบกวน supply-chain) flag สูตรที่ขึ้นต่อวัตถุดิบสำหรับการวางแผนทดแทน
4. **(Procurement) ยก PO** ขนาด PO เพื่อ meet net demand ต่อ vendor ต่อหน้าต่างการจัดส่ง วงจรชีวิตของ PO เป็นเจ้าของโดยโมดูล procurement (ไม่ใช่โมดูล recipe); สูตรเป็น input demand ความถูกต้องของสูตร (โดยเฉพาะ % wastage, conversion factor และ sub-recipe roll-up) กระทบความถูกต้องของการขนาด PO โดยตรง
5. **(Procurement) แสดงคำขอทดแทน** เมื่อวัตถุดิบไม่มีจาก vendor list ปัจจุบัน ยกคำขอทดแทนต่อ Chef: "Vendor X ไม่สามารถ supply Y ใน N วันถัดไป; candidate ทดแทนคือ A / B / C ที่ cost $/$/$ ผลกระทบสูตร: จาน [list] ใช้ Y ในปริมาณ [list]" Chef ประเมินทดแทนและอย่างใดอย่างหนึ่ง revise สูตร (ตาม `REC_POST_004` หรือ `REC_POST_005`) หรือประสานการหยุดเมนูชั่วคราว
6. **(F&B Ops) Review ข้อเสนอสูตรใหม่** เมื่อ Chef publish สูตรใหม่และเสนอสำหรับ menu-item linkage F&B Ops เปิดรายละเอียดสูตร; review cost (`cost_per_portion`), margin (`actual_food_cost_percentage`, `gross_margin_percentage`), fit ของเมนู (complement item ที่มีอยู่หรือไม่? cannibalise ยอดขายของ item ที่มีอยู่หรือไม่?), fit ของ brand (สอดคล้องกับ cuisine / concept หรือไม่?) และ fit ปฏิบัติการ (ครัวมีอุปกรณ์ ทักษะ throughput หรือไม่?)
7. **(F&B Ops) อนุมัติหรือปฏิเสธ menu-item linkage** ตาม `REC_AUTH_011` การอนุมัติบันทึกนอก schema สูตร (ใน POS-integration layer หรือ application-layer mapping); สูตรเองไม่เปลี่ยน การปฏิเสธส่ง Chef กลับไป revise (โดยทั่วไป: cost สูงเกินไป ไม่ fit กับ cuisine ซ้ำกับจานที่มีอยู่) — สูตรยังคง `PUBLISHED` แต่ไม่ link กับ menu item
8. **(F&B Ops) รัน review menu engineering** เป็นระยะ (รายไตรมาส) review menu × ข้อมูล cost / margin / variance ของสูตร matrix รวม popularity (ปริมาณการขาย) กับ profitability (% margin): high-margin / high-volume = star (รักษา ส่งเสริม); high-margin / low-volume = puzzle (พิจารณาส่งเสริม); low-margin / high-volume = workhorse (cost-engineer เพื่อปรับ margin); low-margin / low-volume = dog (drop หรือ re-conceive)
9. **(F&B Ops) ประสานการตัดสินใจ ราคา / cost / สูตร** การค้นพบ menu engineering ขับเคลื่อน collaboration: Cost Controller ปรับราคาบน workhorse (ตาม `REC_AUTH_006`); Chef revise วัตถุดิบบน dog เพื่อให้ cost ต่ำลง; F&B Ops drop linkage สำหรับจานที่กำลังถูกเลิกใช้ โมดูล recipe สนับสนุน workflow แต่การตัดสินใจกลยุทธ์เป็นเจ้าของโดย F&B Ops
10. **(F&B Ops) Signoff ประสิทธิภาพเมนูที่ปิด period** ที่จบของแต่ละ menu cycle (รายไตรมาส / รายฤดูกาล) F&B Ops เซ็นอนุมัติประสิทธิภาพเมนู: จานไหนบรรลุเป้าหมาย margin / sales จานไหน under-perform การตัดสินใจไหน (drop / re-cost / re-price) ถูกทำ Signoff เป็นส่วนของ package operating กลยุทธ์

## 3. Decision Branch

- **ขนาด PO — recipe-driven vs par-level**: Procurement อาจขนาด PO อย่างใดอย่างหนึ่งโดย explosion demand ที่ recipe-driven (ถูกต้องสำหรับปริมาณการผลิตที่รู้จัก — event banquet บริการ set-menu) หรือโดย par-level top-up (default สำหรับ a-la-carte ที่ demand เป็น probabilistic) ทางเลือกเป็นต่อวัตถุดิบ / ต่อ outlet; วัตถุดิบ high-value, slow-moving โดยทั่วไป recipe-driven, commodity fast-moving โดยทั่วไป par-level
- **วิธีการทดแทน**: เมื่อวัตถุดิบไม่มี Procurement อาจเสนอ (a) ทดแทนตรง (วัตถุดิบที่คล้าย cost ที่คล้าย — Chef ยืนยันและ update wastage/conversion ถ้าต้อง), (b) vendor ต่างสำหรับวัตถุดิบเดียวกัน (ไม่มีการเปลี่ยนสูตร), (c) หยุดเมนูชั่วคราวบนจานที่ได้รับผลกระทบ (ไม่มีการเปลี่ยนสูตร demand ชั่วคราวเป็นศูนย์) การตัดสินใจขับเคลื่อนด้วยระยะเวลาของช่องว่าง supply และความสำคัญของจานที่ได้รับผลกระทบ
- **การอนุมัติ menu-link — accept-as-is vs request-revisions**: F&B Ops อาจอนุมัติ linkage สูตรที่เสนอ (publish ดำเนินการไปยังการ list เมนู) ขอการปรับปรุง (cost สูงเกินไป ไม่ fit เมนู — Chef revise) หรือปฏิเสธทันที (concept ไม่ fit) Threshold สำหรับ "accept-as-is" ขึ้นอยู่กับ tolerance ของ tenant และความสำคัญกลยุทธ์ของจานใหม่
- **Menu engineering — drop vs re-cost vs re-price**: สำหรับจาน under-performing F&B Ops ตัดสินใจระหว่าง (a) drop menu link ทั้งหมด (ไม่มีการเปลี่ยนสถานะของสูตร; สูตรยังคง `PUBLISHED` แต่ไม่ link กับ menu item อีก) (b) ประสานกับ Chef เพื่อ re-cost (การ revise วัตถุดิบเพื่อให้ `cost_per_portion` ต่ำลง) (c) ประสานกับ Cost Controller เพื่อ re-price (เพิ่ม `selling_price` เพื่อ restore margin) ทางเลือกขับเคลื่อนด้วย role ของจานบนเมนูและการพิจารณา brand
- **เส้นทางการ escalate cost-drift**: เมื่อ Cost Controller flag cost drift portfolio-wide ในหมวดหมู่ F&B Ops ตัดสินใจว่าจะ (a) ดูดซับ (รักษาราคาเมนู ยอมรับการลด margin), (b) ส่งผ่าน (เพิ่มราคาเมนูเพื่อ restore margin — ต้องการการสื่อสาร / การวิเคราะห์คู่แข่ง) หรือ (c) re-engineer (ขับเคลื่อนการ revise วัตถุดิบข้ามหมวดหมู่ — งานด้าน Chef) การตัดสินใจเป็นกลยุทธ์และกระทบความสัมพันธ์กับ Cost Controller และ Chef

## 4. Exit Point / Handoff

การมีส่วนร่วมของ persona Procurement / F&B Ops บนสูตร / menu cycle ที่กำหนดจบที่หนึ่งในหลาย boundary:

- **(Procurement) ยก PO** — handoff ไปยัง flow PO ของโมดูล procurement (ด้าน vendor [[purchase-order]]); input demand สูตรเก็บเป็น rationale สำหรับการขนาด PO; PO advance โดยอิสระ Procurement กลับไปยังโมดูล recipe ในรอบการวางแผนถัดไป
- **(Procurement) คำขอทดแทนออกให้ Chef** — handoff ไปยัง **Chef** สำหรับการประเมินและ revise สูตรตาม `REC_POST_004` / `REC_POST_005` Procurement ติดตามสำหรับ update สูตรหรือการยืนยันการหยุดชั่วคราว
- **(F&B Ops) Menu-item linkage อนุมัติ** — handoff ไปยัง **menu / POS-integration layer** (นอก schema สูตรตาม `REC_XMOD_008`); สูตรขับเคลื่อน theoretical consumption บนการขายเมนูแล้ว F&B Ops กลับไปสู่ maintenance mode (menu engineering review เป็นระยะ)
- **(F&B Ops) Menu-item linkage ถูกปฏิเสธ** — handoff กลับไปยัง **Chef** (พร้อม feedback) สำหรับการ revise และ re-propose; สูตรยังคง `PUBLISHED` แต่ unlink
- **(F&B Ops) การตัดสินใจ menu engineering บันทึก** — handoff ไปยัง **collaborator ที่ได้รับผลกระทบ**: Chef สำหรับการ revise วัตถุดิบ Cost Controller สำหรับการปรับราคา หรือ [การปลดประจำการ] โมดูล recipe สะท้อนการเปลี่ยนที่ได้ตาม flow ของ persona collaborator
- **(F&B Ops) Signoff เมนูที่ปิด period** — handoff ไปยัง **Audit / Config (Finance + Auditor)** สำหรับการปิด period; signoff เป็นส่วนของ package การปิด period ทางการเงิน / ปฏิบัติการ

Procurement อยู่ในการ engage ต่อเนื่องกับโมดูล recipe — ทุกการขนาด PO แตะ demand สูตร F&B Ops อยู่ใน engagement เป็นระยะ — ที่ช่วงเวลาการอนุมัติการ publish สูตรและที่รอบ review menu-engineering

## 5. แหล่งอ้างอิง

- Parent overview: [03-user-flow.md](./03-user-flow.md) — วงจรชีวิต canonical และตาราง handoff ข้าม persona; Section 4 แถว "Procurement → Chef (substitution request)", "F&B Ops → Chef (menu-item linkage approval)", "F&B Ops → Cost Controller (price / menu engineering)" anchor exit ของ persona นี้
- `../carmen/docs/recipe-module/RECIPE-Overview.md` (และตาราง index ของ wiki `Roles and Personas`) — แถว Procurement Department และ F&B Operations Manager
- `../carmen/docs/recipe-module/RECIPE-PRD.md` § 6 Integration Requirements (Procurement integration; Cost Control integration) — แจ้งการ coupling ต้นน้ำ / ปลายน้ำ
- Sibling: [03-user-flow-chef.md](./03-user-flow-chef.md) — คู่ collaboration หลักสำหรับทั้งสอง sub-role: Procurement ยกคำขอทดแทน; F&B Ops อนุมัติ / ปฏิเสธ menu-item linkage บนสูตรที่ Chef-publish
- Sibling: [03-user-flow-cost-controller.md](./03-user-flow-cost-controller.md) — F&B Ops collaborate บน menu engineering: การตัดสินใจด้าน cost เป็น Cost Controller; การตัดสินใจด้านเมนูเป็น F&B Ops
- Sibling: [03-user-flow-outlet-manager.md](./03-user-flow-outlet-manager.md) — แชร์ข้อมูลการ explode demand (demand ระดับ outlet รวมเป็น demand ระดับ portfolio สำหรับ Procurement); SR ของ Outlet Manager เป็นการแสดงผล per-outlet ของความต้องการที่ recipe-driven เดียวกันที่ Procurement รวม
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — Sysadmin เป็นเจ้าของ RBAC รวมถึง permission `recipe:approve-menu-link` ที่ F&B Ops ใช้; Auditor review การอนุมัติ menu-item linkage เป็นส่วนของ audit
- Sibling: [01-data-model.md](./01-data-model.md) — `tb_recipe.cost_per_portion`, `actual_food_cost_percentage`, `gross_margin_percentage` (ตัวเลขที่ F&B Ops review ที่ menu-engineering); `tb_recipe_pricing_history` (timeline ของการเปลี่ยน cost / ราคาที่แจ้ง menu engineering)
- Sibling: [02-business-rules.md](./02-business-rules.md) — `REC_CALC_014` (สูตร theoretical-consumption — math การ explode demand ที่ Procurement ใช้), `REC_AUTH_010`–`REC_AUTH_011` (scope อำนาจ Procurement / F&B Ops), `REC_XMOD_008` (menu-item linkage เป็น application-layer ไม่อยู่ใน schema สูตร)
- ที่เกี่ยวข้อง: [[purchase-order]] — เอกสารปลายน้ำหลักของ Procurement; demand ที่ recipe-driven ขนาด PO
- ที่เกี่ยวข้อง: [[vendor-pricelist]] — ข้อมูล cost ของ vendor เป็น input ต้นน้ำของ cost สินค้า ซึ่งเป็นต้นน้ำของ cost สูตร; การเปลี่ยน vendor ไหลผ่านไปยัง event cost drift ของสูตร
- ที่เกี่ยวข้อง: [[costing]] — F&B Ops review ข้อมูล cost ที่มาจากโมดูล costing ผ่านสูตร
