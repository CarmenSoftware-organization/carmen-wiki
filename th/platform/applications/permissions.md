---
title: Applications — สิทธิ์ (Permissions)
description: เมทริกซ์ของ gate application.*, การเข้าถึงของ machine-client (x-app-id + api_names) ต่างจาก RBAC ของผู้ใช้อย่างไร และกรณีพิเศษสำหรับผู้ทดสอบ
published: true
date: 2026-09-06T23:00:00.000Z
tags: book/platform, applications, permissions
editor: markdown
dateCreated: 2026-06-10T15:15:00.000Z
---

# Applications — สิทธิ์ (Permissions)

> **At a Glance**
> **Gate:** route ถือ `application.read` / `application.create` / `application.update` **และ** `feature="applications"` บน `PrivateRoute`; รายการ sidebar บน `application.read` (ไม่มี `superAdminOnly`) &nbsp;·&nbsp; **Gate `<Can>` ภายในหน้า:** Add (`application.create`, ทั้ง header **และ** empty-state — ช่องว่างของ empty-state ที่เคยพบใน sync ก่อนหน้าปิดแล้ว), Edit ของ row (`application.update`), Delete ของ row (`application.delete` — ภายในหน้าเท่านั้น ไม่มี route), toggle Edit (`application.update`, ตอนนี้อยู่ใน actions slot ของ `ApplicationIdentityHero`), **View History** ของ row/hero (`activity_log.read`, `clusterId={PLATFORM_SCOPED_RECORD}` — ฟีเจอร์ Activity Trail แบบ cross-cutting ใหม่) &nbsp;·&nbsp; **สองระบบการเข้าถึงมาบรรจบกันที่นี่:** key ของ RBAC gate ว่า *ใครจัดการ* application ได้; grant `api_name` ตัดสินว่า *application เรียกอะไรได้* &nbsp;·&nbsp; **Concurrency:** optimistic lock ด้วย `doc_version` ตอน save

## 1. ภาพรวม

หน้านี้ครอบคลุมเรื่องราว authorization สองเรื่องที่แตกต่างกันซึ่งตัดกันบนหน้าจอเหล่านี้ เรื่องแรกคือ [Platform RBAC](/th/platform/rbac) ตามปกติ: permission key `application.*` ที่ตัดสินว่า *มนุษย์* คนใดเห็นและแก้ไขเรคคอร์ด application ได้ (§2) เรื่องที่สองคือสิ่งที่ตัวเรคคอร์ดเอง encode ไว้: **grant ของ machine-client** — caller ที่แสดง `x-app-id` ของ application นี้เรียก endpoint ที่ถูก guard ด้วย `api_name` ตัวใดได้บ้าง (§3) ผู้ทดสอบต้องใช้ทั้งสองเลนส์: มนุษย์ที่ถือ key `application.*` ครบสามารถมอบอำนาจที่ตัวมนุษย์เองไม่ได้ถือให้กับ application ได้ เพราะคลังศัพท์ทั้งสองเป็นอิสระต่อกัน

## 2. เมทริกซ์ของ gate

gate ทุกตัว resolve ผ่าน resolver `hasPermission` ตัวเดียวที่ document ไว้ใน [Platform RBAC — Permissions](/th/platform/rbac/permissions); route guard ที่ไม่ผ่าน render `<Forbidden>` (หน้า 403) ภายใน shell `<Layout>` ปกติ

| Surface | กลไก | Key | แหล่งที่มา |
|---|---|---|---|
| `/applications` | `PrivateRoute requiredPermission` + `feature` | `application.read` + `feature="applications"` | `../carmen-platform/src/App.tsx` |
| `/applications/new` | `PrivateRoute requiredPermission` + `feature` | `application.create` + `feature="applications"` | `../carmen-platform/src/App.tsx` |
| `/applications/:id/edit` | `PrivateRoute requiredPermission` + `feature` | `application.update` + `feature="applications"` | `../carmen-platform/src/App.tsx` |
| sidebar "Applications" (กลุ่ม Platform) | nav filter | `application.read`, `feature: 'applications'` | `../carmen-platform/src/components/nav/platformNav.ts` (บรรทัด 40) — **ไม่ใช่** `Layout.tsx` ซึ่งไม่นิยาม nav row อีกต่อไป |
| Add Application (header ของหน้า list **และ** empty state) | `<Can>` | `application.create` | `ApplicationManagement.tsx` |
| Edit ของ row (dropdown action) | `<Can>` | `application.update` | `ApplicationManagement.tsx` |
| Delete ของ row (dropdown action) | `<Can>` | `application.delete` | `ApplicationManagement.tsx` |
| **View History** ของ row (dropdown action, ใหม่) | `<Can>` | `activity_log.read`, `clusterId={PLATFORM_SCOPED_RECORD}` | `ApplicationManagement.tsx` — ฟีเจอร์ Activity Trail แบบ cross-cutting เหมือนกับ [clusters](/th/platform/clusters)/[business-units](/th/platform/business-units)/[users](/th/platform/users) |
| toggle Edit (actions slot ของ hero) | `<Can>` | `application.update` | `ApplicationEdit.tsx` (ปุ่ม render โดย `ApplicationIdentityHero.tsx` แล้ว) |
| **View History** ของ hero (หน้า edit, ใหม่) | `<Can>` | `activity_log.read`, `clusterId={PLATFORM_SCOPED_RECORD}` | `ApplicationEdit.tsx` — แสดงเสมอ ไม่ขึ้นกับโหมด edit |

