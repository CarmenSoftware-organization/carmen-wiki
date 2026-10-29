---
title: Report Template — XML Spec
description: Dialog XML element catalogue (Label/Date/Lookup/Group, Cols/ColSpan, From/To ranges, source_params), Content XML storage, Export XML CSV mapping, validation categories, and a worked example.
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, report-templates, xml
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Report Template — XML Spec

> **At a Glance**
> **Three payloads:** Dialog XML (parameter form) &nbsp;·&nbsp; Content XML (report output) &nbsp;·&nbsp; Export XML (optional CSV column mapping) &nbsp;·&nbsp; **Storage:** `dialog` / `content` are non-null `String @db.Text` columns, `export_xml` is nullable (see [Data Model §5.1–5.2](./data-model.md)) &nbsp;·&nbsp; **Editor:** CodeMirror 6 (XML mode, folding, search, parse-error markers, line count, no line wrapping) &nbsp;·&nbsp; **Uploads:** Dialog and Export `.xml`, `.txt`; Content `.frx`, `.xml`, `.txt` (legacy FastReport migration) &nbsp;·&nbsp; **Validation:** browser `DOMParser` — inline parse error with line/column markers, plus non-blocking Export XML lint &nbsp;·&nbsp; **Preview:** Dialog tab only — becomes a drag-and-drop layout editor while editing; Content XML has no SPA preview renderer &nbsp;·&nbsp; **Dialog readers:** four codebases must agree (§2.5) &nbsp;·&nbsp; **Worked example:** §7 contains a minimal complete pair

## 1. Overview

Every row in `tb_report_template` carries two required XML payload columns (plus an optional third, Export XML, §4). The `dialog` column (`String @db.Text`, non-nullable) holds the XML the report runtime renders as the parameter input form shown to users before a report runs. The `content` column (`String @db.Text`, non-nullable) holds the XML defining the report output layout — columns, groupings, totals, formatting, and (for `.frx` uploads) a complete FastReport definition. An empty string `""` is the valid "no parameters" / "no content yet" value for both columns; neither is truly optional at the database level.

The two payloads serve entirely different purposes and follow different conventions. Dialog XML is a shallow, structured vocabulary (`<Dialog>`, `<Label>`, `<Date>`, `<Lookup>`, `<Group>`) that the SPA understands, parses, edits in a layout editor, and renders as a live preview form. Content XML is opaque to the SPA — the editor accepts any well-formed XML string and stores it verbatim. The report runtime (Go microservice) is responsible for interpreting Content XML; the SPA neither validates nor previews it beyond confirming it is well-formed. Each runs through the same CodeMirror-based editor component (`XmlEditor`) but with different upload accept lists and different downstream consumers.

## 2. Dialog XML

### 2.1 Root element

The root element **must** be `<Dialog>`. The `DialogPreview` component enforces this requirement: if the parsed document's `documentElement.tagName` is anything other than `"Dialog"`, the Preview tab displays the error "Preview requires a `<Dialog>` root element" and refuses to render.

```xml
<Dialog Cols="2">
  <!-- child elements -->
</Dialog>
```

`Cols` is the number of columns of the dialog grid, an integer from 1 to 4: absent or invalid (non-integer, 0, negative) is treated as 1 with a preview warning, and a value above 4 is clamped to 4 with a warning (`MAX_COLS = 4`, `src/utils/dialogXml.ts`). Below 640px every reader shows a single column regardless. Other attributes on the root are ignored.

### 2.2 Element catalogue

`src/utils/dialogXml.ts` (`parseDialogXml`) is the SPA's parser, rendered by `DialogPreview` / `DialogLayoutEditor`. The control tags it knows are `Date` and `Lookup` (`CONTROL_TAGS`); `Label` and `Group` are structural; any other child tag is dropped with an "unknown element" warning (the inventory run dialog drops it too, so the preview matches what users see).

