---
title: หน่วยธุรกิจ (Business Units)
description: เอนทิตีต่อ property/ต่อโรงแรม พร้อมฟอร์มหลายเซกชันที่ครอบคลุมข้อมูลระบุตัวตน ข้อมูลติดต่อ ภาษี รูปแบบ การคำนวณ การตั้งค่า การเชื่อมต่อฐานข้อมูล branding และรายชื่อผู้ใช้ที่ผูกกับ BU
published: true
date: 2026-07-29T06:50:54.000Z
tags: platform/business-units, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# หน่วยธุรกิจ (Business Units)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** หน้าจอ authoring ที่ใช้สร้างและตั้งค่าเอนทิตีปฏิบัติการที่ Carmen เรียกว่า **business unit** (BU) — หนึ่งแถวต่อหนึ่งโรงแรม/property/นิติบุคคล พร้อมฟิลด์ในฟอร์มที่ขับเคลื่อนทั้งบริบทของ tenant ใน inventory app และการมอบหมาย role ของผู้ใช้ในแพลตฟอร์ม &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ที่ทำงานกับ Platform admin SPA; การเข้าถึงของ operator ถูก gate ด้วย **permission key `cluster.*` ที่ reuse มา** ([rbac](/th/platform/rbac)) — ไม่มี key `business_unit.*` &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `business_unit` (ฟิลด์ระบุตัวตน `code`, `name`, `alias_name`, `is_hq`, `is_active`, `max_license_users`; บล็อกข้อมูลติดต่อสำหรับ hotel/company; ฟิลด์ภาษี; ฟิลด์รูปแบบวันที่/เวลา/ตัวเลข; `calculation_method`, `default_currency_id`; `db_connection`; `config[]` แถว key/value; branding `logo_file_token`/`avatar_file_token`) บวกกับตาราง join BU-to-user ที่ถือ `role` ระดับ BU เป็น `admin` หรือ `user` &nbsp;·&nbsp; **หน้าย่อย:** 2

## 1. ภาพรวม

Business unit คือ tenant ปฏิบัติการของ Carmen platform: หนึ่ง BU คือหนึ่งโรงแรม หนึ่ง property หรือหนึ่งนิติบุคคลที่ซื้อ รับ นับ และเบิกใช้ inventory หน้ารายการที่ `/business-units` (`BusinessUnitManagement.tsx`) เป็นแคตตาล็อกแบบ server-paginated ค้นหาได้ มี facet สำหรับ Active/Inactive และรายการที่ถูก soft-delete พร้อมส่งออก CSV ได้ และมีแถบสรุป **Overview** (`BuSummary` — จำนวนรวม/active/inactive/archived และจำนวน cluster ที่แตกต่างกันที่ครอบคลุม) คอลัมน์ thumbnail logo ต่อแถวที่เคยอยู่ในหน้ารายการนี้หายไปแล้ว

หน้าแก้ไขที่ `/business-units/:id/edit` และ `/business-units/new` (`BusinessUnitEdit.tsx`) ถูกเขียนใหม่จากการ์ด `CollapsibleSection` 9 ส่วนในกริดสองคอลัมน์ ให้เป็น **หน้าเอกสารเดียวแบบแก้ไข-in-place ("one-document")** — ไม่มี toggle read/edit อีกต่อไป ทุก field แสดงในรูปแบบแก้ไขได้เสมอ gate ด้วย boolean `canEdit` ตัวเดียว (`cluster.create` สำหรับ BU ใหม่, `cluster.update` ที่ scope ด้วย `cluster_id` สำหรับ BU ที่มีอยู่แล้ว) การ์ด hero (logo/avatar, code, ชื่อ cluster และ badge สถานะ Active/HQ ที่คลิกได้) อยู่เหนือกลุ่ม field แบบ inline หกกลุ่ม — **Details, Location, Contact, Company, Tax, Date & time** — ที่แทนที่เซกชัน Basic/Hotel/Company/Tax/Date-Time-Formats เดิม; แต่ละ field commit เมื่อ blur/Enter ผ่าน control `InlineField` ที่ใช้ร่วมกัน (คลิกเพื่อแก้ไข, `Escape` ยกเลิก) ตามด้วยอีกสี่เซกชันที่ซับซ้อนกว่าในสโครลเดียวกัน: **Calculation Settings, Number Formats, Branding** (อัปโหลด logo + avatar), **Configuration** และ **Database Connection** (ตอนนี้เป็นฟอร์มที่แก้ไขได้แบบมีโครงสร้าง — ดู §3) — จากนั้นสำหรับ BU ที่มีอยู่แล้วเท่านั้น มีการ์ด "advanced" อีกสามใบ (**Tenant Migrations, Tenant Seed, Interface Entitlement** — ทั้งหมด super-admin เท่านั้น ดู §3) และสุดท้ายคือการ์ด **Users** แถบล่างแบบ sticky แสดง Save Changes/Cancel เมื่อเอกสารมีการเปลี่ยนแปลง (หรือแสดงเสมอในโหมด create); `Ctrl/⌘+S` และ `Escape` ใช้เป็น keyboard shortcut ได้ การบันทึกได้รับการป้องกันด้วย token optimistic-lock `doc_version` แบบเดียวกับ [clusters](/th/platform/clusters)

