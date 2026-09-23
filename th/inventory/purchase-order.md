---
title: ใบสั่งซื้อ (Purchase Order)
description: เอกสารผูกพันอย่างเป็นทางการกับผู้ขายเพื่อจัดซื้อสินค้าตามราคา ปริมาณ และเงื่อนไขการส่งมอบที่ตกลงกัน
published: true
date: '2026-09-23T01:30:00.000Z'
tags: purchase-order, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# ใบสั่งซื้อ (Purchase Order)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** เอกสารผูกพันกับผู้ขายภายนอก (`draft` → `in_progress` (อยู่ระหว่างอนุมัติ) → `approved` → `sent_or_print` (ส่งอีเมลหรือ mark ว่าส่งแล้ว) → `partial`/`completed` → `closed` โดย `voided` เข้าถึงได้เฉพาะจาก `in_progress` ผ่านการ reject เท่านั้น) ที่ส่งต่อไปยัง GRN เมื่อรับของ &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Purchaser, Procurement Manager, Vendor, Receiver, Auditor &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_purchase_order` (ตอนนี้มี `delivery_point_id` บน header), `tb_purchase_order_detail` (หนึ่งแถว = หนึ่ง location), สะพาน PR↔PO `tb_purchase_order_detail_tb_purchase_request_detail` (FOC ที่สั่งเทียบกับที่รับ), รายการ email/mark-sent ใน `tb_activity`, [purchase-order/credit-note](/th/inventory/purchase-order/credit-note) &nbsp;·&nbsp; **หน้าย่อย:** 18

> ⚠️ **Re-sync 2026-09-22 กับ source HEAD** มี breaking change 3 อย่างนับจาก baseline 2026-07-29 ที่กระทบทุกหน้าย่อย: (1) `enum_purchase_order_doc_status` เพิ่ม `approved` และเปลี่ยนชื่อ `sent` → `sent_or_print` (migration `20260914080000_po_status_add_approved`, `20260914080100_po_status_backfill_and_rename_sent`) — การอนุมัติขั้นสุดท้ายตอนนี้ลงที่ `approved` และ `sent_or_print` เข้าถึงได้เฉพาะเมื่อ `POST .../purchase-orders/:id/send-email` สำเร็จ หรือ `POST .../purchase-orders/:id/mark-sent`; (2) PO line หนึ่งบรรทัด = delivery location เดียว (`feat(po)!: location ย้ายมาแบนบน detail`, 2026-09-09) — breakdown `locations[]` แบบซ้อนหายไปจาก create payload และ detail response; (3) `tb_purchase_order.delivery_point_id/name` บน header (`20260915120000_po_header_delivery_point`) และ `pr_detail_foc_qty` / `foc_received_qty` บนสะพาน PR↔PO (`20260916030000_po_junction_foc_ordered_vs_received`)

![ใบสั่งซื้อ (Purchase Order) screen](/screenshots/purchase-order/index.png)

![ใบสั่งซื้อ (Purchase Order) detail screen](/screenshots/purchase-order/detail.png)

## 1. ภาพรวม

**ใบสั่งซื้อ (Purchase Order — PO)** คือเอกสารทางการที่มีผลผูกพันภายนอก ซึ่งผู้ซื้อออกให้ผู้ขาย และผูกพันองค์กรให้ซื้อสินค้าหรือบริการตามรายการที่ระบุ ในราคาต่อหน่วย ปริมาณ วันส่งของ และเงื่อนไขการชำระเงินที่ตกลงไว้ PO แต่ละใบมีส่วนหัว — หมายเลขอ้างอิงที่ไม่ซ้ำ ผู้ขาย วันที่สั่งซื้อ วันส่งของที่ต้องการ จุดส่งของ สกุลเงินและอัตราแลกเปลี่ยน เงื่อนไขการชำระเงินและการส่งของ สถานะ ผู้สร้าง และยอดรวมที่ roll-up แล้ว — และรายการสินค้าหนึ่งรายการขึ้นไปที่บรรจุข้อมูลสินค้าจากแคตตาล็อกหรือคำอธิบายอิสระ ปริมาณที่สั่ง หน่วยนับ ราคาต่อหน่วย ส่วนลด การจัดการภาษี ปริมาณ FOC และฟิลด์ traceability ที่ลิงก์กลับไปยังบรรทัดของใบขอซื้อต้นทาง ยอดรวมส่วนหัว (subtotal, total discount, total tax, grand total) คำนวณจากค่าระดับบรรทัดที่ปัดเศษแล้ว และ dual-post ทั้งในสกุลเงินที่ใช้บันทึกธุรกรรมและสกุลเงินฐาน

