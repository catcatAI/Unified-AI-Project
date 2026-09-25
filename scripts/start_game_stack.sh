#!/usr/bin/env bash
# Angela in-game autonomy stack (local only, no cloud):
#   1. llama.cpp server :8080  (local LLM decider, Gemma 4 E2B Q4_0 GGUF)
#   2. run_angela.py          (agent loop + bridge :30003)
# Luanti server :30000 stays manual (flatpak/GUI varies per machine):
#   flatpak run org.luanti.luanti --server --gameid minetest_game \
#     --world /tmp/luanti_test --port 30000 \
#     --config ~/.var/app/org.luanti.luanti/config/luanti/minetest.conf
# Then join with any client; the agent pilots "AngelaBot".
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
MODEL="${GEMMA_MODEL:-$HOME/.cache/huggingface/hub/models--google--gemma-4-E2B-it-qat-q4_0-gguf/snapshots/675cff42a74c774d6cb76f76d8eacb49b48c9b93/gemma-4-E2B_q4_0-it.gguf}"
MODEL_ALIAS="gemma-4-E2B-it"

health() { curl -s --max-time 3 "$1" >/dev/null 2>&1; }

if [ ! -f "$MODEL" ]; then
  echo "Missing model: $MODEL"
  echo "Set GEMMA_MODEL to an existing Gemma 4 E2B GGUF path; automatic download is disabled."
  exit 1
fi

if ! health http://127.0.0.1:8080/v1/models; then
  echo "[1/2] starting llama.cpp server :8080 ..."
  "$PY" -m llama_cpp.server --model "$MODEL" --model_alias "$MODEL_ALIAS" \
    --host 127.0.0.1 --port 8080 \
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
