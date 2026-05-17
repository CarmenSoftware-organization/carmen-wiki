---
title: การปรับสต๊อก (Inventory Adjustment) — Test Scenarios — Audit & Config
description: Test cases ของ Auditor และ System Administrator สำหรับการปรับสต๊อก
published: true
date: 2026-05-17T12:00:00.000Z
tags: inventory-adjustment, test-scenarios, audit, sysadmin, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — Test Scenarios — Audit & Config

> **At a Glance**
> **Persona:** Audit / Config (Auditor + System Administrator) &nbsp;·&nbsp; **โมดูล:** [[inventory-adjustment]] &nbsp;·&nbsp; **Scenarios:** ~38
> **ประเภท:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **การครอบคลุม E2E:** map ไปยัง `031-adjustment-type.spec.ts` ใน `../carmen-inventory-frontend-e2e/`

หน้านี้ capture test scenarios ที่ persona group **Audit / Config** — Auditor (การ inspect audit-trail read-only) และ System Administrator (master-data และการกำหนดค่า CRUD) — ขับเคลื่อนในโมดูล `inventory-adjustment` ทั้งสองบทบาทเป็น **non-transactional** ในวงจรชีวิตเอกสาร: พวกเขาไม่สร้าง, อนุมัติ, แก้ไข หรือ void เอกสาร adjustment Scenarios ของ Sysadmin ส่วนใหญ่ exercise โดย E2E spec [`031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) (CRUD admin reason-code); scenarios ของ Auditor โดยทั่วไป manual / planned audit-query patterns Sections group เป็น **happy paths** (เพิ่ม/แก้ไข/deactivate reason-code, การเปลี่ยน threshold, review audit-trail, การตรวจสอบ SoD compliance, lot-recall trace, การตรวจสอบ void-chain), **RBAC / permission** (scope การกำหนดค่า, scope read-only, การอนุมัติ export อ่อนไหว), **validation** (การ validate Sysadmin master-data CRUD, การ validate input audit-query) และ **edge cases** รอบเวลาการกำหนดค่า (apply prospective, การ inherit เอกสาร in-flight), gate การอนุมัติ audit-export และ snapshots การกำหนดค่าประวัติ

## 1. Happy Path

### 1.1 Scenarios ของ System Administrator

| # | Scenario | Pre-condition | ขั้นตอน | Expected |
| - | -------- | ------------- | ----- | -------- |
| AC-HP-01 | Sysadmin เพิ่ม reason code ใหม่ด้วย GL-account mapping | Sysadmin `admin@blueledgers.com` login; business case ใหม่ (insurance-claimable losses) | 1. โมดูล Admin → Master Data → Adjustment Types → New 2. กรอก `code = INSURANCE_WRITE_OFF`, `name = "Insurance Write-Off"`, `type = STOCK_OUT`, `description` 3. Set `info.glAccount = "6535"`, `info.requiresDocument = true`, `info.requiresQualityCheck = true` 4. Save | แถว `tb_adjustment_type` ใหม่สร้าง; `@@unique([code, deleted_at])` บังคับใช้ พร้อมใน pickers สำหรับเอกสารใหม่ทันที Sysadmin audit log บันทึกการเปลี่ยนแปลง Map ไปยัง parent Scenario 19 Exercise โดย [`031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) `TC-AT-010005` (validation) / `TC-AT-010006` (create) |
| AC-HP-02 | Sysadmin แก้ไข reason code ที่มีอยู่ | Reason `BREAKAGE` ที่มีอยู่; Sysadmin อัปเดต `info.glAccount` จาก `"6510"` (breakage ทั่วไป) เป็น `"6512"` (F&B-specific breakage) เนื่องจาก restructure chart-of-accounts | 1. โมดูล Admin → Adjustment Types → Search "BREAKAGE" 2. เปิดแถว 3. อัปเดต `info.glAccount` เป็น `"6512"` 4. Save | แถวอัปเดต; GL mapping ใหม่ apply prospective กับเอกสารใหม่ที่ submit เอกสาร `completed` ที่มีอยู่คง GL mapping เดิมผ่านรูปแบบ snapshot cost-layer ตาม `ADJ_XMOD_007` Audit log บันทึก before/after |
| AC-HP-03 | Sysadmin deactivate reason code ที่ obsolete | Reason `OLD_DATA_FIX` ที่มีอยู่ไม่ใช้แล้วหลังการเปลี่ยนกระบวนการ | 1. โมดูล Admin → Adjustment Types → Search "OLD_DATA_FIX" 2. Toggle `is_active = false` 3. Save | Reason ซ่อนจาก pickers ของเอกสารใหม่; ยังอ่านได้บนเอกสารประวัติตาม `tb_adjustment_type.is_active` Soft-delete (`deleted_at` non-null) เข้มกว่า — ใช้ถ้า reason สร้างผิด; หายาก |
| AC-HP-04 | Sysadmin เปลี่ยน auto-approve threshold | Tenant ตัดสินใจยก auto-approve จาก `฿500` เป็น `฿1,000` | 1. โมดูล Admin → Thresholds 2. เปลี่ยน auto-approve จาก `500` เป็น `1000` 3. Save ด้วย effective date | Threshold apply prospective ที่ submits ใหม่ตาม `ADJ_AUTH_002` เอกสาร `draft` ที่มีอยู่ inherit ที่เวลา submit เอกสาร `in_progress` ที่มีอยู่คงการ route threshold ที่พวกเขาเข้ามาด้วย Audit-log |
| AC-HP-05 | Sysadmin กำหนด user-location scope | Store Keeper ใหม่ `sk2@blueledgers.com` ต้องการ scope สำหรับ `LOC-B` และ `LOC-C` | 1. โมดูล Admin → RBAC → User Locations 2. เลือก `sk2@blueledgers.com` 3. เพิ่ม `LOC-B` และ `LOC-C` ใน scope 4. Save | แถว `tb_user_location` สร้าง SK สามารถสร้าง adjustments ที่ locations เหล่านั้นตาม `ADJ_AUTH_001` |

