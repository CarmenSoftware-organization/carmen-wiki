# Design: Platform `report-templates/` Sub-Pages

**Date:** 2026-05-19
**Status:** Approved (user)
**Scope:** Expand the `report-templates/` module sub-pages, the FOURTH and final multi-page module in the Platform book. Adds two new sub-pages (`data-model.md`, `permissions.md`) on top of expanding the two existing stubs (`ui-screens.md`, `xml-spec.md`).

**Predecessors:**
- `.specs/platform-sub-page-template.md` — the formal template that defines all conventions. THIS SPEC IS LIGHT BECAUSE THE TEMPLATE COVERS THEM.
- `.specs/2026-05-19-platform-clusters-sub-pages-design.md` — established the `permissions.md` shape (cluster has the same role gate; report-templates reuses it).

The `report-templates/` folder currently carries **two** stub sub-pages:
- `ui-screens.md` (28 lines)
- `xml-spec.md` (25 lines)

This spec **adds two more**:
- `data-model.md` — `tb_report_template` schema view; matches the universal shape from template §2.1.
- `permissions.md` — role-gate view (same admin-tier gate as clusters); matches the shape from template §2.4.

Total deliverable: 4 sub-pages.

The provisional `xml-spec.md` shape in template §2.5 will be **refined by this round's implementation** — when the round completes, the template's §2.5 should be updated to reflect what actually worked.

---

## 1. Goals

1. **Four full sub-pages** for `report-templates/`, in English. Two new files (`data-model.md`, `permissions.md`) created; two stubs expanded (`ui-screens.md`, `xml-spec.md`).
2. **No edits to the landing** during the implementation window. Landing patch is a separate post-implementation commit if it carries `(stub — in progress)` annotations.
3. **Reuse conventions from the template spec** — this spec only documents what is module-specific.
4. **Refine `xml-spec.md` shape** by example. Once this round lands, the template spec §2.5 is updated to match.

## 2. Non-goals

- TH mirror.
- Screenshots.
- The `print-template-mapping` feature pair (also role-gated, also under `/print-template-mapping*`) — out of scope; it does not have a Platform-book module folder and is treated as a separate concern. If documentation for it is needed later, that's a separate spec.
- Any landing edits during implementation.

## 3. Sub-page shapes (module-specific only)

For frontmatter, At-a-Glance callout style, cross-link conventions, verification gates, and workflow shape, refer to `.specs/platform-sub-page-template.md`. Below are only the module-specific details.

### 3.1 `data-model.md`

Universal shape (template §2.1). Module-specific facts:

- **Entity:** `tb_report_template` only. The `tb_print_template_mapping` table belongs to the sibling print-template-mapping feature pair and is out of scope.
- Notable fields: `name`, `description`, `report_group`, `dialog` (XML payload), `content` (XML payload), `source_type` (enum), `source_name`, `source_params` (JSON `{ params: [...] }`), `allow_business_unit` / `deny_business_unit` (comma-separated BU code lists), `is_standard`, `is_active`, `builder_key`, soft-delete trio, audit columns.
- Enum: `source_type` likely has values `view` / `function` / `procedure` (verify from Prisma).
- The 38-row table size of `tb_business_unit` is unusual; `tb_report_template` is expected to be more modest. If grouping separator rows are warranted (Identity / XML payloads / Source binding / Scope / Lifecycle / Audit), apply the same pattern from business-units/data-model.
- The `source_params` JSON shape: `{ params: [{ filter, type, nullable }] }` — document the array element shape in §5 (the JSON-column section, modelled on business-units/data-model §5).
- §6 Divergences: compare Prisma against `src/types/index.ts` `ReportTemplate` and any `ReportTemplateFormData` interface.
- Cross-links to: [[business-units]] (BU codes referenced in the chip lists), [[clusters]] (sibling role-gated admin surface), sibling `[Permissions](./permissions.md)`, `[UI Screens](./ui-screens.md)`, `[XML Spec](./xml-spec.md)`.

### 3.2 `permissions.md`

Universal shape (template §2.4) — same skeleton as `clusters/permissions.md`. Module-specific facts:

- The three routes: `/report-templates`, `/report-templates/new`, `/report-templates/:id/edit` — all carry `allowedRoles={["platform_admin", "support_manager", "support_staff"]}` at `src/App.tsx` lines 114, 122, 130.
- The bootstrap exception works identically to clusters — cross-link to `[Permissions](../clusters/permissions.md) §4` for the detailed mechanic and avoid restating it in full.
- Sidebar filter — `Layout.tsx` Report Templates nav item carries the same role list.
- Within the surface — same convention as clusters: no per-button gates; pass the route guard and every action is visible.
- Cross-link to [[auth-roles]] for the role definitions and to `../clusters/permissions.md` for the canonical shape.

