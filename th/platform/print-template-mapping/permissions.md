---
title: Print Template Mapping — สิทธิ์ (Permissions)
description: เมทริกซ์ gate ของ print_template_mapping.*, กฎ precedence ของ allow/deny ตอน resolve และเมทริกซ์กรณีพิเศษสำหรับผู้ทดสอบ — รวมถึงเส้นทางของ micro-business ที่ bypass การกำหนดขอบเขต BU
published: true
date: 2026-06-10T15:30:00.000Z
tags: book/platform, print-template-mapping, permissions
editor: markdown
dateCreated: 2026-06-10T15:30:00.000Z
---

# Print Template Mapping — สิทธิ์ (Permissions)

> **At a Glance**
> **Gate:** route มี `print_template_mapping.read` / `.create` / `.update` บน `PrivateRoute`; รายการ sidebar อยู่บน `.read` &nbsp;·&nbsp; **Gate `<Can>` ภายในหน้า:** New Mapping (`.create`), Edit ของ row (`.update`), Delete ของ row (`.delete` — ภายในหน้าเท่านั้น ไม่มี route), toggle Edit (`.update`) &nbsp;·&nbsp; **เรื่องราว authorization ที่สอง:** กฎ BU ตอน resolve — deny ชนะ, allow ว่าง = ทั้งหมด, **`bu_code` ว่างข้ามการตรวจสอบ BU ทั้งหมด** &nbsp;·&nbsp; **ช่องว่างที่ทราบ:** เส้นทางพิมพ์ของ micro-business ทำการ resolve mapping โดยไม่ apply รายการ BU เลย

## 1. ภาพรวม

สองเรื่องราว authorization ที่เป็นอิสระต่อกันมาบรรจบกันในโมดูลนี้ เรื่องแรกคือ [Platform RBAC](/th/platform/rbac) แบบธรรมดา: key `print_template_mapping.*` ทั้งสี่ (seed ใน `seed.platform-permission.ts`) ที่ตัดสินว่า*มนุษย์*คนใดเห็นและแก้ไข row ของ mapping ได้ (§2) เรื่องที่สองคือสิ่งที่ตัว row เอง encode ไว้: **กฎตอน resolve** — pipeline การพิมพ์เลือก mapping ตัวไหนสำหรับคู่ `(document_type, bu_code)` หนึ่ง ๆ ควบคุมโดย `is_active`, `is_default`, `display_order` และรายการ BU แบบ allow/deny (§3) มนุษย์ที่ถือ key `print_template_mapping.*` ครบกำลังแก้ไขข้อมูล routing ซึ่งการบังคับใช้เกิดขึ้นฝั่ง server ทั้งหมดตอนพิมพ์; ในทางกลับกัน ไม่มี RBAC key ใดมีอิทธิพลต่อว่าเอกสารจะพิมพ์ด้วยเทมเพลตตัวไหน

## 2. เมทริกซ์ของ gate

gate ทั้งหมด resolve ผ่าน resolver `hasPermission` ตัวเดียวที่ document ไว้ใน [Platform RBAC — Permissions](../rbac/permissions.md); route guard ที่ไม่ผ่านจะ render `<AccessDenied>` ภายใน shell `<Layout>` ปกติ

| Surface | กลไก | Key | แหล่งที่มา |
|---|---|---|---|
| `/print-template-mapping` | `PrivateRoute requiredPermission` | `print_template_mapping.read` | `src/App.tsx` |
| `/print-template-mapping/new` | `PrivateRoute requiredPermission` | `print_template_mapping.create` | `src/App.tsx` |
| `/print-template-mapping/:id/edit` | `PrivateRoute requiredPermission` | `print_template_mapping.update` | `src/App.tsx` |
| sidebar "Print Mapping" (กลุ่ม Content, ไอคอน Printer) | nav filter ของ `Layout.tsx` | `print_template_mapping.read` | `src/components/Layout.tsx` |
| New Mapping (header ของหน้า list) | `<Can>` | `print_template_mapping.create` | `PrintTemplateMappingManagement.tsx` |
| Edit ของ row (ปุ่มดินสอแบบ inline) | `<Can>` | `print_template_mapping.update` | `PrintTemplateMappingManagement.tsx` |
| Delete ของ row (ปุ่มถังขยะแบบ inline) | `<Can>` | `print_template_mapping.delete` | `PrintTemplateMappingManagement.tsx` |
| toggle Edit (header ของหน้า edit) | `<Can>` | `print_template_mapping.update` | `PrintTemplateMappingEdit.tsx` |

ความไม่สมมาตรที่เกี่ยวข้องกับผู้ทดสอบ ซึ่งสะท้อนโมดูล Applications:

