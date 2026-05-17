---
title: Carmen Inventory ERP — คู่มือสำหรับนักพัฒนาและทดสอบ
description: หน้าแรกของวิกิ Carmen Inventory ERP — สารบัญโมดูลสำหรับนักพัฒนาและทดสอบ ครอบคลุม procure-to-pay, การควบคุมคลังสินค้า, การคำนวณต้นทุน, การตั้งค่า master และการรายงาน
published: true
date: 2026-05-17T12:00:00.000Z
tags: home, index, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-16T14:00:00.000Z
---

# Carmen Inventory ERP — คู่มือสำหรับนักพัฒนาและทดสอบ

> **At a Glance**
> **กลุ่มผู้ใช้:** นักพัฒนาและ QA ฝั่ง inventory บนแพลตฟอร์ม Carmen Software &nbsp;·&nbsp; **ขอบเขต:** procure-to-pay, การควบคุมคลังสินค้า, การคำนวณต้นทุน, การตั้งค่า master, การรายงาน &nbsp;·&nbsp; สารบัญโมดูล — เริ่มจากหัวข้อที่ตรงกับงานของคุณ แล้วเจาะลึกเข้าไปใน `01-data-model` / `02-business-rules` / `03-user-flow` / `04-test-scenarios`

## 1. เกี่ยวกับวิกินี้

วิกินี้คือคู่มือฉบับอ้างอิงสำหรับนักพัฒนาและวิศวกร QA ที่ทำงานกับ **Carmen Inventory ERP** — ส่วน inventory ของแพลตฟอร์ม Carmen Software สำหรับ supply chain ในอุตสาหกรรมโรงแรม แต่ละหน้าบันทึก data model, กฎทางธุรกิจ, user flow แยกตาม persona และ test scenarios ในระดับรายละเอียดที่นำไปสร้างฟีเจอร์และทวนสอบกับ BRD รวมถึง UI จริงได้ เอกสารฝึกอบรมผู้ใช้ปลายทาง สัญญา vendor portal และเอกสารสถาปัตยกรรมแพลตฟอร์มอยู่ที่อื่น วิกินี้วางอยู่ระดับล่างถัดลงมา ระหว่าง spec กับโค้ด

เนื้อหาถูกจัดตามโมดูลใต้ไดเรกทอรีระดับบนตามภาษา `en/` (ต้นฉบับ) และ `th/` (การติดตามการแปล) แต่ละโฟลเดอร์โมดูลใช้รูปแบบหน้าย่อยเดียวกัน: `01-data-model`, `02-business-rules`, `03-user-flow*`, `04-test-scenarios*` พร้อมหน้าย่อยแยกตาม role ภายใต้ user-flow และ test-scenarios เมื่อโมดูลมีหลาย persona การอ้างอิงข้ามโมดูลใช้ลิงก์แบบ Wiki.js `[[slug]]` เพื่อให้การนำทางอยู่ภายใน locale ปัจจุบัน

## 2. แดชบอร์ด

หน้าหลังเข้าระบบ — KPI tile ข้ามโมดูล, aging bucket และรายการรายการผิดปกติ แต่ละ tile เจาะลงไปยังโมดูล transactional ที่เกี่ยวข้องพร้อมตัวกรองที่เตรียมไว้ล่วงหน้า

- [[dashboard]] — สารบัญของแดชบอร์ดทั้ง 6 หน้า (หลัก, PR, PO, GRN, คลังสินค้า, SR)

## 3. Procure-to-Pay

สายงานจัดซื้อ — จากสัญญาณความต้องการภายในจนถึงการผูกพันกับผู้ขายภายนอก การรับของจริง และการทำ three-way match เพื่อ posting AP

