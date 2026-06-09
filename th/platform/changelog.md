---
title: บันทึกการเปลี่ยนแปลง (Changelog)
description: บันทึกการเปลี่ยนแปลงของแพลตฟอร์มแบบมีเวอร์ชัน — ดึงข้อมูลจาก JSON, เปิดเป็นหน้า public /changelog เข้าถึงผ่าน version badge ในแถบด้านข้างและหน้า landing page
published: true
date: 2026-06-09T00:00:00.000Z
tags: platform, changelog, versioning, carmen-software
editor: markdown
dateCreated: 2026-06-09T00:00:00.000Z
---

# บันทึกการเปลี่ยนแปลง (Changelog)

> **สรุปภาพรวม**
> **แหล่งข้อมูลหลัก:** `src/data/changelog.json` &nbsp;·&nbsp; **หน้าสาธารณะ:** `/changelog` (ไม่ต้องยืนยันตัวตน) &nbsp;·&nbsp; **จุดเข้าถึง:** `VersionBadge` ในส่วนท้ายของแถบด้านข้าง + landing page &nbsp;·&nbsp; **ไฟล์ที่สร้างอัตโนมัติ:** `CHANGELOG.md` (รูปแบบ Keep a Changelog) &nbsp;·&nbsp; **การปล่อยเวอร์ชัน:** `bun run build:bump`.

## 1. คืออะไร และใครใช้

Changelog คือบันทึกที่มีเวอร์ชันและเปิดเป็น **public** สำหรับสิ่งที่เผยแพร่ในผลิตภัณฑ์ Carmen Platform admin ไฟล์ JSON เดียวคือ (`src/data/changelog.json`) คือแหล่งข้อมูลหลัก โดย React app นำเข้าแบบ static (ไม่มีการดึงข้อมูลขณะ runtime) เพื่อแสดงหน้า `/changelog` และสคริปต์ Node จะสร้าง `CHANGELOG.md` ที่อ่านได้ (รูปแบบ Keep a Changelog) ไว้ที่รูทของ repo ใหม่ทุกครั้ง `CHANGELOG.md` **ห้ามแก้ไขด้วยมือ** — ให้แก้ไขที่ JSON เท่านั้น

**ผู้เขียน:** นักพัฒนา (เพิ่มรายการใต้บัฟเฟอร์ `unreleased` ระหว่างการทำงาน) **ผู้อ่าน:** ทุกคน — หน้านี้เปิดสาธารณะ

## 2. วิธีเก็บข้อมูล

JSON มีบัฟเฟอร์ `unreleased` พร้อมกับ `versions` ที่ออกแล้ว (เรียงล่าสุดก่อน) หมวดหมู่ที่ว่างเปล่าจะถูกละไว้เพื่อให้เขียนง่ายขึ้น:

```
{
  "unreleased": { "Added": ["A feature not yet released"] },
  "versions": [
    {
      "version": "0.1.0",
      "date": "2026-06-01",
      "changes": {
        "Added": ["Public changelog page with version badge"],
        "Fixed": ["Audit dates read from the nested audit object in lists"]
      }
    }
  ]
}
```

หมวดหมู่ใช้ชุด Keep a Changelog แบบเต็ม แสดงตามลำดับนี้: **Added, Changed, Deprecated, Removed, Fixed, Security** รายการการเปลี่ยนแปลงเป็น string ธรรมดา (ไม่มี metadata รายการย่อย) วันที่เขียนในรูปแบบ `YYYY-MM-DD` และแสดง **ตรงตามที่เขียน** — หน้านี้จงใจหลีกเลี่ยง `new Date(value)` เพราะการแปลง string วันที่เป็น UTC midnight จะทำให้วันที่ขยับไปก่อนหน้า 1 วันสำหรับผู้ใช้ที่อยู่ทางตะวันตกของ UTC

## 3. ปรากฏที่ไหนบ้าง

| พื้นที่ | พฤติกรรม |
|---|---|
| หน้า `/changelog` | เส้นทางสาธารณะ; แสดงบล็อก `unreleased` (ถ้ามีข้อมูล) ตามด้วยแต่ละเวอร์ชันที่ออกแล้วโดยเรียงล่าสุดก่อน |
| ส่วนท้ายของแถบด้านข้าง | `VersionBadge` แสดง `v{latest}` ลิงก์ไปที่ `/changelog` |
| Landing page | `VersionBadge` อยู่ถัดจากวันที่ build |

เวอร์ชันปัจจุบันสำหรับ badge ดึงมาจาก `versions[0].version` (ค่าสำรอง `0.0.0`) `/changelog` ถูกลงทะเบียนเป็น **public path ใน auth guard** ดังนั้นจึงแสดงผลได้สำหรับผู้เยี่ยมชมที่ยังไม่ได้ลงชื่อเข้าใช้

## 4. สำหรับนักพัฒนา

- **เพิ่มการเปลี่ยนแปลง:** แก้ไข `src/data/changelog.json` โดยเพิ่ม string ในหมวดหมู่ที่เหมาะสมภายใน `unreleased` ห้ามแตะ `CHANGELOG.md`
- **ปล่อยเวอร์ชัน:** `bun run build:bump [patch|minor|major]` (ค่าเริ่มต้น `patch`) จะเพิ่ม semver, เลื่อนบัฟเฟอร์ `unreleased` ไปเป็น entry `versions[0]` ใหม่พร้อมวันที่, รีเซ็ต `unreleased` เป็น `{}`, ซิงค์ `package.json`, สร้าง `CHANGELOG.md` ใหม่ แล้ว build
- **หมายเหตุ public-path:** หากการ refactor ของ route-guard เปลี่ยนวิธีลงรายการ public paths, `/changelog` ต้องยังคงอยู่ใน allowlist มิฉะนั้นหน้าจะ redirect ไปที่หน้าลงชื่อเข้าใช้
