---
title: ใบขอซื้อ — เส้นทางผู้ใช้งาน
description: วงจรเอกสารและไฟล์เส้นทางตาม persona สำหรับโมดูล purchase-request
published: true
date: 2026-05-15T09:00:00.000Z
tags: purchase-request, user-flow, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# ใบขอซื้อ — เส้นทางผู้ใช้งาน

## 1. ภาพรวม

หน้านี้เป็น **จุดเริ่มต้นภาพรวม** ของชุดเอกสารเส้นทางผู้ใช้งานสำหรับโมดูล `purchase-request` ครอบคลุมวงจรชีวิตของเอกสารใบขอซื้อหนึ่งฉบับ — ส่วนหัว PR (`tb_purchase_request`) พร้อมบรรทัดรายละเอียดอย่างน้อยหนึ่งบรรทัด (`tb_purchase_request_detail`) — ตั้งแต่ตอนที่ผู้ร้องขอบันทึกร่างครั้งแรก ผ่านห่วงโซ่การอนุมัติหลายระดับ ไปจนถึงการแปลงเป็นใบสั่งซื้อหรือการยุติด้วยการ void / cancel persona ที่เกี่ยวข้องประกอบด้วย **ผู้ร้องขอ (Requestor)** (สร้างและแก้ไข PR), ห่วงโซ่ **ผู้อนุมัติ (Approver)** (Department Head, Budget Controller, Finance Officer / Manager และระดับที่ escalate), **ผู้จัดซื้อ (Purchaser)** (แปลง PR ที่อนุมัติแล้วเป็น PO), **ผู้จัดการฝ่ายจัดซื้อ (Procurement Manager)** (กำกับดูแลและอนุมัติรายการมูลค่าสูง) และบทบาท **Audit / Config** (Auditor สำหรับการตรวจสอบแบบ read-only และ System Administrator สำหรับการตั้งค่า workflow) แค็ตตาล็อก role อย่างเป็นทางการอยู่ใน [index.md](./index.md) หัวข้อ 4

หัวข้อ 2 ด้านล่างคือ **state machine แบบ global** — รายการ transition ตามค่ามาตรฐานของ `enum_purchase_request_doc_status` โดยไม่ผูกกับ persona ใด ๆ ส่วนไฟล์ตาม persona (ลิงก์อยู่ในหัวข้อ 3) จะอธิบาย *เส้นทาง* ของ persona นั้นผ่าน state machine — จุดเริ่มต้น, action ที่ใช้ได้, การแยกสาขาในการตัดสินใจ และการ handoff ที่จบบทบาทของ persona นั้น หัวข้อ 4 สรุปการ handoff ข้าม persona ที่เชื่อมเส้นทางแต่ละเส้นเข้าด้วยกัน อ่านภาพรวมนี้ก่อนเพื่อยึดวงจรชีวิตให้แน่น แล้วค่อยเจาะลงไปที่ไฟล์ persona ที่ตรงกับ role ของคุณ

## 2. วงจรเอกสาร

status ของเอกสาร PR เก็บใน `tb_purchase_request.pr_status` และจำกัดให้ใช้เฉพาะค่าที่ประกาศใน `enum_purchase_request_doc_status` ได้แก่ `draft`, `in_progress`, `voided`, `approved`, `completed`, `cancelled` ตารางด้านล่างแสดง transition ที่ได้รับอนุญาตระหว่าง state เหล่านี้ การ transition อื่นนอกตารางจะถูก workflow engine ปฏิเสธ

