/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * main — three roles on one stage: roster, speech, visibility, camera, recording.
 *
 * No framework, no build step: serve the repo root and open /apps/space-studio/.
 */

import { drawStage } from "./renderer.js";
import { resolveCamera } from "./camera.js";
import { SpacePort } from "./space_port.js";
import { cycleTint, SLOTS } from "./wardrobe.js";
import { isRecordingSupported, startRecording } from "./recorder.js";
import { scriptedBeat, spawnRoster } from "./roster.js";
import { rendererLabel } from "./live2d.js";
import { applySnapshot } from "./snapshot_sync.js";
import { createSpaceSocket } from "./ws_client.js";

const DATA = {
  room: "../../space/rooms/studio_a.json",
  roster: "../../space/roles.json",
  motions: "../../space/motions/index.json",
};

const AVATARS = {
  angela_base: "../../space/avatars/angela_base.json",
  gemma_b: "../../space/avatars/gemma_b.json",
  qwen_c: "../../space/avatars/qwen_c.json",
};

async function loadJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

const canvas = document.getElementById("stage");
const ctx = canvas.getContext("2d");
const statusEl = document.getElementById("status");
const panel = document.getElementById("panel");

let port;
let camera = resolveCamera("medium");
let recording = null;
let selectedRole = "main";
let lastFrame = performance.now();
let timeMs = 0;
let stopBeat = null;
let modeLabel = "本機模式";
let socket = null;

const viewport = () => ({ width: canvas.width, height: canvas.height, worldWidth: 16, worldHeight: 9 });
const setStatus = (text) => {
  statusEl.textContent = modeLabel ? `${text}　｜　${modeLabel}` : text;
};

function setMode(status) {
  const labels = {
    connected: "後端已連線（狀態同步）",
    closed: "連線中斷（本機模式）",
    error: "連線失敗（本機模式）",
    unsupported: "此瀏覽器沒有 WebSocket（本機模式）",
    idle: "本機模式",
  };
  modeLabel = labels[status] ?? "本機模式";
}

function frame(now) {
  const dt = Math.min(64, now - lastFrame);
  lastFrame = now;
  timeMs += dt;
  port.tick(dt);
  drawStage(ctx, {
    room: port.room,
    actors: [...port.actors.values()],
    camera,
    viewport: viewport(),
    timeMs,
  });
  requestAnimationFrame(frame);
}

function button(parent, label, onClick, className = "") {
  const el = document.createElement("button");
  el.textContent = label;
  el.className = className;
  el.addEventListener("click", onClick);
  parent.appendChild(el);
  return el;
}

function section(title) {
  const el = document.createElement("div");
  el.className = "section";
  const h = document.createElement("h3");
  h.textContent = title;
  el.appendChild(h);
  panel.appendChild(el);
  return el;
}

