---
title: Report Templates — สิทธิ์ (Permissions)
description: Route guard ตาม permission key, gate Can ภายในหน้า, filter ของ sidebar และข้อยกเว้น bootstrap สำหรับ surface ของ report-templates อัพเดทสำหรับการเปลี่ยนชื่อเป็น Forbidden และการลบโมดูล print-template-mapping ข้างเคียง
published: true
date: 2026-09-06T01:00:00.000Z
tags: book/platform, report-templates, permissions
editor: markdown
dateCreated: 2026-06-10T17:00:00.000Z
---

# Report Templates — สิทธิ์ (Permissions)

> **At a Glance**
> **Gate:** route ของ report-templates ทั้งสามถือ `requiredPermission="report_template.read"` / `"report_template.create"` / `"report_template.update"` **และ** `feature="report_templates"` บน `PrivateRoute` (`src/App.tsx` block ของ route report-templates) &nbsp;·&nbsp; **Gate ภายในหน้า:** `<Can>` ห่อ Add Template (`report_template.create`, ทั้งปุ่ม header **และ** ปุ่ม empty-state — ไม่มีตัวใดที่ไม่ถูก gate), Edit ของ row (`report_template.update`), Delete ของ row (`report_template.delete`), **View History** ของ row/หน้า edit (`activity_log.read`, `clusterId={PLATFORM_SCOPED_RECORD}` — ฟีเจอร์ Activity Trail ข้ามโมดูลใหม่) และ toggle Edit ของหน้า edit (`report_template.update`) — ไม่มีตัวใดส่ง `clusterId` จริง &nbsp;·&nbsp; **`report_template.delete` อยู่ภายในหน้าเท่านั้น** — ไม่มี route ใดต้องการมัน &nbsp;·&nbsp; **ข้อยกเว้น bootstrap:** `hasPermission` คืน `true` อย่างไม่มีเงื่อนไขเมื่อ `userCount !== null && userCount <= 1` &nbsp;·&nbsp; **เมื่อไม่ผ่าน:** หน้า `Forbidden` (`src/pages/Forbidden.tsx` เปลี่ยนชื่อจาก `AccessDenied` แบบ inline เดิม) render ในตำแหน่งเดิมภายใน `<Layout>` (sidebar ยังมองเห็นอยู่) &nbsp;·&nbsp; **ตั้งแต่ 2026-07-23:** key permission `report_template.read` ของ sidebar/route ใช้ร่วมกับรายการเมนู Form Groups (`/report-form-groups`) ด้วย — แต่ **key feature แยกกัน** (`report_form_groups` ไม่ใช่ `report_templates`); key `print_template_mapping.*` ที่หน้านี้เคยอ้างอิงไม่มีอยู่แล้ว (โมดูลถูกลบ) &nbsp;·&nbsp; **เอกสาร model ฉบับ canonical:** [rbac permissions](/th/platform/rbac/permissions)

## 1. ภาพรวม

Report Templates เป็น surface สำหรับ authoring ภายในของ Carmen สำหรับเอกสารที่พิมพ์และส่งออกได้ซึ่ง ship เป็นส่วนหนึ่งของ contract การ customise ของแพลตฟอร์ม เทมเพลตถูกเขียนโดยวิศวกร support ของ Carmen — ไม่ใช่ลูกค้า — ด้วย editor XML/FastReport แบบมีโครงสร้างที่ผูก data source เข้ากับ schema ของ tenant เนื่องจากการเขียนเทมเพลตต้องอาศัยความรู้เชิงปฏิบัติการระดับแพลตฟอร์มและส่งผลโดยตรงต่อสิ่งที่ลูกค้าพิมพ์หรือส่งออกจาก business unit ของตนได้ การเข้าถึงจึงถูกกำกับด้วย model RBAC แบบอิง permission ของแพลตฟอร์ม ([rbac](/th/platform/rbac)): catalog ฝั่ง backend นิยาม key `report_template.read`, `report_template.create`, `report_template.update` และ `report_template.delete`; role รวม key เหล่านั้นเป็นชุด; และ assignment ผูก role เข้ากับผู้ใช้

