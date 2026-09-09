---
name: "Kim Ngân JSC / KN CRM"
description: "A compact Vietnamese operations system with a restrained app shell and a purpose-built spreadsheet workspace."
colors:
  accent: "#3a37a3"
  accent-hover: "#2e2b8a"
  accent-soft: "#ecebf9"
  on-accent: "#ffffff"
  brand-brass: "#9a7228"
  plane: "#f2f2f6"
  surface: "#fbfbfd"
  surface-subtle: "#f6f6fa"
  surface-toolbar: "#ecedf3"
  ink: "#15151c"
  ink-muted: "#4a4a58"
  ink-faint: "#83838f"
  rule: "#e3e3ec"
  rule-strong: "#c9c9d6"
  positive: "#0ca30c"
  warning: "#fab219"
  critical: "#d03b3b"
  dark-plane: "#0b0b10"
  dark-surface: "#16161e"
  dark-surface-subtle: "#1c1c26"
  dark-surface-toolbar: "#22222e"
  dark-ink: "#f1f1f6"
  dark-ink-muted: "#b6b6c4"
  dark-ink-faint: "#8a8a99"
  dark-rule: "#2a2a36"
  dark-rule-strong: "#3b3b4a"
  dark-accent: "#9a97ee"
  dark-accent-hover: "#b0adf3"
  dark-accent-soft: "#1f1e39"
  dark-on-accent: "#0b0b10"
  dark-brand-brass: "#c9a458"
  sheet-shell: "#101014"
  sheet-shell-ink: "#ece5cb"
  sheet-gold: "#d8b45c"
  sheet-grid: "#fffdf8"
  sheet-grid-plane: "#f3f0e7"
  sheet-grid-rule: "#e6e0d1"
typography:
  headline:
    fontFamily: '"Be Vietnam Pro", system-ui, -apple-system, "Segoe UI", sans-serif'
    fontSize: "26px"
    fontWeight: 800
    lineHeight: 1.25
    letterSpacing: "-0.025em"
  title:
    fontFamily: '"Be Vietnam Pro", system-ui, -apple-system, "Segoe UI", sans-serif'
    fontSize: "20px"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "normal"
  body:
    fontFamily: '"Be Vietnam Pro", system-ui, -apple-system, "Segoe UI", sans-serif'
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "normal"
  label:
    fontFamily: '"Be Vietnam Pro", system-ui, -apple-system, "Segoe UI", sans-serif'
    fontSize: "12.5px"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "normal"
  mono-label:
    fontFamily: '"IBM Plex Mono", ui-monospace, "Cascadia Mono", Consolas, monospace'
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.1em"
  sheet-body:
    fontFamily: '"Segoe UI", system-ui, -apple-system, "Be Vietnam Pro", sans-serif'
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.3
    letterSpacing: "normal"
rounded:
  sm: "2px"
  md: "3px"
  lg: "6px"
  control: "8px"
  chip: "10px"
  pill: "999px"
spacing:
  1: "4px"
  2: "8px"
  3: "12px"
  4: "16px"
  5: "24px"
  6: "32px"
  7: "48px"
  8: "64px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "6px 16px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "6px 16px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "6px 12px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "16px"
  chip-accent:
    backgroundColor: "{colors.accent-soft}"
    textColor: "{colors.accent}"
    typography: "{typography.label}"
    rounded: "{rounded.chip}"
    padding: "1px 8px"
  navigation-active:
    backgroundColor: "{colors.accent-soft}"
    textColor: "{colors.accent}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "7px 12px"
  sheet-export:
    backgroundColor: "{colors.sheet-gold}"
    textColor: "#241a05"
    typography: "{typography.sheet-body}"
    rounded: "{rounded.control}"
    padding: "0 12px"
    height: "30px"
  sheet-cell:
    backgroundColor: "{colors.sheet-grid}"
    textColor: "#1f2937"
    typography: "{typography.sheet-body}"
    rounded: "0"
    padding: "0 6px"
    height: "25px"
---

# Design System: Kim Ngân JSC / KN CRM

## Overview

**Creative North Star: "The Disciplined Operations Desk"**

Kim Ngân JSC is a compact, desktop-first operations interface. The shared KNERP and KN CRM shell uses pale neutral layers, fine rules, restrained indigo actions, and very small radii so dense business information remains calm and legible. Brass is a rare identity mark, not a general-purpose action color.

The KN CRM grid is a deliberate workspace inside that system: a dark brass-accented tool frame surrounds a permanently warm, paper-like sheet. It behaves more like a familiar desktop spreadsheet than a card-based web page—fixed toolbars, 25px rows, sticky headings, formula controls, sheet tabs, and direct cell states carry the hierarchy.

**Key Characteristics:**

