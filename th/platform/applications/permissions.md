---
title: Applications — สิทธิ์ (Permissions)
description: เมทริกซ์ของ gate application.*, การเข้าถึงของ machine-client (x-app-id + api_names) ต่างจาก RBAC ของผู้ใช้อย่างไร และกรณีพิเศษสำหรับผู้ทดสอบ
published: true
date: 2026-06-10T15:15:00.000Z
tags: book/platform, applications, permissions
editor: markdown
dateCreated: 2026-06-10T15:15:00.000Z
---

# Applications — สิทธิ์ (Permissions)

> **At a Glance**
> **Gate:** route ถือ `application.read` / `application.create` / `application.update` บน `PrivateRoute`; รายการ sidebar บน `application.read` &nbsp;·&nbsp; **Gate `<Can>` ภายในหน้า:** Add (`application.create`), Edit ของ row (`application.update`), Delete ของ row (`application.delete` — ภายในหน้าเท่านั้น ไม่มี route), toggle Edit (`application.update`) &nbsp;·&nbsp; **สองระบบการเข้าถึงมาบรรจบกันที่นี่:** key ของ RBAC gate ว่า *ใครจัดการ* application ได้; grant `api_name` ตัดสินว่า *application เรียกอะไรได้* &nbsp;·&nbsp; **ช่องว่างที่ทราบกัน:** CTA "Add Application" ของ empty-state ไม่ถูกห่อด้วย `<Can>`

## 1. ภาพรวม

หน้านี้ครอบคลุมเรื่องราว authorization สองเรื่องที่แตกต่างกันซึ่งตัดกันบนหน้าจอเหล่านี้ เรื่องแรกคือ [Platform RBAC](/th/platform/rbac) ตามปกติ: permission key `application.*` ที่ตัดสินว่า *มนุษย์* คนใดเห็นและแก้ไขเรคคอร์ด application ได้ (§2) เรื่องที่สองคือสิ่งที่ตัวเรคคอร์ดเอง encode ไว้: **grant ของ machine-client** — caller ที่แสดง `x-app-id` ของ application นี้เรียก endpoint ที่ถูก guard ด้วย `api_name` ตัวใดได้บ้าง (§3) ผู้ทดสอบต้องใช้ทั้งสองเลนส์: มนุษย์ที่ถือ key `application.*` ครบสามารถมอบอำนาจที่ตัวมนุษย์เองไม่ได้ถือให้กับ application ได้ เพราะคลังศัพท์ทั้งสองเป็นอิสระต่อกัน

## 2. เมทริกซ์ของ gate

gate ทุกตัว resolve ผ่าน resolver `hasPermission` ตัวเดียวที่ document ไว้ใน [Platform RBAC — Permissions](../rbac/permissions.md); route guard ที่ไม่ผ่าน render `<AccessDenied>` ภายใน shell `<Layout>` ปกติ

| Surface | กลไก | Key | แหล่งที่มา |
|---|---|---|---|
| `/applications` | `PrivateRoute requiredPermission` | `application.read` | `src/App.tsx` |
| `/applications/new` | `PrivateRoute requiredPermission` | `application.create` | `src/App.tsx` |
| `/applications/:id/edit` | `PrivateRoute requiredPermission` | `application.update` | `src/App.tsx` |
| sidebar "Applications" (กลุ่ม Platform) | nav filter ของ `Layout.tsx` | `application.read` | `src/components/Layout.tsx` |
| Add Application (header ของหน้า list) | `<Can>` | `application.create` | `ApplicationManagement.tsx` |
| Edit ของ row (dropdown action) | `<Can>` | `application.update` | `ApplicationManagement.tsx` |
| Delete ของ row (dropdown action) | `<Can>` | `application.delete` | `ApplicationManagement.tsx` |
| toggle Edit (header ของหน้า edit) | `<Can>` | `application.update` | `ApplicationEdit.tsx` |

ความไม่สมมาตรสามข้อที่ผู้ทดสอบควรใส่ใจ:

- **`application.delete` อยู่ภายในหน้าเท่านั้น** ไม่มี route ใดต้องการมัน และหน้า edit ไม่มี action ลบ — surface ทั้งหมดของ key นี้คือ item Delete ใน row ของหน้า list session ที่ถือเฉพาะ `application.read` เห็นหน้า list แต่ไม่เห็นทั้ง Edit และ Delete ใน dropdown
- **Save ไม่ถูก gate แยกต่างหาก** บนหน้า edit มีเพียง *toggle* Edit ที่ถูกห่อด้วย `<Can>`; ปุ่ม Save เป็นปุ่มธรรมดาแต่เข้าถึงไม่ได้โดยไม่เข้าโหมด edit (และ Save ของ route create อยู่หลัง `application.create` ของ route) ฝั่ง client เรื่องนี้สมเหตุสมผล; การบังคับใช้ของ backend บน `PUT` ยังคงเป็นขอบเขตที่แท้จริง
- **CTA ของ empty-state ไม่ถูก gate** เมื่อ list ว่างโดยไม่มี search term ปุ่ม "Add Application" บนการ์ด `EmptyState` **ไม่ได้**ถูกห่อด้วย `<Can permission="application.create">` (ต่างจากปุ่มใน header) session แบบ read-only คลิกมันได้และไปจบที่ `<AccessDenied>` ที่ `/applications/new` — route guard จับมันไว้ได้ แต่ affordance รั่ว ถ้าเรื่องนี้โผล่ขึ้นมาใน QA ให้ปฏิบัติกับการมองเห็นของปุ่ม ไม่ใช่ผลลัพธ์ของมัน ว่าเป็น defect

