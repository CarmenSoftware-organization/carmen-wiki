---
title: กลุ่มฟอร์มรายงาน (Report Form Groups)
description: หน้าจอ /report-form-groups — การ์ดหนึ่งใบต่อ report_group code ที่ตายตัว แต่ละใบแสดง report template ประเภท "form" พร้อม action ตั้งเป็น default บน tb_report_template.is_default — surface ที่ควบคู่กับฟิลด์ template_type ของ Report Templates เข้ามาแทนที่โมดูล print-template-mapping ที่ถูกลบไป
published: true
date: '2026-09-06T21:00:00.000Z'
tags: book/platform, report-form-groups
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# กลุ่มฟอร์มรายงาน (Report Form Groups)

**Report Form Groups** คือหน้าจอที่ admin ภายในของ Carmen เลือก per ชนิดเอกสารว่า **form** template แบบเอกสารเดี่ยวตัวไหนที่ business unit จะได้เป็น default เมื่อยังไม่ได้เลือกเอง มันใช้ข้อมูลและ permission model ร่วมกับ [Report Templates](/th/platform/report-templates) เป็นส่วนใหญ่ — ทั้งสอง surface แก้ไขแถว `tb_report_template` เดียวกัน — แต่เป็นโมดูล Platform ระดับบนสุดของตัวเอง มี route, sidebar entry และ feature-flag key เป็นของตัวเอง

> **At a Glance**
> **Component:** `ReportFormGroupManagement` &nbsp;·&nbsp; **Route:** `/report-form-groups` gate ด้วย `<PrivateRoute requiredPermission="report_template.read" feature="report_form_groups">` (`../carmen-platform/src/App.tsx:322-329`) &nbsp;·&nbsp; **Nav:** รายการ "Form Groups" ในกลุ่ม Content ของ sidebar — **permission `report_template.read` เดียวกับ** Report Templates แต่ **feature key ต่างกัน** คือ `report_form_groups` (`../carmen-platform/src/components/nav/platformNav.ts:25`) &nbsp;·&nbsp; **เพิ่มเมื่อ:** 2026-07-24 (`bf7a28a`) สัปดาห์เดียวกับที่ `print-template-mapping` ถูกลบออกจากผลิตภัณฑ์ &nbsp;·&nbsp; **ข้อมูล:** ทุกแถว `tb_report_template` ที่ `template_type = "form"` จัดกลุ่มตาม `report_group` &nbsp;·&nbsp; **ตั้งแต่ 2026-08-22:** แต่ละแถวแสดงบรรทัด audit แบบย่อ (actor ล่าสุด สร้างหรือแก้ไข) &nbsp;·&nbsp; **e2e suite:** **ไม่มี** — ยืนยันแล้วว่าไม่มี directory `report-form-groups` (หรือชื่อใกล้เคียง) ใน `../carmen-platform-e2e/tests/` (HEAD `a8e3b31`, 2026-08-25) &nbsp;·&nbsp; **หน้าย่อย:** 0

## 1. ภาพรวม

เรื่องการใช้ permission key ร่วมกันควรพูดตรง ๆ เพราะเป็นสิ่งที่ผู้อ่านมักเข้าใจผิด: route `/report-form-groups` และแถว sidebar ของมันถือ `permission: 'report_template.read'` เหมือนกับ key ที่ gate [Report Templates](/th/platform/report-templates) เอง — ดังนั้นใครก็ตามที่เห็นโมดูลหนึ่งจะเห็นอีกโมดูลด้วย และ grant `report_template.*` ไม่ได้จำกัดแค่ "รายการเทมเพลต" ตามที่ชื่อของมันอาจสื่อ สิ่งที่แยกสองโมดูลนี้ออกจากกันอย่างเป็นอิสระคือ **feature** key ต่างหาก: `report_templates` gate สาม route ของ Report Templates ส่วน `report_form_groups` gate route และแถว nav ของโมดูลนี้แยกต่างหาก — การเปลี่ยน feature flag ของฝั่งหนึ่งไม่กระทบอีกฝั่ง (§4)

หน้าจอนี้ fetch เทมเพลตที่ `template_type = "form"` ทั้งหมดแล้วจัดกลุ่มตาม `report_group` มัน reuse permission `report_template.*` ทั้งหมด — ไม่มี key แบบ `report_form_group.*` หรือคล้ายกันใน permission catalog เลย