แต่ละ BU เป็นของ **cluster** หนึ่ง cluster เท่านั้น (foreign key `cluster_id` เลือกจาก dropdown ในกลุ่ม Details) flow "สร้าง BU" เริ่มได้จากหน้ารายการ BU หรือจากหน้าแก้ไข cluster ซึ่ง navigate ไปที่ `/business-units/new?cluster_id=<id>` เพื่อ preselect parent ให้ นอกจากฟิลด์ระบุตัวตนและข้อมูลติดต่อ BU ยังเก็บค่า locale ที่ inventory runtime อ่านจะใช้ — `date_format`, `time_format`, `timezone`, ตัว format แบบ JSON `amount_format`/`quantity_format`/`recipe_format` ที่ default เป็น `th-TH`, `calculation_method` และ `default_currency_id` (ตอนนี้เป็น dropdown ของสกุลเงินระดับ tenant ของ BU เอง โหลดแบบ lazy เมื่อรู้ `code` ของ BU แล้ว) — บวกกับ array `config[]` ที่เป็นแถว key/value แบบ free-form และ `db_connection` ที่ตอนนี้เก็บเป็นรายการ field key/value ที่แก้ไขได้ (ไม่ใช่ JSON blob แบบอ่านอย่างเดียว) ที่ชี้ BU ไปยัง schema ของ tenant ของตน รายละเอียดต่อฟิลด์และพฤติกรรมของหน้าจออยู่ในหน้าย่อย — หน้า landing นี้เพียงปูทาง

## 2. บริบททางธุรกิจ

ในธุรกิจโรงแรม หน่วยที่เล็กที่สุดที่มีบัญชีของตัวเอง มีสกุลเงินของตัวเอง และมี supply chain ระดับท้องถิ่นของตัวเอง คือ property — โรงแรมเดี่ยวภายในกลุ่มแบรนด์ Carmen จึงโมเดลสิ่งนี้เป็น business unit ทุก inventory transaction (GRN, store requisition, physical count, spot check) อยู่ในขอบเขตของ BU เดียว ทุกรายงานรันกับ schema ของ BU เดียว และผู้ใช้ทุกคนได้รับสิทธิ์เข้าถึง BU หนึ่งหรือมากกว่าหนึ่ง พร้อม role ที่ใช้ภายในแต่ละ BU แถว `business_unit` จึงถือมากกว่าข้อมูลระบุตัวตน มันถือค่า locale ที่ inventory UI แสดง (รูปแบบวันที่และตัวเลข, timezone, default currency) ถือ knob ของการคำนวณต้นทุน (`calculation_method`) ที่ valuation engine ใช้อ้างอิง ถือการเชื่อมต่อฐานข้อมูลของ tenant ที่แพลตฟอร์มใช้ route query ไปยัง schema ของ property นั้น และถือเพดานสิทธิ์การใช้งาน (`max_license_users`) ที่จำกัดว่าผู้ใช้กี่คนจะล็อกอินได้