กลไกการ gate มีสามชั้น ทั้งหมด resolve ผ่านเส้นทาง `AuthContext.hasPermission` → `checkPermission` เดียวกัน (อธิบายอัลกอริทึมไว้ใน [rbac permissions](/th/platform/rbac/permissions) §4) ที่ระดับ route `PrivateRoute` รับ prop `requiredPermission` และ render หน้า `Forbidden` ในตำแหน่งเดิมภายใน shell `<Layout>` ปกติเมื่อการตรวจสอบไม่ผ่าน (เปลี่ยนชื่อจาก component `AccessDenied` แบบ inline เดิม — ดู §5) ที่ระดับ navigation `buildPlatformNav()` ของ `platformNav.ts` filter sidebar เพื่อให้ผู้ใช้ที่ไม่มี `report_template.read` ไม่มีวันเห็นรายการ Report Templates ที่ระดับ action `<Can permission="report_template.*">` ห่อปุ่มที่แก้ไขข้อมูลบนหน้าจอ report-templates (และตั้งแต่ 2026-07-23 หน้าจอ Form Groups ใหม่ — §7) ต่างจาก gate ของ cluster **ไม่มี gate ของ report-template ตัวใดส่ง `clusterId`** — เทมเพลตรายงานเป็น tenant-global ดังนั้นทุกการตรวจสอบ resolve ผ่าน branch แบบกว้างโดยไม่มีการจำกัดต่อ cluster

จนถึง 2026-06 route เหล่านี้เคยถูก gate ด้วย array ของ role enum แบบ hardcode (`platform_admin`, `support_manager`, `support_staff`) ที่ซ้ำกันอยู่ใน route guard ทั้งสามตัว; model นั้นถูกถอดออกจาก SPA, gate ของ login และ Prisma schema โดยสมบูรณ์แล้ว — การ map ของ migration document ไว้ใน [rbac](/th/platform/rbac) §5 และไม่ทวนซ้ำที่นี่

## 2. Route guard

| Route | Component ที่ render | `requiredPermission` | `feature` | แหล่งที่มา |
|---|---|---|---|---|
| `/report-templates` | `ReportTemplateManagement` | `report_template.read` | `report_templates` | `src/App.tsx` (block ของ route report-templates) |
| `/report-templates/new` | `ReportTemplateEdit` | `report_template.create` | `report_templates` | `src/App.tsx` |
| `/report-templates/:id/edit` | `ReportTemplateEdit` | `report_template.update` | `report_templates` | `src/App.tsx` |
| `/report-form-groups` | `ReportFormGroupManagement` | `report_template.read` | `report_form_groups` | **เพิ่มเมื่อ 2026-07-23** `src/App.tsx`; ไม่ใช่หนึ่งในสาม route เดิมที่หน้านี้เคย document แต่ถูก gate ด้วย key permission ตระกูลเดียวกัน — ดู §7 key **feature** ของมันเป็นของตัวเอง (`report_form_groups`) ไม่ได้ใช้ร่วมกับสามแถวข้างบน |

แต่ละ route ถือ key permission เดียวพอดี ต่างจาก array ของ role ที่ซ้ำกันแบบ legacy key เดิมทั้งสามจงใจต่างกันต่อ route ดังนั้น surface ของ list, create และ edit สามารถมอบให้แยกกันได้ — role แบบ read-only ที่รวมเฉพาะ `report_template.read` ตอนนี้เขียนออกมาได้แล้ว