## 2. บริบททางธุรกิจ

จนถึง 2026-07-23 การตัดสินใจว่าเทมเพลตตัวไหน render เอกสารประเภทหนึ่ง ๆ เป็นหน้าที่ของโมดูลแยกต่างหากชื่อ `print-template-mapping` ซึ่งมีตารางของตัวเอง (`tb_print_template_mapping`) และ permission key ของตัวเอง โมดูลนั้นถูกลบออกจากผลิตภัณฑ์ผ่านสองวัน: backend-gateway proxy และแถว permission catalog `print_template_mapping.*` ถูกลบก่อน เมื่อ 2026-07-23 (carmen-turborepo-backend-v2 commit `c135bb21e`) ตามด้วยหน้าฝั่ง frontend ในวันถัดมาคือ 2026-07-24 (carmen-platform commit `de11377`) โมดูลนี้กับฟิลด์ `template_type` ของ [Report Templates](/th/platform/report-templates) เองคือสิ่งที่เข้ามาแทนที่ — เป็นการสืบทอดเชิงเอกสาร ไม่ใช่การรวมผลิตภัณฑ์ และหน้าเอกสารทั้งสองโมดูลควร (และตอนนี้ หลังการย้ายครั้งนี้ ก็เล่า) เรื่องเดียวกัน

การแทนที่นี้ถูกสร้างเป็นลำดับสั้น ๆ ที่ตรวจสอบย้อนกลับได้ ทั้งหมดใน `../carmen-platform`:

