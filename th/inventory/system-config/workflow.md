---
title: เวิร์กโฟลว์ (Workflow)
description: เวิร์กโฟลว์การอนุมัติหลายขั้นสำหรับ PR / PO / SR: stage, action, ผู้รับ, SLA, การมองเห็นฟิลด์, routing rule, ขอบเขตสินค้า; หน้า detail แบบ stage rail; ประเภทล็อกหลังสร้าง
published: true
date: '2026-10-27T15:00:00.000Z'
tags: system-config, workflow, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# เวิร์กโฟลว์ (Workflow)

> **At a Glance**
> **เจ้าของ:** Sysadmin / Workflow Administrator &nbsp;·&nbsp; **ตาราง:** `tb_workflow` &nbsp;·&nbsp; **Routes:** `/system-admin/workflow/purchase-request`, `/purchase-order`, `/store-requisition` (+ `/workflow/new`, `/workflow/:id`); `/system-admin/workflow` redirect ไปหน้า PR — **ไม่มีรายการรวมตั้งแต่ 2026-09-16** &nbsp;·&nbsp; **Endpoints:** `GET api/config/:bu_code/workflows/{purchase-request|purchase-order|store-requisition}` ต่อ type บวก `edit-availability`, `assignees/:user_id` (+ `/handover`), `:id/products/:product_id/locations` &nbsp;·&nbsp; **Permission / licence:** `system_admin.workflow` + ต่อ type `system_admin.workflow.{purchase_request,purchase_order,store_requisition}` &nbsp;·&nbsp; **ใช้โดย:** PR / SR / PO (โมดูลที่มีการอนุมัติ); `gl_jv` มีอยู่ใน enum สำหรับโมดูล GL แต่ไม่มีหน้าที่นี่ &nbsp;·&nbsp; นิยามสาย stage — action, ผู้รับ, SLA, ฟิลด์ที่ซ่อน, ผู้ได้รับมอบหมาย, stage role, routing rule, ขอบเขตสินค้า

![เวิร์กโฟลว์ (Workflow) screen](/screenshots/system-config/workflow.png)

![เวิร์กโฟลว์ (Workflow) detail screen](/screenshots/system-config/workflow-detail.png)

## สถานะการทำงานจริง (ตรวจสอบซ้ำ 2026-10-27)

