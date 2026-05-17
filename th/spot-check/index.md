---
title: การสุ่มตรวจ (Spot Check)
description: การนับบางส่วนแบบเจาะจงของสินค้าหรือตำแหน่งที่เลือก — เป็นการตรวจที่เบากว่าการนับ physical count เต็ม
published: true
date: 2026-05-17T07:00:36.000Z
tags: spot-check, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# การสุ่มตรวจ (Spot Check)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** การนับบางส่วนแบบเจาะจง scope แคบ (สุ่ม / risk-based / event-driven) พร้อม recount และการ post ผลต่างไปสู่ adjustment &nbsp;·&nbsp; **ผู้ใช้งาน:** Inventory Controller, Counter, Auditor &nbsp;·&nbsp; **เอนทิตี/ตารางสำคัญ:** `tb_spot_check`, `tb_spot_check_detail`, ตาราง comment สองตาราง, `enum_spot_check_status`, `enum_spot_check_method` &nbsp;·&nbsp; **หน้าย่อย:** 10

![การสุ่มตรวจ (Spot Check) screen](/assets/screenshots/spot-check/index.png)

## 1. ภาพรวม

**Spot check** คือการนับบางส่วนแบบเจาะจงของสินค้าหรือตำแหน่งจัดเก็บที่เลือก ดำเนินการเพื่อยืนยันว่าปริมาณ on-hand ตรงกับยอดที่บันทึก ไม่เหมือนกับ **physical count** เต็มที่นับทุกสินค้าในทุกตำแหน่งบน cycle ที่กำหนด spot check โฟกัสที่ scope ที่จงใจให้แคบ — SKU มูลค่าสูงไม่กี่ตัว ชั้นเดียว ห้องเก็บหนึ่งห้อง หรือสินค้าที่ถูก flag โดย exception report ทำให้ spot check เร็วพอที่จะดำเนินการในชั่วโมงทำการปกติโดยไม่ต้อง freeze การเคลื่อนไหวสต๊อก

โดยทั่วไป Spot check ถูก **trigger** ด้วยรูปแบบใดรูปแบบหนึ่งจากสามรูปแบบ: *การสุ่มตัวอย่าง* (หมุนเวียนผ่านสินค้าเพื่อรักษาวินัยการนับทั่วไป) *การเลือกตาม risk* (สินค้ามูลค่าสูง ขโมยบ่อย หรือเคลื่อนไหวเร็ว ตรวจถี่กว่า) และการตรวจ *event-driven* (หลังต้องสงสัยว่ามีความไม่ตรง ข้อพิพาทการจัดส่ง ข้อผิดพลาดของระบบ หรือเหตุการณ์ loss-prevention) Workflow ปกติสั้นและจบในตัว: inventory controller เลือกสินค้าใน scope counter ดำเนินการนับ ระบบเปรียบเทียบปริมาณที่นับกับ on-hand ผลต่างที่เกินเกณฑ์ถูก review และ recount หรือยอมรับ และผลต่างที่อนุมัติถูก post เป็น **inventory adjustments** เพื่อให้ยอด perpetual สะท้อนความเป็นจริง

เนื่องจาก Spot check เร็วในการเริ่มและทำซ้ำง่าย จึงเป็นการควบคุมหลักในโปรแกรม inventory ใด ๆ — จับการสูญเสีย ความผิดพลาดการนับ และความผิดพลาดของกระบวนการตั้งแต่เนิ่น ๆ ระหว่าง cycle ที่ยาวกว่าของ physical count แบบเป็นทางการ

> **TODO:** ดึงเนื้อหาจาก `../carmen-inventory-frontend/` (UI flow) และ `../carmen-inventory-frontend-e2e/` (test scenarios) ไม่มี source folder carmen/docs สำหรับโมดูลนี้

## 2. บริบททางธุรกิจ