- **2026-07-23** — migration ของ schema `20260723120000_print_form_default` (path เต็มใน [แหล่งข้อมูลอ้างอิง](#7-แหล่งข้อมูลอ้างอิง)) เพิ่ม `tb_report_template.is_default`, backfill จากทุกแถว `tb_print_template_mapping` ที่ยัง active และไม่ถูก soft-delete, สร้าง partial unique index ที่บังคับ "อย่างมากหนึ่ง default ต่อกลุ่ม" (§3.3) และ drop `tb_print_template_mapping` migration เดียวกันยังเปลี่ยนชื่อค่า `report_group` จาก `RFQ` เป็น `RFP` เป็น no-op ถ้า admin เคยเปลี่ยนชื่อผ่าน UI ไปแล้ว ฝั่ง frontend ก็ลงวันเดียวกัน: `cd4fc5d` ("add IA to form groups, expose the group default") เพิ่ม `IA` เข้าไปในรายการ code ของ form groups และเปิดเผย `is_default` ใน `ReportTemplateEdit.tsx`
- **2026-07-24** — `bf7a28a` เพิ่มหน้า `ReportFormGroupManagement` เอง; `ea699bc` เพิ่ม component `GroupCard` (§3.2); `aa454d3` ดึงรายการ code แบบตายตัวออกจาก `ReportTemplateEdit.tsx` ไปเป็น constant ที่ใช้ร่วมกัน `src/constants/reportGroups.ts` (§3.4); `2a73a4d` ต่อ action **Add** ต่อการ์ดให้ pre-fill เทมเพลตใหม่ (§3.2) วันเดียวกัน `b707b0a` แทนที่การเรียก `perpage: -1` ("fetch ทั้งหมด") แบบเดิมด้วยการ fetch แบบ paginate ตามที่อธิบายใน §3.1 — เวอร์ชันแรกสุดของโมดูลนี้ต้องแก้ปัญหานี้ตั้งแต่วันแรก
- **2026-08-22** — `f62a90ec` เพิ่มบรรทัด audit แบบย่อต่อแถว (§3.2)

ความสามารถหนึ่งอย่างที่ไม่ได้ย้ายมาด้วยคือ **การกำหนด default ต่อ business unit** โมดูลเดิมสามารถ route เทมเพลต default ต่างกันไปยัง business unit ต่างกันสำหรับเอกสารประเภทเดียวกันได้ แต่ไม่มีสิ่งใดในกลไก `is_default` ของหน้าจอนี้ทดแทนสิ่งนั้น — หนึ่งกลุ่มมี default ได้พอดีหนึ่งตัวทั้งแพลตฟอร์ม หรือไม่มีเลย

## 3. แนวคิดสำคัญ

### 3.1 การดึงข้อมูลและการจัดกลุ่ม

`fetchAll()` ดึงข้อมูลผ่าน `reportTemplateService.getAll()` เป็นชุดละ 500 (`PAGE_SIZE`) เรียง `name:asc` กรองฝั่ง server ด้วย `template_type: 'form', deleted_at: null` มันดึงหน้าถัดไปต่อไปเรื่อย ๆ จนกว่าจะได้หน้าที่ว่าง จนกว่าจำนวนสะสมจะถึง `paginate.total` ที่ server รายงาน หรือ — เฉพาะเมื่อไม่มีการรายงาน total เลย — จนกว่าหน้าหนึ่งจะสั้นกว่า 500 ค่าคงที่ `MAX_PAGES` (50) เป็นเพียง guard กันการวิ่งไม่รู้จบ ไม่ใช่ข้อจำกัดที่จะเจอได้ในการใช้งานปกติ (50 × 500 = 25,000 form template) นี่หมายความว่าการจัดกลุ่มด้านล่างจะไม่ทำงานบนข้อมูลที่ดึงมาไม่ครบโดยไม่รู้ตัว แลกกับการต้องขอหนึ่งหน้าเต็มเสมอแม้จะมี form template แค่ไม่กี่ตัว การค้นหามี shortcut ของตัวเอง: `useGlobalShortcuts({ onSearch: ... })` โฟกัสช่องค้นหาผ่านคีย์บอร์ด เหมือนธรรมเนียมของหน้ารายการอื่น ๆ ใน SPA

แถวถูกจัดกลุ่มด้วย `t.report_group` โดยใช้ค่า sentinel ตัวอักษร `(none)` สำหรับแถวที่ไม่มี `report_group` เลย ภายในกลุ่ม แถวเรียงลำดับ default ก่อน แล้วตามด้วยชื่อ (`sortRows`)

### 3.2 การ์ดกลุ่ม

Header (`PageHeader` หัวข้อผูกกับ i18n key `nav.formGroups`, "Form Groups") มีปุ่ม **New Form Template** gate ด้วย `report_template.create` ที่ navigate ไป `/report-templates/new` พร้อม router state `{ template_type: 'form' }` ด้านล่างเป็นแถบ filter: ช่องค้นหา (จับคู่ code ของกลุ่มหรือชื่อเทมเพลต ไม่สนตัวพิมพ์เล็กใหญ่) และ checkbox "Active only" ที่ filter แถว *ภายใน* แต่ละการ์ด — ไม่เคยซ่อนการ์ดทั้งใบที่ตรงเงื่อนไขอื่น

Grid การ์ด (`GroupCard`, `../carmen-platform/src/pages/reportFormGroups/GroupCard.tsx`) render หนึ่งการ์ดต่อกลุ่ม:

- code ของกลุ่มเป็น badge outline แบบ monospace บวกจำนวนเทมเพลต — `"{n} template"` เมื่อมีพอดีหนึ่งตัว, `"{n} templates"` กรณีอื่น (catalog มีทั้งสองรูป; ภาษาไทยใช้สตริงเดียวสำหรับทั้งคู่ เพราะภาษาไทยไม่ผันตามจำนวน)
- ปุ่ม **Add** ต่อการ์ด gate ด้วย `report_template.create` navigate ไปสร้างพร้อม state `{ template_type: 'form', report_group: <code> }` (ไม่มีสำหรับการ์ด `(none)`)
- banner เตือนข้อความตรงตัว `No default set — pick one.` เมื่อกลุ่มมีเทมเพลตอย่างน้อยหนึ่งตัวแต่ไม่มีตัวไหนเป็น default
- หนึ่งแถวต่อเทมเพลต: radio button (checked เมื่อ `is_default`), ชื่อเทมเพลตพร้อมบรรทัด audit แบบย่อด้านล่าง, badge สถานะ **Active/Inactive**, badge ประเภท **Standard**/`Custom`, ลิงก์ **Edit** ไป `/report-templates/:id/edit`, และ — gate ด้วย `report_template.update` — เมนู kebab พร้อม action เดียว
- empty state, `No form templates` / `No form templates in {code} yet.`, เมื่อรายการแถวของการ์ด (**หลัง** ผ่าน filter ค้นหา/active-only แล้ว — ดู [กรณีขอบเขต](#5-กรณีขอบเขต)) ว่างเปล่า

บรรทัด audit (เพิ่มเมื่อ 2026-08-22, commit `f62a90ec54b72cde4fcbc9b77a17650b0e3c389b`) render โดย `<AuditMeta variant="compact" verbKey={...} actor={...}>` โดย `latestActor()` (`../carmen-platform/src/utils/audit.ts:101-108`) เลือกว่า created หรือ updated ตัวไหนล่าสุดกว่า แล้วคืน **key** ของ i18n — `common.audit.created` ("Created") หรือ `common.audit.updatedDate` ("Updated") — ไม่ใช่สตริงตายตัว; component ประกอบเป็น `<verb> <relative> · <name>` (`AuditMeta.tsx:62-70`) นี่คือการแก้ bug ที่ comment ใน source บน `latestActor()` เองบรรยายไว้: เวอร์ชันก่อนหน้าคืนคำอังกฤษตายตัว ทำให้เกิดบรรทัดผสมภาษาแบบ "Updated 23 วันที่แล้ว" ในโหมดไทย เมื่อส่วน relative-time ถูกแปลแล้วแต่คำกริยายังไม่ถูกแปล

Radio จะ disabled เมื่อ `!canWrite || !t.is_active || busy` (`disableRadio`); label ของมันมี tooltip `title` ซึ่งข้อความ — อ่านตรงตัวจาก i18n catalog, `pages.reportFormGroups.activateFirstTitle` — คือ `Activate the template to make it the default` แสดงเฉพาะเมื่อเทมเพลต inactive การคลิก radio ที่ยังไม่ checked และไม่ disabled จะเรียก `onRequestDefault` เปิด confirm dialog ใน §3.3

action เดียวของเมนู kebab สลับ Activate/Deactivate (gate ด้วย `report_template.update`) และ disabled (`lockDeactivate = t.is_default && t.is_active`) เมื่อการ deactivate จะทำให้ default ปัจจุบันของกลุ่ม inactive — label ของเมนูตอนนั้นจะมี suffix ตรงตัว `" (default)"` ต่อท้ายด้วย (`pages.reportFormGroups.defaultSuffix`) ทำให้เห็น item "Deactivate (default)" แบบ disabled ไม่ใช่ถูกซ่อน admin ต้องมอบหมาย default ของกลุ่มไปที่อื่นก่อนจึงจะ deactivate เทมเพลตที่ถือ default อยู่ได้

### 3.3 การตั้งค่า Default ของกลุ่ม

การคลิก radio ที่ยังไม่ checked และไม่ disabled จะเปิด confirm dialog ข้อความของมันประกอบจาก i18n template สองตัว และถูกยกมาตรงตัวตามที่อยู่ใน `../carmen-platform/src/i18n/en.ts` (`pages.reportFormGroups.setDefaultConfirm` / `.setDefaultReplaces`) — เป็น double quote ไม่ใช่ single quote:

> `Set "{name}" as the default for {code}?` — แสดงเสมอ — ตามด้วย `Replaces "{name}".` เมื่อมี default เดิมอยู่

`{name}` ตัวที่สองคือชื่อของ default **เดิม** ไม่ใช่ของเป้าหมาย; สองบรรทัดนี้เป็นสตริง i18n แยกกันสองตัวที่ต่อกันใน component ไม่ใช่ template เดียวที่มี placeholder สองแบบต่างกัน

การยืนยันจะเรียก `reportTemplateService.setGroupDefault({ current, target })` (`../carmen-platform/src/services/reportTemplateService.ts:81-99`) ซึ่งเป็น **สอง `PUT /api-system/report-templates/:id` ที่เรียงตามลำดับ ไม่ใช่ transaction เดียว**: ตัวแรก `{ is_default: false }` บน default เดิม (ข้ามไปเลยถ้าไม่มี) แล้วตามด้วย `{ is_default: true }` บนเป้าหมาย — แต่ละตัวพก `doc_version` ของตัวเองสำหรับตรวจ optimistic-lock และเป็น partial update (แก้เฉพาะสองฟิลด์ที่ส่งไป ส่วนที่เหลือ backend เก็บไว้เหมือนเดิม) ฟังก์ชันยังมี short-circuit (`if (current && current.id === target.id) return;`) ถ้าถูกขอให้แทนที่ default ด้วยตัวมันเอง — ในทางปฏิบัติ path นี้ไปไม่ถึงจาก UI ของหน้าจอนี้เอง เพราะ caller (`requestDefault`) กรอง id ของเป้าหมายออกจาก `current` ไปแล้วตั้งแต่ตอนหา — guard นี้เป็นการป้องกันเชิงรับ ไม่ใช่กลไกที่ path เรียกจริงต้องพึ่ง ความขัดแย้งเวอร์ชัน `409` บน `PUT` ตัวใดก็ตามจะเรียก toast `notifyVersionConflict()` ที่ใช้ร่วมกันและ re-fetch รายการทั้งกลุ่มใหม่; ความล้มเหลวอื่นแสดง toast ทั่วไป "Failed to set default" ตามด้วย re-fetch เช่นกัน เพื่อให้ UI สะท้อน state จริงที่เกิดขึ้น

ฐานข้อมูลบังคับ invariant ที่ flow สองขั้นนี้พยายามรักษาไว้: `idx_report_template_default_per_group` เป็น partial unique index บน `tb_report_template(report_group)` `WHERE is_default AND template_type = 'form' AND deleted_at IS NULL` เพิ่มโดย migration `20260723120000_print_form_default` เดียวกับที่กล่าวใน §2 เพราะสอง `PUT` ไม่ได้อยู่ใน transaction เดียว จึงมีช่วงแคบ ๆ ระหว่างสองการเรียกที่กลุ่มนั้นมี default **เป็นศูนย์** แทนที่จะมีพอดีหนึ่งตัว ว่า request ตั้ง default ของ admin คนที่สองที่เกิดขึ้นพร้อมกันในช่วงเดียวกันจะ fail แบบสะอาด (unique-violation ปรากฏเป็น error) หรือ race แบบคาดเดาไม่ได้ ยังไม่ได้ทดสอบแยกในรอบนี้ — ระบุเป็น edge case ที่ยังไม่ยืนยันทั้งสองทาง (§5)

การตั้งเทมเพลตที่ **inactive** เป็น default ใหม่ผ่าน radio ถูกป้องกันแยกต่างหากอยู่แล้ว เพราะ `disableRadio` ครอบคลุม `!t.is_active` ไว้แล้ว (§3.2) — admin ต้อง activate เทมเพลตก่อนจึงจะเป็น default ของกลุ่มได้

### 3.4 กลุ่มแบบตายตัว vs. Legacy

Grid จะ render 12 code ใน `FORM_REPORT_GROUPS` เสมอ (`../carmen-platform/src/constants/reportGroups.ts:6-8`): `PR, PO, GRN, SR, CN, SI, SO, IA, PC, SC, RFP, EOP` ตามลำดับตายตัวนั้น แม้ code หนึ่งจะยังไม่มี form template เลยก็ตาม — เพื่อให้ admin เห็นรายการชนิดเอกสารที่ต้องมี default ครบถ้วนตามหลักการเสมอ ไม่ใช่แค่ตัวที่มีข้อมูลอยู่แล้ว ค่า `report_group` ใด ๆ ที่มีอยู่ในข้อมูลแต่ **ไม่** อยู่ในรายการตายตัว ("legacy" code รวมถึง bucket ตัวอักษร `(none)` สำหรับแถวที่ไม่มีกลุ่มเลย) ก็ยังได้การ์ดของตัวเอง เรียงตามตัวอักษรและต่อท้ายหลัง 12 code ตายตัว — แต่จะแสดงเฉพาะเมื่อมีอย่างน้อยหนึ่งแถวเหลือหลัง filter ค้นหา/active-only; legacy code ที่ไม่มีอะไรเหลือจะไม่ถูก render เป็นการ์ดว่างแบบที่ code ตายตัวเป็น (§5)

## 4. บทบาทและสิทธิ์

| Surface | Gate | Key |
|---|---|---|
| Route `/report-form-groups` | `requiredPermission` + `feature` | `report_template.read` + `report_form_groups` |
| รายการ sidebar "Form Groups" | `permission` + `feature` filter (`platformNav.ts`) | `report_template.read` + `report_form_groups` |
| ปุ่ม **New Form Template** ที่ header | `hasPermission` (ผ่าน `<Can>`) | `report_template.create` |
| ปุ่ม **Add** ต่อการ์ด | prop `canCreate` ตรวจสอบเดียวกัน | `report_template.create` |
| Radio ตั้ง default, เมนู kebab | prop `canWrite` | `report_template.update` |

ไม่มี **permission** key ใหม่ถูกเพิ่มสำหรับโมดูลนี้ — ถูก gate ทั้งหมดด้วย catalog `report_template.*` เดียวกันที่บันทึกไว้ครบถ้วน (matrix ของ route, bootstrap exception, ตาราง effective-access) บน [เทมเพลตรายงาน — Permissions](/th/platform/report-templates/permissions) แต่มัน **มี** key **feature** ของตัวเอง (`report_form_groups` แยกจาก `report_templates` ของ Report Templates): การเปลี่ยน feature flag ของโมดูลหนึ่งไม่กระทบอีกโมดูล session ที่มีแค่ `report_template.read` จะดูได้ทุกกลุ่มและ default ปัจจุบันของทุกเทมเพลต แต่จะไม่เห็นปุ่ม **New Form Template**/**Add** ไม่เห็นเมนู kebab และไม่สามารถเลือก radio default ตัวอื่นได้ — radio นั้น render แบบ disabled ไม่ใช่ซ่อน

## 5. กรณีขอบเขต

| สถานการณ์ | พฤติกรรม |
|---|---|
| แถวที่เหลือของกลุ่มตายตัวถูก filter ออกหมดด้วย "Active only" | การ์ดยังคง render อยู่ (code ตายตัว render เสมอเมื่อไม่มีคำค้นหา — §3.4) แต่แสดง empty state เดียวกันคือ `No form templates in {code} yet.` เหมือนกลุ่มที่ไม่มีเทมเพลตเลยจริง ๆ ไม่มีข้อความแยกสำหรับ "ทุกอย่างแค่ถูกซ่อนโดย filter" |
| แถวที่เหลือของกลุ่ม legacy ถูก filter ออกหมดด้วย "Active only" | การ์ด **หายไปทั้งใบ** — สาขา legacy จะ render code ก็ต่อเมื่อมีอย่างน้อยหนึ่งแถวรอดจาก filter เท่านั้น ไม่มี state แยกสำหรับ "ถูกกรองออกหมด" นี่คือความไม่สมมาตรจุดเดียวระหว่าง code ตายตัวกับ legacy นอกเหนือจากกฎการเรียงลำดับใน §3.4 |
| คำค้นหาไม่ตรงทั้ง code ตายตัวและแถวใด ๆ ของมัน | นี่คือกรณีเดียวที่การ์ด code ตายตัวจะหายไปจากมุมมองได้ — การ์ดตายตัวใบอื่นทุกใบยังคงแสดงเสมอไม่ว่าคำค้นหาจะเป็นอะไร |
| admin สองคนแข่งกันตั้ง default ของกลุ่มเดียวกัน | partial unique index ของฐานข้อมูลรับประกันว่ามี default ลงได้อย่างมากหนึ่งตัว แต่คู่ `PUT` สองขั้นที่ไม่ใช่ transaction เดียว (§3.3) หมายความว่ามีช่วงจริงที่ default เป็นศูนย์; รูปแบบความล้มเหลวที่แน่ชัดของฝ่ายที่แพ้ยังไม่ได้ทดสอบแยก |
| การตั้ง default บนเทมเพลตที่ inactive | ถูกป้องกันฝั่ง client: radio disabled ขณะ `!t.is_active` พร้อม tooltip บอก admin ให้ activate เทมเพลตก่อน |
| การ deactivate default ปัจจุบันของกลุ่มที่ยัง active | ถูกป้องกันฝั่ง client: item Deactivate ของ kebab disabled (`lockDeactivate`) และมี suffix `(default)` ให้เห็น จนกว่า admin จะมอบหมาย default ไปที่อื่นในกลุ่ม |

## 6. โมดูลที่เกี่ยวข้อง

- [Report Templates](/th/platform/report-templates) — เป็นเจ้าของ `tb_report_template`, คอลัมน์ `template_type`/`is_default`/`report_group` ที่หน้าจอนี้แก้ไข และหน้า Edit ที่ลิงก์ **Edit** ของทุกแถวเปิด; ยังมีเรื่องเล่าการสืบทอดฉบับเต็มจากฝั่งโมดูลด้วย
- [เทมเพลตรายงาน — Permissions](/th/platform/report-templates/permissions) — matrix gate `report_template.*` ฉบับเต็มที่หน้าจอนี้ reuse โดยไม่เปลี่ยนแปลง
- **Print Template Mapping** — โมดูลที่หน้าจอนี้เข้ามาแทนที่หน้าที่ ถูกลบออกจากผลิตภัณฑ์ผ่าน 2026-07-23/24 (§2) หน้า wiki ของมันถูกลบไปแล้ว การสืบทอดตอนนี้ถูกบันทึกไว้บนหน้านี้ บน [Report Templates](/th/platform/report-templates) และบน [Changelog](/th/platform/changelog) §6

## 7. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/pages/ReportFormGroupManagement.tsx` — หน้า: paged fetch, การจัดกลุ่ม, filter ค้นหา/active, handler ตั้ง default และ toggle activate
- `../carmen-platform/src/pages/reportFormGroups/GroupCard.tsx` — การ์ดต่อกลุ่ม: radio, บรรทัด audit แบบย่อ (`latestActor()` + `AuditMeta variant="compact"`), badge, ลิงก์ Edit, เมนู kebab, empty state, banner ไม่มี default
- `../carmen-platform/src/constants/reportGroups.ts` — `FORM_REPORT_GROUPS` ลำดับ 12 code ตายตัว
- `../carmen-platform/src/services/reportTemplateService.ts:81-99` — `setGroupDefault` (สอง `PUT` ตามลำดับ); `:66-69` `update`; `:47-54` `getAll`
- `../carmen-platform/src/utils/docVersion.ts` — `getDocVersion`, `isVersionConflict`, `notifyVersionConflict`
- `../carmen-platform/src/utils/audit.ts:101-108` — `latestActor()`; `../carmen-platform/src/components/AuditMeta.tsx:62-70` — การ render ของ variant compact
- `../carmen-platform/src/i18n/en.ts` (block `reportFormGroups`, "slice 6: Report Templates") — ทุกสตริง UI ที่ยกมาตรงตัวบนหน้านี้ อ่านจาก source ตรง ๆ ไม่ใช่ paraphrase
- `../carmen-platform/src/App.tsx:322-329` — route `/report-form-groups` (`requiredPermission="report_template.read"`, `feature="report_form_groups"`); `../carmen-platform/src/components/nav/platformNav.ts:25` — รายการ sidebar
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260723120000_print_form_default/migration.sql` — คอลัมน์ `is_default`, backfill จาก `tb_print_template_mapping`, partial unique index `idx_report_template_default_per_group`, การเปลี่ยนชื่อ `RFQ`→`RFP`, และ `DROP TABLE tb_print_template_mapping`
- `../carmen-platform-e2e/tests/` — ตรวจสอบ directory โดยตรง (HEAD `a8e3b31`, 2026-08-25) ยืนยันว่าไม่มี directory `report-form-groups`/`form-groups` และ `tests/report-templates/` (`report-template-crud.spec.ts`, `report-template-list.spec.ts`) ก็ไม่ครอบคลุมหน้าจอนี้เช่นกัน
- Commit: `de11377` (ลบฝั่ง frontend, 2026-07-24), `c135bb21e` (ลบฝั่ง backend, 2026-07-23, `../carmen-turborepo-backend-v2`), `cd4fc5d` (เปิดเผย group default + เพิ่ม IA, 2026-07-23), `bf7a28a` (เพิ่มหน้า, 2026-07-24), `ea699bc` (เพิ่ม `GroupCard`, 2026-07-24), `aa454d3` (ดึง `FORM_REPORT_GROUPS` ออกมา, 2026-07-24), `2a73a4d` (pre-fill ตอน Add, 2026-07-24), `b707b0a` (แก้ pagination, 2026-07-24), `f62a90ec54b72cde4fcbc9b77a17650b0e3c389b` (เพิ่มบรรทัด audit, 2026-08-22) — ทั้งหมดอยู่ใน `../carmen-platform` ยกเว้นที่ระบุไว้

## 8. หน้าในโมดูลนี้

โมดูลนี้เป็นหน้าเดียว ดู [ดัชนีหนังสือ Platform](/th/platform) ซึ่งเป็นหน้าแม่