| จากสถานะ | การกระทำ | ไปยังสถานะ | ผู้มีสิทธิ์ | เงื่อนไขก่อนหน้า |
| -------- | -------- | ---------- | ----------- | ---------------- |
| `(none)` | สร้าง | `draft` | ผู้ร้องขอ (Requestor) | validate ฟิลด์ส่วนหัว (`requestor_id`, `department_id`, `pr_date`, `workflow_id`); ยังไม่ต้องมีบรรทัด |
| `draft` | บันทึก (แก้ไข) | `draft` | ผู้ร้องขอ (เจ้าของ PR) | PR ยังอยู่ในความครอบครองของผู้ร้องขอ; stage ใน workflow ยังไม่เดินหน้า |
| `draft` | ส่ง (submit) | `in_progress` | ผู้ร้องขอ (เจ้าของ PR) | มีบรรทัดที่ยังไม่ถูกลบอย่างน้อย 1 รายการ (`PR_VAL_006`); ผ่าน validate รายบรรทัดทั้งหมด; `workflow_id` ที่เลือก active ใน scope `purchase-request` สร้าง soft commitment งบประมาณตอน transition |
| `draft` | ยกเลิก | `cancelled` | ผู้ร้องขอ (เจ้าของ PR) | PR ยังไม่เคย submit (ยังอยู่ในมือผู้ร้องขอ); stage ใน workflow ไม่เคยเดินหน้า ปลดการแก้ไขที่ค้างอยู่ |
| `in_progress` | อนุมัติ (stage นี้ ไม่ใช่ stage สุดท้าย) | `in_progress` | ผู้อนุมัติของ stage ปัจจุบัน | ผู้อนุมัติถูกผูกกับ `workflow_current_stage` ปัจจุบันด้วย `stage_role = approve`; `last_action` ถูกตั้งเป็น `approved` และ cursor ของ stage เลื่อนไปขั้นถัดไป |
| `in_progress` | อนุมัติ (stage สุดท้าย) | `approved` | ผู้อนุมัติของ stage สุดท้าย | ผู้อนุมัติถูกผูกกับ stage สุดท้าย; stage ก่อนหน้าทุกขั้นเซ็นอนุมัติครบ; soft commitment งบประมาณยังคงค้างไว้รอการแปลงเป็น PO |
| `in_progress` | ส่งกลับ (send-back) | `draft` | ผู้อนุมัติคนใดในห่วงโซ่ | ต้องระบุเหตุผล; ปลด soft commitment งบประมาณจนกว่าจะส่งใหม่ บันทึก audit comment |
| `in_progress` | ปฏิเสธ (reject) | `cancelled` | ผู้อนุมัติคนใดในห่วงโซ่ | ต้องระบุเหตุผล; ปลด soft commitment งบประมาณ; workflow ยุติและไม่อนุญาตให้กระทำการใด ๆ ต่อ |
| `in_progress` | void (โมฆะ) | `voided` | System Administrator (หรือ role ที่ได้รับอำนาจสูง) | ต้องระบุเหตุผล; ใช้สำหรับการ void เชิงบริหารหลัง submit (เช่น เอกสารซ้ำ ปัญหา compliance) ปลด soft commitment งบประมาณ |
| `in_progress` | escalate (เกิน threshold) | `in_progress` | workflow engine / ผู้อนุมัติของ stage ปัจจุบัน | `base_total_amount` ในส่วนหัวเกิน threshold มูลค่าสูงที่กำหนด; route ไปยัง Procurement Manager เป็น stage ถัดไป สถานะคงเดิมแต่ cursor ของ stage กระโดด |
| `approved` | แปลงเป็น PO | `completed` | ผู้จัดซื้อ (Purchaser) | บรรทัดที่อนุมัติทุกบรรทัดถูกสะพานไปยัง `tb_purchase_order` หนึ่งใบหรือมากกว่า; PR ปิดไม่ให้แปลงอีก soft commitment แข็งตัวกลายเป็น commitment ของ PO |
| `approved` | void (โมฆะ) | `voided` | System Administrator | ใช้เมื่อ PR ที่อนุมัติแล้วต้องถูกถอนก่อนการแปลง (พบยาก; ต้องระบุเหตุผล) |

## 3. ดัชนีตาม Persona

แต่ละ persona ด้านล่างมีไฟล์เจาะลึกแยกที่อธิบายจุดเริ่มต้น, เส้นทางหลัก, สาขาการตัดสินใจ และจุดสิ้นสุด slug ใน URL ตรงกับ role ของ persona; คลิกลิงก์เพื่อเปิดมุมมองตาม persona