Export (CSV) และ Debug Sheet เฉพาะ dev จงใจไม่ถูก gate นอกเหนือจาก `application.read` ของ route — ทั้งคู่เป็น read-only เหนือข้อมูลที่โหลดมาแล้ว เช่นเดียวกับทุกที่ใน SPA sidebar filter เป็น UX ไม่ใช่ security: session ที่ไม่มี `application.read` จะไม่เห็นรายการ แต่ยังพิมพ์ `/applications` ใน address bar ได้และจะชน route guard

key ของ route ทั้งสามเป็นอิสระต่อกัน — `PrivateRoute` ตรวจสอบเฉพาะ key เดียวที่ route ของมันประกาศ ชุดผสมที่มีประโยชน์ในการทดสอบอย่างจงใจ: `application.update` ที่ไม่มี `application.read` สามารถ deep-link ตรงไป `/applications/:id/edit` ได้ (เมื่อได้ id มาจากที่อื่น) ขณะที่ตัวหน้า list เอง render `<AccessDenied>`; `application.create` ที่ไม่มี `application.read` เข้าถึง `/applications/new` ผ่าน URL ได้แม้ว่าทางเข้าทั้งสอง (ปุ่ม header, CTA ของ empty-state) จะอยู่บนหน้าที่มันเปิดไม่ได้

## 3. การเข้าถึงของ application ต่างจาก RBAC ของผู้ใช้อย่างไร

ไวยากรณ์ `resource.action` ใช้ร่วมกัน; เกือบทุกอย่างที่เหลือต่างกัน:

| แง่มุม | RBAC ของผู้ใช้ | Grant ของ application |
|---|---|---|
| Caller ระบุตัวตนด้วย | `Authorization: Bearer <token>` (session) | header `x-app-id: <tb_application.id>` |
| คลังศัพท์ของ key | row ใน `tb_platform_permission` (Postgres, seed ด้วย migration ฝั่ง backend); ชุด verb `read`/`create`/`update`/… | `api_name` ที่เก็บเกี่ยวจากการเรียก `new AppIdGuard('...')` โดย `scripts/generate-app-api-catalog/run.ts` (ไฟล์ที่ generate ขึ้น ไม่มีตาราง); verb ทำตาม method ของ controller (`findAll`, `findOne`, `uploadLogo`) — ไวยากรณ์เดียวกัน string ต่างกัน |
| ที่เก็บ grant | join row ระหว่าง role→permission บวก assignment row แบบมี scope ระหว่าง user→role (ห้าตาราง — ดู [Platform RBAC data-model](../rbac/data-model.md)) | row `tb_application_api` แบบแบนต่อ application (ไม่มี role ไม่มี scope) |
| Wildcard | flag super-admin (`tb_platform_super_admin`) ต่อผู้ใช้ | boolean `allow_all` ต่อ application |
| มิติของ scope | ทั้งแพลตฟอร์มหรือต่อ cluster (`cluster_id` บน assignment) | ไม่มี — grant มีผลทุกที่ที่ endpoint มีผล |
| Semantics การเขียน (SPA) | permission ของ role ส่งเป็น delta `{ add, remove }` | replace ทั้งชุดผ่าน `details.add[]` ทุกครั้งที่ `PUT` |
| จุดบังคับใช้ | gate ของ SPA (เชิงคำแนะนำ) + การตรวจสอบ session ฝั่ง backend | `AppIdGuard` ของ backend ต่อ endpoint; SPA ไม่เคยประเมิน `api_name` |
| การเพิ่ม key | seed/migration ฝั่ง backend + redeploy | เพิ่ม guard ใน backend-gateway, regenerate catalog, redeploy |

