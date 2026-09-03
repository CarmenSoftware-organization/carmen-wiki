---
title: ใบเบิกของสโตร์ (Store Requisition) — User Flow — Receiver
description: flow ของ Receiver ในโมดูล store-requisition — persona ที่ยังไม่ยืนยัน; บันทึกสิ่งที่ยืนยันได้และยังไม่ยืนยันใน source ปัจจุบัน
published: true
date: 2026-07-15T12:00:00.000Z
tags: store-requisition, user-flow, receiver, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:30:00.000Z
---

# ใบเบิกของสโตร์ (Store Requisition) — User Flow — Receiver

> **At a Glance**
> **Persona:** Receiver — **ยังไม่ยืนยันว่าเป็น persona แยกใน source ปัจจุบัน** &nbsp;·&nbsp; **โมดูล:** [store-requisition](/th/inventory/store-requisition)
> **หน้านี้บันทึกอะไร:** เหตุใด flow "Receiver" ที่เคยบรรยายไว้ (การยืนยันการรับจริง + escalation ความคลาดเคลื่อน) ไม่ตรงกับ source ปัจจุบัน และสิ่งที่ยืนยันได้จริง

> ⚠️ **แก้ไขครั้งใหญ่รอบนี้.** เวอร์ชันก่อนหน้าของหน้านี้บรรยาย persona Receiver ที่เอาท์เลตปลายทางซึ่งยืนยันการรับจริงเทียบกับ `issued_qty` และข้อมูล lot ยก event "ความคลาดเคลื่อน" อย่างเป็นทางการที่ escalate ไปยัง Inventory Controller และส่งต่อการ resolve ไปยัง `inventory-adjustment` ไม่มีสิ่งใดในนี้พบใน source ปัจจุบัน:
> - การค้นทั้ง repo ของ `carmen-turborepo-backend-v2` และ `carmen-inventory-frontend-react` หาคำว่า `receiver`, `discrepancy` และ route/component สำหรับการยืนยันรับที่ปลายทางให้ผลลัพธ์เป็น **ศูนย์** ทุกที่ในโมดูล `store-requisition` ไม่มีหน้าจอสำหรับ receiver ไม่มี comment-type แบบ discrepancy และไม่มี escalation event
> - `enum_stage_role` (`create`, `approve`, `purchase`, `issue`, `view_only`) ไม่มีสมาชิก `receiver` และ SR frontend (`routes/store-operation/store-requisition/`) ไม่มี route หรือ component ที่ชื่อหรือรูปแบบเป็นหน้ายืนยันรับ
> - ตาราง comment ที่หน้านี้เวอร์ชันก่อนหน้าอ้างว่าเป็นพื้นที่เขียนของ Receiver (`tb_store_requisition_comment`, `tb_store_requisition_detail_comment`) เป็น **ตารางทั่วไป** — ผู้ใช้ใดก็ตามที่มีสิทธิ์อ่าน SR สามารถ append comment ประเภท `user` ผ่าน `store-requisition-comments.controller.ts` / `store-requisition-detail-comments.controller.ts` ไม่มี sub-type `discrepancy` ไม่มีข้อจำกัดว่าเขียนได้เฉพาะปลายทาง และไม่มี escalation อัตโนมัติไปยัง role ใด
> - เอกสาร SR ไม่มี transition `completed → <อะไรก็ตาม>` เลยเมื่อถึง `completed` แล้ว (ยืนยันใน `store-requisition.service.ts`) — ดังนั้นแม้แต่ comment ทั่วไปก็ไม่สามารถขยับเอกสารได้; ส่วนนั้นของคำบรรยายก่อนหน้า ("ไม่เปลี่ยน `doc_status`") บังเอิญถูกต้อง แต่ด้วยเหตุผลที่ผิด (ไม่มี action ของ receiver ที่จะทำให้สถานะไม่เปลี่ยน เพราะไม่มี action ของ receiver อยู่เลย)
>
> หน้านี้ถูกเก็บไว้ (แทนที่จะลบ) เพราะชุด persona ของโมดูลระบุชื่อ Receiver ไว้ในตาราง role แบบ legacy บนหน้า landing และตาราง cross-persona ของ [03-user-flow.md](./03-user-flow.md) ที่เป็นแม่ เนื้อหาด้านล่างบันทึกการแก้ไขแทนที่จะพูดซ้ำ flow ที่แต่งขึ้น

## 1. สิ่งที่ยืนยันได้และยังไม่ยืนยัน

