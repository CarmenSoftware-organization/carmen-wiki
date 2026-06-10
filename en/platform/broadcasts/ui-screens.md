---
title: Broadcasts — UI Screens
description: The single BroadcastCompose screen — target tabs, UserMultiSelect and BU select, title/message counters, type presets with custom input, send-now vs schedule, and the per-mode confirmation dialog.
published: true
date: 2026-06-10T13:15:00.000Z
tags: book/platform, broadcasts, ui
editor: markdown
dateCreated: 2026-06-10T13:15:00.000Z
---

# Broadcasts — UI Screens

> **At a Glance**
> **Screens:** `BroadcastCompose` (`/broadcasts/new`) — the module's only screen; no list/edit routes &nbsp;·&nbsp; **Form:** one Compose card — Target tabs · conditional recipient picker · Title (≤200) · Message (≤2000) · Type presets · Send time tabs &nbsp;·&nbsp; **Dialogs:** one ConfirmDialog, title and styling vary by target mode &nbsp;·&nbsp; **Shortcuts:** Ctrl/Cmd+S send · Escape reset &nbsp;·&nbsp; **Persisted UI state:** none

## 1. Overview

Broadcasts is a one-screen module: `/broadcasts/new` → `BroadcastCompose`, a single Compose card under a Megaphone-icon header ("Send Broadcast" / "Push a notification to all users, specific users, or a business unit."). There is no Management list, no view/edit toggle, no record to come back to — the deliberate inverse of every other Platform module. Because nothing is loaded (beyond the BU options), the page has no skeleton state and persists no `localStorage` UI state.

Standard furniture still applies: `useUnsavedChanges` arms a navigation guard as soon as any field deviates from its default (including picked recipients), Ctrl/Cmd+S triggers Send and Escape triggers Reset (both suppressed while a send is in flight or the confirm dialog is open), errors surface as red field messages plus a toast, and a dev-only Debug Sheet (amber floating button, `NODE_ENV === 'development'`) shows the last API response with a Copy JSON button.

## 2. The Compose form

Fields top to bottom; everything except the two tab strips is plain controlled inputs.

### 2.1 Target tabs

A `Tabs` strip with three options — **All users** (Globe icon, `system_all`, the default), **Specific users** (Users icon, `system_users`), **Business Unit** (Building2 icon, `bu`). Switching tabs swaps the conditional section below it (recipient picker vs BU select) but **does not clear state already entered** — see the stale-recipients edge case in [Permissions](./permissions.md) §4.

The two system tabs render only when the session holds `broadcast.send` (`canSendSystem`), with an effect forcing `bu` mode otherwise. Since the route itself requires the same key, this in-component gating is unreachable defensive code today — every user who can open the page sees all three tabs.

### 2.2 Recipients (`system_users` only)

A `UserMultiSelect` — a badge-input combo box backed by the Users API:

- Typing (400 ms debounce, dropdown opens on focus — the debounce also fires an empty-query search on open, so the first 20 users typically populate before any keystroke) searches `userService.getAll({ page: 1, perpage: 20, search })` — top 20 matches by name or email, each rendered as name over muted email. Display name is `firstname middlename lastname`, falling back to `name`, `email`, then the raw id.
- Clicking a result adds a removable badge (already-selected rows are disabled and tagged "Selected"); Backspace with an empty query removes the last badge; Escape closes the dropdown. Empty states: "Type to search users" / `No users match "<query>"`; search failures render the parsed API error inline in the dropdown.
- Validation: at least one recipient ("Pick at least one recipient"), enforced pre-submit and cleared as soon as one is added.

### 2.3 Business Unit (`bu` only)

A native select loaded once on mount via `businessUnitService.getAll({ page: 1, perpage: 100 })` — note the cap: only the **first 100 BUs** are offered. Options are filtered to active BUs (`is_active !== false`) and rendered as `Name (CODE)`; the submitted value is the **code**. While loading, the select is disabled with placeholder "Loading business units…"; a load failure renders the error message with an inline **Retry** button that re-fires the fetch. Validation: required ("Choose a business unit").

### 2.4 Title and Message

