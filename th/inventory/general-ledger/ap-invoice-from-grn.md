---
title: AP Invoice จาก GRN (AP Invoice from GRN)
description: AP invoice ที่สร้างจากบรรทัด GRN ที่ commit แล้ว: candidates, matched_qty, voucher Dr inventory / Dr input VAT / Cr AP, การล็อกแก้ไข GRN และการ export Dr/Cr ภายนอกแยกต่างหาก
published: true
date: '2026-10-27T15:00:00.000Z'
tags: general-ledger, accounts-payable, grn, inventory, carmen-software
editor: markdown
dateCreated: '2026-10-27T00:00:00.000Z'
---

# AP Invoice จาก GRN

> **At a Glance**
> **ข้อสรุป (backend `c9d788829`, 2026-10-27):** GRN ยังคงไม่โพสต์อะไรด้วยตัวเอง ledger ถูกเข้าถึง **หลังจากนั้นอีกหนึ่งขั้น** โดย **AP invoice** (`tb_ap_invoice`, `doc_source = grn`) ที่ดึงบรรทัด GRN ที่ commit แล้วและ `post_type = ap` และเมื่ออนุมัติขั้นสุดท้ายจะโพสต์ voucher หนึ่งใบ (`source = ap`, `source_ref_type = ap_invoice`) ผ่าน subledger facade &nbsp;·&nbsp; **ทิศทางการพึ่งพา:** บรรทัด GRN คือ *ต้นทาง*; AP invoice บันทึกว่าจับคู่แต่ละบรรทัดไปแล้วเท่าใด (`tb_ap_invoice_detail_source.matched_qty`) และ GRN ที่อยู่บน AP invoice ที่ยังใช้งานอยู่จะแก้ไขไม่ได้อีก &nbsp;·&nbsp; **สต๊อกและต้นทุนไม่ถูกแตะ:** ไม่มีสิ่งใดที่นี่เขียน `tb_inventory_transaction*` หรือ cost layer; invoice สร้างเพียงเจ้าหนี้ &nbsp;·&nbsp; **UI:** ยังไม่มี - หน้าจอ AP ของ React ทำงานบน mock ในเบราว์เซอร์ (ดู [General Ledger](/th/inventory/general-ledger) § 4) &nbsp;·&nbsp; **Permission:** `accounting.ap` (licence feature, สถานะ `inactive` ใน seed); มีเพียง `void` ที่มี `@Permission` แบบ static

## 1. ขอบเขต

หน้านี้บันทึกฟีเจอร์ accounts-payable **เฉพาะส่วนที่ใช้ GRN** และส่วนที่ฝั่ง GRN ตอบสนอง voucher การจ่าย AP, การชำระ withholding tax, AR invoice/receipt, dashboard AP/AR และมุมมอง aged-payables เป็นฟีเจอร์บัญชีที่ไม่มีจุดสัมผัสกับ inventory จึงมีเพียงแถวสรุปในหน้าแรก [General Ledger](/th/inventory/general-ledger) และที่เหลือให้ดูที่ source (`apps/micro-business/src/ap/ap-payment/`, `.../ar/`)

## 2. โฟลว์ที่เกี่ยวกับ inventory

```
committed GRN (post_type = ap)  --grn-candidates-->  pick items (same vendor + currency)
        |
        v  POST from-grn { grn_item_ids[], doc_date, vendor_invoice_no, invoice_date, ... }
  draft AP invoice (doc_type = invoice, doc_source = grn)
     one line per GRN item, quantity = received_qty - already matched
     Dr account = inventory account mapping (product, then item group)
     Cr account = vendor.ap_chart_of_accounts_id, else gl_setting.ap_control_account_id
        |
        v  submit
  no AP workflow in the BU  -> posted at once
  AP workflow configured    -> in_review -> (approve ... final approve) -> posted
        |
        v  posted: voucher Dr inventory + Dr input VAT / Cr AP, tax record, GRN lines locked
```

### 2.1 Routes (gateway `api/:bu_code/ap-invoice`, `application/ap-invoice/ap-invoice.controller.ts`)