- **`.delete` มีอยู่ภายในหน้าเท่านั้น** ไม่มี route ใดต้องการมันและหน้า edit ไม่มี action ลบ — surface ทั้งหมดของ key คือปุ่มถังขยะของ row ในหน้า list session ที่มีเฉพาะ `.read` เห็น list แบบจัดกลุ่มพร้อมช่อง action ว่างเปล่า
- **Save ไม่ถูก gate แยกต่างหาก** เฉพาะ *toggle* Edit เท่านั้นที่ถูกห่อด้วย `<Can>`; แถว Save/Cancel render เฉพาะในโหมดแก้ไข ซึ่งไปถึงไม่ได้หากไม่มี toggle (โหมด create อยู่หลัง `.create` ของ route) การบังคับใช้ฝั่ง backend บน `PUT` ยังคงเป็นขอบเขตจริง
- **ไม่มี CTA ของ empty-state ที่ไม่ถูก gate** ต่างจาก Applications, list ที่ว่างแสดงข้อความธรรมดา ไม่ใช่ปุ่ม — ไม่มีการรั่วของ affordance สำหรับ session ที่ไม่มี `.create`
- **Key ของ route เป็นอิสระต่อกัน** `PrivateRoute` ตรวจสอบ key ละหนึ่งตัว: `.update` อย่างเดียว deep-link ไป `/print-template-mapping/:id/edit` ได้ขณะที่หน้า list ปฏิเสธ; `.create` อย่างเดียวไปถึง `/print-template-mapping/new` ทาง URL ได้
- sidebar filter เป็น UX ไม่ใช่ security — session ที่ไม่มี `.read` ยังพิมพ์ URL ได้และจะชน route guard session แบบ super-admin และ bootstrap ผ่านทุก gate; อย่า QA เมทริกซ์นี้จาก session แบบนั้น

## 3. กฎตอน resolve

สัญญา runtime ฉบับ canonical คือ `Resolve` ของ micro-report (`db/print_template_mapping_repo.go`) เปิดเผยเป็น `GET /api-system/print-template-mappings/resolve?document_type=X&bu_code=Y`:

```
resolve(document_type, bu_code):
    rows = mappings WHERE document_type = :document_type
                      AND deleted_at IS NULL
                      AND is_active = true
           ORDER BY is_default DESC, display_order ASC

    for row in rows:
        if permits_bu(row, bu_code):
            return row                  -- row แรกที่ได้รับอนุญาตชนะ
    return 404 "no active mapping found"

permits_bu(row, bu_code):
    if bu_code is blank:                return true
        -- ไม่ปรึกษารายการ BU เลย รวมถึง deny ด้วย
    if bu_code in row.deny_business_unit:
                                        return false   -- deny ชนะ ถูกตรวจสอบก่อน
    if row.allow_business_unit is non-empty
       and bu_code not in row.allow_business_unit:
                                        return false
    return true                         -- allow ว่าง = ทุก BU
```

ผลสืบเนื่องสามข้อที่ควรซึมซับ:

1. **flag default ไม่สัมบูรณ์** การเรียงวาง default ไว้ก่อน แต่ถ้ารายการ BU ของมันปฏิเสธ caller การ resolve จะ*ตกผ่าน*ไปยัง row ถัดไปที่ได้รับอนุญาตตาม `display_order` — BU หนึ่งจึงมี "default" ที่ต่างจากคนอื่นได้โดยพฤตินัย
2. **deny ชนะ allow** รวมถึงเมื่อ code เดียวกันปรากฏในทั้งสองรายการบน row เดียว
3. **`bu_code` ที่ว่าง bypass การกำหนดขอบเขต BU ทั้งหมด** — แม้แต่รายการ deny caller ที่ละ `bu_code` จะได้ row ที่อยู่ลำดับแรกแบบ global เสมอ

**ตัว bypass ในทางปฏิบัติ:** helper พิมพ์ที่ใช้ร่วมกันของ micro-business (`renderViaMicroReport` ใน `apps/micro-business/src/common/print-report.helper.ts`) — เส้นทางเบื้องหลังปุ่ม Print จริงในแปด document service: PO, GRN, SR, CN (credit note), IA (inventory adjustment), PC (physical count), SC (spot check) และ RFQ (request for pricing) โดย PR ทำการ inline query แบบเดียวกัน — **ไม่**เรียก endpoint resolve มัน query `tb_print_template_mapping` โดยตรงผ่าน Prisma ด้วยการเรียง `is_default DESC, display_order ASC` เดียวกันและ filter active/ไม่ถูกลบเหมือนกัน **แต่ไม่ apply การตรวจสอบ allow/deny ใด ๆ ทั้งสิ้น** ทั้งที่มันมี `bu_code` อยู่ในมือ (ใช้เพียงเพื่อระบุที่อยู่ของ viewer URL ของ micro-report) ณ 2026-06-10 การกำหนดขอบเขต BU บน mapping จึงถูกเคารพโดย endpoint `resolve` แต่**ถูกเพิกเฉยโดย flow พิมพ์เอกสารหลัก** test plan ไม่ควร assume ว่าการ route เทมเพลตต่อ BU ทำงานแบบ end-to-end จนกว่า consumer ตัวนั้นจะรับ semantics ของ resolve ไปใช้

