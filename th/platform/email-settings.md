---
title: การตั้งค่าอีเมล (Email Settings)
description: หน้าจอเดียว สอง section ที่เป็น peer กัน — รายการโปรไฟล์ผู้ส่ง SMTP ที่ตั้งชื่อได้ กับแผนที่เส้นทางที่ตัดสินว่าอีเมลขาออกทั้งห้าเส้นทางส่งด้วยโปรไฟล์ไหน
published: true
date: '2026-09-06T20:00:00.000Z'
tags: book/platform, email-settings
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# การตั้งค่าอีเมล (Email Settings)

โมดูล **Email Settings** คือหน้าจอเดียว `EmailSettingManagement` ที่ `/platform/email-settings` ซึ่งดูแลสองสิ่งที่เคยเป็นเรื่องเดียวกัน: รายการหลักที่ตั้งชื่อได้ของโปรไฟล์ผู้ส่ง SMTP ขาออก (`tb_email_sender_profile`) กับแผนที่เส้นทาง (`email_routing` ซึ่งเป็นคีย์หนึ่งของ `tb_platform_config` — ตาราง config **เดียวกัน** กับที่โมดูล [Platform Config](/th/platform/platform-config) แก้ไข) ที่ตัดสินว่าโปรไฟล์ไหนส่งอีเมลขาออกทั้งห้าเส้นทาง ได้แก่ สมัคร/บัญชีมีอยู่แล้ว, ยืนยันอีเมล, คำเชิญ, ลืมรหัสผ่าน, และแจ้งเตือน ทั้งสองสิ่งเคยเป็นเรื่องเดียวกัน — หนึ่งแถวโปรไฟล์ต่อหนึ่งค่า enum `purpose` ที่ตายตัว — จนกระทั่ง migration `20260808130000_email_profile_master_and_routing` แยกออกจากกัน โดยมีเป้าหมายชัดเจนให้ผู้ดูแลเพิ่มผู้ส่งใหม่ หรือเปลี่ยนว่าเส้นทางไหนใช้โปรไฟล์ไหน ได้จากหน้าจอ แทนที่จะต้องแก้ enum แล้ว deploy ใหม่ (§2)

> **At a Glance**
> **Component:** `EmailSettingManagement` &nbsp;·&nbsp; **Route:** `/platform/email-settings` &nbsp;·&nbsp; **Nav:** `permission: 'email_setting.read'`, `feature: 'email_settings'`, `groupKey: 'navGroup.platform'` (`platformNav.ts:39`) &nbsp;·&nbsp; **ด่านของโมดูลนี้เอง:** `email_setting.read` (ดู) / `email_setting.manage` (สร้าง/แก้/ลบโปรไฟล์ผู้ส่ง, ส่งอีเมลทดสอบ) — สอดคล้องกันทั้งฝั่ง frontend และ backend สำหรับทุก endpoint **ของโมดูลนี้เอง** (§4.1) &nbsp;·&nbsp; **จุดเดียวที่ไม่ใช่ด่านของโมดูลนี้เอง:** การ์ด Email Routing ซึ่งอ่านและเขียนแถว `platform_config` ผ่าน endpoint ที่ใช้ร่วมกับโมดูล Platform Config — ดู §4.2 ความไม่ตรงกันที่หน้านี้ถูกขอให้ไล่ตามให้ครบวงจรโดยเฉพาะ &nbsp;·&nbsp; **e2e suite:** **ไม่มี** — `../carmen-platform-e2e/tests/` ไม่มีโฟลเดอร์ `email-settings` ทุกคำกล่าวอ้างด้านล่างมาจากการอ่าน implementation ของ `../carmen-platform` และ `../carmen-turborepo-backend-v2` โดยตรง &nbsp;·&nbsp; **หน้าย่อย:** 1

## 1. ภาพรวม

หน้าจอดึงโปรไฟล์ผู้ส่งทั้งหมดในคำขอเดียว `emailSettingService.getAll()` → `GET /api-system/platform/email-settings?perpage=20` (`emailSettingService.ts:11-14`) กั้นด้วย `email_setting.read` และโหลดแผนที่เส้นทางแยกต่างหากผ่าน hook ที่ใช้ร่วมกัน `useEmailRouting()` (`hooks/useEmailRouting.ts`) ซึ่งเรียก `platformConfigService.getByKey('email_routing')` — client ของโมดูล **Platform Config** เอง ไม่ใช่ service ของโมดูลนี้ hook ถูกแยกออกมาโดยเจตนาเพื่อให้การ์ด routing กับการ์ดโปรไฟล์ทุกใบอ่าน mapping ชุดเดียวกัน (`useEmailRouting.ts:18-24`): ถ้าต่างคนต่างยิงเอง ผังเส้นทางกับป้าย "carries: Invitation, Forgot password" บนการ์ดโปรไฟล์อาจแสดงข้อมูลคนละชุดบนจอเดียวกัน

หน้าจอจัด layout เป็นสอง section ที่เป็น peer กัน (`SectionHeading` ทั้งคู่ render เป็น `<h2>`, `EmailSettingManagement.tsx:134-191`):

| Section | Component | สิ่งที่แก้ไข |
| --- | --- | --- |
| Email Routing | `EmailRoutingCard` → `RoutingPanel` | แถว config `email_routing` — โปรไฟล์ที่แต่ละเส้นทางในห้าเส้นทาง (§3.2) ส่งผ่าน |
| Sender Profiles | กริดของ `EmailSettingCard` หนึ่งใบต่อหนึ่งโปรไฟล์ บวกการ์ดที่ว่างสำหรับสร้างใหม่ | แถว `tb_email_sender_profile` — ชื่อ, ที่อยู่ผู้ส่ง, ปลายทาง SMTP, credential, สถานะใช้งาน |

