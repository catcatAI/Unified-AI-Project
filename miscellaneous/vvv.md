Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.

Install the latest PowerShell for new features and improvements! https://aka.ms/PSWindows

PS D:\Projects\Unified-AI-Project> pnpm install
Scope: all 6 workspace projects
Lockfile is up to date, resolution step is skipped
Already up to date
Done in 14.1s using pnpm v10.18.2
PS D:\Projects\Unified-AI-Project> cd apps/backend
PS D:\Projects\Unified-AI-Project\apps\backend> python main.py
2025-10-13 19:44:27,370 - __main__ - INFO - 🚀 启动Level 5 AGI后端服务...
2025-10-13 19:44:27,379 - __main__ - INFO - 📋 配置: host=0.0.0.0, port=8000, reload=False
INFO:     Started server process [3384]
INFO:     Waiting for application startup.
2025-10-13 19:44:28,519 - main - INFO - 🚀 启动Level 5 AGI后端系统...
2025-10-13 19:44:28,523 - src.core.managers.system_manager - INFO - 初始化系统管理器...
2025-10-13 19:44:28,525 - src.core.managers.system_manager - INFO - 系统管理器初始化完成
2025-10-13 19:44:28,528 - main - INFO - 📋 系统配置加载完成: Unified AI
2025-10-13 19:44:28,530 - main - INFO - 🧠 初始化Level 5 AGI核心组件...
2025-10-13 19:44:28,536 - src.core.config.level5_config - INFO - 🚀 Level 5 AGI 系统监控已启动
 # ctrl+c 無法終止
===

Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.

Install the latest PowerShell for new features and improvements! https://aka.ms/PSWindows

PS D:\Projects\Unified-AI-Project> cd apps/desktop-app
PS D:\Projects\Unified-AI-Project\apps\desktop-app> npm start

> desktop-app@1.0.0 start
> electron .


Main Process: Loaded backend API URL: http://localhost:8000
Main Process: .env file not found. Using default 'python'.
[14704:1013/194600.562:ERROR:CONSOLE(1)] "Request Autofill.enable failed. {"code":-32601,"message":"'Autofill.enable' wasn't found"}", source: devtools://devtools/bundled/core/protocol_client/protocol_client.js (1)

===

Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.

Install the latest PowerShell for new features and improvements! https://aka.ms/PSWindows

PS D:\Projects\Unified-AI-Project> cd apps/frontend-dashboard
PS D:\Projects\Unified-AI-Project\apps\frontend-dashboard> npm run dev

> frontend-dashboard@0.1.0 dev
> nodemon --exec "npx tsx server.ts" --watch server.ts --watch src --ext ts,tsx,js,jsx

[nodemon] 3.1.10
[nodemon] to restart at any time, enter `rs`
[nodemon] watching path(s): server.ts src\**\*
[nodemon] watching extensions: ts,tsx,js,jsx
[nodemon] starting `npx tsx server.ts`
Found existing process with PID: 13680
Previous process 13680 may have already terminated
Saved current PID 9220 to D:\Projects\Unified-AI-Project\apps\frontend-dashboard\.port-manager.pid
   Disabled SWC as replacement for Babel because of custom Babel configuration "babel.config.js" https://nextjs.org/docs/messages/swc-disabled
> Ready on http://127.0.0.1:3000
> Socket.IO server running at ws://127.0.0.1:3000/api/socketio
> Backend API proxying to http://localhost:8000
Incoming request: GET /
Routing to Next.js: /
 ○ Compiling / ...
   Using external babel configuration from D:\Projects\Unified-AI-Project\apps\frontend-dashboard\babel.config.js
