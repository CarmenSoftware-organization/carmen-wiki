---
title: การนับสต๊อกประจำงวด (Physical Count) — Test Scenarios
description: Test case ต่อ persona, scenario ข้าม persona และการ map ไปยัง E2E สำหรับการนับสต๊อกประจำงวด
published: true
date: 2026-05-19T23:55:00.000Z
tags: physical-count, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# การนับสต๊อกประจำงวด (Physical Count) — Test Scenarios

> **At a Glance**
> **โมดูล:** [physical-count](/th/inventory/physical-count) &nbsp;·&nbsp; **จำนวน scenario รวม:** ~20 ข้าม persona + ~90 ต่อ persona (skeleton) &nbsp;·&nbsp; **Persona ที่ครอบคลุม:** Count Lead, Counter, Audit / Config
> **ลำดับการรัน:** Audit / Config setup → happy path ของ persona หลัก → scenario ข้าม persona
> **Drill-down ของแต่ละ persona อยู่ที่ `04-test-scenarios-<role>.md`**

## 1. ภาพรวม

หน้านี้เป็น **จุดเริ่ม overview** สำหรับชุด test-scenario ของโมดูล `physical-count` รวมความครอบคลุมตามสามกลุ่ม persona ที่มีปฏิสัมพันธ์กับวงจรชีวิตการนับ (Count Lead, Counter, Audit / Config — ยุบจากสี่ persona canonical ใน [physical-count](/th/inventory/physical-count) § 4) ลิสต์ไฟล์ test ต่อ persona จับ scenario การ handoff ข้าม persona ที่เย็บเส้นทางบุคคลเข้าด้วยกัน และตีกรอบเป้าหมาย mapping E2E — ปัจจุบันว่างเปล่าเพราะ **ยังไม่มี Playwright spec ของ `physical-count`** ที่ `../carmen-inventory-frontend-e2e/tests/` ณ ขณะนี้ (ตรวจสอบโดย `ls tests/ | grep -i 'physical\|count'`)

ขอบเขตจงใจกว้างแม้ที่ระดับ skeleton: แต่ละไฟล์ persona ตั้งใจให้เติบโตครอบคลุม **functional happy path** (เปิด period, สร้าง sheet, ป้อนการนับ, recount-and-resolve, submit, rollup post), **RBAC / permission case** (Counter พยายาม submit, Count Lead พยายามป้อน counter-zone, Auditor พยายามแก้ไข), **validation** (negative test กับ `PHC_VAL_001`–`PHC_VAL_008` ที่ line entry, ที่ submit, ที่ recount-flag), **edge case** (ศูนย์บนชั้น, การพยายามเคลื่อนไหวโหมด frozen, บรรทัด tolerance-boundary, การมอบหมาย counter ใหม่ระหว่าง period) และ **configuration / audit-trail case** (ผลของการเปลี่ยน tolerance threshold, ผลของการเปลี่ยน costing-method, การ inspect chain audit)

Scenario ข้าม persona ในหัวข้อ 4 อธิบายการเดินทาง end-to-end ที่ข้ามขอบเขต handoff ที่บันทึกใน [03-user-flow.md](./03-user-flow.md) หัวข้อ 4 — ตัวอย่างเช่น *Count Lead สร้าง sheet → Counter ทำการนับ → Count Lead submit → Approver / Finance อนุมัติ rollup adjustment*; *Count Lead flag variance → Counter คนละคน recount → variance reconcile → submit*; *Count Lead submit ด้วย overage และ shortage → สร้าง rollup adjustment สองฉบับ*; *การนับโหมด frozen บล็อกการ post GRN ขนาน → operational reconciliation*; *Auditor ตรวจ chain เต็มตั้งแต่ count sheet ถึง journal entry* หัวข้อ 5 เป็น E2E spec map — ปัจจุบันเป็น TODO เป้าหมายรอ spec physical-count แรกถูกเขียน