คอมเมนต์ระดับ component ที่ `EmailSettingManagement.tsx:22-30` บันทึกการแก้ไขลำดับชั้นภาพที่ตั้งใจ (`#260`, commit `8fc31e7`): ทั้งสองหัวข้อ section render เป็น `<h2>` น้ำหนักเท่ากันโดยตั้งใจ เพราะ layout เดิม section routing ไม่มีหัวข้อของตัวเอง (แค่หัวการ์ดเปล่า ๆ) ซึ่งดูเบากว่า "Sender profiles" ด้านล่าง ทั้งที่ routing เป็นเรื่องระดับสูงกว่า — ลำดับ heading ของเอกสารเดิมจึงเป็น H1 → H3 → H2 → H3 เงียบ ๆ ซึ่งข้ามชั้น

**มีแค่การ์ดเดียวที่เปิดแก้ได้ในเวลาเดียวกัน** ติดตามด้วยตัวแปรระดับหน้าเดียว `editingPurpose: string | null` (`'routing'`, `'new'`, หรือ id ของโปรไฟล์) การขอแก้การ์ดที่สองขณะที่การ์ดหนึ่งเปิดอยู่แล้วจะไม่สลับทันที — มันเปิด dialog ยืนยัน ("ทิ้งการแก้ไข?") และสลับ `editingPurpose` ก็ต่อเมื่อยืนยันเท่านั้น (`EmailSettingManagement.tsx:94-100, 246-259`) ตัวกัน `useUnsavedChanges` ของหน้าจะทำงานทุกครั้งที่มีการ์ด*ใด*เปิดอยู่ ด้วยเหตุผลเดียวกับที่ [Platform Config](/th/platform/platform-config) บันทึกไว้สำหรับการออกแบบเปิดแก้ได้ทีละการ์ดของตัวเอง: แต่ละการ์ดถือ form state ของตัวเอง หน้าจึงคำนวณความสกปรกรายฟิลด์ไม่ได้โดยไม่ผูกกับการ์ดทุกใบ

การบันทึกโปรไฟล์ใดก็ตามจะดึงรายการทั้งหมดใหม่ (`handleSaved` → `fetchAll()`) และการ์ดโปรไฟล์ทุกใบใช้ key `` `${setting.id}-${setting.doc_version ?? 'new'}` `` (`EmailSettingManagement.tsx:221-224`) — การบันทึกที่เปลี่ยน `doc_version` จะ remount การ์ดใบนั้น รีเซ็ตฟอร์มกลับเป็นค่าที่เพิ่งดึงมาใหม่ นี่คือสิ่งที่ทำให้เส้นทางกู้คืนจาก optimistic lock ทำงานได้: เมื่อเจอ `409` การ์ดจะขอให้หน้า refetch โดย*ไม่*ออกจากโหมดแก้ (`onSaved({ keepEditing: true })`, `EmailSettingCard.tsx:229-234`) และการ remount จาก `doc_version` ใหม่จะรีเฟรชฟอร์มในที่เดิม

แผงดีบั๊กที่ใช้เฉพาะตอนพัฒนา (`DevDebugSheet`, มุมล่างขวา, component เดียวกับที่ [Platform Config](/th/platform/platform-config) ใช้) แสดง payload ดิบของ `GET /api-system/platform/email-settings` — เติมค่าเฉพาะเมื่อ `process.env.NODE_ENV === 'development'` และ render เฉพาะเมื่อ `import.meta.env.DEV` เป็นจริง จึงคอมไพล์ทิ้งไปใน production ไม่ว่าผู้ดูจะมีสิทธิ์อะไร คอมเมนต์ของหน้าเองระบุว่าปลอดภัยที่จะเก็บไว้แม้มีข้อมูลจริง เพราะ API คืน `smtp_password` แบบมาสก์เสมอ (§3.3) — ไม่มีทางรั่วความลับที่ถอดรหัสได้

## 2. บริบททางธุรกิจ

ก่อน migration `20260729000000_email_sender_profile` ตารางนี้ไม่มีอยู่ในรูปปัจจุบันเลย: มันถูกสร้างด้วยคอลัมน์ `purpose` ที่พิมพ์เป็น enum สามค่า (`no_reply`, `support`, `billing`) พร้อม unique index บน `(purpose, deleted_at)` — หนึ่งโปรไฟล์ที่ยังไม่ถูกลบต่อหนึ่ง purpose เท่านั้น การเพิ่มอีเมลชนิดที่สี่แปลว่าต้องเพิ่มค่า enum แล้ว deploy ใหม่ migration `20260808130000_email_profile_master_and_routing` เอาเพดานนั้นออก: มันตั้งชื่อแถวเดิมแต่ละแถวตาม purpose ที่มันเคยผูกอยู่ ย้ายความไม่ซ้ำจาก `purpose` ไปที่ `name` ที่ผู้ดูแลตั้งเอง ลบคอลัมน์ `purpose` ทิ้ง และ seed แถว `tb_platform_config` ใหม่ (`key = 'email_routing'`) ที่ชี้ทุกเส้นทางในห้าเส้นทางไปยังโปรไฟล์ "No-reply" เดิมที่มีอยู่แล้ว — migration เองจึงไม่เปลี่ยนอะไรที่มองเห็นได้สำหรับ deployment ที่รันอยู่แล้ว เปลี่ยนแค่โครงสร้างการเก็บข้อมูลข้างใต้เท่านั้น จากจุดนั้นเป็นต้นมา โปรไฟล์คือผู้ส่งเอนกประสงค์ที่ตั้งชื่อได้ ซึ่งผู้ดูแลสร้างได้อย่างอิสระ และการกำหนดว่าเส้นทางไหนใช้โปรไฟล์ไหนอยู่ในแผนที่ routing แยกต่างหากทั้งหมด (§3.2) — การเพิ่มผู้ส่งตัวที่หก หรือย้าย Invitation ไปใช้มัน คือการเปลี่ยนหน้าจอ ไม่ใช่การ deploy อีกต่อไป

