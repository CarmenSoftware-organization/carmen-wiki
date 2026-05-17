---
title: รายการราคาผู้ขาย — User Flow (Vendor Pricelist — User Flow)
description: Lifecycle ของเอกสารและไฟล์ flow ตาม persona สำหรับ vendor-pricelist
published: true
date: 2026-05-17T12:00:00.000Z
tags: vendor-pricelist, user-flow, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย — User Flow (Vendor Pricelist — User Flow)

> **At a Glance**
> **โมดูล:** [[vendor-pricelist]] &nbsp;·&nbsp; **Persona:** Purchaser (+ Purchasing Manager) &nbsp;·&nbsp; Vendor &nbsp;·&nbsp; Finance &nbsp;·&nbsp; Audit / Config
> **Workflow lifecycle:** Template (draft → active → inactive) &nbsp;·&nbsp; Campaign (draft → active → completed / cancelled) &nbsp;·&nbsp; Invitation (pending → in-progress → submitted → approved / expired) &nbsp;·&nbsp; Pricelist (draft → submitted → active / inactive / expired)
> **Drill เข้า view ต่อ persona ด้านล่างสำหรับรายละเอียดระดับ action**

## 1. ภาพรวม

หน้านี้เป็น **จุดเข้า overview** สำหรับชุด user-flow ของโมดูล `vendor-pricelist` Vendor pricelist คือ artefact ที่ vendor submit (`tb_pricelist` header + แถว `tb_pricelist_detail`) ที่ผลิตผ่านกระบวนการเก็บข้อมูล 6-phase: **vendor setup**, **การสร้าง template** (`tb_pricelist_template`), **การวางแผน campaign / request-for-pricing** (`tb_request_for_pricing`), **vendor invitation** (`tb_request_for_pricing_detail` carry `pricelist_url_token` cryptographic), **secure portal submission** (online entry / Excel upload / email) และ **validation + approval** Lifecycle ใน Section 2 ครอบคลุมสาม enum สถานะ — `enum_pricelist_template_status` สำหรับ template, สถานะที่ derive ระดับแอปสำหรับ campaign และ invitation และ `enum_pricelist_status` สำหรับ pricelist ของ vendor — จาก draft template เริ่มต้นผ่านการ launch campaign, draft และ submission ของ vendor, การ review ของ purchaser และการ approve ไปยัง `active` พร้อมสาขา auto-expiry, rejection และ inactivation Persona ที่เกี่ยวข้องคือ **Purchaser** (และ Purchasing Manager — รวบที่ persona file เดียวกัน: สร้าง template, รัน campaign, ส่ง invitation, review และ approve pricelist ที่ submit, จัดการ flag preferred-vendor, upload manually การ submission ที่ email และใช้ high-value sign-off เป็น Manager), **Vendor** (external party ที่ไม่มี Carmen login — เข้าถึง portal ผ่าน token, submit ราคา), ทีม **Finance** (Finance Officer + Finance Manager — audit variance ราคา, validate สกุลเงิน/FX, sign off pricelist multi-currency) และ role **Audit / Config** (Auditor สำหรับการ review อ่านอย่างเดียวข้าม pricelist / campaign / invitation / submission / validation / activity-log, System Administrator สำหรับการกำหนดเลข, RBAC, นโยบาย portal-token, การเชื่อม email, กติกา validation และการเก็บ audit) Receiver / Store Keeper เป็น **ผู้บริโภคทางอ้อม** ผ่าน price-variance ของ GRN — ปรากฏใน scenario ข้าม persona แต่ไม่มี persona file ของตนเอง แคตตาล็อก role เองนิยามใน [index.md](./index.md) Section 4