ทุก route ยังถือ prop `feature` บน `PrivateRoute` ด้วย `feature` ถูกตรวจสอบ**หลัง**จาก `requiredPermission` เสมอ (และหลังการตรวจ `requireSuperAdmin` ถ้ามี) — session ที่ไม่มี permission ยังเห็น `Forbidden` เหมือนเดิม ไม่ใช่ `NotFound`/`ComingSoon` จาก feature เพื่อไม่ให้ feature ที่ถูกปิดกลายเป็น "หน้าไม่มีอยู่" สำหรับคนที่ไม่มีสิทธิ์เข้าอยู่แล้วตั้งแต่ต้น เมื่อ state ของ feature เป็น `hide` `PrivateRoute` จะ render `NotFound`; เมื่อเป็น `inactive` จะ render `ComingSoon` เรื่องนี้แยกจากการ filter ระดับ sidebar ด้วย feature ใน §6

สี่ข้อที่ควรสังเกต:

- **Route guard ตรวจสอบโดยไม่มี `clusterId`** `PrivateRoute` เรียก `hasPermission(requiredPermission)` โดยไม่มี options ผ่าน branch แบบกว้าง "scope ใดก็มอบให้ได้" เนื่องจาก gate `<Can>` ภายในหน้าบน surface นี้ก็ละเว้น `clusterId` เช่นกัน (§7) role assignment ที่ scope ไปยัง cluster เดียวซึ่ง role รวม key `report_template.*` จึงผ่านได้ทุกที่ — ไม่มีการจำกัดต่อ cluster ที่ใดเลยบน surface นี้ ซึ่งสอดคล้องกับ data model: เทมเพลตรายงานเป็น tenant-global และไม่มี cluster FK ([Data Model](/th/platform/report-templates/data-model) §3)
- **ไม่มี route ใดต้องการ `report_template.delete`** การลบเข้าถึงได้ทาง row action ของหน้า list เท่านั้น gate ภายในหน้า (§7)
- **ไม่มีการใช้ key ซ้ำข้ามโมดูล** key `report_template.*` gate เฉพาะโมดูลนี้ (รวม Form Groups แล้วตอนนี้) — ต่างจาก route ของ Business Units ที่ใช้ key `cluster.*` ซ้ำ (ดู [Clusters Permissions](/th/platform/clusters/permissions) §2)
- **ถูกลบเมื่อ 2026-07-24** (carmen-platform commit `de11377`; key `print_template_mapping.*` ถูกลบออกจาก permission-catalog seed ก่อนหน้าหนึ่งวันคือ 2026-07-23, carmen-turborepo-backend-v2 commit `c135bb21e`): โมดูล print-template-mapping พี่น้องและ key ของมันไม่มีอยู่แล้ว — โมดูลนั้นถูกลบไปเลย ไม่ใช่แค่ตัดการเชื่อมโยงจากโมดูลนี้

## 3. เมทริกซ์ effective access

อ่านตารางในความหมาย "session ที่ถือ grant นี้พอดีทำอะไรได้บ้างบน surface ของ report-templates" grant รวมกันแบบ additive; session **super-admin** (flag `is_super_admin`) bypass ทุก row และทำได้ทุกอย่าง gate ของ SPA เป็นเชิงคำแนะนำ — การบังคับใช้ permission ของ backend เองคือขอบเขต security ที่แท้จริง

| Grant ที่ถือ | list `/report-templates` | Add Template | Edit ของ row / หน้า edit | Delete ของ row | หมายเหตุ |
|---|---|---|---|---|---|
| ไม่มี key `report_template.*` เลย | `Forbidden`; รายการ sidebar ถูกซ่อน | — | — | — | ยังพิมพ์ URL ได้; route guard จับไว้ |
| `report_template.read` | list เต็ม, ค้นหา, filter, ส่งออก CSV | ซ่อน — ปุ่ม Add ทั้ง header และ empty-state ถูก gate ด้วย `<Can permission="report_template.create">` เหมือนกัน | Edit ของ row ถูกซ่อน; route `/report-templates/:id/edit` ถูก block | ซ่อน | persona แบบ read-only; เมนู row-action render ว่างเปล่า (ยกเว้นรายการ **View History** เมื่อถือ `activity_log.read` ด้วย) |
| + `report_template.create` | — | แสดงและใช้งานได้ | — | — | ฟอร์ม create แก้ไขได้ทันทีเมื่อ route guard ผ่าน |
| + `report_template.update` | — | — | Edit ของ row บนทุก row; route edit เปิดได้; toggle Edit render | — | ปลดล็อกฟอร์ม edit เต็มรูปแบบ รวมถึง editor XML, chip ขอบเขต BU, probe Browse-in-BU |
| + `report_template.delete` | — | — | — | Delete ของ row render | ภายในหน้าเท่านั้น; ไม่มี route ใดต้องการ key นี้ |

