---
title: การสุ่มตรวจ (Spot Check) — Test Scenarios
description: Test case ต่อ persona, scenario ข้าม persona และการ map ไปยัง E2E สำหรับการสุ่มตรวจ
published: true
date: 2026-05-19T23:55:00.000Z
tags: spot-check, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# การสุ่มตรวจ (Spot Check) — Test Scenarios

> **At a Glance**
> **โมดูล:** [spot-check](/th/inventory/spot-check) &nbsp;·&nbsp; **จำนวน scenario รวม:** drill-down ต่อ persona ข้ามทุก persona &nbsp;·&nbsp; **Persona ที่ครอบคลุม:** Inventory Controller, Counter, Audit / Config
> **ลำดับการรัน:** Audit / Config setup → happy path ของ persona หลัก → scenario ข้าม persona
> **Drill-down ของแต่ละ persona อยู่ที่ `04-test-scenarios-<role>.md`**

## 1. ภาพรวม

หน้านี้เป็น **จุดเริ่ม overview** สำหรับชุด test-scenario ของโมดูล `spot-check` รวมความครอบคลุมตามสามกลุ่ม persona ที่มีปฏิสัมพันธ์กับวงจรชีวิตของ spot-check (Inventory Controller, Counter, Audit / Config — ตาม [spot-check](/th/inventory/spot-check) § 4 บวก Sysadmin โดยปริยาย) ลิสต์ไฟล์ test ต่อ persona จับ scenario การ handoff ข้าม persona ที่เย็บเส้นทางบุคคลเข้าด้วยกัน และตีกรอบเป้าหมาย mapping E2E — ปัจจุบันว่างเปล่าเพราะ **ยังไม่มี Playwright spec ของ `spot-check`** ที่ `../carmen-inventory-frontend-e2e/tests/` ณ ขณะนี้ (ตรวจสอบโดย `ls tests/ | grep -i 'spot\|check'`)

ขอบเขตจงใจกว้างแม้ที่ระดับ skeleton: แต่ละไฟล์ persona ตั้งใจให้เติบโตครอบคลุม **functional happy path** (เปิด spot check ด้วยแต่ละ `method`, ป้อนการนับ, recount-and-resolve, submit, rollup post, path void), **RBAC / permission case** (Counter พยายาม submit, Inventory Controller พยายามดำเนินการข้าม location, Auditor พยายามแก้ไข), **validation** (negative test กับ `SPC_VAL_001`–`SPC_VAL_008` ที่ creation, ที่ line entry, ที่ submit, ที่ recount-flag, ที่ void), **edge case** (ศูนย์บนชั้น, บรรทัด tolerance-boundary, `method = manual` ด้วย selection ว่าง, sample size มากกว่าสินค้าที่มี) และ **configuration / audit-trail case** (ผลของการเปลี่ยน tolerance threshold, ผลของการเปลี่ยน default sampling size / method, การ inspect chain audit)

Scenario ข้าม persona ในหัวข้อ 4 อธิบายการเดินทาง end-to-end ที่ข้ามขอบเขต handoff ที่บันทึกใน [03-user-flow.md](./03-user-flow.md) หัวข้อ 4 — ตัวอย่างเช่น *Inventory Controller เปิด random spot check → Counter ทำการนับ → Inventory Controller submit → Approver / Finance อนุมัติ rollup adjustment ฝั่ง [inventory-adjustment](/th/inventory/inventory-adjustment)*; *Inventory Controller flag variance → Counter คนละคน recount → variance reconcile → submit*; *Inventory Controller submit ด้วย overage และ shortage → สร้าง rollup adjustment สองฉบับ*; *Auditor ตรวจ chain เต็มตั้งแต่ spot-check sheet ถึง journal entry*; *Spot check void ระหว่างการนับ → ไม่มีผลต่อ ledger* หัวข้อ 5 เป็น E2E spec map — ปัจจุบันเป็น TODO เป้าหมายรอ spec spot-check แรกถูกเขียน

