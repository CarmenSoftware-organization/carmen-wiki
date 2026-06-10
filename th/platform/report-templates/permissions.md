---
title: Report Templates — สิทธิ์ (Permissions)
description: Route guard ตาม permission key, gate Can ภายในหน้า, filter ของ sidebar และข้อยกเว้น bootstrap สำหรับ surface ของ report-templates
published: true
date: 2026-06-10T17:00:00.000Z
tags: book/platform, report-templates, permissions
editor: markdown
dateCreated: 2026-06-10T17:00:00.000Z
---

# Report Templates — สิทธิ์ (Permissions)

> **At a Glance**
> **Gate:** route ของ report-templates ทั้งสามถือ `requiredPermission="report_template.read"` / `"report_template.create"` / `"report_template.update"` บน `PrivateRoute` (`src/App.tsx` บรรทัด 156–179) &nbsp;·&nbsp; **Gate ภายในหน้า:** `<Can>` ห่อ Add Template (`report_template.create`), Edit ของ row (`report_template.update`), Delete ของ row (`report_template.delete`) และ toggle Edit ของหน้า edit (`report_template.update`) — ไม่มีตัวใดส่ง `clusterId` &nbsp;·&nbsp; **`report_template.delete` อยู่ภายในหน้าเท่านั้น** — ไม่มี route ใดต้องการมัน &nbsp;·&nbsp; **ข้อยกเว้น bootstrap:** `hasPermission` คืน `true` อย่างไม่มีเงื่อนไขเมื่อ `userCount !== null && userCount <= 1` &nbsp;·&nbsp; **เมื่อไม่ผ่าน:** `<AccessDenied>` render ภายใน `<Layout>` (sidebar ยังมองเห็นอยู่) &nbsp;·&nbsp; **เอกสาร model ฉบับ canonical:** [rbac permissions](/th/platform/rbac/permissions)

## 1. ภาพรวม

Report Templates เป็น surface สำหรับ authoring ภายในของ Carmen สำหรับเอกสารที่พิมพ์และส่งออกได้ซึ่ง ship เป็นส่วนหนึ่งของ contract การ customise ของแพลตฟอร์ม เทมเพลตถูกเขียนโดยวิศวกร support ของ Carmen — ไม่ใช่ลูกค้า — ด้วย editor XML/FastReport แบบมีโครงสร้างที่ผูก data source เข้ากับ schema ของ tenant เนื่องจากการเขียนเทมเพลตต้องอาศัยความรู้เชิงปฏิบัติการระดับแพลตฟอร์มและส่งผลโดยตรงต่อสิ่งที่ลูกค้าพิมพ์หรือส่งออกจาก business unit ของตนได้ การเข้าถึงจึงถูกกำกับด้วย model RBAC แบบอิง permission ของแพลตฟอร์ม ([rbac](/th/platform/rbac)): catalog ฝั่ง backend นิยาม key `report_template.read`, `report_template.create`, `report_template.update` และ `report_template.delete`; role รวม key เหล่านั้นเป็นชุด; และ assignment ผูก role เข้ากับผู้ใช้

กลไกการ gate มีสามชั้น ทั้งหมด resolve ผ่านเส้นทาง `AuthContext.hasPermission` → `checkPermission` เดียวกัน (อธิบายอัลกอริทึมไว้ใน [rbac permissions](/th/platform/rbac/permissions) §4) ที่ระดับ route `PrivateRoute` รับ prop `requiredPermission` และ render `<AccessDenied>` ภายใน shell `<Layout>` ปกติเมื่อการตรวจสอบไม่ผ่าน ที่ระดับ navigation `Layout.tsx` filter sidebar เพื่อให้ผู้ใช้ที่ไม่มี `report_template.read` ไม่มีวันเห็นรายการ Report Templates ที่ระดับ action `<Can permission="report_template.*">` ห่อปุ่มที่แก้ไขข้อมูลบนหน้าจอ report-templates ทั้งสองหน้า ต่างจาก gate ของ cluster **ไม่มี gate ของ report-template ตัวใดส่ง `clusterId`** — เทมเพลตรายงานเป็น tenant-global ดังนั้นทุกการตรวจสอบ resolve ผ่าน branch แบบกว้างโดยไม่มีการจำกัดต่อ cluster

