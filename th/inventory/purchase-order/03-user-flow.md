---
title: ใบสั่งซื้อ (Purchase Order) — User Flow
description: วงจรชีวิตของเอกสารและไฟล์ flow แยกตาม persona สำหรับ purchase-order
published: true
date: 2026-07-29T05:45:00.000Z
tags: purchase-order, user-flow, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# ใบสั่งซื้อ (Purchase Order) — User Flow

> **At a Glance**
> **Module:** [purchase-order](/th/inventory/purchase-order) &nbsp;·&nbsp; **Personas:** Purchaser &nbsp;·&nbsp; Procurement Manager &nbsp;·&nbsp; Vendor &nbsp;·&nbsp; Receiver &nbsp;·&nbsp; Finance &nbsp;·&nbsp; Audit / Config
> **วงจรการทำงาน workflow:** Draft → In Progress → Sent → Partial → Completed / Closed (พร้อม branch Voided)
> **ดูมุมมองแต่ละ persona ด้านล่างเพื่อรายละเอียดระดับ action**

## 1. ภาพรวม

หน้านี้คือ **จุดเริ่มต้นภาพรวม** สำหรับชุด user-flow ของโมดูล `purchase-order` Purchase Order (PO) คือเอกสารการผูกพัน procurement — header PO (`tb_purchase_order`) ร่วมกับบรรทัด detail หนึ่งหรือมากกว่าหนึ่งบรรทัด (`tb_purchase_order_detail`) — ที่สร้างด้วยมือ, จากใบขอซื้อ (Purchase Request) ที่อนุมัติแล้วหนึ่งใบขึ้นไป, หรือโดยตรงจาก vendor price list ซึ่งผูกพัน buyer กับ vendor ในราคา ปริมาณ และวันส่งของที่ fixed วงจรชีวิตใน Section 2 ครอบคลุมจากการสร้าง draft เริ่มต้นผ่าน internal approval การส่งให้ vendor การรับบางส่วนหรือเต็มเทียบกับ PO และสุดท้ายการปิด (การ complete ปกติหรือการปิดก่อนกำหนด) Personas ที่เกี่ยวข้องคือ **Purchaser** (สร้างและ submit PO บริหาร amendments), **Procurement Manager** (ทำหน้าที่เป็นผู้อนุมัติใน workflow stage ที่กำหนดไว้; ถือสิทธิ์ delete-in-draft — `routing_rules` ของ workflow ที่ assign ให้สามารถ skip/กระโดดข้าม stage ตาม `total_amount` ได้จริง ยืนยันแล้ว ดู [02-business-rules.md](./02-business-rules.md) `PO_AUTH_004`; การตั้งค่า vendor-ranking ยังไม่ยืนยัน), **Vendor** (ฝ่ายภายนอกไม่มี system login — รับและ fulfil; ไม่พบฟีเจอร์การตอบรับในระบบหรือ invoice ที่ยืนยันได้), **Receiver** (รับสินค้าจริงและสร้าง GRN เทียบกับ PO), บทบาท **Finance** ที่ถูกระบุไว้ในเอกสารออกแบบรุ่นเก่าแต่ยังไม่ยืนยันใน source ปัจจุบัน, และ roles **Audit / Config** (Auditor สำหรับ read-only review, System Administrator สำหรับการตั้งค่า workflow และการเรียงเลข) Catalogue role เองนิยามใน [หน้าหลักโมดูล](/th/inventory/purchase-order) Section 4

Section 2 ด้านล่างคือ **global state machine** — list canonical ของ transitions ข้ามค่า `enum_purchase_order_doc_status` อิสระจากใครทำ ไฟล์ persona แต่ละไฟล์ (link จาก Section 3) อธิบาย *เส้นทางผ่าน* state machine ของ persona นั้น — entry point ของพวกเขา actions ที่ใช้ได้กับพวกเขา decision branches ที่พวกเขาเผชิญ และ handoff ที่จบการ involvement ของพวกเขา Section 4 จากนั้น summarise cross-persona handoffs ที่เย็บเส้นทางส่วนตัวเข้าด้วยกัน อ่านภาพรวมนี้ก่อนเพื่อ anchor วงจรชีวิต จากนั้นเจาะลึกไฟล์ persona ที่ตรงกับ role ของคุณ

## 2. วงจรชีวิตของเอกสาร

