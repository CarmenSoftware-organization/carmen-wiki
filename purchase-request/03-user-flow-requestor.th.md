---
title: ใบขอซื้อ — เส้นทางผู้ใช้งาน — ผู้ร้องขอ (Requestor)
description: เส้นทางผู้ใช้งานของ Requestor ในโมดูล purchase-request
published: true
date: 2026-05-15T09:00:00.000Z
tags: purchase-request, user-flow, requestor, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# ใบขอซื้อ — เส้นทางผู้ใช้งาน — ผู้ร้องขอ (Requestor)

## 1. บทบาทในโมดูลนี้

**ผู้ร้องขอ (Requestor)** คือพนักงานในโรงแรมหรือแผนกที่เป็นจุดเริ่มต้นของใบขอซื้อ — สัญญาณความต้องการต้นน้ำที่อนุมัติให้เริ่มกระบวนการจัดซื้อก่อนที่จะมีพันธะภายนอกใด ๆ กับ vendor ผู้ร้องขอเป็นเจ้าของ PR ขณะอยู่ในสถานะ `draft`: กรอกส่วนหัว (PR type — `General Purchase`, `Market List`, `Asset` — แผนก, สกุลเงิน, ผู้ร้องขอ, วันที่ขอ, วันส่งที่ต้องการ, รหัสงาน/cost code, จุดส่งของ, คำอธิบายและเหตุผล), สร้างรายการบรรทัด (สินค้าจากแคตตาล็อกหรือคำอธิบายอิสระ, store location, จำนวนที่ขอ, จำนวน FOC, หน่วยนับ, ราคาประมาณการต่อหน่วย, ส่วนลด, การคิดภาษี, วันส่งของบรรทัด), แนบเอกสารประกอบ (ใบเสนอราคา, spec, รูปภาพ) แล้วกด submit เมื่อพร้อมให้ผู้อนุมัติพิจารณา บทบาทไม่ได้จบที่การ submit: เมื่อผู้อนุมัติเลือก **Send Back** PR จะกลับไปยัง `draft` และผู้ร้องขอต้องกลับมาแก้ไขแล้วส่งใหม่ และระหว่างที่ PR ยังเป็น `draft` ผู้ร้องขอสามารถยกเลิกได้ทุกเมื่อ ผู้ร้องขอไม่สามารถแก้ไข PR หลัง submit และไม่มีบทบาทในขั้นตอนการอนุมัติ, การ allocate vendor หรือการแปลงเป็น PO ซึ่งเป็นความรับผิดชอบของห่วงโซ่ Approver, Purchaser และ Procurement Manager ตามลำดับ (ดู [index.md](./index.md) หัวข้อ 4)

## 2. จุดเริ่มต้นและเส้นทางหลัก

**จุดเริ่มต้น:** Sidebar → โมดูล **Purchase Request** → หน้ารายการ PR → ปุ่ม **Create New PR** (ทางเลือก: **Create from Template** เมื่อใช้ template ที่บันทึกไว้ หรือกด `Alt+N` จากที่ใดก็ได้ในโมดูล)

**เส้นทางหลัก (happy path):**

