# @angela/shared-js

Shared JavaScript modules used by `apps/desktop-app/` (Electron) and `apps/web-live2d-viewer/`. 33 files organized under `js/`.

## Usage

Load modules via `<script>` tag in dependency order:

```html
<script src="../../packages/shared-js/js/index.js"></script>
<script src="../../packages/shared-js/js/api-client.js"></script>
<script src="../../packages/shared-js/js/state-matrix.js"></script>
<!-- ... other modules -->
```

Or reference via the monorepo path from any app in `apps/`:

```js
// From desktop-app or web-live2d-viewer
const root = '../../packages/shared-js/js/'
```

## File Index (33 files)

| File | Purpose |
|------|---------|
| `index.js` | Entry point, platform detection (`AngelaPlatform`) |
| `api-client.js` | Backend API client |
| `backend-websocket.js` | WebSocket connection to backend |
| `state-matrix.js` | State matrix client (6D αβγδεθ) |
| `unified-display-matrix.js` | Display matrix management |
| `live2d-manager.js` | Live2D model lifecycle |
| `live2d-cubism-wrapper.js` | Cubism SDK wrapper |
| `simple-live2d-loader.js` | Lightweight Live2D loader |
| `angela-character-config.js` | Character configuration |
| `angela-character-images-config.js` | Character image assets config |
| `dialogue-ui.js` | Chat/dialogue UI components |
| `input-handler.js` | User input handling |
| `audio-handler.js` | Audio playback |
| `haptic-handler.js` | Haptic feedback |
| `character-touch-detector.js` | Touch/drag detection on character |
| `theme-manager.js` | Light/dark theme switching |
| `i18n.js` | Internationalization (locale strings) |
| `settings.js` | User settings persistence |
| `user-manager.js` | User profile management |
| `tray-manager.js` | System tray (Electron) |
| `plugin-manager.js` | Plugin loading |
| `performance-manager.js` | FPS/memory monitoring |
| `precision-manager.js` | Precision tuning |
| `maturity-tracker.js` | Content maturity tracking |
| `availability-manager.js` | Service availability checks |
| `security-utils.js` | Security utilities |
| `error-handler.js` | Error display/logging |
| `logger.js` | Console logging wrapper |
| `frontend-utils.js` | General DOM/UI utilities |
| `layer-renderer.js` | Z-layer rendering |
| `z-index-manager.js` | Z-index stacking |
| `wallpaper-handler.js` | Wallpaper/canvas background |
| `app.js` | App shell / shared initialization |

## Dependencies

Runtime: none (vanilla ES6, loaded as `<script>` tags).  
Test: `echo "No tests yet"` — see `package.json`.
