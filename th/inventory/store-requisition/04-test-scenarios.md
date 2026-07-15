---
title: ใบเบิกของสโตร์ (Store Requisition) — Test Scenarios
description: Test case ตาม persona, scenario ข้าม persona และการ map Playwright สำหรับ store-requisition
published: true
date: 2026-07-15T12:00:00.000Z
tags: store-requisition, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:30:00.000Z
---

# ใบเบิกของสโตร์ (Store Requisition) — Test Scenarios

> **At a Glance**
> **โมดูล:** [store-requisition](/th/inventory/store-requisition) &nbsp;·&nbsp; **Scenario รวม:** scenario ข้าม persona (แก้ไขรอบนี้ หลายรายการถูกลบเพราะยังไม่ยืนยัน) + การเจาะลึกต่อ persona &nbsp;·&nbsp; **Persona ที่ครอบคลุม:** Requester, Approver, Fulfiller ยืนยันแล้ว; "Receiver" และ "Audit / Config" ยังไม่ยืนยัน (เป็น correction stub)
> **ลำดับ run:** happy path ของ persona หลัก → scenario ข้าม persona
> **การเจาะลึกของแต่ละ persona อยู่ที่ `04-test-scenarios-<role>.md`**

## 1. ภาพรวม

หน้านี้คือ **จุดเริ่มต้นภาพรวม** สำหรับชุด test-scenarios ของโมดูล `store-requisition` จัดกลุ่ม coverage ของ SR ตาม persona ที่ interact กับเอกสารข้ามวงจรชีวิต, inventory ไฟล์ test ต่อ persona, จับ scenario การ handoff ข้าม persona ที่ร้อยเส้นทางแต่ละเส้นเข้าด้วยกัน และ map ทุก scenario ข้าม persona กลับไปยัง Playwright spec canonical [`701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) ขอบเขตกว้างกว่า pass เชิง functional ล้วน ๆ จงใจ: แต่ละไฟล์ persona รวม **happy path เชิง functional**, **กรณี RBAC / permission-denial** (ขับโดย fixture `requestor@blueledgers.com`) และ **edge cases** (input ว่าง / ไม่ถูกต้อง / ใหญ่ โหมด soft vs hard ของความพร้อมต้นทาง)

> ⚠️ **แก้ไขรอบนี้** สามกลุ่มข้อกล่าวอ้างที่ปรากฏในทุกไฟล์ persona ถูกตรวจสอบกับ `store-requisition.service.ts`, `store-requisition.logic.ts` และ frontend แล้วพบว่ายังไม่ยืนยัน: (1) **segregation of duties** — ไม่มีการ cross-check `requestor_id` / `approved_by_id` ใด ๆ ใน SR service ดังนั้น scenario "Requester ≠ Approver" และ "Approver ≠ Fulfiller" ไม่ใช่ control ที่บังคับใช้จริง; (2) **`cancelled` เป็นสถานะที่ไปถึงได้** — ไม่มี service method ใดกำหนดค่านี้เลย เส้นทางการยกเลิกที่ยืนยันได้เส้นเดียวคือ action `reject` ทั้งเอกสารซึ่งตั้งเป็น `voided` ใช้ได้โดยผู้ที่ถือขั้น workflow ปัจจุบัน (ไม่ใช่ "void" เฉพาะ admin); (3) **การเลือก lot ด้วยมือ, multi-tier value-threshold escalation, approval delegation, SLA time-out escalation, การเชื่อมโมดูล budget, การ post GL/journal-entry และการ block commit ในงวดปิด** — ไม่พบสิ่งใดใน source ปัจจุบัน (การกำหนด lot เป็น FIFO อัตโนมัติ; ที่เหลือค้นหาแล้วไม่พบ `threshold`, `delegat`, `journal`, `ledger`, `period` หรือ route ของ budget เลย) แถวด้านล่างถูกแก้ไข in place; ดู [01-data-model.md](./01-data-model.md) §5 และ [02-business-rules.md](./02-business-rules.md) สำหรับรายละเอียดเต็ม

Scenario ข้าม persona ในส่วนที่ 4 คือชั้น integration เหนือชุด per-persona บรรยาย journey end-to-end ที่ข้ามขอบเขต handoff ที่บันทึกใน [03-user-flow.md](./03-user-flow.md) ส่วนที่ 4 ส่วนที่ 5 จึง map describe block ของ `701-sr.spec.ts` ไปยัง journey เหล่านั้นเพื่อให้ gap ใน automated coverage มองเห็นได้ในพริบตา; หมายเหตุว่า `701-sr.spec.ts` เป็นไฟล์ E2E SR **ไฟล์เดียว** — ไม่มี spec เฉพาะต่อ persona ดังนั้นไฟล์ test ต่อ persona ในส่วนที่ 3 อธิบาย scenario ที่ครอบคลุมโดย `701-sr.spec.ts` บางส่วนและระบุเป็น test แบบ manual / planned บางส่วน

## 2. Persona ในขอบเขต

- **Requester**: Outlet Manager ที่สร้างและ submit SR; ฝั่ง entry / authoring ของ flow เป็นเจ้าของเส้นทางถอน soft-delete เฉพาะ `draft`
- **Approver**: ผู้ที่ถือขั้น workflow ที่ tag `enum_stage_role.approve` (โดยทั่วไปมีตำแหน่ง Department Head) ที่ review ตัด reject หรือส่งกลับบรรทัดบน SR ที่ submit แล้วผ่าน endpoint ทั่วไป `/approve` และ `/review`
- **Fulfiller**: ผู้ที่ถือขั้น workflow ที่ tag `enum_stage_role.issue` (โดยทั่วไปมีตำแหน่ง Store Keeper) ที่บันทึก `issued_qty` ผ่าน endpoint ทั่วไป `/approve` เดียวกับที่ Approver ใช้ Lot ถูกกำหนดแบบ FIFO อัตโนมัติ
- **"Receiver"** และ **"Audit / Config" (Inventory Controller / Finance / Sysadmin / Auditor)**: **ยังไม่ยืนยันว่าเป็น persona แยก** — ไม่พบ route, สมาชิก `enum_stage_role` หรือ feature ที่ตรงกัน (discrepancy flag, admin-void console, GL verification, RBAC/threshold config) ใน source ปัจจุบัน หน้า test-scenario ของทั้งสองเป็น correction stub — ดู [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) และ [04-test-scenarios-audit-config.md](./04-test-scenarios-audit-config.md)

## 3. ไฟล์ Test ต่อ Persona

- [Requester scenarios](./04-test-scenarios-requester.md)
- [Approver scenarios](./04-test-scenarios-approver.md)
- [Fulfiller scenarios](./04-test-scenarios-fulfiller.md)
- [Receiver scenarios](./04-test-scenarios-receiver.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Scenario ข้าม Persona / Handoff

ตารางด้านล่างคือชั้น integration แต่ละแถวข้าม handoff อย่างน้อยหนึ่งจุดจาก [03-user-flow.md](./03-user-flow.md) ส่วนที่ 4 และจบที่เอกสารในสถานะจุดสิ้นสุดหรือ steady state "Persona ตามลำดับ" ระบุผู้กระทำตามลำดับ execution; "Pre-condition" จับสถานะระบบที่ต้องการก่อนเริ่ม; "End state ที่คาดหวัง" anchor `doc_status` ของ SR และผลกระทบปลายน้ำ (inventory, GL)

| # | Scenario | Persona ตามลำดับ | Pre-condition | End state ที่คาดหวัง |
| - | -------- | ----------------- | ------------- | -------------------- |
| 1 | Happy path เต็ม — `sr_type = issue` (เบิกครัว) | Requester → Approver → Fulfiller | สถานที่ต้นทางเป็น `tb_location.location_type = 'inventory'` พร้อม on-hand บนทุกบรรทัด; ปลายทางเป็น `direct` (ครัว); workflow มีขั้น approve-tag หนึ่งขั้นบวกขั้น issue-tag หนึ่งขั้น | SR `completed`; on-hand ต้นทางลดลงตาม `Σ issued_qty`; on-hand ปลายทางคงที่ 0 (ถูกคิดเป็นค่าใช้จ่ายทันทีตาม branch destination-direct ของ `executeTransfer`); ข้อมูล lot กำหนดอัตโนมัติ (FIFO) บน `tb_inventory_transaction_detail` ที่ลิงก์ การ post GL/journal-entry ยังไม่ยืนยัน — ดู `SR_POST_007` |
| 2 | Happy path เต็ม — `sr_type = transfer` (คลังถึงคลัง) | Requester → Approver → Fulfiller | ต้นทางและปลายทางเป็นประเภท `inventory` ทั้งคู่; ขับโดย recipe หรือสร้างด้วยมือ | SR `completed`; on-hand ต้นทางลดลง; on-hand ปลายทางเพิ่มในปริมาณเดียวกันต่อบรรทัดผ่าน `executeTransfer`; ข้อมูล lot กำหนดอัตโนมัติทั้งสองฝั่ง |
| 3 | Approver ตัดและ fulfillment บางส่วน | Requester → Approver (ตัดบรรทัดหนึ่ง) → Fulfiller | ปริมาณที่ขอบนบรรทัดหนึ่งเกิน on-hand ต้นทางตอนอนุมัติ; approver ตัด `approved_qty` ต่ำกว่า `requested_qty` พร้อม `approved_message` | SR `completed`; `requested_qty − issued_qty > 0` บนบรรทัดที่ตัด (variance คำนวณได้จากสามคอลัมน์ปริมาณที่เก็บไว้ ไม่ใช่ metric ที่ persist); ลายเซ็นของ approver จับต่อบรรทัด |
| 4 | Send-back จาก approver, requester แก้และ resubmit | Requester → Approver (ส่งกลับผ่าน `/review`) → Requester (แก้) → Approver (อนุมัติ) → Fulfiller | Approver พบบรรทัดที่ขาด justification หรือมีปริมาณผิดปกติ; ส่งกลับทั้งเอกสารพร้อม `review_message` (ผสมกับการตัดสินใจ approve/reject บนบรรทัดอื่นในการเรียกเดียวกันไม่ได้) | SR เดิน `draft → in_progress → in_progress (ขั้น requester) → in_progress (ขั้น approver) → completed`; JSON `history` ต่อบรรทัดแสดงลำดับ send-back / amend / re-approve |
| 5 | การ reject ทั้งเอกสาร — แก้ไขรอบนี้ เดิมคือ "บรรทัดทั้งหมดถูก reject → cancel อัตโนมัติ" | Requester → Approver (mark ทุกบรรทัด reject จากนั้นเรียก `/reject` ทั้งเอกสาร) | Approver ตัดสินใจว่า SR ทั้งใบไม่มี justification | `doc_status = voided` ของ SR (ไม่ใช่ `cancelled` — `cancelled` ไม่เคยถูกกำหนดโดย service method ใดในปัจจุบัน); `reject_message` ต่อบรรทัดถูกบรรจุค่า; ไม่กระทบ inventory; requester ถูกแจ้ง การ reject ทุกบรรทัดไม่ *อัตโนมัติ* ทำให้เอกสาร void — `/reject` ทั้งเอกสารเป็นการเรียกแยกต่างหากที่ approver ต้องเรียกเอง |
| 6 | Stock-out ตอน issue — fulfiller บันทึกบางส่วน | Requester → Approver → Fulfiller (short-issue) | ระหว่างอนุมัติกับ issue การบริโภคอื่นลด on-hand ต้นทางต่ำกว่า `approved_qty`; check `SR_VAL_013` live แสดงส่วนที่ขาด | SR `completed` พร้อม `issued_qty < approved_qty` บนบรรทัดที่กระทบ; ช่องว่างคำนวณได้จากคอลัมน์ที่เก็บไว้; ข้อความ system-comment เฉพาะที่บรรยายในเวอร์ชันก่อนหน้าของหน้านี้ยังไม่ได้รับการยืนยันโดยตรง |
| 7 | ~~Receiver flag ความคลาดเคลื่อนปลายทางหลัง commit~~ — แก้ไขรอบนี้ | — | — | **ถูกลบ** ไม่พบหน้าจอสำหรับ receiver, ประเภท comment ความคลาดเคลื่อน หรือ escalation route ใด ๆ ใน source ปัจจุบัน; ดู [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) ผู้ใช้ใดก็ได้ที่มีสิทธิ์อ่าน SR `completed` สามารถทิ้ง comment ทั่วไปได้ — นั่นคือพื้นผิว annotation หลัง commit เดียวที่ยืนยันได้ |
| 8 | สินค้าควบคุม lot — การ consume multi-lot บนบรรทัดเดียว | Requester → Approver → Fulfiller (เดินขั้น workflow สุดท้าย) | สินค้าควบคุม lot; ต้นทางมี lot active หลายใบ | **แก้ไขรอบนี้:** การเลือก lot ไม่ใช่ action ของ Fulfiller `createFifoConsumption()` / `getAvailableFifoLots()` / `consumeFifoLots()` ใน `inventory-transaction.service.ts` กำหนด lot อัตโนมัติแบบ FIFO ที่การเดินขั้น workflow สุดท้าย; อาจเกิดแถว `tb_inventory_transaction_detail` หลายแถวภายใต้ `tb_inventory_transaction` เดียว แต่ไม่มี lot-selection UI ใน SR frontend |
| 9 | ~~การละเมิด segregation-of-duties ตอน commit~~ — แก้ไขรอบนี้ | — | — | **ถูกลบในฐานะ scenario "reject" ที่ test ได้** ไม่มีการ cross-check `requestor_id` / `approved_by_id` ใน `store-requisition.service.ts` หรือ `store-requisition.logic.ts` — ผู้ใช้คนเดียวกันสามารถ request, approve และ issue SR เดียวกันได้โดยไม่มี block ระดับ code ใด ๆ ให้ถือว่า SoD ยังไม่ถูกบังคับใช้จนกว่าจะพบ check |
| 10 | ~~Block การ commit ในงวดปิด~~ — แก้ไขรอบนี้ | — | — | **ถูกลบ** การค้นหาทั่ว repo ใน `store-requisition.service.ts`, `store-requisition.logic.ts` และ SR DTOs สำหรับ `period` ไม่พบผลลัพธ์เลย; ไม่มีกลไกที่ยืนยันได้ที่ block การเดินขั้นสุดท้ายเพราะงวดบัญชีปิด (`SR_VAL_014`) |
| 11 | ~~Void เชิงบริหารบน SR ก่อน commit~~ — แก้ไขรอบนี้ | ผู้ที่ถือขั้น workflow ปัจจุบัน | SR ที่ `in_progress` (ไม่จำกัดเฉพาะ `draft` หรือ `in_progress` "ช่วงต้น" — precondition เดียวของ reject method คือ `doc_status = in_progress`) | SR ย้ายเป็น `voided` ผ่านการเรียก `/reject` ทั้งเอกสารเดียวกันที่ผู้กระทำขั้นปัจจุบันคนใดก็เรียกได้ (`StoreRequisitionService.reject()`) — ไม่มี endpoint "admin void" แยกต่างหากที่จำกัดเฉพาะ Inventory Controller / System Administrator SR ที่ `draft` ไม่สามารถ reject แบบนี้ได้; เส้นทางลบก่อน submit เดียวของมันคือ soft-delete ของ requester เอง |
| 12 | Auto-create ที่ขับโดย recipe ผ่านวงจรชีวิตปกติ | โมดูล Recipe (auto-create) → Requester (review) → Approver → Fulfiller | `[recipe](/th/inventory/recipe)` คำนวณความต้องการวัตถุดิบสำหรับ event banquet ที่วางแผนและ post SR `draft` พร้อม back-reference `info.recipe_id`; requester เปิด ปรับถ้าจำเป็น และ submit | SR เดินวงจรชีวิต `draft → in_progress → completed` ปกติ; `info.recipe_id` รักษา end-to-end ฝั่งการ trigger ของ recipe ใน scenario นี้เป็นของ resync pass ของโมดูล recipe เอง ไม่ได้ re-verify ที่นี่ |
| 13 | ~~การ reconcile period-close~~ — แก้ไขรอบนี้ | — | — | **ถูกลบ** scenario นี้ขึ้นกับ gate งวดปิด (Scenario 10) และการ post GL/journal-entry ซึ่งไม่พบทั้งคู่ใน source ปัจจุบัน |
| 14 | ~~การเปลี่ยน config Workflow / RBAC~~ — แก้ไขรอบนี้ | — | — | **แคบลง** `tb_workflow` เป็นตารางจริงที่ tenant config ได้ ใช้ร่วมกับ PR/PO/GRN — การเปลี่ยน stage definitions เป็น action config workflow ทั่วไป ไม่ใช่ feature เฉพาะ SR ไม่พบฟิลด์ value-threshold หรือ SoD-relaxation-threshold เฉพาะ SR ให้ config |

## 5. การ Map E2E Test

`701-sr.spec.ts` เป็นไฟล์ Playwright E2E **ไฟล์เดียว** สำหรับโมดูล SR มันโครงสร้างเป็นไฟล์เดียวที่มี `describe` block หลายตัวต่อพื้นที่ functional; auth เป็น multi-role ผ่าน `createAuthTest` โดยมี `purchase@blueledgers.com` สำหรับเส้นทาง happy / functional (Requester / Approver / Fulfiller equivalent ใน test) และ `requestor@blueledgers.com` สำหรับกรณี permission-denial **ไม่มี spec เฉพาะต่อ persona** — ไฟล์ test ต่อ persona ที่ลิงก์ในส่วนที่ 3 catalogue scenario; บางส่วนครอบคลุมโดย describe block ของ `701-sr.spec.ts` ด้านล่าง อื่น ๆ ยังคงเป็น manual / planned

| describe block ของ `701-sr.spec.ts` (กลุ่ม TC) | Scenario ข้าม persona ที่ครอบคลุม (ส่วนที่ 4) |
| ------------------------------------------- | --------------------------------------- |
| `Store Requisition — Create` (TC-SR-010001–010005) | 1, 2 (จุดเข้าสำหรับ flow สร้างของ requester) |
| `Store Requisition — Create — Permission denial` (TC-SR-010002) | ชั้น RBAC; requester ที่ไม่ได้กำหนดให้ department ถูก block ตอนสร้าง |
| `Store Requisition — Add Items` (TC-SR-020001–020003) | 1, 2, 3 (การป้อนบรรทัด; ปริมาณไม่ถูกต้อง / สต๊อกไม่พอ กรณี soft / hard) |
| `Store Requisition — Real-time Inventory` (TC-SR-030001–030004) | 1, 6 (source availability check `SR_VAL_009` ตอน submit + `SR_VAL_013` ที่ขั้นสุดท้าย) |
| `Store Requisition — Save & Auto-save` (TC-SR-040001–040005) | 1, 4 (draft persistence; resume หลัง send-back) |
| `Store Requisition — Submit` (TC-SR-050001–050005) | 1, 2 (gate ตอน submit) |
| `Store Requisition — Approver list actions` (TC-SR-060001–060005) | 1, 3, 4 (การ navigate queue ของ approver; bulk action) |
| `Store Requisition — Approve` (TC-SR-070001–070003) | 1 (อนุมัติเต็ม); test annotation บรรยาย warning เกินงบประมาณที่ยังไม่ยืนยันกับ source ปัจจุบัน — ดู [04-test-scenarios-approver.md](./04-test-scenarios-approver.md) |
| `Store Requisition — Approve Item-level` (TC-SR-080001+) | 3, 4 (approve / trim / reject ต่อบรรทัด); permission-denial ผ่าน `requestor@blueledgers.com` |
| `Store Requisition — Adjust approved quantity` (TC-SR-090001+) | 3 (approver ตัดลงจาก `requested_qty`) |
| `Store Requisition — Request Review` (TC-SR-100001+) | 4 (send-back เพื่อแก้ไขพร้อม `review_message`) |
| `Store Requisition — Reject` (TC-SR-110001+) | 5 (การ reject ทั้งเอกสาร → `voided`; ข้อความสถานะ "Rejected" / "Partially Rejected" ใน test annotation เป็น test-plan copy เชิงตัวอย่าง ยังไม่ยืนยันกับ `enum_doc_status` ของ Prisma) |
| `Store Requisition — Issuance` (TC-SR-120001+) | 1, 2, 6, 8 (การเดินขั้นสุดท้าย; การ issue บางส่วน; การ consume multi-lot) |
| (ไม่มี block เฉพาะ) | Scenario 7 (Receiver) และ Scenarios 9, 10, 11, 13, 14 (SoD / งวดปิด / admin-void / period-close / RBAC-config) ถูกลบหรือแคบลงรอบนี้เนื่องจากยังไม่ยืนยันกับ source ปัจจุบัน — ดูส่วนที่ 4 |

Gap เทียบกับส่วนที่ 4 ที่แก้ไขแล้ว: Scenario 12 (auto-create ที่ขับโดย recipe โดยเฉพาะฝั่ง trigger ของ recipe) ไม่ครอบคลุมโดย `701-sr.spec.ts` และยังคงเป็น manual / planned

## 6. แหล่งอ้างอิง

- [`../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) — Playwright E2E spec canonical (multi-role auth, ทุกกลุ่ม TC-SR-0xxxxx)
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4 — handoff ข้าม persona ที่ขับเคลื่อน scenario integration ข้างบน
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 — กฎ posting ที่ถูก invoke ที่การเดินขั้น workflow สุดท้ายและข้าม handoff การอนุมัติ
- รายละเอียดต่อ persona: [Requester](./04-test-scenarios-requester.md), [Approver](./04-test-scenarios-approver.md), [Fulfiller](./04-test-scenarios-fulfiller.md), [Receiver](./04-test-scenarios-receiver.md), [Audit / Config](./04-test-scenarios-audit-config.md)
