---
title: หน่วยธุรกิจ (Business Units)
description: เอนทิตีต่อ property/ต่อโรงแรม พร้อมฟอร์มหลายเซกชันที่ครอบคลุมข้อมูลระบุตัวตน ข้อมูลติดต่อ ภาษี รูปแบบ การคำนวณ การตั้งค่า การเชื่อมต่อฐานข้อมูล branding และรายชื่อผู้ใช้ที่ผูกกับ BU
published: true
date: 2026-06-10T16:30:00.000Z
tags: platform/business-units, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# หน่วยธุรกิจ (Business Units)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** หน้าจอ authoring ที่ใช้สร้างและตั้งค่าเอนทิตีปฏิบัติการที่ Carmen เรียกว่า **business unit** (BU) — หนึ่งแถวต่อหนึ่งโรงแรม/property/นิติบุคคล พร้อมฟิลด์ในฟอร์มที่ขับเคลื่อนทั้งบริบทของ tenant ใน inventory app และการมอบหมาย role ของผู้ใช้ในแพลตฟอร์ม &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ที่ทำงานกับ Platform admin SPA; การเข้าถึงของ operator ถูก gate ด้วย **permission key `cluster.*` ที่ reuse มา** ([rbac](/th/platform/rbac)) — ไม่มี key `business_unit.*` &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `business_unit` (ฟิลด์ระบุตัวตน `code`, `name`, `alias_name`, `is_hq`, `is_active`, `max_license_users`; บล็อกข้อมูลติดต่อสำหรับ hotel/company; ฟิลด์ภาษี; ฟิลด์รูปแบบวันที่/เวลา/ตัวเลข; `calculation_method`, `default_currency_id`; `db_connection`; `config[]` แถว key/value; branding `logo_file_token`/`avatar_file_token`) บวกกับตาราง join BU-to-user ที่ถือ `role` ระดับ BU เป็น `admin` หรือ `user` &nbsp;·&nbsp; **หน้าย่อย:** 2

## 1. ภาพรวม

Business unit คือ tenant ปฏิบัติการของ Carmen platform: หนึ่ง BU คือหนึ่งโรงแรม หนึ่ง property หรือหนึ่งนิติบุคคลที่ซื้อ รับ นับ และเบิกใช้ inventory หน้ารายการที่ `/business-units` (`BusinessUnitManagement.tsx`) เป็นแคตตาล็อกแบบ server-paginated ค้นหาได้ มี facet สำหรับ Active/Inactive และรายการที่ถูก soft-delete พร้อมส่งออก CSV ได้ หน้าแก้ไขที่ `/business-units/:id/edit` และ `/business-units/new` (`BusinessUnitEdit.tsx`) แสดงฟอร์ม 9 ส่วนเป็นการ์ดในกริดสองคอลัมน์ — Basic Information, Hotel Information, Company Information, Tax Information, Date/Time Formats, Number Formats, Calculation Settings, Configuration และ Database Connection — ตามด้วย card Branding ที่แยกออกมา (อัปโหลด logo + avatar) และ card Users ที่แสดงรายชื่อผู้ที่ถูก assign เข้า BU card Branding และ Users จะปรากฏหลังจาก BU ถูกสร้างแล้วเท่านั้น การสร้าง BU เป็น flow แบบ "บันทึกก่อนแล้วค่อย assign"

แต่ละ BU เป็นของ **cluster** หนึ่ง cluster เท่านั้น (foreign key `cluster_id` เลือกจาก dropdown) flow "สร้าง BU" เริ่มได้จากหน้ารายการ BU หรือจากหน้าแก้ไข cluster ซึ่ง navigate ไปที่ `/business-units/new?cluster_id=<id>` เพื่อ preselect parent ให้ นอกจากฟิลด์ระบุตัวตนและข้อมูลติดต่อ BU ยังเก็บค่า locale ที่ inventory runtime อ่านจะใช้ — `date_format`, `time_format`, `timezone`, ตัว format แบบ JSON `amount_format`/`quantity_format`/`recipe_format` ที่ default เป็น `th-TH`, `calculation_method` และ `default_currency_id` — บวกกับ array `config[]` ที่เป็นแถว key/value แบบ free-form และบล็อก JSON `db_connection` ที่ชี้ BU ไปยัง schema ของ tenant ของตน รายละเอียดต่อฟิลด์และพฤติกรรมของหน้าจออยู่ในหน้าย่อย — หน้า landing นี้เพียงปูทาง

## 2. บริบททางธุรกิจ