### 1.2 Scenarios ของ Auditor

| # | Scenario | Pre-condition | ขั้นตอน | Expected |
| - | -------- | ------------- | ----- | -------- |
| AC-HP-06 | Auditor review trail adjustment ของงวด | Auditor `audit@blueledgers.com`; งวด `2026-04` lock; รอบ external audit | 1. โมดูล Audit → Adjustment Trail → period `2026-04` 2. รายงาน aggregate render: total stock-in, total stock-out, ตาม reason, ตาม location, ตาม department, ตามผู้ใช้ 3. Drill เข้าแต่ละ high-cost item; ตรวจสอบลายเซ็นอนุมัติใน `workflow_history` 4. Compile audit findings | ข้อมูล Read-only; ไม่มีการเปลี่ยนสถานะ Findings ติดตามใน workflow รายงาน audit (external) |
| AC-HP-07 | Auditor ตรวจสอบ SoD compliance | Period `2026-04`; SoD threshold configure ที่ `฿5,000` ตาม `ADJ_AUTH_010` | 1. โมดูล Audit → รายงาน SoD Compliance → `2026-04` 2. Query join `tb_stock_out` (`created_by_id`, lot) ต่อ `tb_good_received_note` (`created_by_id`, lot) สำหรับ lot เดียวกันเหนือ SoD threshold 3. รายการ findings flag คู่ | ตามการบังคับใช้ `ADJ_AUTH_010` การละเมิดควรเป็น zero (reject ที่เวลา submit) กรณีประวัติก่อนกฎหรืองวดที่ผ่อนคลายอาจปรากฏ; flag สำหรับ compliance follow-up Map ไปยัง parent Scenario 20 |
| AC-HP-08 | Auditor รัน lot-recall trace | Lot `LOT-2023-Q4` ของ `P-1` ได้รับผลกระทบจาก recall; introduce โดย GRN, ส่วนหนึ่ง issue ผ่าน SR, ส่วนหนึ่ง write off ผ่าน `RECALL_WRITE_OFF` stock-out, ด้วย `tb_credit_note` amount adjustment apply | 1. โมดูล Audit → Lot Recall Trace 2. กรอก `lot_no = LOT-2023-Q4`, `product_id = P-1` 3. Forward trace: SR issues + stock-out write-offs + แถวปริมาณ credit-note 4. Backward trace: GRN ต้นทางด้วย vendor / cost / date 5. Render chain-of-custody | ทั้งสองทิศทาง resolve ผ่าน `tb_inventory_transaction` polymorphic join Read-only; ไม่มีการเปลี่ยนสถานะ Map ไปยัง parent Scenario 21 |
| AC-HP-09 | Auditor ตรวจสอบ void chains | งวดมี 5 `voided` เอกสาร `tb_stock_in` / `tb_stock_out` | 1. โมดูล Audit → Void Chain Verification → `2026-04` 2. สำหรับแต่ละเอกสาร `voided` ค้นหา compensating reversal ผ่าน `info.voidsAdjustmentId` 3. ตรวจสอบว่าเอกสาร compensating เป็น `completed` ด้วยทิศทาง reverse และบรรทัดเดียวกัน 4. รายการ findings orphans (voided โดยไม่มี compensating) | ตาม `ADJ_POST_004`, ทุก `voided` ควรมี compensating reversal Orphans flag Map ไปยัง parent Scenario 22 |
| AC-HP-10 | Auditor review detail เอกสารเฉพาะ | Reactive: Finance flag เอกสารที่ post เป็น anomalous | 1. โมดูล Audit → Document Detail → `<si_no / so_no>` 2. View chain เต็ม: header, lines, attachments, `workflow_history`, `tb_inventory_transaction` ที่เกิดขึ้นพร้อมผลกระทบ cost-layer, GL journal 3. Cross-check กับ `info.glAccount` ของ reason code ที่เวลา post | Read-only; ไม่มีการเปลี่ยนสถานะ Detail เอกสารพร้อม provenance |
| AC-HP-11 | Auditor export ข้อมูล cost อ่อนไหว (การอนุมัติรอง) | Findings audit ต้องการ export ของ cost-per-unit / vendor terms สำหรับงวด | 1. โมดูล Audit → Adjustment Trail → Export 2. คลิก "Export sensitive fields" 3. ระบบ prompt การอนุมัติ Auditor รอง 4. Auditor ที่สอง approve 5. Export ดำเนินการ (CSV / PDF) | ตามรูปแบบ audit `ADJ_AUTH_009`, การ export ฟิลด์อ่อนไหวต้องการการอนุมัติรอง Identities ของ Auditors ทั้งสองบันทึกใน export audit log |