- Compact, information-first density with 4px-based spacing.
- Fine borders and tonal layering before shadow.
- Restrained indigo for normal application actions; brass only for KN identity and spreadsheet emphasis.
- A dark spreadsheet frame around a light cream grid, independent of the selected app theme.
- Vietnamese labels in Be Vietnam Pro; numerical and technical metadata use tabular or monospaced text.

## Colors

The shared application palette is cool-neutral and indigo; the spreadsheet adds a warm black, brass, and cream working surface without replacing the shared semantic colors.

### Primary

- **Operational Indigo** (`accent`): Primary buttons, links, active navigation, focus borders, and selected application states.
- **Pressed Indigo** (`accent-hover`): Hover state for primary actions.
- **Indigo Wash** (`accent-soft`): Active navigation, computed fields, selected chips, and focus halos.

### Secondary

- **Kim Ngân Brass** (`brand-brass`): A sparse identity marker in the application shell.
- **Spreadsheet Gold** (`sheet-gold`): Active sheet tabs, spreadsheet hover outlines, avatar/export emphasis, and the grid selection language.

### Tertiary

- **Positive**, **Warning**, and **Critical**: Status-only colors for feedback, chips, invalid data, save state, and destructive actions. They do not compete with the primary action color.

### Neutral

- **Workspace Plane** (`plane`): Outermost application background.
- **Working Surface** (`surface`): Cards, inputs, navigation, and table surfaces.
- **Subtle Surface** (`surface-subtle`): Hover rows, disabled fields, and low-contrast grouping.
- **Primary Ink** (`ink`), **Muted Ink** (`ink-muted`), and **Faint Ink** (`ink-faint`): Three deliberate text levels.
- **Fine Rule** (`rule`) and **Strong Rule** (`rule-strong`): Structural dividers and control borders.
- **Dark Theme Roles** (`dark-*`): A direct role-for-role swap for the shared shell when dark mode is selected; hierarchy stays identical rather than becoming a second visual system.
- **Spreadsheet Night** (`sheet-shell`) and **Warm Shell Ink** (`sheet-shell-ink`): The default full-screen KN CRM frame.
- **Cream Grid** (`sheet-grid`), **Grid Plane** (`sheet-grid-plane`), and **Grid Rule** (`sheet-grid-rule`): The invariant readable spreadsheet surface.

### Named Rules

**The Two-Layer Workspace Rule.** The application shell may follow light or dark theme tokens, but spreadsheet cells remain a warm light surface so editing and scanning are stable across themes.

**The Brass Restraint Rule.** Brass marks KN identity and spreadsheet emphasis; ordinary product actions remain indigo.

## Typography

**Display Font:** Be Vietnam Pro (with system sans-serif fallbacks)  
**Body Font:** Be Vietnam Pro (with system sans-serif fallbacks)  
**Label/Mono Font:** IBM Plex Mono (with platform monospace fallbacks)

**Character:** Be Vietnam Pro keeps Vietnamese product language compact and neutral. IBM Plex Mono separates codes, counts, dates, and uppercase section labels; the spreadsheet uses Segoe UI for grid familiarity.

### Hierarchy

- **Headline** (`headline`): Page-level titles in the shared application shell.
- **Title** (`title`): Section and CRM page headings.
- **Body** (`body`): Default application copy and controls; descriptive text is generally limited to about 68–70 characters.
- **Label** (`label`): Form labels, metadata, compact buttons, and table support text.
- **Mono Label** (`mono-label`): Uppercase navigation groups, codes, counts, and tabular metadata.
- **Sheet Body** (`sheet-body`): Grid cells, spreadsheet controls, menus, and tabs.

### Named Rules

**The Utility Type Rule.** Monospace is reserved for identifiers, figures, and compact structural labels; ordinary Vietnamese prose stays in the sans-serif body face.

## Layout

The shared shell is a fixed-width 244px navigation rail beside a flexible content column. Its top bar is 56px high; content is capped at 1400px and uses generous horizontal padding while cards and forms use the 4px spacing scale. Responsive grids collapse through content-driven minimum widths rather than fixed device templates.

At 900px and below, the navigation becomes an off-canvas panel and the page gutters reduce to 16px. KN CRM's tree-and-content layout stacks below 760px. The spreadsheet is a separate full-height flex column: 48px top bar, 42px toolbar, 34px formula bar, flexible scrollable grid, and 38px sheet-tab footer. The grid uses 100px default columns, a 46px row-number gutter, 27px letter headers, and 25px data rows. On narrow screens, the surrounding controls compress while the grid itself scrolls horizontally rather than crushing columns.

**The Grid Owns Overflow Rule.** Dense spreadsheet content preserves column width and scrolls inside its workspace; the overall document must not be widened to fit the sheet.

