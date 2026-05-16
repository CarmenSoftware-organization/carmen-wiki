---
title: Email Configuration
description: SMTP / sender / template configuration for outbound system email — workflow notifications, scheduled report delivery, password reset.
published: true
date: 2026-05-16T15:00:00.000Z
tags: system-config, email, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Email Configuration

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/system-admin/config-email`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

Email Configuration holds the SMTP server, port, TLS, authentication credentials, default-from address, and per-channel template overrides for every outbound email Carmen sends. The notification module ([[reporting-audit/notification]]) and the cron service read this config when dispatching workflow notifications, scheduled report deliveries, password resets, and audit alerts. Sysadmin curates; rotation of SMTP credentials is logged via [[reporting-audit/activity]].

## 2. Related Modules

- [[reporting-audit/notification]] — what gets sent through this config
- [[reporting-audit/schedule]] — scheduled emails depend on it
- [[system-config/application-config]] — system-wide settings

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/system-admin/config-email/` — frontend page