ในธุรกิจโรงแรม หน่วยที่เล็กที่สุดที่มีบัญชีของตัวเอง มีสกุลเงินของตัวเอง และมี supply chain ระดับท้องถิ่นของตัวเอง คือ property — โรงแรมเดี่ยวภายในกลุ่มแบรนด์ Carmen จึงโมเดลสิ่งนี้เป็น business unit ทุก inventory transaction (GRN, store requisition, physical count, spot check) อยู่ในขอบเขตของ BU เดียว ทุกรายงานรันกับ schema ของ BU เดียว และผู้ใช้ทุกคนได้รับสิทธิ์เข้าถึง BU หนึ่งหรือมากกว่าหนึ่ง พร้อม role ที่ใช้ภายในแต่ละ BU แถว `business_unit` จึงถือมากกว่าข้อมูลระบุตัวตน มันถือค่า locale ที่ inventory UI แสดง (รูปแบบวันที่และตัวเลข, timezone, default currency) ถือ knob ของการคำนวณต้นทุน (`calculation_method`) ที่ valuation engine ใช้อ้างอิง ถือการเชื่อมต่อฐานข้อมูลของ tenant ที่แพลตฟอร์มใช้ route query ไปยัง schema ของ property นั้น และถือเพดานสิทธิ์การใช้งาน (`max_license_users`) ที่จำกัดว่าผู้ใช้กี่คนจะล็อกอินได้

เนื่องจาก BU ยังเป็นจุดที่ผู้ใช้กลายเป็นมีความหมายในเชิงปฏิบัติการ หน้าแก้ไขจึงทำหน้าที่เป็น workbench สำหรับ assign ผู้ใช้ด้วย card Users แสดงทุกคนที่มีสิทธิ์เข้าถึง BU นี้ พร้อม **BU role** (`admin` หรือ `user`) ที่ orthogonal กับ RBAC assignment ระดับแพลตฟอร์มบนบัญชีผู้ใช้เอง ([rbac](/th/platform/rbac)) สมาชิก BU ใหม่ถูกเลือกจาก cluster ที่เป็นแม่ของ BU นั้น — ผู้ใช้ต้องอยู่ใน cluster ก่อนถึงจะถูกเพิ่มเข้า BU ภายใน cluster ได้ ซึ่งช่วยรักษาขอบเขตของ tenant ให้สะอาด การเข้าถึง route ของ BU เป็นแบบ permission-gated แต่มีจุดพลิก: โมดูลนี้ยืม key `cluster.read` / `cluster.create` / `cluster.update` มาใช้แทนที่จะนิยาม key ของตัวเอง — ดู §4

## 3. แนวคิดสำคัญ