Incoming request: GET /
Routing to Next.js: /
 ✓ Compiled / in 234s (1375 modules) # 時間長到我懷疑開不了
 ⨯ Error: @prisma/client did not initialize yet. Please run "prisma generate" and try to import it again.
    at eval (src\lib\data-archive.ts:5:15)
    at (ssr)/./src/lib/data-archive.ts (D:\Projects\Unified-AI-Project\apps\frontend-dashboard\.next\server\app\page.js:577:1)
    at __webpack_require__ (D:\Projects\Unified-AI-Project\apps\frontend-dashboard\.next\server\webpack-runtime.js:33:42)
    at eval (webpack-internal:///(ssr)/./src/hooks/use-api-data.ts:24:75)
    at (ssr)/./src/hooks/use-api-data.ts (D:\Projects\Unified-AI-Project\apps\frontend-dashboard\.next\server\app\page.js:533:1)
    at __webpack_require__ (D:\Projects\Unified-AI-Project\apps\frontend-dashboard\.next\server\webpack-runtime.js:33:42)
    at eval (webpack-internal:///(ssr)/./src/components/ai-dashboard/tabs/image-generation.tsx:9:77)
    at (ssr)/./src/components/ai-dashboard/tabs/image-generation.tsx (D:\Projects\Unified-AI-Project\apps\frontend-dashboard\.next\server\app\page.js:456:1)
    at __webpack_require__ (D:\Projects\Unified-AI-Project\apps\frontend-dashboard\.next\server\webpack-runtime.js:33:42)
    at eval (webpack-internal:///(ssr)/./src/components/ai-dashboard/dashboard-layout.tsx:8:80)
    at (ssr)/./src/components/ai-dashboard/dashboard-layout.tsx (D:\Projects\Unified-AI-Project\apps\frontend-dashboard\.next\server\app\page.js:357:1)
    at Object.__webpack_require__ [as require] (D:\Projects\Unified-AI-Project\apps\frontend-dashboard\.next\server\webpack-runtime.js:33:42)
  3 |
  4 | // Initialize Prisma client
> 5 | const prisma = new PrismaClient();
    |               ^
  6 |
  7 | // Types for archive entries
  8 | export interface ArchiveEntry { {
  digest: '2160047183'
}
 ⨯ Error: @prisma/client did not initialize yet. Please run "prisma generate" and try to import it again.
    at eval (src\lib\data-archive.ts:5:15)
    at (ssr)/./src/lib/data-archive.ts (D:\Projects\Unified-AI-Project\apps\frontend-dashboard\.next\server\app\page.js:577:1)
    at __webpack_require__ (D:\Projects\Unified-AI-Project\apps\frontend-dashboard\.next\server\webpack-runtime.js:33:42)
    at eval (webpack-internal:///(ssr)/./src/hooks/use-api-data.ts:24:75)
    at (ssr)/./src/hooks/use-api-data.ts (D:\Projects\Unified-AI-Project\apps\frontend-dashboard\.next\server\app\page.js:533:1)
    at __webpack_require__ (D:\Projects\Unified-AI-Project\apps\frontend-dashboard\.next\server\webpack-runtime.js:33:42)
    at eval (webpack-internal:///(ssr)/./src/components/ai-dashboard/tabs/image-generation.tsx:9:77)
    at (ssr)/./src/components/ai-dashboard/tabs/image-generation.tsx (D:\Projects\Unified-AI-Project\apps\frontend-dashboard\.next\server\app\page.js:456:1)
    at __webpack_require__ (D:\Projects\Unified-AI-Project\apps\frontend-dashboard\.next\server\webpack-runtime.js:33:42)
    at eval (webpack-internal:///(ssr)/./src/components/ai-dashboard/dashboard-layout.tsx:8:80)
    at (ssr)/./src/components/ai-dashboard/dashboard-layout.tsx (D:\Projects\Unified-AI-Project\apps\frontend-dashboard\.next\server\app\page.js:357:1)
    at Object.__webpack_require__ [as require] (D:\Projects\Unified-AI-Project\apps\frontend-dashboard\.next\server\webpack-runtime.js:33:42)
  3 |
  4 | // Initialize Prisma client
> 5 | const prisma = new PrismaClient();
    |               ^
  6 |
  7 | // Types for archive entries
  8 | export interface ArchiveEntry { {
  digest: '2160047183'
}
 GET / 500 in 44893ms
Incoming request: GET /_next/static/css/app/layout.css?v=1760356596266
Routing to Next.js: /_next/static/css/app/layout.css?v=1760356596266
Incoming request: GET /_next/static/chunks/webpack.js
Routing to Next.js: /_next/static/chunks/webpack.js
Incoming request: GET /_next/static/chunks/main-app.js
Routing to Next.js: /_next/static/chunks/main-app.js
Incoming request: GET /_next/static/chunks/app-pages-internals.js
Routing to Next.js: /_next/static/chunks/app-pages-internals.js
Incoming request: GET /_next/static/chunks/app/layout.js
Routing to Next.js: /_next/static/chunks/app/layout.js
Incoming request: GET /_next/static/chunks/app/page.js
Routing to Next.js: /_next/static/chunks/app/page.js
Incoming request: GET /_next/static/chunks/_app-pages-browser_node_modules_pnpm_next_15_3_5__babel_core_7_2_3a852f9b94ba7163c4aed37ce93d-ad8e0f.js
Routing to Next.js: /_next/static/chunks/_app-pages-browser_node_modules_pnpm_next_15_3_5__babel_core_7_2_3a852f9b94ba7163c4aed37ce93d-ad8e0f.js
Incoming request: POST /__nextjs_original-stack-frames
Routing to Next.js: /__nextjs_original-stack-frames
Incoming request: POST /__nextjs_original-stack-frames
Routing to Next.js: /__nextjs_original-stack-frames
Incoming request: GET /__nextjs_font/geist-latin.woff2
Routing to Next.js: /__nextjs_font/geist-latin.woff2
Incoming request: GET /__nextjs_font/geist-mono-latin.woff2
Routing to Next.js: /__nextjs_font/geist-mono-latin.woff2

===


連線失敗

Firefox 無法與伺服器 localhost:8000 建立連線。

    該網站可能暫時無法使用或太過忙碌，請過幾分鐘後再試試。
    若無法載入任何網站，請檢查您的網路連線狀態。
    若電腦或網路被防火牆或 Proxy 保護，請確定 Firefox 被允許存取網路。

===


PrismaClient@webpack-internal:///(app-pages-browser)/../../node_modules/.pnpm/@prisma+client@6.13.0_prism_88360a1565554df38704add3bd67e4b4/node_modules/.prisma/client/index-browser.js:49:11
@webpack-internal:///(app-pages-browser)/./src/lib/data-archive.ts:11:16
(app-pages-browser)/./src/lib/data-archive.ts@http://localhost:3000/_next/static/chunks/app/page.js:2997:1
options.factory@http://localhost:3000/_next/static/chunks/webpack.js:712:31
__webpack_require__@http://localhost:3000/_next/static/chunks/webpack.js:37:33
fn@http://localhost:3000/_next/static/chunks/webpack.js:369:21
@webpack-internal:///(app-pages-browser)/./src/hooks/use-api-data.ts:24:94
(app-pages-browser)/./src/hooks/use-api-data.ts@http://localhost:3000/_next/static/chunks/app/page.js:2953:1
options.factory@http://localhost:3000/_next/static/chunks/webpack.js:712:31
__webpack_require__@http://localhost:3000/_next/static/chunks/webpack.js:37:33
fn@http://localhost:3000/_next/static/chunks/webpack.js:369:21
@webpack-internal:///(app-pages-browser)/./src/components/ai-dashboard/tabs/image-generation.tsx:9:96
(app-pages-browser)/./src/components/ai-dashboard/tabs/image-generation.tsx@http://localhost:3000/_next/static/chunks/app/page.js:2898:1
options.factory@http://localhost:3000/_next/static/chunks/webpack.js:712:31
__webpack_require__@http://localhost:3000/_next/static/chunks/webpack.js:37:33
fn@http://localhost:3000/_next/static/chunks/webpack.js:369:21
@webpack-internal:///(app-pages-browser)/./src/components/ai-dashboard/dashboard-layout.tsx:8:99
(app-pages-browser)/./src/components/ai-dashboard/dashboard-layout.tsx@http://localhost:3000/_next/static/chunks/app/page.js:2799:1
options.factory@http://localhost:3000/_next/static/chunks/webpack.js:712:31
__webpack_require__@http://localhost:3000/_next/static/chunks/webpack.js:37:33
fn@http://localhost:3000/_next/static/chunks/webpack.js:369:21
requireModule@webpack-internal:///(app-pages-browser)/../../node_modules/.pnpm/next@15.3.5_@babel+core@7.2_3a852f9b94ba7163c4aed37ce93de657/node_modules/next/dist/compiled/react-server-dom-webpack/cjs/react-server-dom-webpack-client.browser.development.js:121:46
initializeModuleChunk@webpack-internal:///(app-pages-browser)/../../node_modules/.pnpm/next@15.3.5_@babel+core@7.2_3a852f9b94ba7163c4aed37ce93de657/node_modules/next/dist/compiled/react-server-dom-webpack/cjs/react-server-dom-webpack-client.browser.development.js:1078:34
resolveModuleChunk@webpack-internal:///(app-pages-browser)/../../node_modules/.pnpm/next@15.3.5_@babel+core@7.2_3a852f9b94ba7163c4aed37ce93de657/node_modules/next/dist/compiled/react-server-dom-webpack/cjs/react-server-dom-webpack-client.browser.development.js:1042:12
resolveModule/<@webpack-internal:///(app-pages-browser)/../../node_modules/.pnpm/next@15.3.5_@babel+core@7.2_3a852f9b94ba7163c4aed37ce93de657/node_modules/next/dist/compiled/react-server-dom-webpack/cjs/react-server-dom-webpack-client.browser.development.js:1636:20

Home@rsc://React/Server/webpack-internal:///(rsc)/./src/app/page.tsx?3:14:80