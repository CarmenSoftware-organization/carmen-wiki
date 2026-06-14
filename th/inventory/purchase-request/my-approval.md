---
title: รายการอนุมัติของฉัน (My Approval)
description: คิวอนุมัติส่วนบุคคลที่รวมเอกสารทุกใบ (PR และเอกสารที่เกี่ยวข้อง) ที่ผู้ใช้ปัจจุบันต้องดำเนินการ — รวมไว้ในหน้าจอเดียวข้ามทุกโมดูล
published: true
date: 2026-05-20T00:00:00.000Z
tags: purchase-request, approval, workflow, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# รายการอนุมัติของฉัน (My Approval)

> **At a Glance**
> **เจ้าของ:** ผู้อนุมัติของ workflow ใด ๆ &nbsp;·&nbsp; **ตาราง:** *ไม่มี — เป็น projection จากสถานะ workflow* &nbsp;·&nbsp; **Workflow:** กล่องขาเข้าแบบอ่านอย่างเดียว &nbsp;·&nbsp; **ต้นน้ำ:** [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [purchase-order/credit-note](/th/inventory/purchase-order/credit-note) &nbsp;·&nbsp; กล่องขาเข้าส่วนบุคคลที่รวมเอกสารทั้งหมดที่รอให้ผู้ใช้ลงนามจัดการ

![รายการอนุมัติของฉัน (My Approval) screen](/screenshots/purchase-request/my-approval.png)

## 1. ภาพรวมและผู้ใช้งาน

**My Approval** (`/procurement/approval`) คือกล่องขาเข้าส่วนบุคคลของผู้ใช้แต่ละราย รวมทุก stage ของ workflow ที่กำหนดให้ผู้ใช้ที่ล็อกอินอยู่ในเอกสารทุกประเภทที่อนุมัติได้ — โดยหลักคือ Purchase Request แต่ยังครอบคลุม PO, Credit Note และโมดูลใด ๆ ที่ workflow engine คุมอยู่ ในขณะที่แต่ละโมดูลแสดง*เอกสารทั้งหมด*ของตน My Approval จะแสดงเฉพาะ**ส่วนที่ผู้ใช้ปัจจุบันต้องดำเนินการในตอนนี้เท่านั้น** หน้าจอนี้เป็นแบบ **อ่าน-และ-ลงมือทำเท่านั้น** — ไม่ได้เป็นเจ้าของ entity ที่จัดเก็บใด ๆ และเป็น projection จากสถานะ workflow ที่อยู่บนเอกสารต้นทางแต่ละใบ

**ผู้ใช้งาน** ได้แก่ HOD / Procurement Manager / Finance Controller ที่ปรากฏในรายชื่อผู้อนุมัติของ stage ใด ๆ &nbsp;·&nbsp; **ไม่มีการ write-back เข้าตารางท้องถิ่น** — ทุก action เรียก API ของเอกสารต้นทาง

## 2. งานที่พบบ่อย

| งาน | ตำแหน่ง | หมายเหตุ |
|---|---|---|
| ดูรายการที่ค้างอยู่ | Procurement → **My Approval** | เรียงตาม `last_action_at_date` จากใหม่ไปเก่าเป็นค่าเริ่มต้น |
| อนุมัติ PR / PO / CN | แถว → **Approve** | เรียก API ของเอกสารต้นทาง แถวจะหายเมื่อสำเร็จ |
| ส่งกลับ PO (หรือ PR) | แถว → **Send Back** | ส่งไปที่ `workflow_previous_stage` จำเป็นสำหรับการ "แก้แล้วส่งใหม่" |
| ปฏิเสธ | แถว → **Reject** | จบ workflow ของเอกสารต้นทาง |
| อนุมัติแบบ bulk | เลือกหลายรายการ → **Approve selected** | แตกเป็นหนึ่ง transaction ต่อหนึ่งแถว |
| ตรวจสอบประวัติ | ขยายแถว | แสดงรายการ JSON ของ `workflow_history` |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ / ข้อความ | สาเหตุ | การแก้ไข |
|---|---|---|
| ไม่พบแถวในกล่องขาเข้า | ผู้ใช้ที่ล็อกอินอยู่ไม่อยู่ใน `user_action.execute[]` ของ stage ปัจจุบันของเอกสาร | ตรวจสอบการตั้งค่า stage ใน [system-config/workflow](/th/inventory/system-config/workflow) |
| "409 Conflict" ตอนกด approve | เพื่อนใน `execute[]` เดียวกันลงมือทำไปแล้ว engine เลื่อน stage ไปแล้ว | UI จะ refresh อัตโนมัติ ลองเช็คกล่องขาเข้าใหม่ |
| ปุ่ม action ถูก disable | งวดบัญชีของเอกสารต้นทางถูกปิดแล้ว | เปิดงวดใหม่หรือ void เอกสาร (ต้องเป็น finance) |
| มีแถวขึ้นมาแต่ลงมือทำไม่ได้ | `deleted_at` ถูก set บนต้นทางจากที่อื่น | refresh แถวควรหายไป |
| เห็นเอกสารข้าม tenant | (เกิดขึ้นไม่ได้) | query ทั้งหมดถูก scope ด้วย active tenant context |

## 4. กรณีพิเศษ

- **ไม่มีตารางของตัวเอง** ทุก action เป็น write บนเอกสารต้นทาง ไม่ใช่บนกล่องขาเข้า กล่องขาเข้าเองไม่มี audit trail — `workflow_history` อยู่บนต้นทาง
- **Concurrency** สองคนที่อยู่ในกลุ่ม peer เดียวกันลงมือกับแถวเดียวกันพร้อมกัน คนที่สองจะได้ `409 Conflict` เพราะ `workflow_current_stage` เลื่อนไปแล้ว UI จะ re-query และแถวหายไป
- **เอกสารต้นทางที่ถูก soft-delete จะถูกซ่อน** แถวที่ `deleted_at IS NOT NULL` บนต้นทางจะถูกตัดออก
- **เอกสารในงวดที่ปิดแล้ว** แถวยังขึ้น แต่ปุ่ม action ถูก disable — finance ต้องเปิดงวดใหม่หรือ void
- **กรองด้วย identity เท่านั้น** แถวจะปรากฏ **ก็ต่อเมื่อ** id ของผู้ใช้ที่ล็อกอินอยู่อยู่ใน `user_action.execute[]` ไม่มีการเช็ค role เพิ่มที่ชั้นนี้ — engine ได้ resolve role เป็น user-id ตอนเขียน array ไปแล้ว
- **Multi-tenancy** ทุก query ถูก scope ด้วย active tenant context การอนุมัติข้าม tenant เป็นไปไม่ได้

---

## 5. โมเดลข้อมูล (Dev)

**ไม่มีตาราง `tb_my_approval`** หน้านี้เป็น query / view ที่ backed ด้วยคอลัมน์สถานะ workflow ที่ embed อยู่บนเอกสารทุกใบที่อนุมัติได้ มันจะ scan เอกสารเหล่านั้นและแสดง subset ที่ stage ปัจจุบันตรงกับผู้ใช้ที่ล็อกอินอยู่

### 5.1 Pattern ของ query

สำหรับเอกสารทุกประเภทที่อนุมัติได้ (PR, PO, CN, store requisition ฯลฯ) จะใช้ shape คอลัมน์เดียวกัน:

| คอลัมน์บนตารางต้นทาง | บทบาทใน My Approval |
| --- | --- |
| `workflow_id` | ระบุว่า workflow definition ใดคุมเอกสารใบนี้ |
| `workflow_current_stage` | stage ที่จะใช้ match กับ role / membership ของผู้ใช้ |
| `workflow_previous_stage`, `workflow_next_stage` | ใช้แสดงเป้าหมายของ Send-Back และ preview "ผู้อนุมัติคนถัดไป" |
| `workflow_history` (JSON) | `[{stage, action, message, by:{id,name}, at}, …]` — audit trail ที่แสดงเมื่อขยายแถว |
| `user_action` (JSON) | `{ execute: [{id}, …] }` — **ตัวกรองที่เป็นทางการ**: แถวจะปรากฏก็ต่อเมื่อ id ของผู้ใช้ที่ล็อกอินอยู่อยู่ใน array นี้ |
| `last_action`, `last_action_at_date`, `last_action_by_id`, `last_action_by_name` | การ transition ล่าสุด แสดงบนแถว |
| `doc_status` (enum ของแต่ละโมดูล) | กรองระดับผิว — แสดงเฉพาะ `in_progress` (หรือสถานะ "รอดำเนินการ" ที่เทียบเท่า) |

shape คอลัมน์เหมือนกันทั้งบน `tb_purchase_request`, `tb_purchase_order`, `tb_credit_note` และตารางอื่น ๆ ที่อนุมัติได้ หน้าจะ issue query คู่ขนานตามประเภทเอกสารแล้ว union แถวทั้งหมด

### 5.2 Array `user_action.execute[]`

ถูก populate โดย workflow engine ในการ transition แต่ละ stage โดยอ้างอิงการตั้งค่า stage ใน [system-config/workflow](/th/inventory/system-config/workflow):

- **Stage แบบ role-based** — ผู้ใช้ทุกคนที่มี role ที่กำหนดไว้จะถูกนับเข้า `execute[]`
- **Stage แบบ named-approver** — ผู้ใช้ที่ระบุชื่อจะถูกเพิ่มเข้าตรง ๆ
- **Stage แบบ threshold-routed** — กฎ threshold resolve เป็น role หรือ named user แล้วค่อยนับ

ผู้ใช้จะเห็นแถว **ก็ต่อเมื่อ** id ของพวกเขาอยู่ใน `execute[]` ของ `workflow_current_stage` ของเอกสาร เมื่อ peer คนใดลงมือทำ engine จะคำนวณใหม่สำหรับ stage ถัดไปและแถวจะหายไป

## 6. Workflow / กติกาทางธุรกิจ

กล่องขาเข้า **ไม่มีสถานะของตัวเอง** — พฤติกรรมทั้งหมดเป็น projection:

- **แถวปรากฏ** เมื่อ engine populate `execute[]` ของเอกสารด้วย id ของผู้ใช้ที่ล็อกอินอยู่
- **แถวหายไป** เมื่อผู้ใช้ (หรือ peer) approve, reject, send-back หรือ split-reject
- **สถานะแถวสะท้อนต้นทาง** ถ้าต้นทางถูก cancel / void จากที่อื่น แถวจะหายไปใน refresh ครั้งถัดไป

Approve / reject / send-back ต่างก็เรียก backend endpoint ชุดเดียวกับหน้า detail ของแต่ละโมดูล — กล่องขาเข้าเป็นเพียง routing convenience เท่านั้น Bulk approve แตกเป็นหนึ่ง transaction ต่อหนึ่งแถว ไม่มีฟิลด์ใดบนแถวในกล่องขาเข้าที่แก้ไขได้ กล่องขาเข้าไม่มี posting effect ของตัวเอง

## 7. ความเชื่อมโยงข้ามโมดูล

- [purchase-request](/th/inventory/purchase-request) — ประเภทเอกสารหลัก กล่องขาเข้าโดยทั่วไปจะแสดง PR ที่รอแต่ละ stage
- [purchase-order](/th/inventory/purchase-order) — PO ที่ต้องอนุมัติด้วยมือ (price-threshold, vendor-risk, budget-override)
- [purchase-order/credit-note](/th/inventory/purchase-order/credit-note) — CRN ที่รออนุมัติภายใต้สัญญา workflow-state เดียวกัน
- [system-config/workflow](/th/inventory/system-config/workflow) — นิยาม stage, การ map role, กฎ threshold และกฎที่ populate `user_action.execute[]`
- [access-control/application-role](/th/inventory/access-control/application-role) — การ map role-to-permission สำหรับสิทธิ์การใช้งาน
- [purchase-request/03-user-flow-approver](/th/inventory/purchase-request/03-user-flow-approver) — flow walkthrough ของ persona ผู้อนุมัติ

## 8. แหล่งอ้างอิง

- **Prisma (ไม่มีตารางของตัวเอง):** คอลัมน์สถานะ workflow บน `tb_purchase_request`, `tb_purchase_order`, `tb_credit_note` ฯลฯ — `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (block `workflow_*` และ `user_action` ทำซ้ำบนทุก model ที่อนุมัติได้ ตัวอย่าง CN ที่บรรทัด 358-376)
- **Frontend route:** `../carmen-inventory-frontend-react/routes/procurement/approval/`
- **Carmen docs:** `../carmen/docs/business-analysis/my-approvals-ba.md`; ประสบการณ์ผู้อนุมัติใน `../carmen/docs/purchase-request-management/PR-User-Experience.md`