**ซากฟอสซิลของ schema ที่ควรจำหน้าได้ทันทีที่เห็น:** enum `enum_email_sender_purpose` เดิมยังคงประกาศอยู่ใน schema (`schema.prisma:1415-1425`) และไม่มีคอลัมน์ใดอ้างถึงมันเลย — migration ลบแค่*คอลัมน์*ที่ใช้มัน ไม่ได้ลบตัว type คอมเมนต์ของมันตอนนี้กลายเป็นตัวหลอกที่อันตราย: มันบอกว่า "เส้นทางที่ยังไม่มีโปรไฟล์ของตัวเองจะถอยไปใช้ `no_reply`" — ซึ่งเป็นจริงสำหรับดีไซน์ก่อน 2026-08-08 แต่เท็จสำหรับดีไซน์ปัจจุบัน ซึ่งปลายทางสำรองคือโปรไฟล์ที่ผู้ดูแลตั้งเป็น `default` ใน mapping `email_routing` (§3.2) ที่ไม่จำเป็นต้องชื่อ "No-reply" เลยด้วยซ้ำ อย่าใช้คอมเมนต์ของ enum นี้เป็นคำอ้างอิงพฤติกรรมปัจจุบัน มันบันทึกสถาปัตยกรรมที่ migration นี้แทนที่ไปแล้ว

## 3. แนวคิดสำคัญ

### 3.1 สองเรื่องที่เป็น peer กันบนหน้าจอเดียว: ใครส่งได้ กับใครส่งอะไร

โปรไฟล์ผู้ส่ง (§4 ของ data model) กับ routing ของเส้นทางอีเมล (section นี้) เป็นแกนที่แยกจากกันโดยตั้งใจ โปรไฟล์ที่ไม่มีเส้นทางไหนใช้เลยยังโชว์ในกริดว่าตั้งค่าครบ แค่ไม่มีใครใช้ (`pages.emailSettings.laneDark`, render โดย `Lane` component ของ `RoutingPanel` เมื่อ `carries === 0`) — การลบโปรไฟล์ที่ดู "ไม่มีใครใช้" ยังถูกกั้นเหมือนการลบโปรไฟล์ที่มีคนใช้อยู่ เพราะ "ไม่มีใครใช้" อ่านมาจาก routing map ซึ่งอาจกำลังโหลดหรือโหลดไม่สำเร็จ (§4.2) ในจังหวะที่การ์ดโปรไฟล์ render พอดี ตอนนั้น `lane` เป็น `null` ไม่ใช่ `false` และการ์ดตั้งใจไม่พูดเรื่อง routing เลยแทนที่จะพูดคำว่า "ไม่มีใครใช้" ผิด ๆ (`EmailSettingCard.tsx`, คอมเมนต์ของ prop `lane` เอง)

### 3.2 ห้าเส้นทางอีเมล — อะไรกระตุ้น, ค่าตั้งอะไรควบคุม, และส่งจริงจากไหน

`src/constants/emailFlows.ts` นิยามรายการห้าเส้นทางตายตัวที่เส้นทางหนึ่งกำหนดปลายทางได้ (`EMAIL_FLOWS`, ใช้ render ทั้งเลนของ `RoutingPanel` และ label/เมนูของ `FlowChip` แต่ละใบ) รายการนี้คือ*แคตตาล็อกปลายทาง*ฝั่ง UI เท่านั้น ตัวกระตุ้นจริง ค่าตั้งอายุลิงก์ และคำสั่งส่งจริงของแต่ละเส้นทางอยู่ที่ backend แยกกันเป็นสอง service ใน `../carmen-turborepo-backend-v2`:

| เส้นทาง | กระตุ้นโดย | คีย์ `platform_config` ที่ควบคุม | ส่งจากที่ไหน |
| --- | --- | --- | --- |
| **register** | `AuthService.signupRequest()` (micro-business, `auth.service.ts:1396-1481`) — endpoint ขอสมัครแบบ self-service ที่ตอบ `200` เสมอไม่ว่าผลจะเป็นอย่างไร เพื่อไม่ให้ใช้สำรวจว่ามีบัญชีอยู่แล้วหรือไม่ **สองข้อความต่างกันใช้เส้นทางเดียวกันนี้** เลือกตามสถานะบัญชีของอีเมลนั้น: อีเมลใหม่/ยึดคืนได้ ได้รับ `sendSignupLinkEmail()` ("Confirm your email to finish signing up", `auth.service.ts:3065-3092`); อีเมลที่มีบัญชีอยู่แล้วหรือชนกับ username ได้รับ `sendAccountExistsEmail()` ("You already have a Carmen account" — ข้อความที่ปิด enumeration oracle ในขณะที่ยังช่วยผู้ใช้จริงได้ `auth.service.ts:3100-3116`) ทั้งคู่ไหลผ่าน helper ร่วม `sendPlatformEmail(..., 'register')` (`auth.service.ts:3127-3151`) | `signup` — `verify_base_url`/`link_expiry_hours` อ่านผ่าน `readSignupConfig()` (`auth.service.ts:322-327`) | micro-business ผ่าน RPC `Notifications.platformEmailSend` ไปยัง micro-notification |
| **verify_email** | `AuthService.resendVerificationEmail()` (`auth.service.ts:1329-1382`) — endpoint แยกต่างหาก **เส้นทางเดิม (legacy)** สำหรับบัญชีที่มีอยู่แล้วใน `tb_user` โดย `email_verified_at: null` (สร้างโดยตรง หรือมีมาก่อนที่ flow สมัครจะกลับทิศทางในปี 2026) ยังทำงานพร้อมกันกับ `register` ด้านบน ไม่ได้ถูกแทนที่ ส่ง `sendEmailVerification()` ("Verify your email address", `auth.service.ts:3010-3057`) | `email_verification` — `base_url`/`expiry_hours` อ่านผ่าน `readEmailVerificationConfig()` (`auth.service.ts:335-338, 1364`) | micro-business ผ่าน RPC เดียวกัน |
| **forgot_password** | `AuthService.forgotPassword()` (`auth.service.ts:1648`+) ซึ่งเรียก `sendPasswordResetEmail()` แบบ **fire-and-forget** (ไม่มี `await`) เพื่อไม่ให้การส่งอีเมลล้มเหลวทำให้คำขอลืมรหัสผ่านล้มไปด้วย (`auth.service.ts:2923-2999`, คอมเมนต์บรรทัด 2989-2996 อธิบายเหตุผลที่ตั้งใจไม่ throw) ส่ง "Password Reset Request" พร้อมทั้งลิงก์และรหัสสั้น | `password_reset` — `base_url`/`expiry_hours` อ่านผ่าน `readPasswordResetConfig()` (`auth.service.ts:348-350`) | micro-business ผ่าน RPC เดียวกัน |
| **invitation** | `UserInvitationService` (micro-cluster, `user-invitation.service.ts`) — สามจุดเรียกที่ต่างกัน ทั้งหมดเป็นเส้นทางนี้: `sendInvitationEmail()` (บรรทัด 303, เรียก RPC ที่ 336) ส่งลิงก์คำเชิญเอง เรียกจาก `createInvitation()` และ `resendInvitation()`; `notifyAccountCreatedFromInvitation()` (บรรทัด 1254, เรียก RPC ราวบรรทัด 1276) ส่งข้อความยืนยันสร้างบัญชีเมื่อผู้ถูกเชิญสมัครเสร็จผ่าน `acceptWithSignup()`; `notifyAddressConflict()` (บรรทัด 1336, เรียก RPC ราวบรรทัด 1412) ส่งข้อความแจ้งความขัดแย้งเมื่อการรับคำเชิญชนกับบัญชีที่มีอยู่แล้ว | `invitation` — ครึ่ง `base_url`/`expiry_days` ของคีย์สองการ์ด `invitation` ที่บันทึกไว้ในหน้า landing ของ [Platform Config](/th/platform/platform-config) §3.2 | micro-cluster ผ่าน RPC เดียวกัน |
| **notification** | **ไม่พบตัวกระตุ้นที่ไหนเลย** การค้นทั้ง repository หาทุกจุดที่เรียก RPC contract ที่ทุกเส้นทางในโมดูลนี้ใช้ร่วมกัน `Notifications.platformEmailSend` (`packages/rpc-contract/src/contracts/notifications.ts:31`) พบพอดี **เจ็ด**จุด — สามจุดใน `auth.service.ts` (บรรทัด 2951, `forgot_password`; บรรทัด 3032, `verify_email`; บรรทัด 3135, helper ร่วม `sendPlatformEmail()` ที่ทั้งสองข้อความของ `register` เรียกผ่าน) สามจุดใน `user-invitation.service.ts` และตัว handler `@MessagePattern` เองใน `micro-notification` ไม่มีจุดไหนส่ง `flow: 'notification'` การค้นเดียวกันข้าม `micro-report`, `micro-cronjobs`, และ `micro-data` ก็ไม่พบอะไรเช่นกัน ผังเส้นทางยังคง render เลน "Notification" ที่ยังใช้งานได้ — ผู้ดูแลตั้งให้มันชี้ไปโปรไฟล์ไหนก็ได้ — แต่ไม่มีอะไรในโค้ดปัจจุบันส่งผ่านมันเลย | *(ไม่พบ)* | *(ไม่พบ)* |

**เส้นทาง `notification` ด้านบนเป็นคนละเรื่องกับคีย์ `notification_email` ของ platform-config** ที่บันทึกไว้ในหน้าของโมดูล [Platform Config](/th/platform/platform-config) เอง (§3.2 ของหน้านั้น) — คีย์นั้นเป็นแถว `tb_platform_config` แยกต่างหากไม่เกี่ยวกัน (รายชื่อผู้รับ + คำนำหน้าหัวเรื่องสำหรับอีเมลรายงาน/แจ้งเตือนภายใน) ซึ่งงานวิจัยของโมดูลนั้นก็พบว่าไม่มีผู้อ่านที่ยืนยันได้เช่นกัน การพบว่า "ไม่มีอะไรใช้สิ่งนี้จริง" สองครั้งอย่างเป็นอิสระต่อกัน บนกลไกสองอย่างที่บังเอิญมีคำว่า "notification" ร่วมกัน ควรพูดให้ชัดแทนที่จะปล่อยให้ผู้อ่านสับสน: สิ่งที่หน้านี้พบคือ**เลน routing อีเมล**ที่ไม่มีผู้ส่ง; สิ่งที่หน้า Platform Config พบคือ**คีย์ config**ที่ไม่มีผู้อ่าน อย่างใดอย่างหนึ่งไม่ได้ยืนยันหรือขึ้นกับอีกอย่าง

### 3.3 เส้นทางกลายเป็นการส่ง SMTP จริงได้อย่างไร — และเกิดอะไรขึ้นเมื่อส่งไม่ได้