จนถึง 2026-06 route เหล่านี้เคยถูก gate ด้วย array ของ role enum แบบ hardcode (`platform_admin`, `support_manager`, `support_staff`) ที่ซ้ำกันอยู่ใน route guard ทั้งสามตัว; model นั้นถูกถอดออกจาก SPA, gate ของ login และ Prisma schema โดยสมบูรณ์แล้ว — การ map ของ migration document ไว้ใน [rbac](/th/platform/rbac) §5 และไม่ทวนซ้ำที่นี่

## 2. Route guard

| Route | Component ที่ render | `requiredPermission` | แหล่งที่มา |
|---|---|---|---|
| `/report-templates` | `ReportTemplateManagement` | `report_template.read` | `src/App.tsx` (block ของ route report-templates บรรทัด 156–179) |
| `/report-templates/new` | `ReportTemplateEdit` | `report_template.create` | `src/App.tsx` |
| `/report-templates/:id/edit` | `ReportTemplateEdit` | `report_template.update` | `src/App.tsx` |

แต่ละ route ถือ key เดียวพอดี ต่างจาก array ของ role ที่ซ้ำกันแบบ legacy key ทั้งสามจงใจต่างกันต่อ route ดังนั้น surface ของ list, create และ edit สามารถมอบให้แยกกันได้ — role แบบ read-only ที่รวมเฉพาะ `report_template.read` ตอนนี้เขียนออกมาได้แล้ว

สามข้อที่ควรสังเกต:

- **Route guard ตรวจสอบโดยไม่มี `clusterId`** `PrivateRoute` เรียก `hasPermission(requiredPermission)` โดยไม่มี options ผ่าน branch แบบกว้าง "scope ใดก็มอบให้ได้" เนื่องจาก gate `<Can>` ภายในหน้าบน surface นี้ก็ละเว้น `clusterId` เช่นกัน (§7) role assignment ที่ scope ไปยัง cluster เดียวซึ่ง role รวม key `report_template.*` จึงผ่านได้ทุกที่ — ไม่มีการจำกัดต่อ cluster ที่ใดเลยบน surface นี้ ซึ่งสอดคล้องกับ data model: เทมเพลตรายงานเป็น tenant-global และไม่มี cluster FK ([Data Model](./data-model.md) §3)
- **ไม่มี route ใดต้องการ `report_template.delete`** การลบเข้าถึงได้ทาง row action ของหน้า list เท่านั้น gate ภายในหน้า (§7)
- **ไม่มีการใช้ key ซ้ำข้ามโมดูล** key `report_template.*` gate เฉพาะโมดูลนี้ — ต่างจาก route ของ Business Units ที่ใช้ key `cluster.*` ซ้ำ (ดู [Clusters Permissions](../clusters/permissions.md) §2) route ของ [print-template-mapping](/th/platform/print-template-mapping) พี่น้องถือ key `print_template_mapping.*` ของตัวเอง; grant บนโมดูลหนึ่งไม่เปิดอีกโมดูลหนึ่ง

## 3. เมทริกซ์ effective access

อ่านตารางในความหมาย "session ที่ถือ grant นี้พอดีทำอะไรได้บ้างบน surface ของ report-templates" grant รวมกันแบบ additive; session **super-admin** (flag `is_super_admin`) bypass ทุก row และทำได้ทุกอย่าง gate ของ SPA เป็นเชิงคำแนะนำ — การบังคับใช้ permission ของ backend เองคือขอบเขต security ที่แท้จริง