- **หน้า detail สร้างรอบ stage rail ไม่ใช่แผนภาพ** (FE `0b0fbf6b`, `f89c0427`) แผนภาพ ReactFlow (`wf-diagram.tsx`) และแผงตรวจสอบ (`wf-validation-panel.tsx`) ถูกลบแล้ว `/system-admin/workflow/:id` (`wf-detail.tsx`) เป็น layout สองคอลัมน์: **stage rail** แบบ sticky ด้านซ้าย (`wf-stage-list.tsx`, ลากเรียงด้วย `@dnd-kit`, **Add stage**, ลบ, จำนวนผู้อนุมัติ, เวลา cycle รวมจาก SLA และ validation issue ที่ listed ใต้ stage ที่เกี่ยวข้อง) และรายละเอียดด้านขวา ด้านขวามีสาม tab ระดับ workflow — **Overview** (ฟิลด์ identity ตอนแก้ไข บวกบล็อก insights), **Routing**, **Products** — และการคลิก stage ใน rail จะสลับด้านขวาเป็น tab ของ stage นั้นเอง (**General**, **Notifications**, **Assigned Users**; `wf-stage-detail.tsx`) tab **Stages** แบบ standalone เดิมไม่มีแล้ว รายละเอียด stage ยังมีมุมมอง "view" แบบ read-only ในทั้งสาม tab เมื่อไม่ได้แก้ไข (FE `e4cdaa93`) header มี **Duplicate** ที่เปิดสำเนาใหม่ทันที (FE `935b2fce`, `wf-header.tsx:151-156`)
- **tab Overview / Insights** (`wf-insights.tsx`, FE `1b589ed0`): รายการตรวจก่อนบันทึก (validation error / warning, ปัญหาของ routing rule, คำเตือน "no products selected"), เส้นทางเอกสารที่สัดส่วนตาม SLA ของแต่ละ stage, สถิติย่อย (cycle time, stage ผู้อนุมัติ, stage HoD, ผู้ใช้ทั้งหมด, routing rule, สินค้า, inherit-signature สำหรับ PO) และ matrix stage × action ที่แสดงว่าปุ่มใดเปิดอยู่ แต่ละปุ่มมีผู้รับกี่คน ใครเป็น HoD และฟิลด์ราคาใดถูกซ่อน
- **ประเภท workflow ถูกล็อกหลังสร้าง** (BE `49c5f0872`): `WorkflowUpdateSchema` ไม่มี `workflow_type` แล้ว; micro-service ทิ้งมันถ้า client ยังส่งมา เพราะ `role` ของทุก stage ถูก validate กับ type FE แสดง type เป็นค่าที่ล็อกข้างชื่อทั้งหน้าสร้างและหน้า detail (`wf-new-form.tsx`, FE `a8a32ae7`) role ที่เสนอต่อ stage ถูกจำกัดตาม type (`wf-role-colors.ts`: PR `create/approve/purchase`, PO `create/approve`, SR `create/approve/issue`) และ validator รายงาน `role_not_allowed` ถ้า stage ถือ role นอกชุดนั้น
- **การเทียบ skeleton-lock ไม่สนลำดับ key ของ JSON** (BE `7b01e2cc5`): Postgres คืน key ของ JSONB เรียงใหม่ ทำให้ workflow ที่มี routing rule บันทึกไม่ได้ขณะมีเอกสารกำลังดำเนินอยู่ `workflow-edit-scope.helper.ts` ตอนนี้เทียบ routing rule ด้วย JSON ที่เรียง key (`toCanonicalJson`) ลำดับของ array ยังมีความหมาย (ลำดับ rule = ลำดับความสำคัญ)
- **การล็อกถูกอธิบายในทุก tab** (FE `d590dbc7`): `WfStructureLockNotice` แสดงจำนวนเอกสารที่กำลังดำเนินอยู่พร้อมลิงก์ไปรายการเอกสารที่กรองไว้ล่วงหน้าเป็นเอกสาร `in_progress` ของ workflow นั้น (`getInProgressDocumentsHref`: PR `/procurement/purchase-request`, PO `/procurement/purchase-order`, SR `/store-operation/store-requisition`) และ rail, tab Routing และฟิลด์โครงสร้างถูก disable พร้อมไอคอนกุญแจ
- **notification template ที่ seed ไว้ถูกเลือกล่วงหน้า** (FE `18405175`, `d40bf6c5`): เมื่อสร้าง stage ช่องแจ้งเตือนที่ว่างจะถูกเติมด้วย system template ที่ `code` เป็น `wf.<action>.<slot>` (`wf-seeded-templates.ts`, `use-seeded-template-ids.ts`; template ที่ listed ใน [system-config/notification-template](/th/inventory/system-config/notification-template)) เติมเฉพาะช่องที่ว่างและไม่แตะสวิตช์ `wf.complete.requestor` เลือกไม่ได้ — backend ใช้มันเองตอนอนุมัติขั้นสุดท้าย
- **ช่องผู้รับเปลี่ยน**: มีช่องที่สี่ `previous_step` (`recipients.previous_step`, ไม่บังคับ) แถว "previous approver" ของ action Reject ตอนนี้เขียน `previous_step` (เดิมเขียน `current_approve` ซึ่ง dispatcher ส่งถึงคนที่เพิ่งกด); ตอนโหลด FE ย้ายค่าเก่า (`moveRejectPreviousApprover`) และ **ล้าง `current_approve` ทุกที่** (`clearCurrentApprover`) เพราะแถวนั้นไม่แสดงอีกแล้วและ backend ไม่เคยส่ง slot นั้น ตอนบันทึก `syncRecipientChannels` บังคับให้ `is_notification` และ `notification_channel.app.is_active` เท่ากับสวิตช์ผู้รับ — หนึ่งสวิตช์ต่อผู้รับ (FE `d32a7958`; `wf-form-schema.ts`)
- **tab Routing อ่านเป็นประโยค** (FE `626ef5f3`): แต่ละ rule แสดงเป็น "when [stage] … if [field op value] … then go to [stage]" พร้อมระบุชื่อ stage ที่ถูกข้าม ฟิลด์เงื่อนไขคือ `total_amount` (operator `eq/gt/lt/gte/lte/between` พร้อม `min_value`/`max_value` สำหรับ `between`), `department` (เลือกจาก checklist แบบแบ่งหน้า เลือกได้เกิน 30 แผนก — FE `56362c10`) หรือ `category` เป้าหมายเป็นได้เฉพาะ stage **หลัง** stage ที่กระตุ้น และชนิด action `SKIP_STAGE` / `NEXT_STAGE` derive จากเป้าหมายไม่ใช่เลือกเอง (`wf-routing-utils.ts`); rule ของ `category` ถูก flag ว่าไม่มีผล เพราะเอกสารยังไม่มี category ระดับเอกสาร (comment ของ backend `evaluateCondition`, `workflows.navagation.service.ts`)
- **tab Products** (FE `b6e3818a`): แสดงที่เลือก / ทั้งหมด และแถบ coverage พร้อมสวิตช์ให้ list เฉพาะสินค้าที่เลือก **Stage Notifications** เป็นหนึ่งแถวและหนึ่งสวิตช์ต่อผู้รับ และเตือนเมื่อผู้รับเปิดอยู่แต่ไม่มี template; **Assigned Users** มี checkbox ทั้งแถว, select-all แบบ tri-state และ HoD เป็นสวิตช์
- **สวิตช์ action ต่อ stage ถูกบังคับใช้** (`workflow-orchestrator.service.ts:560-604`, `checkStageActionAllowed`): เมื่อ stage ปัจจุบันของเอกสารมี role `approve`, `purchase` หรือ `issue` และ `available_actions.<verb>.is_active === false` สำหรับ `approve`, `reject` หรือ `sendback` action จะถูกปฏิเสธด้วย **422 `WORKFLOW_STAGE_ACTION_DISABLED`** (`Action "{action}" is turned off for stage {stage} in this workflow`, `error-catalog/src/catalog.ts:3219`) stage ที่มี role อื่น (`create`, `view_only`) ไม่ถูกตรวจ และเอกสาร AP ข้ามการตรวจโดยตั้งใจ response รายละเอียดของ PR / PO / SR พก flag ที่ derive เป็น `stage_actions: { approve, reject, sendback }` (boolean; gateway `purchase-request.serializer.ts`, `purchase-order.serializer.ts`, `store-requisition.serializer.ts`; BE `aeafc119d`) และ FE ซ่อนปุ่มที่ตรงกันจากมัน (`getStageActionFlags` ใน `pr-form.tsx` / `po-form.tsx` / `sr-form.tsx`) การซ่อนราคาคือ `hide_fields.price_per_unit` / `hide_fields.total_price` ของ stage (tab General ของ stage, ส่วน "Visibility"; §5.2)
- **badge ราคาที่ซ่อน** (FE `a2734e55`, `88252a4a`): รายการและ My Approvals แสดง badge เมื่อ stage ปัจจุบันซ่อนราคา; PR ที่ซ่อนเฉพาะราคาต่อหน่วยยังแสดงยอดรวมจาก backend
- **enum ฝั่ง backend ขยาย**: `enum_workflow_type` ตอนนี้มีเจ็ดค่า — `purchase_request`, `store_requisition`, `purchase_order`, `gl_jv`, `ap_invoice`, `ap_payment`, `ar_invoice` (`schema.prisma:271-279`); ทั้งสามประเภท AP/AR อนุญาต role `create`/`approve` และถูกจัดการใน `getEditAvailability` และโค้ด handover (`workflow-stage-role.helper.ts:45-47`, `workflows.service.ts`) เป็นของโมดูลบัญชีและไม่มีหน้าใน FE นี้ (`WORKFLOW_TYPE` มีเฉพาะ PR/PO/SR)
- **code ของ validator ฝั่ง client ที่ HEAD** (`wf-validate.ts`): `empty_name`, `duplicate_name`, `no_users_assigned`, `no_actions_enabled`, `no_sla`, `missing_create_role`, `missing_completed_stage`, `role_not_allowed` `submit_only_on_first` ยังประกาศในชนิด `IssueCode` แต่ไม่มีอะไร emit