| Field | Control | Limit | Notes |
|---|---|---|---|
| Title | Text input, placeholder "Scheduled maintenance" | 200 | Live `N/200` counter; input hard-truncates at the limit (`slice(0, 200)`), so the max-length error is normally unreachable by typing. Required ("Title is required") |
| Message | Textarea, 6 rows, placeholder "The system will be unavailable from 02:00 to 03:00 UTC." | 2000 | Live `N/2000` counter, same hard truncation. Required ("Message is required") |

Both are trimmed before validation and submission.

### 2.5 Type

A native select with five presets — Info (default), Warning, Critical, Maintenance, **Other…**. The first four resolve client-side to `SYS_<PRESET>` (system modes) or `BU_<PRESET>` (BU mode) at submit time. Choosing Other… reveals a custom-type input (placeholder `CUSTOM_TYPE`) that **uppercases as you type** and submits verbatim with no prefix. Validation (Other… only): required, ≤50 chars, must match `[A-Z0-9_]+` ("Use uppercase letters, digits, and underscores only").

### 2.6 Send time

A second `Tabs` strip — **Send immediately** (Send icon, default) vs **Schedule for later** (Calendar icon). Schedule mode reveals a native `datetime-local` input; validation requires a value ("Pick a date and time"), a parseable value ("Invalid date/time"), and a **future** instant ("Scheduled time must be in the future" — checked against `Date.now()` at validation time). The value is converted to a UTC ISO string (`new Date(v).toISOString()`) in the payload.

## 3. Send flow

### 3.1 Validation → confirmation

The **Send** button (footer, `<Can permission="broadcast.send">`; label flips to **Schedule** in schedule mode, spinner while sending) first runs validation — failures mark the fields and toast "Please fix the highlighted fields". On success a `ConfirmDialog` opens:

| Target mode | Dialog title | Confirm button |
|---|---|---|
| `system_all` | **Send to ALL users?** | **destructive** (red) styling |
| `system_users` | Send to N user(s)? | default |
| `bu` | Send to {BU name}? (falls back to the code) | default |

The description leads with timing — "Will be delivered immediately." or "Scheduled for `<local datetime>`." — then the audience: the title being sent (`system_all`), the first five recipient names plus "and N more" (`system_users`), or "Business unit: Name (CODE)" (`bu`). The confirm label is **Send** or **Schedule** to match the mode.

### 3.2 Submit, success, failure

Confirming posts `BroadcastBuPayload` to `/api/notifications/broadcasts/bu` in BU mode, otherwise `BroadcastSystemPayload` to `.../broadcasts/system` (with `userIds` when recipients were picked — see [Data Model](./data-model.md) §5 for the payload shapes). On success: toast "Broadcast sent" or "Broadcast scheduled for `<local datetime>`", the **entire form resets** to defaults, and the raw response is retained for the Debug Sheet. On failure: `parseApiError` toasts the message and maps any field errors onto the form; the dialog closes either way. There is no redirect — the screen is ready for the next broadcast, and the one just sent is not visible anywhere in this SPA.

### 3.3 Reset, shortcuts, unsaved-changes guard

**Reset** (outline button beside Send, also Escape) clears the form, recipients, and field errors without confirmation — the confirm-before-discard protection exists only on *navigation*, via `useUnsavedChanges`, which arms when any field differs from its default. Ctrl/Cmd+S is equivalent to clicking Send (validation first, then the dialog).

## 4. References

- `../carmen-platform/src/pages/BroadcastCompose.tsx` — the whole screen: constants (`TITLE_MAX`, `MESSAGE_MAX`, `TYPE_CUSTOM_RE`), `resolveType`, payload builders, `validate`, confirm title/description, Debug Sheet.
- `../carmen-platform/src/components/UserMultiSelect.tsx` — debounce, page size, display-name fallback, badge/keyboard interactions.
- `../carmen-platform/src/services/broadcastService.ts` — `sendSystem` / `sendBu`.
- `../carmen-platform/src/components/KeyboardShortcuts.tsx`, `src/hooks/useUnsavedChanges.ts` — shortcuts and the navigation guard.
- `../carmen-platform/src/App.tsx` (route), `src/components/Layout.tsx` ("Send Broadcast", Content group).

**Cross-links:** [Broadcasts landing](/en/platform/broadcasts) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [Permissions](./permissions.md)