เนื่องจากไม่มี gate ใดบน surface นี้ส่ง `clusterId` จึงไม่มี row ของ scoped grant ในเมทริกซ์นี้ — assignment ที่ scope ต่อ cluster ประพฤติเหมือน assignment ที่ scope ทั้งแพลตฟอร์มทุกประการที่นี่ (§2) ข้อยกเว้น bootstrap (§4) สามารถ override ทุกคอลัมน์ให้ session ใดก็ได้ตราบที่ `userCount <= 1`

## 4. ข้อยกเว้น bootstrap

`hasPermission()` ใน `AuthContext.tsx` ยกทางลัด first-admin จาก model legacy มาด้วย: เมื่อ `userCount !== null && userCount <= 1` ฟังก์ชันคืน `true` อย่างไม่มีเงื่อนไข — route guard, filter ของ sidebar และ gate `<Can>` ทุกตัวผ่าน รวมถึง gate ของ report-template ทั้งหมด รายละเอียด implementation ฉบับเต็ม — `userCount` ถูก populate อย่างไร, ปฏิสัมพันธ์กับ gate ของ login และ pseudo-code ของการ resolve — อยู่ใน [rbac permissions](/th/platform/rbac/permissions) §4 caveat เดียวกันมีผลกับ report-templates:

- **ระหว่างหน้าต่างเวลาที่ API กำลังโหลด** (`userCount === null`): เงื่อนไขเป็น `false` ดังนั้นการตรวจสอบรันเทียบกับ snapshot ของ permission อย่างเข้มงวด — ข้อยกเว้น fail แบบ closed ไม่ใช่ open session ที่ไม่มี `report_template.read` ที่เข้า `/report-templates` ก่อนการ fetch count จะ resolve เห็น `Forbidden`
- **เมื่อ `userCount > 1` แล้ว**: ข้อยกเว้นอยู่ในสถานะหลับ count refresh เฉพาะตอน mount และตอน login — การลบผู้ใช้ระหว่าง session ไม่ re-arm มันจนกว่าจะถึงการ refresh ครั้งถัดไป
- **ขอบเขต**: ภายใต้ model แบบ permission branch ของ bootstrap ยังไปถึง gate ของ login ด้วย — `login()` ข้ามข้อกำหนดต้องถืออย่างน้อยหนึ่ง permission เมื่อจำนวนผู้ใช้เป็น 0 หรือ 1

## 5. Forbidden (เปลี่ยนชื่อจาก AccessDenied)

กลไกเดียวกับ [Clusters Permissions §5](/th/platform/clusters/permissions) `PrivateRoute` (`src/components/PrivateRoute.tsx` รวม 40 บรรทัด) implement เส้นทางการปฏิเสธสองแบบที่แตกต่างกัน:

**Auth-fail (ไม่มี session):** ถ้า `isAuthenticated` เป็น `false` component render `<Navigate to="/login" replace />` — redirect แบบ hard ที่แทนที่ history entry ปัจจุบัน ผู้ใช้ไปจบที่หน้า login โดยไม่มี error ที่มองเห็นได้ใน view ปัจจุบัน