## 2. Permission / Authorization

### 2.1 System Administrator

| # | Scenario | พฤติกรรมที่คาดหวัง (allow/deny + เหตุผล) |
| - | -------- | --------------------------------------- |
| AC-PERM-01 | Sysadmin CRUD `tb_adjustment_type` | **Allow ตาม `ADJ_AUTH_008`** Scope master-data |
| AC-PERM-02 | Sysadmin เปลี่ยน thresholds (auto-approve, Controller, Finance, SoD) | **Allow ตาม `ADJ_AUTH_008`** Apply prospective Audit-log |
| AC-PERM-03 | Sysadmin จัดการ scope `tb_user_location` และ RBAC | **Allow** |
| AC-PERM-04 | Sysadmin พยายามสร้าง / อนุมัติ adjustment | **Deny — role config-only เท่านั้น** ตามข้อจำกัด `ADJ_AUTH_008` Role Sysadmin ไม่รวมอำนาจสร้างหรืออนุมัติ Store Keeper / Controller / Finance (ในทางปฏิบัติ ผู้ใช้คนเดียวอาจถือบทบาทหลายตัว; กฎนี้ครอบคลุมการกำหนด Sysadmin-only) |
| AC-PERM-05 | Sysadmin พยายามแก้ไขเอกสาร `completed` | **Deny ตาม `ADJ_VAL_013`** Immutable; ต้องการ void ผ่าน compensating reversal (และ Sysadmin role ไม่มีอำนาจนั้น) |
| AC-PERM-06 | Sysadmin พยายามเปลี่ยน GL mapping ประวัติย้อนหลัง | **Deny — forward-only** การเปลี่ยน GL ของ reason-code apply prospective; เอกสาร `completed` ประวัติคง mapping เดิม เพื่อ "แก้ไข" posts ประวัติ ต้องการรอบ void + compensating + การ submit ใหม่ (อำนาจ Controller / Finance) |

### 2.2 Auditor

| # | Scenario | พฤติกรรมที่คาดหวัง (allow/deny + เหตุผล) |
| - | -------- | --------------------------------------- |
| AC-PERM-07 | Auditor อ่าน `tb_stock_in` / `tb_stock_out` / detail / comment / attachment ใด ๆ | **Allow ตาม `ADJ_AUTH_009`** Full read scope รวมเอกสาร soft-deleted และ voided |
| AC-PERM-08 | Auditor อ่าน `tb_inventory_transaction` / cost-layer ledger / GL journal entries | **Allow ตาม [[inventory]] `INV_AUTH_009`** (รูปแบบการอ่านเดียวกัน, join) |
| AC-PERM-09 | Auditor พยายามแก้ไข, อนุมัติ หรือ void เอกสาร | **Deny — read-only** Auditor role ไม่มีอำนาจเขียนบนเอกสาร adjustment |
| AC-PERM-10 | Auditor export aggregate ที่ไม่อ่อนไหว (counts, totals ตาม reason) | **Allow** Read scope มาตรฐาน |
| AC-PERM-11 | Auditor export ฟิลด์อ่อนไหว (cost-per-unit, vendor terms) | **Allow ด้วยการอนุมัติ Auditor รอง** ตาม `ADJ_AUTH_009` Single-Auditor export block Map ไปยัง AC-HP-11 |
| AC-PERM-12 | Auditor พยายามเปลี่ยนการกำหนดค่า reason-code หรือ threshold | **Deny — Sysadmin required** ตาม `ADJ_AUTH_008` |