ทุกเส้นทางด้านบนไปจบที่ resolver เดียวกัน `PlatformEmailService.resolveProfile()` (micro-notification, `platform-email.service.ts:114-138`): มันอ่านแถว `email_routing` ล่าสุดจาก `tb_platform_config` ตรวจสอบด้วย Zod schema หา `routing[flow] ?? routing.default` แล้วโหลดแถว `tb_email_sender_profile` นั้น**ก็ต่อเมื่อ**มันไม่ถูก soft-delete และ `is_active` เป็น `true` เท่านั้น ถ้าแถวหาย ถูกลบ หรือปิดใช้งาน `send()` จะรายงาน `{ sent: false, reason: 'no-config' }` และบันทึก log คำเตือนที่ระบุชื่อเส้นทางและ id โปรไฟล์ที่ค้างอยู่ — มันไม่เคยถอยไปใช้โปรไฟล์อื่นหรือ environment variable เลย

**ไม่มี environment-variable fallback อยู่ในไฟล์นี้เลย** แม้คอมเมนต์บน method พี่น้อง `resolveSmtpConfig()` จะอ้างตรงกันข้าม ("a failed lookup... falls through to env exactly as `send()` does", `platform-email.service.ts:195-196`) `process.env` ตัวเดียวที่อ่านในไฟล์นี้ทั้งไฟล์คือ connection string ของฐานข้อมูล (บรรทัด 93); `send()` คืน `no-config` เมื่อหาโปรไฟล์ไม่เจอตามที่อธิบายด้านบนเท่านั้น ไม่มีการอ่าน env ใด ๆ เลย `resolveSmtpConfig()` เองยังเป็นโค้ดที่ตายแล้วด้วย — ค้นทั่ว `micro-notification` พบว่ามัน**ไม่มีผู้เรียกเลย**; มีแค่ `send()`, `sendTest()`, และ `sendWithConfig()` เท่านั้นที่ต่อกับ handler `@MessagePattern` ที่ micro-business และ micro-cluster เรียกจริง คอมเมนต์ของมันบรรยายการผสานงานในอนาคต ("made public so the internal-notification path shares one SMTP source") ที่ไม่มีอยู่ในโค้ดปัจจุบัน — ให้ถือว่าคอมเมนต์นี้เป็นความตั้งใจในอนาคต ไม่ใช่คำบรรยายสิ่งที่ทำงานอยู่วันนี้

**deployment ที่ยังไม่เคยตั้งค่าจะเริ่มต้นด้วยค่า placeholder ที่ใช้งานไม่ได้** ค่า default ของ registry สำหรับคีย์ `email_routing` (`platform-config.schema.ts`, registry เดียวกับที่ [Platform Config](/th/platform/platform-config) บันทึกไว้) คือ `{ default: '00000000-0000-0000-0000-000000000000' }` — UUID ศูนย์ล้วนที่ไม่ตรงกับโปรไฟล์จริงตัวไหนเลย โดยตั้งใจ (คอมเมนต์ของ registry เองบอกว่าไม่มี default ที่มีความหมายจริง เพราะ id ของโปรไฟล์ต่างกันทุก environment) ในทางปฏิบัติ deployment ที่ upgrade มาจะไม่มีวันเจอ default นี้ เพราะ migration `20260808130000_email_profile_master_and_routing` seed mapping จริงที่ชี้ทุกเส้นทางไปยังโปรไฟล์ "No-reply" เดิมตอน migrate (§2) environment ใหม่ล้วนที่ไม่มีโปรไฟล์ให้ seed จะค้างอยู่กับ default placeholder — ทุกเส้นทางคืน `no-config` — จนกว่าผู้ดูแลจะสร้างโปรไฟล์อย่างน้อยหนึ่งตัวและบันทึก routing map ที่มี `default` จริง

### 3.4 การจัดการรหัสผ่าน

`smtp_password` เก็บแบบเข้ารหัส (`enc:v1`, AES-256-GCM, `decryptSecret`/`encryptSecret` จาก `@repo/secret-crypto`) และ**ไม่เคย**ถูกส่งกลับเป็น plaintext จาก endpoint ใดเลย — `findAll`/`findOne`/`create`/`update` ทุกตัวมาสก์มันเป็นสตริงคงที่ `••••••` ก่อนตอบกลับ (`email-sender-profile.service.ts:41-43`) component `PasswordField` ฝั่ง frontend ปฏิบัติต่อค่ามาสก์ว่าเป็น "ไม่เปลี่ยน อย่าส่งซ้ำ": payload การบันทึกละเว้น `smtp_password` ทั้งหมดเว้นแต่ผู้ดูแลจะพิมพ์ค่าใหม่จริง ๆ (`PasswordField.tsx:40-43`) และสตริงว่างก็ถูกปฏิบัติเหมือน "ไม่เปลี่ยน" เช่นกัน ไม่ใช่ "ล้างค่า" — คอมเมนต์ของ field เองระบุว่าตั้งใจให้เป็นแบบนี้ เพื่อไม่ให้การล้างกล่องข้อความโดยไม่ได้ตั้งใจไปลบ credential ที่ใช้งานอยู่ (`PasswordField.tsx:13-15`) ฝั่ง backend `passwordPatch()` (`email-sender-profile.service.ts:51-56`) เอง*รองรับ*การส่ง `null`/`''` ตรง ๆ เพื่อล้างรหัสผ่านที่เก็บไว้ แต่ไม่มีอะไรใน UI ของหน้าจอนี้สร้างค่านั้นได้ — การล้างรหัสผ่านของโปรไฟล์ไม่สามารถทำได้จากหน้า Email Settings วันนี้ ทำได้แค่แทนที่ด้วยรหัสใหม่เท่านั้น

### 3.5 การส่งอีเมลทดสอบ