**Permission-fail (authenticated แต่ขาด key):** ถ้า `requiredPermission` ถูกตั้งค่าและ `hasPermission(requiredPermission)` คืน `false` component render `<Forbidden />` **ในตำแหน่งเดิม** — หน้าเฉพาะ (`src/pages/Forbidden.tsx`) ไม่ใช่ component `AccessDenied` แบบ inline ภายใน `PrivateRoute.tsx` ที่ sync ครั้งก่อนอธิบายไว้อีกต่อไป การ render ในตำแหน่งเดิม (แทนที่จะ redirect ไป `/403`) รักษา URL ที่ถูก block ไว้ในแถบที่อยู่ ทำให้ action "Go Back" ของหน้าเองไม่เด้งกลับผ่าน guard ห่อด้วย `<Layout>` ดังนั้น sidebar และ header เต็มรูปแบบยังมองเห็นอยู่ แสดง icon `ShieldX`, "403", heading "Access Denied", ข้อความ generic "You don't have permission to access this page." และตอนนี้มี **สอง** action — "Go Back" (รู้บริบท fallback ไป `/dashboard`) และ "Go to Dashboard" — จาก sync ครั้งก่อนที่อธิบายไว้เพียงปุ่ม Back-to-Dashboard ปุ่มเดียว route `/403` โดยตรงก็ render หน้าเดียวกันนี้ ข้อความยังไม่ quote role ที่ทำให้ไม่ผ่าน — ไม่มีค่า role เดี่ยวให้แสดงภายใต้ model แบบ permission

ผู้ใช้แบบ permission-fail ยังอยู่ใน shell ของ SPA ยังใช้ sidebar นำทางไปยังหน้าที่ได้รับอนุญาตได้ และไม่ถูก log out — session ของพวกเขายัง valid

## 6. Filter ของ sidebar

**แก้ citation ที่ล้าสมัย:** array ของ nav sidebar ถูกนิยามใน `../carmen-platform/src/components/nav/platformNav.ts` (`ALL_PLATFORM_NAV_ITEMS`) ไม่ใช่ `Layout.tsx` — `Layout.tsx` ไม่ได้นิยาม nav row ใดเลยในปัจจุบัน มันแค่ import `buildPlatformNav()` จาก `platformNav.ts` แล้วเรียกใช้ รายการ Report Templates ในกลุ่ม "Content" คือ:

```
{ path: '/report-templates', labelKey: 'nav.reportTemplates', icon: FileText, permission: 'report_template.read', groupKey: 'navGroup.content', feature: 'report_templates' }
```

ต่อจากบรรทัดนั้นทันที (เพิ่มเมื่อ 2026-07-23): `{ path: '/report-form-groups', labelKey: 'nav.formGroups', icon: LayoutGrid, permission: 'report_template.read', groupKey: 'navGroup.content', feature: 'report_form_groups' }` — หน้าจอ Form Groups ใช้ key **permission** ตัวเดียวกัน (`report_template.read`) แต่มี **key feature ของตัวเอง** (`report_form_groups`) ไม่ใช่ `report_templates` ทั้งสองแถวตอนนี้ถือ `labelKey`/`groupKey` (i18n key ที่ sidebar resolve) ไม่ใช่ string ตายตัว `label`/`group`

`buildPlatformNav()` filter array `ALL_PLATFORM_NAV_ITEMS` เต็มชุดก่อน render:

```
return ALL_PLATFORM_NAV_ITEMS.filter(
  (item) =>
    (!item.permission || opts.hasPermission(item.permission)) &&
    (!item.superAdminOnly || opts.isSuperAdmin) &&
    (!item.feature || opts.flagOf(item.feature) !== 'hide'),
).map((item) =>
  item.feature && opts.flagOf(item.feature) === 'inactive'
    ? { ...item, comingSoon: true }
    : item,
);
```

นี่คือเงื่อนไขที่**สาม**นอกเหนือจาก permission กับ `superAdminOnly` ที่ snippet ที่ sync ครั้งก่อนอ้างไว้ไม่มี: แถวที่ flag `feature` เป็น `hide` จะถูกตัดออกจาก sidebar ไปเลย (สอดคล้องกับ `NotFound` ระดับ route ใน §2); แถวที่ flag เป็น `inactive` ยังอยู่ใน sidebar แต่ถูกทำเครื่องหมาย `comingSoon` (render แบบสีจาง ตรงกับหน้า `ComingSoon` ระดับ route)