## 4. กรณีพิเศษ

| # | สถานการณ์ | พฤติกรรม | หมายเหตุสำหรับผู้ทดสอบ |
|---|---|---|---|
| 1 | สอง row ถูก save `is_default = true` สำหรับชนิดเอกสารเดียว | UI ไม่เคยห้าม; Go service รัน `EnsureSingleDefault` หลังแต่ละ create/update โดยลดสถานะ default *ตัวอื่น ๆ* — การ save ครั้งสุดท้ายชนะ | best-effort เท่านั้น: การลดสถานะที่ล้มเหลวเพียงแค่ log warning และการเขียน DB ตรง bypass มันทั้งหมด เมื่อมีตัวซ้ำอยู่ `resolve` ยังทำงาน — `display_order ASC` เป็น tie-break |
| 2 | BU code อยู่ทั้งใน allow และ deny บน row เดียวกัน | ถูก deny — deny ถูกตรวจสอบก่อน | precedence เดียวกับการกำหนดขอบเขตของ `tb_report_template`; ตรวจสอบด้วย setup แบบสอง row เพื่อให้การตกผ่าน (§3.1) สังเกตได้ |
| 3 | mapping ที่ `is_active = false` | ถูกข้ามโดย `resolve` และโดย query ของ micro-business; ยังแสดงใน SPA เว้นแต่ "Active only" ถูกติ๊ก | การ deactivate เป็นวิธีที่ปลอดภัยในการปลดระวาง layout โดยยังคง row ไว้ให้ audit ได้ |
| 4 | ไม่มี row ที่ `is_default` สำหรับชนิดเอกสาร | `resolve` คืน row ที่ active ที่มี `display_order` ต่ำสุดอยู่ดี — default เป็น preference ของการเรียง ไม่ใช่ข้อบังคับ | ปุ่ม Print แบบ legacy ยังพิมพ์ได้; มีเพียง*ตัวเลือก*ของเทมเพลตที่อาจทำให้ประหลาดใจ |
| 5 | ไม่มี mapping ที่ active เลยสำหรับชนิดเอกสาร | `resolve` → 404 "no active mapping found"; micro-business คืน "No active \<type\> print mapping found" และ action Print ล้มเหลว | seed ลงทะเบียน default หนึ่งตัวต่อชนิดที่รองรับ — 404 ในสภาพแวดล้อมที่ seed แล้วหมายความว่ามีคน deactivate หรือลบมัน |
| 6 | `resolve` ด้วย `bu_code` ที่ไม่รู้จัก/พิมพ์ผิด | ถูกปฏิบัติเป็นเพียง string อีกตัวหนึ่ง: ถูกปฏิเสธโดยทุก row ที่มีรายการ allow ไม่ว่าง, ได้รับอนุญาตโดย row ที่ allow ว่าง | BU code ในรายการเป็นข้อความอิสระที่ไม่มี FK — การพิมพ์ผิดฝั่งใดฝั่งหนึ่งเปลี่ยน routing เงียบ ๆ แทนที่จะ error |
| 7 | `resolve` โดยไม่มี `bu_code` | การตรวจสอบ BU ทั้งหมดถูกข้าม — แม้แต่ row ที่ deny ทุก BU ก็มีสิทธิ์ | เป็นความจงใจในโค้ด Go; flag caller ใดก็ตามที่ละ `bu_code` โดยคาดหวังให้รายการ deny มีผล |
| 8 | การทำให้รายการ allow/deny ว่างในฟอร์ม edit ของ SPA | SPA ส่ง `null`; update ของ Go ปฏิบัติกับ `null` ว่า "ไม่ได้ส่งมา" และคงรายการที่เก็บไว้ | การ save toast ว่าสำเร็จขณะที่รายการยังรอดอยู่ — ตรวจสอบผ่าน Debug Sheet หรือ `GET :id` การเคลียร์ต้องใช้ `PUT` ตรง ๆ ด้วย `[]` ([Data Model](./data-model.md) §5) |
| 9 | create/update ด้วย `document_type` ที่ไม่รองรับ | 400 "unsupported document_type — see GET /document-types" (เส้นทาง update ละ suffix "— see GET /document-types") | การ validate ฝั่ง server กับรายการ Go แบบ hard-code; select ของ SPA ทำให้กรณีนี้ไปถึงได้เฉพาะผ่านการเรียก API ตรงเท่านั้น |
| 10 | mapping ชี้ไปยังเทมเพลตที่ถูก soft-delete หรือไม่ใช่ print | row ทำการ save และแสดงใน list ได้ (โดย `template_name` เป็น `-` เมื่อถูกลบ); micro-business ล้มเหลวตอน render ด้วย "Mapped template … not found" สำหรับเป้าหมายที่ถูกลบ | การไม่มี FK และการ match `kind`/`report_group` แบบ soft หมายความว่า UI ป้องกันเป้าหมายที่ค้างลอยหรือไม่ตรงกันได้ไม่เต็มที่ |

