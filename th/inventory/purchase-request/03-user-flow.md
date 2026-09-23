---
title: ใบขอซื้อ (Purchase Request) — User Flow
description: วงจรชีวิตของเอกสารและไฟล์ flow แยกตาม persona สำหรับโมดูล purchase-request
published: true
date: '2026-09-23T01:30:00.000Z'
tags: purchase-request, user-flow, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# ใบขอซื้อ (Purchase Request) — User Flow

> **At a Glance**
> **โมดูล:** [purchase-request](/th/inventory/purchase-request) &nbsp;·&nbsp; **Persona:** Requestor &nbsp;·&nbsp; Approver &nbsp;·&nbsp; Procurement Manager &nbsp;·&nbsp; Purchaser &nbsp;·&nbsp; Audit / Config
> **วงจรชีวิตของ workflow:** Draft → In Progress (อนุมัติหลายขั้นตอน; send-back คงอยู่ที่ `in_progress`) → Approved → Completed (Voided ได้เฉพาะผ่าน Reject ของผู้อนุมัติ; draft ถูก soft-delete) &nbsp;·&nbsp; **ตรวจสอบซ้ำ 2026-09-22** กับ `purchase-request.service.ts` / `logic/purchase-request.logic.ts`
> **เจาะดูมุมมองแยกตาม persona ด้านล่างเพื่อรายละเอียดในระดับ action**

## 1. ภาพรวม

หน้านี้เป็น **จุดเริ่มต้นภาพรวม** สำหรับชุด user-flow ของโมดูล `purchase-request` ครอบคลุมวงจรชีวิตของเอกสาร Purchase Request หนึ่งใบ — ส่วนหัวของ PR (`tb_purchase_request`) พร้อมกับรายการสินค้าหนึ่งรายการหรือมากกว่า (`tb_purchase_request_detail`) — ตั้งแต่ตอนที่ Requestor บันทึก draft ครั้งแรก ผ่านสายอนุมัติหลายระดับ ไปจนถึงการแปลงเป็นใบสั่งซื้อหรือการสิ้นสุดด้วยการ void / ยกเลิก persona ที่เกี่ยวข้องคือ **Requestor** (ผู้ตั้งและแก้ไข PR), สายอนุมัติ **Approver** (ทุก stage role `approve` ที่ workflow กำหนด — "Department Head", "Budget Controller", "Finance" เป็นชื่อประกอบการอธิบาย; code ไม่มีการตรวจสอบงบประมาณ), **Purchaser** (ผู้แปลง PR ที่อนุมัติแล้วเป็น PO), **Procurement Manager** (กำกับและอนุมัติ PR มูลค่าสูง) และบทบาท **Audit / Config** (Auditor สำหรับ review แบบอ่านอย่างเดียว, System Administrator สำหรับตั้งค่า workflow) แค็ตตาล็อก role อยู่ที่ [หน้าหลักโมดูล](/th/inventory/purchase-request) Section 4

Section 2 ด้านล่างเป็น **state machine ของระบบ** — รายการการ transition ตามมาตรฐานข้ามค่าของ `enum_purchase_request_doc_status` โดยไม่ขึ้นกับว่าใครเป็นคนลงมือ ไฟล์ของแต่ละ persona (link จาก Section 3) จะอธิบาย *เส้นทางที่ persona นั้นเดินผ่าน* state machine — จุดเริ่มต้น, action ที่ใช้ได้, แขนงการตัดสินใจ และ handoff ที่จบการมีส่วนร่วมของพวกเขา จากนั้น Section 4 จะสรุป handoff ข้าม persona ที่ร้อยเส้นทางแต่ละเส้นเข้าด้วยกัน อ่านภาพรวมนี้ก่อนเพื่อจับ lifecycle จากนั้นเจาะลงไปที่ไฟล์ persona ที่ตรงกับ role ของคุณ

## 2. วงจรชีวิตของเอกสาร

สถานะของเอกสาร PR เก็บไว้ที่ `tb_purchase_request.pr_status` และจำกัดไว้ที่ค่าที่ประกาศใน `enum_purchase_request_doc_status`: `draft`, `in_progress`, `voided`, `approved`, `completed` การ transition ด้านล่างคือการเคลื่อนที่ที่ถูกต้องระหว่างพวกมัน อย่างอื่นจะถูก workflow engine ปฏิเสธ