| Grant ที่ถือ | list `/report-templates` | Add Template | Edit ของ row / หน้า edit | Delete ของ row | หมายเหตุ |
|---|---|---|---|---|---|
| ไม่มี key `report_template.*` เลย | `AccessDenied`; รายการ sidebar ถูกซ่อน | — | — | — | ยังพิมพ์ URL ได้; route guard จับไว้ |
| `report_template.read` | list เต็ม, ค้นหา, filter, ส่งออก CSV | ซ่อน (header); Add ของ empty-state ยังแสดงแต่นำไปสู่ `AccessDenied` | Edit ของ row ถูกซ่อน; route `/report-templates/:id/edit` ถูก block | ซ่อน | persona แบบ read-only; เมนู row-action render ว่างเปล่า |
| + `report_template.create` | — | แสดงและใช้งานได้ | — | — | ฟอร์ม create แก้ไขได้ทันทีเมื่อ route guard ผ่าน |
| + `report_template.update` | — | — | Edit ของ row บนทุก row; route edit เปิดได้; toggle Edit render | — | ปลดล็อกฟอร์ม edit เต็มรูปแบบ รวมถึง editor XML, chip ขอบเขต BU, probe Browse-in-BU |
| + `report_template.delete` | — | — | — | Delete ของ row render | ภายในหน้าเท่านั้น; ไม่มี route ใดต้องการ key นี้ |

เนื่องจากไม่มี gate ใดบน surface นี้ส่ง `clusterId` จึงไม่มี row ของ scoped grant ในเมทริกซ์นี้ — assignment ที่ scope ต่อ cluster ประพฤติเหมือน assignment ที่ scope ทั้งแพลตฟอร์มทุกประการที่นี่ (§2) ข้อยกเว้น bootstrap (§4) สามารถ override ทุกคอลัมน์ให้ session ใดก็ได้ตราบที่ `userCount <= 1`

## 4. ข้อยกเว้น bootstrap

`hasPermission()` ใน `AuthContext.tsx` (บรรทัด 210–214) ยกทางลัด first-admin จาก model legacy มาด้วย: เมื่อ `userCount !== null && userCount <= 1` ฟังก์ชันคืน `true` อย่างไม่มีเงื่อนไข — route guard, filter ของ sidebar และ gate `<Can>` ทุกตัวผ่าน รวมถึง gate ของ report-template ทั้งหมด รายละเอียด implementation ฉบับเต็ม — `userCount` ถูก populate อย่างไร, ปฏิสัมพันธ์กับ gate ของ login และ pseudo-code ของการ resolve — อยู่ใน [rbac permissions](/th/platform/rbac/permissions) §4 caveat เดียวกันมีผลกับ report-templates:

- **ระหว่างหน้าต่างเวลาที่ API กำลังโหลด** (`userCount === null`): เงื่อนไขเป็น `false` ดังนั้นการตรวจสอบรันเทียบกับ snapshot ของ permission อย่างเข้มงวด — ข้อยกเว้น fail แบบ closed ไม่ใช่ open session ที่ไม่มี `report_template.read` ที่เข้า `/report-templates` ก่อนการ fetch count จะ resolve เห็น `<AccessDenied>`
- **เมื่อ `userCount > 1` แล้ว**: ข้อยกเว้นอยู่ในสถานะหลับ count refresh เฉพาะตอน mount และตอน login — การลบผู้ใช้ระหว่าง session ไม่ re-arm มันจนกว่าจะถึงการ refresh ครั้งถัดไป
- **ขอบเขต**: ภายใต้ model แบบ permission branch ของ bootstrap ยังไปถึง gate ของ login ด้วย — `login()` ข้ามข้อกำหนดต้องถืออย่างน้อยหนึ่ง permission เมื่อจำนวนผู้ใช้เป็น 0 หรือ 1

## 5. พฤติกรรมของ AccessDenied

เหมือนกับ [Clusters Permissions §5](../clusters/permissions.md) `PrivateRoute` (`src/components/PrivateRoute.tsx`) implement เส้นทางการปฏิเสธสองแบบที่แตกต่างกัน:

**Auth-fail (ไม่มี session):** ถ้า `isAuthenticated` เป็น `false` component render `<Navigate to="/login" replace />` — redirect แบบ hard ที่แทนที่ history entry ปัจจุบัน ผู้ใช้ไปจบที่หน้า login โดยไม่มี error ที่มองเห็นได้ใน view ปัจจุบัน

**Permission-fail (authenticated แต่ขาด key):** ถ้า `requiredPermission` ถูกตั้งค่าและ `hasPermission(requiredPermission)` คืน `false` component render `<AccessDenied />` (นิยามไว้ในไฟล์เดียวกัน บรรทัด 9–37) ห่อด้วย `<Layout>` ดังนั้น sidebar และ header เต็มรูปแบบยังมองเห็นอยู่ ภายในพื้นที่ content การ์ดที่จัดกึ่งกลางแสดง icon shield-X, heading "Access Denied" สีแดง, ข้อความ generic "You don't have permission to access this page." และปุ่ม "Back to Dashboard" ต่างจากเวอร์ชัน legacy ข้อความไม่ quote role ที่ทำให้ไม่ผ่านอีกต่อไป — ไม่มีค่า role เดี่ยวให้แสดงภายใต้ model แบบ permission