`PLATFORM_SCOPED_RECORD` เป็นนามแฝงของ `UNRESOLVED_CLUSTER_ID` (`../carmen-platform/src/utils/permissions.ts`): sentinel `clusterId` ที่บังคับให้กิ่ง scoped ของ `checkPermission` ประเมินเป็น false สำหรับทุก cluster จริง เหลือเพียง grant `activity_log.read` ระดับแพลตฟอร์มเป็นทางเดียวไปสู่ `true` — รูปแบบที่ถูกต้องสำหรับ record ประเภทที่ไม่มี cluster ของตัวเอง (application) การบันทึกเริ่มตั้งแต่ 2026-08-31 (`AUDIT_RECORDING_STARTED_ON_PHASE_2`); application ที่สร้างก่อนหน้านั้นจะเห็นประวัติว่างเปล่า ไม่ใช่ประวัติที่พัง

**Feature flag** ทั้งสาม route และ sidebar entry ยังต้องการ feature flag `applications` ซึ่ง `PrivateRoute` ตรวจ**หลัง**การตรวจ permission session ที่ไม่มี `application.*` key ที่ถูกต้องยังเห็น `<Forbidden>` เหมือนเดิมไม่ว่า flag จะเป็นอย่างไร; session ที่มี key นั้นจะเห็น `NotFound` หรือหน้า "Coming Soon" แทนหน้าจริง ถ้า flag ถูกตั้งเป็น `hide`/`inactive` จากหน้าจอ [Feature Flags](/th/platform/feature-flags) ของ platform (`/platform/features`)

ความไม่สมมาตรสองข้อที่ผู้ทดสอบควรใส่ใจ (ข้อที่สาม เชิงประวัติ — ช่องว่างของ gate ที่ empty-state — ได้รับการแก้ไขแล้ว ดูข้างล่าง):

- **`application.delete` อยู่ภายในหน้าเท่านั้น** ไม่มี route ใดต้องการมัน และหน้า edit ไม่มี action ลบ — surface ทั้งหมดของ key นี้คือ item Delete ใน row ของหน้า list session ที่ถือเฉพาะ `application.read` เห็นหน้า list แต่ไม่เห็นทั้ง Edit และ Delete ใน dropdown
- **Save ไม่ถูก gate แยกต่างหาก** บนหน้า edit มีเพียง *toggle* Edit ที่ถูกห่อด้วย `<Can>`; ปุ่ม Save (ตอนนี้อยู่ในแถบ sticky ด้านล่าง ไม่ใช่ inline ในการ์ดแล้ว) เป็นปุ่มธรรมดาแต่เข้าถึงไม่ได้โดยไม่เข้าโหมด edit (และ Save ของ route create อยู่หลัง `application.create` ของ route) ฝั่ง client เรื่องนี้สมเหตุสมผล; การบังคับใช้ของ backend บน `PUT`/`POST` ยังคงเป็นขอบเขตที่แท้จริง

**แก้ไขแล้วตั้งแต่ sync ก่อนหน้า — ช่องว่างของ gate ที่ empty-state ปิดแล้ว** เมื่อ list ว่างโดยไม่มี search term ปุ่ม "Add Application" บนการ์ด `EmptyState` ตอนนี้ถูกห่อด้วย `<Can permission="application.create">` แล้ว ยืนยันด้วยการอ่าน source ของ `ApplicationManagement.tsx` โดยตรง — ตรงกับปุ่มใน header ข้อค้นพบเดิม ("ไม่ได้ถูกห่อด้วย `<Can>`... ปฏิบัติกับการมองเห็นของปุ่ม... ว่าเป็น defect") ไม่เป็นจริงอีกต่อไป ผู้ทดสอบควรคาดหวังว่า CTA ของ empty-state จะหายไปสำหรับ session ที่มีเฉพาะ `application.read` เหมือนปุ่ม header