- **Business unit (BU)**: หนึ่งแถวใน `business_unit` ที่แทนหนึ่งโรงแรม/property/นิติบุคคล ทุก inventory transaction เป็นของ BU เดียว ทุกรายงานรันกับ BU เดียว
- **Cluster membership**: ทุก BU มี `cluster_id` ที่ไม่ nullable เลือกจาก dropdown ของ cluster หน้าแก้ไข cluster สามารถเปิด flow สร้าง BU โดย preselect `cluster_id` ผ่าน query parameter `/business-units/new?cluster_id=<id>`
- **HQ flag (`is_hq`)**: ระบุว่า BU นี้เป็นสำนักงานใหญ่ภายใน cluster ของตน — Boolean ค่าเดียวที่แสดงคู่กับ flag Active ใน Basic Information ความหมายขึ้นอยู่กับโมดูลที่ใช้ค่านี้
- **Active flag (`is_active`)**: สลับว่า BU เปิดใช้งานเชิงปฏิบัติการหรือไม่ BU ที่ inactive ยังแก้ไขได้ในหน้า admin แต่จะถูกกรองออกจากการเลือกตอน runtime ปกติ หน้ารายการแสดง Active/Inactive เป็น chip กรอง
- **Max licensed users (`max_license_users`)**: integer ที่ใส่หรือไม่ใส่ก็ได้ เพื่อจำกัดจำนวนผู้ใช้ที่ assign เข้า BU ได้ ว่าง = ไม่จำกัด
- **Hotel vs. Company information**: บล็อกข้อมูลติดต่อสองบล็อกคู่ขนาน (`hotel_*` และ `company_*` — name, telephone, email, address, ZIP) เพราะตัวตนเชิงปฏิบัติการของ property (hotel) มักต่างจากนิติบุคคลที่ออกใบแจ้งหนี้ (company)
- **Tax information**: `tax_no` และ `branch_no` เก็บเลขประจำตัวผู้เสียภาษีของไทยและรหัสสาขาที่ใช้บนเอกสารพิมพ์
- **Date/Time formats**: `date_format`, `date_time_format`, `time_format`, `long_time_format`, `short_time_format` และ `timezone` ตั้งค่าว่า inventory UI จะ render timestamp ของ BU นี้อย่างไร
- **Number formats**: ตัว format แบบ JSON สามชุด — `amount_format`, `quantity_format`, `recipe_format` — บวกกับ `perpage_format` JSON ที่ขับเคลื่อนค่า default ของ pagination แต่ละ formatter default เป็น `{"locales":"th-TH","minimumIntegerDigits":2}`
- **Calculation settings**: `calculation_method` (วิธีคำนวณต้นทุนของ BU เช่น FIFO/Weighted Average — ใช้โดย inventory valuation engine) และ `default_currency_id` (foreign key ไปยังตารางสกุลเงิน โดย code/name/symbol/decimals ที่ resolve แล้วจะแสดงข้าง ๆ ในโหมดอ่าน)
- **Configuration array (`config[]`)**: รายการแบบมีลำดับของแถว `{ key, value }` แบบ free-form ที่เก็บเป็น JSON array บน BU ใช้โดย inventory app สำหรับ feature toggle ระดับ BU และการตั้งค่า integration หน้า admin ไม่บังคับ schema
- **Database connection (`db_connection`)**: บล็อก JSON ที่เก็บบน BU ที่บอกแพลตฟอร์มว่า transaction ของ BU นี้อยู่ที่ database/schema ใด render เป็นบล็อก `<pre>` แบบ pretty-printed หน้า admin validate แค่ในระดับ JSON เท่านั้น
- **Branding (logo + avatar)**: แต่ละ BU มี **logo** สี่เหลี่ยมผืนผ้าและ **avatar** สี่เหลี่ยมจัตุรัส เก็บใน Prisma เป็น file token (`logo_file_token`, `avatar_file_token`) และ API คืนค่าเป็น presigned object ฝังในตัว (`logo: { url, expires_at }`, `avatar: { url, expires_at }`) การอัปโหลดทำบน card Branding ของหน้าแก้ไขผ่าน multipart endpoint เฉพาะ ส่วนหน้ารายการแสดง thumbnail ของ logo (fallback เป็น avatar)
- **คอลัมน์ audit**: หน้ารายการแสดงคอลัมน์ Created และ Updated (timestamp พร้อมชื่อผู้กระทำ) SPA จะ flatten object `audit` แบบ nested จาก API response (`audit.created.{at,name}`, `audit.updated.{at,name}`) สำหรับคอลัมน์วันที่ โดยยอมรับ shape แบบ flat รุ่นเก่าด้วย ซึ่งชนะเมื่อมีค่า (`item.created_at ?? item.audit?.created?.at`) เซลล์ Updated จะถูกละเมื่อ `updated_at` เท่ากับ `created_at`
- **BU role (`admin` vs. `user`)**: role ที่ผูกกับการ assign user-BU แต่ละครั้ง เก็บบนแถว join ของ BU-user คู่กับ `is_active` และ `is_default` ค่าคงที่ `BU_ROLES` ใน `BusinessUnitEdit.tsx` กำหนดสองค่าพอดี role นี้ **orthogonal** กับ permission assignment ของ Platform RBAC บนบัญชีผู้ใช้ BU role ควบคุมพฤติกรรมของผู้ใช้ใน inventory app สำหรับ BU นั้น ไม่ใช่การเข้าถึง route ของ admin
- **Pattern เพิ่ม user จาก cluster**: สมาชิก BU ใหม่ถูกเลือกจากรายชื่อผู้ใช้ของ cluster ที่เป็นแม่ (`clusterUsers`) — ผู้ใช้ต้องเป็นสมาชิก cluster ก่อนถึงจะถูกเพิ่มเข้า BU ภายใน cluster ได้
- **Soft delete**: BU ถูก soft-delete ผ่าน `deleted_at` / `deleted_by_name` หน้ารายการมี toggle filter "Show soft-deleted business units" ที่ทาบ badge แดง `Deleted` และคอลัมน์ "Deleted By" เพิ่มเพื่อ audit

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
| หน้าแก้ไข: toggle Edit | `<Can>` | `cluster.update` | ใช่ — `clusterId={formData.cluster_id}` |