เนื่องจาก BU ยังเป็นจุดที่ผู้ใช้กลายเป็นมีความหมายในเชิงปฏิบัติการ หน้าแก้ไขจึงทำหน้าที่เป็น workbench สำหรับ assign ผู้ใช้ด้วย card Users แสดงทุกคนที่มีสิทธิ์เข้าถึง BU นี้ พร้อม **BU role** (`admin` หรือ `user`) ที่ orthogonal กับ RBAC assignment ระดับแพลตฟอร์มบนบัญชีผู้ใช้เอง ([rbac](/th/platform/rbac)) สมาชิก BU ใหม่ถูกเลือกจาก cluster ที่เป็นแม่ของ BU นั้น — ผู้ใช้ต้องอยู่ใน cluster ก่อนถึงจะถูกเพิ่มเข้า BU ภายใน cluster ได้ ซึ่งช่วยรักษาขอบเขตของ tenant ให้สะอาด การเข้าถึง route ของ BU เป็นแบบ permission-gated แต่มีจุดพลิก: โมดูลนี้ยืม key `cluster.read` / `cluster.create` / `cluster.update` มาใช้แทนที่จะนิยาม key ของตัวเอง — ดู §4

การ์ด super-admin เท่านั้นอีกสามใบบนหน้าแก้ไขขยาย BU ให้ไปไกลกว่าการตั้งค่าธรรมดา เข้าสู่งานปฏิบัติการฐานข้อมูลระดับ tenant: **Tenant Migrations** ตรวจสอบและ apply database schema migration ที่ค้างอยู่กับฐานข้อมูล tenant ของ BU นั้นเอง; **Tenant Seed** รัน seed script กับฐานข้อมูลนั้น; และ **Interface Entitlement** ควบคุมว่า BU นี้มีสิทธิ์แสดง interface/brand ใดบ้าง (เลือกว่างเปล่า = ไม่จำกัด — ทุก interface แสดง ตรงกับ default ของ gateway) ทั้งสามต้องการ `isSuperAdmin` และ (สองอันแรก) ต้องมี `db_connection` ที่ไม่ว่าง เรียกใช้ service module ของตัวเอง ไม่ใช่ `businessUnitService`

## 3. แนวคิดสำคัญ