วงจรชีวิตของ PO ขับเคลื่อนด้วยสถานะ (`enum_purchase_order_doc_status`): `draft` (แก้ไขได้ ยังไม่มีการผูกพัน) → `in_progress` (ถูกส่งเข้าสู่ workflow การอนุมัติแบบหลายขั้นตอนที่กำหนดไว้ — แต่ละขั้นตอนมี `stage_role` เช่น `purchase` หรือ `approve` และรายชื่อผู้มีสิทธิ์ดำเนินการใน `user_action.execute[]`) → `approved` (ขั้นตอนอนุมัติสุดท้าย; `purchase-order.logic.ts` `performApprove`: `po_status: isFinalApproval ? approved : in_progress` และ set `approval_date` — **ยังไม่มีการส่งอะไรออกไป**) → `sent_or_print` (เข้าถึงได้เฉพาะเมื่อ PO ไปถึงผู้ขายจริง: `POST .../purchase-orders/:id/send-email` สำเร็จ หรือผู้ใช้บันทึกการส่งนอกระบบด้วย `POST .../purchase-orders/:id/mark-sent`; ทั้งคู่เป็น `updateMany where po_status = approved` ใน `purchase-order.service.ts` `markPoAsSent`) → อาจเป็น `partial` เมื่อมีการ post GRN กับ PO → `completed` เมื่อทุกบรรทัดถูกจับคู่ครบ หรือ `closed` เมื่อ PO ถูกปิดในเชิงบริหารก่อนกำหนดโดยส่วนที่เหลือถูกเขียนลงใน `cancelled_qty` GRN สร้างได้กับ PO ที่ `approved`, `sent_or_print`, หรือ `partial` — การรับของปลดล็อกตอนอนุมัติ ไม่ใช่ตอนส่ง (`findOnePoForGrn`, `receivableStatuses`) `voided` เข้าถึงได้เฉพาะจาก `in_progress` เมื่อผู้อนุมัติที่ขั้นตอนปัจจุบัน reject PO เท่านั้น — เป็นการเปลี่ยนสถานะแบบตรงและสิ้นสุด (terminal) โดยไม่มีการย้อนกลับไป `draft` ระหว่างทาง การลบทำได้เฉพาะใน `draft` เท่านั้น และเฉพาะโดยเจ้าของเอกสารหรือ platform super-admin (`remove()`, `isDocumentOwner`) action "ส่งกลับเพื่อแก้ไข" (`review`) แยกต่างหาก ไม่เปลี่ยน `po_status` — เพียงรีเซ็ต `workflow_current_stage` กลับไปยังขั้นตอนก่อนหน้า (โดยทั่วไปกลับไปยังผู้สร้าง) ในขณะที่ PO ยังคงอยู่ใน `in_progress`; การ submit ซ้ำหลังถูกส่งกลับทำได้เพราะ `submit()` รับทั้ง `draft` **หรือ** `in_progress + last_action = reviewed` เลข PO ถูกกำหนดครั้งเดียวตอนสร้างและ **ไม่ออกเลขใหม่ตอน submit อีกต่อไป** (`fix(po): PO เลิกออกเลขใหม่ตอน submit`, 2026-09-14) การ short-close PO — ยอมรับการรับของบางส่วนเป็นการสิ้นสุด — เป็นการกระทำโดยจงใจที่ปล่อย commitment ส่วนที่เหลือออก