1. จากหน้ารายการ PR กด **Create New PR** ระบบสร้างแถวส่วนหัวใหม่โดยตั้ง `pr_status = draft`, สร้างเลขที่อ้างอิงอัตโนมัติ, ตั้ง `pr_date` เป็นวันที่ปัจจุบัน และ pre-fill `requestor_id` จากผู้ใช้ที่ login อยู่
2. กรอกส่วนหัว: เลือก **PR type** (`General Purchase`, `Market List` หรือ `Asset`), ยืนยันหรือเปลี่ยน `department_id`, กำหนด **วันส่งของที่ต้องการ**, เลือก **สกุลเงิน** (ระบบดึงอัตราแลกเปลี่ยนให้อัตโนมัติ), ใส่ **คำอธิบาย / เหตุผล** และเลือก **workflow_id** ที่จะใช้ในขอบเขต `purchase-request` กดบันทึกส่วนหัว (ระบบมี auto-save เมื่อขาดการเชื่อมต่อ)
3. เปิดแท็บ **Items** แล้วกด **Add Item** สำหรับแต่ละบรรทัด: ค้นหาสินค้าในแคตตาล็อก (หรือใช้คำอธิบายอิสระสำหรับรายการที่ไม่อยู่ในแคตตาล็อก), เลือก **store location**, ใส่ **จำนวนที่ขอ** และ **หน่วยนับ**, ใส่ **ราคาประมาณการต่อหน่วย** (หรือยอมรับราคาที่ระบบดึงมาจาก pricelist อัตโนมัติ), ตั้ง **จำนวน FOC**, **ส่วนลด** ระดับบรรทัด, การคิด **ภาษี** และ **วันส่งของ** ของบรรทัด เพิ่ม note ของบรรทัดได้หากจำเป็น
4. ทำซ้ำขั้นตอน 3 จนครบทุกบรรทัดที่ต้องการ ระบบ validate ฟิลด์ที่จำเป็นแบบ inline ในแต่ละบรรทัด (อ้างอิงกฎ: `PR_VAL_006` กำหนดให้มีบรรทัดที่ยังไม่ถูกลบอย่างน้อย 1 รายการตอน submit; validate รายบรรทัดถูกบังคับใช้ก่อนบันทึกบรรทัดได้)
5. ตรวจ **financial summary** บนส่วนหัว: subtotal, total discount, total tax และ grand total ทั้งในสกุลเงินที่ทำรายการและสกุลเงินฐาน ตัวเลขเหล่านี้ roll up มาจากค่าระดับบรรทัดที่ปัดเศษแล้ว (จำนวน 3 ตำแหน่ง, เงิน 2 ตำแหน่ง, exchange rate 5 ตำแหน่ง)
6. เปิดแท็บ **Attachments** แล้วอัปโหลดเอกสารประกอบ — ใบเสนอราคาของ vendor, spec ของสินค้า, รูปภาพ, ใบอนุมัติภายใน เพิ่มคำอธิบายและตั้งค่า visibility ของแต่ละไฟล์
7. (ทางเลือก) สั่งให้ระบบทำ **budget validation** จากส่วนหัว ระบบจะตรวจ availability เทียบกับงบประมาณของแผนกและ cost centre ของผู้ร้องขอ แล้วแสดงสถานะ Available / Warning / Exceeded พร้อม breakdown (งบทั้งหมด, soft commitment จาก PR ฉบับอื่น / PO เปิด, hard commitment) การตรวจนี้เป็นข้อมูลประกอบ — ไม่บล็อก submit
8. ตรวจ PR ทั้งฉบับในแท็บ **Review**: ส่วนหัว, บรรทัดทั้งหมด, ยอดรวม, ไฟล์แนบ และ stage ของ workflow ที่จะรันหลัง submit แก้ไขปัญหาในที่ได้เลย
9. กด **Submit** ระบบรัน validate ทั้งหมดในจังหวะ submit (ฟิลด์ที่จำเป็นในส่วนหัว, อย่างน้อย 1 บรรทัด, validate รายบรรทัด, workflow ที่ active อยู่) เมื่อผ่าน ระบบจะ transition `pr_status` จาก `draft` ไป `in_progress`, เลื่อน `workflow_current_stage` ไปยัง stage อนุมัติแรก, สร้าง **soft budget commitment** ในหมวดงบที่เกี่ยวข้อง, เขียน audit entry และส่ง notification ให้ผู้อนุมัติคนแรก (โดยทั่วไปคือ Department Head) พร้อมสำเนาไปยังผู้ร้องขอ
10. ติดตามความคืบหน้าได้จาก dashboard **My PRs** หรือหน้ารายละเอียดของ PR — workflow stepper แสดง stage ปัจจุบัน, ผู้อนุมัติคนปัจจุบัน และประวัติ action สะสม เส้นทางหลักของผู้ร้องขอจบที่นี่ในกรณี happy path; กลับมาที่เส้นทางนี้อีกเฉพาะกรณี send-back (หัวข้อ 3)

## 3. สาขาการตัดสินใจ

- **ถ้าฟิลด์ที่จำเป็นในส่วนหัวขาดหรือไม่ถูกต้องตอน submit** (เช่น ไม่มี `department_id`, ไม่มี `pr_date`, ไม่มี `workflow_id`, สกุลเงินหรืออัตราแลกเปลี่ยนไม่ถูกต้อง): การ submit จะถูกบล็อก ระบบจะ scroll ไปยังฟิลด์แรกที่มีปัญหาและแสดงข้อความ error แบบ inline PR ยังคงอยู่ใน `draft` แก้ฟิลด์แล้วลอง submit ใหม่
- **ถ้า PR ไม่มีบรรทัดที่ยังไม่ถูกลบเลยตอน submit** (กฎ `PR_VAL_006`): submit จะถูกปฏิเสธพร้อมข้อความ "At least one line is required" PR ยังคงอยู่ใน `draft` เพิ่มบรรทัดอย่างน้อย 1 รายการแล้วลองใหม่
- **ถ้า budget validation รายงาน `Warning` หรือ `Exceeded`**: ระบบแสดงผลกระทบงบประมาณแต่ **ไม่** บล็อก submit (budget check ในจังหวะ submit เป็นข้อมูลประกอบ) ผู้ร้องขอตัดสินใจว่าจะ (a) ลดจำนวนหรือราคาประมาณการแล้ว validate ใหม่, (b) แยก PR ออกเป็นใบเล็กลง, หรือ (c) submit ต่อแล้วให้ Budget Controller อนุมัติหรือปฏิเสธในขั้นถัดไป
- **ถ้าผู้อนุมัติเลือก Send Back** บน PR ที่ submit แล้ว (stage ใดก็ได้): PR จะ transition จาก `in_progress` กลับเป็น `draft`, soft budget commitment ถูกปลดจนกว่าจะ submit ใหม่, เหตุผลของผู้อนุมัติถูกแนบใน activity log และผู้ร้องขอจะได้รับ notification ผู้ร้องขอกลับมาที่หัวข้อ 2 ขั้นตอน 2 (แก้ไขส่วนหัวหรือบรรทัดตามความเห็น) แล้ว submit อีกครั้งในขั้นตอน 9 ประวัติการแก้ไขถูกเก็บรักษาไว้
- **ถ้าผู้ร้องขอต้องการยกเลิก PR ที่ยังไม่ได้ submit**: จากหน้ารายละเอียด PR หรือหน้ารายการ เลือก **Cancel** ขณะที่ PR ยังเป็น `draft` ระบบจะ transition ไปเป็น `cancelled`, ปลดการแก้ไขที่ค้างอยู่ และยุติเอกสาร PR ที่ submit แล้ว (`in_progress`, `approved`) ไม่สามารถถูกยกเลิกโดยผู้ร้องขอได้ — มีเพียง workflow ที่ reject ได้ (transition เป็น `cancelled`) หรือ administrator ที่ void ได้ (transition เป็น `voided`)
- **ถ้าผู้ร้องขอพยายามแก้ไข PR หลัง submit** (`in_progress`, `approved`, `completed`, `voided`, `cancelled`): control ทุกอันเป็น read-only วิธีเดียวที่จะเปลี่ยนเนื้อหาคือต้องขอให้ผู้อนุมัติคนปัจจุบันส่ง PR กลับไปยัง `draft` เมื่อ PR กลับเป็น `draft` แล้ว ผู้ร้องขอจะได้สิทธิ์แก้ไขคืนและเส้นทางจะกลับไปยังหัวข้อ 2 ขั้นตอน 2