ในการดำเนินงานโรงแรม spot check ให้ **การยืนยันรายวันหรือรายสัปดาห์** ของสินค้าเสี่ยงสูง — สุราพรีเมียม โปรตีนชั้นดี amenity แบรนด์ ของควบคุม — โดยไม่มีการรบกวนการดำเนินงานจากการนับเต็ม การวิ่ง check สั้น ๆ ถี่ ๆ บนสินค้าที่เสี่ยงต่อการสูญเสียมากที่สุด ผู้ดำเนินการปิด gap การมองเห็นระหว่าง physical count ที่ตามตาราง (ปกติเดือนหรือไตรมาส) กับการเคลื่อนไหวสต๊อกประจำวัน

การควบคุมนี้รับใช้สองวัตถุประสงค์ที่เสริมกัน ประการแรก เป็นเครื่องมือ **loss-prevention**: การนับเจาะจงบนหมวดที่เสี่ยงขโมยหรือพิลเฟอเรจขัดขวางการสูญเสียและเปิดเผยปัญหาขณะที่ trail ยังร้อนพอที่จะสืบสวน ประการที่สอง เป็น **ตัวเสริมของ cycle physical-count รายงวด**: ด้วยการสุ่มตัวอย่างต่อเนื่อง finance และ operations ได้รับการประกันต่อเนื่องว่ายอด perpetual เชื่อถือได้ มากกว่าการเรียนรู้เรื่องความไม่ตรงเฉพาะปลายเดือนเท่านั้น เมื่อรวมกัน spot check ลด shock ของผลต่าง ณ เวลาปิดและทำให้การรายงาน cost-of-goods น่าเชื่อถือตลอดงวด

## 3. แนวคิดสำคัญ

- **Selection Criteria**: กฎที่ใช้เลือกสินค้าหรือตำแหน่งที่จะนับ สามโหมดทั่วไปคือ *random* (ระบบเลือกตัวอย่างเพื่อหมุนเวียนการครอบคลุม) *risk-based* (สินค้ามูลค่าสูง เคลื่อนไหวเร็ว หรือผันผวนในประวัติ เลือกบนความถี่ที่กำหนด) และ *triggered* (เหตุการณ์เจาะจง — รายงานเหตุการณ์ ต้องสงสัยข้อผิดพลาด ข้อพิพาทการจัดส่ง — กระตุ้นการตรวจ)
- **Count Scope**: ขอบเขตของ spot check หนึ่งครั้ง — รายการ SKU ชั้นหรือ bin เจาะจง sub-location หรือหมวดหมู่ Scope จงใจให้แคบเพื่อให้การนับเสร็จเร็วโดยไม่ต้อง freeze กิจกรรม inventory อื่น
- **Variance Threshold**: tolerance (ปริมาณสัมบูรณ์หรือเปอร์เซ็นต์ของ on-hand) ที่ผลต่าง counted-vs-system ต้องถูกสืบสวน ผลต่างภายใน threshold อาจ post อัตโนมัติ; ผลต่างเกินต้อง recount และ/หรืออนุมัติ
- **Recount**: การนับ physical รอบที่สอง โดยปกติดำเนินการโดย counter ที่แตกต่าง ใช้เมื่อการนับครั้งแรกผลิตผลต่างเกิน threshold ผล recount คือสิ่งที่ถูกเปรียบเทียบกับยอดระบบสำหรับการตัดสินผลต่างขั้นสุดท้าย
- **Posting Workflow**: ลำดับที่ผลต่างที่อนุมัติกลายเป็นรายการระบบ — ผลต่างถูก review, reason ของ adjustment ถูกกำหนด, รายการถูกอนุมัติ และธุรกรรม **inventory adjustment** ถูก post เพื่ออัปเดตยอด perpetual และบัญชี GL ที่เกี่ยวข้อง

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| Inventory Controller | กำหนด selection criteria จัดตารางและเริ่ม spot check review ผลต่าง อนุมัติหรือปฏิเสธคำขอ recount และอนุมัติ adjustment สำหรับการ post |
| Counter | ดำเนินการนับ physical ของสินค้าหรือตำแหน่งใน scope และบันทึกปริมาณที่นับได้อย่างถูกต้องและทันเวลา |
| Auditor | review ผล spot check หลักฐาน recount และ adjustment ที่ post อย่างเป็นอิสระเพื่อยืนยันว่าการควบคุมทำงานและการสูญเสียได้รับการสืบสวน |