| Element | Attributes | Meaning |
|---------|------------|---------|
| `<Label>` | `Text`; `Visible` (`"false"` hides it); `ColSpan` is meaningless here (warning) | Caption for the **next** control. Also the "to" half of a range when it reads `to` or is `Visible="false"` |
| `<Date>` | `Name` (required in practice), `Value` (default value; the property panel hints `@today` = today), optional `Label`, optional `ColSpan` | Date filter |
| `<Lookup>` | `Name`, either `DataSource` (e.g. `@vendor_list`) **or** `Items` + `Values` (fixed list, entries separated by `~`), optional `Multi="true"`, `Value`, `Label`, `ColSpan` | Dropdown. `DataSource` values the inventory run dialog understands live in its `dataSourceMap`; the layout editor suggests the same list from `src/utils/dialogDataSources.ts` and warns on an unknown one (inventory passes unknown values through unchanged). A `~` inside a fixed-list value is rejected by the editor because it is the separator |
| `<Group>` | optional `Label` (heading above its fields), optional `ColSpan`; `Cols` on a group is reserved | Wraps Label+control pairs and lays them side by side in one cell. Nested groups are lifted into the outer group with a warning; empty groups are skipped with a warning; From/To auto-pairing does **not** happen inside a group |
| `<TextBox>` | `Name`, optional `Label`, `Items`/`Values` | Read only by micro-report's filter-header parser (`parseDialogDefs` accepts `Date`, `Lookup` and `TextBox`), e.g. Slow Moving's free-typed Day. The inventory run dialog and the SPA preview do **not** render it, so the preview shows it as an unknown element |

**Attribute details:**

- `Text` on `<Label>`: the human-readable field caption displayed above the control.
- `Name` on `<Date>` / `<Lookup>`: the filter field name that must match the `filter` key in `source_params.params[]` for runtime binding (see §2.4). Typically PascalCase (`DateFrom`, `VendorCode`). The layout editor requires letters, digits and `_`, not starting with a digit, and unique within the dialog.
- `DataSource` on `<Lookup>`: a reference to the list source, conventionally prefixed with `@` (e.g. `@vendor_list`). When no `DataSource` is set the editor uses a **Fixed list** (`Items` = shown text, `Values` = sent value, parallel `~`-separated lists).
- `Label="…"` on `<Date>` / `<Lookup>`: the control is a field on its own; it never takes the `<Label>` before it (that label is dropped with a warning) and is never part of a From/To range — wrap From and To in a `<Group>` instead. The value is trimmed; empty falls back to the control's `Name` (with a warning). Micro-report's filter header also prefers the control's own `Label` over a preceding `<Label>`.
- `ColSpan="n"`: integer ≥ 1, clamped to `Cols` (with a warning); on a control or a `<Group>`, never on `<Label>`.

**Rollout rules (from `docs/dialog-xml/README.md`):** do not put a `<Group>` or a `Label=` attribute on a control into a live template until the inventory release that supports it is on inventory production — older builds silently drop grouped fields and controls with their own `Label`. (`Label` on `<Group>` is safe: the heading is just missing.) The preview shows a notice whenever the XML uses either feature. Fields added by the layout editor's **Add field** menu always use the classic `<Label/>` + control pair, never `Label=`, to stay safe on older builds.

### 2.3 `<Label>` / control pairing

Pairing is **positional** — sibling order in the XML determines which label belongs to which control. The `parseDialogXml` function walks `root.children` in order (runs of non-`<Group>` children are paired together, and each `<Group>` is paired internally). When it encounters a `<Label>` element:

1. It looks at the next node after dropping elements the inventory dialog does not know.
2. If that node is a control (`Date` / `Lookup`) without its own `Label=`, the pair becomes one field cell: label text + the control element. Both siblings are consumed.
3. If the next node is absent or is not such a control, the current `<Label>` draws nothing and the preview lists a "label without control" warning.

There is **no** `for` attribute or name-based pairing. A `<Label>` followed immediately by a non-Label element always pairs with that element, regardless of whether the `Name` values match. Swapping sibling order changes the label assignment.

**Ranges.** Outside a group, `<Label>` + control followed by a second label that reads `to` (or is `Visible="false"`) and a second control of the same tag collapse into one **range** cell (From … To). A pair of same-tag controls named `XFrom` / `XTo` also pairs when the second `<Label>` is present. The range takes the From control's `ColSpan`.