Section 2 ด้านล่างคือ **state machine ทั่วโลก** — รายการ canonical ของการเปลี่ยนข้ามทั้งสาม lifecycle, อิสระจากผู้กระทำ แต่ละไฟล์ต่อ persona (link จาก Section 3) อธิบาย *เส้นทางผ่าน* state machine ของ persona นั้น — จุดเข้า, action ที่มี, สาขาการตัดสินใจที่เผชิญ และ handoff ที่จบการมีส่วนร่วม Section 4 จากนั้นสรุป handoff ข้าม persona ที่เย็บเส้นทางรายตัวเข้าด้วยกัน อ่าน overview นี้ก่อนเพื่อ anchor lifecycle จากนั้น drill เข้าไฟล์ persona ที่ตรงกับ role ของคุณ

## 2. Lifecycle ของเอกสาร

โมดูลมีสาม surface สถานะ Status template เก็บบน `tb_pricelist_template.status` (`draft`, `active`, `inactive`) Status pricelist เก็บบน `tb_pricelist.status` (`draft`, `active`, `inactive`, `expired`) Campaign และ invitation status **ไม่ใช่คอลัมน์ Prisma** — derive โดยแอปจาก `tb_request_for_pricing.start_date` / `end_date`, `submitted_at` และ `status` ของ pricelist ที่ link และ flag JSON `info` (ดู [02-business-rules.md](./02-business-rules.md) § 5.2 และ § 5.3 สำหรับกติกาการ derive แบบเต็ม)

### 2.1 Template lifecycle

| จาก state | Action | ไป state | อนุญาตสำหรับ | Pre-condition |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | create | `draft` | Purchaser | ฟิลด์ header validate (`name` unique ตาม `VPL_VAL_001`, default `currency_id`, `validity_period` ถ้าตั้ง) |
| `draft` | save (edit) | `draft` | Purchaser (เจ้าของ / role procurement-team) | แถว detail สามารถเพิ่ม / แก้ได้อิสระ; structure `MOQ tier` validate ตาม `VPL_VAL_006` |
| `draft` | activate | `active` | Purchaser | มีแถว detail อย่างน้อยหนึ่ง (`VPL_VAL_002`); การอ้างอิงสินค้าถูกต้อง; schedule reminder ถูกต้อง |
| `active` | inactivate | `inactive` | Purchaser, System Administrator | ไม่สามารถ inactivate ขณะ campaign ที่อ้างอิง template in-flight |
| `inactive` | re-activate | `active` | Purchaser | สินค้าและสกุลเงินที่อ้างอิงต้องยัง active |
| `draft` | soft-delete | `(none)` | Purchaser | อนุญาตเฉพาะที่ `draft`; unique index รวม `deleted_at` เพื่ออนุญาตการใช้ชื่อซ้ำ |

### 2.2 Campaign (request-for-pricing) lifecycle — แอป-derived

| จาก state | Action | ไป state | อนุญาตสำหรับ | Pre-condition |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | create | `draft` | Purchaser | ฟิลด์ header validate (`name` unique ตาม `VPL_VAL_008`, `pricelist_template_id` อ้างอิง template `active` ตาม `VPL_VAL_009`) |
| `draft` | edit / add vendors | `draft` | Purchaser | แถว invitation (`tb_request_for_pricing_detail`) เพิ่มได้ตาม `VPL_VAL_011`–`VPL_VAL_012` |
| `draft` | launch | `active` | Purchaser | `start_date < end_date` ตาม `VPL_VAL_010`; มีแถว invitation อย่างน้อยหนึ่ง; email template ถูกต้อง (`VPL_VAL_013`) ตอน launch อีเมล invitation dispatch และ `pricelist_url_token` materialise ต่อแถว |
| `active` | pause | `paused` | Purchaser, Purchasing Manager | ระงับ reminder และล็อก invitation ใหม่; portal token ที่มีอยู่ยังถูกต้อง Flag แอปใน JSON `info` |
| `paused` | resume | `active` | Purchaser, Purchasing Manager | clear flag `paused`; reminder resume |
| `active` | (auto) complete | `completed` | — | Trigger เมื่อ `now() >= end_date` OR ทุกแถว detail มี `tb_pricelist.status = active` ที่ link |
| `active` | cancel | `cancelled` | Purchaser, Purchasing Manager, System Administrator | Flag แอปใน JSON `info` พร้อม `system` comment เหตุผลใน `tb_request_for_pricing_comment` portal token ทั้งหมดถูก revoke; vendor ได้รับแจ้ง |