| Route | Line | ทำอะไร |
|---|---|---|
| `GET grn-candidates?vendor_id&currency_id` | `:89` | รายการของ GRN ที่ **committed** และ `post_type = ap` สำหรับ vendor และสกุลเงินนั้น ที่ `received_qty` ยังจับคู่ไม่ครบ; แต่ละแถวมี `remaining_qty` (`ap-invoice.service.ts` `grnCandidates :333`) |
| `POST from-grn` | `:329` | สร้าง invoice แบบ **draft** จาก `grn_item_ids[]` (`createFromGrn :422`) |
| `POST` / `PUT :id` / `DELETE :id` | `:291` / `:370` / `:414` | สร้างด้วยมือ (`doc_type` `invoice`, `debit_note`, `credit_note`, `deposit`); update และ delete ทำได้เฉพาะ draft |
| `GET`, `GET :id`, `GET :id/reference-candidates` | `:152` / `:197` / `:244` | list, รายละเอียด และเอกสาร CN/DN/deposit ที่ invoice นี้นำไปหักกลบได้ |
| `POST :id/submit` / `approve` / `review` / `reject` | `:457` / `:503` / `:549` / `:597` | action ของ workflow (`enum_workflow_type.ap_invoice`) |
| `POST :id/void` | `:647` | void draft หรือ reverse invoice ที่โพสต์แล้ว; `@Permission({ 'accounting.ap': ['void'] })` แบบ static |

คลาสมี `KeycloakGuard` + `PermissionGuard` แต่ guard คืน `true` บน route ใดก็ตามที่ไม่มี `@Permission` ของตัวเอง ดังนั้นมีเพียง `void` ที่ถูก gate ด้วย permission; ที่เหลือใช้เพียง licence + Keycloak (`ap-invoice.controller.ts:40-66`)

### 2.2 กฎที่บังคับเมื่อดึงบรรทัด GRN

| กฎ | Error (`packages/error-catalog`) | อยู่ที่ |
|---|---|---|
| ทุกรายการที่ขอมีอยู่จริง | `AP_INVOICE_LINE_INVALID` ("one or more GRN items were not found") | `checkGrnItems` (`ap-invoice.service.ts:1357`) |
| GRN เป็น `committed`, ไม่ถูกลบ, `post_type = ap` (GRN แบบ `cash` และ `consignment` จึงออก invoice ไม่ได้) | `AP_GRN_NOT_COMMITTED` (422) | เหมือนกัน |
| ทุกรายการใช้ vendor และสกุลเงินเดียวกัน | `AP_VENDOR_CURRENCY_MISMATCH` (422) | เหมือนกัน |
| `remaining = received_qty - Σ matched_qty` ของบรรทัดที่ยังใช้งานบนเอกสารอื่นที่ไม่ void ต้องมากกว่า 0 | `AP_GRN_OVER_MATCHED` (422) | `grnLines :468`; ตรวจซ้ำตอน submit/post พร้อม row lock (`checkGrnSources`, `ap-invoice.posting.ts:169`) |
| สินค้ามี account mapping แบบ `inventory` (`tb_product_account_code_mapping` ดูที่สินค้าก่อน แล้วค่อย item group) | `AP_INVOICE_LINE_INVALID` ("no inventory account mapping for product ...") | `resolveProductAccount` |
| เลขที่ invoice ของ vendor ไม่ซ้ำต่อ vendor ในบรรดาเอกสารที่ยังใช้งานและไม่ void | `AP_VENDOR_INVOICE_NO_DUPLICATE` (409) | partial index `apinvoice_vendor_invoice_no_u` |
| GL period ของ `doc_date` เปิดอยู่ | `GL_PERIOD_NOT_OPEN` | ตรวจตอน submit และอีกครั้งภายใน post transaction |

แต่ละบรรทัดของ invoice เก็บต้นทางไว้ใน `tb_ap_invoice_detail_source` (`good_received_note_id`, `grn_no`, `good_received_note_detail_item_id`, `matched_qty`, `grn_unit_price`, `matched_amount`, `variance_amount`) `variance_amount = line net - round2(matched_qty x grn_unit_price)` คือส่วนต่างราคาระหว่าง invoice กับใบรับของ (`ap-invoice.writer.ts:419-466`) ราคาต่อหน่วยบนบรรทัด from-GRN เริ่มต้นเป็น `received_price` ของ GRN และ VAT profile เป็น `tax_profile_id` ของรายการ GRN

## 3. Voucher ที่โพสต์

เมื่ออนุมัติขั้นสุดท้าย (หรือตอน `submit` เมื่อ BU ไม่มี AP workflow) `ApInvoicePosting.postInTx` (`ap-invoice.posting.ts:278`) สร้างบรรทัดด้วย `buildInvoiceJvLines` (`ap-invoice.logic.ts:393`) แล้วส่งให้ `GlSubledgerPostingService.postFromSource` ใน **transaction เดียวกัน** กับการเปลี่ยนสถานะ:

