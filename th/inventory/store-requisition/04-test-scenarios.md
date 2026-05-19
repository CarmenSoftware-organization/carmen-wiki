---
title: ใบเบิกของสโตร์ (Store Requisition) — Test Scenarios
description: Test case ตาม persona, scenario ข้าม persona และการ map Playwright สำหรับ store-requisition
published: true
date: 2026-05-17T12:00:00.000Z
tags: store-requisition, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:30:00.000Z
---

# ใบเบิกของสโตร์ (Store Requisition) — Test Scenarios

> **At a Glance**
> **โมดูล:** [[store-requisition]] &nbsp;·&nbsp; **scenario รวม:** ~14 ข้าม persona + การเจาะลึกต่อ persona ข้ามทุก persona &nbsp;·&nbsp; **Persona ที่ครอบคลุม:** Requester, Approver, Fulfiller, Receiver, Audit / Config
> **ลำดับ run:** Audit / Config setup → happy path persona หลัก → scenario ข้าม persona
> **การเจาะลึกของแต่ละ persona อยู่ที่ `04-test-scenarios-<role>.md`**

## 1. ภาพรวม

หน้านี้คือ **จุดเริ่มต้นภาพรวม** สำหรับชุด test-scenarios ของโมดูล `store-requisition` จัดกลุ่ม coverage ของ SR ตาม 5 persona ที่ interact กับเอกสารข้ามวงจรชีวิต (Requester, Approver, Fulfiller, Receiver, Audit / Config), inventory ไฟล์ test ต่อ persona, จับ scenario การ handoff ข้าม persona ที่ร้อยเส้นทางแต่ละเส้นเข้าด้วยกัน และ map ทุก scenario ข้าม persona กลับไปยัง Playwright spec canonical [`701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) ขอบเขตกว้างกว่า pass เชิง functional ล้วน ๆ จงใจ: แต่ละไฟล์ persona รวม **happy path เชิง functional**, **กรณี RBAC / permission-denial** (ขับโดย fixture `requestor@blueledgers.com`), **edge cases** (input ว่าง / ไม่ถูกต้อง / ใหญ่ โหมด soft vs hard ของความพร้อมต้นทาง), **test segregation-of-duties** (Requester ≠ Approver ตาม `SR_AUTH_011`, Approver ≠ Fulfiller ตาม `SR_AUTH_012`) และ **lot-tracking traces** (ข้อมูล lot persist บน `tb_inventory_transaction_detail` ที่ลิงก์ ไม่ใช่บนบรรทัด SR)

Scenario ข้าม persona ในส่วนที่ 4 คือชั้น integration เหนือชุด per-persona บรรยาย journey end-to-end ที่ข้ามขอบเขต handoff ที่บันทึกใน [03-user-flow.md](./03-user-flow.md) ส่วนที่ 4 — ตัวอย่างเช่น *Requester submit → Approver ตัด → Fulfiller commit บางส่วน → Receiver flag* ส่วนที่ 5 จึง map describe block ของ `701-sr.spec.ts` ไปยัง journey เหล่านั้นเพื่อให้ gap ใน automated coverage มองเห็นได้ในพริบตา; หมายเหตุว่า `701-sr.spec.ts` เป็นไฟล์ E2E SR **ไฟล์เดียว** — ไม่มี spec เฉพาะต่อ persona ดังนั้นไฟล์ test ต่อ persona ในส่วนที่ 3 อธิบาย scenario ที่ครอบคลุมโดย `701-sr.spec.ts` บางส่วนและระบุเป็น test แบบ manual / planned บางส่วน

## 2. Persona ในขอบเขต

- **Requester**: Outlet Manager ที่สร้างและ submit SR; ฝั่ง entry / authoring ของ flow
- **Approver**: Department Head (และ approver ระดับสูงขึ้น) ที่ review ตัด reject หรือส่งกลับบรรทัดบน SR ที่ submit แล้ว
- **Fulfiller**: Store Keeper ที่สถานที่ต้นทางที่หยิบสินค้า บันทึก `issued_qty` เลือก lot และ commit SR
- **Receiver**: ผู้แทนเอาท์เลตปลายทางที่ยืนยันการรับจริงและ flag ความคลาดเคลื่อน; **ไม่** เปลี่ยน `doc_status`
- **Audit / Config**: Inventory Controller (variance, admin void), Finance (block งวดปิด ตรวจสอบ journal-entry period close), Sysadmin (workflow / RBAC config), Auditor (trace อ่านอย่างเดียว)

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
| 1 | Happy path เต็ม — `sr_type = issue` (เบิกครัว) | Requester → Approver → Fulfiller → Receiver | สถานที่ต้นทางเป็น `tb_location.location_type = 'inventory'` พร้อม on-hand บนทุกบรรทัด; ปลายทางเป็น `direct` (ครัว); requester / approver / fulfiller เป็นผู้ใช้ต่างคน (SoD เป็นไปตาม); workflow มีขั้นอนุมัติเดียว; tenant ในโหมด hard หรือ soft `SR_VAL_009` | SR `completed`; on-hand ต้นทางลด `Σ issued_qty`; cost-centre ปลายทาง debit ผ่าน journal entry ตาม `SR_POST_007`; ข้อมูล lot persist บน `tb_inventory_transaction_detail` ที่ลิงก์; Receiver ยืนยันการรับเต็ม |
| 2 | Happy path เต็ม — `sr_type = transfer` (คลังถึงคลัง) | Requester → Approver → Fulfiller → Receiver | ต้นทางและปลายทางเป็นประเภท `inventory` ทั้งคู่; ขับโดย recipe หรือสร้างด้วยมือ; tenant config รองรับ `transfer` โดยไม่ต้องมี GRN คู่ | SR `completed`; on-hand ต้นทางลด; on-hand ปลายทางเพิ่มในปริมาณเดียวกันต่อบรรทัด; แถว stock-OUT / stock-IN คู่บน `tb_inventory_transaction`; ข้อมูล lot รักษาทั้งสองฝั่ง; Receiver ยืนยัน |
| 3 | Approver ตัดและ fulfillment บางส่วน | Requester → Approver (ตัดบรรทัดหนึ่ง) → Fulfiller (commit) → Receiver | ปริมาณที่ขอบนบรรทัดหนึ่งเกิน on-hand ต้นทางตอนอนุมัติ; approver ตัด `approved_qty` ต่ำกว่า `requested_qty` พร้อม `approved_message` | SR `completed`; `requested_qty − issued_qty > 0` บนบรรทัดที่ตัด (variance บันทึก); ลายเซ็นของ approver จับต่อบรรทัด; Receiver ยืนยันปริมาณที่ตัดเป็นการรับเต็มของสิ่งที่อนุมัติจริง |
| 4 | Send-back จาก approver, requester แก้และ resubmit | Requester → Approver (ส่งกลับ) → Requester (แก้) → Approver (อนุมัติ) → Fulfiller → Receiver | Approver พบบรรทัดที่ขาด justification หรือมีปริมาณผิดปกติ; ส่งกลับพร้อม `review_message` | SR เดิน `draft → in_progress → in_progress (ขั้น requester) → in_progress (ขั้น approver) → completed`; JSON `history` ต่อบรรทัดแสดงลำดับ send-back / amend / re-approve; ในที่สุด requester commit SR ที่แก้แล้วผ่านถึงการรับ |
| 5 | บรรทัดทั้งหมดถูก reject ตอนอนุมัติ — cancel อัตโนมัติ | Requester → Approver (reject ทุกบรรทัด) | Approver ตัดสินใจว่า SR ทั้งใบไม่มี justification (เช่น ซ้ำกับ SR active, เกินงบประมาณ, การยกเลิกฝั่งผู้ขาย) | SR `cancelled` อัตโนมัติผ่าน `SR_POST_004` tail → `SR_POST_009`; `reject_message` ต่อบรรทัดบรรจุค่า; ไม่กระทบ inventory หรือ GL; requester ถูกแจ้งต่อบรรทัด; อาจตั้ง SR ที่แก้ |
| 6 | Stock-out ตอน issue — fulfiller commit บางส่วน | Requester → Approver → Fulfiller (short-fulfill) → Receiver + Inventory Controller | ระหว่างอนุมัติกับ issue SR อื่น (หรือการบริโภคอื่น) ลด on-hand ต้นทางต่ำกว่า `approved_qty`; check `SR_VAL_013` live แสดงการขาด | SR `completed` พร้อม `issued_qty < approved_qty` บนบรรทัดที่กระทบ; `fulfilment_gap` บันทึก; system comment ต่อบรรทัด "issued X of Y; Z short due to concurrent consumption"; ยก variance event; Inventory Controller ถูกแจ้งคู่ขนาน |
| 7 | Receiver flag ความคลาดเคลื่อนปลายทางหลัง commit | Requester → Approver → Fulfiller → Receiver (flag) → Inventory Controller (resolve ผ่าน adjustment) | SR `completed`; สินค้ามาถึงปลายทางขาดจาก `issued_qty` หรือ lot ผิด; Receiver เขียน comment ความคลาดเคลื่อนพร้อมหลักฐาน | SR ยังคงเป็น `completed` (ไม่เปลี่ยนสถานะตาม `SR_POST_013`); Inventory Controller post `[[inventory-adjustment]]` ที่มี back-reference `sr_id`; on-hand ปลายทาง reconcile กับจริง; thread comment ของ SR แสดงการ resolve ความคลาดเคลื่อน |
| 8 | สินค้าควบคุม lot — multi-lot pick บนบรรทัดเดียว | Requester → Approver → Fulfiller (เลือก lot) → Receiver | สินค้าควบคุม lot; ต้นทางมี lot active หลายใบ; นโยบายการหมุนเวียน FIFO ตาม expiry | Fulfiller เลือก lot รวมเป็น `issued_qty`; การเลือก lot เขียนแถว `tb_inventory_transaction_detail` หลายแถวภายใต้ `tb_inventory_transaction` หนึ่งสำหรับบรรทัด; การ consume cost-layer เลือก `cost_per_unit` ของแต่ละ lot; Receiver ยืนยัน label lot บนสินค้าจริงตรงกับ transaction ที่ลิงก์ |
| 9 | การละเมิด segregation-of-duties ตอน commit | Requester → Approver (= Fulfiller, ผู้ใช้คนเดียว) → พยายาม commit | การผ่อนคลาย SoD ไม่ได้เปิดใช้งาน; tenant ต้องการ `Approver ≠ Fulfiller`; ผู้ใช้คนเดียวกันถือสิทธิ์ทั้งสองและพยายาม commit SR ที่อนุมัติเอง | Commit ถูก reject ตาม `SR_AUTH_012` พร้อม error message; SR ยังคงเป็น `in_progress`; fulfiller อื่น (รองหรือ escalation) ต้องเข้ารับเพื่อ complete flow |
| 10 | Block การ commit ในงวดปิด | Requester → Approver → Fulfiller (พยายาม commit) → Finance (เปิดงวดหรือ reject) | Fulfiller พยายาม commit ด้วย `last_action_at_date` ที่ map ไปยังงวดบัญชีปิด; `SR_VAL_014` block | Commit ถูก reject; SR ยังคงเป็น `in_progress`; Finance เปิดงวดใหม่ (พบยาก; ลายเซ็น CFO) หรือขอ Fulfiller เลื่อนวันที่ post ไปงวดปัจจุบัน; ถ้า reconcile ไม่ได้ Inventory Controller void เชิงบริหารและตั้ง SR ใหม่ |
| 11 | Void เชิงบริหารบน SR ก่อน commit | Requester → Inventory Controller (admin void) | Audit hold ยกบน requester ตรวจพบ SR ซ้ำ หรือการยกเลิกฝั่งผู้ขาย invalidate คำขอ; SR อยู่ที่ `draft` หรือ `in_progress` ตอนต้น | SR ย้ายเป็น `voided` ตาม `SR_POST_010`; ข้อความเหตุผลบันทึก; ไม่กระทบ inventory หรือ GL; requester ถูกแจ้ง; เอกสารจบ |
| 12 | Auto-create ที่ขับโดย recipe ผ่านวงจรชีวิตปกติ | โมดูล Recipe (auto-create) → Requester (review) → Approver → Fulfiller → Receiver | `[[recipe]]` คำนวณความต้องการวัตถุดิบสำหรับ event banquet ที่วางแผนและ post SR `draft` พร้อม back-reference `info.recipe_id`; requester เปิด ปรับถ้าจำเป็น และ submit | SR เดินวงจรชีวิต `draft → in_progress → completed` ปกติ; `info.recipe_id` รักษา end-to-end; variance เทียบกับความต้องการที่คำนวณของ recipe surface ใน variance dashboard ที่ period close |
| 13 | การ reconcile period-close | Finance | SR `completed` ทั้งหมดในงวด; รายงาน food-cost เอาท์เลตคำนวณ | Finance reconcile food-cost เอาท์เลตกับ `Σ (issued_qty × cost_per_unit)` ต่อเอาท์เลตจาก inventory transactions ที่ขับโดย SR; gap ถูกสอบสวน; งวดล็อก โมดูล SR ไม่เห็นการเปลี่ยนสถานะ; SR ถัดไปที่มีวันที่ post ในงวดปิดถูก block โดย `SR_VAL_014` |
| 14 | การเปลี่ยน config Workflow / RBAC | Sysadmin → ทุก persona | Tenant ตัดสินใจเพิ่ม approval tier ที่สองเหนือ ฿10,000 หรือผ่อนคลาย threshold SoD สำหรับ SR มูลค่าต่ำ | Sysadmin commit การเปลี่ยน `tb_workflow`; กฎใหม่ apply prospective กับ SR ถัดไป; SR ที่อยู่ใน flow ถูก re-route ตามการประสาน Sysadmin / Inventory Controller; ไม่มีการเปลี่ยนสถานะ SR จากตัว config เอง |

## 5. การ Map E2E Test

`701-sr.spec.ts` เป็นไฟล์ Playwright E2E **ไฟล์เดียว** สำหรับโมดูล SR มันโครงสร้างเป็นไฟล์เดียวที่มี `describe` block หลายตัวต่อพื้นที่ functional; auth เป็น multi-role ผ่าน `createAuthTest` โดยมี `purchase@blueledgers.com` สำหรับเส้นทาง happy / functional (Requester / Approver / Fulfiller equivalent ใน test) และ `requestor@blueledgers.com` สำหรับกรณี permission-denial **ไม่มี spec เฉพาะต่อ persona** — ไฟล์ test ต่อ persona ที่ลิงก์ในส่วนที่ 3 catalogue scenario; บางส่วนครอบคลุมโดย describe block ของ `701-sr.spec.ts` ด้านล่าง อื่น ๆ ยังคงเป็น manual / planned

| describe block ของ `701-sr.spec.ts` (กลุ่ม TC) | Scenario ข้าม persona ที่ครอบคลุม (ส่วนที่ 4) |
| ------------------------------------------- | --------------------------------------- |
| `Store Requisition — Create` (TC-SR-900001 / 010001–010005) | 1, 2, 11 (จุดเข้าสำหรับ flow สร้างของ requester; กรณี permission-denial `requestor@blueledgers.com`) |
| `Store Requisition — Create — Permission denial` (TC-SR-010002) | ชั้น RBAC; requester ที่ไม่ได้กำหนดให้ department ถูก block ตอนสร้าง |
| `Store Requisition — Add Items` (TC-SR-900002 / 020001–020003) | 1, 2, 3 (การป้อนบรรทัด; ปริมาณไม่ถูกต้อง / สต๊อกไม่พอ กรณี soft / hard) |
| `Store Requisition — Real-time Inventory` (TC-SR-900003 / 030001–030004) | 1, 6 (source availability check `SR_VAL_009` ตอน submit + `SR_VAL_013` ตอน commit) |
| `Store Requisition — Save & Auto-save` (TC-SR-900004 / 040001–040005) | 1, 4 (draft persistence; resume หลัง send-back) |
| `Store Requisition — Submit` (TC-SR-900005 / 050001–050005) | 1, 2, 11 (gate ตอน submit; permission-denial; emergency flag) |
| `Store Requisition — Approver list actions` (TC-SR-900006 / 060001–060005) | 1, 3, 4, 5 (การ navigate queue ของ approver; bulk action; delegation) |
| `Store Requisition — Approve` (TC-SR-900007 / 070001–070003) | 1 (อนุมัติเต็ม); 9 (approver ไม่ได้รับอนุญาต — ใกล้ SoD); warning เกินงบประมาณ |
| `Store Requisition — Approve Item-level` (TC-SR-900008 / 080001+) | 3, 5 (approve / trim / reject ต่อบรรทัด); permission-denial ผ่าน `requestor@blueledgers.com` |
| `Store Requisition — Adjust approved quantity` (TC-SR-900009 / 090001+) | 3 (approver ตัดลงจาก `requested_qty`) |
| `Store Requisition — Request Review` (TC-SR-900010 / 100001+) | 4 (send-back เพื่อแก้ไขพร้อม `review_message`) |
| `Store Requisition — Reject` (TC-SR-900011 / 110001+) | 5 (บรรทัดทั้งหมด reject → cancelled) |
| `Store Requisition — Issuance` (TC-SR-900012 / 120001+) | 1, 2, 6, 8 (commit ของ fulfiller; partial fulfillment; multi-lot pick) |
| (ไม่มี block เฉพาะสำหรับการยืนยันของ Receiver) | Scenario 7 (ความคลาดเคลื่อนของ Receiver) ระบุเป็น manual / planned ปัจจุบัน |
| (ไม่มี block เฉพาะสำหรับ period close หรือ admin void) | Scenarios 10, 11, 13, 14 (flow Audit / Config) ระบุเป็น manual / planned |

Gap เทียบกับส่วนที่ 4: Scenarios 7 (ความคลาดเคลื่อนของ Receiver end-to-end), 10 (การ resolve block การ commit งวดปิด), 11 (void เชิงบริหารพร้อม event chain เต็ม), 12 (auto-create ที่ขับโดย recipe), 13 (การ reconcile period-close) และ 14 (การเปลี่ยน config workflow / RBAC) ยังไม่ครอบคลุมโดย `701-sr.spec.ts` และอยู่เป็นกรณี manual / planned ในไฟล์ persona (เป็นหลักภายใต้ [04-test-scenarios-audit-config.md](./04-test-scenarios-audit-config.md) และ [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md))

## 6. แหล่งอ้างอิง

- [`../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) — Playwright E2E spec canonical (multi-role auth, ทุกกลุ่ม TC-SR-9xxxxx)
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4 — handoff ข้าม persona ที่ขับเคลื่อน scenario integration ข้างบน
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 — กฎ posting และกฎ SoD ที่ถูก invoke ที่ transition `in_progress → completed` และข้าม handoff อนุมัติ
- รายละเอียดต่อ persona: [Requester](./04-test-scenarios-requester.md), [Approver](./04-test-scenarios-approver.md), [Fulfiller](./04-test-scenarios-fulfiller.md), [Receiver](./04-test-scenarios-receiver.md), [Audit / Config](./04-test-scenarios-audit-config.md)