gate แบบ scoped (`clusterId`) จะ resolve กับ **cluster แม่** ของ BU — role assignment ที่ scope ไว้กับ cluster A จะ render Edit/Delete ของ row และ toggle Edit เฉพาะบน BU ที่ `cluster_id` เป็น A เท่านั้น ขณะที่ route guard แบบ unscoped จะผ่านด้วย grant แบบ cluster-scoped ของ cluster ใดก็ได้ ส่วน action ของ card Users (Add User, เปลี่ยน role, ลบ) ไม่มี gate `<Can>` ของตัวเอง — เข้าถึงหน้าแก้ไขได้ก็เห็นพวกมันแล้ว การบังคับใช้ฝั่ง backend จึงเป็นขอบเขตเดียวของ mutation เหล่านั้น ปุ่ม Save ของฟอร์มแก้ไขไม่ถูก gate แยกต่างหาก — ถ้าไม่มี toggle Edit ที่ gate ด้วย `<Can>` ฟอร์มจะไม่มีวันออกจากโหมด view อัลกอริทึมการ resolve, ข้อยกเว้น bootstrap และ bypass ของ super-admin อยู่ใน [rbac permissions](/th/platform/rbac/permissions)

## 5. โมดูลที่เกี่ยวข้อง

- [clusters](/th/platform/clusters) — ทุก BU เป็นของ cluster หนึ่ง cluster ผ่าน `cluster_id` หน้าแก้ไข cluster เปิด flow สร้าง BU โดย preselect parent ผ่าน query parameter `/business-units/new?cluster_id=<id>` และ key `cluster.*` ที่ gate โมดูลนี้ถูกอธิบายไว้จากฝั่ง cluster ใน [clusters permissions](/th/platform/clusters/permissions)
- [users](/th/platform/users) — เป็นแหล่งของบัญชีผู้ใช้ที่ถูก assign เข้า BU ผ่าน card Users สมาชิก BU ใหม่ถูกดึงจากรายชื่อผู้ใช้ของ cluster ที่เป็นแม่ และการคลิกชื่อใน card Users จะกระโดดไปหน้าแก้ไข user
- [rbac](/th/platform/rbac) — โมเดล permission เบื้องหลังทุก gate ใน §4: catalog, role, scoped assignment, bypass ของ super-admin และ (§5 ของหน้านั้น) โมเดล role-enum รุ่นเก่าที่เคย gate โมดูลนี้จนถึง 2026-06
- [report-templates](/th/platform/report-templates) — chip input `allow_business_unit` / `deny_business_unit` ที่นั่นกำหนดขอบเขตเทมเพลตรายงานด้วยค่า `code` ของ BU ที่นิยามไว้ที่นี่

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/App.tsx` — route ทั้งสามของ BU พร้อม prop `requiredPermission="cluster.*"` (authoritative สำหรับการ gate route; `SITEMAP.md` ยังแสดง role list รุ่นเก่าและ stale ในคอลัมน์ access)
- `../carmen-platform/src/components/Layout.tsx` — รายการ "Business Units" ใน sidebar filter ด้วย `cluster.read`
- `../carmen-platform/src/pages/BusinessUnitManagement.tsx` — หน้ารายการ: thumbnail ของ logo, filter, ส่งออก CSV, คอลัมน์ audit, Add/Edit/Delete ที่ gate ด้วย `<Can>`
- `../carmen-platform/src/pages/BusinessUnitEdit.tsx` — หน้า create/view/edit: ฟอร์ม 9 เซกชัน, card Branding, card Users, toggle Edit ที่ gate ด้วย `<Can>`
- `../carmen-platform/src/components/BrandingImageUpload.tsx` — control อัปโหลด logo/avatar ที่ใช้ร่วมกันบน card Branding
- `../carmen-platform/src/services/businessUnitService.ts` — REST client (`/api-system/business-units` บวก endpoint อัปโหลด `/logo` และ `/avatar` และ endpoint join `/api-system/user/business-units`)

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/business-units/data-model) — เอกสารอ้างอิงเอนทิตี BU (stub — ยังไม่สมบูรณ์): ฟิลด์ระบุตัวตน บล็อกข้อมูลติดต่อของ hotel/company ฟิลด์รูปแบบวันที่/เวลา/ตัวเลข การตั้งค่าการคำนวณ array `config[]` แบบ key/value บล็อก JSON `db_connection` branding file token และ schema ของตาราง join BU-user
- [UI Screens](/th/platform/business-units/ui-screens) — ทัวร์ของหน้ารายการ (`BusinessUnitManagement`) และหน้าแก้ไข (`BusinessUnitEdit`) ทุกเซกชันฟอร์ม (stub — ยังไม่สมบูรณ์) บวกกับ card Branding และ card Users พร้อม select สำหรับ BU role และ dialog เพิ่ม user จาก cluster