> **TODO:** แทนที่กรอบ E2E ของ overview นี้ด้วย citation spec ที่ตรวจสอบด้วย `ls` เมื่อ `../carmen-inventory-frontend-e2e/tests/` เพิ่มความครอบคลุม physical-count จนกว่าจะถึงตอนนั้น scenario test ใน persona file เป็นการครอบคลุม manual / planned

## 2. Persona ในขอบเขต

- **Count Lead** — Inventory Controller / Inventory Manager เจ้าของการดำเนินการ; ตาม [physical-count/03-user-flow-count-lead](/th/inventory/physical-count/03-user-flow-count-lead)
- **Counter** — Counter / Store Keeper การป้อนข้อมูลพื้นที่; ตาม [physical-count/03-user-flow-counter](/th/inventory/physical-count/03-user-flow-counter)
- **Audit / Config** — Approver / Finance Reviewer + Auditor + Sysadmin การอนุมัติ การสังเกต การ config; ตาม [physical-count/03-user-flow-audit-config](/th/inventory/physical-count/03-user-flow-audit-config)

## 3. ไฟล์ Test ของ Persona

- [Scenario ของ Count Lead](./04-test-scenarios-count-lead.md)
- [Scenario ของ Counter](./04-test-scenarios-counter.md)
- [Scenario ของ Audit / Config](./04-test-scenarios-audit-config.md)

## 4. Scenario ข้าม Persona / Handoff

ตารางด้านล่างเป็น integration layer แต่ละ row spans handoff อย่างน้อยหนึ่งจาก [03-user-flow.md](./03-user-flow.md) หัวข้อ 4 และจบที่ระบบใน terminal หรือสถานะ steady "Persona ตามลำดับ" ลิสต์ผู้กระทำตามลำดับการ execute; "Pre-condition" จับสถานะระบบที่ต้องใช้เพื่อเริ่ม; "สถานะปลายทางที่คาดหวัง" anchor `tb_physical_count.status`, ผลของ rollup adjustment (`tb_stock_in` / `tb_stock_out` เขียนผ่าน `info.countId` link ไป [inventory-adjustment](/th/inventory/inventory-adjustment)) และผลข้างเคียงข้ามโมดูล