- **Business unit (BU)**: หนึ่งแถวใน `business_unit` ที่แทนหนึ่งโรงแรม/property/นิติบุคคล ทุก inventory transaction เป็นของ BU เดียว ทุกรายงานรันกับ BU เดียว
- **Cluster membership**: ทุก BU มี `cluster_id` ที่ไม่ nullable เลือกจาก dropdown ของ cluster หน้าแก้ไข cluster สามารถเปิด flow สร้าง BU โดย preselect `cluster_id` ผ่าน query parameter `/business-units/new?cluster_id=<id>`
- **HQ flag (`is_hq`)**: ระบุว่า BU นี้เป็นสำนักงานใหญ่ภายใน cluster ของตน — ตอนนี้แสดงเป็น badge "HQ" ที่คลิกได้ในการ์ด hero (toggle ได้ตรง ไม่มี checkbox/เซกชันแยกอีกต่อไป) ความหมายขึ้นอยู่กับโมดูลที่ใช้ค่านี้
- **Active flag (`is_active`)**: สลับว่า BU เปิดใช้งานเชิงปฏิบัติการหรือไม่ — ตอนนี้ก็เป็น badge ที่คลิกได้ในการ์ด hero เช่นกัน ไม่ใช่ checkbox ในฟอร์มอีกต่อไป BU ที่ inactive ยังแก้ไขได้ในหน้า admin แต่จะถูกกรองออกจากการเลือกตอน runtime ปกติ หน้ารายการแสดง Active/Inactive เป็น chip กรอง
- **Max licensed users (`max_license_users`)**: integer ที่ใส่หรือไม่ใส่ก็ได้ เพื่อจำกัดจำนวนผู้ใช้ที่ assign เข้า BU ได้ ว่าง = ไม่จำกัด
- **ที่อยู่ hotel/company แบบมีโครงสร้าง**: field ข้อความอิสระเดี่ยว `hotel_address`/`company_address` เดิม ถูกแทนที่ด้วยคอลัมน์แบบมีโครงสร้างสิบคอลัมน์ต่อฝั่ง — `*_address_line1`, `*_address_line2`, `*_sub_district`, `*_district`, `*_city`, `*_province`, `*_postal_code`, `*_country`, `*_latitude`, `*_longitude` — ทั้งกลุ่ม "Location" (hotel) และกลุ่ม "Company" ปุ่ม **Copy from hotel address** บนกลุ่ม Company จะคัดลอก field ที่อยู่ทั้งสิบของ hotel ไปยัง field ของ company แบบทางเดียวในคลิกเดียว (ยังเป็นแค่การแก้ไขฟอร์มในเครื่อง — ไม่มีอะไรถูกบันทึกจนกว่าจะกดปุ่ม Save ที่ sticky)
- **Tax information**: `tax_no` และ `branch_no` เก็บเลขประจำตัวผู้เสียภาษีของไทยและรหัสสาขาที่ใช้บนเอกสารพิมพ์
- **Date/Time formats**: `date_format`, `date_time_format`, `time_format`, `long_time_format`, `short_time_format` และ `timezone` ตั้งค่าว่า inventory UI จะ render timestamp ของ BU นี้อย่างไร — ตอนนี้รวมอยู่ในกลุ่ม inline เดียวชื่อ "Date & time" แทนที่จะเป็นเซกชันฟอร์มแยกต่างหาก
- **Number formats**: ตัว format แบบ JSON สามชุด — `amount_format`, `quantity_format`, `recipe_format` — บวกกับ `perpage_format` JSON ที่ขับเคลื่อนค่า default ของ pagination แต่ละ formatter default เป็น `{"locales":"th-TH","minimumIntegerDigits":2}` (perpage default เป็น `{"default":10}`)
- **Calculation settings**: `calculation_method` (`average`/`fifo` — ใช้โดย inventory valuation engine) และ `default_currency_id` — ตอนนี้เป็น `<select>` ที่ populate จาก `GET /api/config/:buCode/currencies` (ตาราง currency ระดับ tenant ของ BU เอง โหลดแบบ lazy เมื่อรู้ code ของ BU แล้ว) โดย fallback เป็น input ข้อความอิสระสำหรับ UUID หากดึงข้อมูลไม่สำเร็จ; code/name/symbol/decimals ที่ resolve แล้วยังคงแสดงข้าง ๆ ในโหมดอ่าน
- **Configuration array (`config[]`)**: รายการแบบมีลำดับของแถว `{ key, value, datatype }` แบบ free-form ที่เก็บเป็น JSON array บน BU ตัวเลือก Data Type ตอนนี้มี `enum` เพิ่มเข้ามาด้วยนอกเหนือจาก `string`/`number`/`boolean`/`date`/`json` ใช้โดย inventory app สำหรับ feature toggle ระดับ BU และการตั้งค่า integration หน้า admin ไม่บังคับ schema
- **Database connection (`db_connection`)**: ไม่ใช่บล็อก `<pre>` แบบอ่านอย่างเดียวอีกต่อไป — เป็นฟอร์มไฮบริดที่แก้ไขได้: เจ็ด **field ที่รู้จัก** (`host`, `port`, `database`, `schema`, `user`, `password`, `ssl`) render เป็น input แบบมี type (password ถูก mask พร้อม toggle แสดง/ซ่อน; `ssl` เป็น checkbox) บวกกับรายการ **field เพิ่มเติม** ที่เปิดกว้างสำหรับสิ่งอื่น ๆ field password เป็น write-only เมื่ออ่าน (backend จะ redact เป็นสตริงว่างเสมอเมื่ออ่าน list/detail) — ปุ่ม **Reveal current password** ที่ gate ด้วย super-admin เรียก endpoint แบบ on-demand เฉพาะเพื่อแสดงค่าที่เก็บจริง; การเว้นว่าง field นี้ตอน save จะ**ไม่**ล้างรหัสผ่านที่เก็บไว้
- **Branding (logo + avatar)**: แต่ละ BU มี **logo** สี่เหลี่ยมผืนผ้าและ **avatar** สี่เหลี่ยมจัตุรัส เก็บใน Prisma เป็น file token (`logo_file_token`, `avatar_file_token`) และ API คืนค่าเป็น presigned object ฝังในตัว (`logo: { url, expires_at }`, `avatar: { url, expires_at }`) การอัปโหลดทำบนเซกชัน Branding ของหน้าแก้ไขผ่าน multipart endpoint เฉพาะ หน้ารายการไม่แสดงคอลัมน์ thumbnail ของ logo อีกต่อไป (ถูกลบพร้อมกับการเพิ่มแถบสรุป Overview เช่นเดียวกับที่เกิดขึ้นบน [clusters](/th/platform/clusters))
- **Optimistic concurrency (`doc_version`)**: `tb_business_unit` มี counter `doc_version` (เพิ่มเมื่อ 2026-07-16, ทั้ง 35 ตารางของ platform); หน้าแก้ไขจะส่งค่านี้กลับไปทุกครั้งที่ `PUT` และแสดง toast แจ้ง conflict + โหลดใหม่เมื่อเจอ `409` ที่ล้าหลัง
- **คอลัมน์ audit**: หน้ารายการแสดงคอลัมน์ Created และ Updated (timestamp พร้อมชื่อผู้กระทำ) SPA จะ flatten object `audit` แบบ nested จาก API response (`audit.created.{at,name}`, `audit.updated.{at,name}`) สำหรับคอลัมน์วันที่ โดยยอมรับ shape แบบ flat รุ่นเก่าด้วย ซึ่งชนะเมื่อมีค่า (`item.created_at ?? item.audit?.created?.at`) เซลล์ Updated จะถูกละเมื่อ `updated_at` เท่ากับ `created_at`
- **BU role (`admin` vs. `user`)**: role ที่ผูกกับการ assign user-BU แต่ละครั้ง เก็บบนแถว join ของ BU-user คู่กับ `is_active` และ `is_default` ค่าคงที่ `BU_ROLES` (ตอนนี้อยู่ใน `businessUnitEdit/types.ts`) กำหนดสองค่าพอดี role นี้ **orthogonal** กับ permission assignment ของ Platform RBAC บนบัญชีผู้ใช้ BU role ควบคุมพฤติกรรมของผู้ใช้ใน inventory app สำหรับ BU นั้น ไม่ใช่การเข้าถึง route ของ admin
- **Pattern เพิ่ม user จาก cluster**: สมาชิก BU ใหม่ถูกเลือกจากรายชื่อผู้ใช้ของ cluster ที่เป็นแม่ (`clusterUsers`) — ผู้ใช้ต้องเป็นสมาชิก cluster ก่อนถึงจะถูกเพิ่มเข้า BU ภายใน cluster ได้ flow dialog นี้ (และ dialog Edit/Remove) ไม่เปลี่ยนแปลงจากการเขียนใหม่แบบ one-document — มีแค่ตัว toggle read/edit ระดับหน้าที่ครอบมันอยู่เท่านั้นที่ถูกลบไป
- **Soft delete**: BU ถูก soft-delete ผ่าน `deleted_at` / `deleted_by_name` หน้ารายการมี toggle filter "Show soft-deleted business units" ที่ทาบ badge แดง `Deleted` และคอลัมน์ "Deleted By" เพิ่มเพื่อ audit ต่างจาก [clusters](/th/platform/clusters) ตรงที่ action Delete ของหน้ารายการ BU ไม่มี client-side dependency guard