### สถานะก่อนหน้า (2026-09-22) — การแยกต่อ type, handover และ skeleton lock ด้านล่างยังเป็นปัจจุบัน

## 1. คืออะไรและใครใช้

Record ของเวิร์กโฟลว์คือ *นิยามการ route เอกสาร* ที่ใช้โดยทุกโมดูลที่มีการอนุมัติ คอลัมน์ header น้อย — name, type, active flag — แต่งานหนักอยู่ใน `data` JSONB: รายการ **stages** ตามลำดับ, **action ที่ใช้ได้** ต่อ stage (`submit`, `approve`, `reject`, `sendback`), **ผู้รับ** ที่จะ notify เมื่อแต่ละ action, **ฟิลด์ที่ซ่อน** ที่ stage นั้น และ **ผู้ใช้ที่ได้รับมอบหมาย** ให้ดำเนินการ

เวิร์กโฟลว์เป็นแบบ *typed*: เวิร์กโฟลว์ SR ไม่สามารถแนบกับ PR Typing ผ่าน `enum_workflow_type` และบังคับเมื่อเอกสารเลือกเวิร์กโฟลว์ เวิร์กโฟลว์หลายตัวของ type เดียวกันอยู่ร่วมกันได้ — property โดยทั่วไปดำเนินงาน "Standard PR" และ "High-Value PR" ด้วย chain ที่แตกต่างกัน