- [[purchase-request]] — เอกสารคำขอภายใน workflow อนุมัติหลายระดับ soft commitment กับงบประมาณ การจัดสรรผู้ขาย และสะพานเชื่อมจาก PR ไปยัง PO
- [[purchase-order]] — เอกสารผูกพันกับผู้ขาย สร้างด้วยมือหรือจาก PR การอนุมัติ PO มูลค่าสูง การส่ง การแก้ไขภายใต้ข้อจำกัดหลัง `sent`
- [[good-receive-note]] — การรับของจริงเทียบกับ PO (หรือแบบ standalone สำหรับการรับฉุกเฉิน) การบันทึก lot/expiry การแยกหน้าที่กับผู้สร้าง PO commit จะกระตุ้นการเขียน inventory และ cost layer
- [[vendor-pricelist]] — vendor master, ความครอบคลุมของ pricelist, เกณฑ์การจัดอันดับ, tolerance band ที่ป้อน semantic ของ snapshot ใน PR/PO และเส้นทางการตรวจค่าผิดเพี้ยน

## 4. การควบคุมคลังสินค้า

ฝั่ง inventory — ยอดคงเหลือสต๊อก การจัดการ lot การปรับปรุง และจังหวะ count กับ spot-check ที่เป็นเงื่อนไขปิดงวด

- [[inventory]] — ระบบบันทึกหลักของยอดสต๊อกตาม สินค้า × คลัง × location พร้อมต้นทุนต่อหน่วยปัจจุบัน/เฉลี่ย จำนวน on-hand / allocated / available และสถานะ workflow ของการเคลื่อนไหว
- [[inventory-adjustment]] — การแก้ไขสต๊อกด้วยมือ stock-in (`tb_stock_in`) และ stock-out (`tb_stock_out`) การสร้าง layer ใหม่ของ FIFO เทียบกับการบริโภค layer เก่าที่สุด การ re-average ของ AVCO เทียบกับ cost hold
- [[physical-count]] — การนับแบบเต็มขอบเขตช่วงปลายงวด ล็อค location ขณะ `IN PROGRESS` การจัดการ variance เงื่อนไข Stage-3 สำหรับปิดงวด
- [[spot-check]] — cycle count แบบขอบเขตแคบ เงื่อนไข Stage-2 สำหรับปิดงวด จังหวะเร็วกว่า physical count แบบเต็ม
- [[store-requisition]] — การโอนสต๊อกภายใน (สามแบบ: DIR, CONS, INV-to-INV) ไม่มีการ re-average ของ AVCO ต้นทุนไหลผ่านที่ layer เดิม
- [[product]] — product master, แคตตาล็อก SKU, หน่วย UoM ฐานของ inventory, การกำหนดวิธีคิดต้นทุนต่อสินค้า

## 5. การคำนวณต้นทุนและสูตรอาหาร

วิธีคำนวณต้นทุนต่อหน่วย คำนวณซ้ำ และการนำไปใช้ฝั่งสูตรอาหาร / เมนู

- [[costing]] — เครื่องคำนวณต้นทุน AVCO เทียบกับ FIFO ธุรกรรมที่กระตุ้น (GRN, การปรับสต๊อก, physical count) การไหลผ่านสำหรับ SR semantic ของ period-lock เลือก AVCO/FIFO ที่การตั้งค่า Business Unit และเปลี่ยนไม่ได้หลัง go-live
- [[recipe]] — recipe master, รายการวัตถุดิบ, yield, flag สารก่อภูมิแพ้ ข้อมูลเข้าของ menu-engineering ที่บริโภคผลลัพธ์จาก cost engine

## 6. การตั้งค่า Master

ข้อมูล master และการตั้งค่าข้ามฟังก์ชันที่ทุกโมดูล transactional บริโภค

