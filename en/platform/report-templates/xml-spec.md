---
title: Report Template — XML Spec
description: Dialog XML element catalogue (Label/Date/Lookup pairing, source_params binding), Content XML storage, editor surface (CodeMirror config, upload accept lists), validation categories, and a worked example pair.
published: true
date: '2026-05-19T18:30:00.000Z'
tags: book/platform, report-templates, xml
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Report Template — XML Spec

> **At a Glance**
> **Two payloads:** Dialog XML (parameter form) &nbsp;·&nbsp; Content XML (report output) &nbsp;·&nbsp; **Storage:** both columns are `String @db.Text` on `tb_report_template` (see [Data Model §5.1–5.2](./data-model.md)) &nbsp;·&nbsp; **Editor:** CodeMirror 6 (XML mode, folding, search, parse-error markers, line count) &nbsp;·&nbsp; **Dialog uploads:** `.xml`, `.txt` only &nbsp;·&nbsp; **Content uploads:** `.frx`, `.xml`, `.txt` (legacy FastReport migration) &nbsp;·&nbsp; **Validation:** browser `DOMParser` — inline parse error with line/column markers &nbsp;·&nbsp; **Preview:** Dialog tab only — Content XML has no SPA preview renderer &nbsp;·&nbsp; **Worked example:** §6 contains a minimal complete pair

## 1. Overview

Every row in `tb_report_template` carries two XML payload columns. The `dialog` column (`String @db.Text`, non-nullable) holds the XML the report runtime renders as the parameter input form shown to users before a report runs. The `content` column (`String @db.Text`, non-nullable) holds the XML defining the report output layout — columns, groupings, totals, formatting, and (for `.frx` uploads) a complete FastReport definition. An empty string `""` is the valid "no parameters" / "no content yet" value for both columns; neither is truly optional at the database level.

The two payloads serve entirely different purposes and follow different conventions. Dialog XML is a shallow, structured vocabulary (`<Dialog>`, `<Label>`, `<Date>`, `<Lookup>`) that the SPA understands, parses, and renders as a live preview form. Content XML is opaque to the SPA — the editor accepts any well-formed XML string and stores it verbatim. The report runtime (Go microservice) is responsible for interpreting Content XML; the SPA neither validates nor previews it beyond confirming it is well-formed. Each runs through the same CodeMirror-based editor component (`XmlEditor`) but with different upload accept lists and different downstream consumers.

## 2. Dialog XML

### 2.1 Root element

The root element **must** be `<Dialog>`. The `DialogPreview` component enforces this requirement: if the parsed document's `documentElement.tagName` is anything other than `"Dialog"`, the Preview tab displays the error "Preview requires a `<Dialog>` root element" and refuses to render.

```xml
<Dialog>
  <!-- child elements -->
</Dialog>
```

The `<Dialog>` element carries no required or documented attributes. Any attributes placed on the root element are silently ignored by the parser.

### 2.2 Element catalogue

The SPA's `DialogPreview` component (`src/components/DialogPreview.tsx`) is the source of truth for which child element tags are recognised. The `renderControl` function handles three cases explicitly; any other tag falls through to a neutral fallback.

| Element | Required attributes | Optional attributes | Preview rendering |
|---------|---------------------|---------------------|-------------------|
| `<Label>` | `Text` (string) | — | Rendered as a field label for the immediately following sibling. Not itself a control. |
| `<Date>` | `Name` (string) | — | Disabled `<input type="date">` with the `Name` value as placeholder. |
| `<Lookup>` | `Name` (string), `DataSource` (string) | — | Disabled `<select>` with "Select _Cleaned Source_…" placeholder text. |
| Any other tag | — | any | Neutral dashed-border row showing the tag name and all attribute key/value pairs in monospace text. No validation error is raised. |

**Attribute details:**

- `Text` on `<Label>`: the human-readable field caption displayed above the control in the Preview form.
- `Name` on `<Date>` and `<Lookup>`: the filter field name that must match the `filter` key in `source_params.params[]` for runtime binding (see §2.4). Typically PascalCase (`DateFrom`, `VendorCode`).
- `DataSource` on `<Lookup>`: a reference to the list source, conventionally prefixed with `@` (e.g. `@vendor_list`, `@department_list`). The Preview renderer strips the `@` prefix, removes a trailing `_list` suffix, replaces underscores with spaces, and title-cases the result to produce the dropdown placeholder text — so `@vendor_list` becomes "Select Vendor…" and `@department_list` becomes "Select Department…".

### 2.3 `<Label>` / control pairing

Pairing is **positional** — sibling order in the XML determines which label belongs to which control. The `parseDialogXml` function walks `root.children` in order. When it encounters a `<Label>` element:

1. It reads the next sibling (`children[i + 1]`).
2. If the next sibling exists and is **not** another `<Label>`, it groups them as a single preview row: label text + the control element. The index advances by 2 (both siblings consumed).
3. If the next sibling is absent or is itself a `<Label>`, the current `<Label>` renders as a standalone label row with no paired control (displays "(no control)" in the Preview).