### 2.3 Invitation lifecycle — แอป-derived

| จาก state | Action | ไป state | อนุญาตสำหรับ | Pre-condition |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | invite | `pending` | Purchaser (campaign launch) | แถว invitation insert ใน `tb_request_for_pricing_detail`; `pricelist_url_token` materialise; email dispatch |
| `pending` | first portal access | `in-progress` | Vendor (token-authenticated) | `system` comment first-access บันทึกใน `tb_request_for_pricing_detail_comment`; auto-save เริ่มตอน save ครั้งแรก |
| `in-progress` | submit pricelist | `submitted` | Vendor | Vendor คลิก Submit ที่ portal; `tb_pricelist.submitted_at` เขียน; purchaser ถูกแจ้ง |
| `submitted` | approve pricelist | `approved` | Purchaser (หรือ Manager / Finance Manager สำหรับ high-value / multi-currency) | Trigger โดย `tb_pricelist.status = active` Invitation lifecycle terminate ที่นี่ |
| `submitted` | reject pricelist | `in-progress` | Purchaser (หรือ Manager) | Vendor ได้รับ email + token ต้นฉบับ; สามารถ resubmit ผ่าน portal เดียวกันจนกว่าจะหมดอายุ |
| `pending` / `in-progress` | (auto) expire | `expired` | — | Campaign `end_date < now()` และไม่มีการ submission Token ถูก revoke อัตโนมัติ |

### 2.4 Pricelist lifecycle (`enum_pricelist_status`)

| จาก state | Action | ไป state | อนุญาตสำหรับ | Pre-condition |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | vendor บันทึกครั้งแรก | `draft` | Vendor (token-authenticated) | Header pricelist insert ผ่าน portal; FK บนแถว invitation populate; auto-save engage |
| `draft` | save (edit) | `draft` | Vendor (token-authenticated) | การแก้ online / upload Excel / รับ email; structure `MOQ tier` validate ตาม `VPL_VAL_018`–`VPL_VAL_022` |
| `draft` | submit | `draft` (พร้อม `submitted_at` เขียน) | Vendor | Vendor คลิก Submit; validator รัน `VPL_VAL_023`; quality score คำนวณ; purchaser ถูกแจ้งสำหรับ review |
| `draft` (submitted) | approve | `active` | Purchaser (`VPL_AUTH_004`) หรือ Purchasing Manager / Finance Manager (`VPL_AUTH_005` / `VPL_AUTH_010`) สำหรับ high-value / multi-currency | Quality score และผล validate ผ่านขีดจำกัด; flag preferred-vendor ตั้งตาม business rule |
| `draft` (submitted) | reject | `draft` (พร้อม `submitted_at` reset) | Purchaser, Purchasing Manager (`VPL_AUTH_006`) | ต้องการข้อความเหตุผล; vendor email สำหรับ resubmission |
| `active` | inactivate | `inactive` | Purchaser, System Administrator | PR / PO / GRN ปลายน้ำปฏิบัติกับ pricelist เป็น historical-only จากจุดนี้ |
| `inactive` | re-activate | `active` | Purchaser | อนุญาตภายใน validity window เท่านั้น |
| `active` | (auto) expire | `expired` | — | Cron: `now() > effective_to_date` AND `status = active` |
| `draft` | soft-delete | `(none)` | Purchaser | อนุญาตเฉพาะที่ `draft` (ก่อน approve); unique index รวม `deleted_at` เพื่ออนุญาตการใช้ reference number ซ้ำ |

## 3. Index ของ Persona

แต่ละ persona ด้านล่างมีไฟล์ drill-down dedicated อธิบายจุดเข้า, primary flow, สาขาการตัดสินใจ และจุดออก Slug ตรงกับ role ของ persona; คลิก link เปิด view ต่อ persona