## 4. บทบาทและ Persona

การเข้าถึงเป็นแบบ permission-based ([Platform RBAC](/th/platform/rbac)) — แต่มี gotcha ที่สำคัญที่สุดของโมดูลนี้:

> **Gotcha การ reuse key: โมดูล Business Units ไม่มี permission key ของตัวเอง** route `/business-units`, `/business-units/new` และ `/business-units/:id/edit` reuse key **`cluster.read` / `cluster.create` / `cluster.update`**, รายการใน sidebar filter ด้วย `cluster.read` และ gate Delete ภายในหน้าใช้ `cluster.delete` — **ไม่มี key `business_unit.*`** ใน catalog เลย grant ใดที่เปิดโมดูล Clusters จะเปิด Business Units ไปด้วย และแยกทั้งสองออกจากกันไม่ได้ grant `cluster.update` ที่ scope ไว้กับ cluster X ครอบคลุมการแก้ไข BU ของ cluster X มุมมองฝั่ง cluster ของ gotcha เดียวกันอยู่ใน [clusters permissions](/th/platform/clusters/permissions) §2

| Surface | ชนิดของ gate | Key | Scoped? |
|---|---|---|---|
| route `/business-units` | `requiredPermission` | `cluster.read` | ไม่ |
| route `/business-units/new` | `requiredPermission` | `cluster.create` | ไม่ |
| route `/business-units/:id/edit` | `requiredPermission` | `cluster.update` | ไม่ |
| รายการ "Business Units" ใน sidebar | filter `permission` | `cluster.read` | ไม่ |
| List: ปุ่ม Add Business Unit | `<Can>` | `cluster.create` | ไม่ |
| List: action Edit ของ row | `<Can>` | `cluster.update` | ใช่ — `clusterId={row.original.cluster_id}` |
| List: action Delete ของ row | `<Can>` | `cluster.delete` | ใช่ — `clusterId={row.original.cluster_id}` |
| หน้าแก้ไข: ทุก field, ปุ่ม Reveal password, การ์ด advanced | `canEdit = isNew ? hasPermission('cluster.create') : hasPermission('cluster.update', {clusterId})` | `cluster.create` (ใหม่) / `cluster.update` (มีอยู่แล้ว) | ใช่สำหรับ BU ที่มีอยู่แล้ว — `clusterId={formData.cluster_id \|\| UNRESOLVED_CLUSTER_ID}` |
| หน้าแก้ไข: การ์ด Tenant Migrations / Tenant Seed / Interface Entitlement | `isSuperAdmin` (แยกจาก `canEdit`) | — | ไม่ |

