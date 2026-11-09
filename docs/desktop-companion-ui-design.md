# Desktop Companion UI and Tray — Design Proposal

> Character identity baseline: `angela.core@1.0.0`; Lucifaella host edition: `angela.lucifaella@1.0.0`. See the character-system design spec for identity invariants, persona boundaries, and provenance policy.

## Intent

Make the transparent desktop companion feel character-first and calm while keeping chat discoverable, controls usable, and the app recoverable/configurable from the system tray.

## Goals

- Keep the character as the first and primary thing users see in the transparent desktop window.
- Present chat/history as a bottom drawer: expanded on first launch with a short invitation; after the user's first message, keep it open through Angela's first reply and collapse it only after an idle delay.
- In normal use, support configurable pointer-hover expand and pointer-leave delayed collapse. Hovering/focusing the drawer or typing must prevent accidental collapse; a visible chat toggle remains available.
- Preserve existing top `− □ ✕` controls, hidden until the pointer reaches the top area, styled consistently with the bottom drawer, and make each action operate on the correct window state.
- Provide settings for hover expansion and hover-leave collapse, persist the preferences, and apply them in the running renderer.
- Ensure the system tray has an app icon and usable menu for show/hide, settings/configuration, about, restart, and quit. Refreshing menu state must not leak tray instances; settings must open the intended settings page.
- Preserve the existing transparent, click-through character experience while keeping controls and the chat drawer interactive.

## Existing design worth preserving

- **Transparent, borderless desktop overlay:** the companion belongs on the desktop rather than inside a conventional app window. Keep the transparent canvas and frameless window as the foundation.
- **Character-first composition and separate interaction layer:** the character canvas remains visually unobstructed, while the click layer handles hit-testing. Preserve this separation when making controls interactive so UI changes do not break character rendering or click-through.
- **Hidden top controls and translucent treatment:** retain the existing `− □ ✕` controls, soft blur/gradient surfaces, and hover reveal. These already establish the right low-distraction desktop language; make their hit areas reliable rather than replacing them.
- **Bottom-anchored conversation history:** keep history and input together below the character. User/Angela messages already have distinct alignment and color treatment, timestamps, and gentle entry motion; preserve the conversational hierarchy while fixing state/visibility behavior.
- **Explicit health feedback:** keep the compact health indicator and meaningful online/offline state colors. The verbose CPU/LLM/service status panel should not dominate the idle desktop; preserve its information as an optional/revealable detail rather than removing useful diagnostics.
- **Settings grouped by task:** retain the existing category navigation (General, Appearance, Audio, Haptics, Network, LLM, Advanced, Help), descriptive helper text, and clear disabled/unavailable notes. Add the drawer behavior in the natural General/Window or Behavior area instead of inventing a separate settings system.
- **Recognizable Angela tray icon and concise system menu:** preserve the existing pink Angela icon assets and the conventional show/hide, settings, about, restart, and quit actions; make the same tray instance reliable and the commands actually reachable.
- **Truthful UI states:** continue distinguishing available controls from unavailable capabilities; do not make an inactive setting look functional merely for visual completeness.

## Character identity consistency

- Use `angela.core@1.0.0` as the shared family identity and keep product brand, family identity, user-selected instance name, and role edition as separate concepts.
- The first-contact host is Lucifaella (`angela.lucifaella@1.0.0`), an Angela edition and workshop 看板娘; after handover the user's named Angela remains the primary assistant.
- Preserve the existing character-first layout. Apply shared rose/ivory identity cues with restrained teal/gold accents only through established theme/config tokens; do not redesign the window or recolor third-party model textures.
- Existing static Gemini art and downloaded Live2D models remain exploratory until their identity match and reuse terms are recorded. Do not bundle assets with unclear redistribution terms.
- Persona descriptions and any quote examples are not UI default chat text. The normal AI response remains generated for the user's message.
- The wheat-ring/donut with a flower is an unadopted reference idea, not the Angela mark or app icon.

## Non-goals

- No visual redesign of Dashboard, Web Live2D Viewer, or Space Studio in this change.
- No new backend lifecycle controls: the Electron main process does not own the Python backend lifecycle.
- No unrelated settings cleanup or new chat features.
- No promise of platform-perfect tray behavior without running on each target OS.

## Approaches

1. **Minimal patch**: add hover chat and first-use behavior, then fix only the immediately apparent tray defects. Smallest change, but leaves interaction coverage gaps.
2. **Focused desktop workflow audit (recommended)**: validate window controls, drawer states, settings persistence/application, click-through boundaries, tray icon/menu/reopen flows, and packaged Live2D asset paths; repair reproducible issues within those areas. This matches the request to inspect and repair the whole desktop interaction while keeping scope bounded.
3. **Full frontend redesign**: rework the visual language and all frontend surfaces. Broader than requested and risks changing established products and behavior unnecessarily.

**Recommendation:** Approach 2, because the request explicitly includes the desktop interaction and system tray end to end, while leaving other frontends outside this change.

## Agreed direction and implementation calls

- The companion stays transparent, with the character visible on launch.
- Preserve the existing frameless overlay, layered character/click handling, hover-revealed translucent top controls, bottom conversation hierarchy, concise health signal, grouped settings navigation, and Angela tray branding described above; improve reliability without replacing these established patterns.
- Keep detailed system metrics available without leaving a large persistent dashboard over the character by default.
- First-use chat starts expanded and stays available through the first assistant response; it then collapses after a short idle delay.
- Normal-use hover reveal/collapse is controlled by settings and uses a delay so moving from the character into the drawer does not close it prematurely.
- Top window buttons and bottom chat controls share a restrained translucent visual treatment; the top controls appear on hover.
- Use Electron's existing settings JSON/IPC path as the source of persisted preferences.
- Keep one tray object for the app lifetime and update its context menu rather than recreate it for each menu refresh.
- Treat a missing or unpackaged Live2D SDK dependency as a verified limitation/defect to resolve only if the existing SDK assets and license allow an in-scope fix; do not silently substitute a different model/runtime.

## Acceptance checks

- On a clean first-use state, the transparent character view opens with the chat drawer expanded and a concise prompt; first user submission does not hide the conversation before the first assistant reply, and the drawer collapses only after the configured idle interval.
- On later launches, hover behavior follows the saved preferences; pointer movement into the drawer/input and keyboard focus do not trigger premature collapse. Manual toggle continues to work.
- Top minimize/maximize/close controls remain discoverable on hover and perform their labeled action. Close follows the app's tray-resident behavior.
- The settings UI loads and saves the hover preferences through SettingsManager/IPC, and changes affect the live main window.
- Tray initialization resolves a valid icon, repeated menu updates retain one tray icon, menu actions open/focus/hide/settings/restart/quit as labeled, and closing the main view can be reversed from the tray.
- Transparent areas remain click-through while visible controls/chat remain interactive.
- Referenced local UI scripts/assets exist; desktop JavaScript syntax checks pass; focused tests/checks cover changed interaction and tray behavior. Platform-specific runtime verification is reported separately when unavailable.

## Builder choices left open

- Exact idle delay and drawer animation timing should follow existing motion conventions; choose conservative short defaults and keep the idle delay internal unless the current settings UI naturally supports it.
- First-use state should use the existing settings store, with a backward-compatible default for existing installations.
- Preserve existing icon assets and app behavior where valid; fix path/package inclusion rather than inventing new branding.