- [Purchaser](./03-user-flow-purchaser.md) — Purchaser / Purchasing Staff + Purchasing Manager (รวบ) สร้าง template, รัน campaign, ส่ง invitation, review และ approve pricelist ที่ submit, จัดการการแก้ price-item รายตัวและ flag preferred-vendor, upload manually การ submission ที่ email ของ vendor Manager ใช้สิทธิ์ high-value approval, การตั้งค่า business-rule และ sign-off multi-currency
- [Vendor](./03-user-flow-vendor.md) — External party ที่ไม่มี Carmen system login ได้รับ invitation, เข้าถึง portal ผ่าน `pricelist_url_token`, ให้ราคา (online / Excel / email), เลือกสกุลเงิน, จัด MOQ tier พร้อมหน่วยและ conversion factor, บันทึก draft และ resubmit หลังการ reject
- [Finance](./03-user-flow-finance.md) — Finance Officer / AP audit variance ราคาเทียบกับ GRN / invoice ที่ post; Finance Manager review รายงาน variance, validate สกุลเงิน / FX, sign off pricelist multi-currency ไม่มี surface เขียนบน pricelist เอง; อ่าน pricelist + post ข้อค้นพบ variance ไปยังโมดูล AP
- [Audit / Config](./03-user-flow-audit-config.md) — Auditor อ่าน pricelist / campaign / invitation / submission / ผล validate / activity-log ข้าม chain; System Administrator ตั้งค่าการกำหนดเลข pricelist, RBAC, การตั้งค่า template / campaign, นโยบาย portal token (การหมดอายุ, IP restriction, session limit), การเชื่อม email, กติกา validation, การ revoke token และการเก็บ audit

โน้ต: **Receiver / Store Keeper** ระบุเป็น "ผู้บริโภคทางอ้อม" ใน [index.md](./index.md) Section 4 — การ post GRN อ่าน pricelist active สำหรับการคำนวณ variance แต่ persona ไม่มี surface เขียนบนโมดูล pricelist เอง พฤติกรรม Receiver จับใน scenario ข้าม persona (Section 4 ด้านล่างและใน [04-test-scenarios.md](./04-test-scenarios.md)) แทน persona file dedicated

## 4. Handoff ข้าม Persona

ตารางด้านล่างจับช่วงเวลาที่ความรับผิดชอบของ pricelist ย้ายจาก persona หนึ่งไปยังอีก persona แต่ละ handoff anchor กับสถานะเอกสารที่จุดถ่ายโอน