| # | Scenario | Persona ตามลำดับ | Pre-condition | สถานะปลายทางที่คาดหวัง |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | การนับสิ้นงวดเต็ม — happy path | Count Lead → Counter → Count Lead → Approver / Finance | `tb_period` เปิด; ไม่มีการนับอื่น in-progress ที่ location | `tb_physical_count_period.status = completed`; `tb_physical_count.status = completed`; เอกสาร rollup `tb_stock_in` / `tb_stock_out` post; row `tb_inventory_transaction` เขียน |
| 2 | Cycle count สำหรับหมวดมูลค่าสูง — variance auto-resolved | Count Lead → Counter → Count Lead | หมวดย่อยสุรา; tolerance threshold 5% | variance ทั้งหมดอยู่ภายใน tolerance; submit ยิง rollup; `tb_inventory_transaction` เขียนสำหรับบรรทัด `diff_qty` ไม่เป็นศูนย์ |
| 3 | Recount escalation — counter คนละคน | Count Lead → Counter (A) → Count Lead → Counter (B) → Count Lead | Counter A ป้อน `actual_qty` trigger tolerance breach ตาม `PHC_VAL_007` | บรรทัด recount แก้ไขโดย Counter B; variance reconcile ภายใน tolerance; submit ยิง rollup |
| 4 | Recount ยืนยัน variance — ยอมรับและ post | Count Lead → Counter (A) → Counter (B) → Count Lead | Recount ยืนยันการนับเดิม | Count Lead override พร้อม countersignature; rollup post บรรทัด variance Thread comment พกพา justification ของ override |
| 5 | การนับโหมด frozen บล็อก GRN | Count Lead → Counter → (พยายาม GRN ขนาน) → Count Lead | `physical_count_type = yes`; GRN ตั้งที่ location เดียวกัน | การ post GRN ถูก reject ตาม `PHC_VAL_006` พร้อม error location-locked; การนับ complete; GRN พยายาม post ใหม่หลัง completion |
| 6 | การนับโหมด live ขนานกับ GRN | Count Lead → Counter → (GRN ขนาน) → Count Lead | `physical_count_type = no` | GRN post ปกติ; `on_hand_qty` ของการนับ snapshot ที่เวลา sheet-gen ดังนั้นผลของ GRN ต่อ inventory ไม่ back-drift การนับ Variance เปรียบเทียบกับ snapshot |
| 7 | ศูนย์บนชั้น vs ศูนย์นับ | Counter → Count Lead | บรรทัดที่ `on_hand_qty = 5`, counter ไม่เห็นอะไร | Counter ป้อน `actual_qty = 0`; `diff_qty = -5`; บรรทัด flag recount ตาม `PHC_VAL_007`; recount ยืนยัน; rollup เป็น `COUNT_SHORTAGE` |
| 8 | บรรทัด overage | Counter → Count Lead | บรรทัดที่ `on_hand_qty = 10`, counter พบ 12 | `diff_qty = +2`; rollup เป็น `COUNT_OVERAGE` ผ่าน `tb_stock_in` |
| 9 | overage + shortage ผสมในการนับเดียวกัน | Count Lead → Counter → Count Lead | เอกสาร count ที่มีหลาย variance บวกและลบ | เอกสาร rollup **สองฉบับ**: `tb_stock_in` หนึ่ง (บรรทัด overage), `tb_stock_out` หนึ่ง (บรรทัด shortage) ทั้งสองพกพา `info.countId` |
| 10 | Flag รายการเสียหายข้าม normal count | Counter → Count Lead | Counter พบรายการเสียหายที่ไม่อยู่บน sheet | Detail-comment flag พร้อม attachment photo; Count Lead review; อาจเพิ่มบรรทัดเองหรืออ้างอิงไป write-off ผ่าน [inventory-adjustment](/th/inventory/inventory-adjustment) โดยตรง |
| 11 | Counter พยายาม submit — reject (RBAC) | Counter | Counter มี zone-grant; ทุกบรรทัด zone นับแล้ว | Action submit ไม่มีให้ Counter ตาม `PHC_AUTH_002`; Count Lead รับ notification ของการ complete |
| 12 | Counter พยายามป้อนการนับนอก zone — reject | Counter | Counter มี zone-grant สำหรับ zone A; พยายามแก้ไขบรรทัด zone B | บันทึก reject ตาม `PHC_AUTH_004` พร้อม error zone-scope |
| 13 | เปลี่ยน tolerance threshold ระหว่าง period | Sysadmin → Count Lead → Counter | Sysadmin แน่นขึ้น threshold จาก 5% เป็น 2% | การนับใหม่หลังเปลี่ยนใช้ 2%; การนับที่กำลังดำเนินใช้ 5% (snapshot ตอน sheet-gen) ตรวจสอบผ่านการทดสอบ tolerance count |
| 14 | ผลของการเปลี่ยน costing-method ต่อมูลค่า rollup | Sysadmin → Count Lead | Sysadmin เปลี่ยน default จาก `last` เป็น `average` | Rollup ในอนาคตตีมูลค่า variance ที่ weighted average ปัจจุบันตาม `PHC_CALC_003` Rollup ที่ post แล้วไม่เปลี่ยน |
| 15 | การ post backdate การนับ — reject | Count Lead | Period ที่บรรจุการนับเป็น `closed` ตาม [inventory](/th/inventory/inventory) `INV_VAL_008` | Submit ของ rollup adjustment ถูก reject; Count Lead ต้อง escalate ไป Finance Manager เพื่อเปิด period ใหม่ |
| 16 | Approver / Finance reject rollup adjustment | Count Lead → Approver / Finance → Count Lead | Variance ใหญ่ผิดปกติ (เช่น 30% บนหมวดติดตาม) | Rollup `tb_stock_in` / `tb_stock_out` return ไป `draft`; Count Lead สืบสวน (อาจ mis-count, mis-categorisation, miss-pour); อาจ trigger recount ใหม่ |
| 17 | Auditor ตรวจ chain เต็ม | Auditor | Period `completed`; rollup adjustment `completed` | Auditor trace `tb_physical_count_period` → `tb_physical_count` → `tb_physical_count_detail` → rollup adjustment (`info.countId`) → `tb_inventory_transaction` → journal entry ของ GL ไม่มี gap; SoD ตรวจสอบ (Count Lead ≠ Approver) |
| 18 | Period ปิดด้วย sub-count ทั้งหมด complete | Count Lead → ระบบ | sub-`tb_physical_count` ฉบับสุดท้ายถึง `completed` | `tb_physical_count_period.status = completed` auto-transition; ไม่รับเอกสาร count เพิ่มภายใต้ period |
| 19 | Sysadmin เพิ่ม costing-method default ใหม่ | Sysadmin | Tenant เลือก `last_receiving` สำหรับ rollup ในอนาคต | Rollup ในอนาคตใช้ cost-layer ของการรับล่าสุดสำหรับ `cost_per_unit` Rollup ที่ post แล้วไม่ถูกแตะ |
| 20 | Session counter ขนานบน count เดียวกัน | Counter (A) + Counter (B) — count เดียวกัน, zone ต่างกัน | Counter สองคนพร้อม zone-grant ที่ไม่ทับซ้อนบน `tb_physical_count` เดียวกัน | ทั้งสองเขียนบรรทัด detail ของตนพร้อมกัน; ไม่ขัดแย้ง; `product_counted` เพิ่มถูกต้อง |