| บรรทัด | บัญชี | จำนวนเงิน (สกุลเงินฐาน) |
|---|---|---|
| Dr | `dr_chart_of_accounts_id` ของบรรทัด (บัญชี inventory จาก mapping) | `base_net_amount` |
| Dr | `vat_chart_of_accounts_id` ของบรรทัด หรือ `gl_setting.input_vat_account_id` | `base_vat_amount` |
| Cr | `cr_chart_of_accounts_id` ของบรรทัด (บัญชี AP ของ vendor หรือ `ap_control_account_id`) | `base_total_amount` |

Credit note กลับทุกด้าน; deposit เดบิต `advance_deposit_account_id` แทนและไม่มี VAT บรรทัดที่จำนวนเงินเป็นศูนย์ถูกข้าม voucher เป็น idempotent ต่อ (`source`, `source_ref_type`, `source_ref_id`) - unique index `gljvheader_source_ref_u` - และ prefix เริ่มต้นคือ `gl_setting.ap_jv_prefix_id` แล้วจึง `auto_jv_prefix_id` หาก period ปิดอยู่หรือขาด setting key (`GL_SETTING_ACCOUNT_MISSING`) การอนุมัติทั้งหมดจะ rollback และลองใหม่ได้

ผลข้างเคียงตอนโพสต์: สร้างเรกคอร์ด `tb_ap_invoice_tax` (`tax_status = pending`, `expiry_claim_date = invoice_date + 6 months`; credit note เก็บจำนวนเงินติดลบ; ถ้าไม่มีบรรทัดใดมี VAT เรกคอร์ดจะถูกลบ) และ reference (การหักกลบ credit note / deposit) ถูกนำไปใช้

**สิ่งที่ไม่ทำ:** ไม่โพสต์ *Dr inventory / Cr GR-IR* ตอนรับของ ไม่เปรียบเทียบราคา invoice กับ cost layer และไม่เปลี่ยน `tb_inventory_transaction_cost_layer` - ดังนั้นส่วนต่างราคา (`variance_amount`) ไม่เคยตีมูลค่าสต๊อกใหม่ สินทรัพย์ inventory ถูกเดบิตที่ราคา **invoice** ไม่ใช่ที่ต้นทุน GRN

## 4. ฝั่ง GRN ตอบสนองอย่างไร

| พฤติกรรม | Source |
|---|---|
| `GET good-received-note/:id` คืน `ap_invoices: [{ id, doc_no, doc_status }]` - AP invoice ที่ยังใช้งาน (ไม่ void ไม่ถูกลบ) ที่จับคู่บรรทัดใดของ GRN | `good-received-note.service.ts:351,357`; `good-received-note.ap-link.ts:87` |
| การอัปเดต GRN ที่ **committed** ซึ่งอยู่บน AP invoice ที่ยังใช้งานถูกปฏิเสธด้วย `GRN_AP_LINKED_NOT_EDITABLE` (400, "... already on AP invoice {doc_nos} ...") **ก่อน** กฎ header-only ทำงาน | `good-received-note.ap-link.ts:122-153`; เรียกจาก `update` (`good-received-note.service.ts:1499`) |
| GRN ที่ committed และไม่มี AP invoice ยังเปลี่ยนได้เฉพาะข้อเท็จจริงของ vendor invoice (`invoice_no`, `invoice_date`, `invoice_f`, `payment_due_date`, ฟิลด์ credit-term, `description`, `note`, `post_type`); อย่างอื่นคือ `GRN_COMMITTED_HEADER_ONLY` | `HEADER_EDITABLE_KEYS` (`good-received-note.ap-link.ts:19`) |
| หน้าจอ GRN ปิดการแก้ไขเมื่อ `ap_invoices` ไม่ว่างและ GRN เป็น committed | `carmen-frontend/routes/procurement/goods-receive-note/grn-header.tsx:61-65` |
| การ void AP invoice (draft: ลบ/void ตรง ๆ; posted: reversal voucher) คืนปริมาณที่จับคู่ไว้ - `checkGrnSources` และ lock query ไม่สนเอกสาร `void` | `ap-invoice.posting.ts:169`, `voidPostedInTx :339` |

ดู [good-receive-note](/th/inventory/good-receive-note) สำหรับสถานะของ GRN และ `post_type`

## 5. การ Void