**ตั้งแต่ 2026-09-16 หน้าจอถูกแยกต่อประเภทเอกสาร** กลุ่ม Workflows บน sidebar มีลูกสามตัว — Purchase Request, Purchase Order, Store Requisition (FE `a5b49e68`, `293009f0`, `f3e13d30`) — แต่ละตัว render โดย `workflow-doc-type.route.tsx` ซึ่งอ่าน type จาก segment สุดท้ายของ URL และเรียก endpoint ของ type นั้นเอง (`GET api/config/:bu_code/workflows/purchase-request` ฯลฯ, BE `003e12fb8`, guard `AppIdGuard('workflow.findAllPurchaseRequest' | 'findAllPurchaseOrder' | 'findAllStoreRequisition')`, `config_workflows.controller.ts:192-301`) `GET …/workflows` แบบ generic (`:542`) ยังมีอยู่ (ถูกเอาออกชั่วครู่แล้วคืนกลับ `4263c78f8`) แต่ FE ไม่ render รายการรวมอีกแล้ว; `/system-admin/workflow` เป็น `<Navigate>` ไปหน้า PR (`router.tsx:769-775`) การแยกทำให้มอบสิทธิ์ให้ application หรือ role หนึ่งประเภทเอกสารโดยไม่ต้องให้ประเภทอื่นได้ — nav entry gate ด้วย `system_admin.workflow.purchase_request.view` ฯลฯ (`module-list.ts:809-850`; ลูกตัวที่สี่ของกลุ่มคือ Notification Template ไม่ใช่ประเภทเอกสาร)

**บำรุงรักษาโดย** Sysadmin (หรือ Workflow Admin ที่ได้รับมอบหมาย) **อ่านโดย** engine runtime ของเวิร์กโฟลว์ในทุก stage transition

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้างเวิร์กโฟลว์ใหม่ | Workflows → *(ประเภทเอกสาร)* → **New** (`/system-admin/workflow/new`, `wf-new-form.tsx`) | เลือก `workflow_type`; สร้าง stages; type ของหน้าที่มาถูกเลือกไว้ล่วงหน้า |
| แก้ stage | `/system-admin/workflow/:id` → คลิก stage ใน rail (`wf-stage-list.tsx`, `wf-stages.tsx`, `wf-stage-detail.tsx`) | ลากเรียงใหม่ใน rail; ต่อ stage ตั้ง SLA, `role` ของ stage, `creator_access`, action, ผู้รับ, ฟิลด์ที่ซ่อน, ลายเซ็น |
| มอบหมายผู้ใช้ให้ stage | Stage → **Assigned Users** (`wf-stage-users.tsx`) | ระเบียนผู้ใช้ (`user_id`, ชื่อ, อีเมล, แผนก); รายการว่างที่ stage approve ที่ไม่ใช่ HOD = ใครก็ตามที่มี role ของ stage |
| Mark stage เป็น HoD gate | Toggle `is_hod = true` | Route ไปยัง HoD ของแผนกของเอกสาร; ละเว้น `assigned_users` |
| เลือกว่า stage ไหนพิมพ์ลายเซ็น | Stage → **Show signature** | สูงสุด **5** stage ลายเซ็นต่อเวิร์กโฟลว์ (`wf-signature-limit.ts` `MAX_SIGNATURES`); เวิร์กโฟลว์ PO ยังตั้ง `inherit_signature_from_pr` เพิ่มได้ (FE `409fcc81`) |
| เพิ่ม routing rule | tab **Routing** (`wf-routing.tsx`) | `trigger_stage` + เงื่อนไขบน `total_amount`, `department` หรือ `category` (`eq`/`lt`/`gt`/`lte`/`gte`/`between`) → ไปยัง `target_stage` ที่อยู่หลังใน chain (`SKIP_STAGE` / `NEXT_STAGE` derive ให้) |
| กำหนดขอบเขตเวิร์กโฟลว์ตามสินค้า | tab **Products** (`wf-products.tsx`, มุมมองตารางตั้งแต่ `53a4b0ee`, แถบ coverage ตั้งแต่ `b6e3818a`) | เก็บเป็น `data.products: string[]` (id เท่านั้น, `ff2b55db`); ใช้โดย location picker (ด้านล่าง) |
| เช็คว่าเวิร์กโฟลว์แก้ไขได้หรือไม่ | การเปิด `/system-admin/workflow/:id` เรียก `GET …/workflows/:id/edit-availability` (`use-wf-availability.ts`) | คืน `can_edit`, `can_edit_stages`, `can_delete`, `blocked_reason`, `documents{draft,in_progress,done,total}`; header แสดงจำนวน (`613e649c`) และ `wf-structure-lock-notice.tsx` อธิบายการล็อก |
| ส่งมอบ stage ของคนที่ลาออกให้คนอื่น | `GET …/workflows/assignees/:target_user_id` แล้ว `POST …/workflows/assignees/:target_user_id/handover` | แสดงทุก stage ที่ผู้ใช้ถูกระบุชื่อ ว่าถือคนเดียวหรือไม่ และจำนวน `in_progress` ต่อ stage; handover แทนที่พวกเขาใน stage ที่ระบุ **และประทับเอกสารที่รออยู่ที่นั่นใหม่** ในการเรียกเดียว (BE `4fecf678f`, `00ffaaeba`); ยังไม่มีหน้าจอ FE — Bruno เท่านั้น |
| หาว่าสินค้าใช้ได้ที่ไหนภายใต้เวิร์กโฟลว์ | `GET …/workflows/:workflow_id/products/:product_id/locations` | intersection ของ `data.products`, `tb_product_location` และแถว `tb_location_user` ของผู้เรียก; 404 สำหรับเวิร์กโฟลว์ที่ไม่รู้จัก `[]` สำหรับกรณีว่างอื่นทั้งหมด (BE `383fc4ca4`, `ec3f10704`) |
| Clone สำหรับ variant ใหม่ | row action **Duplicate** (`wf-row-actions.tsx`) หรือปุ่ม **Duplicate** บน header ของหน้า detail (`wf-header.tsx:151`) ซึ่งเปิดสำเนาให้ | เส้นทาง migration มาตรฐานสำหรับการเปลี่ยนแปลงที่ทำลายเข้ากันได้ |
| ปลดระวางเวอร์ชันเก่า | ตั้ง `is_active = false` (toggle บน row) | เอกสารใหม่เลือกจาก `is_active = true` เท่านั้น |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Workflow name exists" | `(name, workflow_type)` ซ้ำ | เลือกชื่ออื่น |
| Type assignment ไม่ตรงกัน | ประเภทเอกสาร ≠ `workflow_type` | เลือกเวิร์กโฟลว์ของ type ที่ถูก |
| issue จาก validation ฝั่ง client (listed ใต้ stage ใน rail และในรายการตรวจของ Overview) | code ของ `wf-validate.ts`: `empty_name`, `duplicate_name`, `no_users_assigned`, `no_actions_enabled`, `no_sla`, `missing_create_role`, `missing_completed_stage`, `role_not_allowed` | แก้ stage ที่ถูก flag (`wf-validation-panel.tsx` ถูกลบแล้ว; `submit_only_on_first` ประกาศไว้แต่ไม่เคย emit) |
| `WORKFLOW_STAGE_CHANGE_BLOCKED` ตอนบันทึก | รายการ stage หรือ routing rule เปลี่ยนขณะ `documents.in_progress > 0` (`workflows.service.ts:1380-1387`; `workflow-edit-scope.helper.ts` diff stage/routing) | รอให้เอกสารที่กำลังดำเนินอยู่เสร็จ หรือ clone; name / description / `is_active` / notification / products / assignee ยังแก้ได้ |
| `WORKFLOW_HAS_IN_PROGRESS_DOCUMENTS` ตอนลบ | มีเอกสาร `in_progress` บนเวิร์กโฟลว์นี้ (`delete()` `:1554-1571`) | inactivate แทน |
| ไม่สามารถ delete เวิร์กโฟลว์ | ถูกอ้างอิงโดยเอกสารที่ไม่ complete | Clone + inactivate เวอร์ชันเก่า |
| ผู้อนุมัติเห็นราคาที่ mask | `hide_fields.price_per_unit = true` ที่ stage ที่ active | คาดหวัง — ปรับ stage หากไม่ได้ตั้งใจ |
| HoD route ล้มเหลว | ไม่มี HoD ตั้งค่าสำหรับแผนกของเอกสาร | ตั้งค่า HoD บน [master-data/department](/th/inventory/master-data/department) |

