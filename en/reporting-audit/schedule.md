---
title: Report Schedule
description: Cron-style schedule for recurring report generation — emails / archives the output to configured recipients without manual run.
published: true
date: 2026-05-16T15:00:00.000Z
tags: reporting-audit, schedule, automation, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Report Schedule

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/report/schedules`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

Report Schedule defines when each report from [[reporting-audit/report]] auto-runs (daily 06:00, weekly Monday, monthly 1st, etc.), the parameter set used, and the delivery target (email, sFTP, archived to [[reporting-audit/attachment]]). The cron service (`micro-cronjobs`) reads this table and dispatches the run; outputs are written to [[reporting-audit/history]] for traceability.

## 2. Related Modules

- [[reporting-audit/report]] — the report definitions this schedules
- [[reporting-audit/history]] — generated outputs
- [[reporting-audit/notification]] — delivery channels

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/report/schedules/` — frontend page
- `../micro-cronjobs/` — Go microservice that fires scheduled runs