## 4. จุดสิ้นสุด / การส่งต่อ

บทบาทหลักของผู้ร้องขอสิ้นสุดเมื่อ PR transition จาก `draft` เป็น `in_progress` ในขั้นตอน 9 ของหัวข้อ 2 ณ จุดนั้นเอกสารหลุดจากความรับผิดชอบของผู้ร้องขอและถูกส่งต่อให้ผู้อนุมัติ stage แรกใน workflow ที่กำหนด (โดยทั่วไปคือ Department Head; ดู [03-user-flow-approver.md](./03-user-flow-approver.md) เมื่อ publish แล้ว) สถานะเอกสาร ณ จุดส่งต่อคือ `in_progress` โดย `workflow_current_stage` ชี้ไปที่ stage อนุมัติแรก และมี soft budget commitment ลงทะเบียนกับแผนกของผู้ร้องขอ

ทิศทาง handoff อีกแบบคือ **กลับมาที่ผู้ร้องขอเมื่อ send-back**: ผู้อนุมัติคนใดในห่วงโซ่อาจส่ง PR กลับเป็น `draft` พร้อมเหตุผล โดยปลด soft commitment การ handoff นี้ไม่ใช่จุดสิ้นสุดจริง — ผู้ร้องขอกลับมาที่หัวข้อ 2 ขั้นตอน 2 เพื่อแก้ไข PR แล้ว submit ใหม่ วงรอบนี้เกิดซ้ำจนกว่า PR จะ approved (stage สุดท้าย), rejected (`cancelled`) หรือ voided (`voided`)

จุดสิ้นสุดจริง (ผู้ร้องขอไม่มี action เพิ่มเติม) ได้แก่:

- **ยกเลิกโดยผู้ร้องขอใน draft** — `pr_status = cancelled`, terminal
- **ปฏิเสธโดยผู้อนุมัติ** — `pr_status = cancelled`, terminal Auditor ตรวจสอบย้อนหลัง
- **void โดย System Administrator** — `pr_status = voided`, terminal Auditor ตรวจสอบย้อนหลัง
- **อนุมัติและแปลงเป็น PO** — `pr_status = completed`, terminal Purchaser เป็นเจ้าของการแปลง; ผู้ร้องขอเห็น PO ที่ linked อยู่ในหน้ารายละเอียด PR เพื่อการ traceability

## 5. แหล่งอ้างอิง

- ภาพรวมหลัก: [03-user-flow.th.md](./03-user-flow.th.md)
- `../carmen/docs/purchase-request-management/PR-User-Experience.md` — แหล่งหลักสำหรับ flow การสร้าง, การ submit และ send-back
- `../carmen/docs/purchase-request-management/PR-Overview.md` — ภาพรวมโมดูล, นิยามบทบาทของ requestor, จุดเชื่อมต่อกับโมดูลอื่น
- `../carmen/docs/purchase-request-management/purchase-request-module-prd.md` — product requirements ที่ขับเคลื่อนเส้นทางของผู้ร้องขอ
- ไฟล์พี่น้อง: [01-data-model.md](./01-data-model.md) — `tb_purchase_request`, `tb_purchase_request_detail`, `enum_purchase_request_doc_status`
- ไฟล์พี่น้อง: [02-business-rules.md](./02-business-rules.md) — `PR_VAL_006` (ต้องมีอย่างน้อย 1 บรรทัด) และ validation อื่น ๆ ในจังหวะ submit
- ไฟล์พี่น้อง: [index.md](./index.md) หัวข้อ 4 — นิยามมาตรฐานของบทบาท Requestor
