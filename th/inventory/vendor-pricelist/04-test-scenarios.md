---
title: รายการราคาผู้ขาย (Vendor Pricelist) — Test Scenarios
description: Test case ตาม persona, scenario ข้าม persona และ E2E mapping สำหรับ vendor-pricelist
published: true
date: 2026-05-17T12:00:00.000Z
tags: vendor-pricelist, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — Test Scenarios

> **At a Glance**
> **โมดูล:** [[vendor-pricelist]] &nbsp;·&nbsp; **Scenario รวม:** ~12 ข้าม persona + drill-down ต่อ persona ข้ามทุก persona &nbsp;·&nbsp; **Persona ครอบคลุม:** Purchaser, Vendor, Finance, Audit / Config
> **ลำดับการรัน:** การตั้งค่า Audit / Config → happy path persona หลัก → scenario ข้าม persona
> **Drill-down ของแต่ละ persona คือ `04-test-scenarios-<role>.md`**

## 1. ภาพรวม

หน้านี้เป็น **จุดเข้า overview** สำหรับชุด test-scenario ของโมดูล `vendor-pricelist` Lifecycle ของ pricelist ครอบคลุมสี่ persona — Purchaser (รวบ Purchasing Staff + Purchasing Manager), Vendor (external), Finance (Officer + Manager) และ Audit / Config (Auditor + System Administrator) — และ test coverage แยกตามนั้น: แต่ละ persona มีไฟล์ dedicated (link ใน Section 3) ที่แจกแจง scenario functional, authorization (เมื่อมีผลใช้), validation, edge และ golden-journey ของ persona นั้น ไฟล์ overview นี้ให้ภาพรวม: ใครอยู่ใน scope, สิ่งที่ test ของแต่ละ persona ครอบคลุมที่ระดับ headline, scenario handoff ข้าม persona ที่เย็บการเดินทางรายตัวเป็น flow end-to-end สมบูรณ์ และ mapping จากแต่ละ scenario กลับไปยัง test E2E / API / integration ที่ exercise มัน

Scope ของการ test บนโมดูล vendor-pricelist ครอบคลุมสี่พื้นที่กว้าง: **coverage functional** ของทุก action ข้ามสาม tier (template create / edit / activate, campaign launch / pause / cancel, vendor portal entry / submit / resubmit, pricelist review / approve / reject / inactivate), **RBAC / authorization** ของใครสามารถดำเนินการแต่ละ action (Purchaser create / edit / approve, Manager high-value approval, Vendor portal access ผ่าน token, Finance Manager multi-currency co-signoff, Sysadmin configuration + token revocation, Auditor read-only across the chain), **edge case** รอบกรณีขอบเขต MOQ-tier, การจัดการ multi-currency, vendor session พร้อมกัน, race การหมดอายุและ revoke token, optimistic-concurrency บนแถว pricelist และ registry กติกา-validation และ **พฤติกรรม three-way-match ปลายน้ำ** ที่การ post GRN / invoice เทียบกับ pricelist active (handoff กลับไปยัง Finance และ Purchaser ตาม [[purchase-order/02-business-rules]] § `PO_POST_008` / `PO_POST_009`)

## 2. Persona ใน Scope

- **Purchaser** — สร้าง template, รัน campaign (request-for-pricing), ส่ง invitation, review pricelist ที่ submit, approve / reject, จัดการ flag preferred-vendor, upload manually submission ที่ email scenario ของ Purchasing Manager บนไฟล์เดียวกันขยายด้วย high-value approval, การ toggle การตั้งค่า business-rule และ sign-off multi-currency เป็นเจ้าของ ~24+ scenario ข้าม template, campaign, pricelist review, golden journey
- **Vendor** — External party Portal session ที่ authenticate ด้วย token เป็น surface **เดียว** ใน-ระบบสำหรับ external party ในโมดูลนี้ ขับ state ผ่านการเขียน `tb_pricelist.submitted_at` และการ insert `(none) → draft` implicit เป็นเจ้าของ scenario happy-path และ validation; section Permission / Authorization ลดลงเป็นแถว N/A เดียวเพราะ vendor ไม่มี Carmen login (นโยบาย portal-token เองถูก test เป็นข้อกังวลการตั้งค่าฝั่ง Sysadmin)
- **Finance** — อ่านอย่างเดียวบน pricelist เอง (`VPL_AUTH_009`); เขียนเฉพาะผ่าน comment และผ่าน `system` co-signoff comment ของ Finance Manager สำหรับ pricelist multi-currency / high-value การสืบสวน variance ขับ scenario ส่วนใหญ่; coverage three-way-match ปลายน้ำอยู่ใน scenario Finance ของโมดูล [[purchase-order]] และอ้างอิงผ่าน handoff ข้าม persona
- **Audit / Config** — Auditor (อ่านอย่างเดียวข้าม chain — template, campaign, invitation, pricelist, ผล validate, activity log, การบริโภคปลายน้ำ) และ System Administrator (การตั้งค่าเท่านั้น — การกำหนดเลข, RBAC, นโยบาย portal-token, การเชื่อม email, กติกา validation, แหล่ง currency / FX, การเก็บ audit; บวกสิทธิ์ revoke token ต่อ invitation) พฤติกรรมส่วนใหญ่อยู่นอกเส้น happy path เชิงธุรกรรม; บันทึกแยกใน Section 3 เพื่อความครบถ้วน

