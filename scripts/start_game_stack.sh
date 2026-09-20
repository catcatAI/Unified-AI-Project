#!/usr/bin/env bash
# Angela in-game autonomy stack (local only, no cloud):
#   1. llama.cpp server :8080  (local LLM decider, Qwen2.5-1.5B-Q4 gguf)
#   2. run_angela.py          (agent loop + bridge :30003)
# Luanti server :30000 stays manual (flatpak/GUI varies per machine):
#   flatpak run org.luanti.luanti --server --gameid minetest_game \
#     --world /tmp/luanti_test --port 30000 \
#     --config ~/.var/app/org.luanti.luanti/config/luanti/minetest.conf
# Then join with any client; the agent pilots "AngelaBot".
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
MODEL="$ROOT/data/models/qwen2.5-1.5b-instruct-q4_k_m.gguf"

health() { curl -s --max-time 3 "$1" >/dev/null 2>&1; }

if [ ! -f "$MODEL" ]; then
  echo "Missing model: $MODEL"
  echo "Download: curl -L -o $MODEL https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
  exit 1
fi

if ! health http://127.0.0.1:8080/v1/models; then
  echo "[1/2] starting llama.cpp server :8080 ..."
  "$PY" -m llama_cpp.server --model "$MODEL" --host 127.0.0.1 --port 8080 \
    --n_ctx 4096 --n_threads 6 >/tmp/llama-server.log 2>&1 &
  for _ in $(seq 1 30); do
    health http://127.0.0.1:8080/v1/models && break
    sleep 2
  done
  health http://127.0.0.1:8080/v1/models || { echo "llama server failed (see /tmp/llama-server.log)"; exit 1; }
else
  echo "[1/2] llama.cpp server already up"
fi

if ! health http://127.0.0.1:30003/health; then
  echo "[2/2] starting Angela agent (bridge :30003) ..."
  (cd "$ROOT" && "$PY" run_angela.py >/tmp/angela.log 2>&1 &)
  sleep 12
  health http://127.0.0.1:30003/health || { echo "agent failed (see /tmp/angela.log)"; exit 1; }
else
  echo "[2/2] agent bridge already up"
fi

echo "STACK UP: llm :8080, bridge :30003. Start the Luanti server, join, and talk to Angela in game chat."