gate แบบ scoped (`clusterId`) จะ resolve กับ **cluster แม่** ของ BU — role assignment ที่ scope ไว้กับ cluster A จะ render Edit/Delete ของ row เฉพาะบน BU ที่ `cluster_id` เป็น A เท่านั้น ขณะที่ route guard แบบ unscoped จะผ่านด้วย grant แบบ cluster-scoped ของ cluster ใดก็ได้ ไม่มี gate แบบ toggle Edit แยกต่างหากอีกต่อไป: หน้าแก้ไขคำนวณ boolean `canEdit` ตัวเดียวแล้วส่งให้ทุกส่วน รวมถึง action Add/Edit/Remove ของ card Users (เดิมไม่มี gate ระดับ action — ตอนนี้รวมเข้ากับ check ระดับหน้าเดียวกัน ผลลัพธ์แทบไม่ต่างกัน) หมายเหตุ sentinel `UNRESOLVED_CLUSTER_ID`: เมื่อ `formData.cluster_id` ว่างเปล่า (BU ที่ไม่มี cluster หรือก่อนที่ dropdown Cluster จะมีค่าตอน create) check จะถูกจงใจรักษาไว้ที่ branch แบบ scoped ของ `checkPermission` (fail closed) แทนที่จะตกไปที่ branch แบบกว้าง "cluster ใดก็ได้" อัลกอริทึมการ resolve, ข้อยกเว้น bootstrap และ bypass ของ super-admin อยู่ใน [rbac permissions](/th/platform/rbac/permissions)

## 5. โมดูลที่เกี่ยวข้อง