```mermaid
stateDiagram-v2
    [*] --> draft: create (Requestor)
    draft --> draft: save / edit (Requestor)
    draft --> in_progress: submit (Requestor)
    draft --> [*]: delete — soft delete, not a status (Requestor / super-admin)
    in_progress --> in_progress: approve intermediate stage
    in_progress --> in_progress: routing rule skips / jumps a stage (threshold)
    in_progress --> in_progress: send-back (review) — stage cursor moves back
    in_progress --> approved: approve final stage
    in_progress --> voided: reject (any approver)
    approved --> completed: convert to PO (Purchaser)
    voided --> [*]
    completed --> [*]
```

| จากสถานะ | Action | ไปสถานะ | อนุญาตให้ใคร | เงื่อนไขก่อน |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | create | `draft` | Requestor | ฟิลด์ header ผ่านการตรวจสอบ (`requestor_id`, `department_id`, `pr_date`, `workflow_id`); ยังไม่ต้องมี line |
| `draft` | save (edit) | `draft` | Requestor (เจ้าของ) | PR ยังเป็นของ requestor; ยังไม่มีการเลื่อน stage ของ workflow |
| `draft` | submit | `in_progress` | Requestor (เจ้าของ) | มี `workflow_id`, `requestor_id`, `department_id`, `pr_date`; มี line อย่างน้อยหนึ่งบรรทัด (`PR_VAL_006`); ทุกบรรทัดซื้อหรือรับ FOC (`PR_VAL_008`); `POST …/verify` (`verify_state = submit`) list ทุกกฎที่ไม่ผ่านล่วงหน้า (`PR_VAL_017`) |
| `draft` | delete | *(row ถูก soft-delete)* | Requestor (เจ้าของ: `created_by_id` หรือ `requestor_id`) หรือ platform super-admin | `pr_status` ต้องเป็น `draft`; header และ line ได้ `deleted_at` (`PR_VAL_018` / `PR_POST_009`) **ไม่ใช่** transition ไป `voided` — เอกสารรุ่นก่อนผิด |
| `in_progress` | approve (stage นี้, ไม่ใช่ final) | `in_progress` | ผู้อนุมัติ stage ปัจจุบัน | ผู้อนุมัติถูก assign ที่ `workflow_current_stage` ปัจจุบันด้วย `stage_role = approve`; `last_action` กลายเป็น `approved` และ cursor ของ stage เลื่อนไป |
| `in_progress` | approve (stage สุดท้าย) | `approved` | ผู้อนุมัติ stage สุดท้าย | ผู้อนุมัติถูก assign ที่ stage อนุมัติสุดท้าย; ทุก stage ก่อนหน้าเซ็นแล้ว (`purchase-request.service.ts:1913`) |
| `in_progress` | send-back (review) | `in_progress` | ผู้อนุมัติคนใดบน chain | ต้องมีเหตุผลและ stage เป้าหมาย; `workflow_current_stage` ย้ายไปเป้าหมาย, `last_action = reviewed`, `pr_status` ถูกเขียนใหม่เป็น `in_progress` (`purchase-request.service.ts:2052`) — PR ไม่กลับไป `draft` เลย มี audit comment เขียน |
| `in_progress` | reject | `voided` | ผู้อนุมัติคนใดบน chain | ต้องมีข้อความเหตุผล; workflow จบ ไม่อนุญาตให้ทำอะไรเพิ่ม (`purchase-request.service.ts:2201` — ผู้เขียน `voided` เพียงจุดเดียว) |
| `in_progress` | routing rule (threshold) | `in_progress` | Workflow engine | เงื่อนไขใน `tb_workflow.data.routing_rules` บน `total_amount` / `department` match ตอน submit หรือ approve; engine ข้ามหรือกระโดดไป stage ที่ระบุ (`PR_AUTH_005`) สถานะไม่เปลี่ยนแต่ cursor ของ stage กระโดด |
| `approved` | convert to PO | `completed` | Purchaser (ไม่มีการบังคับ permission บน dialog) | line ที่อนุมัติแล้วทั้งหมดถูก bridge เข้าสู่ `tb_purchase_order` หนึ่งใบหรือมากกว่า; PR ถูกปิดไม่ให้แปลงต่อ |

## 3. ดัชนี Persona