PO เกิดขึ้นได้ 3 ช่องทาง เลือกจาก dialog **Create Purchase Order** (`po-create-dialog.tsx`): สร้างด้วยมือ (PO เปล่าที่สร้างจาก scratch ที่ `/procurement/purchase-order/new`, `po_type = manual`), โดยการแปลงใบขอซื้อ (Purchase Request) ที่อนุมัติแล้วหนึ่งใบขึ้นไป (`po_type = purchase_request`, หน้า 3 ขั้นตอน `/procurement/purchase-order/from-pr` — Select PRs → Review Groups → Result, `routes/procurement/purchase-order/from-pr/`), หรือสร้างโดยตรงจาก vendor price list ผ่าน wizard 4 ขั้นตอน — Order Details → Select Vendors → Select Items → Review & Confirm (`po_type = pricelist`, `routes/procurement/purchase-order/from-price-list/`) เมื่อเลือก PR หลายใบเพื่อแปลง เซิร์ฟเวอร์ group บรรทัดด้วย **vendor + delivery date + currency** (`buildPoGroupKey` → `${vendor_id}|${yyyy-MM-dd}|${currency_id}`) สร้าง PO หนึ่งใบต่อแต่ละ combination ที่ไม่ซ้ำ และรวมบรรทัดของ PR เข้าไปในนั้น พร้อมรักษา traceability จาก PR ไปยัง PO บนทุกบรรทัด (`POST .../purchase-orders/group-pr` สำหรับ preview, `POST .../purchase-orders/confirm-pr` สำหรับสร้างจริง) ตั้งแต่ 2026-09-15 endpoint ทั้งสองรับ header override แบบ optional `delivery_date`, `delivery_point_id`, และ `note` ด้วย (`IPurchaseOrderFromPrOverrides`); `delivery_date` ที่ส่งมาจะแทนที่วันที่ขอของทุกบรรทัด ทำให้มิติวันที่ใน grouping key ยุบลง บรรทัดที่เดิมจะแยกตามวันที่จึงรวมเป็น PO เดียว หน้า React ยังไม่ส่ง override เหล่านี้ — ส่งแค่ `pr_ids`, `workflow_id`, `buyer_id`, `buyer_name` (`from-pr-content.tsx` `handleConfirm`) จากนั้น PO จะเป็นเอกสารที่ผู้ขายส่งของให้ และผู้รับสร้าง Good Receive Note กับ PO นั้น หมายเหตุ: ไม่มีฟีเจอร์บันทึก vendor-invoice / three-way-match (PO ↔ GRN ↔ invoice) อยู่ใน source ปัจจุบัน — การค้นหาทั่ว frontend และ backend สำหรับโค้ด invoice/AP-matching ไม่พบสิ่งใดเลย ให้ถือว่าข้อความอ้างอิงลักษณะนี้ในหน้าอื่นของโมดูลนี้ยังไม่ยืนยัน/เป็นเพียงแผน ไม่ใช่พฤติกรรมจริงที่ใช้งานอยู่

### 1.1 Endpoint surface (gateway `apps/backend-gateway/src/application/purchase-orders/purchase-orders.controller.ts`, Bruno `procurement/purchase-order/`)

| Verb + path (`/api/{bu_code}/purchase-orders…`) | จุดประสงค์ | Status guard (backend) |
|---|---|---|
| `GET /`, `GET /:id`, `GET /:id/details`, `GET /:id/details/:detail_id` | List / detail / บรรทัด detail response มี object ซ้อน `vendor`, `currency`, `buyer`, `workflow`, `credit_term` (`@ExpandRefs`, 2026-09-17) และต่อบรรทัดมี `location`, `delivery_point`, `pr_details[] { pr_detail, pr_id, pr_no, grn[] { grn_id, grn_no }, order_qty, received_qty, foc_qty, foc_received_qty }` | — |
| `GET /detail/:detail_id/history` | ประวัติการเปลี่ยนแปลงต่อบรรทัด (ทุกการ save และ stage action) **ใหม่นับจาก baseline** | — |
| `POST /`, `PUT /:id`, `PATCH /:id/save`, `DELETE /:id`, `DELETE /batch`, `DELETE /:id/details/:detail_id` | Create / update / save (role-aware: เฉพาะ save ของผู้สร้างเท่านั้นที่ส่งราคา) / delete | delete: `draft` + เจ้าของหรือ super-admin |
| `POST /verify` | Dry-run ของ `create` / `save` / `submit` — ประเมินทุกกฎ คืน `200` พร้อม `is_valid: false` และรายการปัญหาทั้งหมด **ใหม่นับจาก baseline** (`e3a6f0efb`, 2026-08-19) | — |
| `PATCH /:id/submit` | `draft → in_progress` (รับจาก `in_progress + last_action = reviewed` ด้วย) | ดูซ้าย |
| `PATCH /:id/approve`, `/reject`, `/review` | Stage action; approve ขั้นสุดท้าย → `approved`; reject → `voided`; review คง `in_progress` | `in_progress` |
| `POST /swipe-approve` | Batch-approve `{ po_ids[] }` — ทุกบรรทัดของแต่ละ PO ที่ stage ปัจจุบัน; success/failure ต่อ PO; ปฏิเสธสำหรับ `stage_role = purchase` หรือผู้ใช้ที่ไม่มีสิทธิ์ action **ใหม่นับจาก baseline** (`8e1319614`, 2026-08-13; mobile) | `in_progress` |
| `POST /:id/send-email` | ส่งอีเมล PO ถึงผู้ขายผ่าน BU email profile (`profile_id`, `to[]`, `cc[]`, `subject`, `body`, `attach_pdf`); PDF render ฝั่งเซิร์ฟเวอร์โดย micro-report (`exportPdfViaMicroReport` → FastReport `POST /api/Report/Export/Pdf`, `micro-report/service/render/viewer_client.go:133`); ทุกความพยายามถูก log ลง `tb_activity` (`email_sent`); สำเร็จแล้วย้าย `approved → sent_or_print` **ใหม่นับจาก baseline** (`1897b4fc1`, 2026-09-08) | `approved`, `sent_or_print`, `partial`, `closed`, `completed` (`EMAILABLE_PO_STATUSES`) |
| `POST /:id/mark-sent` | บันทึกการส่งนอกระบบ (พิมพ์ แฟกซ์ โทร); `tb_activity` "Marked as sent to vendor" **ใหม่นับจาก baseline** (`3969b8cf6`, 2026-09-14) ยังไม่มีปุ่มใน React — Bruno/API เท่านั้น | `approved` เท่านั้น |
| `POST /:id/cancel` | `→ closed` ทุกบรรทัด `cancelled_qty = order_qty − received_qty` | `draft`, `in_progress`, `approved`, `sent_or_print` |
| `POST /:id/close` | `→ closed` ส่วนที่เหลือเขียนลง `cancelled_qty` เมื่อ `> 0`; แจ้งเตือน buyer | `in_progress`, `approved`, `sent_or_print`, `partial` |
| `POST /group-pr`, `POST /confirm-pr` | PR→PO preview / create พร้อม override แบบ optional `delivery_date`, `delivery_point_id`, `note` | PR ต้นทาง `approved` |
| `GET /grn/vendor`, `GET /grn/vendor/:vendor_id`, `GET /grn`, `GET /grn/:id` | PO picker สำหรับสร้าง GRN พร้อม `can_use` ต่อ location (จาก `tb_location_user`, `c0b6d549f`) `GET /grn/:id` เป็น route PO **เพียงตัวเดียว** ที่มี `@Permission` ที่ gateway (`procurement.purchase_order: ['create']`) | `approved`, `sent_or_print`, `partial` |
| `GET /:id/print`, `GET /:id/print-viewer`, `GET /:id/export` | PDF, URL ของ FastReport viewer, Excel | — |
| `GET /workflow-stages`, `GET /:po_id/previous-stages` | lookup workflow stage สำหรับ dialog send-back | — |