PO document status เก็บใน `tb_purchase_order.po_status` และจำกัดให้เป็นค่าที่ประกาศใน `enum_purchase_order_doc_status`: `draft`, `in_progress`, `voided`, `sent`, `partial`, `closed`, `completed` Transitions ด้านล่างครอบคลุมการเคลื่อนไหวที่ถูกต้องระหว่างกัน; อย่างอื่นถูก reject โดย workflow engine หมายเหตุว่า transitions ที่ driven โดย receipt (`sent → partial → completed`) ถูก trigger โดย GRN postings ในโมดูลปลายน้ำ [good-receive-note](/th/inventory/good-receive-note) ไม่ใช่โดย action ผู้ใช้โดยตรงบน PO

```mermaid
stateDiagram-v2
    [*] --> draft: create (Purchaser)
    draft --> draft: save / edit
    draft --> in_progress: submit for approval
    draft --> [*]: soft-delete (PO_AUTH_005)
    in_progress --> in_progress: approve intermediate stage / send-back (stage resets, status unchanged)
    in_progress --> sent: approve final + transmit
    in_progress --> voided: reject (direct, terminal)
    draft --> closed: cancel
    in_progress --> closed: cancel / close
    sent --> closed: cancel / close
    sent --> partial: GRN posts partial receipt
    sent --> completed: GRN posts full receipt
    partial --> partial: subsequent partial GRN
    partial --> completed: GRN clears outstanding balance
    partial --> closed: close (Inv. Mgr / PM; PO_AUTH_008)
    completed --> [*]
    closed --> [*]
    voided --> [*]
```

> ⚠️ **แก้ไขในรอบนี้:** diagram/ตารางรุ่นก่อนหน้าแสดง `in_progress → draft` ตอน send-back และ "void" ที่เฉพาะ Procurement Manager เข้าถึงได้จาก `draft`/`sent`/`partial` ทั้งสองอย่างไม่มีอยู่ใน source ปัจจุบัน Send-back (`/review`) คง `po_status = in_progress` ไว้และรีเซ็ตเฉพาะ `workflow_current_stage`; เส้นทางเดียวไปยัง `voided` คือ transition แบบตรงและสิ้นสุด `in_progress → voided` ผ่าน `/reject` การจบ PO จาก `draft`, `sent`, หรือ `partial` ใช้ **Cancel** หรือ **Close** แทน (ทั้งคู่ลงเอยที่ `closed` โดยเขียนส่วนที่เหลือลงใน `cancelled_qty`) ไม่ใช่ `voided`