โปรไฟล์ที่ตั้งค่าแล้วแต่ละใบ ในสถานะไม่ได้แก้ไข จะมีปุ่ม "Send test email" เปิด `TestEmailDialog` ซึ่งตั้งผู้รับเริ่มต้นเป็นที่อยู่ของผู้เรียกเองถ้าดูเหมือนอีเมล (`user.email.includes('@')` เพราะ `AuthContext` อาจเติม `user.email` มาจาก username ไม่ใช่ที่อยู่อีเมล) และปล่อยว่างให้ผู้ดูแลกรอกเองถ้าไม่ใช่ การส่งไปทาง endpoint ของโมดูลนี้เอง `POST /api-system/platform/email-settings/:id/test` (`email_setting.manage` ไม่ใช่ `.read` — การส่งเมล แม้แค่ทดสอบ ก็ต้องมี permission เขียน) ซึ่งถูกส่งต่อไปยัง `sendTest()` ของ micro-notification — เส้นทางเดียวใน service นี้ที่โหลดโปรไฟล์โดย**ไม่**ตรวจ `is_active` เพื่อให้ทดสอบโปรไฟล์ที่ปิดใช้งานอยู่ได้ก่อนจะเปิดกลับมาใช้ เหตุผลที่ล้มเหลว (`smtp-error`, `decrypt-failed`, `lookup-failed`, `no-config`) ถูกแปลงเป็นข้อความ toast ที่ทำอะไรต่อได้แตกต่างกันไป (`TestEmailDialog.tsx:27-33`) ไม่ใช่ข้อความล้มเหลวทั่วไปข้อความเดียว

## 4. บทบาทและสิทธิ์

### 4.1 ด่านของโมดูลนี้เอง — สอดคล้องกันทุกจุด

| จุด | Permission | ที่มา |
| --- | --- | --- |
| รายการใน sidebar, route `/platform/email-settings` | `email_setting.read` + feature `email_settings` | `platformNav.ts:39`; `App.tsx:491-494` |
| ปุ่ม Edit/Configure, Send test email, Unset ของทุกการ์ด Sender Profile | `email_setting.manage` (`canManage`) | `EmailSettingManagement.tsx:48`, ส่งลงมาเป็น prop `canManage` |
| `GET`/`POST`/`PUT`/`DELETE`/`POST .../test` บน `/api-system/platform/email-settings*` | `email_setting.read` (list/get) หรือ `email_setting.manage` (create/update/delete/test) | `platform_email-settings.controller.ts:55-56, 92-93, 129-130, 168-169, 210-211, 247-248` |

ทุก route ของโมดูลนี้**เอง**ตรงกับด่านฝั่ง frontend เป๊ะ — list/get บน `.read` ทุกการเขียน (รวมถึงการส่งทดสอบ) บน `.manage` ไม่มีความไม่ตรงกันในตารางนี้เลย

### 4.2 จุดเดียวที่ไม่ใช่ด่านของโมดูลนี้เอง — การ์ด Email Routing ไล่ให้ครบวงจร

เรื่องนี้ถูกโมดูล [Platform Config](/th/platform/platform-config) เองยกธงไว้ล่วงหน้าว่าเป็นความไม่ตรงกันที่ต้องตรวจสอบ ไม่ใช่แค่กล่าวอ้าง เมื่อไล่ให้ครบวงจร ทั้งฝั่งอ่านและฝั่งเขียน:

**ฝั่งอ่าน** `useEmailRouting()` เรียก `platformConfigService.getByKey('email_routing')` → `GET /api-system/platform/configs/email_routing` ซึ่ง controller ของโมดูล Platform Config กั้นด้วย **`platform_config.read`** (`platform_configs.controller.ts:198-200`) — ไม่ใช่ `email_setting.read` คำขอนี้ยิงทันทีทุกครั้งที่หน้า Email Settings mount สำหรับผู้ดู**ทุกคน** ไม่ว่าจะแก้อะไรได้หรือไม่ session ที่มีแค่ `email_setting.read` (พอจะเข้าหน้านี้ได้) แต่ไม่มี `platform_config.read` จะเห็นกริด Sender Profiles โหลดตามปกติ — คำขอนั้นถูกกั้นถูกต้อง ด้วยคีย์ของโมดูลนี้เอง — ในขณะที่การ์ด Email Routing ด้านบนแสดง error การโหลดค้างถาวร (`loadError`, `EmailRoutingCard.tsx:166-167`) เพราะ API เดียวที่มันพึ่งพากั้นด้วย resource ที่หน้าจอของโมดูลนี้ไม่เคยตรวจสอบเลย

**ฝั่งเขียน** `EmailRoutingCard.handleSave()` เรียก `platformConfigService.update('email_routing', payload)` → `PUT /api-system/platform/configs/email_routing` (`EmailRoutingCard.tsx:124`) การจะเจอปุ่ม Save ที่กดได้จริงต้องผ่านด่านฝั่ง frontend **สอง**ด่าน ไม่ใช่ด่านเดียว: `canManage` — `hasPermission('email_setting.manage')` คำนวณครั้งเดียวที่หน้า (`EmailSettingManagement.tsx:48`) — **และ** `!routingError` (`EmailSettingManagement.tsx:140-143`) ซึ่งจะเป็น false ก็ต่อเมื่อคำขออ่านใน "ฝั่งอ่าน" ด้านบนสำเร็จแล้วเท่านั้น `EmailRoutingCard` เองไม่มีการตรวจ permission ของตัวเองเลย เชื่อใจหน้าทั้งหมด แต่ตัวกัน error ฝั่งอ่านของหน้าเองทำให้ปุ่มนี้ render ไม่ได้เลยตามโครงสร้าง สำหรับ session ที่คำขอ `GET` ของมันโดน 403 ไปแล้ว ส่วน endpoint ฝั่ง **backend** ที่การบันทึกนั้นเรียกจริงต้องมี `platform_config.manage` (`platform_configs.controller.ts:236-238`, decorator `@RequirePlatformPermission` ของ route `PUT` ที่บังคับโดย `PlatformPermissionGuard` *ก่อน*ตัว handler จะทำงาน) — และ `writeKeyDenial()` ซึ่งเป็นด่านที่สองรายคีย์ของ handler เอง ไม่ได้เพิ่มอะไรสำหรับ `email_routing` เลย มันเข้มขึ้นเฉพาะ `license` กับ `platform_migration` เท่านั้น (บันทึกไว้ที่ [Platform Config](/th/platform/platform-config) §3.3) `email_routing` ไม่ใช่หนึ่งในสองคีย์นั้น ดังนั้น `platform_config.manage` เพียงอย่างเดียวคือสิ่งที่ endpoint ตรวจ