Controls that appear **without** a preceding visible `<Label>` and without their own `Label=` (a `<Date>` or `<Lookup>` as the first element, or following another control) are **not drawn** — the inventory run dialog drops them — and the preview lists a "control without label" warning instead. A `<Label>` with no control after it likewise draws nothing and raises a "label without control" warning. (Earlier versions of this page said such controls rendered with a blank caption; the shared parser, kept in step with inventory by common fixtures, no longer does.)

### 2.4 Mapping to `source_params`

At report runtime the Dialog XML's `<Date Name="X"/>` and `<Lookup Name="X" .../>` fields are bound to positional arguments by matching the `Name` attribute value against the `filter` key in each `source_params.params[]` entry. The binding only applies when `source_type` is `"function"` or `"procedure"` — for `"view"` templates the runtime applies filters via a WHERE clause and `source_params` is unused.

Binding rules:

- A Dialog field whose `Name` matches a `source_params` entry is passed as a positional argument in the order the params array is declared, not the order the fields appear in the Dialog XML.
- A Dialog field whose `Name` does **not** appear in `source_params` is rendered in the Preview form but is silently ignored at runtime — no argument is passed for it.
- A `source_params` entry whose `filter` does not match any Dialog field will be passed `NULL` to the function/procedure (or will cause a runtime error if `nullable: false`).

This means the Dialog XML and `source_params` must be kept in sync by the template author: every non-nullable `source_params` entry must have a matching `<Date>` or `<Lookup>` (or other input) in the Dialog XML, and vice versa.

Cross-reference: the `source_params` column shape is documented in [Data Model §5.3](./data-model.md).

### 2.5 The four readers of Dialog XML

The Dialog XML is read by four codebases, which must interpret it identically (`../carmen-backstage/docs/dialog-xml/README.md`): the Backstage preview (`src/utils/dialogXml.ts` → `DialogPreview`), the inventory run dialog (`carmen-frontend/routes/report/list/parse-report-dialog.ts`), the inventory schedule form (`parse-schedule-dialog.ts`), and micro-report's filter-header injector (`service/template_filter_inject.go`, `parseDialogDefs`). The same fixture files (`docs/dialog-xml/fixtures/<name>.xml` + `<name>.expected.json`) run as tests in both frontends; the inventory copy is re-copied by hand when the set changes. Change the grammar in all four places together.

## 3. Content XML

### 3.1 Storage and opaqueness

The `content` column stores the XML that the Go report runtime (see `micro-report`) uses to render the report output — rows, columns, groupings, subtotals, page layout, and embedded images. The SPA treats this column as an **opaque XML string**: it accepts any content that parses as well-formed XML (or empty string), stores it verbatim, and exposes it in the CodeMirror editor. The SPA does not parse, interpret, or preview Content XML.

Because the SPA imposes no structural constraints beyond well-formedness, there is no element catalogue defined at the SPA layer. The report runtime owns the Content XML schema. The exact elements and attributes in use depend on the runtime version and whether the template originated from the Go builder or was migrated from FastReport.

### 3.2 `.frx` file upload

The Content tab's upload accept list is `.frx,.xml,.txt`. The `.frx` extension is FastReport's native format — an XML-based template definition used in earlier versions of Carmen Blue before the Go-based report runtime. The SPA performs **no conversion** on upload: it reads the file as UTF-8 text (`FileReader.readAsText`), runs the content through `formatXml()` to indent it, and stores the result directly in the `content` field. The Go runtime is responsible for interpreting `.frx` content.

The Dialog and Export tabs' upload accept list is `.xml,.txt` only — `.frx` is not accepted there because Dialog XML must conform to the `<Dialog>` root structure and FastReport definitions do not.

### 3.3 Empty content

An empty string `""` is valid for the `content` column (new templates before content is added). The SPA does not block saving a template with empty content; validation is the runtime's responsibility.

## 4. Export XML

