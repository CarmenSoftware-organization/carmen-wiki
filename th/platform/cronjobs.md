---
title: งานตามกำหนดเวลา (Cronjobs)
description: CRUD over scheduled backend jobs and their cron expressions, gated by cronjob.read/manage.
published: true
date: '2026-09-05T18:14:07.000Z'
tags: book/platform, cronjobs
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# งานตามกำหนดเวลา (Cronjobs)

## 1. At a Glance

- CronJobManagement (list) and CronJobEdit (create/edit) with CronScheduleField for cron-expression input
- cronjob.read gates the nav/list; cronjob.manage gates create/edit/delete
- feature key cronjobs

## 2. References

- ../carmen-platform/src/pages/CronJobManagement.tsx
- ../carmen-platform/src/pages/CronJobEdit.tsx
- ../carmen-platform/src/pages/cronjobs/
- ../carmen-platform/src/services/cronjobService.ts

## 3. TODO

- [ ] Fill from source in Task 27