**สองคีย์นี้ไม่ตรงกัน — แต่กับดักไปถึงแค่ชุดเดียวที่เจาะจงเท่านั้น ไม่ใช่ "`email_setting.manage` โดยไม่มี `platform_config.manage`" แบบกว้าง ๆ** เพราะปุ่มนี้กั้นด้วย `!routingError` (ฝั่งอ่าน) session จึงต้องมี `platform_config.read` สำเร็จ*ก่อน*ที่จะเห็นปุ่ม Save บนการ์ดนี้ได้เลยด้วยซ้ำ กับดักที่ดูใช้งานได้จริงจึงต้องการ **`platform_config.read` มีอยู่ และ `platform_config.manage` ไม่มี** เพิ่มเติมจาก `email_setting.read`/`.manage` ของโมดูลนี้เอง: ผังโหลดปกติ ปุ่มปรากฏ ตัวแก้ไขเปิดได้ สลับปลายทางของทุก flow chip ได้ — แล้วกด Save จะโดน 403 ถูกปฏิเสธโดย `PlatformPermissionGuard` ก่อนที่ `writeKeyDenial()` หรือโค้ดแอปพลิเคชันใด ๆ จะทำงานเลย เพราะ resource ที่ decorator ของ endpoint ระบุคือ `platform_config` ไม่ใช่ `email_setting` session ที่มี `email_setting.manage` แต่**ไม่มี** `platform_config.*` เลย ไม่มีวันไปถึงกับดักนี้ได้ — มันจะติดที่ด่านอ่านก่อน (ฝั่งอ่านด้านบน) และปุ่มจะไม่ปรากฏให้กดเลย ไม่มีชุด permission ใดในทิศทางตรงข้ามที่ทำแบบนี้ได้เช่นกัน: session ที่มีแค่ `platform_config.*` และไม่มี `email_setting.*` เลย เข้า `/platform/email-settings` ไม่ได้ตั้งแต่แรก เพราะตัว route เองต้องการ `email_setting.read` (`App.tsx:493`)

**นี่ยืนยัน ไม่ใช่ขัดแย้ง กับสิ่งที่โมดูล Platform Config เองยกธงไว้ล่วงหน้า** โดยมีการแก้ไขหนึ่งจุดว่ากับดักฝั่งเขียนไปถึงได้อย่างไร โมดูลนั้นบรรยายรูปแบบเดียวกันนี้จากฝั่งของมันเอง (§3.5 ของหน้า landing) และตั้งใจปล่อยการตรวจสอบไว้ให้งานนี้ทำ เมื่ออ่านทั้งสองฝั่งอย่างเป็นอิสระ: `email_setting.manage` จำเป็นแต่ไม่พอที่จะบันทึก routing map จากหน้าจอนี้ — แต่ไม่พอในแบบที่เจาะจงมาก เพราะด่านอ่าน (`platform_config.read`) ต้องผ่านก่อน ปุ่ม Save จึงจะมีอยู่ให้เห็น `platform_config.manage` คือด่านเดียวที่ ถ้าขาดไปโดยที่ `platform_config.read` ยังอยู่ จะสร้างตัวแก้ไขที่ดูใช้งานได้แต่บันทึกไม่ได้

### 4.3 สาม session สามผลลัพธ์ที่ต่างกัน

การที่ด่านอ่านมีอำนาจยับยั้งปุ่ม (§4.2) แปลว่าการให้แค่ `email_setting.*` เพียงอย่างเดียว**ไม่**สร้างกับดักฝั่งเขียนขึ้นมา — มันสร้างแค่ความล้มเหลวฝั่งอ่านเท่านั้น สามชุดที่ควรทดสอบแยกกัน:

| Session ถือ | สิ่งที่เกิดขึ้นบนหน้าจอนี้ |
| --- | --- |
| `email_setting.read`/`.manage` เท่านั้น — ไม่มี `platform_config.*` เลย | กริด Sender Profiles โหลดและแก้ไขได้เต็มที่ (กั้นถูกต้องด้วยคีย์ของโมดูลนี้เอง) `GET` ของ Email Routing โดน 403, `routingError` ถูกตั้ง, และปุ่ม Edit Routing **ไม่ render เลย** — error การโหลดค้างถาวร ไม่ใช่กับดักฝั่งเขียน |
| `email_setting.read`/`.manage` **บวก** `platform_config.read` แต่**ไม่มี** `platform_config.manage` | `GET` ของ Email Routing สำเร็จ ผังโหลดปกติ และปุ่ม Edit Routing render (`canManage` กับ `!routingError` เป็นจริงทั้งคู่) ตัวแก้ไขเปิดได้ ทุกเส้นทางสลับปลายทางได้ — แล้ว Save โดน 403 **นี่คือกับดักฝั่งเขียนตัวจริง** และมันต้องการ `platform_config.read` แบบเจาะจง ไม่ใช่แค่ "มี `platform_config` permission บางตัว" |
| `email_setting.read`/`.manage` บวก `platform_config.read`/`.manage` | ทำงานตามที่ออกแบบไว้ — ชุดเดียวเท่านั้นที่ทำได้ |