| จาก state | Action | ไปยัง state | อนุญาตสำหรับ | เงื่อนไขก่อน |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | create | `draft` | Purchaser | ฟิลด์ header ถูก validate (`vendor_id`, `currency_id`, `order_date`, `delivery_date`, `workflow_id`); ต้องมีอย่างน้อยหนึ่งบรรทัดก่อน submission PR linkage เขียนเข้าตาราง bridge เมื่อมีต้นทางจาก PR; ไม่ต้องมี linkage สำหรับต้นทาง `manual` หรือ `pricelist` |
| `draft` | save (edit) | `draft` | Purchaser (owner) | PO ยังแก้ไขได้; ไม่มี workflow stage advance Header totals (`total_qty`, `total_price`, `total_tax`, `total_amount`) คำนวณใหม่ตอน save |
| `draft` | submit for approval | `in_progress` | Purchaser (owner) | อย่างน้อยบรรทัดที่ไม่ deleted หนึ่งบรรทัด; header ครบ; `workflow_id` ที่เลือก active สำหรับ scope `purchase-order` `last_action` ตั้งเป็น `submitted`; stage cursor advance ไปยัง stage approval แรก |
| `draft` | delete | `(none)` | Purchaser, Procurement Manager | Soft-delete เท่านั้น (`deleted_at` ตั้ง); อนุญาตเฉพาะตอน PO อยู่ใน `draft` และไม่เคย submit |
| `draft` / `in_progress` / `sent` | cancel | `closed` | ผู้ที่ถือ action นั้น (ไม่พบข้อจำกัด role ที่ยืนยันได้) | ถอน commitment; ส่วนที่เหลือต่อบรรทัดเขียนลงใน `cancelled_qty` |
| `in_progress` | approve (stage นี้ ไม่ใช่ final) | `in_progress` | Current-stage approver | Approver อยู่ใน `user_action.execute[]` สำหรับ `workflow_current_stage`; `last_action` กลายเป็น `approved`; stage cursor advance การอนุญาตให้ดำเนินการที่ stage นี้คือ membership ใน `user_action.execute[]` เท่านั้น — ไม่มี amount threshold ใดมา gate ว่า *ใคร* อนุมัติได้ แต่ stage ถัดไปเองอาจขับเคลื่อนด้วย amount ได้: `routing_rules` ของ workflow อาจ skip หรือกระโดดข้าม stage ตาม `total_amount` (`PO_AUTH_004`) |
| `in_progress` | approve (final stage) | `sent` | ผู้ที่ถือ stage สุดท้ายของ workflow | `workflow_next_stage === '-'` PO ถูกส่งให้ vendor บน transition เดียวกันนี้ (email / EDI / portal ตามที่ตั้งค่า); ตั้ง `approval_date` |
| `in_progress` | send-back / review | `in_progress` (ไม่เปลี่ยน) | ผู้อนุมัติใด ๆ บนห่วงโซ่ | รีเซ็ต `workflow_current_stage` ไปยัง stage ก่อนหน้า (เช่น กลับไปยังผู้สร้าง); `po_status` ไม่เปลี่ยน เหตุผล (ถ้ามี) บันทึกเป็น comment |
| `in_progress` | reject | `voided` | ผู้อนุมัติใด ๆ บนห่วงโซ่ | Transition แบบตรงและสิ้นสุด — ไม่มี state ระหว่างทาง |
| `{sent, partial, in_progress}` | close | `closed` | Inventory Manager / Receiver (ตาม `PO_AUTH_008`); ไม่พบ role gate เพิ่มเติมที่ยืนยันได้ | Vendor ไม่สามารถ supply ปริมาณที่เหลือ; open qty ที่เหลือเขียนลงใน `cancelled_qty` |
| `sent` | receive (partial) | `partial` | Receiver ผ่าน GRN posting | อย่างน้อย PO line หนึ่งมี `received_qty > 0` แต่ `received_qty < order_qty − cancelled_qty` ข้าม PO State change คำนวณจาก GRN postings ระดับบรรทัด |
| `sent` | receive (full) | `completed` | Receiver ผ่าน GRN posting | ทุกบรรทัดเป็นไปตาม `received_qty + cancelled_qty ≥ order_qty`; ทุกบรรทัดปิดผ่าน GRN ใน transaction เดียว |
| `partial` | receive (เพิ่มเติม) | `partial` | Receiver ผ่าน GRN posting | GRN ถัดไป post quantity เพิ่ม แต่ PO ยังมีอย่างน้อยหนึ่งบรรทัดที่เปิด; state ยังคงเป็น `partial` |
| `partial` | receive (final balance) | `completed` | Receiver ผ่าน GRN posting | GRN สุดท้าย clear outstanding balance บนทุกบรรทัด; PO transition ไปยัง normal completion |
| `completed` | (ไม่มี action เพิ่ม) | `completed` | — | Terminal state สำหรับเส้นทาง receipt ไม่พบฟีเจอร์ three-way-match / invoice ที่ยืนยันได้ใน source ปัจจุบันเพื่อ track ต่อจากนี้ |

## 3. สารบัญ Persona

แต่ละ persona ด้านล่างมีไฟล์ drill-down เฉพาะที่อธิบาย entry point, primary flow, decision branches, และ exit point Slugs ตรงกับ role ของ persona; การคลิก link เปิดมุมมองต่อ persona

- [Purchaser](./03-user-flow-purchaser.md) — สร้าง PO ด้วยมือ, โดยการแปลง PR ที่อนุมัติแล้ว (group ด้วย vendor + delivery date + currency), หรือจาก vendor price list; validate ราคา pricelist; submit และบริหาร amendments และการติดตาม
- [Procurement Manager](./03-user-flow-procurement-manager.md) — ทำหน้าที่เป็นผู้อนุมัติใน workflow stage ที่กำหนดไว้ (กลไกทั่วไปเดียวกับผู้อนุมัติรายอื่น; `routing_rules` ของ workflow ที่ assign ให้สามารถ skip/กระโดดข้าม stage ตาม `total_amount` ได้จริง ยืนยันแล้ว, `PO_AUTH_004`); ถือสิทธิ์ delete-in-draft
- [Vendor](./03-user-flow-vendor.md) — ฝ่ายภายนอกไม่มี system login; รับ PO ที่ส่งมาและ fulfil การส่งของตามเงื่อนไขที่ตกลง ไม่พบฟีเจอร์การตอบรับในระบบหรือ invoice ที่ยืนยันได้
- [Receiver](./03-user-flow-receiver.md) — Receiver / Store Keeper + Inventory Manager รับสินค้าจริง สร้าง GRN เทียบกับ PO ทีละบรรทัด และ trigger receipt-state transitions `sent → partial → completed`
- [Finance](./03-user-flow-finance.md) — ถูกระบุไว้ในเอกสารออกแบบรุ่นเก่าว่าเป็นผู้ review ก่อนส่งและเจ้าของ AP หลังรับของ; **ยังไม่ยืนยัน** ใน source ปัจจุบัน (ไม่พบ stage role แยกต่างหาก, การบันทึก invoice, หรือโค้ด AP-matching)
- [Audit / Config](./03-user-flow-audit-config.md) — Auditor (read-only review ของ POs, amendments, และ activity log) และ System Administrator (workflow stage configuration, RBAC, การเรียงเลข)