- [Requestor](./03-user-flow-requestor.th.md) — สร้างและส่ง PR, ตอบสนองต่อการส่งกลับ, ยกเลิกร่างที่ตัวเองเป็นเจ้าของ
- [Approver](./03-user-flow-approver.th.md) — ห่วงโซ่การอนุมัติหลายระดับ (Department Head, Budget Controller, Finance Officer / Manager) พร้อม action approve / send-back / reject / split-reject ในแต่ละ stage
- [Purchaser](./03-user-flow-purchaser.th.md) — รับ PR ที่อนุมัติแล้ว, ตรวจสอบการ allocate vendor และราคา, และแปลงเป็นใบสั่งซื้อ
- [Procurement Manager](./03-user-flow-procurement-manager.th.md) — กำกับดูแลฝ่ายจัดซื้อ, อนุมัติ PR มูลค่าสูงหรือที่ถูก escalate, ปรับ vendor ranking และกฎ Allocate Vendor
- [Audit / Config](./03-user-flow-audit-config.th.md) — Auditor (ตรวจสอบ PR และ activity log แบบ read-only) และ System Administrator (ตั้งค่า stage ของ workflow, threshold, กฎ delegation)

## 4. การส่งต่อข้าม Persona

ตารางด้านล่างจับโมเมนต์ที่ PR ย้ายจากความรับผิดชอบของ persona หนึ่งไปยังอีก persona หนึ่ง การ handoff แต่ละครั้งยึดกับสถานะของเอกสาร ณ จุดที่ส่งต่อ

| จาก persona | ตัวกระตุ้น | ไปยัง persona | สถานะเอกสาร ณ จุดส่งต่อ |
| ----------- | ---------- | ------------- | ------------------------- |
| ผู้ร้องขอ (Requestor) | กด Submit | ผู้อนุมัติ stage แรก (โดยทั่วไปคือ Department Head) | `in_progress` (cursor ของ stage อยู่ที่ stage อนุมัติแรก) |
| ผู้อนุมัติ (Approver) stage N (ไม่ใช่ stage สุดท้าย) | อนุมัติที่ stage นี้ | ผู้อนุมัติ (Approver) stage N+1 | `in_progress` (cursor ของ stage เลื่อนไป stage ถัดไป) |
| ผู้อนุมัติ (Approver) stage สุดท้าย | อนุมัติที่ stage สุดท้าย | ผู้จัดซื้อ (Purchaser) | `approved` |
| ผู้อนุมัติ (Approver) stage ใด ๆ | ส่งกลับพร้อมเหตุผล | ผู้ร้องขอ (Requestor) | `draft` (เก็บประวัติการแก้ไขและความเห็นของผู้อนุมัติไว้) |
| ผู้อนุมัติของ stage ปัจจุบัน | ยอดในส่วนหัวเกิน threshold มูลค่าสูง | ผู้จัดการฝ่ายจัดซื้อ (Procurement Manager) | `in_progress` (escalate แล้ว; cursor ของ stage อยู่ที่ stage ของ Procurement Manager) |
| ผู้จัดซื้อ (Purchaser) | แปลงเป็น PO | โมดูล Purchase Order (และโดยอ้อม Receiver / GRN ปลายน้ำ) | `completed` (สร้าง `tb_purchase_order` หนึ่งใบหรือมากกว่า โดยลิงก์กลับมาที่ PR) |
| System Administrator | void พร้อมเหตุผล | Auditor (เพื่อตรวจสอบย้อนหลังเท่านั้น) | `voided` |
| ผู้อนุมัติ (Approver) | reject พร้อมเหตุผล | Auditor (เพื่อตรวจสอบย้อนหลังเท่านั้น) | `cancelled` |

## 5. แหล่งอ้างอิง

- `../carmen/docs/purchase-request-management/PR-User-Experience.md` — แหล่งหลักสำหรับ flow ฝั่งประสบการณ์ผู้ใช้ (การสร้าง, การอนุมัติ, การเปรียบเทียบ vendor, การใช้ template)
- `../carmen/docs/purchase-request-management/PR-Overview.md` — ภาพรวมโมดูล, user roles, จุดเชื่อมต่อกับโมดูลอื่น
- `../carmen/docs/purchase-request-management/purchase-request-module-prd.md` — product requirements ที่ขับเคลื่อน flow
- ไฟล์พี่น้อง: [01-data-model.md](./01-data-model.md) — ค่ามาตรฐานของ `enum_purchase_request_doc_status` ที่ใช้ในหัวข้อ 2
- ไฟล์พี่น้อง: [02-business-rules.md](./02-business-rules.md) — กฎ validation, authorization และ posting ที่อ้างโดย transition แต่ละแถว