## 4. กรณีพิเศษ

- **Versioning** การแก้เวิร์กโฟลว์ที่ live ไม่ retroactively เปลี่ยนเอกสารที่กำลังดำเนินอยู่ — runtime อ่านรายการ stage ตามที่เป็นตอน attach การเปลี่ยนแปลงที่ทำลายเข้ากันได้: clone ภายใต้ชื่อใหม่
- **เอกสารที่กำลังดำเนินอยู่ล็อกโครง ไม่ใช่ฟอร์ม (2026-09-02, BE `b1bcb1e98`; FE `8cac942d`)** `getEditAvailability` คืน `can_edit: true` เสมอ, `can_edit_stages: !(in_progress > 0)`, `blocked_reason: WORKFLOW_STAGE_CHANGE_BLOCKED` เมื่อล็อก (`workflows.service.ts:830-880`) คอลัมน์สถานะต่างกันต่อ type — PR `pr_status`, PO `po_status`, SR `doc_status` — และมีเพียง `draft` / `in_progress` ที่ระบุชื่อ; อย่างอื่นนับเป็น `done` (`countDocumentsByStatus` `:892`) FE ฉบับก่อน (`c60430ea`, 2026-09-01) ปฏิเสธการเข้าโหมด edit ทั้งหมด; ผ่อนคลายในวันถัดมา
- **Handover ประทับเอกสารที่รออยู่ใหม่** `POST …/assignees/:user_id/handover` apply การแทนที่ทั้งหมดในการเรียกเดียว เพื่อให้ handover ที่ apply ครึ่งเดียวเกิดขึ้นไม่ได้; มันยังเขียน `user_action` ใหม่บนเอกสารที่รออยู่ที่ stage เหล่านั้น (Bruno `POST-handover-assignee-config-workflows.bru`) stage ที่ actor มาจาก HOD ของแผนกหรือทั้งแผนกไม่ถูกแสดงโดย endpoint impact เพราะการเสียคนหนึ่งคนไม่ทำให้ว่าง
- **Assigned users vs stage role** `assigned_users` เก็บระเบียนผู้ใช้เต็ม (`user_id`, ชื่อ, อีเมล, แผนก — ดู §5.3) ไม่ใช่ role descriptor; `role` ของ stage (`enum_stage_role`) เป็นฟิลด์แยก รายการว่างที่ stage approve ที่ไม่ใช่ HOD = ใครก็ตามที่มี role ของ workflow-stage
- **HoD resolution** เมื่อ `is_hod: true` runtime lookup HoD ของแผนกและ route ไปที่นั่น — ละเว้น `assigned_users`
- **ฟิลด์ที่ซ่อน** mask cell UI แต่ค่ายังไหลผ่าน API

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_workflow`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key (`gen_random_uuid()`) |
| `name` | `String @db.VarChar` | No | ชื่อสำหรับแสดง |
| `workflow_type` | `enum_workflow_type` | No | `purchase_request`, `store_requisition`, `purchase_order`, `gl_jv` (เพิ่มเมื่อ 2026-09-09, `0d119b990`; โมดูล GL เท่านั้น), `ap_invoice`, `ap_payment`, `ar_invoice` (บัญชี เพิ่มหลัง 2026-09-22; ไม่มีหน้าที่นี่) ล็อกตอนสร้าง — update DTO ไม่มี `workflow_type` |
| `data` | `Json? @db.JsonB` | Yes | นิยาม stage เต็ม Default `{}` |
| `is_active` | `Boolean?` | Yes | Default `true` |
| `doc_version` | `Int` | No | Default `0` Optimistic-concurrency token — `PUT` ส่งกลับมา |
| `description` / `note` | `String? @db.VarChar` | Yes | Free text |
| `info` / `dimension` | `Json? @db.JsonB` | Yes | Metadata |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, workflow_type, deleted_at])` Index บน `[name, workflow_type]` และ `[name]` Reverse relations ไปยัง `tb_purchase_request`, `tb_purchase_request_template`, `tb_store_requisition`, `tb_workflow_comment`