There is **no** `for` attribute or name-based pairing. A `<Label>` followed immediately by a non-Label element always pairs with that element, regardless of whether the `Name` values match. Swapping sibling order changes the label assignment.

Controls that appear **without** a preceding `<Label>` (i.e. a `<Date>` or `<Lookup>` as the first element, or following another control) render as rows without a label caption. The Preview shows the control with a blank label area.

### 2.4 Mapping to `source_params`

At report runtime the Dialog XML's `<Date Name="X"/>` and `<Lookup Name="X" .../>` fields are bound to positional arguments by matching the `Name` attribute value against the `filter` key in each `source_params.params[]` entry. The binding only applies when `source_type` is `"function"` or `"procedure"` — for `"view"` templates the runtime applies filters via a WHERE clause and `source_params` is unused.

Binding rules:

- A Dialog field whose `Name` matches a `source_params` entry is passed as a positional argument in the order the params array is declared, not the order the fields appear in the Dialog XML.
- A Dialog field whose `Name` does **not** appear in `source_params` is rendered in the Preview form but is silently ignored at runtime — no argument is passed for it.
- A `source_params` entry whose `filter` does not match any Dialog field will be passed `NULL` to the function/procedure (or will cause a runtime error if `nullable: false`).

This means the Dialog XML and `source_params` must be kept in sync by the template author: every non-nullable `source_params` entry must have a matching `<Date>` or `<Lookup>` (or other input) in the Dialog XML, and vice versa.

Cross-reference: the `source_params` column shape is documented in [Data Model §5.3](./data-model.md).

## 3. Content XML

### 3.1 Storage and opaqueness

The `content` column stores the XML that the Go report runtime (see `micro-report`) uses to render the report output — rows, columns, groupings, subtotals, page layout, and embedded images. The SPA treats this column as an **opaque XML string**: it accepts any content that parses as well-formed XML (or empty string), stores it verbatim, and exposes it in the CodeMirror editor. The SPA does not parse, interpret, or preview Content XML.

Because the SPA imposes no structural constraints beyond well-formedness, there is no element catalogue defined at the SPA layer. The report runtime owns the Content XML schema. The exact elements and attributes in use depend on the runtime version and whether the template originated from the Go builder or was migrated from FastReport.

### 3.2 `.frx` file upload

The Content tab's upload accept list is `.frx,.xml,.txt`. The `.frx` extension is FastReport's native format — an XML-based template definition used in earlier versions of Carmen before the Go-based report runtime. The SPA performs **no conversion** on upload: it reads the file as UTF-8 text (`FileReader.readAsText`), runs the content through `formatXml()` to indent it, and stores the result directly in the `content` field. The Go runtime is responsible for interpreting `.frx` content.

The Dialog tab's upload accept list is `.xml,.txt` only — `.frx` is not accepted there because Dialog XML must conform to the `<Dialog>` root structure and FastReport definitions do not.

### 3.3 Empty content

An empty string `""` is valid for the `content` column (new templates before content is added). The SPA does not block saving a template with empty content; validation is the runtime's responsibility.

## 4. Editor surface

Both Dialog XML and Content XML are edited in the same `XmlEditor` component (`src/components/XmlEditor.tsx`), a CodeMirror 6 wrapper. The component accepts a `readOnly` prop — in view mode all toolbar buttons except Copy and Download are hidden and the editor is read-only.

| Feature | Detail |
|---------|--------|
| Language mode | `@codemirror/lang-xml` — syntax highlighting for tags, attributes, and text nodes |
| Line numbers | `lineNumbers()` extension — always visible |
| Code folding | `foldGutter()` + `foldKeymap` — fold/unfold at any tag boundary with the gutter icon or keyboard |
| Bracket matching | `bracketMatching()` — highlights matching tag pairs |
| Auto-close | `closeBrackets()` — closes `>` automatically |
| Auto-complete | `autocompletion()` + `completionKeymap` — basic XML completion |
| Search | `search({ top: true })` + `searchKeymap` — Ctrl/Cmd+F opens panel at top of editor |
| History (undo) | `history()` + `historyKeymap` — Ctrl/Cmd+Z / Ctrl/Cmd+Shift+Z |
| Tab indentation | `indentWithTab` — Tab key inserts indent (does not trap focus permanently) |
| Line wrapping | `EditorView.lineWrapping` — long lines wrap rather than scroll horizontally |
| Height | `minHeight: 360px`, `maxHeight: 560px` on the edit page (defaults: 320 / 560). Scrollable within the max |
| Font | `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace` at `12px` |
| Toolbar (edit mode) | Upload · Format · Copy · Download · Clear |
| Toolbar (view mode) | Copy · Download only |
| Upload (Dialog tab) | `.xml`, `.txt` |
| Upload (Content tab) | `.frx`, `.xml`, `.txt` |
| Format button | Runs `formatXml()` (DOMParser re-serialise + indent) — no-op if content is already formatted or invalid |
| Download button | Blob download as `dialog.xml` or `content.xml` |
| Clear button | Empties editor after `ConfirmDialog` confirmation; Ctrl/Cmd+Z restores |
| Line/byte display | Below editor: `{n} lines` badge + `{size}` (B / KB / MB) badge |
| Parse status | Below editor: green "Valid XML" with check icon, or red error message with line/col |