async function boot() {
  const [room, roster, motions, ...avatars] = await Promise.all([
    loadJson(DATA.room),
    loadJson(DATA.roster),
    loadJson(DATA.motions),
    ...Object.entries(AVATARS).map(async ([id, path]) => [id, await loadJson(path)]),
  ]);

  port = new SpacePort({ room, avatars: Object.fromEntries(avatars), motions });
  spawnRoster(port, roster);
  for (const actor of port.actors.values()) port.play(actor.id, "idle_breath");

  // S1: if a backend is up, it is authoritative; otherwise stay local.
  try {
    socket = createSpaceSocket({
      url: window.SPACE_WS_URL || "ws://127.0.0.1:8000/ws/space",
      roomId: room.room_id,
      onSnapshot: (message) => applySnapshot(port, message),
      onStatus: (status) => {
        setMode(status);
        setStatus("舞台");
      },
    });
    socket.connect();
  } catch (err) {
    socket = null;
    setStatus(`後端未連線：${err.message}`);
  }

  // who you are talking to
  const selectSection = section("說話對象");
  const select = document.createElement("select");
  select.innerHTML = [...port.actors.keys()]
    .map((id) => `<option value="${id}">${port.get(id).avatar.display_name ?? id}</option>`)
    .join("");
  select.addEventListener("change", () => {
    selectedRole = select.value;
    setStatus(`對象 → ${selectedRole}`);
  });
  selectSection.appendChild(select);

  const line = document.createElement("input");
  line.placeholder = "對她說一句話…";
  line.value = "我回來了。";
  selectSection.appendChild(line);

  button(selectSection, "說話", () => {
    try {
      port.say(selectedRole, line.value || "…", 4500);
      port.play(selectedRole, "nod");
      socket?.send({ type: "say", actor_id: selectedRole, text: line.value || "…" });
      setStatus(`${selectedRole} 說完一句`);
    } catch (err) {
      setStatus(`說話失敗：${err.message}`);
    }
  });

  // three-way beat
  const beatSection = section("三人對話");
  button(beatSection, "示範一輪", () => {
    if (stopBeat) stopBeat();
    stopBeat = scriptedBeat(port, [
      { role_id: "main", text: "歡迎回來，今天過得怎麼樣？" },
      { role_id: "role_b", text: "我把今天的帳整理好了，數字不太好看。" },
      { role_id: "role_c", text: "先別談帳，先說你吃飯了沒。" },
    ]);
    setStatus("三人輪流說話中…");
  });

  // expressions
  const exSection = section("表情");
  for (const expression of avatars[0][1].expression_channels) {
    button(exSection, expression, () => {
      port.express(selectedRole, expression);
      socket?.send({ type: "express", actor_id: selectedRole, expression });
      setStatus(`${selectedRole} → ${expression}`);
    });
  }

  // motions
  const motionSection = section("動作");
  for (const motionId of Object.keys(motions)) {
    button(motionSection, motionId, () => {
      port.play(selectedRole, motionId);
      socket?.send({ type: "play", actor_id: selectedRole, motion: motionId });
      setStatus(`${selectedRole} → ${motionId}`);
    });
  }

  // wardrobe
  const wardrobeSection = section("穿著（對象）");
  for (const slot of SLOTS) {
    button(wardrobeSection, `換 ${slot}`, () => {
      const actor = port.get(selectedRole);
      actor.avatar = cycleTint(actor.avatar, slot);
      setStatus(`${selectedRole} ${slot} → rev ${actor.avatar.rev}`);
    });
  }

  // visibility
  const visibilitySection = section("可見性");
  let hidden = false;
  button(visibilitySection, "對 role_c 隱藏 role_b", () => {
    hidden = !hidden;
    port.get("role_b").visibleTo = hidden ? ["main", "role_b"] : null;
    const visible = port.visibleFrom("role_c").map((a) => a.id);
    setStatus(`role_c 看得到：${visible.join(", ") || "（無）"}`);
  });

  // movement
  const moveSection = section("走動");
  button(moveSection, "走到中央", () => {
    port.move(selectedRole, [8, 0], 900);
    socket?.send({ type: "move", actor_id: selectedRole, position: [8, 0] });
    setStatus(`${selectedRole} 走向中央`);
  });

  // camera
  const camSection = section("鏡頭");
  for (const preset of room.camera_presets) {
    button(camSection, preset, () => {
      camera = resolveCamera(preset);
      setStatus(`鏡頭 → ${preset}`);
    });
  }

  // recording
  const recSection = section("錄影");
  const recBtn = button(
    recSection,
    "開始錄影",
    async () => {
      if (recording) {
        const blob = await recording.stop();
        recording = null;
        recBtn.textContent = "開始錄影";
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `space-${Date.now()}.webm`;
        a.click();
        URL.revokeObjectURL(url);
        setStatus(`錄影完成（${(blob.size / 1024).toFixed(0)} KB）`);
        return;
      }
      try {
        recording = startRecording(canvas);
        recBtn.textContent = "停止錄影";
        setStatus("錄影中…");
      } catch (err) {
        setStatus(`此瀏覽器不支援錄影：${err.message}`);
      }
    },
    "record"
  );
  if (!isRecordingSupported(canvas)) {
    recBtn.disabled = true;
    recBtn.title = "此瀏覽器不支援 MediaRecorder";
  }

  setStatus(`S1 舞台就緒｜3 個角色｜${rendererLabel()}`);
  requestAnimationFrame(frame);
}

boot().catch((err) => {
  setStatus(`載入失敗：${err.message}`);
  console.error(err);
});