Export (CSV) และ Debug Sheet เฉพาะ dev จงใจไม่ถูก gate นอกเหนือจาก `application.read` ของ route — ทั้งคู่เป็น read-only เหนือข้อมูลที่โหลดมาแล้ว **ตรวจสอบซ้ำโดยตรงกับ source สำหรับ task นี้แล้ว**: ทั้ง `handleExport` (ปุ่ม Export) และ `<DevDebugSheet>` ใน `ApplicationManagement.tsx` ไม่ได้ถูกห่อด้วย `<Can>` — ข้อความนี้ยังเป็นจริง เช่นเดียวกับทุกที่ใน SPA sidebar filter เป็น UX ไม่ใช่ security: session ที่ไม่มี `application.read` จะไม่เห็นรายการ แต่ยังพิมพ์ `/applications` ใน address bar ได้และจะชน route guard

key ของ route ทั้งสามเป็นอิสระต่อกัน — `PrivateRoute` ตรวจสอบเฉพาะ key เดียวที่ route ของมันประกาศ ชุดผสมที่มีประโยชน์ในการทดสอบอย่างจงใจ: `application.update` ที่ไม่มี `application.read` สามารถ deep-link ตรงไป `/applications/:id/edit` ได้ (เมื่อได้ id มาจากที่อื่น) ขณะที่ตัวหน้า list เอง render `<Forbidden>`; `application.create` ที่ไม่มี `application.read` เข้าถึง `/applications/new` ผ่าน URL ได้แม้ว่าทางเข้าทั้งสอง (ปุ่ม header, CTA ของ empty-state) จะอยู่บนหน้าที่มันเปิดไม่ได้

## 3. การเข้าถึงของ application ต่างจาก RBAC ของผู้ใช้อย่างไร

ไวยากรณ์ `resource.action` ใช้ร่วมกัน; เกือบทุกอย่างที่เหลือต่างกัน:

| แง่มุม | RBAC ของผู้ใช้ | Grant ของ application |
|---|---|---|
| Caller ระบุตัวตนด้วย | `Authorization: Bearer <token>` (session) | header `x-app-id: <tb_application.id>` |
| คลังศัพท์ของ key | row ใน `tb_platform_permission` (Postgres, seed ด้วย migration ฝั่ง backend); ชุด verb `read`/`create`/`update`/… | `api_name` ที่เก็บเกี่ยวจากการเรียก `new AppIdGuard('...')` โดย `scripts/generate-app-api-catalog/run.ts` (ไฟล์ที่ generate ขึ้น ไม่มีตาราง); verb ทำตาม method ของ controller (`findAll`, `findOne`, `uploadLogo`) — ไวยากรณ์เดียวกัน string ต่างกัน |
| ที่เก็บ grant | join row ระหว่าง role→permission บวก assignment row แบบมี scope ระหว่าง user→role (ห้าตาราง — ดู [Platform RBAC data-model](/th/platform/rbac/data-model)) | row `tb_application_api` แบบแบนต่อ application (ไม่มี role ไม่มี scope) |
| Wildcard | flag super-admin (`tb_platform_super_admin`) ต่อผู้ใช้ | boolean `allow_all` ต่อ application |
| มิติของ scope | ทั้งแพลตฟอร์มหรือต่อ cluster (`cluster_id` บน assignment) | ไม่มี — grant มีผลทุกที่ที่ endpoint มีผล |
| Semantics การเขียน (SPA) | permission ของ role ส่งเป็น delta `{ add, remove }` | replace ทั้งชุดผ่าน `details.add[]` ทุกครั้งที่ `PUT` |
| จุดบังคับใช้ | gate ของ SPA (เชิงคำแนะนำ) + การตรวจสอบ session ฝั่ง backend | `AppIdGuard` ของ backend ต่อ endpoint; SPA ไม่เคยประเมิน `api_name` |
| การเพิ่ม key | seed/migration ฝั่ง backend + redeploy | เพิ่ม guard ใน backend-gateway, regenerate catalog, redeploy |