แต่ละ persona ด้านล่างมีไฟล์ drill-down ของตัวเองที่อธิบายจุดเริ่มต้น, flow หลัก, แขนงการตัดสินใจ และจุดออก slug ตรงกับ role ของ persona; คลิก link เพื่อเปิดมุมมองของแต่ละ persona

- [Requestor](./03-user-flow-requestor.md) — สร้างและ submit PR ตอบสนองต่อ send-back ยกเลิก draft ของตัวเอง
- [Approver](./03-user-flow-approver.md) — ทุก stage role `approve` ของ chain (แสดงตัวอย่างเป็น Department Head → Budget Controller → Finance) พร้อม action approve / send-back / reject / split ในแต่ละ stage
- [Purchaser](./03-user-flow-purchaser.md) — รับ PR ที่อนุมัติแล้ว ตรวจสอบการจัดสรรผู้ขายและราคา แล้วแปลงเป็นใบสั่งซื้อ
- [Procurement Manager](./03-user-flow-procurement-manager.md) — กำกับฟังก์ชัน procurement, อนุมัติ PR มูลค่าสูงหรือที่ถูก escalate, ปรับ vendor ranking และกฎ Allocate Vendor
- [Audit / Config](./03-user-flow-audit-config.md) — Auditor (review PR และ activity log แบบอ่านอย่างเดียว) และ System Administrator (ตั้งค่า stage ของ workflow, กฎ routing ตาม amount threshold; กฎ delegation และ void โดยผู้ดูแลระบบยังไม่ยืนยัน — ไม่พบกลไกหรือ endpoint ที่ตรงกัน ดู `PR_AUTH_006` / `PR_AUTH_007`)

## 4. Handoff ข้าม Persona

ตารางด้านล่างจับโมเมนต์ที่ PR ย้ายความรับผิดชอบจาก persona หนึ่งไปอีก persona handoff แต่ละจุด anchor ที่สถานะของเอกสารตอน transfer

| จาก persona | Trigger | ไป persona | สถานะเอกสารตอน handoff |
| ------------ | ------- | ---------- | ------------------------- |
| Requestor | Submit | ผู้อนุมัติ stage แรก (โดยทั่วไปคือ Department Head) | `in_progress` (cursor ของ stage อยู่ที่ stage อนุมัติแรก) |
| Approver (stage N, ไม่ใช่ final) | Approve ที่ stage นี้ | Approver (stage N+1) | `in_progress` (cursor ของ stage เลื่อนไปยัง stage ถัดไป) |
| Approver (stage สุดท้าย) | Approve ที่ stage สุดท้าย | Purchaser | `approved` |
| Approver (stage ใด ๆ) | Send-back พร้อมเหตุผล (เป้าหมาย = stage create) | Requestor | `in_progress` ที่ stage `create` (ประวัติการแก้ไขและ comment ของผู้อนุมัติเก็บไว้; `pr_status` **ไม่**กลับไป `draft`) |
| Workflow engine | Routing rule บน `total_amount` / `department` match | Stage เป้าหมาย (เช่น Procurement Manager) | `in_progress` (cursor ของ stage กระโดดไป stage เป้าหมายของ rule) |
| Purchaser | Convert to PO | โมดูล Purchase Order (และโดยอ้อมไปยัง Receiver / GRN ปลายน้ำ) | `completed` (สร้าง `tb_purchase_order` หนึ่งใบหรือมากกว่า โดย link กลับมายัง PR) |

| Approver | Reject พร้อมเหตุผล | Auditor (review หลังเหตุการณ์เท่านั้น) | `voided` |

## 5. แหล่งอ้างอิง

- `../carmen/docs/purchase-request-management/PR-User-Experience.md` — แหล่งหลักของ user-experience flow (การสร้าง, การอนุมัติ, การเปรียบเทียบ vendor, การใช้ template)
- `../carmen/docs/purchase-request-management/PR-Overview.md` — ภาพรวมโมดูล, user roles, จุด integration
- `../carmen/docs/purchase-request-management/purchase-request-module-prd.md` — product requirements ที่ขับเคลื่อน flow
- หน้าพี่น้อง: [01-data-model.md](./01-data-model.md) — ค่าตามมาตรฐานของ `enum_purchase_request_doc_status` ที่ใช้ใน Section 2 ด้านบน
- หน้าพี่น้อง: [02-business-rules.md](./02-business-rules.md) — กติกาการ validate, อนุมัติ และ posting ที่อ้างถึงในแต่ละ transition