> **TODO:** แต่ละ row ควรเติบโตให้รวม assertion ชัดเจนบนค่าฟิลด์ `tb_*`, ข้อความ error ที่คาดหวัง และ (เมื่อ spec มี) reference บรรทัด spec E2E ปัจจุบัน row เป็นกรอบสำหรับการครอบคลุม manual / planned

## 5. E2E Spec Map

> **TODO:** ไม่มี Playwright spec ของ physical-count ที่ `../carmen-inventory-frontend-e2e/tests/` ณ `2026-05-15` เมื่อ spec แรกถูกเขียน (ชื่อไฟล์เป้าหมาย: `8XX-physical-count.spec.ts` หรือ `90X-physical-count.spec.ts` ตาม convention การกำหนดหมายเลข period-end / stock-issue) เติมหัวข้อนี้ด้วย:
> - Path ของไฟล์ spec + คำอธิบายสั้น ๆ
> - ตาราง mapping: หมายเลข scenario ข้าม persona (หัวข้อ 4) → ชื่อ test ของ spec
> - รายงาน coverage gap (scenario ใดยังคง manual vs automated)

จนกว่าจะมี coverage ให้ถือทุก scenario ในหัวข้อ 4 และไฟล์ persona เป็น **manual หรือ planned**

## 6. แหล่งอ้างอิง

- **Primary (TODO):** source carmen/docs — ไม่มีสำหรับโมดูลนี้
- **Frontend (TODO):** `../carmen-inventory-frontend-react/` — source ของพฤติกรรม UI สำหรับ assertion ของ scenario
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec physical-count
- ที่เกี่ยวข้อง: [physical-count/03-user-flow](/th/inventory/physical-count/03-user-flow) (matrix handoff ที่หน้านี้ใช้), [physical-count/02-business-rules](/th/inventory/physical-count/02-business-rules) (`PHC_VAL_*` / `PHC_AUTH_*` / `PHC_POST_*`), [inventory-adjustment/04-test-scenarios](/th/inventory/inventory-adjustment/04-test-scenarios) (scenario ฝั่ง rollup, scenario 5–6 ที่นั่นทับซ้อนกับ row 1–9 ที่นี่)