Draft ถูก void ในที่เดิม (tax record ถูก void) invoice ที่ **posted** ถูก void ด้วย reversal voucher ผ่าน facade (`reverseBySource`) โดยมีเงื่อนไขตามลำดับ: ไม่มี payment voucher ที่ยังใช้งาน (`AP_INVOICE_HAS_PAYMENT`, 409), ไม่มีเอกสารอื่นนำไปหักกับมัน (`AP_INVOICE_IS_REFERENCED`, 409) และ GL period ของวันที่ void เปิดอยู่ (`GL_PERIOD_NOT_OPEN`) การ void/reverse ของหน้าจอ GL เองปฏิเสธ voucher เดียวกันนี้ (`isSubledgerVoucher`, `gl-posting.service.ts:77`): ให้ void **AP invoice** ไม่ใช่ journal voucher

## 6. การ export ข้อมูลเดียวกันสู่ภายนอก (อ่านอย่างเดียว, pull)

แยกจากการโพสต์ micro-business สร้างข้อมูล Dr/Cr **ตามคำขอ** จากเอกสาร inventory เพื่อระบบบัญชีภายนอก ไม่มีสิ่งใดถูกเขียนลง `tb_gl_jv_*`

| Endpoint (`apps/backend-gateway/src/external-api/`) | เอกสาร | รูปแบบ |
|---|---|---|
| `GET api/ext/v1/ap-invoices` | `GRN`, `CN` (final และ voided) | เรกคอร์ด vendor-invoice หนึ่งบรรทัดต่อรายการที่รับ/คืน ระบุบัญชีตามบทบาท (`debit_*` inventory, `ap_*` เจ้าหนี้) พร้อมจำนวนภาษี; จำนวนเงิน CN เป็นบวก (กลับด้านตาม `doc_type`); บัญชี input-VAT เป็นหน้าที่ของระบบภายนอก |
| `GET api/ext/v1/gl-journals` | `SR`, `SI`, `SO` (final และ voided ที่เคลื่อนไหวสต๊อก) | journal Dr/Cr ที่สมดุลหนึ่งใบต่อเอกสาร; เอกสารที่ไม่เคลื่อนไหวสต๊อกถูกตัดออก |

Query: `date_from`, `date_to` (รวมปลายทาง, ไม่เกิน 366 วัน), `doc_types` ที่ไม่บังคับ, `date_field` (`document` เป็นค่าเริ่มต้น หรือ `updated` สำหรับ incremental sync), `page`, `perpage` (1-200, ค่าเริ่มต้น 50) การยืนยันตัวตนใช้ API key ต่อ BU (`x-client-id` / `x-client-secret`, `BuApiKeyGuard`) ไม่ใช่ Keycloak; BU มาจาก key บัญชีมาจาก `tb_account_mapping` เท่านั้น (migration `20261014100100_account_mapping`: `mapping_type` `AP` สำหรับ `grn`/`cn`, `GL` สำหรับ `adjustment`/`sr_in`/`sr_out`, คีย์ด้วย location x product item group; ดู [chart-of-account-mapping](/th/inventory/master-data/chart-of-account-mapping)) - สังเกตว่านี่เป็นคนละตารางกับ `tb_product_account_code_mapping` ที่ route AP-invoice-from-GRN ใน § 2 ใช้; บรรทัดที่หาบัญชีไม่ได้จะถูกคืนพร้อม `unmapped: true` และรายการ `issues` แทนที่จะล้มเหลว Builders: `micro-business/src/inventory/accounting-export/builders/{grn.ap-builder,cn.ap-builder,sr.builder,stock-adjustment.builder}.ts` เอกสารหนึ่งใบปรากฏใน endpoint เดียวจากสองตัวเท่านั้น GRN builder ตัดรายการที่ location แบบ consignment, ถือ `cash` เป็น AP และตัด GRN แบบ `consignment` ออกทั้งหมด

## 7. Edge Cases