header ทั้งสองเดินทางไปด้วยกันบนทุก request ที่ **authenticated** ของ Platform SPA — SPA authenticate ผู้ใช้ของมันด้วย bearer token *และ* ระบุตัวเองเป็น application ที่ลงทะเบียนผ่าน `x-app-id` จาก build environment ของมัน (interceptor เพิ่ม bearer เฉพาะเมื่อมี token อยู่; `/auth/login` ถือ `x-app-id` ตัวเดียว) request จึงล้มเหลวได้บนแกนใดแกนหนึ่งอย่างอิสระ: ผู้ใช้ที่ valid ผ่าน app id ที่ไม่รู้จัก/ไม่ได้รับ grant หรือ app id ที่ได้รับ grant ครบถ้วนแต่ถือผู้ใช้ที่ไม่ได้รับอนุญาต

## 4. กรณีพิเศษ

| # | สถานการณ์ | พฤติกรรม | หมายเหตุสำหรับผู้ทดสอบ |
|---|---|---|---|
| 1 | `allow_all = true` โดยที่เคยเลือก `api_names` ไว้ก่อน | selector หายไป; payload การเขียน **ละเว้น `details` ทั้งหมด** และ backend มอบทุก API โดยไม่สน grant row ที่เก็บไว้ | badge ในหน้า list พลิกเป็น "All APIs" การ toggle `allow_all` กลับเป็นปิดภายใน edit session เดียวกันคืนการเลือกที่อยู่ใน memory — ให้ตรวจสอบว่าอะไร persist จริงหลังการ save แต่ละครั้ง ไม่ใช่สิ่งที่ฟอร์มแสดง การ flip ไปถึง gateway ที่การ refresh allowlist ครั้งถัดไปเท่านั้น (ตาม interval ค่าเริ่มต้น 60 วินาที) ดังนั้นเผื่อเวลาหนึ่งรอบก่อนตรวจสอบฝั่ง server |
| 2 | การแก้ไขพร้อมกัน + semantics แบบ replace | operator สองคนที่แก้ไข application เดียวกันต่างส่งชุดที่ต้องการแบบ*เต็ม*ของตัวเอง; การ save ครั้งสุดท้ายชนะและทิ้งการเพิ่ม/ถอนของอีกฝ่ายอย่างเงียบ ๆ | foot-gun ของ replace-ไม่ใช่-delta ต่างจาก delta ของ role ใน RBAC ที่นี่ไม่มีการ merge — reproduce ด้วยสอง session และตรวจสอบว่าคอลัมน์ audit ระบุผู้เขียนที่รอด |
| 3 | การ fetch catalog ล้มเหลว | selector ลดรูปเป็น `ChipInput` แบบ free-text; string ใดก็ได้ถูกกรอกเป็น `api_name` ได้ | การพิมพ์ผิด persist เป็น grant row ที่ตายแล้ว — `tb_application_api.api_name` ไม่มี FK หรือ enum ให้ validate เทียบ ตรวจสอบการจัดการ trailing space (service trim ให้) และว่าชื่อมั่ว ๆ ก็เพียงแค่ไม่มีวัน match guard ใดเลย |
| 4 | response ของ catalog ที่ไม่มี `groups` (backend รุ่นเก่ากว่า) | client derive กลุ่มที่เหมือนกันทุกประการผ่าน `groupApiNames()` — กฎ prefix-ก่อนจุดแรกเดียวกับ generator | ความทนทานต่อลำดับการ deploy ไม่ใช่ bug; UI แบบจัดกลุ่มต้องดูเหมือนเดิมไม่ว่าทางใด |
| 5 | Application `is_active = false` | SPA render badge Inactive และให้เรคคอร์ดยังแก้ไขได้เต็มที่; ไม่มีอะไรใน SPA ที่ block caller ของ application | การที่ `x-app-id` ของ application ที่ inactive จะถูกปฏิเสธหรือไม่เป็นพฤติกรรมของ backend (`AppIdGuard`) — ตรวจสอบมันฝั่ง server; อย่าอนุมานการบังคับใช้จาก badge guard ตรวจกับ allowlist snapshot ใน memory ที่ refresh ตาม interval ดังนั้น app ที่เพิ่งถูก deactivate อาจยังผ่านต่อไปจนถึงการ refresh ครั้งถัดไป — ความหน่วงนั้นไม่ใช่ bug |
| 6 | session ที่มีเฉพาะ `application.read` | list โหลดได้; dropdown ของ action ว่างเปล่า (ไม่มี Edit/Delete), Add ใน header ถูกซ่อน — แต่ CTA ของ empty-state ยังแสดงบน list ที่ว่างและจบเป็นทางตันที่ `<AccessDenied>` | ช่องว่างของ gate ใน §2; นอกนั้นเป็นการตรวจสอบการหายไปของ `<Can>` แบบ canonical |
| 7 | การลบ application ที่ client ยังใช้อยู่ | dialog ยืนยันเตือนว่า undo ไม่ได้; เมื่อถูกลบแล้ว caller ที่แสดง UUID นั้นถูก guard ปฏิเสธ **หลังการ refresh allowlist ครั้งถัดไป** — app ที่เพิ่งถูกลบอาจยังผ่านได้ชั่วครู่ | Soft delete (`deleted_at`) — ยืนยันว่าการลบหลุดออกจาก snapshot ที่การ refresh ครั้งถัดไป และ `name` ที่ถูกปล่อยนำกลับมาใช้ได้ (`@@unique` รวม `deleted_at`); หน้าต่าง grace สั้น ๆ นั้นคือ interval ของการ refresh ไม่ใช่ bug |
| 8 | guard ถูกเพิ่มใน backend แต่ catalog ไม่ถูก regenerate | endpoint บังคับใช้ key ที่ไม่มี selector ใดเสนอให้; application แบบรายการระบุชัดรับ grant ของมันผ่าน UI ไม่ได้ | การ regenerate + deploy เป็นส่วนหนึ่งของการ ship `AppIdGuard` ตัวใหม่; จนกว่าจะถึงตอนนั้น มีเพียง application แบบ `allow_all` ที่ผ่าน |
| 9 | ถือ key โดยไม่มี `read` ที่เป็นพี่น้องของมัน | `application.update` ตัวเดียวเปิด `/applications/:id/edit` ผ่าน deep link ได้; `application.create` ตัวเดียวเปิด `/applications/new` ผ่าน URL ได้ — ทั้งคู่ขณะที่ route ของ list ปฏิเสธ | route guard ตรวจสอบ key เดียวต่อตัว (§2); ตัดสินตาม test plan ว่า partial grant แบบนี้เป็นรูปร่าง role ที่ตั้งใจหรือเป็นการตั้งค่าผิด |
| 10 | session ของ super-admin หรือ bootstrap | gate `application.*` ทุกตัวผ่านโดยไม่สน grant — [resolver ของ RBAC](../rbac/permissions.md) short-circuit ก่อนการตรวจสอบ key ใด ๆ | อย่า QA เมทริกซ์ของ gate ของโมดูลนี้จาก session ของ super-admin; มันเผยให้เห็น key ที่ขาดหายไม่ได้ |