## 3. Validation / Error

### 3.1 System Administrator

| # | Scenario | Trigger | Expected error |
| - | -------- | ------- | -------------- |
| AC-VAL-01 | Reason-code uniqueness บน `code` (`@@unique([code, deleted_at])`) | Sysadmin สร้าง `tb_adjustment_type` ใหม่ด้วย `code = BREAKAGE` (มีอยู่แล้ว, ไม่ soft-deleted) | Reject ด้วย `"Reason code <BREAKAGE> already exists."` แถว soft-deleted ไม่ conflict (unique scope รวม `deleted_at`) สะท้อน Prisma unique constraint ของ `tb_adjustment_type` |
| AC-VAL-02 | ฟิลด์ที่บังคับขาด | Sysadmin สร้าง `tb_adjustment_type` ใหม่โดยไม่มี `code` หรือ `name` หรือ `type` | Reject ด้วย error ตามฟิลด์: `"Code is required."` / `"Name is required."` / `"Direction (type) is required."` Exercise โดย [`031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) `TC-AT-010005` |
| AC-VAL-03 | `info.glAccount` invalid | Sysadmin set `info.glAccount = "9999"` สำหรับบัญชีที่ไม่มีอยู่ใน chart of accounts | Reject ด้วย `"GL account <9999> is not a valid account."` (Validation ต่อ Finance chart-of-accounts integration) |
| AC-VAL-04 | การเปลี่ยน threshold ด้วยค่า invalid | Sysadmin set auto-approve threshold = `-100` (negative) หรือ > Controller threshold | Reject ด้วย `"Auto-approve threshold must be positive and less than Controller threshold."` |
| AC-VAL-05 | Soft-delete reason ที่มีเอกสาร in-flight active | Sysadmin soft-delete แถว `tb_adjustment_type` ที่มีเอกสารอ้างอิง active (`draft` / `in_progress`) | Block soft-delete ด้วย `"Reason <code> is in use by <N> active documents; deactivate (is_active = false) or wait for documents to complete / cancel."` Soft-delete ดำเนินการเฉพาะเมื่อไม่มี references active (references `completed` ประวัติอนุญาต — พวกเขา snapshot รหัส) |

### 3.2 Auditor

| # | Scenario | Trigger | Expected error |
| - | -------- | ------- | -------------- |
| AC-VAL-06 | Lot-recall trace ด้วย lot ที่ไม่มี | Auditor กรอก `lot_no = LOT-XYZ` ที่ไม่มีแถว `tb_inventory_transaction_cost_layer` | "No history found for lot LOT-XYZ at product <product>." Trace ว่าง; ไม่มี error |
| AC-VAL-07 | Sensitive-export approval timeout | Auditor ที่สองไม่ approve ภายใน window ที่ tenant configure (เช่น 24h) | Export request expire; Auditor คนแรกต้อง submit ใหม่ Audit log บันทึก expiry |

## 4. Edge Cases

| # | Scenario | เงื่อนไข | Expected |
| - | -------- | --------- | -------- |
| AC-EDGE-01 | การเปลี่ยน config reason-code ระหว่างเอกสาร in-flight | SK มีเอกสาร `draft` ด้วย `adjustment_type_id = X`; Sysadmin อัปเดต `X.info.glAccount` ระหว่างการสร้าง draft และ SK submit | Submit ใช้ `info.glAccount` **ปัจจุบัน** (อัปเดต) Snapshot draft คือ reference `adjustment_type_id` ของเอกสาร ไม่ใช่เนื้อหา `info` JSON — นั่น resolve ที่ post time |
| AC-EDGE-02 | การเปลี่ยน direction reason-code ถูก block | Sysadmin พยายามเปลี่ยน `tb_adjustment_type.type` จาก `STOCK_IN` เป็น `STOCK_OUT` บน reason ที่มีอยู่ | **Block** — การเปลี่ยนทิศทางจะ corrupt picker filter สำหรับเอกสารประวัติที่อ้างอิง; แทนนั้น deactivate reason เดิมและสร้างใหม่ด้วยทิศทางที่ต้องการ (UI อาจแสดงเป็น warning แทน hard block ขึ้นกับ tenant policy) |
| AC-EDGE-03 | การเปลี่ยน threshold effective-date สำหรับ period ถัดไป | Sysadmin set effective date = `2026-06-01` | การเปลี่ยน apply เฉพาะกับ submits ใหม่ที่ `2026-06-01` หรือหลัง Submits ก่อนวันที่ใช้ threshold ก่อนหน้า |
| AC-EDGE-04 | Audit query การกำหนดค่า — ใครเปลี่ยนอะไร | Auditor query platform audit log สำหรับการเปลี่ยน `tb_adjustment_type` ทั้งหมดในงวด | Return รายการด้วย actor, timestamp, before/after JSON Cross-reference กับเอกสาร adjustment ที่ post ระหว่าง window เดียวกันเพื่อประเมินผลกระทบ |
| AC-EDGE-05 | Recall-trace performance บน lot ที่ hot | Lot มี 10,000+ การเคลื่อนไหวปลายน้ำ (issues, transfers, write-offs, credit-notes) | Trace query รันด้วย indices ที่เหมาะสมบน `tb_inventory_transaction_cost_layer.lot_no, lot_index` (`inventorytransactionclosingbalance_lotno_lot_index_u`); ผล paginate Read-only; ไม่มีการเปลี่ยนสถานะ |
| AC-EDGE-06 | การตรวจสอบ Void-chain ด้วย two-deep void | Compensating reversal ถูก void เอง (parent IC-EDGE-07) | Trace render สามเอกสาร: original → comp → comp-of-comp Auditor inspect chain เหตุผล; orphan-detection มอง level เดียว (แต่ละ `voided` จับคู่กับ comp อย่างน้อยหนึ่งตัว) |
| AC-EDGE-07 | Sensitive-export approver self-approve | Auditor คนแรกพยายามใช้ login ที่สองเพื่อ approve export ของตัวเอง | **Deny** — secondary approver ต้องเป็นผู้ใช้ต่างจากคนแรก Self-approval block ที่ auth layer |
| AC-EDGE-08 | SoD-report performance บนงวดใหญ่ | งวดที่มี 50,000+ adjustment posts | Report รันเป็น scheduled job (offline); generate ภายใน tenant SLA (เช่น 30 นาที) Auditor download ผลเมื่อพร้อม |

## 5. แหล่งอ้างอิง

- ภาพรวม parent: [04-test-scenarios.md](./04-test-scenarios.md) — handoff scenarios ที่ Audit/Config เป็น protagonist: 19 (Sysadmin เพิ่ม reason-code), 20 (Auditor SoD compliance), 21 (Auditor lot-recall), 22 (Auditor การตรวจสอบ void-chain)
- User flow: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — Sysadmin primary 7 ขั้น CRUD flow สำหรับ reason codes; Auditor primary 7 ขั้น trail-review flow และ 4 ขั้น lot-recall flow; decision branches (soft-fail vs hard-fail audit findings, add vs modify reason, threshold scope)
- กฎทางธุรกิจ: [02-business-rules.md](./02-business-rules.md) — `ADJ_AUTH_008` (scope Sysadmin), `ADJ_AUTH_009` (scope การอ่าน Auditor), `ADJ_AUTH_010` (SoD), `ADJ_VAL_001` (รูปแบบเลขที่เอกสาร unique แชร์กับ reason-code uniqueness), `ADJ_VAL_002` (reason direction), `ADJ_VAL_010` (requiresDocument flag), `ADJ_POST_004` (void chain)
- E2E specs: [`../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) — spec CRUD Sysadmin canonical (TC-AT-010001..n ครอบคลุม list / search / pagination / create / edit / activate-toggle / validation / security cases) ผู้ใช้ fixture `admin@blueledgers.com`
- Cross-link: [[inventory]] — `INV_AUTH_008` (scope การกำหนดค่า Sysadmin span นิยาม location-type / costing-method / period นอกเหนือจาก adjustment-type); `INV_AUTH_009` (scope การอ่าน Auditor span ข้อมูล inventory ทั้งหมด)
- Cross-link: [[good-receive-note]] — รูปแบบ lot-recall trace ของ Auditor สะท้อนวิธีของ [[good-receive-note/04-test-scenarios-audit-config]]
- Cross-link: [[physical-count]] / [[spot-check]] — adjustments variance-rollup cross-check โดย Auditor สำหรับความสมเหตุสมผลและ SoD compliance
