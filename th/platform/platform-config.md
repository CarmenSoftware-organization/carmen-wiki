---
title: การตั้งค่าแพลตฟอร์ม (Platform Config)
description: หน้าจอเดียว เก้าการ์ด แปดคีย์ config — คำเชิญ การสมัคร ยืนยันอีเมลเส้นทางเดิม ตั้งรหัสผ่านใหม่ อีเมลแจ้งเตือนภายใน การบังคับใช้ license เกณฑ์เตือนใกล้หมดอายุ และสวิตช์ API migration ของแพลตฟอร์ม
published: true
date: '2026-09-06T09:00:00.000Z'
tags: book/platform, platform-config
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# การตั้งค่าแพลตฟอร์ม (Platform Config)

โมดูล **Platform Config** คือหน้าจอเดียว `PlatformConfigManagement` ที่ `/platform/configs` ซึ่งอ่านและเขียนแถวในตารางเดียวที่ใช้ร่วมกัน `tb_platform_config` แต่ละแถวคือ namespace (ออบเจกต์ JSON) ไม่ใช่ค่าเดี่ยว และหน้าจอนี้ render หนึ่งการ์ดต่อหนึ่ง namespace ที่มันรู้จักวิธีแก้ — เก้าการ์ดสำหรับแปดคีย์จากสิบคีย์ที่ registry ฝั่ง backend นิยามไว้ (§3.5 อธิบายสองคีย์ที่หน้านี้ไม่แตะ) ทุกอย่างบนหน้าจอนี้เป็นอย่างใดอย่างหนึ่งในสามแบบ: ค่าตั้งลิงก์+อายุที่ย้ายมาจาก environment variable เพื่อให้ผู้ดูแลแก้ได้โดยไม่ต้อง deploy ใหม่, สวิตช์ระดับแพลตฟอร์มที่เป็น kill switch จริง, หรือเกณฑ์แสดงผลล้วน ๆ — และการสับสนสามแบบนี้เข้าด้วยกันคือทางที่ง่ายที่สุดที่จะตัดสินผลของการบันทึกผิด นี่คือเหตุผลที่ §3.2 ไล่ทุกคีย์ตาม*ผล*ของมัน ไม่ใช่แค่ฟิลด์ที่มี

> **At a Glance**
> **Component:** `PlatformConfigManagement` &nbsp;·&nbsp; **Route:** `/platform/configs` &nbsp;·&nbsp; **Nav:** `permission: 'platform_config.read'`, `feature: 'platform_config'`, `groupKey: 'navGroup.platform'` (`platformNav.ts:38`) &nbsp;·&nbsp; **ด่านเขียนพื้นฐาน:** `platform_config.manage` ที่ backend บังคับกับทุกคีย์ทั้ง `PUT`/`PATCH` ไม่ว่าจะเรียกจากหน้าจอไหน &nbsp;·&nbsp; **สองคีย์ที่ต้องมีด่านที่สองจึงจะบันทึกได้:** `license` ต้องมี `license.manage` เพิ่ม (§4.3 — **ไม่ใช่** คีย์ของโมดูล `licenses`); `platform_migration` ต้องเป็น super-admin เท่านั้น ไม่รับ permission string ใด ๆ &nbsp;·&nbsp; **การ์ด:** 9 ใบ จาก 8 คีย์ (`invitation` มีสองการ์ด, §3.1) &nbsp;·&nbsp; **e2e suite:** **ไม่มี** — `../carmen-platform-e2e/tests/` ไม่มีโฟลเดอร์ `platform-config`/`configs` ทุกคำกล่าวอ้างด้านล่างมาจากการอ่าน implementation ของ `../carmen-platform` และ `../carmen-turborepo-backend-v2` โดยตรง &nbsp;·&nbsp; **หน้าย่อย:** 1

## 1. ภาพรวม

`PlatformConfigManagement` ดึงทุกคีย์ที่รองรับในคำขอเดียว `platformConfigService.getAll()` → `GET /api-system/platform/configs` (`platformConfigService.ts:11-14`) กั้นด้วย `platform_config.read` คีย์ที่ยังไม่เคยถูกบันทึกก็ยังได้แถวกลับมา — backend เติมค่า default ในตัวจาก registry และคืน `id: null` (`platform_configs.service.ts` ใน `findAll`, ส่งต่อผ่าน `PlatformConfigsService` ไป micro-cluster) หน้าจอจึงไม่ต้องแยกกรณี "ยังไม่ได้ตั้งค่า" ออกจาก "ตั้งค่าเท่ากับ default" เลย

หน้าจอจัดการ์ดเป็นสี่กลุ่ม (`SectionHeading`, `PlatformConfigManagement.tsx:220-351`):

| กลุ่ม | การ์ด | คีย์ |
| --- | --- | --- |
| Email Links | Invitation, Sign-up, Email Verification, Password Reset | `invitation` (ครึ่ง base_url/expiry_days), `signup`, `email_verification`, `password_reset` |
| Invitation Limits | Rate Limits | `invitation` (ครึ่ง limits) |
| Notifications | Notification Email | `notification_email` |
| Licensing | License Enforcement, Expiry Thresholds | `license`, `expiry_thresholds` |
| Platform Migration | Platform Migration | `platform_migration` |