## 5. Validation

Validation runs in `src/utils/xml.ts:validateXml()` using the browser's native `DOMParser`. Validation is triggered on mount and debounced 300 ms after each edit. The result is surfaced in two places: the status row below the editor, and a red dot on the tab header badge for the affected tab.

| Condition | Status row display | Tab indicator |
|-----------|--------------------|---------------|
| Empty string | Treated as valid — no error shown | No red dot |
| Well-formed XML | Green "Valid XML" with check icon | No red dot |
| Malformed XML | Red error message: `Line {n}, col {m}: {browser message}` (truncated to 240 chars) | Red dot |
| Unclosed tag | Malformed — same as above | Red dot |
| Mismatched closing tag | Malformed — same as above | Red dot |

**Important caveats:**

- The validator uses `DOMParser` only — it checks **well-formedness**, not validity against any schema or XSD.
- Unknown element names in Dialog XML (e.g. `<TextBox>` or `<Numeric>`) are **not** validation errors. They parse as well-formed XML; the Preview renderer renders them using the neutral fallback (dashed-border box with tag name).
- A Dialog XML document with the wrong root element (anything other than `<Dialog>`) is **not** a validation error — it is well-formed XML. Only the Preview renderer refuses to render it and shows its own "Preview requires a `<Dialog>` root element" error message.
- The `format` button silently skips malformed XML (returns the input unchanged) rather than raising an additional error.

## 6. Worked example

The following is a minimal complete Dialog + Content pair for a date-range and vendor lookup report using a PostgreSQL function as its data source. The Dialog XML was constructed from the element catalogue in §2.2; no sample was found in the carmen-platform codebase outside of design documentation. The field names (`DateFrom`, `DateTo`, `VendorCode`) correspond to a matching `source_params` configuration shown below.

```xml
<!-- Dialog XML — stored in tb_report_template.dialog -->
<Dialog>
  <Label Text="Date From"/>
  <Date Name="DateFrom"/>
  <Label Text="Date To"/>
  <Date Name="DateTo"/>
  <Label Text="Vendor"/>
  <Lookup Name="VendorCode" DataSource="@vendor_list"/>
</Dialog>
```

In the Preview tab this renders as a 2-column grid of three rows:

| Label | Control |
|-------|---------|
| Date From | Disabled date input |
| Date To | Disabled date input |
| Vendor | Disabled select — "Select Vendor…" |

The `DataSource="@vendor_list"` value is cleaned by the Preview renderer: `@` stripped → `vendor_list` → `_list` removed → `vendor` → title-cased → "Vendor". The placeholder reads "Select Vendor…".

The matching `source_params` for a function-type template:

```
{
  "params": [
    { "filter": "DateFrom",  "type": "date", "nullable": false },
    { "filter": "DateTo",    "type": "date", "nullable": false },
    { "filter": "VendorCode","type": "text", "nullable": true  }
  ]
}
```

At runtime the executor calls `SELECT * FROM fn_receiving_report($1, $2, $3)` with the three user-supplied values in param-array order.

The Content XML column for this template would contain the Go report runtime's layout definition (column widths, grouping fields, totals). The SPA stores it opaquely; a representative placeholder is shown below to illustrate the separate payload:

```xml
<!-- Content XML — stored in tb_report_template.content -->
<!-- Actual structure is defined by the Go report runtime, not the SPA.
     This placeholder represents a report with three output columns. -->
<Content>
  <Columns>
    <Column Name="grn_no"       Label="GRN No"      Width="120"/>
    <Column Name="vendor_name"  Label="Vendor"       Width="200"/>
    <Column Name="total_amount" Label="Total (฿)"    Width="100" Align="right"/>
  </Columns>
</Content>
```

**Note:** The `<Content>` structure above is illustrative. The Go runtime's actual element names and attributes are defined in the `micro-report` service, not in the carmen-platform SPA.

## 7. References

- `src/components/DialogPreview.tsx` (lines 33–89, `parseDialogXml`; lines 92–124, `renderControl`) — source of truth for the Dialog element catalogue, pairing algorithm, and Preview rendering behaviour.
- `src/components/XmlEditor.tsx` (lines 49–82, `baseExtensions`) — CodeMirror 6 extension list; (lines 195–207, `handleUpload`) — file upload handling with `FileReader.readAsText` and auto-format on load.
- `src/utils/xml.ts` (lines 33–53, `validateXml`) — `DOMParser`-based well-formedness check; line/column extraction from `parsererror` text node.
- `src/pages/ReportTemplateEdit.tsx` (lines 869–895) — `XmlEditor` usage: Dialog tab `uploadAccept=".xml,.txt"`, Content tab `uploadAccept=".frx,.xml,.txt"`.
- Sibling [Data Model §5.1–5.3](./data-model.md) — column types (`String @db.Text` for both `dialog` and `content`), the `source_params` JSON shape, and the positional binding behaviour by `source_type`.
- Sibling [UI Screens §4.5–4.7](./ui-screens.md) — Dialog XML tab, Content XML tab, and Preview tab within the right-column Card.