- [[master-data]] — vendor, currency, tax profile, unit (UoM), department, location, dimension — ข้อมูลอ้างอิงที่ถูก snapshot ลงในเอกสารธุรกรรมทุกชุด
- [[system-config]] — นิยาม workflow, รูปแบบเลขรันนิ่ง, การตั้งค่า dimension หน้านโยบายที่ขับเคลื่อนการตัดสินใจอนุมัติ / posting / numbering ทุกครั้ง
- [[access-control]] — แผนที่ role / permission, gate ของ user action, กฎ segregation of duties แกนหลักของการอนุญาตที่กฎ `*_AUTH_*` ทุกข้ออ้างอิง
- [[templates]] — นิยาม scaffold ที่ใช้ซ้ำได้ (PR, Price List) ที่ถูก clone เข้าสู่ record transactional ใหม่ เป็น seed อย่างเดียว ไม่เข้า workflow ด้วยตัวเอง

## 7. การรายงานและตรวจสอบ

หน้า observation และ governance นอกเส้นทางหลัก

- [[reporting-audit]] — activity log, ไฟล์แนบ, การแจ้งเตือน, แคตตาล็อกรายงาน, widget และกลไก audit case file ที่ persona Auditor และ System Administrator อ้างอิงในทุกโมดูล transactional

## 8. วิธีนำทาง

`index.md` ของแต่ละโมดูลคือหน้าเริ่มต้น (ภาพรวม, บริบททางธุรกิจ, แนวคิดสำคัญ, บทบาทและ Persona, โมดูลที่เกี่ยวข้อง, แหล่งข้อมูลอ้างอิง, หน้าในโมดูลนี้) จากตรงนั้น:

- **Data model** → `01-data-model.md` — เอนทิตี Prisma, enum, ความสัมพันธ์, ความละเอียดการปัดเศษ
- **Business rules** → `02-business-rules.md` — การตรวจสอบ การคำนวณ การกำหนดสิทธิ์ การ posting และกฎข้ามโมดูล พร้อมรหัสกฎที่เสถียร (`<MOD>_VAL_NNN`, `<MOD>_AUTH_NNN` ฯลฯ) Section 5.1 ในโมดูล transactional มีตาราง **Status Lifecycle — Live UI vs BRD Mapping** และ callout ที่ชี้ความไม่ตรงกัน
- **User flow** → `03-user-flow.md` (ภาพรวมพร้อม state-machine Mermaid) + หน้าเจาะลึกตาม persona `03-user-flow-{role}.md` พร้อม Mermaid แสดงตำแหน่งใน workflow และ Permission Matrix
- **Test scenarios** → `04-test-scenarios.md` (ข้าม persona) + หน้าเจาะลึกตาม persona พร้อม scenario แบบ happy-path / permission / validation / edge-case ที่ map ไปยังรหัสกฎและไฟล์ E2E spec

## 9. แหล่งข้อมูลอ้างอิง

วิกินี้สังเคราะห์จากแหล่งข้อมูลภายนอกเหล่านี้ (sibling repo ในองค์กร Carmen Software):

- `../carmen/docs/` — เอกสารแนวคิดและการออกแบบหลักของทุกโมดูล
- `../carmen-inventory-frontend/` — Next.js UI ของ inventory แหล่งข้อมูลอ้างอิงของพฤติกรรมหน้าจอ
- `../carmen-turborepo-backend-v2/` — Turborepo monorepo, REST API surface
- `../micro-report/`, `../micro-cronjobs/` — Go microservice สำหรับการรายงานและงานตามตารางเวลา
- `../carmen-turborepo-backend-bruno/` — Bruno API collection รูป request/response ที่แน่นอน
- `../carmen-inventory-frontend-e2e/` — Playwright suite สเปคแบบรันได้สำหรับพฤติกรรม
- `Test_case/` (อยู่นอก repo วิกิ) — ไฟล์ Test_case ระดับหน้าจอและระดับ process ที่ callout ความไม่ตรงกันอ้างอิง บันทึกสภาพ UI จริงที่วันที่แน่นอน

เมื่อสงสัยว่าระบบทำงานจริงอย่างไร implementation และ E2E test ชนะ `../carmen/docs/`; `../carmen/docs/` ชนะความทรงจำ
