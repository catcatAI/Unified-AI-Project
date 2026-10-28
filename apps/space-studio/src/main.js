/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * main — wires the stage to the page: load data, run the loop, bind controls.
 *
 * No framework, no build step: `python3 -m http.server` at the repo root and
 * open /apps/space-studio/.
 */

import { drawStage } from "./renderer.js";
import { resolveCamera } from "./camera.js";
import { SpacePort } from "./space_port.js";
import { cycleTint, SLOTS } from "./wardrobe.js";
import { isRecordingSupported, startRecording } from "./recorder.js";

const DATA = {
  room: "../../space/rooms/studio_a.json",
  avatar: "../../space/avatars/angela_base.json",
  motions: "../../space/motions/index.json",
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
let camera = resolveCamera("wide");
let recording = null;
let lastFrame = performance.now();
let timeMs = 0;

function viewport() {
  return { width: canvas.width, height: canvas.height, worldWidth: 16, worldHeight: 9 };
}

function setStatus(text) {
  statusEl.textContent = text;
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
  const [room, avatar, motions] = await Promise.all([
    loadJson(DATA.room),
    loadJson(DATA.avatar),
    loadJson(DATA.motions),
  ]);

  port = new SpacePort({ room, avatars: { angela_base: avatar }, motions });
  port.spawn("main", {
    roleId: "main",
    avatarId: "angela_base",
    position: [room.spawn_points[0].x, room.spawn_points[0].y],
  });
  port.play("main", "idle_breath");

  // Expressions
  const exSection = section("表情");
  for (const expression of avatar.expression_channels) {
    button(exSection, expression, () => {
      port.express("main", expression);
      setStatus(`表情 → ${expression}`);
    });
  }

  // Camera
  const camSection = section("鏡頭");
  for (const preset of room.camera_presets) {
    button(camSection, preset, () => {
      camera = resolveCamera(preset);
      setStatus(`鏡頭 → ${preset}`);
    });
  }
  button(camSection, "自由視角", () => {
    camera = resolveCamera("free");
    setStatus("鏡頭 → free（可拖曳平移）");
  });

  // Motion
  const motionSection = section("動作");
  for (const motionId of Object.keys(motions)) {
    button(motionSection, motionId, () => {
      port.play("main", motionId);
      setStatus(`動作 → ${motionId}`);
    });
  }

  // Wardrobe
  const wardrobeSection = section("穿著");
  for (const slot of SLOTS) {
    button(wardrobeSection, `換 ${slot}`, () => {
      const actor = port.get("main");
      actor.avatar = cycleTint(actor.avatar, slot);
      setStatus(`${slot} 換色 → rev ${actor.avatar.rev}`);
    });
  }

  // Movement
  const moveSection = section("走動");
  button(moveSection, "走到左側", () => {
    port.move("main", [5, 0], 900);
    setStatus("移動 → (5, 0)");
  });
  button(moveSection, "走到中央", () => {
    port.move("main", [8, 0], 900);
    setStatus("移動 → (8, 0)");
  });

  // Recording
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

  // Free-camera drag
  let dragging = false;
  canvas.addEventListener("pointerdown", () => {
    dragging = camera.free === true;
  });
  canvas.addEventListener("pointerup", () => {
    dragging = false;
  });
  canvas.addEventListener("pointermove", (event) => {
    if (!dragging) return;
    camera = { ...camera, panX: camera.panX - event.movementX / canvas.width };
  });

  setStatus("S0 舞台就緒：角色已站在攝影棚中央");
  requestAnimationFrame(frame);
}

boot().catch((err) => {
  setStatus(`載入失敗：${err.message}`);
  console.error(err);
});
