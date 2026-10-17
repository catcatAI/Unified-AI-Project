# Luanti (Minetest) 遊戲模組 — agent_poller

伺服端 mod：每 **2.0 s** 向 Python 橋接（預設 `http://localhost:30003`）`POST /api/poll`
取指令並執行（goto / dig / place / craft / look_at / scan / give），把玩家聊天轉送
`POST /api/chat` 給 Angela 代理。目標玩家 `AngelaBot`（不存在時取第一個在線玩家）。
Python 側由 `scripts/run_luanti_agent.py` 啟動（獨立進程，**不是**統一啟動器
`scripts/run_angela.py`——後者不起 :30003，見 `docs/INVOCATION_MATRIX.md`）。

## 完整安裝四前置（缺一不可）

> ⚠️ **前置 3 最易漏**：沒有它 `minetest.request_http_api()` 返回 `nil`，
> `init.lua` 第 4-7 行直接 `return`——mod 靜默失效（只在伺服器 log 留一行
> `[agent_poller] HTTP API not available!`，世界照常運行、看似一切正常）。

### 1) 把 mod 放進世界 mods 目錄

```bash
# 方式 A：本世界（world 目錄旁）
ln -s "$(pwd)/apps/luanti-mods/agent_poller" /tmp/luanti_test/mods/agent_poller

# 方式 B：全域（所有世界可見）
ln -s "$(pwd)/apps/luanti-mods/agent_poller" ~/.minetest/mods/agent_poller
```

### 2) 啟用 mod：世界目錄的 `world.mt`

```ini
load_mod_agent_poller = true
```

### 3) 授予 HTTP 權限：`minetest.conf`（**必做**）

```ini
secure.http_mods = agent_poller
```

flatpak 預設設定檔路徑：
`~/.var/app/org.luanti.luanti/config/luanti/minetest.conf`

可選同檔設定：

```ini
agent_poller_bridge_url = http://localhost:30003   # 橋接位址（LAN 改 IP）
agent_poller_allow_give = false                    # 測試後門 /give，預設關
```

### 4) 啟動 Python 橋接（:30003）

```bash
# 一鍵（含本地 llama.cpp :8080；step2 即本代理）
./scripts/start_game_stack.sh

# 或只啟動代理
.venv/bin/python scripts/run_luanti_agent.py
```

驗證橋接：`curl http://127.0.0.1:30003/health` →
`{"status":"ok","has_state":false,...}`

## 啟動伺服器

```bash
flatpak run org.luanti.luanti --server --gameid minetest_game \
  --world /tmp/luanti_test --port 30000 \
  --config ~/.var/app/org.luanti.luanti/config/luanti/minetest.conf
```

（服務端保持手工啟動——見 `scripts/start_game_stack.sh` 檔頭註釋。）

## 橋接端點（Python 側 `integrations/luanti_polling_bridge.py`）

| 端點 | 方向 | 用途 |
|---|---|---|
| `GET /health` | 探活 | 探活/啟動驗收（`{status:"ok",...}`） |
| `POST /api/poll` | mod → 橋接 | 每 2s 取一行待執行指令 |
| `GET /api/state` | 代理查詢 | 遊戲世界狀態快照 |
| `POST /api/action` | 代理寫入 | 排隊動作（下一 tick 由 mod 執行） |
| `POST /api/chat` | mod → 橋接 | 玩家聊天轉發（Angela 回覆入隊） |
| `GET /api/chat` | 代理讀取 | 讀取待發聊天訊息 |

## 驗證 mod 生效

1. 伺服器 log 出現 poller 相關輸出（HTTP API 不可用時為
   `[agent_poller] HTTP API not available!`——即前置 3 未做）。
2. `curl -s http://127.0.0.1:30003/health` 顯示 `pending_actions` 隨代理活動變化。
3. 遊戲內與 `AngelaBot` 聊天，橋接 log 出現 chat 轉發。

## 侷限與注意

- **無 Lua 測試**：Python 側僅 `tests/integrations/test_luanti_chat_dispatch.py`
  （chat 分發）；mod 行為靠上述手動驗證清單。
- `POLL_INTERVAL = 2.0 s`；代理側視覺輪詢另計——「20 FPS」目標未達
  （`docs/03-technical-architecture/GAME_AI_IMPLEMENTATION_PLAN.md` §10）。
- 橋接與 mod 都是**本機/內網**設計：橋接綁 `0.0.0.0:30003`（nosec B104），
  勿暴露公網。