> **TODO:** แทนที่กรอบ E2E ของ overview นี้ด้วย citation spec ที่ตรวจสอบด้วย `ls` เมื่อ `../carmen-inventory-frontend-e2e/tests/` เพิ่มความครอบคลุม spot-check จนกว่าจะถึงตอนนั้น scenario test ใน persona file เป็นการครอบคลุม manual / planned

## 2. Persona ในขอบเขต

- **Inventory Controller** — เจ้าของการดำเนินการ; ตาม [spot-check/03-user-flow-inventory-controller](/th/inventory/spot-check/03-user-flow-inventory-controller)
- **Counter** — การป้อนข้อมูลพื้นที่; ตาม [spot-check/03-user-flow-counter](/th/inventory/spot-check/03-user-flow-counter)
- **Audit / Config** — Auditor + Sysadmin (โดยปริยาย) การสังเกต การ config; ตาม [spot-check/03-user-flow-audit-config](/th/inventory/spot-check/03-user-flow-audit-config) หมายเหตุ: การอนุมัติ rollup-adjustment (Approver / Finance) ลงจอดฝั่ง [inventory-adjustment](/th/inventory/inventory-adjustment) ไม่ใช่บน spot-check โดยตรง

## 3. ไฟล์ Test ของ Persona

- [Scenario ของ Inventory Controller](./04-test-scenarios-inventory-controller.md)
- [Scenario ของ Counter](./04-test-scenarios-counter.md)
- [Scenario ของ Audit / Config](./04-test-scenarios-audit-config.md)

## 4. Scenario ข้าม Persona / Handoff

ตารางด้านล่างเป็น integration layer แต่ละ row spans handoff อย่างน้อยหนึ่งจาก [03-user-flow.md](./03-user-flow.md) หัวข้อ 4 และจบที่ระบบใน terminal หรือสถานะ steady "Persona ตามลำดับ" ลิสต์ผู้กระทำตามลำดับการ execute; "Pre-condition" จับสถานะระบบที่ต้องใช้เพื่อเริ่ม; "สถานะปลายทางที่คาดหวัง" anchor `tb_spot_check.doc_status`, ผลของ rollup adjustment (`tb_stock_in` / `tb_stock_out` เขียนผ่าน `info.spotCheckId` link ไป [inventory-adjustment](/th/inventory/inventory-adjustment)) และผลข้างเคียงข้ามโมดูล