| # | สถานการณ์ | ผลที่คาดหวัง | Source |
|---|---|---|---|
| 1 | AP invoice ใบที่สองดึงรายการ GRN ที่ invoice ใบแรก (แม้เป็น draft) จับคู่ไปแล้ว | `matchedQtyByItem` นับทุกเอกสารที่ไม่ void และไม่ถูกลบ ดังนั้น `from-grn` ได้เฉพาะปริมาณที่เหลือ หรือ `AP_GRN_OVER_MATCHED` เมื่อไม่เหลือ; submit/post ตรวจซ้ำภายใต้ row lock (`FOR NO KEY UPDATE`, เรียงตาม id) การ submit พร้อมกันจึงเรียงลำดับ | `grnLines`, `checkGrnSources` |
| 2 | รายการ GRN ไม่มี inventory account mapping | `from-grn` ปฏิเสธทั้งคำขอ; ให้สร้าง invoice ด้วยมือพร้อม `dr_chart_of_accounts_id` ที่ระบุเอง | `grnLines` |
| 3 | GRN เป็น `cash` หรือ `consignment` | ไม่อยู่ใน `grn-candidates`; `from-grn` คืน `AP_GRN_NOT_COMMITTED` | `checkGrnItems` |
| 4 | แก้บรรทัดของ GRN ที่ committed หลังจาก AP invoice (แม้เป็น draft) ดึงไปแล้ว | `GRN_AP_LINKED_NOT_EDITABLE`; ต้อง void/ลบ invoice ก่อน | `findActiveApInvoicesForGrn` นับทุก invoice ที่ไม่ void และไม่ถูกลบ |
| 5 | อนุมัติตอนที่ GL period ปิดอยู่ | `GL_PERIOD_NOT_OPEN`; การอนุมัติ rollback, invoice คงสถานะ `in_review` | doc comment ของ `approve` |
| 6 | void GL voucher ของ AP invoice จากหน้าจอ journal | `GL_JV_IMMUTABLE`; ให้ void invoice แทน | `isSubledgerVoucher` |
| 7 | void invoice ที่โพสต์แล้วและมี payment | `AP_INVOICE_HAS_PAYMENT` | `voidPostedInTx` |
| 8 | ราคา invoice ต่างจากราคา GRN | เก็บเป็น `variance_amount`; มูลค่าสต๊อกไม่เปลี่ยน ledger ถือราคา invoice | `ap-invoice.writer.ts:466` |

## 8. ข้อค้นพบในโค้ด (ยังไม่ได้แก้)

- **ไม่มี AP-link guard ตอน void GRN** `findActiveApInvoicesForGrn` ถูกเรียกจากการอ่านรายละเอียด GRN และ `update` เท่านั้น (`good-received-note.service.ts:351,1499`); การ grep path void ของ GRN ไม่พบการใช้ ควรยืนยันด้วยการทดสอบว่า GRN ที่ committed และอยู่บน AP invoice ที่ *posted* แล้ว void ได้หรือไม่ (จะเหลือเจ้าหนี้ที่อ้างสต๊อกที่ถูก reverse)
- **`enum_gl_jv_source.inventory` ยังคงไม่มีผู้เขียน** - ฝั่งรับของใน ledger มีอยู่ผ่าน route AP นี้และ export ใน § 6 เท่านั้น
- **Frontend ไม่เรียก route เหล่านี้** `routes/accounting/accounts-payable/shared/use-accounts-payable.ts` สร้าง `createApMockRepository` เสมอ; ไม่มี `fetch` ของ `ap-invoice` ทดสอบได้เฉพาะ backend ผ่าน Bruno / Swagger

## 9. อ้างอิง

- **Backend:** `../carmen-turborepo-backend/apps/micro-business/src/ap/ap-invoice/` (`ap-invoice.service.ts`, `ap-invoice.posting.ts`, `ap-invoice.logic.ts`, `ap-invoice.writer.ts`, `ap-invoice.validation.ts`); `.../gl/gl-subledger-posting/gl-subledger-posting.service.ts`; `.../inventory/good-received-note/good-received-note.ap-link.ts`; `.../inventory/accounting-export/`
- **Gateway:** `apps/backend-gateway/src/application/ap-invoice/ap-invoice.controller.ts`; `apps/backend-gateway/src/external-api/{ap-invoice,gl-journal}/`; query schemas `packages/rpc-contract/src/schemas/accounting-export-query.ts`
- **Prisma:** `packages/prisma-shared-schema-tenant/prisma/schema.prisma` - `tb_ap_invoice :7182`, `tb_ap_invoice_detail :7267`, `tb_ap_invoice_detail_source :7350`, `tb_ap_invoice_reference :7370`, `tb_ap_invoice_tax :7390`, `enum_ap_invoice_doc_type :300`, `enum_ap_invoice_status :307`, `enum_ap_invoice_source :314`; migration `20260923060040_accounting_foundation_ap`
- **เกี่ยวข้อง:** [GL Posting และรอยต่อกับ Inventory](/th/inventory/general-ledger/gl-posting), [good-receive-note](/th/inventory/good-receive-note), [credit-note](/th/inventory/purchase-order/credit-note)
