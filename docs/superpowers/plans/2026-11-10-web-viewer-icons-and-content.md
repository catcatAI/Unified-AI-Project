# Web Live2D Viewer Icons and Content Consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for
> tracking.

**Goal:** Unify the Web Live2D Viewer’s navigation and heading icons, add a
palette-aligned favicon, and correct only content conflicts that are directly
evidenced by authoritative project documentation.

**Architecture:** Continue using the existing single-page HTML/CSS Viewer, with
small inline SVG icons and a favicon stored in the Viewer asset directory. No
new runtime dependency or framework is introduced; no model, texture, or runtime
configuration changes are made.

**Tech Stack:** HTML, CSS, inline SVG, existing browser tooling.

**Spec:**
`docs/superpowers/specs/2026-11-10-web-viewer-icons-and-content-design.md`

## Global Constraints

- Preserve existing Live2D models, textures, rigs, and runtime behavior.
- Do not display the PicLumen concept art in the Viewer.
- Do not use the unapproved wheat-ring/flower motif as a logo.
- Use only the documented palette: rose `#E88DB8`, blue `#69A9E8`, ivory
  `#FFF8F0`, teal `#4D9A91`, gold `#C9A44C`.
- Do not add icon/font dependencies or unrelated refactors.
- Correct only content conflicts with direct documentation evidence; leave
  uncertain claims explicitly unverified.

## Review Focus

- Navigation destinations and `data-panel` values remain unchanged while icons
  change: verify links/buttons retain the same panel identifiers and text
  labels.
- Icon-only controls remain accessible: verify toolbar and window controls have
  descriptive accessible names.
- Narrow viewport remains usable with new icons: inspect responsive layout and
  ensure labels do not overlap controls.
- Favicon resolves correctly from the Viewer root in the intended static-file
  hosting context.
- Content corrections do not imply an unverified identity or redistribution
  license for the existing Live2D models; verify copy against the approved
  character design and asset audit documents.

---

### Task 1: Unify Viewer iconography, favicon, and evidence-backed content

**Files:**

- Modify: `apps/web-live2d-viewer/index.html`
- Modify: `apps/web-live2d-viewer/style.css`
- Create: `apps/web-live2d-viewer/assets/angela-viewer-icon.svg`

**Interfaces:**

- Consumes: palette and identity constraints in the approved design spec.
- Produces: consistent compact inline SVG icon treatment for existing
  navigation/headings; favicon at `assets/angela-viewer-icon.svg`; same existing
  labels, controls, and panel targets.

- [ ] **Step 1: Inventory authoritative content conflicts**

Compare visible Viewer copy, identity labels, and model claims with
`docs/art-and-persona-audit.md` and the approved Angela core design spec. Record
changes only for direct contradictions; do not treat unverified model identity,
licensing, or provenance as settled.

- [ ] **Step 2: Replace emoji pictograms in navigation and panel headings**

Use small inline SVGs with a consistent viewBox, stroke weight, and palette
treatment for the existing six navigation entries and corresponding section
headings. Preserve all current button text, `data-panel` values, IDs, and
control handlers. Ensure each icon is decorative (`aria-hidden="true"`,
`focusable="false"`) and labels continue providing the accessible name.

- [ ] **Step 3: Give toolbar/window controls accessible names and add favicon
      reference**

Ensure each icon-only toolbar/window-control button has a descriptive
`aria-label` consistent with its existing `title`; add a
`<link rel="icon" type="image/svg+xml" href="assets/angela-viewer-icon.svg">` in
the document head.

- [ ] **Step 4: Create a restrained palette-based SVG favicon**

Create `apps/web-live2d-viewer/assets/angela-viewer-icon.svg` as a simple,
original abstract mark using the approved rose/ivory/gold palette. Do not
present it as a canonical project logo or include the unapproved wheat/flower
reference.

- [ ] **Step 5: Apply only evidence-backed content corrections**

Where copy asserts unverified existing model identity or canon, replace it with
a concise status that matches the asset audit (identity/provenance/license not
verified). Do not change established Angela Core identity label or fabricate
model-specific claims.

- [ ] **Step 6: Verify HTML, paths, and responsive visual result**

Inspect the edited markup for unchanged panel IDs/labels and valid icon
accessibility; verify the favicon asset exists and the reference resolves. Open
the Viewer at desktop and narrow viewport sizes and confirm icons render
consistently without obscuring labels. Verify no Live2D model or texture files
changed.