| # | Scenario | Persona ตามลำดับ | Pre-condition | สถานะปลายทางที่คาดหวัง |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | Random-sample spot check — happy path | Inventory Controller → Counter → Inventory Controller → Approver / Finance (ฝั่ง adjustment) | Location ประเภท inventory; ไม่มี spot check ที่กำลังดำเนิน | `tb_spot_check.doc_status = completed`; เอกสาร rollup `tb_stock_in` / `tb_stock_out` post; row `tb_inventory_transaction` เขียน |
| 2 | High-value sampling — สุราพรีเมียม | Inventory Controller → Counter → Inventory Controller | Location bar มูลค่าสูง; `method = high_value`; `size = 10` | top-10 ตามมูลค่าสุ่ม; นับ; บรรทัด variance ภายใน tolerance; submit ยิง rollup |
| 3 | Manual selection — trigger โดยเหตุการณ์ | Inventory Controller → Counter → Inventory Controller | รายงานต้องสงสัย pilferage; `method = manual`; controller เพิ่มสินค้าเฉพาะ 3 รายการ | สาม row สร้างบน detail; นับ; variance post เป็น rollup adjustment พร้อม `info.spotCheckId` |
| 4 | Recount escalation — counter คนละคน | Inventory Controller → Counter (A) → Inventory Controller → Counter (B) → Inventory Controller | Counter A ป้อน `actual_qty` trigger tolerance breach ตาม `SPC_VAL_006` | บรรทัด recount แก้ไขโดย Counter B; variance reconcile ภายใน tolerance; submit ยิง rollup |
| 5 | Recount ยืนยัน variance — ยอมรับและ post | Inventory Controller → Counter (A) → Counter (B) → Inventory Controller | Recount ยืนยันการนับเดิม | Inventory Controller override พร้อม countersignature; rollup post บรรทัด variance Thread comment พกพา justification ของ override |
| 6 | ศูนย์บนชั้น vs ศูนย์นับ | Counter → Inventory Controller | บรรทัดที่ `on_hand_qty = 5`, counter ไม่เห็นอะไร | Counter ป้อน `actual_qty = 0`; `diff_qty = -5`; บรรทัด flag recount ตาม `SPC_VAL_006`; recount ยืนยัน; rollup เป็น shortage |
| 7 | บรรทัด overage | Counter → Inventory Controller | บรรทัดที่ `on_hand_qty = 10`, counter พบ 12 | `diff_qty = +2`; rollup เป็น overage ผ่าน `tb_stock_in` |
| 8 | overage + shortage ผสมใน spot check เดียวกัน | Inventory Controller → Counter → Inventory Controller | Spot check ที่มีหลาย variance บวกและลบ | เอกสาร rollup **สองฉบับ**: `tb_stock_in` หนึ่ง (บรรทัด overage), `tb_stock_out` หนึ่ง (บรรทัด shortage) ทั้งสองพกพา `info.spotCheckId` |
| 9 | Flag รายการเสียหายข้าม normal count | Counter → Inventory Controller | Counter พบรายการเสียหายบน sheet | Detail-comment flag พร้อม attachment photo; Inventory Controller review; อาจเพิ่มบรรทัดเองหรืออ้างอิงไป write-off ผ่าน [inventory-adjustment](/th/inventory/inventory-adjustment) โดยตรง |
| 10 | Counter พยายาม submit — reject (RBAC) | Counter | Counter มี location-grant; ทุกบรรทัดนับแล้ว | Action submit ไม่มีให้ Counter ตาม `SPC_AUTH_002`; Inventory Controller รับ notification ของการ complete |
| 11 | Counter พยายามป้อนการนับนอก location — reject | Counter | Counter มี location-grant สำหรับ Location A; พยายามแก้ไข spot check ของ Location B | บันทึก reject ตาม `SPC_AUTH_004` พร้อม error location-scope |
| 12 | เปลี่ยน tolerance threshold ระหว่างการดำเนินงาน | Sysadmin → Inventory Controller → Counter | Sysadmin แน่นขึ้น threshold จาก 5% เป็น 2% | spot check ใหม่หลังเปลี่ยนใช้ 2%; spot check ที่กำลังดำเนินใช้ 5% (snapshot ตอน sheet-gen) ตรวจสอบผ่านการทดสอบ tolerance spot check |
| 13 | การ post backdate rollup — reject | Inventory Controller | Period ที่บรรจุ rollup adjustment เป็น `closed` ตาม [inventory](/th/inventory/inventory) `INV_VAL_008` | Submit ของ rollup adjustment ถูก reject; Inventory Controller ต้อง escalate ไป Finance Manager เพื่อเปิด period ใหม่หรือรอ |
| 14 | Approver / Finance reject rollup adjustment | Inventory Controller → Approver / Finance → Inventory Controller | Variance ใหญ่ผิดปกติ (เช่น 50% บน SKU ติดตาม) | Rollup `tb_stock_in` / `tb_stock_out` return ไป `draft`; Inventory Controller สืบสวน (อาจ mis-count, mis-categorisation); อาจ trigger spot check ใหม่ |
| 15 | Auditor ตรวจ chain เต็ม | Auditor | Spot check `completed`; rollup adjustment `completed` | Auditor trace `tb_spot_check` → `tb_spot_check_detail` → rollup adjustment (`info.spotCheckId`) → `tb_inventory_transaction` → journal entry ของ GL ไม่มี gap; SoD ตรวจสอบ (Inventory Controller ≠ approver ของ rollup) |
| 16 | Sysadmin เปลี่ยน default sampling size | Sysadmin → Inventory Controller | Default `size` ยกขึ้นจาก 10 เป็น 25 | Random / high_value spot check ในอนาคตสร้าง 25 บรรทัดเป็น default; spot check ที่มีอยู่ไม่เปลี่ยน |
| 17 | Sysadmin เปลี่ยน default sampling method | Sysadmin → Inventory Controller | Default `method` เปลี่ยนจาก `random` เป็น `high_value` | Spot check ในอนาคตใช้ `high_value` เป็น default ยกเว้นจะ override ชัดเจนโดย controller |
| 18 | Void spot check ระหว่างการนับ | Inventory Controller | Spot check อยู่ `in_progress` ด้วยการป้อนบางส่วน | `doc_status = void`; ไม่มี rollup; การป้อนบางส่วนเก็บใน audit log; `tb_inventory_transaction` ไม่ถูกแตะ |
| 19 | Session counter ขนานบน spot check เดียวกัน | Counter (A) + Counter (B) — spot check เดียวกัน | Counter สองคนพร้อม location-grant ทับซ้อนบน `tb_spot_check` เดียวกัน | ทั้งสองเขียนบรรทัด detail พร้อมกัน; last-write-wins ต่อบรรทัด; audit log เก็บผู้เขียนทั้งสอง |
| 20 | `method = manual` ด้วย detail ว่างตอน submit | Inventory Controller | Controller ลืมเพิ่มบรรทัด detail | Submit reject ตาม `SPC_VAL_002` / `SPC_VAL_004` (`"Cannot submit — 0 lines counted."`) |

