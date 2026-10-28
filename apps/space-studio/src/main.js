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
import { isRecordingSupported, startRecording } from "./recorder.js";
import { scriptedBeat, spawnRoster } from "./roster.js";
import { rendererLabel } from "./live2d.js";
import { hasFeature, resolveFeatures } from "./features.js";
import { pickMotion, parseRules } from "./al_rules.js";
import { inspectLive2D } from "./live2d_renderer.js";
import { addKeyframe, CHANNELS, createMotion, moveKeyframe, removeKeyframe } from "./motion_editor.js";
import { loadLibrary, persistLibrary, saveMotion, toLibraryJson } from "./motion_store.js";
import { OutfitStore } from "./outfit_store.js";
import { watchJson } from "./reload.js";
import { applySnapshot } from "./snapshot_sync.js";
import { createSpaceSocket } from "./ws_client.js";

const DATA = {
  room: "../../space/rooms/studio_a.json",
  roster: "../../space/roles.json",
  motions: "../../space/motions/index.json",
  catalog: "../../space/wardrobe/catalog.json",
  rules: "../../space/rules/al_motion.json",
};

const AVATARS = {
  angela_base: "../../space/avatars/angela_base.json",
  gemma_b: "../../space/avatars/gemma_b.json",
  qwen_c: "../../space/avatars/qwen_c.json",
  deepseek_d: "../../space/avatars/deepseek_d.json",
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
let roomWatcher = null;
const features = resolveFeatures(window);
const storage = safeStorage();

const viewport = () => ({ width: canvas.width, height: canvas.height, worldWidth: 16, worldHeight: 9 });
function safeStorage() {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

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

function section(title, feature = null) {
  const el = document.createElement("div");
  el.className = "section";
  const h = document.createElement("h3");
  h.textContent = title;
  el.appendChild(h);
  // S6: a disabled feature is built but not shown, so turning it on later needs
  // no reload of the module graph.
  if (feature && !hasFeature(features, feature)) el.hidden = true;
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
  const motionSection = section("動作", "motion");
  for (const motionId of Object.keys(motions)) {
    button(motionSection, motionId, () => {
      port.play(selectedRole, motionId);
      socket?.send({ type: "play", actor_id: selectedRole, motion: motionId });
      setStatus(`${selectedRole} → ${motionId}`);
    });
  }


  // motion editor (S3): pick a motion, add/remove keys, preview, save, export
  const editorSection = section("動作編輯", "motion_editor");
  const library = loadLibrary(storage);
  const motionSelect = document.createElement("select");
  const channelSelect = document.createElement("select");
  channelSelect.innerHTML = CHANNELS.map((channel) => `<option>${channel}</option>`).join("");
  const tInput = document.createElement("input");
  tInput.type = "number";
  tInput.min = "0";
  tInput.value = "0";
  const vInput = document.createElement("input");
  vInput.type = "number";
  vInput.step = "0.1";
  vInput.value = "0.5";
  const keyList = document.createElement("div");
  keyList.className = "keys";
  let editing = null;

  const motionOptions = () => ({ ...port.motions, ...library });

  function renderKeys() {
    keyList.innerHTML = "";
    if (!editing) return;
    for (const [channel, keys] of Object.entries(editing.tracks ?? {})) {
      keys.forEach(([t, v], index) => {
        const row = document.createElement("div");
        row.className = "key";
        row.textContent = `${channel} @${t}ms = ${v}`;
        const slider = document.createElement("input");
        slider.type = "range";
        slider.min = "0";
        slider.max = String(editing.durationMs);
        slider.step = "10";
        slider.value = String(t);
        slider.title = "拖曳調整時間";
        slider.addEventListener("change", () => {
          try {
            editing = moveKeyframe(editing, channel, index, Number(slider.value));
            port.motions[editing.id] = editing;
            renderKeys();
            setStatus(`${channel} 移到 ${slider.value}ms`);
          } catch (err) {
            setStatus(`拖曳失敗：${err.message}`);
          }
        });
        row.appendChild(slider);
        const del = document.createElement("button");
        del.textContent = "×";
        del.addEventListener("click", () => {
          editing = removeKeyframe(editing, channel, index);
          renderKeys();
        });
        row.appendChild(del);
        keyList.appendChild(row);
      });
    }
  }

  function loadMotion(id) {
    const source = motionOptions()[id];
    editing = source ? { ...source, tracks: { ...(source.tracks ?? {}) } } : null;
    tInput.max = String(editing?.durationMs ?? 2000);
    renderKeys();
  }

  function refreshMotionSelect(preserve) {
    const all = motionOptions();
    motionSelect.innerHTML = Object.keys(all)
      .map((id) => `<option value="${id}">${id}</option>`)
      .join("");
    if (preserve && all[preserve]) motionSelect.value = preserve;
    loadMotion(motionSelect.value);
  }

  motionSelect.addEventListener("change", () => loadMotion(motionSelect.value));
  editorSection.appendChild(motionSelect);
  editorSection.appendChild(channelSelect);
  editorSection.appendChild(tInput);
  editorSection.appendChild(vInput);
  editorSection.appendChild(keyList);

  button(editorSection, "加關鍵影格", () => {
    if (!editing) return;
    try {
      editing = addKeyframe(editing, channelSelect.value, Number(tInput.value), Number(vInput.value));
      port.motions[editing.id] = editing;
      renderKeys();
      setStatus(`已加 ${channelSelect.value} @${tInput.value}ms`);
    } catch (err) {
      setStatus(`加不進去：${err.message}`);
    }
  });

  button(editorSection, "預覽", () => {
    if (!editing) return;
    port.motions[editing.id] = editing;
    port.play(selectedRole, editing.id);
    setStatus(`${selectedRole} 預覽 ${editing.id}`);
  });

  button(editorSection, "存到動作庫", () => {
    if (!editing) return;
    try {
      Object.assign(library, saveMotion(library, editing));
      persistLibrary(storage, library);
      port.motions[editing.id] = editing;
      refreshMotionSelect(editing.id);
      setStatus(`已存 ${editing.id}（${Object.keys(editing.tracks).length} 個頻道）`);
    } catch (err) {
      setStatus(`存不進去：${err.message}`);
    }
  });

  button(editorSection, "匯出 JSON", () => {
    const text = toLibraryJson(library);
    const url = URL.createObjectURL(new Blob([text], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "motions.json";
    link.click();
    URL.revokeObjectURL(url);
    setStatus(`已匯出 ${Object.keys(library).length} 個動作`);
  });

  button(editorSection, "新增動作", () => {
    const id = window.prompt("動作 id（英數）", `custom_${Date.now().toString(36)}`);
    if (!id) return;
    try {
      const motion = createMotion({ id, durationMs: 2000, tracks: { offset_y: [[0, 0], [1000, 0.4], [2000, 0]] } });
      Object.assign(library, saveMotion(library, motion));
      persistLibrary(storage, library);
      port.motions[id] = motion;
      refreshMotionSelect(id);
      setStatus(`新動作 ${id}（2 秒，含一個示範 keyframe）`);
    } catch (err) {
      setStatus(`新增失敗：${err.message}`);
    }
  });

  refreshMotionSelect();


  // AL state → motion (S3 finish): the same vitals that colour the persona
  const alSection = section("狀態 → 動作", "al_motion");
  const { rules } = parseRules(await loadJson(DATA.rules));
  const vitals = {};
  for (const [key, label] of [["fatigue", "疲勞"], ["stress", "壓力"], ["valence", "情緒"]]) {
    const wrap = document.createElement("label");
    wrap.textContent = `${label} `;
    const input = document.createElement("input");
    input.type = "range";
    input.min = "0";
    input.max = "1";
    input.step = "0.05";
    input.value = key === "valence" ? "0.5" : "0.2";
    vitals[key] = input;
    wrap.appendChild(input);
    alSection.appendChild(wrap);
  }
  button(alSection, "依狀態選動作", () => {
    const state = Object.fromEntries(Object.entries(vitals).map(([k, el]) => [k, Number(el.value)]));
    const picked = pickMotion(state, rules);
    if (!picked) {
      setStatus("沒有符合的規則（保持原動作）");
      return;
    }
    if (!port.motions[picked.motion]) {
      setStatus(`規則指向 ${picked.motion}，但動作庫沒有它`);
      return;
    }
    port.play(selectedRole, picked.motion);
    setStatus(`狀態 → ${picked.motion}（priority ${picked.priority}）`);
  });

  // Live2D probe (S1.5): checks the runtime and the model metadata, honestly
  const live2dSection = section("Live2D（S1.5）", "live2d");
  button(live2dSection, "檢查執行時", async () => {
    const verdict = await inspectLive2D();
    setStatus(
      verdict.ok
        ? `Live2D core OK、模型 metadata OK（${verdict.moc}）；繪製器尚未接`
        : `Live2D 不可用（${verdict.stage}）：${verdict.reason}`
    );
  });

  // wardrobe (S2): slot → item → tint, with undo and persistence
  const wardrobeSection = section("穿著（對象）", "wardrobe");
  const catalog = await loadJson(DATA.catalog);
  const stores = new Map();
  for (const roleId of port.actors.keys()) {
    const store = new OutfitStore(port.get(roleId).avatar, { storage });
    stores.set(roleId, store);
    port.get(roleId).avatar = store.avatar;
  }

  const slotSelect = document.createElement("select");
  slotSelect.innerHTML = Object.entries(catalog.slots)
    .map(([id, slot]) => `<option value="${id}">${slot.label}</option>`)
    .join("");
  wardrobeSection.appendChild(slotSelect);

  const itemSelect = document.createElement("select");
  wardrobeSection.appendChild(itemSelect);

  const tints = document.createElement("div");
  tints.className = "tints";
  wardrobeSection.appendChild(tints);

  function currentSlot() {
    return catalog.slots[slotSelect.value];
  }

  function refreshTints() {
    const slot = currentSlot();
    const item = slot.items.find((entry) => entry.id === itemSelect.value) ?? slot.items[0];
    tints.innerHTML = "";
    for (const tint of item.tints) {
      const swatch = document.createElement("button");
      swatch.className = "tint";
      swatch.style.background = tint;
      swatch.title = tint;
      swatch.addEventListener("click", () => applyWardrobe(item.id, tint));
      tints.appendChild(swatch);
    }
  }

  function refreshItems() {
    const slot = currentSlot();
    itemSelect.innerHTML = slot.items
      .map((entry) => `<option value="${entry.id}">${entry.label}</option>`)
      .join("");
    refreshTints();
  }

  function applyWardrobe(item, tint) {
    const store = stores.get(selectedRole);
    if (!store) return;
    store.set({ slot: slotSelect.value, item, tint });
    port.get(selectedRole).avatar = store.avatar;
    setStatus(`${selectedRole} ${slotSelect.value} → ${item} ${tint}（rev ${store.avatar.rev}）`);
  }

  slotSelect.addEventListener("change", refreshItems);
  itemSelect.addEventListener("change", refreshTints);
  refreshItems();

  button(wardrobeSection, "復原", () => {
    const store = stores.get(selectedRole);
    if (!store || !store.canUndo) {
      setStatus("沒有可復原的穿著");
      return;
    }
    store.undo();
    port.get(selectedRole).avatar = store.avatar;
    setStatus(`${selectedRole} 穿著復原（rev ${store.avatar.rev}）`);
  });

  // visibility
  const visibilitySection = section("可見性", "visibility");
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
  const camSection = section("鏡頭", "camera");
  for (const preset of room.camera_presets) {
    button(camSection, preset, () => {
      camera = resolveCamera(preset);
      setStatus(`鏡頭 → ${preset}`);
    });
  }

  // recording
  const recSection = section("錄影", "record");
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

  // S6: hot reload the room JSON; a palette/position edit lands without a restart.
  try {
    roomWatcher = watchJson(DATA.room, {
      onChange: (room) => {
        port.room = room;
        setStatus("房間設定已熱載入");
      },
    });
  } catch (err) {
    console.warn("room hot reload unavailable", err);
  }
  window.addEventListener("beforeunload", () => {
    roomWatcher?.stop();
    socket?.close();
  });

  setStatus(`S1 舞台就緒｜${port.actors.size} 個角色｜${rendererLabel()}`);
  requestAnimationFrame(frame);
}

boot().catch((err) => {
  setStatus(`載入失敗：${err.message}`);
  console.error(err);
});