### 5.2 Shape `data` JSONB

```
{
  "document_reference_pattern": "",
  "stages": [
    {
      "name": "Request Creation",
      "sla": "24",
      "sla_unit": "hours",
      "available_actions": {
        "submit":   { "is_active": true,  "recipients": { ... } },
        "approve":  { "is_active": false, "recipients": { ... } },
        "reject":   { "is_active": false, "recipients": { ... } },
        "sendback": { "is_active": false, "recipients": { ... } }
      },
      "hide_fields": { "price_per_unit": false, "total_price": false },
      "is_hod": false,
      "assigned_users": []
    }
  ]
}
```

Key ต่อ stage: `name`, `description`; `sla` + `sla_unit` (`hours`/`days`); `available_actions` (`is_active` + `recipients` ต่อ verb); `hide_fields` (mask financials); `is_hod` (HoD gate); `assigned_users` (user ID หรือ role descriptor)

### 5.3 key ที่เพิ่มหลังจากเขียน shape ข้างต้น (FE `wf-form-schema.ts:96-160`, ตรวจสอบ 2026-09-22)

| Key | ระดับ | Shape | หมายเหตุ |
|---|---|---|---|
| `inherit_signature_from_pr` | `data` | `boolean?` | เวิร์กโฟลว์ PO เท่านั้น — พิมพ์ลายเซ็นของ PR ต้นทางก่อนของ PO เอง ประกาศใน schema ของ FE เพื่อให้ `PUT` แบบ `data` เต็มจากหน้ารายการไม่ทำให้มันหายเงียบ ๆ |
| `products` | `data` | `string[]` (id สินค้า) | ขอบเขตสินค้า; contract ของ backend `products: string[]` (`workflow-products.helper.ts`); ป้อน `GET …/products/:product_id/locations` |
| `routing_rules` | `data` | `[{ name, description, trigger_stage, condition{ field: total_amount\|department\|category, operator: eq\|lt\|gt\|lte\|gte\|between, value[], min_value?, max_value? }, action{ type: SKIP_STAGE\|NEXT_STAGE, parameters{ target_stage } } }]` | ประเมินโดย `workflows.navagation.service.ts:340-348`; การเปลี่ยนขณะเอกสารกำลังดำเนินอยู่เป็น `WORKFLOW_STAGE_CHANGE_BLOCKED` |
| `notifications`, `notification_templates` | `data` | `[]` | มีอยู่ใน payload; array ว่างที่ HEAD |
| `available_stage_role` | `data` (server ประทับ) | `enum_stage_role[]` | `withAvailableStageRole()` ประทับ role ที่ถูกต้องสำหรับ type: PR `create/approve/purchase`, PO `create/approve`, SR `create/approve/issue` และ `create/approve` สำหรับ `gl_jv`, `ap_invoice`, `ap_payment`, `ar_invoice` (`workflow-stage-role.helper.ts:32-48`); `enum_stage_role` ยังมี `view_only` ซึ่งไม่ถูกเสนอโดยตั้งใจ |
| `role` | stage | `enum_stage_role?` | role ของ stage; validator ฝั่ง client ต้องการ role `create` อยู่ที่ไหนสักแห่ง (`missing_create_role`) |
| `creator_access` | stage | `string?` | ผู้สร้างเอกสารทำ action ที่ stage นี้ได้หรือไม่ (`wf-stage-general.tsx:119`); การเปลี่ยนขณะเอกสารกำลังดำเนินอยู่ถือเป็นการเปลี่ยนโครง (`workflow-edit-scope.helper.ts:104`) |
| `is_show_signature` | stage | `boolean?` | พิมพ์ลายเซ็นผู้อนุมัติของ stage นี้; สูงสุด 5 ต่อเวิร์กโฟลว์ |
| `sla_warning_notification` | stage | `{ recipients{ requestor, current_approve }, template? }` | เป้าหมายการเตือน SLA ใกล้เกิน |
| `assigned_users[]` | stage | `{ user_id, firstname, middlename, lastname, email, department{ id?, name? }, initials? }` | ระเบียนผู้ใช้เต็ม ไม่ใช่ id เปล่า |
| `available_actions.<verb>.recipients.<slot>` | stage | `boolean` **หรือ** `{ is_active, is_notification, notification_channel{ app{ is_active, notification_template_id }, email{…} } }` | slot `requestor`, `current_approve` (ยังเก็บในข้อมูลแต่ไม่เคย dispatch และถูกล้างตอนโหลด), `next_step`, `previous_step` (ไม่บังคับ; ในทางปฏิบัติเฉพาะ Reject); editor ตอนนี้เสนอเฉพาะ channel `app` (`WfChannel = "app"`, `wf-stage-notifications.tsx:11`) — `email` ยังคงอยู่สำหรับแถวเก่าแต่ไม่เคยถูก dispatch (ดู [system-config/notification-template](/th/inventory/system-config/notification-template)) |