header ทั้งสองเดินทางไปด้วยกันบนทุก request ที่ **authenticated** ของ Platform SPA — SPA authenticate ผู้ใช้ของมันด้วย bearer token *และ* ระบุตัวเองเป็น application ที่ลงทะเบียนผ่าน `x-app-id` จาก build environment ของมัน (interceptor เพิ่ม bearer เฉพาะเมื่อมี token อยู่; `/auth/login` ถือ `x-app-id` ตัวเดียว) request จึงล้มเหลวได้บนแกนใดแกนหนึ่งอย่างอิสระ: ผู้ใช้ที่ valid ผ่าน app id ที่ไม่รู้จัก/ไม่ได้รับ grant หรือ app id ที่ได้รับ grant ครบถ้วนแต่ถือผู้ใช้ที่ไม่ได้รับอนุญาต

## 4. กรณีพิเศษ

| # | สถานการณ์ | พฤติกรรม | หมายเหตุสำหรับผู้ทดสอบ |
|---|---|---|---|
| 1 | `allow_all = true` โดยที่เคยเลือก `api_names` ไว้ก่อน | selector หายไป; payload การเขียน **ละเว้น `details` ทั้งหมด** และ backend มอบทุก API โดยไม่สน grant row ที่เก็บไว้ `api_names` ที่เก็บไว้ **ไม่ถูกล้าง** — หน้า edit ตอนนี้บอกตรงๆ ด้วย ("ยังเก็บ `N` endpoint ที่จำกัดขอบเขตไว้ข้างใต้...") | cell Access ของ list ตอนนี้แสดง `n/n` บนบาร์โทนเตือน แทนคำว่า "All APIs" การ toggle `allow_all` กลับเป็นปิด (session เดียวกันหรือแก้ไขทีหลัง) คืนการเลือกที่เก็บไว้ — ให้ตรวจสอบว่าอะไร persist จริงหลังการ save แต่ละครั้ง ไม่ใช่สิ่งที่ฟอร์มแสดง การ flip ไปถึง gateway ที่การ refresh allowlist ครั้งถัดไปเท่านั้น (ตาม interval ค่าเริ่มต้น 60 วินาที) ดังนั้นเผื่อเวลาหนึ่งรอบก่อนตรวจสอบฝั่ง server |
| 2 | การแก้ไขพร้อมกัน + semantics แบบ replace | operator สองคนที่แก้ไข application เดียวกันต่างส่งชุดที่ต้องการแบบ*เต็ม*ของตัวเอง; การ save ครั้งสุดท้ายชนะและทิ้งการเพิ่ม/ถอนของอีกฝ่ายอย่างเงียบ ๆ | foot-gun ของ replace-ไม่ใช่-delta ต่างจาก delta ของ role ใน RBAC ที่นี่ไม่มีการ merge — reproduce ด้วยสอง session และตรวจสอบว่าคอลัมน์ audit ระบุผู้เขียนที่รอด |
| 3 | การ fetch catalog ล้มเหลว | selector ลดรูปเป็น `ChipInput` แบบ free-text; string ใดก็ได้ถูกกรอกเป็น `api_name` ได้ | การพิมพ์ผิด persist เป็น grant row ที่ตายแล้ว — `tb_application_api.api_name` ไม่มี FK หรือ enum ให้ validate เทียบ ตรวจสอบการจัดการ trailing space (service trim ให้) และว่าชื่อมั่ว ๆ ก็เพียงแค่ไม่มีวัน match guard ใดเลย |
| 4 | response ของ catalog ที่ไม่มี `groups` (backend รุ่นเก่ากว่า) | client derive กลุ่มที่เหมือนกันทุกประการผ่าน `groupApiNames()` — กฎ prefix-ก่อนจุดแรกเดียวกับ generator | ความทนทานต่อลำดับการ deploy ไม่ใช่ bug; UI แบบจัดกลุ่มต้องดูเหมือนเดิมไม่ว่าทางใด |
| 5 | Application `is_active = false` | SPA render badge Inactive และให้เรคคอร์ดยังแก้ไขได้เต็มที่; ไม่มีอะไรใน SPA ที่ block caller ของ application | การที่ `x-app-id` ของ application ที่ inactive จะถูกปฏิเสธหรือไม่เป็นพฤติกรรมของ backend (`AppIdGuard`) — ตรวจสอบมันฝั่ง server; อย่าอนุมานการบังคับใช้จาก badge guard ตรวจกับ allowlist snapshot ใน memory ที่ refresh ตาม interval ดังนั้น app ที่เพิ่งถูก deactivate อาจยังผ่านต่อไปจนถึงการ refresh ครั้งถัดไป — ความหน่วงนั้นไม่ใช่ bug |
| 6 | session ที่มีเฉพาะ `application.read` | list โหลดได้; dropdown ของ action แสดง **View History** เฉพาะถ้า session ถือ `activity_log.read` แยกต่างหาก (เป็นอิสระจาก `application.*`) — Edit/Delete หายไป, Add ใน header ถูกซ่อน และ CTA ของ empty-state ก็ถูกซ่อนด้วย (ช่องว่าง `<Can>` ของมันแก้ไขแล้ว) | `activity_log.read` เป็น grant ที่แยกจาก `application.*` ทุก key จริงๆ — ทดสอบทั้งสองแยกกัน session อาจถืออันใดอันหนึ่ง ทั้งคู่ หรือไม่มีเลย |
| 7 | การลบ application ที่ client ยังใช้อยู่ | dialog ยืนยันเตือนว่า undo ไม่ได้; เมื่อถูกลบแล้ว caller ที่แสดง UUID นั้นถูก guard ปฏิเสธ **หลังการ refresh allowlist ครั้งถัดไป** — app ที่เพิ่งถูกลบอาจยังผ่านได้ชั่วครู่ | Soft delete (`deleted_at`) — ยืนยันว่าการลบหลุดออกจาก snapshot ที่การ refresh ครั้งถัดไป และ `name` ที่ถูกปล่อยนำกลับมาใช้ได้ (`@@unique` รวม `deleted_at`); หน้าต่าง grace สั้น ๆ นั้นคือ interval ของการ refresh ไม่ใช่ bug |
| 8 | guard ถูกเพิ่มใน backend แต่ catalog ไม่ถูก regenerate | endpoint บังคับใช้ key ที่ไม่มี selector ใดเสนอให้; application แบบรายการระบุชัดรับ grant ของมันผ่าน UI ไม่ได้ | การ regenerate + deploy เป็นส่วนหนึ่งของการ ship `AppIdGuard` ตัวใหม่; จนกว่าจะถึงตอนนั้น มีเพียง application แบบ `allow_all` ที่ผ่าน |
| 9 | ถือ key โดยไม่มี `read` ที่เป็นพี่น้องของมัน | `application.update` ตัวเดียวเปิด `/applications/:id/edit` ผ่าน deep link ได้; `application.create` ตัวเดียวเปิด `/applications/new` ผ่าน URL ได้ — ทั้งคู่ขณะที่ route ของ list ปฏิเสธ | route guard ตรวจสอบ key เดียวต่อตัว (§2); ตัดสินตาม test plan ว่า partial grant แบบนี้เป็นรูปร่าง role ที่ตั้งใจหรือเป็นการตั้งค่าผิด |
| 10 | session ของ super-admin หรือ bootstrap | gate `application.*` ทุกตัวผ่านโดยไม่สน grant — [resolver ของ RBAC](/th/platform/rbac/permissions) short-circuit ก่อนการตรวจสอบ key ใด ๆ | อย่า QA เมทริกซ์ของ gate ของโมดูลนี้จาก session ของ super-admin; มันไม่มีทางเผยให้เห็น key ที่ขาดหายไป |
| 11 | การ fetch catalog ของบาร์วัดรัศมี (หน้า list) ล้มเหลว | `ApplicationReachCell` ถอยไปแสดงแบบไม่มีตัวหาร (ตัวเลข `N` เปล่าๆ ไม่มีบาร์ ไม่มีตัวหาร) — เป็นการ fetch catalog แยกต่างหากจากที่ selector ของหน้า edit ใช้ | best-effort โดยเจตนา: list ยังทำงานต่อได้แม้ reach จะแสดงลดรูป ไม่มี retry banner สำหรับ fetch เฉพาะนี้ (ต่างจาก fallback `ChipInput` ของหน้า edit ในกรณีที่ 3) — อย่าสับสน catalog fetch ทั้งสองจุดเวลา reproduce |
| 12 | grant row ที่มี `api_name` ไม่มีใน catalog ที่ regenerate ใหม่แล้ว | มุมมองแบบอ่านอย่างเดียวนับมันแยกจากเศษส่วน `known/total` ของโมดูลเป็น annotation เตือน `+N` (เช่น `known/total +1`) แทนที่จะรวมเข้าตัวเศษ | จุดเดียวบนแพลตฟอร์มที่เผย grant กำพร้าเหล่านี้; ยืนยันว่าจำนวน stale ตรงกับจำนวน row ของ `tb_application_api` ที่ `api_name` ไม่ match กับ catalog |
| 13 | `api_name` ที่ถูก grant มีกริยา authority (`delete`/`approve`/`submit`/`revoke`/…) | chip เหล่านั้น render แบบย้อมสี (ขอบ/พื้นเตือน) และเรียงก่อนภายในโมดูลของมัน ทั้งใน accordion selector และมุมมองอ่านอย่างเดียว; ตัวนับ "`N` can delete or approve" แบบ running ปรากฏใกล้มิเตอร์การเลือก | `isAuthorityAction()` จงใจแคบกว่า "การเขียนใดๆ" — `create`/`update`/`upload` ไม่ถูกย้อม ใช้ตรวจว่าผู้ตรวจสอบ audit หา grant ที่เสี่ยงที่สุดได้โดยไม่ต้องอ่านทุกชิปใน catalog 148 โมดูล |

