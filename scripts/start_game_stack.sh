#!/usr/bin/env bash
# Angela game stack — three independently selectable segments
# (GAME_SUBSYSTEM_AUDIT_AND_AXIS_ENGINE_PLAN §八 執行順序 5):
#   --backend   unified launcher scripts/run_angela.py
#               (backend API :8000 + desktop app)
#   --agent     llama.cpp server :8080 (local LLM decider, Gemma 4 E2B Q4_0
#               GGUF) + run_luanti_agent.py (angela_agent loop +
#               PollingBridge :30003)
#   --luanti    Luanti game server :30000 (flatpak server; GUI variants
#               stay manual)
# NOTE: the unified launcher scripts/run_angela.py does NOT bind :30003 —
# the game agent is a separate process (docs/INVOCATION_MATRIX.md).
# The Luanti mod needs FOUR prerequisites incl. `secure.http_mods =
# agent_poller` in that minetest.conf — see apps/luanti-mods/README.md
# (without it the mod returns early and the stack looks fine but the
# bridge is never polled). Then join with any client; the agent pilots
# "AngelaBot".
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
MODEL="${GEMMA_MODEL:-${HF_HUB_CACHE:-$HOME/.cache/huggingface/hub}/models--google--gemma-4-E2B-it-qat-q4_0-gguf/snapshots/675cff42a74c774d6cb76f76d8eacb49b48c9b93/gemma-4-E2B_q4_0-it.gguf}"
MODEL_ALIAS="gemma-4-E2B-it"
LUANTI_WORLD="${LUANTI_WORLD:-/tmp/luanti_test}"

health() { curl -s --max-time 3 "$1" >/dev/null 2>&1; }
tcp_up() { timeout 1 bash -c "exec 3<>/dev/tcp/127.0.0.1/$1" 2>/dev/null; }

usage() {
  cat <<'EOF'
Usage: start_game_stack.sh SEGMENT [SEGMENT ...]
  --backend   backend API :8000 + desktop (scripts/run_angela.py)
  --agent     llama.cpp :8080 + Angela game agent (PollingBridge :30003)
  --luanti    Luanti server :30000 (flatpak; four mod prerequisites in
              apps/luanti-mods/README.md)
Segments are independent and combinable, e.g.:
  start_game_stack.sh --agent --luanti
EOF
}

start_backend() {
  if health http://127.0.0.1:8000/api/v1/health; then
    echo "[backend] API :8000 already up"
    return 0
  fi
  echo "[backend] starting unified launcher (API :8000 + desktop) ..."
  (cd "$ROOT" && "$PY" "$ROOT/scripts/run_angela.py" >/tmp/angela_backend.log 2>&1 &)
  for _ in $(seq 1 30); do
    health http://127.0.0.1:8000/api/v1/health && break
    sleep 2
  done
  health http://127.0.0.1:8000/api/v1/health || {
    echo "backend failed (see /tmp/angela_backend.log)"
    return 1
  }
}

start_agent() {
  if [ ! -f "$MODEL" ]; then
    echo "Missing model: $MODEL"
    echo "Set GEMMA_MODEL to an existing Gemma 4 E2B GGUF path; automatic download is disabled."
    return 1
  fi
  if ! health http://127.0.0.1:8080/v1/models; then
    echo "[agent] starting llama.cpp server :8080 ..."
    "$PY" -m llama_cpp.server --model "$MODEL" --model_alias "$MODEL_ALIAS" \
      --host 127.0.0.1 --port 8080 \
      --n_ctx 4096 --n_threads 6 >/tmp/llama-server.log 2>&1 &
    for _ in $(seq 1 30); do
      health http://127.0.0.1:8080/v1/models && break
      sleep 2
    done
    health http://127.0.0.1:8080/v1/models || {
      echo "llama server failed (see /tmp/llama-server.log)"
      return 1
    }
  else
    echo "[agent] llama.cpp server already up"
  fi
  if ! health http://127.0.0.1:30003/health; then
    echo "[agent] starting Angela game agent (PollingBridge :30003) ..."
    (cd "$ROOT" && "$PY" "$ROOT/scripts/run_luanti_agent.py" >/tmp/angela.log 2>&1 &)
    sleep 12
    health http://127.0.0.1:30003/health || {
      echo "agent failed (see /tmp/angela.log)"
      return 1
    }
  else
    echo "[agent] agent bridge already up"
  fi
}

start_luanti() {
  if tcp_up 30000; then
    echo "[luanti] server :30000 already up"
    return 0
  fi
  if ! command -v flatpak >/dev/null 2>&1; then
    echo "flatpak not found — Luanti segment unavailable (see apps/luanti-mods/README.md)"
    return 1
  fi
  echo "[luanti] starting flatpak Luanti server :30000 (log: /tmp/luanti-server.log) ..."
  mkdir -p "$LUANTI_WORLD"
  flatpak run org.luanti.luanti --server --gameid minetest_game \
    --world "$LUANTI_WORLD" --port 30000 \
    --config "$HOME/.var/app/org.luanti.luanti/config/luanti/minetest.conf" \
    >/tmp/luanti-server.log 2>&1 &
  for _ in $(seq 1 15); do
    tcp_up 30000 && break
    sleep 2
  done
  tcp_up 30000 || {
    echo "Luanti failed (see /tmp/luanti-server.log; four mod prerequisites in apps/luanti-mods/README.md)"
    return 1
  }
}

if [ $# -eq 0 ]; then
  usage >&2
  exit 2
fi

for arg in "$@"; do
  case "$arg" in
    --backend | --agent | --luanti) ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "unknown segment: $arg" >&2
      usage >&2
      exit 2
      ;;
  esac
done

status=0
endpoints=""
luanti_selected=0
case " $* " in *" --backend "*)
  start_backend || status=1
  endpoints="$endpoints, backend :8000"
  ;;
esac
case " $* " in *" --agent "*)
  start_agent || status=1
  endpoints="$endpoints, llm :8080, bridge :30003"
  ;;
esac
case " $* " in *" --luanti "*)
  luanti_selected=1
  start_luanti || status=1
  endpoints="$endpoints, luanti :30000"
  ;;
esac

[ "$status" -ne 0 ] && exit 1
if [ "$luanti_selected" = "1" ]; then
  echo "STACK UP:${endpoints#, }. Join with any client and talk to Angela in game chat."
else
  echo "STACK UP:${endpoints#, }. Start the Luanti server (flatpak / --luanti), join, and talk to Angela in game chat."
fi