ค่า `permission` ของ sidebar (`report_template.read`) ตรงกับ route guard ของ `/report-templates` พอดี จึงไม่มี divergence ที่รายการที่มองเห็นนำไปสู่ `Forbidden` **ถูกลบเมื่อ 2026-07-24:** รายการ **Print Mapping** ข้างเคียงเดิม (ที่ filter ด้วย key `print_template_mapping.read` ของตัวเอง) ไม่มีอยู่แล้ว — โมดูลนั้นถูกลบไปเลย ไม่ใช่แค่จัดกลุ่มใหม่ การเปลี่ยนแปลงใดในอนาคตว่า key ใด gate Report Templates ต้อง apply ทั้งใน `src/App.tsx` (route guard) และ `src/components/nav/platformNav.ts` (ฟิลด์ `permission`/`feature` ของ sidebar); การแก้ที่เดียวโดยไม่แก้อีกที่จะเปิดเผยรายการขณะ block route หรือกลับกัน

ผู้ใช้ที่ไม่มี `report_template.read` ก็แค่ไม่เห็นรายการ Report Templates หรือ Form Groups พวกเขายังเข้าถึง `/report-templates` ได้ด้วยการพิมพ์ URL โดยตรง แต่ route guard render `Forbidden` ก่อนข้อมูลเทมเพลตใด ๆ จะถูกโหลด

## 7. ภายใน surface ของ report-templates

ต่างจาก model legacy การผ่าน route guard ไม่ได้ปลดล็อกทุกปุ่มอีกต่อไป — action ที่แก้ไขข้อมูลถือ gate `<Can>` ของตัวเอง (เพิ่มเข้ามาพร้อมการ migrate สู่ RBAC) ไม่มีตัวใดส่ง `clusterId` จริง — gate ของ View History ด้านล่างส่ง sentinel `PLATFORM_SCOPED_RECORD` แทน ซึ่งไม่ใช่ cluster:

| Action | Gate ภายในหน้า |
|---|---|
| ดู list เทมเพลต (pagination, ค้นหา, filter) | ไม่มี — key ของ route (`report_template.read`) เพียงพอ |
| ส่งออก list เป็น CSV | ไม่มี — ผู้ถือ `report_template.read` คนใดก็ได้; disabled เฉพาะระหว่างโหลดหรือเมื่อว่าง |
| Add Template (ปุ่ม header) | `<Can permission="report_template.create">` |
| Add Template (ปุ่ม empty-state) | `<Can permission="report_template.create">` — **ไม่ใช่ ungated** `addAction` ของ `ReportTemplateManagement.tsx` ห่อปุ่ม empty-state ด้วย `<Can>` เดียวกันเป๊ะกับปุ่ม header (`src/pages/ReportTemplateManagement.tsx:529-536`); session ที่มีแค่ `report_template.read` จะไม่เห็นปุ่มไหนเลยทั้งสองตัว |
| Edit ของ row (dropdown ของ list) | `<Can permission="report_template.update">` |
| **View History** ของ row (dropdown ของ list, ใหม่) | `<Can permission="activity_log.read" clusterId={PLATFORM_SCOPED_RECORD}>` — ฟีเจอร์ Activity Trail ข้ามโมดูล เหมือนกับ [clusters](/th/platform/clusters)/[business-units](/th/platform/business-units)/[users](/th/platform/users)/[applications](/th/platform/applications) |
| Delete ของ row (dropdown ของ list) | `<Can permission="report_template.delete">` |
| toggle Edit (header ของหน้า edit) | `<Can permission="report_template.update">` |
| **View History** ของ hero (header หน้า edit, ใหม่) | `<Can permission="activity_log.read" clusterId={PLATFORM_SCOPED_RECORD}>` — อยู่ในแถว `actions` ของ `PageHeader` เองเคียงข้างปุ่ม Edit/Cancel แสดงเสมอเมื่อ `!isNew && !loading` (ไม่ขึ้นกับ state `editing`) |
| Save / Cancel บนฟอร์ม edit | ไม่มี — เข้าถึงไม่ได้โดยไม่ผ่าน toggle Edit ที่ถูก gate |
| การแก้ไข XML + อัพโหลดไฟล์ (แท็บ Dialog/Content) | ไม่มี — แต่ `readOnly={!editing}` จึงอยู่หลัง gate `report_template.update` ของ toggle Edit โดยพฤตินัย |
| probe Browse-in-BU (การ lookup views/functions/procedures) | ไม่มี — render เฉพาะในโหมด edit จึงอยู่หลัง toggle Edit |
| checkbox Standard / Custom และ Active / Inactive | ไม่มี — render เฉพาะในโหมด edit จึงอยู่หลัง toggle Edit |
| **หน้าจอ Form Groups** (`/report-form-groups`) — set group default | ไม่ใช้ `<Can>` ที่นี่; action "Set default" ใช้ได้กับผู้ถือ `report_template.update` คนใดก็ได้ (การมองเห็นปุ่มขับเคลื่อนด้วย `hasPermission` ไม่ใช่ wrapper `<Can>`) — **เพิ่มเมื่อ 2026-07-23** gate ด้วย key permission ตระกูลเดียวกับส่วนที่เหลือของโมดูลนี้ |
| **หน้าจอ Form Groups** — ปุ่ม "New Form Template" | แสดงเฉพาะเมื่อถือ `report_template.create` |