## Elevation & Depth

The shared application is flat by default. Cards use a nearly imperceptible structural shadow (`0 1px 2px rgba(21,21,40,.05)`), while menus and dialogs alone receive clear lift. The spreadsheet uses borders and tonal separation for its fixed bars; floating menus use a deep ambient shadow (`0 16px 40px rgba(0,0,0,.6)` in the default dark shell), and the waybill dialog uses `0 12px 36px #0004`.

### Shadow Vocabulary

- **Structural Low** (`0 1px 2px rgba(21,21,40,.05)`): Shared cards and metric containers.
- **Overlay** (`0 4px 16px rgba(21,21,40,.10)`): Mobile navigation and shared floating surfaces.
- **Spreadsheet Overlay** (`0 16px 40px rgba(0,0,0,.6)`): Spreadsheet menus, filters, and popovers.
- **Cell Editor** (`0 3px 10px rgba(60,48,10,.25)`): The active editor lifted above the grid.

**The Flat-Until-Floating Rule.** Borders and background steps define normal structure; pronounced shadows are reserved for content that truly overlays the workspace.

## Shapes

The system uses tight, functional corners: 2–3px for ordinary controls and cards, 6px for larger containers, and 8–10px for spreadsheet controls and floating menus. Chips and progress tracks may be fully rounded because their silhouette communicates status rather than container hierarchy. Grid cells and headers remain square and contiguous; selected cells use an inset rectangular outline with a small square fill handle.

## Components

### Buttons

- **Shape:** Compact rectangular controls with tight shared-shell corners; spreadsheet top-bar controls use the slightly softer control radius.
- **Primary:** Indigo fill with white text and a stronger weight.
- **Secondary:** Surface fill, strong-rule border, and primary ink; hover shifts to the subtle surface.
- **Danger:** Transparent surface with critical text and border, gaining a critical wash on hover.
- **Focus:** A 2px accent outline with 2px offset at the application level; reduced motion removes transitions and animations.

### Chips

- **Style:** Compact, softly rounded labels with tinted backgrounds and medium-weight text.
- **State:** Indigo identifies selection, neutral gray identifies passive information, and semantic colors are reserved for true statuses.

### Cards / Containers

- **Corner Style:** Tight shared cards and 6px larger CRM/waybill sections.
- **Background:** Working surface over the workspace plane.
- **Shadow Strategy:** Structural low shadow only; spreadsheet and waybill sections generally rely on borders.
- **Border:** One-pixel fine rule.
- **Internal Padding:** Usually 12–16px; major page gutters use 24–32px on desktop.

### Inputs / Fields

- **Style:** Surface background, strong-rule border, tight radius, and compact vertical padding.
- **Focus:** Accent border plus a 3px indigo wash in shared forms; spreadsheet editors use a 2px gold inset or enclosing border.
- **Error / Disabled:** Errors use critical border/text/wash; disabled fields shift to the subtle surface and muted ink.

### Navigation

The application navigation is a 244px light rail with compact 7px-by-12px items, restrained icons, and an indigo-wash active state. KN CRM may collapse the rail to a 60px icon strip. At mobile width the rail becomes off-canvas. The full-screen spreadsheet replaces it with a 48px dark top bar, a back control that returns to the CRM folder context, and a compact account menu.

### Spreadsheet Workspace

The signature workspace is dense and desktop-like: dark toolbar and footer, warm formula bar, cream grid, sticky letter/name headers, precise one-pixel cell rules, and a 2px gold current-cell outline. Sheet tabs are uppercase, horizontally scrollable, and mark the active sheet with a thin gold edge. Formatting palettes, column filters, context menus, undo/redo, selection ranges, and fill handles follow the same compact control language.

### Waybill Group Header

The new Vận đơn surface adds green grouped column headers and pale-green field headers to mirror the source Excel structure. This is a local data-categorization treatment inside the spreadsheet; it does not alter the global KN CRM palette or button hierarchy.

## Do's and Don'ts

### Do:

- **Do** use the shared neutral/indigo tokens for ordinary application pages and controls.
- **Do** keep the KN CRM grid cream and legible in both light and dark shell modes.
- **Do** preserve the compact spreadsheet measurements, sticky headers, rectangular selection outline, and horizontal overflow behavior.
- **Do** use tabular or monospaced text for codes and figures where alignment improves scanning.
- **Do** keep visible keyboard focus and honor reduced-motion preferences.

### Don't:

- **Don't** use brass as a replacement for the normal indigo application action color.
- **Don't** turn Vận đơn's green grouped headers into a global brand or navigation color.
- **Don't** render the spreadsheet as floating cards or loosen its row density into a dashboard layout.
- **Don't** add decorative shadows to resting surfaces; reserve strong elevation for overlays.