## 5. คำแนะนำ

**เมทริกซ์ QA สำหรับ precedence ของ resolve** — รันแต่ละ case กับชนิดเอกสารที่มีสอง row ที่ active (A: `is_default`, `display_order 0`; B: ไม่เป็น default, `display_order 1`):

| allow ของ row A | deny ของ row A | `bu_code` | ที่คาดหวัง |
|---|---|---|---|
| ว่าง | ว่าง | ใดก็ได้หรือว่าง | A (default, อนุญาตทั้งหมด) |
| `[T01,T03]` | ว่าง | `T01` | A |
| `[T01,T03]` | ว่าง | `T02` | **B** — A ปฏิเสธ การ resolve ตกผ่าน |
| ว่าง | `[T02]` | `T02` | **B** — deny ชนะบน A |
| `[T01]` | `[T01]` | `T01` | **B** — deny ชนะ allow บน A |
| `[T01]` | ว่าง | (ว่าง) | A — การตรวจสอบ BU ถูกข้ามทั้งหมด |
| `[T01]` | ว่าง | code ที่ไม่รู้จัก | **B** ถ้า B อนุญาต ไม่เช่นนั้น 404 |

- **ทดสอบสองเรื่องราว authorization แยกจากกัน** ตรวจสอบการ gate มนุษย์ด้วย session ที่ถือ key `print_template_mapping.*` ทีละหนึ่งตัวเป๊ะ ๆ; ตรวจสอบ routing ด้วยการเรียก `resolve` — การ save ใน SPA ที่ผ่านไม่ได้บอกอะไรเลยเกี่ยวกับสิ่งที่จะพิมพ์ออกมา
- **ใช้ resolve ผ่านทั้งสองเส้นทางเสมอ** endpoint `resolve` และ query แบบ inline ของ micro-business เห็นพ้องเรื่องการเรียงแต่ขัดแย้งกันเรื่องการกำหนดขอบเขต BU (§3) — การทดสอบ routing แบบ scope ต่อ BU ใด ๆ ต้องยืนยันพฤติกรรมบนปุ่ม Print จริง ไม่ใช่แค่ที่ endpoint
- **probe การลดสถานะแบบ single-default** save row B เป็น default, re-fetch row A และยืนยันว่ามันถูกลดสถานะ; จากนั้นก่อให้เกิด race (การ save พร้อมกันสองครั้ง) และยืนยันว่าตัวที่รอดตรงกับคอลัมน์ audit
- **audit รายการ BU เทียบกับทะเบียน BU** code เป็นข้อความอิสระ — diff เนื้อหาของรายการกับ `tb_business_unit.code` เป็นระยะ เพราะ BU ที่ถูกเปลี่ยนชื่อจะหลุดจากทุกรายการ allow ที่มันปรากฏอยู่อย่างเงียบ ๆ
- **ปฏิบัติกับการ save รายการว่างของ SPA เป็นกับดักที่ทราบกันดี** จนกว่าเส้นทาง update จะตีความ `null` ว่า "เคลียร์" ให้ document วิธีแก้ขัดด้วย `PUT` พร้อม `[]` ไว้ใน runbook แทนที่จะยื่น defect ซ้ำซ้อน

**แหล่งข้อมูลอ้างอิง:** `../carmen-platform/src/App.tsx` (route guard ทั้งสาม) · `src/components/Layout.tsx` (รายการ sidebar) · `src/pages/PrintTemplateMappingManagement.tsx` / `PrintTemplateMappingEdit.tsx` (gate `<Can>`) · `../micro-report/db/print_template_mapping_repo.go` (`Resolve`, `mappingPermitsBU`, `EnsureSingleDefault`) · `../micro-report/controller/print_template_mapping_controller.go` (การ validate, เส้นทาง 404/400) · `../carmen-turborepo-backend-v2/apps/micro-business/src/common/print-report.helper.ts` (ตัว bypass การกำหนดขอบเขต BU) · `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.ts` (key ทั้งสี่)
**Cross-link:** [หน้า landing ของ Print Template Mapping](/th/platform/print-template-mapping) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Platform RBAC — Permissions](../rbac/permissions.md)