`PLATFORM_SCOPED_RECORD` เป็น alias ของ `UNRESOLVED_CLUSTER_ID` (`../carmen-platform/src/utils/permissions.ts`): sentinel `clusterId` ที่บังคับให้ branch แบบ scoped ของ `checkPermission` ประเมินเป็น false สำหรับ cluster จริงทุกตัว เหลือแค่ grant `activity_log.read` ระดับแพลตฟอร์มเป็นทางเดียวที่จะได้ `true` — shape ที่ถูกต้องสำหรับ record type (report template) ที่ไม่มี cluster ของตัวเอง การบันทึก activity เริ่มเมื่อ 2026-08-31 (`AUDIT_RECORDING_STARTED_ON_PHASE_2`); เทมเพลตที่สร้างก่อนหน้านั้นจะเห็น history ว่างเปล่า ไม่ใช่ที่พัง

จุดที่เรียกใช้: gate ของหน้า list ใน `ReportTemplateManagement.tsx` (`<Can>` ของ Edit/Delete/View History ของ row ใน definition ของคอลัมน์ `actions`, Add Template ใน `actions` ของ `PageHeader`); toggle Edit และ View History ของหน้า edit ใน `ReportTemplateEdit.tsx` (`actions` ของ header)

ผลพวงที่เกี่ยวข้องกับผู้ทดสอบ ข้อแรก session ที่มีเฉพาะ `report_template.read` เห็น catalogue แบบ read-only เต็มรูปแบบ: dropdown ของ row-action render แต่ว่างเปล่า (เว้นแต่ session ถือ `activity_log.read` ด้วย ซึ่งจะเห็นแค่ View History) และไม่มีทางออกผ่านปุ่ม Add Template เลย — ปุ่ม header และ empty-state ถูก gate เหมือนกันทั้งคู่ ดังนั้น session แบบ read-only จะไม่มีวันไปถึง route create ได้ด้วยการคลิกอะไรใน UI (พิมพ์ `/report-templates/new` ตรง ๆ ก็ยังโดน route guard) ข้อสอง route `/report-templates/:id/edit` เปิดให้ผู้ถือ `report_template.update` คนใดก็ได้ แต่หน้ายังเริ่มในโหมด view — toggle Edit ภายในหน้าตรวจสอบ key เดียวกันซ้ำ ดังนั้น route กับ toggle จะไม่ขัดแย้งกัน test plan ควรครอบคลุม gate ต่อ key (§3) และข้อยกเว้น bootstrap (§4) ไม่ใช่ความแตกต่างต่อ role — ไม่มี persona แบบ role-enum อีกแล้ว **ถูกลบเมื่อ 2026-07-23/24:** test plan ใดที่อ้างอิง key `print_template_mapping.*` กำลังทดสอบโมดูลที่ไม่มีอยู่แล้ว