route PO อื่น ๆ ทุกตัวระบุ `Permissions: None` ใน Bruno; แอป React ประกาศ `procurement.purchase_order` เป็น resource แบบ view-only และ `procurement.credit_note` เป็น CRUD ใน `constant/permissions.ts`

## 2. บริบททางธุรกิจ

PO คือจุดที่คำขอภายในกลายเป็นการผูกพันภายนอก ก่อนหน้านี้การใช้จ่ายเป็นเพียง soft commitment กับงบประมาณ การออก PO เปลี่ยนสิ่งนั้นให้กลายเป็น hard commitment พร้อมภาระผูกพันที่บังคับใช้ได้ตามกฎหมายต่อผู้ขายตามเงื่อนไขที่ตกลง การเปลี่ยนผ่านเพียงครั้งเดียวนี้คือสิ่งที่ทำให้ฝ่ายการเงินและจัดซื้อควบคุมการใช้จ่ายที่ควบคุมไม่ได้ได้: โดยการส่งทุกการผูกพันภายนอกผ่าน PO ที่มีเอกสารกำกับ พร้อมหมายเลขอ้างอิงที่ไม่ซ้ำ ผู้ขายที่อนุมัติแล้ว ราคา pricelist ที่ผ่านการ validate และ budget check องค์กรจึงป้องกันการสั่งซื้อนอกระบบและรับประกันว่าทุก invoice ในอนาคตจะมีการอนุมัติที่ตรงกัน

โมดูลนี้คือแกนกลางของการ integration ในห่วงโซ่ procure-to-pay PR ป้อนเข้ามาทางต้นน้ำพร้อมการจัดสรรผู้ขายและปริมาณที่อนุมัติ; PO ผูกพันปริมาณและราคาเหล่านั้นกับผู้ขาย; โมดูล GRN รับของกับ PO และตรวจสอบปริมาณที่สั่งเทียบกับที่รับ; โมดูล inventory เพิ่ม on-order ตอน PO ถูกส่ง และเพิ่ม on-hand ตอน GRN post; โมดูล vendor-pricelist จัดหาราคาต่อหน่วย Document management (attachments, comments, activity log) ให้ทุก PO มี audit trail ครบถ้วน — ใครสร้าง แก้ไขอะไร ส่งเมื่อไหร่ ใครรับของ ปิดเมื่อไหร่ **ยังไม่ยืนยัน (Unverified):** ไม่พบฟีเจอร์บันทึก vendor-invoice หรือ three-way-match (PO ↔ GRN ↔ invoice) ใน source ของ frontend หรือ backend ปัจจุบัน — ให้ถือว่าข้อความอ้างอิงเกี่ยวกับ AP/invoice-matching ในที่อื่นเป็นเพียงเจตนาการออกแบบ ไม่ใช่พฤติกรรมที่ implement แล้ว