## 5. คำแนะนำ

- **ทดสอบสองแกนแยกกัน** ตรวจสอบการ gate ของมนุษย์ด้วย session ที่ถือ key `application.*` ทีละหนึ่งตัวพอดี และการ gate ของ machine ด้วย scratch application ที่ toggle ระหว่าง `allow_all`, รายการระบุชัด และไม่มี grant — อย่าเหมาว่า action ของ SPA ที่ผ่านเท่ากับการเรียกด้วย `x-app-id` ที่ผ่าน
- **ปฏิบัติกับ semantics แบบ replace เป็นอันตรายโดยปริยาย** workflow หรือ script ใดที่อัพเดท application ต้อง read-modify-write ชุด `api_names` แบบเต็ม; PUT บางส่วนแบบ "แค่เพิ่ม key เดียว" จะล้างส่วนที่เหลือทิ้ง flag โค้ด client ใหม่ใดที่ port shape แบบ delta ของ RBAC มาที่นี่
- **Audit รายการระบุชัดหลัง catalog เปลี่ยน** การเปลี่ยนชื่อหรือลบ key ของ `AppIdGuard` ทิ้ง grant row เดิมให้ค้างอยู่ (ไม่มี FK ที่เก็บกวาดมัน); diff ค่า `tb_application_api.api_name` กับ catalog ที่ generate ขึ้นเป็นระยะ
- **เลือกใช้รายการระบุชัดแทน `allow_all` นอก dev** `allow_all` คือ super-admin ฉบับ machine — มีประโยชน์สำหรับ bootstrap และ tooling ภายใน แต่มันทำให้รายการ grant ไร้ความหมายและซ่อน defect แบบ missing-grant เหมือนกับการทดสอบ RBAC จาก session ของ super-admin เป๊ะ ๆ
- ~~ปิดช่องว่างของ gate บน empty-state ที่ต้นทาง~~ **เสร็จแล้ว** — CTA ของ `EmptyState` ถูกห่อด้วย `<Can permission="application.create">` แล้ว ตรงกับปุ่ม header ไม่ต้องดำเนินการเพิ่มเติมตรงนี้