## 5. โมดูลที่เกี่ยวข้อง

**กระแสข้ามโมดูล:**
- [[inventory]] — spot check ยืนยัน subset ของยอด inventory
- [[inventory-adjustment]] — ผลต่างถูก post เป็น adjustment
- [[physical-count]] — คู่เทียบการนับเต็ม

**การกำหนดค่าหลัก:**
- [[master-data/unit]] — หน่วยนับสำหรับแต่ละบรรทัด spot-check
- [[master-data/location]] — (sub-)ตำแหน่งใน scope สำหรับ spot check
- [[master-data/adjustment-type]] — reason code ใช้เมื่อ post adjustment ผลต่าง
- [[system-config/workflow]] — workflow การอนุมัติสำหรับ recount และการ post ผลต่าง
- [[access-control/user-location]] — จำกัดตำแหน่งที่ผู้ใช้สามารถ spot-check ได้
- [[reporting-audit/activity]] — log กิจกรรม spot-check และ recount สำหรับ audit

## 6. แหล่งอ้างอิง

- Concepts: (ไม่มี source — ดู TODO ใน section 1)
- Frontend: `../carmen-inventory-frontend/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. หน้าในโมดูลนี้

- [[spot-check/01-data-model]] — เอนทิตี ฟิลด์ ความสัมพันธ์ enum (`tb_spot_check`, `tb_spot_check_detail` พร้อม comment สองตาราง; enum สองตัว `enum_spot_check_status` / `enum_spot_check_method`)
- [[spot-check/02-business-rules]] — การตรวจสอบ การคำนวณ การกำหนดสิทธิ์ การ posting กฎข้ามโมดูล (`SPC_VAL_*` / `SPC_CALC_*` / `SPC_AUTH_*` / `SPC_POST_*` / `SPC_XMOD_*`)
- [[spot-check/03-user-flow]] — ภาพรวมวงจรชีวิตเอกสาร + สารบัญ persona
  - [[spot-check/03-user-flow-inventory-controller]] — เส้นทาง Inventory Controller
  - [[spot-check/03-user-flow-counter]] — เส้นทาง Counter
  - [[spot-check/03-user-flow-audit-config]] — เส้นทาง Auditor + (โดยปริยาย) Sysadmin
- [[spot-check/04-test-scenarios]] — ภาพรวม test scenarios + scenario การส่งต่อข้าม persona + เป้าหมาย mapping E2E
  - [[spot-check/04-test-scenarios-inventory-controller]] — scenarios Inventory Controller
  - [[spot-check/04-test-scenarios-counter]] — scenarios Counter
  - [[spot-check/04-test-scenarios-audit-config]] — scenarios Auditor + Sysadmin

> **Status:** หน้าย่อยทั้งหมดอยู่ระดับ skeleton (~50-100 บรรทัดต่อหน้า) แต่ละหน้ามี TODO ชัดเจนชี้ไปที่ source ต้นน้ำที่ต้องใช้เมื่อเติม (`../carmen-inventory-frontend/` สำหรับ UI flow; `../carmen-inventory-frontend-e2e/tests/` สำหรับ E2E specs — ยังไม่มี spec spot-check) Data-model section อ้างอิงจาก Prisma schema (`tb_spot_check*` เป็น **table set ของตัวเอง** — เอนทิตี 4 ตัว enum 2 ตัว — *ไม่* แชร์กับ `tb_physical_count*`; ทั้งสองโมดูลเป็นลูกพี่ลูกน้องเชิงแนวคิดที่ทั้งคู่ roll up ไปยัง [[inventory-adjustment]] ไม่ใช่ infrastructure ที่แชร์); business-rules แนะนำ catalog `SPC_*` rule-ID ที่เสนอซึ่งต้องการการยืนยันจาก carmen/docs; user-flow และ test-scenarios เป็น placeholder เชิงโครงสร้าง
