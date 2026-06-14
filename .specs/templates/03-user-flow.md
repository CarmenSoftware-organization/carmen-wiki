---
title: <Module> — User Flow
description: Document lifecycle, state transitions, and persona-specific paths for <module>.
published: true
date: <ISO 8601 timestamp>
tags: <module-slug>, user-flow, inventory, carmen-software
editor: markdown
dateCreated: <ISO 8601 timestamp>
---

# <Module> — User Flow

## 1. Overview
<Scope: which personas covered, which document type(s).>

## 2. Document Lifecycle
<State machine — global view, not split by persona. Table form:>

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |

## 3. Flows by Persona

### 3.1 <Persona A>
**Role in this module:** <one-line summary of their job here>
**Entry point:** <where they start — which screen, which trigger>
**Primary flow (happy path):**
1. <step>
2. <step>

**Decision branches:**
- If <condition> → <alternate path or hand-off>

**Exit point:** <end state, hand-off to which other persona, or terminal>

### 3.2 <Persona B>
<Same structure.>

<Repeat per persona relevant to this module. Personas should match the roles listed in the module's index.md Section 4.>

## 4. Cross-Persona Handoffs
<Key handoff moments — e.g. Requester → Approver → Purchaser → Receiver. Show each handoff as a row with: from persona, trigger, to persona, what state the document is in at handoff.>

## 5. References
- `../carmen/docs/<source-folder>/` — specific files describing flow/UX.
- Frontend screens: `../carmen-inventory-frontend-react/routes/<route>/` (if relevant).