## 8. แหล่งข้อมูลอ้างอิง

**แหล่งข้อมูลหลัก (อ่านสิ่งเหล่านี้ก่อนอัพเดทหน้านี้):**
- `../carmen-platform/src/App.tsx` — route ของ report-templates + Form Groups พร้อม prop `requiredPermission`
- `../carmen-platform/src/context/AuthContext.tsx` — `hasPermission`, state `userCount`, gate permission ตอน login
- `../carmen-platform/src/utils/permissions.ts` — การ resolve `checkPermission` แบบ pure (super-admin → key ระดับแพลตฟอร์ม → key ระดับ cluster)
- `../carmen-platform/src/components/PrivateRoute.tsx` — redirect ของ auth-fail, การ render permission-fail (รวม 40 บรรทัด)
- `../carmen-platform/src/pages/Forbidden.tsx` — หน้า 403 ที่เปลี่ยนชื่อแล้ว
- `../carmen-platform/src/components/Can.tsx` — component gate ภายในหน้า (`permission`, `clusterId` แบบ optional, `fallback` แบบ optional)
- `../carmen-platform/src/components/nav/platformNav.ts` — `ALL_PLATFORM_NAV_ITEMS` (Report Templates บรรทัด 24, Form Groups บรรทัด 25 — ทั้งคู่ `permission: 'report_template.read'` แต่ `feature` key แยกกัน) และ `buildPlatformNav()` ฟังก์ชัน filter; `src/components/Layout.tsx` ไม่ได้นิยาม nav row แล้ว มันแค่เรียก `buildPlatformNav()`
- `../carmen-platform/src/components/activityTrail/{ActivityTrailSheet,useRowActivityTrail,constants}.tsx` — ฟีเจอร์ View History (`PLATFORM_SCOPED_RECORD` นิยามใน `src/utils/permissions.ts` ด้านบน); `AUDIT_RECORDING_STARTED_ON_PHASE_2` = 2026-08-31
- `../carmen-platform/src/pages/ReportTemplateManagement.tsx` / `ReportTemplateEdit.tsx` / `ReportFormGroupManagement.tsx` — จุดเรียกใช้ `<Can>` / `hasPermission` ตามรายการใน §7

**Cross-link:**
- [rbac](/th/platform/rbac) — model ของ permission: catalog, role, assignment แบบมี scope, flag super-admin และตาราง migration จาก model legacy (§5)
- [rbac permissions](/th/platform/rbac/permissions) — เมทริกซ์ gate ทั่วทั้ง SPA และอัลกอริทึมการ resolve permission ฉบับเต็ม
- [users](/th/platform/users) — row ตัวตนผู้ใช้ที่ role assignment ชี้ไป
- [Clusters Permissions](/th/platform/clusters/permissions) — หน้า permissions พี่น้อง; document ตัวแปร `<Can clusterId>` แบบ scope ต่อ cluster ที่ surface นี้*ไม่*ใช้
- **Print Template Mapping** — ถูกลบออกจากผลิตภัณฑ์เมื่อ 2026-07-24 (carmen-platform commit `de11377`); เคยเป็นโมดูลพี่น้องในกลุ่ม Content ที่มี key `print_template_mapping.*` ของตัวเอง ถูกลบออกจาก permission catalog ก่อนหน้าหนึ่งวัน (carmen-turborepo-backend-v2 commit `c135bb21e`, 2026-07-23) — ไม่มีสิ่งใดเหลืออยู่แล้ววันนี้
- [Data Model](/th/platform/report-templates/data-model) &nbsp;·&nbsp; [UI Screens](/th/platform/report-templates/ui-screens) &nbsp;·&nbsp; [XML Spec](/th/platform/report-templates/xml-spec) — หน้าย่อยพี่น้อง