> **TODO:** แต่ละ row ควรเติบโตให้รวม assertion ชัดเจนบนค่าฟิลด์ `tb_*`, ข้อความ error ที่คาดหวัง และ (เมื่อ spec มี) reference บรรทัด spec E2E ปัจจุบัน row เป็นกรอบสำหรับการครอบคลุม manual / planned

## 5. E2E Spec Map

> **TODO:** ไม่มี Playwright spec ของ spot-check ที่ `../carmen-inventory-frontend-e2e/tests/` ณ `2026-05-15` เมื่อ spec แรกถูกเขียน (ชื่อไฟล์เป้าหมายเดา: `7XX-spot-check.spec.ts` ตาม convention การกำหนดหมายเลข stock-issue / stock-take หรือทำนองเดียวกัน) เติมหัวข้อนี้ด้วย:
> - Path ของไฟล์ spec + คำอธิบายสั้น ๆ
> - ตาราง mapping: หมายเลข scenario ข้าม persona (หัวข้อ 4) → ชื่อ test ของ spec
> - รายงาน coverage gap (scenario ใดยังคง manual vs automated)

จนกว่าจะมี coverage ให้ถือทุก scenario ในหัวข้อ 4 และไฟล์ persona เป็น **manual หรือ planned**

## 6. แหล่งอ้างอิง

- **Primary (TODO):** source carmen/docs — ไม่มีสำหรับโมดูลนี้
- **Frontend (TODO):** `../carmen-inventory-frontend/` — source ของพฤติกรรม UI สำหรับ assertion ของ scenario
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec spot-check
- ที่เกี่ยวข้อง: [spot-check/03-user-flow](/th/inventory/spot-check/03-user-flow) (matrix handoff ที่หน้านี้ใช้), [spot-check/02-business-rules](/th/inventory/spot-check/02-business-rules) (`SPC_VAL_*` / `SPC_AUTH_*` / `SPC_POST_*`), [physical-count/04-test-scenarios](/th/inventory/physical-count/04-test-scenarios) (scenario คู่เทียบการนับเต็มที่มีโครงสร้าง period สามชั้น), [inventory-adjustment/04-test-scenarios](/th/inventory/inventory-adjustment/04-test-scenarios) (scenario ฝั่ง rollup)