### 3.3 `ui-screens.md`

Universal shape (template §2.2). Module-specific facts:

- The list page (`ReportTemplateManagement`) — list with Standard/Custom and Active/Inactive facets, search, filters Sheet, Add Template, Export CSV (verify), row actions (Edit, soft-delete).
- The edit page (`ReportTemplateEdit`) is the most complex Platform admin edit page in terms of UX: a left pane (identity + source binding + BU scope + lifecycle toggles) and a right pane with three CodeMirror tabs (**Dialog XML**, **Content XML**, **Preview**). The Preview tab renders the Dialog XML as a disabled form.
- Source section detail: `source_type` select (view/function/procedure), `source_name` input, `source_params` editable table, and a **"Browse in BU"** probe dialog that calls `reportTemplateService.listDbObjects(business_unit_id)` to populate a picker.
- BU scope inputs: chip-input components for allow/deny with BU-code autocomplete (verify whether the autocomplete pulls from `businessUnitService` or a static list).
- Sticky bottom action bar with **unsaved-changes** indicator (`useUnsavedChanges` hook) — Save / Cancel / Reset behaviour.
- File upload affordance: the Content XML tab accepts `.frx`, `.xml`, `.txt` uploads (legacy FastReport `.frx` migration support).
- Dialogs (likely): Browse in BU, Soft Delete confirm. Confirm presence of any Hard Delete dialog (the service probably has no `hardDelete` method).
- localStorage keys on the list page — verify verbatim names.

### 3.4 `xml-spec.md` (refines the provisional template shape)

The template's §2.5 provisional structure is:

1. Overview
2. Format A
3. Format B
4. Editor surface
5. Validation
6. References

After implementation, revise the template (separate commit) to reflect what worked. Module-specific facts for this round:

- **Dialog XML**: root element + child structure. Per the landing, fields include `<Label>` + `<Date>` / `<Lookup>` pairs. Document the actual element catalogue from `ReportTemplateEdit.tsx`'s validation logic.
- **Content XML**: root element + child structure. Likely paragraphs / tables / images / formula cells — document what the editor accepts and what the runtime renders.
- **Editor surface**: CodeMirror — language mode (XML), folding, search, syntax highlighting, parse-error markers (line/col), file upload (Content tab accepts `.frx`/`.xml`/`.txt`).
- **Validation**: line-count display, inline parse error indicator. Document each error category the validator surfaces.
- Worked example: include a minimal but COMPLETE Dialog + Content pair so the reader can copy-paste-modify. (This addresses the stub's `[ ] Add a fully-valid example template` TODO.)
- Cross-link to `[Data Model](./data-model.md) §2.1` for the `dialog` and `content` column types.

## 4. Verification gates

Inherit template §7 in full. Run the standard grep set per file.

For `xml-spec.md` specifically, the placeholder-syntax grep (`<[A-Z][a-z]+|<[a-z-]+>`) will fire heavily because the page legitimately contains XML element names like `<Label>`, `<Date>`, `<Lookup>`, `<Dialog>`. Treat these as expected false positives — confirm each match is inside a code fence or an inline `<element>` reference, not a leftover template placeholder.

## 5. Workflow shape

Inherit template §8 in full. Subagent-driven execution: implementer → spec reviewer → code-quality reviewer → fix subagent → re-review per task. Final cross-checks task at the end. Optional landing stub-cleanup commit if annotations exist.

After the round completes: a separate small commit may revise `.specs/platform-sub-page-template.md` §2.5 to reflect the working `xml-spec.md` shape.

## 6. Deferrals

- TH mirror, screenshots — consistent with prior rounds.
- `print-template-mapping` documentation — future spec.
- `tb_report_template.source_params` validation rules — document what the SPA validator enforces, but a separate effort can codify the full backend-side validation.

## 7. Out of scope

- Edits to `report-templates.md` landing during implementation.
- The `print-template-mapping` feature pair and its routes.
- The runtime executor (the backend service that consumes `dialog` + `content` + `source_*` to produce output) — only the admin product surface is documented here.

## 8. Open questions

None at design time. The xml-spec template refinement is an implementation-time discovery item.
