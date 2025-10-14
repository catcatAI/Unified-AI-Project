Preload script loading...
VM5:41 Error in preload script: Error: module not found: ./src/ipc-channels.js
    at preloadRequire (VM4 sandbox_bundle:2:82852)
    at <anonymous>:9:20
    at runPreloadScript (VM4 sandbox_bundle:2:83516)
    at VM4 sandbox_bundle:2:83813
    at VM4 sandbox_bundle:2:83968
    at ___electron_webpack_init__ (VM4 sandbox_bundle:2:83972)
    at VM4 sandbox_bundle:2:84095
(anonymous) @ VM5:41
VM5:45 IPC not available for channel 'save-state'
invoke @ VM5:45
VM5:45 IPC not available for channel 'api:atlassian-status'
invoke @ VM5:45
VM5:45 IPC not available for channel 'api:jira-projects'
invoke @ VM5:45
VM5:45 IPC not available for channel 'api:confluence-spaces'
invoke @ VM5:45
VM5:45 IPC not available for channel 'api:rovo-agents'
invoke @ VM5:45
VM5:45 IPC not available for channel 'api:rovo-tasks'
invoke @ VM5:45
VM5:45 IPC not available for channel 'save-state'
invoke @ VM5:45
renderer.js:254 Error loading Jira projects: TypeError: Cannot read properties of null (reading 'projects')
    at loadJiraProjects (renderer.js:251:89)
loadJiraProjects @ renderer.js:254
2VM5:45 IPC not available for channel 'save-state'
invoke @ VM5:45
renderer.js:266 Error loading Confluence spaces: TypeError: Cannot read properties of null (reading 'spaces')
    at loadConfluenceSpaces (renderer.js:263:91)
loadConfluenceSpaces @ renderer.js:266
2VM5:45 IPC not available for channel 'save-state'
invoke @ VM5:45
renderer.js:278 Error loading Rovo agents: TypeError: Cannot read properties of null (reading 'agents')
    at loadRovoAgents (renderer.js:275:85)
loadRovoAgents @ renderer.js:278
2VM5:45 IPC not available for channel 'save-state'
invoke @ VM5:45
renderer.js:290 Error loading Rovo tasks: TypeError: Cannot read properties of null (reading 'tasks')
    at loadRovoTasks (renderer.js:287:83)
loadRovoTasks @ renderer.js:290
2VM5:45 IPC not available for channel 'save-state'
invoke @ VM5:45

===

PS D:\Projects\Unified-AI-Project\apps\desktop-app> npm start

> desktop-app@1.0.0 start
> electron .


Main Process: Loaded backend API URL: http://localhost:8000
Main Process: .env file not found. Using default 'python'.
[7232:1014/072906.781:ERROR:CONSOLE(1)] "Request Autofill.enable failed. {"code":-32601,"message":"'Autofill.enable' wasn't found"}", source: devtools://devtools/bundled/core/protocol_client/protocol_client.js (1)

===

PS D:\Projects\Unified-AI-Project\apps\backend> python main.py
2025-10-14 07:31:52,655 - __main__ - INFO - 🚀 启动Level 5 AGI后端服务...
2025-10-14 07:31:52,655 - __main__ - INFO - 📋 配置: host=0.0.0.0, port=8000, reload=False
INFO:     Started server process [15852]
INFO:     Waiting for application startup.
2025-10-14 07:31:53,165 - main - INFO - 🚀 启动Level 5 AGI后端系统...
ERROR:    Traceback (most recent call last):
  File "C:\Users\catai\AppData\Local\Programs\Python\Python312\Lib\site-packages\starlette\routing.py", line 694, in lifespan
    async with self.lifespan_context(app) as maybe_state:
               ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\catai\AppData\Local\Programs\Python\Python312\Lib\contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\catai\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\routing.py", line 134, in merged_lifespan
    async with original_context(app) as maybe_original_state:
               ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\catai\AppData\Local\Programs\Python\Python312\Lib\contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "D:\Projects\Unified-AI-Project\apps\backend\main.py", line 53, in lifespan
    from src.core.sync.realtime_sync import sync_manager
  File "D:\Projects\Unified-AI-Project\apps\backend\src\core\sync\realtime_sync.py", line 15, in <module>
    import redis.asyncio as redis
ModuleNotFoundError: No module named 'redis'

ERROR:    Application startup failed. Exiting.
PS D:\Projects\Unified-AI-Project\apps\backend>

===

PS D:\Projects\Unified-AI-Project\apps\frontend-dashboard> npm run dev

> frontend-dashboard@0.1.0 dev
> nodemon --exec "npx tsx server.ts" --watch server.ts --watch src --ext ts,tsx,js,jsx

[nodemon] 3.1.10
[nodemon] to restart at any time, enter `rs`
[nodemon] watching path(s): server.ts src\**\*
[nodemon] watching extensions: ts,tsx,js,jsx
[nodemon] starting `npx tsx server.ts`
Found existing process with PID: 13108
Previous process 13108 may have already terminated
Saved current PID 19076 to D:\Projects\Unified-AI-Project\apps\frontend-dashboard\.port-manager.pid
   Disabled SWC as replacement for Babel because of custom Babel configuration "babel.config.js" https://nextjs.org/docs/messages/swc-disabled
> Ready on http://127.0.0.1:3000
> Socket.IO server running at ws://127.0.0.1:3000/api/socketio
> Backend API proxying to http://localhost:8000
Incoming request: GET /
Routing to Next.js: /
 ○ Compiling / ...
   Using external babel configuration from D:\Projects\Unified-AI-Project\apps\frontend-dashboard\babel.config.js
 ✓ Compiled / in 17.1s (1372 modules)
Incoming request: GET /_next/static/css/app/layout.css?v=1760398434306
Routing to Next.js: /_next/static/css/app/layout.css?v=1760398434306
Incoming request: GET /_next/static/chunks/webpack.js?v=1760398434306
Routing to Next.js: /_next/static/chunks/webpack.js?v=1760398434306
Incoming request: GET /_next/static/chunks/main-app.js?v=1760398434306
Routing to Next.js: /_next/static/chunks/main-app.js?v=1760398434306
Incoming request: GET /_next/static/chunks/app-pages-internals.js
Routing to Next.js: /_next/static/chunks/app-pages-internals.js
Incoming request: GET /_next/static/chunks/app/layout.js
Routing to Next.js: /_next/static/chunks/app/layout.js
Incoming request: GET /_next/static/chunks/app/page.js
Routing to Next.js: /_next/static/chunks/app/page.js
 GET / 200 in 22370ms
Incoming request: GET /_next/static/chunks/_app-pages-browser_node_modules_pnpm_next_15_3_5__babel_core_7_2_3a852f9b94ba7163c4aed37ce93d-ad8e0f.js
Routing to Next.js: /_next/static/chunks/_app-pages-browser_node_modules_pnpm_next_15_3_5__babel_core_7_2_3a852f9b94ba7163c4aed37ce93d-ad8e0f.js