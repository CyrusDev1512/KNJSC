---
version: 1
slug: "app-templates-crm-bang-tinh-html"
primary_target: "app/templates/crm/bang_tinh.html"
related_targets: ["app/static/css/waybill.css","app/static/js/waybill.js"]
---

# Vận đơn mới — local extension, Operate

Scope: app/templates/crm/bang_tinh.html, only van_don_moi and its entry/detail/statistics fragments.

## Direction contract

THESIS: One working page follows the user's Excel sheet: entry, operations, statistics.

OWN-WORLD: Preserve the running KN CRM spreadsheet shell, toolbar, tokens, typography and interactions. Green grouped headers distinguish Excel content. Do not redesign the existing shell to match the unrelated pending global brief.

STORY: Sale creates an order; operators update its independent product/payment snapshot; filtered statistics reflect those edits.

FIRST VIEWPORT: Existing compact topbar, collapsible entry form, operations heading and familiar spreadsheet. Statistics follow the grid. Entry and statistics collapse to give the grid room.

FORM: Precisely specified local extension; no concept seed or replacement visual world. Product detail is a focused dialog opened from four aggregate cells.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.
