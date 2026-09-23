---
title: รายการอนุมัติของฉัน (My Approval)
description: คิว pending ส่วนบุคคล — PR, PO และ SR ทุกใบที่ผู้ใช้ที่ล็อกอินต้องดำเนินการ ให้บริการเป็น list เดียวที่เรียงแล้วจาก view sys_v_my_pending ผ่าน GET /api/my-pending
published: true
date: '2026-09-23T01:30:00.000Z'
tags: purchase-request, approval, workflow, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# รายการอนุมัติของฉัน (My Approval)

> **At a Glance**
> **เจ้าของ:** ผู้อนุมัติของ workflow ใด ๆ (และเจ้าของ draft ใด ๆ) &nbsp;·&nbsp; **ตาราง:** *ไม่มี — view อ่านอย่างเดียว `sys_v_my_pending`* &nbsp;·&nbsp; **Workflow:** กล่องขาเข้าแบบอ่านอย่างเดียว; ทุก action เกิดบนเอกสารต้นทาง &nbsp;·&nbsp; **ต้นน้ำ:** [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [store-requisition](/th/inventory/store-requisition) &nbsp;·&nbsp; คิวส่วนบุคคลที่รวมเอกสารทั้งหมดที่รอให้ผู้ใช้ที่ล็อกอินดำเนินการ

![รายการอนุมัติของฉัน (My Approval) screen](/screenshots/purchase-request/my-approval.png)

> **ตรวจสอบซ้ำ 2026-09-22** คิวถูกสร้างใหม่ทั้งสองฝั่งตั้งแต่เอกสารรุ่นก่อนของหน้านี้: backend เพิ่ม read model แบบรวม (`apps/backend-gateway/src/application/my-pending/unified/`, micro-business `src/my-pending/`, database view `sys_v_my_pending` — migration `20260916030000_add_sys_v_my_pending`) และ frontend เปลี่ยนมาใช้เมื่อ 2026-09-16 (`routes/procurement/approval/use-approval.ts`, commit `9bd21427` "หน้าอนุมัติใช้ /api/my-pending แทนการรวมสามกลุ่มฝั่ง client") Credit Note ไม่เคยเป็นส่วนหนึ่งของคิวนี้ — เอกสารรุ่นก่อนของหน้านี้ list ไว้ผิด

## 1. ภาพรวมและผู้ใช้งาน

**My Approval** (`/procurement/approval`, `routes/router.tsx:287-288`) คือคิวต่อผู้ใช้ของ **Purchase Request, Purchase Order และ Store Requisition** ทุกใบที่ยังต้องการ action ของผู้ใช้ที่ล็อกอิน ในขณะที่แต่ละโมดูล list *เอกสารทั้งหมด*ของตน หน้านี้แสดงเฉพาะ**ส่วนที่ผู้ใช้ปัจจุบันต้องดำเนินการในตอนนี้เท่านั้น** — บวก draft ที่ยังไม่ submit ของผู้ใช้เอง หน้านี้เป็นแบบ **อ่านและ navigate เท่านั้น**: ไม่มีตารางของตัวเอง, ไม่ render ปุ่ม Approve / Reject และทุกการตัดสินใจทำบนหน้า detail ของเอกสารต้นทาง

**ผู้ใช้งาน** คือใครก็ตามที่ถูกระบุใน `user_action.execute[]` ของ stage ใน workflow (HOD, Purchaser, FC, GM, …) และใครก็ตามที่เป็นเจ้าของ PR / PO / SR สถานะ `draft` &nbsp;·&nbsp; **ไม่มีการ write-back** — หน้านี้อ่านอย่างเดียว

## 2. สิ่งที่ frontend เรียกวันนี้

| วัตถุประสงค์ | Endpoint | แหล่งที่มา |
|---|---|---|
| แถวของคิว (list เดียวแบบ flat เรียงแล้ว แบ่งหน้า ของ PR + PO + SR) | `GET /api/my-pending` — query `bu_code` (optional; ถ้าไม่ระบุ = ทุก business unit ที่ผู้ใช้สังกัด), `page`, `perpage`, `sort`, `filter`, `search`, `searchfields` | `use-approval.ts` → `API_ENDPOINTS.APPROVAL_PENDING` (`constant/api-endpoints.ts:40`); backend `my-pending.unified.controller.ts` (`AppIdGuard('my-pending.unified.findAll')`) |
| Card สรุป (จำนวน `total` / `pr` / `po` / `sr`) | `GET /api/my-approve/pending` | `use-approval.ts` → `APPROVAL_PENDING_SUMMARY` (`api-endpoints.ts:41`); backend `my-approve.controller.ts` (`AppIdGuard('my-approve.findAllPending.count')`) |

Endpoint ที่ยังมีอยู่แต่หน้า approval **ไม่เรียกแล้ว**: `GET /api/my-approve` (response แบบจัดกลุ่มรุ่นเก่า — สาม array แต่ละอันมี pagination envelope; `my-approve.controller.ts`) และตระกูลต่อประเภท `GET /api/my-pending/purchase-requests`, `/purchase-orders`, `/store-requisitions` (แต่ละอันมีจำนวน `/pending`, `:bu_code/workflow-stages`, `:bu_code/:id` และ verb submit / approve / reject / review / save ชุดเดียวกับ endpoint ของโมดูล — `apps/backend-gateway/src/application/my-pending/{purchase-request,purchase-order,store-requisition}/`) endpoint ต่อประเภทคือตัวที่แท็บ **My Pending** ของ list PR และแอป mobile ใช้; การค้นหาระดับบรรทัดสินค้าทำได้ที่นั่นเท่านั้น เพราะ view รวมมีเฉพาะข้อความ header สัญญา Bruno: `../carmen-turborepo-backend-bruno/collections/carmen-inventory/my-pending/`

## 3. งานที่พบบ่อย

| งาน | ตำแหน่ง | หมายเหตุ |
|---|---|---|
| ดูรายการที่ค้างอยู่ | Procurement → **My Approval** | ลำดับ default `doc_date:asc` (เอกสารเก่าสุดก่อน, `MY_PENDING_DEFAULT_SORT` ใน `my-pending.sql.ts`; FE `defaultSort: "doc_date:asc"` ใน `approval-component.tsx`) ตัดสินเสมอด้วย `doc_type, id` เพื่อให้การแบ่งหน้าคงที่ |
| แคบลงเหลือประเภทเอกสารเดียว | คลิก card สรุป **Purchase Request / Purchase Order / Store Requisition** | ตั้ง `filter=doc_type:pr` (หรือ `po` / `sr`); **Total Pending** ล้าง filter การกรอง ค้นหา และแบ่งหน้าทั้งหมดรันใน SQL ดังนั้น `paginate.total` คือจำนวนที่ match จริง |
| ค้นหา | ช่องค้นหาบน toolbar | ข้อความ header เท่านั้น: `doc_no`, `description`, `requestor_name`, `department_name`, `counterparty_name`, `workflow_current_stage` (`DEFAULT_SEARCH_COLUMNS`) |
| เรียงตามคอลัมน์ | คลิก header ของคอลัมน์ | เรียงได้เฉพาะคอลัมน์ของ view ที่อยู่ใน allowlist (`COLUMN_TYPES` ใน `my-pending.sql.ts`); key ที่ไม่รู้จักถูกตัดทิ้งเงียบ ๆ และ list กลับไปใช้ `doc_date` |
| เปิดเอกสาร | link ในคอลัมน์ **Document** | `/procurement/purchase-request/:id`, `/procurement/purchase-order/:id` หรือ `/store-operation/store-requisition/:id` (`approve-queue-list.tsx` `DOC_TYPE_CONFIG`) — approve / reject / send back ที่นั่น |
| อนุมัติแบบ bulk | *ไม่มีบนหน้านี้* | Mobile ใช้ `POST /:bu_code/purchase-requests/swipe-approve` / `swipe-reject` (และคู่แฝดของ PO); คิวบน web ไม่มี multi-select |

คอลัมน์ที่ `approve-queue-list.tsx` render: `#`, Document (`doc_no` มี link), เครื่องหมาย Send-back, badge ประเภท (`pr` / `po` / `sr`), Date (`doc_date`), Status (`doc_status` render ด้วย label `PR_STATUS_CONFIG` สำหรับทุกประเภท)

## 4. ข้อผิดพลาดและการตรวจสอบ

| อาการ / ข้อความ | สาเหตุ | การแก้ไข |
|---|---|---|
| ไม่พบแถวในคิว | ผู้ใช้ที่ล็อกอินไม่อยู่ใน `user_action.execute[]` ของ stage ปัจจุบันของเอกสาร และเอกสารไม่ใช่ `draft` ที่ผู้ใช้เป็นเจ้าของ | ตรวจสอบ membership ของ stage ใน [system-config/workflow](/th/inventory/system-config/workflow) |
| แถวยังอยู่ทั้งที่ผู้ใช้ "อนุมัติไปแล้ว" | Action ถูกทำบน `doc_version` ที่ stale หรือ peer ลงมือก่อน; เอกสารต้นทางปฏิเสธการเขียน (409) | Reload เอกสารต้นทาง — คิว refresh ตาม stale time 1 นาทีของ `CACHE_DYNAMIC` |
| แถวแสดงเอกสาร `draft` | draft ของตัวเองถูกรวมโดยตั้งใจ (สาขา `("doc_status" = 'draft' AND "owner_id" = me)` ของ predicate) | ถูกต้อง — เปิดแล้ว submit หรือลบ |
| แถวของ business unit ที่ผู้ใช้ไม่ได้เลือก | ไม่ระบุ `bu_code` → service อ่านทุก unit ที่ผู้ใช้สังกัด (`resolveBuCodes`, `my-pending.service.ts`) และ merge หน้าใน memory | ส่ง `bu_code` เพื่อแคบลง |
| คลิก sort "ไม่มีอะไรเกิดขึ้น" | Sort key ไม่ใช่คอลัมน์ของ view | ใช้คอลัมน์ใน allowlist (หัวข้อ 5.2) |
| เห็นเอกสารข้าม tenant | เกิดขึ้นไม่ได้ | แต่ละ unit ถูก query ผ่าน tenant connection ของตัวเอง; unit ที่ resolve ไม่ได้ถูกข้ามและ log |

## 5. โมเดลข้อมูล (Dev)

**ไม่มีตาราง `tb_my_approval`** ตั้งแต่ migration `20260916030000_add_sys_v_my_pending` คิวอ่านจาก database view `sys_v_my_pending` ซึ่งเป็น `UNION ALL` ของ `tb_purchase_request`, `tb_purchase_order` และ `tb_store_requisition` ที่ normalise เป็น row shape เดียว view ถูก deploy ต่อ tenant schema และถูกสร้างใหม่ด้วย `DROP VIEW … CREATE VIEW` ทุกครั้งที่เปลี่ยน (ลำดับและ type ของคอลัมน์เป็นส่วนหนึ่งของสัญญา)

### 5.1 Row shape (`MyPendingUnifiedItemResponseDto`, `unified/swagger/response.ts`)

| คอลัมน์ | แหล่ง PR | แหล่ง PO | แหล่ง SR |
| --- | --- | --- | --- |
| `doc_type` | `'pr'` | `'po'` | `'sr'` |
| `id`, `doc_no`, `doc_date` | `id`, `pr_no`, `pr_date` | `id`, `po_no`, `order_date` | `id`, `sr_no`, `sr_date` |
| `due_date` | `NULL` | `delivery_date` | `expected_date` |
| `doc_status` | `pr_status::text` | `po_status::text` | `doc_status::text` |
| `doc_subtype` | `NULL` | `po_type` | `sr_type` |
| `description`, `workflow_id`, `workflow_name`, `workflow_current_stage`, `workflow_next_stage`, `workflow_previous_stage` | คอลัมน์ชื่อเดียวกัน | เหมือนกัน | เหมือนกัน |
| `owner_id`, `requestor_name` | `requestor_id`, `requestor_name` | `buyer_id`, `buyer_name` | `requestor_id`, `requestor_name` |
| `department_id`, `department_name` | คอลัมน์ header | `NULL` (PO ไม่มีแผนก) | คอลัมน์ header |
| `counterparty_name` | `NULL` | `vendor_name` | `"<from_location_name> -> <to_location_name>"` |
| `currency_code` | `NULL` | `currency_code` | `NULL` |
| `net_amount`, `total_amount` | `base_net_amount`, `base_total_amount` | `SUM(detail.base_net_amount)`, `SUM(detail.base_total_price)` | `NULL` (SR ไม่มีมูลค่าเงิน) |
| `total_qty` | `NULL` | `total_qty` | `SUM(detail.requested_qty)` |
| `last_action`, `last_action_at_date`, `last_action_by_id`, `last_action_by_name`, `user_action`, `created_at`, `created_by_id`, `doc_version` | คอลัมน์ header | เหมือนกัน | เหมือนกัน |
| `bu_code`, `bu_name` | เพิ่มโดย service ต่อ business unit ที่อ่าน | | |

`user_action` ถูกอ่าน (filter stage-role ของ mobile ต้องใช้) แต่**ถูกตัดออกก่อน row ออกจาก service** — มันระบุชื่อผู้ใช้อื่น gateway เพิ่ม `@EnrichAuditUsers()`; ตั้งแต่ 2026-09-18 ฟิลด์ vendor / audit บน list เป็น object ตรงกับ endpoint list ต่อ unit

### 5.2 Predicate, การยกเว้น, index

```
WHERE  ("user_action" -> 'execute' @> '[{"user_id": <me>}]'::jsonb
        OR ("doc_status" = 'draft' AND "owner_id" = <me>))
  AND  <allowlisted filter predicates>
  AND  (<search columns> ILIKE '%term%')          -- when search is given
ORDER BY <caller sort, allowlisted> , "doc_type" ASC, "id" ASC
LIMIT / OFFSET                                    -- perpage = -1 fetches everything
```

- เอกสารที่จบแล้วไม่เข้า view เลย — รายการยกเว้นคัดลอกตรงตัวจาก filter pending ต่อประเภททั้งสาม: PR `NOT IN ('voided','approved','completed')`; PO `NOT IN ('voided','approved','sent_or_print','partial','closed','completed')`; SR `NOT IN ('voided','completed','cancelled')` สถานะ `NULL` ถูกยกเว้นด้วย
- คอลัมน์ที่เรียง / กรองได้ (`COLUMN_TYPES`, `my-pending.sql.ts`): `doc_type`, `doc_no`, `doc_date`, `due_date`, `doc_status`, `doc_subtype`, `description`, `workflow_id`, `workflow_name`, `workflow_current_stage`, `workflow_next_stage`, `workflow_previous_stage`, `owner_id`, `requestor_name`, `department_id`, `department_name`, `counterparty_name`, `currency_code`, `net_amount`, `total_amount`, `total_qty`, `last_action`, `last_action_at_date`, `last_action_by_name`, `created_at`, `doc_version` ค่า filter รองรับ list คั่นด้วย comma (`= ANY`), `name|contains`, `name|daterange` (`from,to`)
- Index ที่ migration สร้าง: GIN `jsonb_path_ops` บน `(user_action -> 'execute')` สำหรับทั้งสามตาราง (`ix_pr_user_action_execute`, `ix_po_user_action_execute`, `ix_sr_user_action_execute`) บวก partial index สำหรับเจ้าของ draft `ix_po_buyer_draft`, `ix_sr_requestor_draft` (`tb_purchase_request` มี `ix_pr_requestor_status` อยู่แล้ว)
- **การ merge หลาย unit** เมื่อไม่มี `bu_code` `my-pending.service.ts` resolve ทุก membership ที่ active จาก `tb_user_tb_business_unit` รัน statement ต่อ tenant schema merge แถวด้วย comparator เดียวกับที่ SQL ใช้ (`compareRows`, `NULLS LAST`) และรวม `paginate.total` ข้าม unit
- **Mobile** header `x-app-id` เลือก policy stage-role ต่อประเภทเอกสาร (`getMobileStageRoleFilter(appId, 'pr' | 'po' | 'sr')`); SR คง stage `issue` ไว้ PR และ PO ไม่

## 6. Workflow / กติกาทางธุรกิจ

คิว **ไม่มีสถานะของตัวเอง** — พฤติกรรมทั้งหมดเป็น projection:

- **แถวปรากฏ** เมื่อ workflow engine เขียน id ของผู้ใช้ที่ล็อกอินเข้า `user_action.execute[]` ของเอกสาร หรือเมื่อผู้ใช้ save `draft` ที่ตนเป็นเจ้าของ
- **แถวหายไป** เมื่อสถานะของเอกสารเข้ารายการยกเว้น (final approve, complete, void, cancel) หรือเมื่อการ transition stage คำนวณ `execute[]` ใหม่โดยไม่มีผู้ใช้
- **Approve / reject / send back** คือ endpoint ของโมดูลต้นทาง (`PATCH /:bu_code/purchase-requests/:id/approve` ฯลฯ) แต่ละอัน guard ด้วย optimistic lock `doc_version` ของเอกสารต้นทาง — ดู [system-config/doc-version](/th/inventory/system-config/doc-version) คิวเองไม่เคยเขียน

## 7. ความเชื่อมโยงข้ามโมดูล

- [purchase-request](/th/inventory/purchase-request) — ประเภทเอกสารหลัก; แท็บ **My Pending** ของ list PR เองอ่านจาก endpoint ต่อประเภท `GET /api/my-pending/purchase-requests`
- [purchase-order](/th/inventory/purchase-order) — PO ที่รออนุมัติ (เฉพาะ `draft` / `in_progress`; `approved` และ `sent_or_print` ถูกยกเว้น)
- [store-requisition](/th/inventory/store-requisition) — SR ที่รออนุมัติหรือ issue
- [system-config/workflow](/th/inventory/system-config/workflow) — นิยาม stage และกฎที่ populate `user_action.execute[]`
- [purchase-request/03-user-flow-approver](/th/inventory/purchase-request/03-user-flow-approver) — flow walkthrough ของ persona ผู้อนุมัติ

## 8. แหล่งอ้างอิง

- **View + index:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/migrations/20260916030000_add_sys_v_my_pending/migration.sql`
- **Backend:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/my-pending/unified/` (controller, service, `swagger/response.ts`), `.../my-pending/my-approve/` (จำนวนสรุป), `.../apps/micro-business/src/my-pending/` (`my-pending.sql.ts` predicate / allowlist / sort default, `my-pending.service.ts` การ merge หลาย unit)
- **Frontend:** `../carmen-inventory-frontend-react/routes/procurement/approval/` (`approval.route.tsx`, `approval-component.tsx`, `approve-queue-list.tsx`, `use-approval.ts`), `types/approval.ts` (`RawApprovalUnified`, `ApprovalItem`, `ApprovalPendingSummary`)
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/my-pending/` (`my-approve/`, `purchase-request/`, `purchase-order/`, `store-requisition/`)
- **E2E:** `../carmen-inventory-frontend-e2e/tests/201-my-approvals.spec.ts` (21 test), gap report `docs/test-cases/gaps/201-my-approvals-gap.md` (34 case ที่ catalogue ไว้), story ที่ generate `docs/user-stories/201-my-approvals.md`
