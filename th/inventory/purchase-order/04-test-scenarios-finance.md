---
title: ใบสั่งซื้อ (Purchase Order) — Test Scenarios — Finance
description: เหตุผลที่ไม่มี test scenarios แบบ three-way-match / AP สำหรับ purchase-order ในซอร์สโค้ดปัจจุบัน และสิ่งที่ยืนยันได้แทน
published: true
date: 2026-07-15T12:00:00.000Z
tags: purchase-order, test-scenarios, finance, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# ใบสั่งซื้อ (Purchase Order) — Test Scenarios — Finance

> **At a Glance**
> **Persona:** Finance — **ยังไม่ยืนยันว่าเป็น persona แยกต่างหากในซอร์สโค้ดปัจจุบัน** &nbsp;·&nbsp; **Module:** [purchase-order](/th/inventory/purchase-order)
> **E2E coverage:** ไม่มีที่ยืนยันได้ เวอร์ชันก่อนหน้าของหน้านี้อ้างถึง `403-po-finance-ap-match.spec.ts` ซึ่ง **ไม่มีอยู่จริง** ใน `../carmen-inventory-frontend-e2e/tests/`

> ⚠️ **แก้ไขครั้งใหญ่ในรอบนี้** เวอร์ชันก่อนหน้าของหน้านี้ระบุ ~25 scenarios (FIN-HP-01 ถึง FIN-EDGE-05) ครอบคลุมขั้นตอน Finance Manager sign-off ก่อน transmission และ flow three-way-match / AP-posting ของ Finance Officer รวมถึง GL account entries เฉพาะ, การจัดการ purchase-price-variance, และ FX-adjustment postings ทั้งหมดนี้ไม่ตรงกับซอร์สโค้ดปัจจุบัน:
> - Spec file ที่อ้างถึงคือ `403-po-finance-ap-match.spec.ts` ถูกตรวจสอบโดยตรงและ **ไม่มีอยู่จริง** ในไดเรกทอรี e2e test นั่นหมายความว่าทุกคำกล่าวอ้างเรื่อง "E2E coverage" บน scenarios ที่ถูกตัดออกนั้นถูกสร้างขึ้นเองพร้อมกับฟีเจอร์ที่ไม่มีจริง
> - การค้นทั่ว repo ของ `carmen-turborepo-backend-v2` และ `carmen-inventory-frontend-react` สำหรับ `three-way`, `vendor_invoice`, `VendorInvoice`, และ `tb_invoice` ไม่พบผลลัพธ์ใด ๆ เลย
> - ดู [03-user-flow-finance.md](./03-user-flow-finance.md) สำหรับคำแก้ไขฉบับเต็มและหลักฐานที่ตรวจสอบ
>
> หน้านี้ยังคงเก็บไว้ ไม่ได้ลบทิ้ง เพื่อบันทึกคำแก้ไขและชี้ไปยังสิ่งที่มีอยู่จริง ไม่มีการสร้างตาราง scenario ขึ้นมาใหม่ที่นี่ เพราะไม่มีฟีเจอร์ที่ยืนยันได้ให้เขียน test scenario เทียบด้วย

## สิ่งที่ถูกตัดออกและเหตุผล

| กลุ่ม scenario ที่ถูกตัดออก | เหตุผล |
|---|---|
| FIN-HP-01 ถึง FIN-HP-06 (sign-off ก่อน transmission, three-way match, PPV, FX adjustment, GL postings) | ไม่พบโค้ด invoice-capture, AP-posting, หรือ match-algorithm ใด ๆ ในซอร์สโค้ดปัจจุบัน |
| FIN-PERM-01 ถึง FIN-PERM-07 | ขึ้นอยู่กับฟีเจอร์ AP/invoice ที่ไม่มีจริงทั้งหมด และ stage role `finance` ที่ไม่มีอยู่ใน `enum_stage_role` |
| FIN-VAL-01 ถึง FIN-VAL-07 | เช่นเดียวกัน — กฎ validation สำหรับฟีเจอร์ที่ไม่ได้ implement |
| FIN-EDGE-01 ถึง FIN-EDGE-05 | เช่นเดียวกัน |

## สิ่งที่ยืนยันได้แทน

- User คนใดก็ได้ (ไม่ว่าจะมีตำแหน่งอะไร) สามารถถูก assign ไปยัง generic `approve` workflow stage ได้ — ดู [04-test-scenarios-procurement-manager.md](./04-test-scenarios-procurement-manager.md) สำหรับกลไกที่ยืนยันได้จริงและอิง e2e ของ stage approval, send-back, และ reject Tenant อาจตั้งชื่อ user ที่ assign ไปยัง stage นั้นว่า "Finance Manager" ก็ได้ แต่ไม่มีโค้ดใดปฏิบัติต่อพวกเขาต่างจาก approver คนอื่น
- [Credit Note](/th/inventory/purchase-order/credit-note) เป็นเอกสารที่ implement จริงและใกล้เคียง AP โดยมี Prisma tables และ routes ที่ยืนยันได้ มันโพสต์ AP debit memo กับ GRN ก่อนหน้า ไม่ใช่ three-way match และไม่มีหน้า test-scenario เฉพาะในโมดูลนี้ (เป็นเอกสารพี่น้องคนละชนิด ไม่ใช่ persona ของโมดูล PO)

## แหล่งอ้างอิง

- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) — คำแก้ไขฉบับเต็ม รวมถึงการค้นที่รันจริงและผลลัพธ์ที่ได้
- Sibling: [04-test-scenarios-procurement-manager.md](./04-test-scenarios-procurement-manager.md) — กลไก generic approval-stage ที่ยืนยันได้จริงและอิง e2e
- [Credit Note](/th/inventory/purchase-order/credit-note) — ฟีเจอร์ AP-adjacent เดียวที่มีอยู่จริงในโมดูลนี้
- กฎทางธุรกิจ: [02-business-rules.md](./02-business-rules.md) § 5 (`PO_POST_008` / `PO_POST_009`, ระบุว่ายังไม่ implement), § 6 (`PO_XMOD_007`, ระบุว่ายังไม่ implement)