An optional third payload, stored in `tb_report_template.export_xml` (null when absent; a blank editor is saved as `null`). It tells the report service how to turn the report's dataset into a flat **CSV file** for the "Export data" button. It is only used when the template has `allow_export = true` and a non-blank Export XML (`has_export` in micro-report's template list). The SPA edits it in the **Export XML** tab and only checks well-formedness plus the lint below; the format is defined and enforced by micro-report (`service/export_xml.go`, `ParseExportXML`), which rejects an invalid document when the export is requested.

```xml
<Export FileName="purchase_order_list" GroupBy="poNo">
  <Sort Field="RowKey"/>
  <Column Header="Date" Field="PoDate" Format="dd/MM/yyyy"/>
  <Column Header="PO.No" Field="PoNo"/>
  <Column Header="Total Amount" Field="TotalAmount" Format="0.00"/>
  <Column Header="Source" Value="PO"/>
  <Column Header="Vendor" Expression="[VendorCode] - [VendorName]"/>
</Export>
```

| Element / attribute | Rule |
|---|---|
| root | Must be `<Export>`. A leading BOM is tolerated |
| `FileName` (root, optional) | Base name for the download |
| `GroupBy` (root, optional) | Fixes the report's Group By for the export, whatever the user picked on screen — e.g. Purchase Order List exports one row per PO even when the screen is grouped per PO and location |
| `<Sort Field Desc>` (optional, repeatable) | `Field` required; `Desc` must be `true` or `false` when present; the first `Sort` is the primary key. Numbers compare numerically (including NUMERIC columns delivered as plain-decimal strings), date-looking strings compare as dates, nulls always sort last |
| `<Column>` (at least one) | `Header` required; **exactly one** of `Field`, `Value` or `Expression`. CSV column order is the order of the elements |
| `Field` | A dataset row key. The data-source prefix Content XML uses is stripped (`CreditNoteDetail.CnNo` → `CnNo`, everything up to the last `.`), and `ADMIN_Bu.Name` resolves to `BuName` |
| `Format` (on `Field` only) | Dates: any format containing `dd`, `MM`, `yyyy`, `HH`, `mm`, `ss` (default `dd/MM/yyyy`, rendered in Asia/Bangkok time). Numbers: `0`, `0.00`, `0.0000…`, optionally with thousands grouping `#,##0.00` |
| `Value` | A literal string (may be empty) |
| `Expression` | Text with `[Field]` placeholders substituted from the row; an expression that is exactly one numeric placeholder is emitted as a number |

Output is UTF-8 **with BOM**, CRLF line endings, a header row (an export with zero rows still gets the header). Any text cell that starts with `=`, `+`, `-`, `@`, a tab or a carriage return gets a leading `'` to defuse spreadsheet formula injection; formatted numbers are exempt. The SPA lint (`src/utils/exportXml.ts`, same rules for the field-name normalisation as the Go engine) never blocks saving; it warns when the root is not `<Export>`, there is no `<Column>`, a column lacks `Header` or has zero/several of `Field`/`Value`/`Expression`, `Field` is empty, `Sort` lacks a `Field` or has a bad `Desc`, or a referenced field (`Field`, `Sort Field`, or a `[placeholder]` in an `Expression`) is not a column declared in the Content XML's `<TableDataSource>` (computed `GroupBy`, `BuName`, `CalculationMethod` are exempt) — in which case "the cell will be empty".

## 5. Editor surface

Dialog XML, Content XML and Export XML are edited in the same `XmlEditor` component (`src/components/XmlEditor.tsx`), a CodeMirror 6 wrapper. The component accepts a `readOnly` prop — in view mode all toolbar buttons except Copy and Download are hidden and the editor is read-only.

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
| Line wrapping | **None** (since 2026-10) — long lines (`ReportInfo`, `Expression=…`) scroll horizontally so the XML matches its real line structure; the editor also scrolls vertically inside its box |
| Height | `minHeight: 360px`, `maxHeight: calc(100vh - 21rem)` on the edit page (the props now accept any CSS length; defaults 320 / 560 elsewhere). The max applies to the CodeMirror scroller itself, so long documents scroll instead of being cut off |
| Font | `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace` at `12px` |
| Toolbar (edit mode) | Upload · Format · Copy · Download · Clear |
| Toolbar (view mode) | Copy · Download only |
| Upload (Dialog tab) | `.xml`, `.txt` |
| Upload (Content tab) | `.frx`, `.xml`, `.txt` |
| Upload (Export tab) | `.xml`, `.txt` |
| Format button | Runs `formatXml()` (DOMParser re-serialise + indent) — no-op if content is already formatted or invalid |
| Download button | Blob download as `dialog.xml`, `content.xml` or `export.xml` |
| Clear button | Empties editor after `ConfirmDialog` confirmation; Ctrl/Cmd+Z restores |
| Line/byte display | Below editor: `{n} lines` badge + `{size}` (B / KB / MB) badge |
| Parse status | Below editor: green "Valid XML" with check icon, a neutral "empty XML" note when blank, or red error message with line/col |