### 5.4 API surface (gateway, ตรวจสอบ 2026-09-22)

```
config_workflows.controller.ts  (api/config/:bu_code/workflows)          AppIdGuard api_name
  GET    assignees/:target_user_id                                        workflow.findAssigneeImpact
  POST   assignees/:target_user_id/handover                               workflow.handoverAssignee
  GET    purchase-request | purchase-order | store-requisition            workflow.findAllPurchaseRequest | …PurchaseOrder | …StoreRequisition
  GET    :workflow_id/products/:product_id/locations                      workflow.findProductLocations
  GET    :workflow_id/edit-availability                                   workflow.getEditAvailability
  GET    :workflow_id · GET (all) · POST · PUT :workflow_id · DELETE      workflow.findOne / findAll / create / update / delete
  PUT    :workflow_id/notification                                        workflow.updateNotification
workflows.controller.ts  (application)
  GET    /type/:type · GET :workflow_id/previous_stages · PATCH patch-user-action
```

Licence: ทุก route `config:workflows` resolve ไป `system_admin.workflow` พร้อม sub-feature ต่อ type (`permission.route-map.ts:234`, BE `6832493b7` "sell workflow per document type")

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** `(name, workflow_type)` unique ในกลุ่มที่ไม่ถูก delete
- **Type binding** ประเภทเอกสาร X แนบกับเวิร์กโฟลว์ที่ `workflow_type = X` เท่านั้น; runtime reject mismatch
- **At-least-one submit stage** Stage แรกต้องเปิด `submit`; stage ถัดไปต้องเปิดอย่างน้อยหนึ่งใน `approve` / `reject` / `sendback`
- **การ์ดการลบ** เวิร์กโฟลว์ที่มีเอกสาร `in_progress` ใด ๆ ไม่สามารถ delete (`WORKFLOW_HAS_IN_PROGRESS_DOCUMENTS`); clone + inactivate คือเส้นทาง migration
- **การล็อกโครง** ขณะมีเอกสาร `in_progress` การเปลี่ยนรายการ stage, ลำดับ stage, `creator_access` หรือ `routing_rules` ถูกปฏิเสธด้วย `WORKFLOW_STAGE_CHANGE_BLOCKED`; ฟิลด์อื่นบันทึกตามปกติ
- **Versioning** การแก้ live ไม่ retroactively เปลี่ยนเอกสารที่กำลังดำเนินอยู่
- **Stage role ผูกกับ type** เฉพาะ role ใน `available_stage_role` ของ type ของเวิร์กโฟลว์เท่านั้นที่ใช้ได้กับ stage ของมัน
- **HoD resolution** Lookup HoD ของแผนกของเอกสาร; ละเว้น `assigned_users`
- **ฟิลด์ที่ซ่อน** mask cell UI; ค่าใน API ยังไหลผ่าน