## 5. คำแนะนำ

- **ทดสอบสองแกนแยกกัน** ตรวจสอบการ gate ของมนุษย์ด้วย session ที่ถือ key `application.*` ทีละหนึ่งตัวพอดี และการ gate ของ machine ด้วย scratch application ที่ toggle ระหว่าง `allow_all`, รายการระบุชัด และไม่มี grant — อย่าเหมาว่า action ของ SPA ที่ผ่านเท่ากับการเรียกด้วย `x-app-id` ที่ผ่าน
- **ปฏิบัติกับ semantics แบบ replace เป็นอันตรายโดยปริยาย** workflow หรือ script ใดที่อัพเดท application ต้อง read-modify-write ชุด `api_names` แบบเต็ม; PUT บางส่วนแบบ "แค่เพิ่ม key เดียว" จะล้างส่วนที่เหลือทิ้ง flag โค้ด client ใหม่ใดที่ port shape แบบ delta ของ RBAC มาที่นี่
- **Audit รายการระบุชัดหลัง catalog เปลี่ยน** การเปลี่ยนชื่อหรือลบ key ของ `AppIdGuard` ทิ้ง grant row เดิมให้ค้างอยู่ (ไม่มี FK ที่เก็บกวาดมัน); diff ค่า `tb_application_api.api_name` กับ catalog ที่ generate ขึ้นเป็นระยะ
- **เลือกใช้รายการระบุชัดแทน `allow_all` นอก dev** `allow_all` คือ super-admin ฉบับ machine — มีประโยชน์สำหรับ bootstrap และ tooling ภายใน แต่มันทำให้รายการ grant ไร้ความหมายและซ่อน defect แบบ missing-grant เหมือนกับการทดสอบ RBAC จาก session ของ super-admin เป๊ะ ๆ
- **ปิดช่องว่างของ gate บน empty-state ที่ต้นทาง** ห่อ CTA ของ `EmptyState` ด้วย `<Can permission="application.create">` ให้ตรงกับปุ่ม header; จนกว่าจะถึงตอนนั้น ให้ document ทางตันนี้ใน test plan แทนที่จะ file เป็น bug ของ route guard

**แหล่งข้อมูลอ้างอิง:** `../carmen-platform/src/App.tsx` (route guard `application.*` ทั้งสาม) · `src/components/Layout.tsx` (รายการ sidebar) · `src/pages/ApplicationManagement.tsx` (gate `<Can>`, empty state) · `src/pages/ApplicationEdit.tsx` (gate ของ toggle Edit) · `../carmen-turborepo-backend-v2/scripts/generate-app-api-catalog/run.ts` (การ generate catalog)
**Cross-link:** [หน้า landing ของ Applications](/th/platform/applications) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Platform RBAC — Permissions](../rbac/permissions.md)