## 3. ไฟล์ Test Persona

- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Vendor scenarios](./04-test-scenarios-vendor.md) — สั้นกว่าไฟล์ persona อื่น; section Permission / Authorization ลดลงเป็นแถว N/A เดียวตาม [03-user-flow-vendor.md](./03-user-flow-vendor.md) Section 1
- [Finance scenarios](./04-test-scenarios-finance.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Scenario ข้าม Persona / Handoff

Scenario ด้านล่าง trace pricelist ข้ามหลาย persona แต่ละแถว anchor sequence handoff กับสถานะเอกสารที่ขอบเขตและ end state ที่คาด derive จากตาราง handoff ใน [03-user-flow.md](./03-user-flow.md) Section 4

| # | Scenario | Persona ตามลำดับ | Pre-condition | End state ที่คาด |
| - | -------- | ----------------- | ------------- | ------------------ |
| X-VPL-01 | Happy path เต็ม — vendor เดียว, สกุลเงินเดียว, ต่ำกว่าขีดจำกัด | Purchaser (template + campaign) → Vendor (portal submit) → Purchaser (approve) → PR / PO / GRN ปลายน้ำ | Template active, vendor ในแคตตาล็อกพร้อม email ผู้ติดต่อ | Pricelist `active`; บรรทัด PR ปลายน้ำ default จาก pricelist นี้ |
| X-VPL-02 | High-value approval — gate Manager | Purchaser → Vendor → Purchasing Manager (approve) | Pricelist ที่ submit มี aggregate projected เกินขีดจำกัด high-value | Pricelist `active`; `system` signoff Manager บน activity log |
| X-VPL-03 | Multi-currency approval — co-signoff Manager + Finance Manager | Purchaser → Vendor → Purchasing Manager + Finance Manager (ขนาน) → activation | Pricelist ที่ submit สกุลเงินต่างจากฐาน tenant และข้ามขีดจำกัด FX | Pricelist `active`; ทั้ง Manager + Finance Manager `system` signoff |
| X-VPL-04 | Reject และ resubmit | Purchaser → Vendor → Purchaser (reject) → Vendor (correct + resubmit) → Purchaser (approve) | Pricelist ที่ submit พร้อม warning validator | Pricelist `active` หลังวงจร submit ครั้งที่สอง |
| X-VPL-05 | การ submission วิธี email (vendor ปฏิเสธ portal) | Purchaser (ออก email template) → Vendor (return Excel ทาง email) → Purchaser (upload ในนาม vendor) → Purchaser (approve) | Vendor ยืนยันผ่าน contact campaign ว่าไม่สามารถใช้ portal | Pricelist `active`; `submission_method = email`; `system` comment จับแหล่ง email + staff ที่ upload |
| X-VPL-06 | Variance เทียบกับ pricelist active บน GRN | Purchaser (pricelist active) → Receiver (GRN post พร้อม gap ราคา) → Finance (audit variance) → Purchaser (action) | Pricelist active; ราคาต่อหน่วย GRN เบี่ยงเบนเกินขีดจำกัด | Variance จัดประเภท; pricelist เป็น `inactive` (ถ้า out-of-date) หรือ `active` ไม่เปลี่ยน (ถ้า vendor over-bill หรือ FX-only) |
| X-VPL-07 | Token revoke mid-flight | Purchaser (invite) → Vendor (draft in-progress) → Sysadmin (revoke) → Purchaser (re-issue หรือละทิ้ง) | Vendor บันทึก draft; token ถูก compromise | Invitation `expired`; การเข้า portal ของ vendor `401`; draft รักษาสำหรับ audit |
| X-VPL-08 | Auto-expire ที่สิ้นสุด campaign | Purchaser (launch) → Vendor (ไม่ submit) → (cron auto-expire) | `end_date` ผ่านกับ invitation ที่ยัง `pending` หรือ `in-progress` | Invitation `expired`; token revoke; pricelist `(none)` หรือ `draft` (รักษา) |
| X-VPL-09 | Validation `quality_score` ต่ำกว่าขีดจำกัด route ไป Manager | Purchaser → Vendor → (validator คะแนนต่ำ) → Purchasing Manager (review + decide) | ข้อมูลของ vendor คุณภาพต่ำแต่ submit | เป็น `active` พร้อม Manager override + คะแนนต่ำในบันทึก หรือ `draft + submitted_at = NULL` หลังการ reject |
| X-VPL-10 | Auditor พบการละเมิดการแยก; Manager remediate | Auditor (chain audit) → Manager (inactivate ตามการแนะนำของ audit) | Pricelist high-value approve โดย user เดียวกันที่แก้แถว | Pricelist `inactive`; ไฟล์เคส audit ปิด; launch campaign ใหม่ |
| X-VPL-11 | การเปลี่ยน config ของ Sysadmin รักษา snapshot in-flight | Sysadmin (เปลี่ยน RBAC mid-flight) → pricelist in-flight (ดำเนินต่อภายใต้ snapshot เก่า) → pricelist ใหม่ (ใช้ RBAC ใหม่) | Pricelist mid-Manager-review ที่ moment ของ save | Pricelist in-flight activate ภายใต้ RBAC เก่า; pricelist ใหม่ครั้งต่อไปใช้ RBAC ใหม่ |
| X-VPL-12 | การแก้ pricelist active ผ่าน inactivate + campaign ใหม่ | Purchaser (inactivate) → Purchaser (launch campaign ใหม่) → Vendor (re-submit) → Purchaser (approve) | Pricelist active พบว่ามี error หลังการ activate | Pricelist เก่า `inactive` (historical); pricelist ใหม่ `active`; ผู้บริโภคปลายน้ำตกไปยังตัวใหม่ที่การอ่านครั้งต่อไป |

## 5. E2E Test Mapping

ไม่มี Playwright spec dedicated สำหรับโมดูล `vendor-pricelist` วันนี้; `tasks.md` ของ carmen/docs ระบุ pricelist E2E เป็น roadmap item Coverage วันนี้แยกใน:

- **Test API / integration บน backend** — exercise template / campaign / pricelist CRUD, output validation-engine, middleware portal-token และการเขียน log audit การตั้งค่า อยู่ภายใต้ `../carmen-turborepo-backend-v2/apps/<service>/test/` เมื่อ vendor-pricelist service module ถูกสร้าง; ติดตามใน `tasks.md` § Implementation Tasks
- **E2E ข้ามโมดูล** — การ interact `vendor-pricelist` ถูก exercise ทางอ้อมผ่าน spec ผู้บริโภคปลายน้ำ:
  - `../carmen-inventory-frontend-e2e/tests/4*-pr*.spec.ts` — การ default preferred-vendor บรรทัด PR และการจัดการการขาด pricelist coverage
  - `../carmen-inventory-frontend-e2e/tests/401-po.spec.ts` และ `402-po-purchaser-journey.spec.ts` — Snapshot PO จาก pricelist active ที่ PR-to-PO conversion + wizard From Price List (TC-PO-060205..TC-PO-060208)
  - `../carmen-inventory-frontend-e2e/tests/4*-grn*.spec.ts` — GRN variance check ที่การ posting เทียบกับ pricelist active
- **Harness vendor portal** — secure portal ภายใต้ `app/(main)/vendor-portal/[token]/` (carmen/docs `design.md` § Phase 5) มีชั้น harness ของตนสำหรับการ test session ที่ authenticate ด้วย token; นี่เป็น test bed แยกจาก Carmen E2E หลักเพราะ vendor portal เป็น surface สาธารณะที่ไม่ authenticate ที่ใช้การแลกเปลี่ยน token
- **Test การ audit / การตั้งค่า** — exercise ที่ระดับ API / integration (service audit และ config ข้ามโมดูล) การ query audit-log และ surface การจัดการการตั้งค่าไม่มี UI E2E dedicated

ไฟล์ test ของแต่ละ persona Section 5 บันทึก "ไม่มี vendor-pricelist E2E spec dedicated วันนี้ — ดู roadmap item ใน `tasks.md`" และ cross-reference เส้นทาง coverage ทางอ้อมข้างต้น ที่ scenario ถูก exercise โดย spec โมดูลปลายน้ำ ไฟล์ persona เรียก spec file และ test-case id ที่เกี่ยวข้อง

## 6. แหล่งอ้างอิง

- `../carmen/docs/vendor-pricelist-management/tasks.md` — roadmap item: vendor-pricelist E2E spec dedicated; จนกว่าจะเสร็จ coverage รันผ่าน test API / integration และ E2E ผู้บริโภคปลายน้ำ
- `../carmen-inventory-frontend-e2e/tests/401-po.spec.ts` — scenario wizard `From Price List` ครอบคลุมฝั่งอ่านของการบริโภค pricelist (TC-PO-060205..TC-PO-060208)
- `../carmen-inventory-frontend-e2e/tests/402-po-purchaser-journey.spec.ts` — Snapshot PR-to-PO conversion ของราคา pricelist active; ตรวจสอบ `VPL_XMOD_003`
- Sibling: [03-user-flow.md](./03-user-flow.md) § 4 (แหล่ง handoff) — ทุก scenario ข้าม persona ใน Section 4 map ไปยัง handoff ในตารางนี้
- Sibling: [02-business-rules.md](./02-business-rules.md) § 5 (กติกา posting + transition), § 6 (กติกาข้ามโมดูล `VPL_XMOD_001`–`VPL_XMOD_009`)
- Sibling: [01-data-model.md](./01-data-model.md) — เอนทิตี, enum, ข้อจำกัด unique และตาราง divergence ที่ scenario อ้างอิง