ผู้ใช้แบบ permission-fail ยังอยู่ใน shell ของ SPA ยังใช้ sidebar นำทางไปยังหน้าที่ได้รับอนุญาตได้ และไม่ถูก log out — session ของพวกเขายัง valid

## 6. Filter ของ sidebar

`Layout.tsx` (บรรทัด 56) นิยามรายการ nav ของ Report Templates ในกลุ่ม "Content" เป็น:

```
{ path: '/report-templates', label: 'Report Templates', icon: FileText, permission: 'report_template.read', group: 'Content' }
```

array `allNavItems` เต็มชุดถูก filter ก่อน render:

```
const navItems = allNavItems.filter(
  (item) =>
    (!item.permission || hasPermission(item.permission)) &&
    (!item.superAdminOnly || isSuperAdmin),
);
```

ค่า `permission` ของ sidebar (`report_template.read`) ตรงกับ route guard ของ `/report-templates` พอดี จึงไม่มี divergence ที่รายการที่มองเห็นนำไปสู่ `AccessDenied` รายการ **Print Mapping** ข้างเคียง (บรรทัด 57) filter ด้วย key `print_template_mapping.read` ของตัวเอง — โมดูลกลุ่ม Content ทั้งสอง grant แยกกันได้อย่างอิสระ การเปลี่ยนแปลงใดในอนาคตว่า key ใด gate Report Templates ต้อง apply ทั้งใน `src/App.tsx` (route guard) และ `src/components/Layout.tsx` (ฟิลด์ `permission` ของ sidebar); การแก้ที่เดียวโดยไม่แก้อีกที่จะเปิดเผยรายการขณะ block route หรือกลับกัน

ผู้ใช้ที่ไม่มี `report_template.read` ก็แค่ไม่เห็นรายการ Report Templates พวกเขายังเข้าถึง `/report-templates` ได้ด้วยการพิมพ์ URL โดยตรง แต่ route guard render `<AccessDenied>` ก่อนข้อมูลเทมเพลตใด ๆ จะถูกโหลด

## 7. ภายใน surface ของ report-templates

ต่างจาก model legacy การผ่าน route guard ไม่ได้ปลดล็อกทุกปุ่มอีกต่อไป — action ที่แก้ไขข้อมูลถือ gate `<Can>` ของตัวเอง (เพิ่มเข้ามาพร้อมการ migrate สู่ RBAC) ไม่มีตัวใดส่ง `clusterId`:

| Action | Gate ภายในหน้า |
|---|---|
| ดู list เทมเพลต (pagination, ค้นหา, filter) | ไม่มี — key ของ route (`report_template.read`) เพียงพอ |
| ส่งออก list เป็น CSV | ไม่มี — ผู้ถือ `report_template.read` คนใดก็ได้; disabled เฉพาะระหว่างโหลดหรือเมื่อว่าง |
| Add Template (ปุ่ม header) | `<Can permission="report_template.create">` |
| Add Template (ปุ่ม empty-state) | **ไม่ถูก gate** — render ให้ผู้ถือ `report_template.read` คนใดก็ได้เมื่อ list ว่าง; route guard `report_template.create` บน `/report-templates/new` จับไว้ |
| Edit ของ row (dropdown ของ list) | `<Can permission="report_template.update">` |
| Delete ของ row (dropdown ของ list) | `<Can permission="report_template.delete">` |
| toggle Edit (header ของหน้า edit) | `<Can permission="report_template.update">` |
| Save / Cancel บนฟอร์ม edit | ไม่มี — เข้าถึงไม่ได้โดยไม่ผ่าน toggle Edit ที่ถูก gate |
| การแก้ไข XML + อัพโหลดไฟล์ (แท็บ Dialog/Content) | ไม่มี — แต่ `readOnly={!editing}` จึงอยู่หลัง gate `report_template.update` ของ toggle Edit โดยพฤตินัย |
| probe Browse-in-BU (การ lookup views/functions/procedures) | ไม่มี — render เฉพาะในโหมด edit จึงอยู่หลัง toggle Edit |
| checkbox Standard / Custom และ Active / Inactive | ไม่มี — render เฉพาะในโหมด edit จึงอยู่หลัง toggle Edit |

