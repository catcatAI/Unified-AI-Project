# Web Live2D Viewer Icons and Content Consistency — Design

**Date:** 2026-11-10  
**Status:** Awaiting user approval before implementation

## Intent and goals

Bring the Web Live2D Viewer’s existing navigation/title iconography into a
consistent style and correct content that conflicts with documented Angela
identity. Add a small browser-tab favicon using the project’s existing visual
identity cues. The aim is to stop presenting arbitrary current UI choices as
established project canon.

## Non-goals and anti-goals

- Do not alter, replace, or reconfigure Live2D models, textures, rigs, or
  runtime behavior.
- Do not make the generated PicLumen concept art part of the Viewer interface.
- Do not adopt the unapproved wheat-ring/flower idea as a brand mark.
- Do not change uncertain persona/runtime claims or fabricate identity details;
  preserve or clearly label material whose status is not established.
- Do not introduce icon/font dependencies or perform unrelated refactors.

## Approaches considered

1. **Focused consistency pass (recommended):** unify existing Viewer navigation
   and heading icons, add a favicon derived from the already documented Angela
   palette/identity, and correct only content conflicts supported by project
   documentation. Keep unknowns unchanged or explicitly provisional. This
   addresses the user’s stated icon and content concerns while limiting scope.
2. **Icons only:** update iconography and favicon but leave content untouched.
   Lower risk, but does not address the explicit request to correct unsuitable
   content.
3. **Broad Viewer redesign/content rewrite:** audit and rewrite the whole
   interface. This risks inventing decisions and exceeds the evidence-backed
   scope.

## Constraints and implementation calls

- Target `apps/web-live2d-viewer` and follow its existing plain HTML/CSS
  approach.
- Use only existing palette cues: rose `#E88DB8`, blue `#69A9E8`, ivory
  `#FFF8F0`, teal `#4D9A91`, gold `#C9A44C`.
- Replace emoji icons with simple inline SVG or CSS-drawn icons consistent in
  size and stroke/fill; keep labels and accessible names intact.
- Use a small inline/vector favicon or existing project-owned mark if one is
  clearly suitable; do not create a new canonical logo.
- Correct content only where current authoritative project documentation
  provides a direct answer. Leave the Live2D model’s identity and redistribution
  rights explicitly unverified.
- Keep the new PicLumen image as a separate exploratory asset; it is not part of
  this UI change.

## Verification

Review the changed HTML/CSS for preserved navigation labels and accessible
names, validate favicon references/asset paths and markup, and inspect the
rendered Viewer once in a browser. No model replacement or broad test suite is
in scope.