**แหล่งข้อมูลอ้างอิง:** path ทั้งหมดคือ `../carmen-platform` เว้นแต่ระบุไว้ `src/App.tsx` (route guard `application.*` ทั้งสาม แต่ละตัวมี `feature="applications"` ด้วย) · `src/components/nav/platformNav.ts` (รายการ sidebar, บรรทัด 40 — ไม่ใช่ `Layout.tsx` ซึ่งไม่นิยาม nav row อีกต่อไป) · `src/pages/ApplicationManagement.tsx` (gate `<Can>`, empty state, View History ของ row) · `src/pages/ApplicationEdit.tsx` (gate ของ toggle Edit, View History ของ hero) · `src/utils/permissions.ts` (`PLATFORM_SCOPED_RECORD`) · `src/components/activityTrail/{ActivityTrailSheet,useRowActivityTrail,constants}.tsx` (ฟีเจอร์ View History; `AUDIT_RECORDING_STARTED_ON_PHASE_2` = 2026-08-31) · `../carmen-turborepo-backend-v2/scripts/generate-app-api-catalog/run.ts` (การ generate catalog)
**Cross-link:** [หน้า landing ของ Applications](/th/platform/applications) &nbsp;·&nbsp; [Data Model](/th/platform/applications/data-model) &nbsp;·&nbsp; [UI Screens](/th/platform/applications/ui-screens) &nbsp;·&nbsp; [Platform RBAC — Permissions](/th/platform/rbac/permissions)