จุดที่เรียกใช้: gate ของหน้า list ใน `ReportTemplateManagement.tsx` (Edit ของ row บรรทัด 304–309, Delete ของ row บรรทัด 310–315, Add Template บรรทัด 335–340); toggle Edit ของหน้า edit ใน `ReportTemplateEdit.tsx` (บรรทัด 360–365)

ผลพวงที่เกี่ยวข้องกับผู้ทดสอบ ข้อแรก session ที่มีเฉพาะ `report_template.read` เห็น catalogue แบบ read-only เต็มรูปแบบ: dropdown ของ row-action render แต่ว่างเปล่า และทางออกเดียวคือปุ่ม Add ของ empty-state ที่ไม่ถูก gate ซึ่งจบเป็นทางตันที่ route guard ข้อสอง route `/report-templates/:id/edit` เปิดให้ผู้ถือ `report_template.update` คนใดก็ได้ แต่หน้ายังเริ่มในโหมด view — toggle Edit ภายในหน้าตรวจสอบ key เดียวกันซ้ำ ดังนั้น route กับ toggle จะไม่ขัดแย้งกัน test plan ควรครอบคลุม gate ต่อ key (§3) และข้อยกเว้น bootstrap (§4) ไม่ใช่ความแตกต่างต่อ role — ไม่มี persona แบบ role-enum อีกแล้ว

## 8. แหล่งข้อมูลอ้างอิง

**แหล่งข้อมูลหลัก (อ่านสิ่งเหล่านี้ก่อนอัพเดทหน้านี้):**
- `../carmen-platform/src/App.tsx` — route ของ report-templates ทั้งสามพร้อม prop `requiredPermission` (block ของ route บรรทัด 156–179)
- `../carmen-platform/src/context/AuthContext.tsx` — `hasPermission` (บรรทัด 210–214), state `userCount`, gate permission ตอน login
- `../carmen-platform/src/utils/permissions.ts` — การ resolve `checkPermission` แบบ pure (super-admin → key ระดับแพลตฟอร์ม → key ระดับ cluster)
- `../carmen-platform/src/components/PrivateRoute.tsx` — redirect ของ auth-fail, การ render `<AccessDenied>` ของ permission-fail (component ที่บรรทัด 9–37)
- `../carmen-platform/src/components/Can.tsx` — component gate ภายในหน้า (`permission`, `clusterId` แบบ optional, `fallback` แบบ optional)
- `../carmen-platform/src/components/Layout.tsx` — `NavItem[]` ของ sidebar พร้อมฟิลด์ `permission` (Report Templates ที่บรรทัด 56) และ expression ของ filter
- `../carmen-platform/src/pages/ReportTemplateManagement.tsx` / `ReportTemplateEdit.tsx` — จุดเรียกใช้ `<Can>` ตามรายการใน §7

**Cross-link:**
- [rbac](/th/platform/rbac) — model ของ permission: catalog, role, assignment แบบมี scope, flag super-admin และตาราง migration จาก model legacy (§5)
- [rbac permissions](/th/platform/rbac/permissions) — เมทริกซ์ gate ทั่วทั้ง SPA และอัลกอริทึมการ resolve permission ฉบับเต็ม
- [users](/th/platform/users) — row ตัวตนผู้ใช้ที่ role assignment ชี้ไป
- [Clusters Permissions](../clusters/permissions.md) — หน้า permissions พี่น้อง; document ตัวแปร `<Can clusterId>` แบบ scope ต่อ cluster ที่ surface นี้*ไม่*ใช้
- [print-template-mapping](/th/platform/print-template-mapping) — โมดูลพี่น้องในกลุ่ม Content ที่มี key `print_template_mapping.*` ของตัวเอง
- [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [XML Spec](./xml-spec.md) — หน้าย่อยพี่น้อง
