---
title: ใบเบิกของสโตร์ (Store Requisition) — Test Scenarios — Receiver
description: test case ของ Receiver — persona ยังไม่ยืนยัน; อธิบายว่าทำไมชุด scenario เดิมไม่ตรงกับ source ปัจจุบัน
published: true
date: 2026-07-15T12:00:00.000Z
tags: store-requisition, test-scenarios, receiver, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:30:00.000Z
---

# ใบเบิกของสโตร์ (Store Requisition) — Test Scenarios — Receiver

> **At a Glance**
> **Persona:** Receiver — **ยังไม่ยืนยันว่าเป็น persona แยกใน source ปัจจุบัน** &nbsp;·&nbsp; **โมดูล:** [store-requisition](/th/inventory/store-requisition)
> ⚠️ **แก้ไขครั้งใหญ่รอบนี้** หน้านี้เคยระบุ test scenario ~20 รายการ (happy path, permission, validation, edge case) สำหรับ "Receiver" ของเอาท์เลตปลายทางที่ยืนยันการรับจริง flag ความคลาดเคลื่อน และ escalate ไปยัง Inventory Controller [03-user-flow-receiver.md](./03-user-flow-receiver.md) บันทึกร่องรอยการตรวจสอบ source เต็ม: การค้นหาทั่ว repo ใน `carmen-turborepo-backend-v2` และ `carmen-inventory-frontend-react` สำหรับ `receiver` / `discrepancy` ไม่พบผลลัพธ์ใด ๆ ภายในโมดูล `store-requisition`, `enum_stage_role` ไม่มีสมาชิก `receiver` และไม่มี route หรือ component ใดสำหรับ receiver ดังนั้นจึงไม่มีอะไรให้เขียน test scenario ต่อ

## 1. สิ่งที่มาแทน Scenario เหล่านี้

การ interact หลัง commit เดียวที่ยืนยันได้ในปัจจุบันคือ: ผู้ใช้ใดก็ได้ที่มีสิทธิ์อ่าน SR `completed` สามารถ append comment ประเภท `user` ทั่วไปผ่าน `tb_store_requisition_comment` / `tb_store_requisition_detail_comment` (endpoint comment เดียวกับที่ทุก persona ใช้ — ไม่ใช่เฉพาะ receiver ไม่มี sub-type `discrepancy`) Test scenario ขั้นต่ำที่ตรงตามความเป็นจริงกับพื้นผิวจริงนั้นจะเป็น:

| # | Scenario | Pre-condition | Steps | คาดหวัง |
| - | -------- | ------------- | ----- | ------- |
| RCV-HP-01 | ผู้ใช้ใดก็ได้ append comment ข้อความอิสระบน SR `completed` | SR อยู่ที่ `doc_status = completed`; ผู้ใช้มีสิทธิ์อ่าน | 1. เปิด SR 2. เพิ่ม comment ผ่านแผง comment 3. Save | Comment persist ผ่าน endpoint comment ทั่วไป; `doc_status` ไม่ได้รับผลกระทบ; ไม่มีฟิลด์เฉพาะความคลาดเคลื่อน, escalation หรือ notification ใด ๆ ให้ assert |

ถ้าฟีเจอร์การยืนยันการรับอย่างเป็นทางการหรือการ flag ความคลาดเคลื่อนกลายเป็น product requirement จริงในอนาคต scenario ที่เคยอยู่ในหน้านี้ (รับขาด, รับเกิน, lot ผิด, สินค้าเสีย, มาช้า, missing-on-arrival) เป็นจุดเริ่มต้นการ *ออกแบบ* ที่สมเหตุสมผลสำหรับ test plan ของ feature นั้นในอนาคต — แต่จะต้องไม่ถูกนำเสนอว่าเป็น test ของพฤติกรรมปัจจุบัน

## 2. แหล่งอ้างอิง

- ภาพรวมแม่: [04-test-scenarios.md](./04-test-scenarios.md) — Scenario 7 ในตารางข้าม persona ถูกลบรอบนี้ด้วยเหตุผลเดียวกัน
- User flow: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — ร่องรอย "อะไรยืนยันได้และอะไรยังไม่ยืนยัน" เต็มที่หน้านี้สรุป
- Sibling: [04-test-scenarios-fulfiller.md](./04-test-scenarios-fulfiller.md) — การเดินขั้น workflow สุดท้ายคือ action สุดท้ายที่ยืนยันได้บนเอกสาร; ไม่พบสิ่งใดปลายน้ำจากนั้นใน code
- Business rules: [02-business-rules.md](./02-business-rules.md) § 4 (`SR_AUTH_008`, mark ว่ายังไม่ยืนยัน), § 5 (`SR_POST_013`, mark ว่ายังไม่ยืนยัน)