- [clusters](/th/platform/clusters) — ทุก BU เป็นของ cluster หนึ่ง cluster ผ่าน `cluster_id` หน้าแก้ไข cluster เปิด flow สร้าง BU โดย preselect parent ผ่าน query parameter `/business-units/new?cluster_id=<id>` และ key `cluster.*` ที่ gate โมดูลนี้ถูกอธิบายไว้จากฝั่ง cluster ใน [clusters permissions](/th/platform/clusters/permissions)
- [users](/th/platform/users) — เป็นแหล่งของบัญชีผู้ใช้ที่ถูก assign เข้า BU ผ่าน card Users สมาชิก BU ใหม่ถูกดึงจากรายชื่อผู้ใช้ของ cluster ที่เป็นแม่ และการคลิกชื่อใน card Users จะกระโดดไปหน้าแก้ไข user
- [rbac](/th/platform/rbac) — โมเดล permission เบื้องหลังทุก gate ใน §4: catalog, role, scoped assignment, bypass ของ super-admin และ (§5 ของหน้านั้น) โมเดล role-enum รุ่นเก่าที่เคย gate โมดูลนี้จนถึง 2026-06
- [report-templates](/th/platform/report-templates) — chip input `allow_business_unit` / `deny_business_unit` ที่นั่นกำหนดขอบเขตเทมเพลตรายงานด้วยค่า `code` ของ BU ที่นิยามไว้ที่นี่

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/App.tsx` — route ทั้งสามของ BU พร้อม prop `requiredPermission="cluster.*"` (authoritative สำหรับการ gate route; `SITEMAP.md` ยังแสดง role list รุ่นเก่าและ stale ในคอลัมน์ access)
- `../carmen-platform/src/components/Layout.tsx` — รายการ "Business Units" ใน sidebar filter ด้วย `cluster.read`
- `../carmen-platform/src/pages/BusinessUnitManagement.tsx` และ `businessUnitManagement/BuSummary.tsx` — หน้ารายการ: แถบสรุป Overview, filter, ส่งออก CSV, คอลัมน์ audit, Add/Edit/Delete ที่ gate ด้วย `<Can>` (ไม่มี client-side deletion guard)
- `../carmen-platform/src/pages/BusinessUnitEdit.tsx` และ `businessUnitEdit/{BusinessUnitDocument,HeroName,BusinessUnitBrandingCard,BusinessUnitUsersCard,useBusinessUnitUsers,types,shared}.ts(x)`, `sections/{CalculationSettingsSection,NumberFormatsSection,ConfigurationSection,DatabaseConnectionSection}.tsx` — หน้าแก้ไขแบบ one-document, hero, กลุ่ม field แบบ inline, เซกชันซับซ้อน และ card Users
- `../carmen-platform/src/components/{TenantMigrationCard,TenantSeedCard,InterfaceEntitlementCard}.tsx` — การ์ด advanced สาม super-admin เท่านั้น; `../carmen-platform/src/services/{tenantMigrationService,tenantSeedService,interfaceEntitlementService,currencyService}.ts` — REST client ของแต่ละอัน
- `../carmen-platform/src/utils/dbConnection.ts` — parsing/masking/serialization ของ field `db_connection` (`objectToDbFields`, `dbFieldsToObject`, `SAFE_DB_CONNECTION_KEYS`)
- `../carmen-platform/src/components/BrandingImageUpload.tsx` — control อัปโหลด logo/avatar ที่ใช้ร่วมกันบนเซกชัน Branding
- `../carmen-platform/src/services/businessUnitService.ts` — REST client (`/api-system/business-units` บวก endpoint อัปโหลด `/logo` และ `/avatar`, `revealDbPassword` และ endpoint join `/api-system/user/business-units`)

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/business-units/data-model) — เอกสารอ้างอิงเอนทิตี BU: ฟิลด์ระบุตัวตน บล็อกที่อยู่ hotel/company แบบมีโครงสร้างใหม่ ฟิลด์รูปแบบวันที่/เวลา/ตัวเลข การตั้งค่าการคำนวณ array `config[]` แบบ key/value บล็อก `db_connection` branding file token `doc_version` และ schema ของตาราง join BU-user
- [UI Screens](/th/platform/business-units/ui-screens) — ทัวร์ของหน้ารายการ (`BusinessUnitManagement`) และหน้าแก้ไขแบบ one-document (`BusinessUnitEdit`) รวมถึง hero, กลุ่ม field แบบ inline, การ์ด advanced สำหรับ super-admin และ card Users พร้อม select สำหรับ BU role และ dialog เพิ่ม user จาก cluster