| จาก persona | Trigger | ไป persona | สถานะเอกสารที่ handoff |
| ------------ | ------- | ---------- | ------------------------- |
| Purchaser | Activate template | Purchaser (persona เดียวกัน, surface ต่าง — ตอนนี้ใช้ได้เป็นแหล่ง campaign) | Template `active` |
| Purchaser | Launch campaign (dispatch invitation email) | Vendor | Invitation `pending` (token materialise; vendor ได้รับ email) |
| Vendor | First portal access | Vendor (ต่อ) | Invitation `in-progress`; pricelist `(none)` จนกว่าจะบันทึกครั้งแรก |
| Vendor | First save ที่ portal | Vendor (ต่อ) | Pricelist `draft`; invitation `in-progress` |
| Vendor | Submit pricelist | Purchaser | Pricelist `draft` พร้อม `submitted_at IS NOT NULL`; invitation `submitted` |
| Purchaser | Approve pricelist (ต่ำกว่าขีดจำกัด high-value) | (terminal — pricelist live) | Pricelist `active`; invitation `approved` |
| Purchaser | Approve pricelist high-value | Purchasing Manager (role Manager บน persona file เดียวกัน) | Pricelist `draft` พร้อม `submitted_at`; invitation `submitted` (queue Manager) |
| Purchasing Manager | Approve pricelist high-value | (terminal — pricelist live) | Pricelist `active`; invitation `approved` |
| Purchasing Manager | ต้องการ co-approval สำหรับ multi-currency | Finance Manager | Pricelist `draft` พร้อม `submitted_at`; invitation `submitted` (queue Finance Manager) |
| Finance Manager | Sign off บน pricelist multi-currency | Purchaser / Manager (return สำหรับการ activate) | Pricelist `draft` พร้อม `submitted_at`; การ activate ดำเนินการเมื่อได้รับ sign-off |
| Purchaser / Manager | Reject pricelist | Vendor | Pricelist `draft` พร้อม `submitted_at` reset; invitation `in-progress`; vendor ได้รับ email reject |
| Purchaser | Upload manually email pricelist | (ต่อ) | Pricelist `draft` พร้อม `submission_method = email`; ไหลเข้าเส้นทาง approve มาตรฐาน |
| (cron) | Pricelist auto-expire | (terminal — historical) | Pricelist `expired`; ไม่มี reference live ปลายน้ำ |
| (cron) | Invitation auto-expire | Auditor (review post-hoc เท่านั้น) | Invitation `expired`; token revoke |
| Purchaser / Manager / System Administrator | Cancel campaign | Vendor ที่เชิญทั้งหมด (แจ้งทาง email) | Campaign `cancelled`; token ทั้งหมด revoke |
| Finance Officer | ข้อค้นพบ variance ที่ GRN | Purchaser (สำหรับ resolution) | Pricelist `active` (ไม่เปลี่ยน); entry variance log เทียบกับ vendor / pricelist สำหรับ analytics |
| System Administrator | Revoke portal token | Vendor (สูญเสียการเข้า portal) | Invitation `expired` (มีผลทันที); การเข้า portal ตามมา return `401` |
| System Administrator | Save การเปลี่ยนตั้งค่า validation-rule / RBAC / token-policy | (ไปข้างหน้าในเวลา) | Pricelist / campaign ที่มีอยู่คงตั้งค่าที่ snapshot; pricelist / campaign ใหม่ใช้ตั้งค่าใหม่ |
| Auditor | ข้อค้นพบ audit flag (อ่านอย่างเดียว) | เจ้าของธุรกิจที่รับผิดชอบ (Purchaser, Manager, Finance หรือ Sysadmin) สำหรับ remediation นอกแบนด์ | ไม่มีการเปลี่ยนสถานะ pricelist — Auditor ออกผ่านรายงาน; remediation ทำโดย persona ธุรกรรมภายใต้สิทธิ์ของตน |

## 5. แหล่งอ้างอิง

- `../carmen/docs/vendor-pricelist-management/design.md` — แหล่ง carmen/docs หลักสำหรับสถาปัตยกรรม 6-phase และ workflow diagram ที่อ้างอิงใน Section 2
- `../carmen/docs/vendor-pricelist-management/requirements.md` — functional requirement ขับ surface area ของแต่ละ persona
- `../carmen/docs/vendor-pricelist-management/price-assignment-workflow-documentation.md` — เอกสาร business-rule-engine ที่อยู่ใต้ handoff ข้าม persona ของ preferred-vendor และ price-assignment
- `../carmen/docs/vendor-pricelist-management/VENDOR_PORTAL_ENHANCEMENT_SUMMARY.md` — feature vendor portal เบื้องหลัง surface หลักของ persona Vendor
- Sibling: [01-data-model.md](./01-data-model.md) — การอ้างอิงเอนทิตี / enum canonical สำหรับ lifecycle ใน Section 2
- Sibling: [02-business-rules.md](./02-business-rules.md) — กติกา validation, calculation, authorization, posting (การเปลี่ยนสถานะ) และข้ามโมดูลที่อ้างอิงโดยแต่ละแถว Section 2 และแต่ละ handoff ใน Section 4
- โมดูลที่เกี่ยวข้อง: [[purchase-request]] (PR default ราคาจาก pricelist active), [[purchase-order]] (PO snapshot ราคา pricelist + ติดตาม deviation), [[good-receive-note]] (GRN price-variance check), [[product]] (entry pricelist อ้างอิงสินค้า)