| ข้อความจากเวอร์ชันก่อนหน้า | สถานะ |
|---|---|
| Persona "Receiver" ที่เอาท์เลตปลายทางแยกจาก Requester/Approver/Fulfiller | **ยังไม่ยืนยัน.** ไม่พบ route, component หรือสมาชิก `enum_stage_role` |
| การยืนยันการรับจริงเทียบกับ `issued_qty` และข้อมูล lot | **ไม่ได้ implement** ไม่มีหน้าจอสำหรับ receiver ใน `routes/store-operation/store-requisition/` |
| ประเภท comment / flag "ความคลาดเคลื่อน" ที่แยกจาก comment ปกติ | **ไม่ได้ implement** `tb_store_requisition_comment.type` / `tb_store_requisition_detail_comment.type` คือ `enum_comment_type` ทั่วไปที่ใช้ร่วมกัน (`user` / `system`) — ไม่มีค่าหรือ field เฉพาะสำหรับความคลาดเคลื่อน |
| การ escalate ความคลาดเคลื่อนไปยัง queue "Inventory Controller" | **ไม่ได้ implement** ไม่พบ escalation route, notification type หรือ queue |
| ผู้ใช้ใดก็ตามที่มีสิทธิ์อ่านสามารถ append comment แบบอิสระบน SR ที่ `completed` | **ยืนยันว่าจริง** — ผ่าน endpoint comment ทั่วไป เปิดให้ทุก persona ไม่ใช่เฉพาะ receiver |
| รูปแบบ SR + GRN คู่กันสำหรับการโอนระหว่างคลัง โดยฝั่ง GRN จัดการการรับที่ปลายทางอย่างเป็นทางการ | **ยังไม่ได้ตรวจสอบซ้ำอย่างเป็นอิสระในรอบนี้** — สืบทอดจากเวอร์ชันก่อนหน้าของหน้านี้; ถือว่ายังไม่ยืนยันจนกว่า resync ของโมดูล [good-receive-note](/th/inventory/good-receive-note) จะตรวจสอบเทียบกับ SR โดยเฉพาะ |

## 2. ควรทำอย่างไรกับหน้านี้

จนกว่าจะยืนยันว่ามีฟีเจอร์การยืนยันรับหรือ flag ความคลาดเคลื่อนที่เอาท์เลตปลายทางจริง อย่าถือว่าข้อความ "Receiver ยืนยันการรับ", "flag ความคลาดเคลื่อน" หรือ "escalate ไปยัง Inventory Controller" ที่ปรากฏในหน้าอื่นของโมดูลนี้เป็นพฤติกรรมจริง สิ่งที่ใกล้เคียงที่สุดที่มีอยู่วันนี้คือ: ผู้ใช้ใดก็ตามที่มีสิทธิ์อ่าน SR ที่ `completed` สามารถเขียน comment แบบอิสระผ่านตาราง comment ทั่วไป — ไม่มีหน้าจอเฉพาะ ไม่มี field ที่บังคับ และไม่มีการ route อัตโนมัติ

ถ้าฟีเจอร์การยืนยันรับอย่างเป็นทางการสำหรับ SR เป็นความต้องการผลิตภัณฑ์ในระยะใกล้ การสร้างมันขึ้นมาคือฟังก์ชันใหม่ ไม่ใช่ช่องว่างของเอกสาร

## 3. แหล่งอ้างอิง

- ภาพรวมแม่: [03-user-flow.md](./03-user-flow.md) — state machine กลางของ SR; Receiver ถูกระบุไว้ที่นั่นว่ายังไม่ยืนยัน และตาราง handoff ข้าม persona ไม่ยืนยัน handoff แบบ Fulfiller → Receiver อีกต่อไป
- Sibling: [03-user-flow-fulfiller.md](./03-user-flow-fulfiller.md) — การเดินขั้น workflow สุดท้ายคือ action ล่าสุดที่ยืนยันได้บนเอกสาร; ไม่พบสิ่งใดปลายน้ำจากมันในโค้ด
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — "Inventory Controller" ที่เวอร์ชันก่อนหน้าของหน้านี้บรรยายว่าเป็นผู้ resolve ความคลาดเคลื่อนเองก็ยังไม่ยืนยันว่าเป็น role แยก — ดูการแก้ไขในหน้านั้น
- Business rules: [02-business-rules.md](./02-business-rules.md) § 4 (`SR_AUTH_008`, mark ว่ายังไม่ยืนยัน), § 5 (`SR_POST_013`, mark ว่ายังไม่ยืนยัน)
- `../carmen/docs/store-requisitions/SR-Overview.md` § User Roles → แถว Receiver — แหล่งออกแบบ legacy สำหรับแนวคิด receiver; ถือเป็นเจตนาการออกแบบ ไม่ใช่พฤติกรรมปัจจุบันที่ยืนยันแล้ว