## 6. Validation

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
- Unknown element names in Dialog XML (e.g. `<TextBox>` or `<Numeric>`) are **not** validation errors. They parse as well-formed XML; the Preview lists an "unknown element" warning and does not draw them as fields (inventory drops them too), though micro-report still reads `<TextBox>` for the filter header (§2.2).
- A Dialog XML document with the wrong root element (anything other than `<Dialog>`) is **not** a validation error — it is well-formed XML. Only the Preview renderer refuses to render it and shows its own "Preview requires a `<Dialog>` root element" error message.
- The `format` button silently skips malformed XML (returns the input unchanged) rather than raising an additional error.

## 7. Worked example

The following is a minimal complete Dialog + Content pair for a date-range and vendor lookup report using a PostgreSQL function as its data source. The Dialog XML was constructed from the element catalogue in §2.2; real templates (as of 2026-10-08) are kept as `real-*` fixtures in `../carmen-backstage/docs/dialog-xml/fixtures/`. The field names (`DateFrom`, `DateTo`, `VendorCode`) correspond to a matching `source_params` configuration shown below.

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

In the Preview tab this renders as a single-column grid (no `Cols` attribute, so 1 column) of three rows:

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

**Note:** The `<Content>` structure above is illustrative. The Go runtime's actual element names and attributes are defined in the `micro-report` service, not in the carmen-backstage SPA.

## 8. References

- `../carmen-backstage/src/utils/dialogXml.ts` (`parseDialogXml`, `parseDialogDocument`) — the SPA's Dialog XML parser: `Cols`/`ColSpan` rules, `<Group>`, control `Label`, range pairing, warnings. Rendered by `src/components/DialogPreview.tsx` and `src/components/dialogPreview/{CellView,DialogLayoutEditor,PropertyPanel}.tsx`.
- `../carmen-backstage/docs/dialog-xml/README.md` and `docs/dialog-xml/fixtures/` — the cross-repo Dialog XML grammar, rollout rules and shared fixtures.
- `../carmen-backstage/src/utils/exportXml.ts` (`lintExportXml`, `normalizeExportField`) — Export XML lint; `../micro-report/service/export_xml.go` (`ParseExportXML`, `WriteExportCSV`) — the authoritative Export XML parser and CSV writer; `../micro-report/db/seed/report-templates/*.export.xml` — real examples.
- `../micro-report/service/template_filter_inject.go` (`parseDialogDefs`) — the Dialog reader used for the report's filter header.
- `../carmen-backstage/src/components/XmlEditor.tsx` — CodeMirror 6 editor (extension list, upload handling, download name, empty-XML note).
- `../carmen-backstage/src/utils/xml.ts` (`validateXml`) — `DOMParser`-based well-formedness check; line/column extraction from the `parsererror` text node.
- `../carmen-backstage/src/pages/ReportTemplateEdit.tsx` — `XmlEditor` usage for the Dialog, Content and Export tabs (`uploadAccept`, `filename`, `maxHeight`).
- Sibling [Data Model §5.1–5.3](./data-model.md) — column types, the `source_params` JSON shape, and the positional binding behaviour by `source_type`.
- Sibling [UI Screens §4.5–4.8](./ui-screens.md) — Dialog XML, Content XML, Export XML and Preview/layout-editor tabs within the right-column Card.