## 7. การอ้างอิงข้าม

- [purchase-request](/th/inventory/purchase-request) — consumer หลัก (`purchase_request`)
- [store-requisition](/th/inventory/store-requisition) — ผู้ใช้หลายขั้นแบบมาตรฐาน (`store_requisition`)
- [purchase-order](/th/inventory/purchase-order) — การอนุมัติมูลค่าสูง (`purchase_order`)
- **สามโมดูลนี้คือโมดูล inventory เดียวที่ผูกเวิร์กโฟลว์ได้** `enum_workflow_type` มี member เจ็ดค่าที่ HEAD (`schema.prisma:271-279`): สามค่าข้างต้นบวก `gl_jv` (GL journal voucher) และ `ap_invoice` / `ap_payment` / `ar_invoice` — โมดูลบัญชี ไม่มีหน้า inventory ไม่มี endpoint ต่อ type ที่นี่ [good-receive-note](/th/inventory/good-receive-note), [inventory-adjustment](/th/inventory/inventory-adjustment), [vendor-pricelist](/th/inventory/vendor-pricelist), [physical-count](/th/inventory/physical-count) และ [spot-check](/th/inventory/spot-check) ไม่มี enum member และ **ไม่สามารถ** ผูก row `tb_workflow` ได้ (เวอร์ชันก่อนหน้าของรายการนี้ระบุ "การ gate ด้วยเวิร์กโฟลว์แบบ optional" สำหรับโมดูลเหล่านั้นไว้ผิด)
- [access-control/application-role](/th/inventory/access-control/application-role) — Role descriptor ใน `assigned_users`
- [master-data/department](/th/inventory/master-data/department) — HoD resolution

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_workflow`, `enum_workflow_type` (lines 271-279), `enum_stage_role`
- **Seed:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/tb_workflow.json`
- **Backend gateway:** `../carmen-turborepo-backend/apps/backend-gateway/src/config/config_workflows/config_workflows.controller.ts`; `apps/backend-gateway/src/application/workflows/workflows.controller.ts`
- **Backend service:** `../carmen-turborepo-backend/apps/micro-business/src/master/workflows/` — `workflows.service.ts` (`getEditAvailability` `:830`, `countDocumentsByStatus` `:892`, ล็อก `:1380-1387`, `delete` `:1554`), `workflow-edit-scope.helper.ts` (อะไรนับเป็นการเปลี่ยนโครง), `workflow-stage-role.helper.ts`, `workflow-products.helper.ts`, `workflows.navagation.service.ts` (routing rule)
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/workflows/` — `GET-find-all-{purchase-request,purchase-order,store-requisition}-…`, `GET-find-assignee-impact-…`, `POST-handover-assignee-…`, `GET-find-product-locations-…`, `GET-get-edit-availability-…`
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` — semantics ของ role-type (freeze เมื่อ 2026-04-27; ก่อนมีหน้าต่อ type, routing rule และการล็อกโครง)
- **Frontend:** `../carmen-frontend/routes/system-admin/workflow/` — `workflow-doc-type.route.tsx` (รายการต่อ type), `wf-component.tsx`, `wf-new-form.tsx`, `wf-edit-content.tsx`, `wf-detail.tsx` (layout), `wf-stage-list.tsx` / `wf-stage-rail-node.tsx` (rail), `wf-stages.tsx` / `wf-stage-*.tsx`, `wf-insights*.ts(x)`, `wf-routing*.ts(x)`, `wf-products*.tsx`, `wf-seeded-templates.ts`, `wf-form-schema.ts` (shape ของ data), `wf-validate.ts` (code กฎฝั่ง client), `wf-signature-limit.ts`, `use-wf-availability.ts`, `wf-structure-lock-notice.tsx`; `constant/module-list.ts:805-850`
- **E2E:** `../carmen-frontend-e2e/docs/test-cases/1103-workflow.md` — แคตตาล็อกเท่านั้น (ไม่มี Playwright spec)