**คำถามเปิดที่ต้องระบุไว้ตรง ๆ ไม่ใช่เดาเอาเอง:** มี role จริงที่ seed ไว้ในโปรดักต์นี้ให้ `platform_config.read` โดยไม่มี `.manage` หรือไม่ — ชุดเฉพาะที่แถวกลางของตารางต้องการเพื่อให้เป็นความเสี่ยงจริง — เป็นสิ่งที่บอกไม่ได้จากซอร์สโค้ดฝั่ง frontend/backend ที่อ่านสำหรับงานนี้ ขึ้นอยู่กับว่า role ถูกประกอบขึ้นจริงตอน runtime อย่างไร ซึ่งตาม source map เองก็ระบุว่าไม่สามารถแจกแจงได้จากซอร์สโค้ดอย่างเดียว (`PermissionCatalog.tsx` เสิร์ฟแคตตาล็อกสดจาก backend ไม่ใช่ repo นี้) ให้ถือว่ากับดักฝั่งเขียนเป็นผลลัพธ์ที่**เป็นไปได้ในเชิงโครงสร้าง**ของการจับคู่ permission นี้ ยืนยันได้ว่าไปถึงได้จริงในโค้ด แต่ไม่ใช่สถานการณ์ที่ยืนยันแล้วว่าเกิดขึ้นจริงใน deployment ใด ๆ

## 5. โมดูลที่เกี่ยวข้อง

- [Platform Config](/th/platform/platform-config) — เจ้าของคีย์ registry `email_routing` และ endpoint กลาง `/api-system/platform/configs` ที่การ์ด routing ของโมดูลนี้อ่านและเขียนผ่าน (§4.2) พร้อมทั้งบันทึกความไม่ตรงกันของ permission เดียวกันนี้ไว้จากฝั่งของตัวเองด้วย
- [Platform RBAC](/th/platform/rbac) — แคตตาล็อก permission ที่ `email_setting.read`/`.manage` และ `platform_config.read`/`.manage` ปรากฏเป็น resource อิสระจากกันทั้งคู่

## 6. แหล่งอ้างอิง

path ทั้งหมดด้านล่างคือ `../carmen-platform` (SPA ของ Platform admin, HEAD `157a65e`, 2026-09-04) ยกเว้นที่ขึ้นต้นด้วย `../carmen-turborepo-backend-v2` (backend monorepo, HEAD `937cf5ac4`, 2026-09-06)

- `../carmen-platform/src/pages/EmailSettingManagement.tsx` — เปลือกของหน้า, state machine ของ `editingPurpose`, การต่อสาย permission
- `../carmen-platform/src/pages/emailSettings/{EmailSettingCard,EmailRoutingCard,PasswordField,TestEmailDialog,routingLanes,RoutingPanel}.ts(x)` — component รายโปรไฟล์ทั้งห้า และโครงข้อมูลของ routing lane
- `../carmen-platform/src/constants/emailFlows.ts` — `EMAIL_FLOWS` แคตตาล็อกห้าเส้นทางที่ UI routing render
- `../carmen-platform/src/services/emailSettingService.ts`, `src/hooks/useEmailRouting.ts` — REST client ของโปรไฟล์และตัวโหลด routing map ที่ใช้ร่วมกัน
- `../carmen-platform/src/components/nav/platformNav.ts` (บรรทัด 39), `src/App.tsx` (บรรทัด 491-494) — รายการ nav และการลงทะเบียน route
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_email-settings/{platform_email-settings.controller.ts,platform_email-settings.service.ts}` — REST surface ของโมดูลนี้เองและ RPC proxy ไป micro-cluster/micro-notification
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/email-sender-profile/email-sender-profile.service.ts` — CRUD โปรไฟล์, การบังคับความไม่ซ้ำของชื่อ, การมาสก์/เข้ารหัสรหัสผ่าน
- `../carmen-turborepo-backend-v2/apps/micro-notification/src/platform-email/platform-email.service.ts` — `resolveProfile`/`resolveSmtpConfig`/`send`/`sendTest`, resolver ที่ทุกเส้นทางไปจบ
- `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` (บรรทัด 322-350, 1329-1481, 1648+, 2923-3151) — ตัวกระตุ้นและผู้ส่งของ `register`/`verify_email`/`forgot_password`
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/user-invitation/user-invitation.service.ts` (บรรทัด 303-370, 1254-1335, 1336-1470) — ตัวกระตุ้นและผู้ส่งของ `invitation`
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_configs/platform_configs.controller.ts` (บรรทัด 198-200, 236-238, 285-287, 145-159) — ด่านอ่าน/เขียนของ `email_routing` ที่ใช้ร่วมกับ [Platform Config](/th/platform/platform-config)
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.schema.ts` — entry ของ registry `email_routing` และ default placeholder ของมัน
- `../carmen-turborepo-backend-v2/packages/rpc-contract/src/contracts/notifications.ts` (บรรทัด 31) — RPC contract `platformEmailSend` ที่การส่งของทุกเส้นทางผ่าน
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (บรรทัด 1415-1460) — `enum_email_sender_purpose` (ที่ถูกทิ้งร้าง), `tb_email_sender_profile`
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/{20260729000000_email_sender_profile,20260808130000_email_profile_master_and_routing}/migration.sql` — การปรับดีไซน์จาก purpose-enum เป็นรายการที่ตั้งชื่อได้
- `../carmen-turborepo-backend-v2/packages/error-catalog/src/catalog.ts` (บรรทัด 513-514) — `EMAIL_SENDER_PROFILE_NOT_FOUND` (404), `EMAIL_SENDER_PROFILE_NAME_EXISTS` (409)

## 7. หน้าย่อยของโมดูลนี้

- [Data Model](/th/platform/email-settings/data-model) — entity `tb_email_sender_profile` แบบเต็ม, โครงสร้าง config `email_routing`, และกลไกฝั่งเขียน (optimistic locking, ความหมายของ password patch, ความไม่ซ้ำของชื่อ) เบื้องหลัง §3 และ §4 ด้านบน