แถบสถานะเหนือการ์ด (`PlatformConfigManagement.tsx:198-218`) แสดงสามค่าที่ผู้อ่านอาจพลาดถ้าไม่เลื่อนดู: การบังคับใช้ license (**Enforced**/**Shadow Mode**), อีเมลแจ้งเตือนภายใน (**On**/**Off**), และ API migration ของแพลตฟอร์ม (**On**/**Off**) — แต่ละค่าตรวจด้วย `=== true` ไม่ใช่ truthy เพื่อให้ค่าที่เก็บไว้ผิดรูปแบบอ่านเป็น "ปิด" แทนที่จะทำให้ badge พัง ทุกการ์ดใช้เปลือกเดียวกัน (`ConfigCardShell`/`ConfigField`, `pages/platformConfig/ConfigCardShell.tsx`): ตอนปิดเป็น `<dl>` แถว label/ค่าอย่างเดียว ตอนเปิดเป็นฟอร์ม และมีบรรทัด audit ท้ายการ์ดหนึ่งบรรทัดเสมอ ("Updated 3 days ago by …" หรือ "Created …" ผ่าน `normalizeAudit()`/`latestActor()`, `utils/audit.ts:72-108`) — ลองรูป nested `audit.*` ก่อน ตกไปฟิลด์แบน `updated_at`/`updated_by_name` เป็นสำรอง โดย `updated` จะถูกซ่อนถ้าไม่มีการแก้จริง (มีชื่อคนแก้ หรือเวลาต่างจาก `created_at`)

การบันทึกทุกครั้งไปทาง `PATCH /api-system/platform/configs/:key` (`platformConfigService.patch()` ไม่มีการ์ดใดเรียก `.update()`/`PUT` เลย — ดู §3.4) แต่ละการ์ดส่งเฉพาะฟิลด์ที่มันแสดง เมื่อสำเร็จหน้าจอจะดึงรายการทั้งหมดใหม่ (`handleSaved` → `fetchAll()`) ซึ่งทั้งปิดการ์ดที่กำลังแก้และ remount ทุกการ์ดที่ prop `key` ของมันมีเวลาที่อัปเดตล่าสุดผสมอยู่ — ฟอร์มของการ์ดจึงรีเซ็ตกลับเป็นค่าที่เพิ่งบันทึกเสมอ ไม่ใช่สำเนาเก่าที่ค้างใน memory

แผงดีบั๊กที่ใช้เฉพาะตอนพัฒนา (`DevDebugSheet`, มุมล่างขวา) แสดง payload ดิบของ `GET` — แต่เฉพาะ dev build ในเครื่องเท่านั้น: `DevDebugSheet` เองคืน `null` ถ้า `import.meta.env.DEV` ไม่เป็นจริง และหน้าจอเติม `rawResponse` ก็ต่อเมื่อ `process.env.NODE_ENV === 'development'` เท่านั้น (`PlatformConfigManagement.tsx:97,356-360`) นี่**ไม่ใช่ด่าน RBAC** — production build จะคอมไพล์แผงนี้ทิ้งไปเลยไม่ว่าผู้ดูจะมีสิทธิ์อะไร

ตัวกันไว้เมื่อมีการแก้ไขค้าง (`useUnsavedChanges(editingCard !== null)`) หยาบโดยตั้งใจ: มีแค่การ์ดเดียวที่เปิดแก้ได้ในเวลาเดียวกัน (`editingCard: CardId | null`) และตัวกันนี้จะทำงานทุกครั้งที่มีการ์ดใดเปิดอยู่ เพราะแต่ละการ์ดถือ form state ของตัวเอง หน้าเพจจึงคำนวณความสกปรกรายฟิลด์ไม่ได้โดยไม่ผูกกับการ์ดทุกใบ — คอมเมนต์ในโค้ดเองเรียกนี่ว่าฝั่งที่ปลอดภัยกว่าของ trade-off นี้

## 2. บริบททางธุรกิจ

ทุกคีย์บนหน้าจอนี้เคยเป็น environment variable ที่อ่านครั้งเดียวตอน process เริ่มทำงาน: `INVITATION_BASE_URL`/`INVITATION_EXPIRY_DAYS`, `SIGNUP_VERIFY_BASE_URL`, `SMTP_ENABLED`/`SMTP_RECIPIENTS`/`SMTP_CC`/`SMTP_SUBJECT_PREFIX`, `PLATFORM_MIGRATION_API_ENABLED` การย้ายเข้า `tb_platform_config` ทำให้ผู้ดูแลเปลี่ยนปลายทางลิงก์ อายุ token หรือ kill switch จากหน้าจอได้เลย — ไม่ต้อง deploy ใหม่ ไม่ต้อง restart — พร้อมกับเก็บค่าไว้นอก source control และนอกรายการ env-var ของทุก deploy pipeline สิ่งที่คอมเมนต์ในซอร์สของโมดูลนี้พูดตรง ๆ คือ trade-off: สามในเก้าการ์ด (License Enforcement, Platform Migration และโดยอ้อมคือคำเตือนเรื่อง rate limit บน Invitation Limits) ไม่ใช่ "ค่าตั้ง" ในความหมายทั่วไป — มันคือสวิตช์ที่ส่วนอื่นของแพลตฟอร์มถือเป็นความจริงสูงสุด ตรวจอยู่บนเส้นทางร้อนของ request พร้อม cache 60 วินาทีคั่นระหว่าง "กด Save แล้ว" กับ "พฤติกรรมใหม่มีผลจริงทุกที่" การตีความเจตนาของการบันทึกผิด — เช่นมอง `license.enforcement_enabled` เป็นสวิตช์แสดงผล หรือมอง `expiry_thresholds` เป็นตัวบังคับใช้ — คือความผิดพลาดที่ร้ายแรงที่สุดที่ผู้ทดสอบหน้าจอนี้จะทำได้ ซึ่งเป็นเหตุผลที่ §3.2 ระบุผลจริงของแต่ละคีย์ ไม่ใช่แค่รูปร่างที่มันเก็บไว้

## 3. แนวคิดสำคัญ

### 3.1 เก้าการ์ด แปดคีย์ — มีแค่ `invitation` ที่มีสองการ์ด

`tb_platform_config` เป็นตารางแบบ namespace-ต่อ-แถว: ทุกแถวเป็นออบเจกต์ JSON ไม่เคยเป็นสเกลาร์เดี่ยว (`platform-config.schema.ts:176-184` ระบุธรรมเนียมนี้ตรง ๆ — คีย์แบบจุดอย่าง `license.enforcement_enabled` ที่เป็นแถวของตัวเองจะเป็น "ธรรมเนียมที่สองในตารางเดียว" และยังมองไม่เห็นบนหน้าจอนี้ด้วย เพราะ `findAll` กรองด้วยรายชื่อคีย์ของ registry) `invitation` คือคีย์เดียวที่มีสองการ์ดใช้ร่วมกัน: `InvitationConfigCard` แก้ `base_url`/`expiry_days`, `InvitationLimitsCard` แก้ `max_per_admin_per_hour`/`max_per_cluster_per_day` — ทั้งคู่ `PATCH` แถว `invitation` แถวเดียวกัน และแต่ละการ์ดตั้งใจใช้ `patch()` แทน `update()` เพื่อไม่ให้การบันทึกครึ่งหนึ่งไปล้างอีกครึ่งทิ้ง (`InvitationConfigCard.tsx:105-107`, `InvitationLimitsCard.tsx:96-97`)

`email_verification` กับ `password_reset` ใช้ component เดียวกัน `LinkConfigCard` (`pages/platformConfig/LinkConfigCard.tsx`) พารามิเตอร์ด้วย `configKey`/`title`/`urlExample`/`defaults` — ทั้งสองคีย์มีรูปร่างเหมือนกันเป๊ะ `{ base_url, expiry_hours }` การแยกการ์ดเฉพาะต่อคีย์จึงเป็นการคัดลอกโค้ดเปล่า ๆ (`LinkConfigCard.tsx:34-39`)

### 3.2 แต่ละคีย์คุมอะไร และผลของมันอยู่ที่ไหนจริง ๆ

| การ์ด / คีย์ | ฟิลด์ (default) | สิ่งที่เปลี่ยนในผลิตภัณฑ์เมื่อบันทึก | บังคับใช้ที่ |
| --- | --- | --- | --- |
| **Invitation** (`invitation`) | `base_url` (`http://localhost:3000/invitations`), `expiry_days` (7, 1–365) | ข้อความลิงก์ที่ส่งในอีเมลคำเชิญ cluster/BU ทุกฉบับ และจำนวนวันที่ token คำเชิญยังกดรับได้ `base_url` ประกอบด้วย `new URL()` + `searchParams.set('token', …)` ไม่ใช่การต่อสตริง — ค่าที่มี query string ติดมาแล้วถูกต้องโดยตั้งใจ | เส้นทางออกคำเชิญของ micro-cluster ที่อ่านแถว `tb_platform_config` นี้ตรง ๆ (คอมเมนต์ registry, `platform-config.schema.ts:4-23`) |
| **Rate Limits** (`invitation`, อีกครึ่ง) | `max_per_admin_per_hour` (100), `max_per_cluster_per_day` (500) เป็นจำนวนเต็มบวก **ไม่มีเพดานบนที่ backend บังคับ** | เพดานจำนวนคำเชิญที่แอดมินคนหนึ่ง (ต่อชั่วโมง) หรือ cluster หนึ่ง (ต่อวัน) ออกได้ก่อนจะถูกปฏิเสธ คำเตือนในหน้าระบุว่าตัวนับเป็น**หน่วยความจำต่อ process** เพดานจริงบน deployment ที่มีหลาย instance จึงคูณตามจำนวน instance — ขึ้นค่านี้อย่างตั้งใจสำหรับงานเปิดโรงแรมใหม่ ไม่ใช่ทำเล่น ๆ | ตัวจำกัดอัตราในหน่วยความจำของ process (micro-cluster) บน endpoint ออกคำเชิญ ไม่ใช่ขอบเขตความปลอดภัย เป็นตัวกันการใช้ผิดปกติ |
| **Sign-up** (`signup`) | `verify_base_url` (`http://localhost:3000/register/verify`), `link_expiry_hours` (24, 1–720) | ลิงก์และอายุ token ของอีเมลยืนยัน**การสมัครแบบ self-service** (`auth.service.ts` ฟังก์ชัน `signupRequest`, micro-business) — เส้นทางที่บัญชีใหม่เอี่ยมใช้ยืนยันอีเมลของตัวเองก่อนบัญชีจะถูกสร้างจริง | `readSignupConfig()` ของ micro-business ที่อ่านแถวนี้ตรง ๆ (`auth.service.ts:319-327`) |
| **Email Verification** (`email_verification`) | `base_url` (`http://localhost:3000/verify-email`), `expiry_hours` (24, 1–720) | ลิงก์และอายุ token ของอีเมลยืนยัน**เส้นทางเดิม** — ส่งให้บัญชีที่ถูกสร้าง*ก่อน*ที่เส้นทางสมัครจะถูกกลับลำดับ หรือบัญชีที่แอดมินสร้างให้ตรง ๆ ซึ่งบัญชีมีอยู่แล้ว เหลือแค่ต้องยืนยันอีเมล คนละเส้นทางโค้ดกับ Sign-up ด้านบน และทั้งคู่ยังทำงานพร้อมกันอยู่ | `readEmailVerificationConfig()` ของ micro-business (`auth.service.ts:329-338` ใช้จริงใน handler ขอยืนยันซ้ำแถวประมาณ 1362) |
| **Password Reset** (`password_reset`) | `base_url` (`http://localhost:3000`), `expiry_hours` (24, 1–720) | ลิงก์และอายุ token ของอีเมลลืมรหัสผ่าน คอมเมนต์บนเส้นทางอ่านระบุตรง ๆ ว่าทำไมถึงย้ายออกจาก `process.env`: โค้ดเดิมอ่าน env ดิบ ๆ ไม่มี schema และมี default เป็น **1 ชั่วโมง** ซึ่งไม่ตรงกับค่าจริงในไฟล์ `.env` ที่ตั้งไว้ 24 ชั่วโมง — ค่าที่บอกผู้ใช้ในอีเมลกับอายุจริงของ token จึงเคยเพี้ยนกันได้เงียบ ๆ การย้ายนี้ตัดความเสี่ยงแบบนั้นทิ้ง | `readPasswordResetConfig()` ของ micro-business (`auth.service.ts:340-350` ใช้จริงที่ `auth.service.ts:1684-1687`) |
| **Notification Email** (`notification_email`) | `enabled` (ปิด), `recipients` (`[]`), `cc` (`[]`), `subject_prefix` ('') | ตามที่ตั้งใจไว้: ใครได้รับอีเมลแจ้งเตือนภายใน (รายงาน / แจ้งเตือนระดับ BU) และคำนำหน้าหัวเรื่อง แยกจาก *credential* SMTP ที่อยู่ใน `tb_email_sender_profile` ของโมดูล Email Setting **ในทางปฏิบัติ: การบันทึกการ์ดนี้ไม่เปลี่ยนอะไรที่สังเกตได้เลยในตอนนี้** การค้นทั้ง repo ของ `carmen-turborepo-backend-v2`, `micro-notification`, `micro-report`, `micro-cronjobs` และ `micro-data` หาผู้อ่านคีย์ `notification_email` หรือฟิลด์ของมัน (`recipients`, `cc`, `subject_prefix`) ไม่พบเลยนอกจากตัว registry เอง — เอกสารภายในของ `micro-notification` เอง (`apps/micro-notification/CLAUDE.md`) บอกว่า *credential* SMTP ย้ายออกจาก env ไปที่ `tb_email_sender_profile` หมดแล้ว แต่ไม่พูดถึงคีย์นี้เลย ให้ถือว่าการ์ดนี้เป็นแค่**บันทึกไว้เฉย ๆ**จนกว่าจะยืนยันผู้อ่านได้ — อย่าสมมติว่าการสลับ `enabled` เปลี่ยนว่ารายงานหรืออีเมลแจ้งเตือนใด ๆ จะถูกส่งจริงหรือไม่ | **ไม่พบผู้อ่าน** — เป็นข้อสังเกต ไม่ใช่คำยืนยันว่ามีการบังคับใช้ที่ไหน |
| **License Enforcement** (`license`) | `enforcement_enabled` (`false`, shadow mode) | Kill switch ระดับแพลตฟอร์มของการบังคับใช้ license เมื่อเป็น `true` `LicenseInterceptor` (backend-gateway) จะบล็อกทุกการเขียน — และทุกการอ่านที่ feature ไม่มีสิทธิ์ — บน route ที่ตรงกับ `/api/:bu_code/*` หรือ `/api/config/:bu_code/*` สำหรับ business unit ที่ไม่มีสิทธิ์ที่จำเป็น ตอบ `403 LICENSE_REQUIRED` (ไม่เคยขายให้) หรือ `403 LICENSE_EXPIRED` (พยายามเขียนบนสัญญาที่หมดอายุแล้ว การอ่านยังผ่านได้) สวิตช์เดียวกันนี้ยังเปิดการบังคับเพดานที่นั่งใน `assertSeatAvailable` ของ micro-cluster ไปพร้อมกัน ตอบ `403 SEAT_LIMIT_REACHED` เมื่อคำเชิญใหม่จะทำให้เกินที่นั่งที่ cluster ซื้อไว้ `/api-system/*` — ทุกอย่างที่หน้าจอ admin นี้เองเรียก — **ไม่อยู่ในขอบเขต**ของสวิตช์นี้ การเปิดสวิตช์จึงไม่มีวันล็อกหน้าจอ admin ออกจากตัวเอง ผู้อ่านทั้งสองฝั่ง cache ค่านี้ไว้ 60 วินาที การบันทึกจึงมีผลภายในราวหนึ่งนาที ไม่ใช่ทันที และค่าที่ parse ไม่ผ่านจะอ่านเป็น `false` (fail-open) ทั้งสองฝั่ง | `license.interceptor.ts` (backend-gateway, ขอบเขต route ใน `license-route-resolver.ts:21,25`) + `seat-enforcement-flag.service.ts` (micro-cluster) |
| **Expiry Thresholds** (`expiry_thresholds`) | `subscription_days`, `bu_quota_days`, `seat_days` — ทั้งหมด `30`, 1–365 | เป็นเกณฑ์**แสดงผล/นับ**ล้วน ๆ — ขึ้นหรือลดค่าเปลี่ยนแค่ว่า badge "ใกล้หมดอายุ" เริ่มขึ้นเมื่อไหร่บนหน้า [Licenses](/th/platform/licenses) และ Clusters และตัวเลขในแถบสรุปของ `expiring_soon` รวมอะไรบ้าง **ไม่มีใครถูกบล็อกเพิ่มหรือลดจากการ์ดนี้** — มันอยู่หัวข้อเดียวกับ License Enforcement เพราะทั้งคู่เกี่ยวกับวงจรชีวิตของ license เท่านั้น ไม่ใช่เพราะใช้กลไกร่วมกัน สามกระบวนการอ่านค่านี้แยกกัน (รายการ/ตัวนับ cluster ของ micro-cluster, สรุป subscription ของ micro-business และ `ExpiryThresholdContext` ของ frontend เอง ซึ่งเรียก `refresh()` ทันทีหลังบันทึกให้ `/licenses` กับ `/clusters` สะท้อนหน้าต่างใหม่โดยไม่ต้องรีโหลดทั้งแอป) แต่ละที่มี cache 60 วินาทีของตัวเอง | `ExpiryThresholdsService` ใน micro-cluster และ micro-business; `ExpiryThresholdContext.tsx` ฝั่ง frontend (endpoint สาธารณะ ไม่มี permission — ดู §4.1) |
| **Platform Migration** (`platform_migration`) | `api_enabled` (`false`) | สวิตช์เปิด/ปิด `/api-system/platform/migrations/*` ซึ่งรัน `prisma migrate deploy` บน**ฐานข้อมูลกลางที่ทุก cluster ใช้ร่วมกัน** ไม่ใช่ของ BU ใด BU หนึ่ง เคยเป็น env `PLATFORM_MIGRATION_API_ENABLED` การย้ายมาที่นี่แลก "ต้องเข้าเครื่องได้จึงจะสลับได้" เป็น "ต้องเป็น super-admin จึงจะสลับได้" (§4.3) `PlatformMigrationGuard` cache สวิตช์นี้ไว้ 60 วินาที ตามคำเตือนในการ์ด — เพิ่งเปิดสวิตช์ยังอาจได้ 403 อีกไม่เกินหนึ่งนาที ซึ่งเป็นพฤติกรรมที่ถูกต้อง ไม่ใช่บั๊ก | `platform-migration.guard.ts` (backend-gateway) รูปแบบ cache 60 วิเดียวกับ License Enforcement |

### 3.3 สองคีย์ที่ต้องการมากกว่า `platform_config.manage` จึงจะบันทึกได้ — ดู §4.3 สำหรับ conjunction ที่แม่นยำ

decorator ระดับ endpoint บนทั้งสอง route เขียนเหมือนกันทุกคีย์ คือ `@RequirePlatformPermission('platform_config.manage')` (`platform_configs.controller.ts:238,287`) มีสองคีย์ที่เพิ่มด่านที่**สอง**เฉพาะคีย์ตัวเองไว้ข้างใน handler เอง `writeKeyDenial()` (`platform_configs.controller.ts:145-159`) เพราะ `@RequirePlatformPermission` เป็น decorator ระดับ endpoint แยกรายคีย์ไม่ได้:

- `license` ต้องมี `license.manage` เพิ่ม — หรือ `is_super_admin === true` เป็นทางลัดแบบไม่มีเงื่อนไข (`platform_configs.controller.ts:147-151`)
- `platform_migration` ต้องเป็น `is_super_admin === true` **เท่านั้น** — ไม่มี permission string ใดผ่านได้เลย ต่างจาก `license` (`platform_configs.controller.ts:153-157`)

คีย์อื่นทุกตัวทำงานเหมือนมีแค่ `@RequirePlatformPermission('platform_config.manage')` เพียงอย่างเดียว — `writeKeyDenial()` คืน `null` (ผ่าน) ทันทีให้กับคีย์เหล่านั้น

### 3.4 ทำไมการบันทึกทุกครั้งเป็น `PATCH` ไม่ใช่ `PUT`

`platformConfigService.update()` (`PUT`) มีอยู่แต่ไม่มีการ์ดใดในโมดูลนี้เรียกมัน — `PUT` ต้องการทุกฟิลด์ที่ schema ของคีย์ปลายทางรู้จัก payload ที่ขาดฟิลด์ใดจะถูกปฏิเสธด้วย `422` ไม่ใช่ถูกเติมด้วยค่า default อย่างเงียบ ๆ (`platformConfigService.ts:21-30`, backend PR #319) `PATCH` ผสานเฉพาะฟิลด์ที่ส่งไป ปล่อยที่เหลือไว้เหมือนเดิม — ตัวเลือกที่ถูกต้องสำหรับทุกการ์ดที่นี่ เพราะไม่มีการ์ดใดแสดงครบ 100% ของฟิลด์ที่*อาจจะ*มีในอนาคตของคีย์นั้น backend ถอด `.default()` ออกจาก schema ฝั่งเขียนโดยตั้งใจ เพื่อให้ฟิลด์ที่ถูกละไว้จริง ๆ ใน payload ของ `PATCH` แยกออกจากฟิลด์ที่ผู้เรียกตั้งใจส่งค่าเท่ากับ default ได้ (`toWriteSchema()`, `platform-config.schema.ts:405-434`) `doc_version` มีเป็นคอลัมน์ในตารางนี้แต่ backend ยังไม่บังคับ optimistic locking ด้วยมัน — คอมเมนต์ของ `platformConfigService.update()` เองบอกไว้ว่าอย่าส่งมันมา

### 3.5 มีอีกสองคีย์ใน registry ที่อยู่บนตารางนี้แต่ไม่เคยโผล่บนหน้าจอนี้

`PLATFORM_CONFIG_REGISTRY` ของ backend (`platform-config.schema.ts:260-369`) นิยามสิบคีย์ ไม่ใช่แปด — `email_routing` กับ `feature_flags` ใช้ตาราง `tb_platform_config` เดียวกันและใช้พื้นผิว REST `/api-system/platform/configs/:key` แบบทั่วไปเดียวกัน แต่ไม่มีตัวไหน render โดย `PlatformConfigManagement`:

- **`email_routing`** — เส้นทางอีเมลไหนใช้โปรไฟล์ผู้ส่งตัวไหน — ถูกแก้จากหน้าจอของโมดูล **Email Settings** เอง (`EmailRoutingCard.tsx:124` เรียก `platformConfigService.update('email_routing', …)` — service ทั่วไปตัวเดียวกับที่โมดูลนี้ใช้) **ควรกล่าวไว้ให้แม่นยำ ในจิตวิญญาณเดียวกับ §4.3 ด้านล่าง:** หน้าจอนั้นกั้นปุ่ม Edit ของตัวเองด้วย `email_setting.manage` (`EmailSettingManagement.tsx:48`) — แต่ endpoint ที่มันเรียกจริงตอนบันทึกยังต้องการ `platform_config.manage` ระดับ controller เหมือนทุกคีย์ในโมดูลนี้ (§3.3) session ที่ถือ `email_setting.manage` โดยไม่มี `platform_config.manage` จะเห็น UI Edit ที่ดูใช้งานได้บนหน้า Email Settings แล้วได้ 403 ทุกครั้งที่บันทึก — บั๊กรูปร่างเดียวกับที่คำเตือน `license.manage` ของโมดูลนี้เอง (§4.3) มีไว้เพื่อป้องกัน เพียงแต่อยู่คนละหน้าจอ ยังไม่ได้ยืนยันกับหน้าของโมดูล Email Settings เอง — ตั้งข้อสังเกตไว้ที่นี่สำหรับใครก็ตามที่จะตรวจสอบหรือเขียนโมดูลนั้นต่อไป
- **`feature_flags`** — flag เปิด/ปิด feature รายตัวที่ frontend อ่านไปตัดสินว่าจะ render อะไร — **ไม่**เข้าถึงได้ผ่าน `/api-system/platform/configs` เลย แม้จะอยู่ใน registry และตารางเดียวกัน มันมีคู่ endpoint เฉพาะของตัวเอง ยืนยันตรงจาก `feature_flags.controller.ts`: `GET /api-system/platform/feature-flags` **ไม่มี** `PlatformPermissionGuard`/`RequirePlatformPermission` เลย — มีแค่ `AppIdGuard` (`feature_flags.controller.ts:83-84`) — เพราะทุกแอปที่ยืนยันตัวตนแล้วต้องอ่าน flag ได้ ไม่ใช่แค่ platform admin; `PUT /api-system/platform/feature-flags` ต้องมี `feature_flag.manage` (`feature_flags.controller.ts:118-120`) ซึ่งเป็นคีย์ที่โมดูลนี้ไม่เคยตรวจเลย คู่นี้เป็นของโมดูล **Feature Flags** แยกต่างหาก

## 4. บทบาทและสิทธิ์

### 4.1 เมทริกซ์ด่านฝั่ง frontend

| จุด | Permission | Feature flag | ที่มา |
| --- | --- | --- | --- |
| รายการ sidebar, route `/platform/configs` | `platform_config.read` | `platform_config` | `platformNav.ts:38`; `App.tsx:501-502` |
| ปุ่ม Edit ของทุกการ์ด ยกเว้น License Enforcement กับ Platform Migration | `platform_config.manage` (`canManage`) | — | `PlatformConfigManagement.tsx:72` |
| ปุ่ม Edit ของการ์ด License Enforcement | `platform_config.manage` **และ** `license.manage` (`canManageLicense`) | — | `PlatformConfigManagement.tsx:75` |
| ปุ่ม Edit ของการ์ด Platform Migration | `platform_config.manage` **และ** `isSuperAdmin` (`canManagePlatformMigration`) | — | `PlatformConfigManagement.tsx:79` |
| ปุ่ม Edit ของการ์ด Expiry Thresholds | `platform_config.manage` (`canManage`) **เท่านั้น** — ตั้งใจไม่ใช้ `canManageLicense` | — | `PlatformConfigManagement.tsx:326-335` มีคอมเมนต์ในโค้ดเตือนไม่ให้ลอกด่านที่แน่นกว่าของการ์ด License มาใช้ที่นี่ |

`ConfigCardShell` ซ่อนปุ่ม Edit ทั้งหมดเมื่อ `canManage` เป็น false (`ConfigCardShell.tsx:75-80`) — ผู้อ่านที่ไม่มีสิทธิ์จะไม่เห็นปุ่มแก้เลยตั้งแต่ต้น ในทุกการ์ด ไม่มีสถานะ "เห็นแต่กดไม่ได้"

`checkPermission()` ฝั่ง frontend เองลัดวงจรเป็น `true` ทันทีสำหรับคีย์ใด ๆ เมื่อผู้เรียกเป็น super admin (`src/utils/permissions.ts:56`) super admin จึงเห็นปุ่ม Edit บน**ทุก**การ์ด รวมถึง License Enforcement โดยไม่ต้องมีสตริง `license.manage` จริง ๆ — ตรงกับทางลัด super-admin ฝั่ง backend เองใน `writeKeyDenial()` (§3.3)

### 4.2 การบังคับใช้ฝั่ง backend

path ทั้งหมดด้านล่างคือ `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_configs/platform_configs.controller.ts` HEAD `937cf5ac4` (2026-09-06)

| Route | Guard | ที่มา |
| --- | --- | --- |
| `GET /api-system/platform/configs` | `AppIdGuard` + `PlatformPermissionGuard`, `platform_config.read` | บรรทัด 168-170 |
| `GET /api-system/platform/configs/:config_key` | เหมือนกัน, `platform_config.read` | บรรทัด 198-200 |
| `PUT /api-system/platform/configs/:config_key` | เหมือนกัน, `platform_config.manage`, **บวก** `writeKeyDenial()` สำหรับ `license`/`platform_migration` | บรรทัด 236-238, 262-266 |
| `PATCH /api-system/platform/configs/:config_key` | เหมือนกัน, `platform_config.manage`, **บวก** `writeKeyDenial()` สำหรับ `license`/`platform_migration` | บรรทัด 285-287, 311-315 |

handler เขียนทั้งสองตัวตรวจส่วน `config_key` ของ path กับ `KEY_REGEX` (`^[a-zA-Z0-9_.-]+$`) ก่อนแตะชั้น service เลย ปฏิเสธคีย์ที่ผิดรูปด้วย `422` แทนที่จะปล่อยให้ถึง RPC (`platform_configs.controller.ts:37,219-222,258-261,307-310`)

### 4.3 `license.manage` อยู่ที่นี่ ไม่ใช่ในโมดูล Licenses — conjunction ที่แม่นยำที่ผู้ทดสอบต้องรู้

**การ grep ทั้ง repo พบ `license.manage` อยู่ที่เดียวเท่านั้น: โมดูลนี้** มันอยู่ที่ `PlatformConfigManagement.tsx:75` (`canManageLicense = canManage && hasPermission('license.manage')`) และในการตรวจฝั่ง backend ที่ตรงกัน คือ constant `LICENSE_MANAGE_PERMISSION` ใน `writeKeyDenial()` (`platform_configs.controller.ts:58,149-151`) มัน**ไม่ได้**กั้นอะไรในโมดูล [Licenses](/th/platform/licenses) เลย — สองคีย์ของโมดูลนั้นคือ `subscription.read`/`subscription.manage` ยืนยันจากเอกสาร permissions ของโมดูลนั้นเอง

**Conjunction นี้สำคัญ ทั้งสองฝั่ง:**

- `canManage` เพียงอย่างเดียว (`platform_config.manage`) **จำเป็นแต่ไม่พอ** — ผู้ถือ `platform_config.manage` ที่ไม่มี `license.manage` จะเห็นปุ่ม Edit ของการ์ด License Enforcement **หายไปทั้งหมด** (`&&` ถูกประเมินก่อนปุ่มจะ render เลยด้วยซ้ำ `PlatformConfigManagement.tsx:75` ส่งเข้า prop `canManage` ของ `ConfigCardShell`) จึงอ่านว่า "ไม่มีปุ่มแก้" ไม่ใช่กับดัก "แก้แล้วโดน 403"
- ช่องว่างในทิศตรงข้ามคือสิ่งที่ควรจำให้แม่นยำ: **`license.manage` เพียงอย่างเดียวโดยไม่มี `platform_config.manage` ก็บันทึกการ์ดนี้ไม่ได้เหมือนกัน** — decorator ระดับ endpoint บน `PUT`/`PATCH` (§4.2) คือ `platform_config.manage` ตรวจ*ก่อน*ตรรกะเฉพาะคีย์ของ `writeKeyDenial()` จะทำงานเสียอีก role ที่ได้แค่ `license.manage` — สมมติสร้างขึ้นเพื่อให้ใครสักคนดูแลเรื่อง licensing โดยไม่แตะส่วนอื่นของ platform config — จะยังได้ 403 ทุกครั้งที่บันทึกที่นี่ เพราะ resource ที่ decorator นี้ตรวจคือ `platform_config` ไม่ใช่ `license` คอมเมนต์ของ backend เองบน `LICENSE_MANAGE_PERMISSION` ระบุเหตุผลตรง ๆ: มันเป็น resource แยกต่างหากโดยตั้งใจ เพื่อไม่ให้ role ที่สร้างมาให้แก้คีย์อื่น (เช่น Email Verification) พลอยได้ kill switch การบังคับใช้ license ของทั้งแพลตฟอร์มติดไปด้วยเงียบ ๆ ไม่ได้มีไว้ให้ `license.manage` เดี่ยว ๆ เป็นทางลัดที่ขอบเขตแคบกว่าไปสู่การ์ดนี้

คำอธิบายที่ scaffold ไว้ก่อนหน้าของโมดูล [Licenses](/th/platform/licenses) เคยกำหนด `license.manage` ผิดว่าเป็นด่าน CRUD ของโมดูลนั้น ได้แก้ไขที่นั่นแล้ว หน้านี้คือแหล่งความจริงเรื่องนี้

### 4.4 สิ่งที่ `platform_config.read`/`.manage` ไม่ครอบคลุม

การอ่านข้อมูลหน้าจอนี้ไม่ต้องการคีย์ที่ละเอียดกว่าที่กั้นค่าตั้งแต่ละอย่างในส่วนอื่นของผลิตภัณฑ์ — เช่นค่าของ Expiry Thresholds เองก็เปิดให้อ่านผ่าน endpoint **แยกต่างหาก ไม่มี permission โดยตั้งใจ** (`expiryThresholdService`, ใช้โดย `ExpiryThresholdContext`) เพื่อให้ผู้ใช้ทั่วไปที่ดูหน้า `/licenses` หรือ `/clusters` — ซึ่งไม่มี `platform_config.read` — ยังเห็น badge "ใกล้หมดอายุ" ที่ถูกต้องได้ โดยไม่ต้องได้รับสิทธิ์เข้าหน้าจอ admin นี้

## 5. โมดูลที่เกี่ยวข้อง

- [Licenses](/th/platform/licenses) — ผู้บริโภคของทั้ง kill switch `license.enforcement_enabled` และหน้าต่างแสดงผล `expiry_thresholds` และเป็นโมดูลที่คู่ permission ของตัวเอง (`subscription.read`/`subscription.manage`) ไม่เกี่ยวข้องกับ `license.manage` เลย (§4.3)
- Clusters, Business Units — ก็อ่านหน้าต่าง `expiry_thresholds` สำหรับ badge "ใกล้หมดอายุ" และตัวนับโควตาของตัวเอง (ดู data model ของโมดูล [Licenses](/th/platform/licenses) สำหรับรูปแบบการใช้ threshold ร่วมกัน)
- Email Settings — เป็นเจ้าของ `tb_email_sender_profile` (credential SMTP) และคีย์ registry `email_routing` (§3.5) แก้จากหน้าจอของตัวเอง แต่เขียนผ่านพื้นผิว `/api-system/platform/configs` เดียวกันนี้
- Feature Flags — เป็นเจ้าของคีย์ registry `feature_flags` (§3.5) ผ่านคู่ endpoint เฉพาะของตัวเอง ไม่ใช่พื้นผิวของโมดูลนี้
- [Platform RBAC](/th/platform/rbac) — แคตตาล็อก permission ที่เห็น `platform_config.read`/`.manage`, `license.manage` และทุกคีย์บนหน้านี้เคียงข้างทุก resource อื่นของแพลตฟอร์ม

## 6. แหล่งอ้างอิง

path ทั้งหมดด้านล่างคือ `../carmen-platform` (Platform admin SPA, HEAD `157a65e`, 2026-09-04) ยกเว้นที่ขึ้นต้นด้วย `../carmen-turborepo-backend-v2` (backend monorepo, HEAD `937cf5ac4`, 2026-09-06)

- `../carmen-platform/src/pages/PlatformConfigManagement.tsx` — เปลือกหน้าจอ การผูก permission (บรรทัด 69-81) แถบสถานะ กริดการ์ด `DevDebugSheet`
- `../carmen-platform/src/pages/platformConfig/ConfigCardShell.tsx` — เปลือกการ์ดและตัว render ฟิลด์อ่าน/แก้ที่ใช้ร่วมกัน
- `../carmen-platform/src/pages/platformConfig/{InvitationConfigCard,InvitationLimitsCard,invitationDefaults}.ts(x)` — สองการ์ดของคีย์ `invitation`
- `../carmen-platform/src/pages/platformConfig/SignupConfigCard.tsx`, `LinkConfigCard.tsx`, `NotificationEmailConfigCard.tsx`, `LicenseEnforcementCard.tsx`, `ExpiryThresholdsCard.tsx`, `PlatformMigrationConfigCard.tsx` — การ์ดที่เหลืออีกเจ็ดใบ
- `../carmen-platform/src/services/platformConfigService.ts` — REST client `getAll`/`getByKey`/`update`/`patch`
- `../carmen-platform/src/context/ExpiryThresholdContext.tsx`, `src/services/expiryThresholdService.ts` — ตัวอ่าน threshold แยกต่างหาก ไม่มี permission ที่ใช้ทั้งแพลตฟอร์ม
- `../carmen-platform/src/utils/audit.ts` — `normalizeAudit`/`latestActor` ที่ทุกการ์ดใช้ร่วมกันในบรรทัด audit ท้ายการ์ด
- `../carmen-platform/src/utils/permissions.ts` — ทางลัด super-admin ของ `checkPermission()` (§4.1)
- `../carmen-platform/src/components/nav/platformNav.ts` (บรรทัด 38), `src/App.tsx` (บรรทัด 501-502) — รายการ nav และการลงทะเบียน route
- `../carmen-platform/src/pages/emailSettings/EmailRoutingCard.tsx` (บรรทัด 124), `src/pages/EmailSettingManagement.tsx` (บรรทัด 48) — ข้อเท็จจริงข้ามโมดูลเรื่อง `email_routing` ใน §3.5
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_configs/platform_configs.controller.ts` — พื้นผิว REST, `writeKeyDenial()` (§3.3, §4.2)
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.schema.ts` — `PLATFORM_CONFIG_REGISTRY` schema/default ของทุกคีย์ (§3.2, §3.5)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/license/{license.service.ts,license.interceptor.ts,license.evaluator.ts,license-route-resolver.ts}` — กลไกการบังคับใช้ license (§3.2)
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/common/{seat-enforcement-flag.service.ts,expiry-thresholds.service.ts}` — การบังคับที่นั่งและการอ่าน expiry threshold ใน micro-cluster
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/platform-migration.guard.ts` — guard ที่ cache 60 วิของ API platform-migration เอง
- `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` (บรรทัด 319-350, 1362-1385, 1684-1687) — ผู้อ่าน `signup`/`email_verification`/`password_reset`
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/feature_flags/feature_flags.controller.ts` — คู่ endpoint เฉพาะของคีย์ `feature_flags` (§3.5)
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_platform_config` (บรรทัด 1462)

## 7. หน้าย่อยของโมดูลนี้

- [Data Model](/th/platform/platform-config/data-model) — entity `tb_platform_config`, `PLATFORM_CONFIG_REGISTRY` เต็มรูปแบบ (ทั้งสิบคีย์ รวมสองคีย์ที่หน้าจอนี้ไม่เคยแสดง) และแผนที่ผู้อ่านหลายกระบวนการที่อยู่เบื้องหลังผลของ §3.2