## 4. Handoffs ข้าม Persona

ตารางด้านล่าง capture moments ที่ PO เคลื่อนจากความรับผิดชอบของ persona หนึ่งไปยังอีก persona Handoff แต่ละครั้ง anchor ที่ document state ณ จุด transfer

| จาก persona | Trigger | ไปยัง persona | Document state ที่ handoff |
| ------------ | ------- | ---------- | ------------------------- |
| Purchaser | Submit for approval | ผู้อนุมัติ stage แรก | `in_progress` (stage cursor อยู่บน stage approval แรก) |
| Approver (stage N, ไม่ใช่ final) | Approve ที่ stage นี้ | Approver (stage N+1) | `in_progress` (stage cursor advance) |
| Approver (final stage) | Approve ที่ final stage และส่ง | Vendor | `sent` (PO ส่งแล้ว; รอ GRN ครั้งแรก) |
| Approver (stage ใด ๆ) | Send-back / review พร้อมเหตุผล | Purchaser (หรือ stage ที่เฉพาะผู้สร้าง) | `in_progress` ไม่เปลี่ยน (รีเซ็ตเฉพาะ `workflow_current_stage` — ไม่ถึง `draft`) |
| Vendor | การส่งของจริง | Receiver | `sent` (state ระบบไม่เปลี่ยนจนกว่า GRN จะ post) |
| Receiver | Post GRN — partial fulfilment | Purchaser, Inventory Manager | `partial` (บรรทัดหนึ่งหรือมากกว่ายังเปิดอยู่) |
| Receiver | Post GRN — final balance | — | `completed` (ทุกบรรทัดรับครบ; ไม่พบ handoff invoice/AP ปลายน้ำที่ยืนยันได้) |
| Procurement Manager / Inventory Manager | Close PO ด้วย qty ที่เหลือเป็น cancelled | — (เป้าหมาย review close-out ยังไม่ยืนยัน) | `closed` (qty ที่เหลือเขียนเป็น `cancelled_qty`) |
| ผู้อนุมัติใด ๆ ที่ stage ปัจจุบัน | Reject (แบบตรงและสิ้นสุด) | Auditor (review หลังเกิดเหตุเท่านั้น) | `voided` (เข้าถึงได้เฉพาะจาก `in_progress`) |

## 5. แหล่งอ้างอิง

- `../carmen/docs/purchase-order-management/purchase-order-module.md` — แหล่ง carmen/docs หลักสำหรับ business analysis, state diagram, และ PO creation flows ให้ถือว่า claim เกี่ยวกับ state-machine และ role ในนั้นเป็นเจตนาการออกแบบทางประวัติศาสตร์ ไม่ใช่พฤติกรรมปัจจุบันที่ verify แล้ว — ดู [02-business-rules.md](./02-business-rules.md) § 5.1 สำหรับ mapping ที่แก้ไขแล้ว
- ส่วนคู่ขนาน: [01-data-model.md](./01-data-model.md) — ค่า `enum_purchase_order_doc_status` canonical ที่ใช้ใน Section 2 ข้างต้นและตาราง bridge ที่ carry PR→PO traceability
- ส่วนคู่ขนาน: [02-business-rules.md](./02-business-rules.md) — กฎ validation, authorization, posting, และ transition ที่อ้างอิงโดยแต่ละ row ของ Section 2
- โมดูลที่เกี่ยวข้อง: [purchase-request](/th/inventory/purchase-request) (ต้นทาง upstream ผ่าน PR→PO bridge), [good-receive-note](/th/inventory/good-receive-note) (fulfilment ปลายน้ำที่ขับเคลื่อน transitions `partial` / `completed`), [vendor-pricelist](/th/inventory/vendor-pricelist) (price snapshot ที่ PR-to-PO conversion time)