ความถูกต้องทางการเงินถูกบังคับใช้ที่ชั้นการคำนวณ subtotal บรรทัด ส่วนลด net amount ภาษี และยอดรวม ถูกปัดเศษที่ระดับบรรทัดด้วย half-up (banker's) rounding โดยใช้ทศนิยม 3 ตำแหน่งสำหรับปริมาณ 2 ตำแหน่งสำหรับเงิน และ 5 ตำแหน่งสำหรับอัตราแลกเปลี่ยน; ยอดรวมส่วนหัว PO roll up จากค่าบรรทัดที่ปัดเศษแล้ว; PO ข้ามสกุลเงิน dual-post พร้อมการจัดการอัตราแลกเปลี่ยนที่ชัดเจน PO ต้องกระทบยอดกับ PR ต้นทางและ GRN และ invoice ที่เกิดขึ้นได้สะอาด ดังนั้นวินัยการปัดเศษเดียวกันจึงใช้ end-to-end ตลอดการคำนวณ procure-to-pay

## 3. แนวคิดสำคัญ

- **PO Header**: เร็คคอร์ดระดับ transaction ที่บรรจุผู้ขาย หมายเลขอ้างอิง วันที่สั่งและวันส่งของที่ต้องการ สกุลเงินและอัตราแลกเปลี่ยน จุดส่งของ (`delivery_point_id/name` บน `tb_purchase_order` ตั้งแต่ 2026-09-15 — ก่อนหน้านี้ delivery point เดียวใน PO tree อยู่บนสะพาน PR↔PO) เงื่อนไขการชำระเงินและการส่งของ สถานะ ยอดรวม และฟิลด์ audit ส่วนหัวผูกทุก line item เข้าด้วยกันเป็น commitment เดียวต่อผู้ขายรายเดียวในสกุลเงินเดียว
- **PO Line / PO Item**: บรรทัดบน PO ที่แสดงสินค้าเดี่ยว **สำหรับ delivery location เดียว** — สินค้าที่ไปสองร้านคือสองบรรทัด (`create-purchase-order.dto.ts`: `location_id` required ต่อบรรทัด; detail response มี object `location` / `delivery_point` บนแถว) บรรทัดบรรจุปริมาณที่สั่ง หน่วยนับ ราคาต่อหน่วย ส่วนลด อัตราภาษี ปริมาณ FOC (`foc_qty`) และ FOC ที่รับแล้ว (`foc_received_qty`) ยอดรวมบรรทัดที่คำนวณแล้ว และ traceability ผ่าน `pr_details[]` (แต่ละ entry ระบุ PR ต้นทาง `pr_id`/`pr_no`, บรรทัด PR, และ GRN ที่รับกับมัน) บรรทัดคือหน่วยของการรับของกับ GRN หน้าจอ detail แสดง label GRN ต่อบรรทัด, ปุ่ม "view source PR" ต่อบรรทัด, และ FOC ที่รับแล้วใต้คอลัมน์ FOC / GRN (`po-item-cells/pr-source-button.tsx`, `qty-cell.tsx`, 2026-09-21/22)
- **Approved vs Sent-or-Print**: `approved` หมายถึง workflow เสร็จสิ้น; `sent_or_print` หมายถึงผู้ขายได้รับเอกสารแล้ว ที่แยกกันเพราะของอาจมาถึงก่อนที่ใครจะส่งอีเมลหรือพิมพ์ใบสั่ง ดังนั้นการรับของจึงปลดล็อกที่ `approved` ในขณะที่สถานะการส่งยังบอกตามจริงว่าผู้ขายเห็นอะไรแล้ว
- **Delivery Terms**: Incoterm หรือ clause ที่เทียบเท่าซึ่งกำหนดว่ากรรมสิทธิ์จะส่งต่อที่ใด ใครจ่ายค่าขนส่งและประกัน และที่ใดที่หน้าที่ส่งของของผู้ขายสิ้นสุด (เช่น จุดส่งของ on-premise unloading) บรรจุบนส่วนหัวและใช้โดย receiving และ finance
- **Payment Terms**: เงื่อนไขเครดิตที่ตกลงกับผู้ขาย (เช่น net 30, 2/10 net 30, COD) มาจาก vendor master คัดลอกลงในส่วนหัว PO ตอนสร้าง และใช้โดย AP คำนวณวันครบกำหนดและช่วงส่วนลดบน invoice ที่เกิดขึ้น
- **Amendment**: การเปลี่ยนแปลงที่ควบคุมต่อ PO ที่ active — ราคา ปริมาณ วันส่งของ เงื่อนไข หรือเพิ่ม/ลบบรรทัด — บันทึกเป็นเหตุการณ์ที่ version แล้วใน activity log การ amendment ปรับ open commitment และ propagate ไปยังงบประมาณและ on-order ของ inventory; การ re-acknowledge ของผู้ขายมักจำเป็นสำหรับการเปลี่ยนแปลงที่สำคัญ
- **Open vs Closed PO**: PO **open** มีปริมาณที่เหลือต้องรับหรือยังไม่ถูกปิดในเชิงบริหาร PO **closed** ถูก finalise — รับครบและปิด หรือ short-close พร้อมปล่อย commitment ที่เหลือ Closed PO ไม่รับ GRN เพิ่มและกลายเป็น read-only ยกเว้นสำหรับ reporting และ audit
- **Voided PO**: ผลลัพธ์แบบสิ้นสุด (terminal) เมื่อผู้อนุมัติ reject PO ขณะที่ยังอยู่ในสถานะ `in_progress` (ผ่าน endpoint `/reject`) — การเปลี่ยนสถานะเป็นแบบตรง (`in_progress → voided`) โดยไม่มีการย้อนกลับไป `draft` ระหว่างทาง ไม่มี action "void" แยกต่างหากที่ทำด้วยมือซึ่งเข้าถึงได้จาก `draft`, `approved`, `sent_or_print`, หรือ `partial`: การจบ PO จากสถานะเหล่านั้นใช้ **Cancel** (`draft`/`in_progress`/`approved`/`sent_or_print`) หรือ **Close** (`in_progress`/`approved`/`sent_or_print`/`partial`) แทน ซึ่งทั้งคู่ลงเอยที่ `closed` (โดยยอดคงเหลือถูกเขียนลงใน `cancelled_qty`) ไม่ใช่ `voided`
- **Vendor + Delivery Date + Currency Grouping**: กฎที่แบ่ง PR ที่เลือกชุดหนึ่งออกเป็น PO หนึ่งใบต่อแต่ละ combination `(vendor, delivery_date, currency)` ที่ไม่ซ้ำ ระหว่างการแปลง PR-to-PO รับประกันว่า PO แต่ละใบเป็น single-vendor และ single-currency รวมบรรทัด PR ที่มีสิทธิ์และมีวันส่งของเดียวกันเข้าไปใน PO เดียว และรักษาแนวปฏิบัติ procurement ให้สะอาด
- **PR-to-PO Traceability**: ลิงก์ถาวรจาก PO line แต่ละบรรทัดกลับไปยัง PR line ต้นทาง (`prItemId`, `prNumber`) รักษาไว้ผ่าน amendments และ partial receipts เพื่อให้ผู้ตรวจสอบและผู้ปฏิบัติงานสามารถ trace สินค้าที่รับใด ๆ กลับไปยังความต้องการที่ขอได้
- **FOC (Free of Charge)**: ฟิลด์ระดับบรรทัดสำหรับสินค้าที่ผู้ขายให้มาในราคา 0 (ตัวอย่าง, โบนัสส่งเสริมการขาย) ปริมาณ FOC ไม่รวมใน subtotal ของ PO แต่ flow ผ่านไปยัง GRN เพื่อให้ฝั่งรับสินค้าบันทึกเข้าคลัง
- **Exchange Rate**: อัตราแปลงที่ capture บนส่วนหัว PO ตอนสร้าง ใช้ dual-post ยอดรวม PO ในสกุลเงินฐาน Lock ไว้บน PO เพื่อให้ commitment และ receipt และ invoice ที่เกิดขึ้นกระทบยอดกับฐานที่เสถียร

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| Procurement Officer / Purchaser | สร้าง PO ด้วยมือ โดยการแปลง PR ที่อนุมัติแล้ว หรือจาก vendor price list; ตรวจสอบการจัดสรรผู้ขายและราคา pricelist; ตั้งเงื่อนไขการส่งของและการชำระเงิน; ส่งเข้าสู่ workflow การอนุมัติ; เมื่อ PO เป็น `approved` แล้ว ส่งให้ผู้ขายทางอีเมล (ปุ่ม **Send Email**, `po-send-email-dialog.tsx`) — ซึ่งเป็นสิ่งที่ย้ายมันไป `sent_or_print` — และบริหารการติดตามผล |
| Procurement Manager | ทำหน้าที่เป็นผู้อนุมัติในขั้นตอน workflow ที่กำหนดไว้ (ใช้กลไก approve / send-back / reject แบบ stage-based ทั่วไปเหมือนผู้อนุมัติรายอื่น) **ยืนยันแล้วในรอบนี้:** `routing_rules` ของ workflow ที่ assign ให้ (ตั้งค่าได้จากแท็บ **Routing** ทั่วไปใน `/system-admin/workflow`) สามารถ auto-route stage ถัดไปตาม `total_amount` ได้ — เป็นทางเลือกการตั้งค่าต่อ workflow ไม่ใช่กลไกเฉพาะของ Procurement Manager; ไม่มี field routing ตาม pricelist-deviation-percentage (ดู `02-business-rules.md` `PO_AUTH_004`) delete-in-draft **ไม่ใช่** สิทธิ์ของ Manager — `remove()` อนุญาตเฉพาะเจ้าของเอกสารหรือ platform super-admin เท่านั้น |
| Vendor | ฝ่ายภายนอกที่รับ PO (อีเมลพร้อม PDF แบบ optional หรือการพิมพ์/แฟกซ์นอกระบบที่บันทึกผ่าน `mark-sent`) และส่งของตามเงื่อนไขที่ตกลงกัน ปัจจุบันยังไม่พบฟีเจอร์การตอบรับในระบบหรือการจับคู่ invoice ที่ยืนยันได้ |
| Receiver / Store Keeper | บทบาทปลายน้ำที่รับสินค้าจริงและสร้าง GRN กับ PO ทีละบรรทัด GRN สร้างได้จาก `approved`, `sent_or_print`, หรือ `partial`; การ post GRN เพิ่มค่า `received_qty` บนบรรทัด PO (และ `foc_received_qty` บนแถวสะพาน) และขับเคลื่อนการเปลี่ยนสถานะ `→ partial → completed`; on-hand ของ inventory จะถูกเพิ่มโดยโมดูล GRN / inventory ไม่ใช่โดย PO |
| Inventory Manager | บริหารการรับสินค้าสำหรับ location กำกับดูแลการสร้าง GRN และปิด PO เมื่อรับของครบหรือยอมรับเป็นการสิ้นสุด |
| Finance | ถูกระบุไว้ในเอกสารออกแบบรุ่นเก่าว่าเป็นผู้อนุมัติก่อนส่งและเจ้าของขั้นตอน three-way-match / AP-posting หลังรับของ **ยังไม่ยืนยัน:** ไม่พบ `stage_role` ชื่อ "finance" แยกต่างหาก หน้าจอบันทึก invoice หรือโค้ด AP-matching ใด ๆ; หลักฐานผู้อนุมัติเพียงรายเดียวใน e2e fixtures ปัจจุบัน (`fc@blueledgers.com`) ถูกบันทึกไว้ในที่อื่นว่าเป็น actor ขั้นตอน approve ทั่วไปแบบเดียวกับ Procurement Manager |
| System Administrator | ตั้งค่าการเรียงเลข PO (ผ่านหน้าจอ running-code ทั่วไป) นิยามขั้นตอน workflow และกฎ routing ตาม amount/department/category (ผ่านแท็บ **Routing** ทั่วไปใน `/system-admin/workflow` ใช้ร่วมกันระหว่าง PR/PO/SR — ไม่ใช่หน้าจอเฉพาะของ PO) และ RBAC ไม่พบ configuration workbench เฉพาะของ PO (การจัดอันดับผู้ขาย, ตัวแก้ไขกฎ conversion-grouping, ช่วง pricelist-tolerance) ใน source ปัจจุบัน — ให้ถือว่ายังไม่ยืนยัน |
| Auditor | สิทธิ์ read-only ต่อ PO, amendments และ activity log เพื่อตรวจสอบความสอดคล้องของนโยบาย segregation of duties และ traceability จาก PR ผ่าน PO ไปยัง GRN |

## 5. โมดูลที่เกี่ยวข้อง

**การไหลข้ามโมดูล:**
- [purchase-request](/th/inventory/purchase-request) — PO สร้างจาก PR ที่อนุมัติแล้ว
- [good-receive-note](/th/inventory/good-receive-note) — GRN ถูกสร้างกับ PO เมื่อรับของ
- [vendor-pricelist](/th/inventory/vendor-pricelist) — ราคา PO ถูก validate กับ vendor pricelist
- [product](/th/inventory/product) — บรรทัด PO อ้างอิงสินค้าจากแคตตาล็อก

**Master configuration:**
- [master-data/vendor](/th/inventory/master-data/vendor) — vendor master (header + addresses + contacts) ที่ส่วนหัว PO อ้างอิง
- [master-data/currency](/th/inventory/master-data/currency) — สกุลเงินและอัตราแลกเปลี่ยนสำหรับ PO หลายสกุลเงิน
- [master-data/tax-profile](/th/inventory/master-data/tax-profile) — รหัสภาษีที่ใช้กับบรรทัด PO
- [master-data/credit-term](/th/inventory/master-data/credit-term) — เงื่อนไขการชำระเงินที่คัดลอกจาก vendor master ลงในส่วนหัว PO
- [master-data/delivery-point](/th/inventory/master-data/delivery-point) — จุดส่งของที่ตกลงกันสำหรับ commitment (`tb_purchase_order.delivery_point_id` บน header ตั้งแต่ 2026-09-15; `delivery_point_id` ต่อบรรทัดบนสะพาน PR↔PO)
- [master-data/location](/th/inventory/master-data/location) — PO line หนึ่งบรรทัดคือ delivery location เดียว; `can_use` บน GRN picker มาจาก `tb_location_user`
- [system-config/config-email](/th/inventory/system-config/config-email) — BU email profile ที่ `POST .../purchase-orders/:id/send-email` ใช้; email template ของ PO/RFP seed ต่อ BU (`ccc72e78b`, 2026-09-16)
- [master-data/unit](/th/inventory/master-data/unit) — หน่วยนับสำหรับปริมาณบรรทัด PO
- [system-config/workflow](/th/inventory/system-config/workflow) — นิยาม workflow อนุมัติสำหรับการอนุญาต PO และ amendments
- [system-config/running-code](/th/inventory/system-config/running-code) — การเรียงลำดับเลขเอกสาร PO
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — log การเปลี่ยนสถานะ PO และการ amendment สำหรับ audit
- [reporting-audit/attachment](/th/inventory/reporting-audit/attachment) — vendor acknowledgements และเอกสาร contract ที่แนบกับ PO

## 6. แหล่งอ้างอิง

- Concepts: `../carmen/docs/purchase-order-management/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. หน้าในโมดูลนี้

- [01 — โมเดลข้อมูล](/th/inventory/purchase-order/01-data-model) — เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum (อิงจาก Prisma)
- [01a — โมเดลข้อมูล — ตารางคอมเมนต์](/th/inventory/purchase-order/01a-data-model-comments) — ตารางคอมเมนต์ / ไฟล์แนบระดับเอกสารและระดับบรรทัด พร้อมการแยก user/system ผ่าน `enum_comment_type`
- [02 — กติกาทางธุรกิจ](/th/inventory/purchase-order/02-business-rules) — การตรวจสอบความถูกต้อง การคำนวณ การกำหนดสิทธิ์ การ posting และกฎข้ามโมดูล
- [03 — User Flow](/th/inventory/purchase-order/03-user-flow) — วงจรชีวิตของเอกสารและสารบัญ persona
  - [Purchaser](/th/inventory/purchase-order/03-user-flow-purchaser)
  - [Procurement Manager](/th/inventory/purchase-order/03-user-flow-procurement-manager)
  - [Vendor](/th/inventory/purchase-order/03-user-flow-vendor)
  - [Receiver](/th/inventory/purchase-order/03-user-flow-receiver)
  - [Finance](/th/inventory/purchase-order/03-user-flow-finance)
  - [Audit / Config](/th/inventory/purchase-order/03-user-flow-audit-config)
- [04 — Test Scenarios](/th/inventory/purchase-order/04-test-scenarios) — ขอบเขตของแต่ละ persona, scenario ข้าม persona และ E2E mapping
  - [Purchaser](/th/inventory/purchase-order/04-test-scenarios-purchaser)
  - [Procurement Manager](/th/inventory/purchase-order/04-test-scenarios-procurement-manager)
  - [Vendor](/th/inventory/purchase-order/04-test-scenarios-vendor)
  - [Receiver](/th/inventory/purchase-order/04-test-scenarios-receiver)
  - [Finance](/th/inventory/purchase-order/04-test-scenarios-finance)
  - [Audit / Config](/th/inventory/purchase-order/04-test-scenarios-audit-config)
- [Credit Note](/th/inventory/purchase-order/credit-note) — เอกสาร credit ที่ผู้ขายออกเพื่อคืนมูลค่าทั้งหมดหรือบางส่วนของ PO / GRN ก่อนหน้า
