/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * S1: three actors on one stage — roster, speech bubbles, visibility, Live2D probe.
 */

import assert from "node:assert/strict";
import test from "node:test";

import { Actor } from "../src/actors.js";
import { detectLive2D, rendererLabel } from "../src/live2d.js";
import { drawStage } from "../src/renderer.js";
import { spawnRoster } from "../src/roster.js";
import { resolveCamera } from "../src/camera.js";
import { SpacePort } from "../src/space_port.js";

const AVATARS = {
  angela_base: {
    avatar_id: "angela_base",
    display_name: "Angela",
    expression_channels: ["neutral", "smile"],
    wardrobe: { slots: { top: { tint: "#3b6ea5" } } },
    rev: 0,
  },
  gemma_b: {
    avatar_id: "gemma_b",
    display_name: "Gemma 角色",
    expression_channels: ["neutral"],
    wardrobe: { slots: { top: { tint: "#4e8f6d" } } },
    rev: 0,
  },
  qwen_c: {
    avatar_id: "qwen_c",
    display_name: "Qwen 角色",
    expression_channels: ["neutral"],
    wardrobe: { slots: { top: { tint: "#6a4f9e" } } },
    rev: 0,
  },
};

const MOTIONS = { idle_breath: { id: "idle_breath", durationMs: 2600, loop: true } };
const ROOM = { room_id: "studio_a", spawn_points: [{ x: 8, y: 0 }] };
const ROSTER = {
  actors: [
    { role_id: "main", avatar_id: "angela_base", position: [5.5, 0] },
    { role_id: "role_b", avatar_id: "gemma_b", position: [8, 0] },
    { role_id: "role_c", avatar_id: "qwen_c", position: [10.5, 0] },
  ],
};

function port() {
  return new SpacePort({ room: ROOM, avatars: AVATARS, motions: MOTIONS });
}

function fakeContext() {
  const calls = [];
  const ctx = new Proxy(
    {},
    {
      get(_t, prop) {
        if (prop === "createLinearGradient") return () => ({ addColorStop() {} });
        if (prop === "measureText") return (text) => ({ width: String(text).length * 6 });
        return (...args) => {
          calls.push([prop, args]);
        };
      },
      set() {
        return true;
      },
    }
  );
  return { ctx, calls };
}

// --------------------------------------------------------------------------
// roster
// --------------------------------------------------------------------------
test("roster spawns every role with its own avatar and position", () => {
  const p = port();
  const actors = spawnRoster(p, ROSTER);
  assert.deepEqual(
    actors.map((a) => a.id),
    ["main", "role_b", "role_c"]
  );
  assert.equal(p.get("role_b").avatar.avatar_id, "gemma_b");
  assert.deepEqual(p.get("role_c").position, [10.5, 0]);
});

test("roster rejects entries without a role id", () => {
  assert.throws(() => spawnRoster(port(), { actors: [{ avatar_id: "x" }] }), /needs a role_id/);
  assert.throws(() => spawnRoster(port(), {}), /actors array/);
});

// --------------------------------------------------------------------------
// speech
// --------------------------------------------------------------------------
test("say puts a bubble on the speaking actor only", () => {
  const p = port();
  spawnRoster(p, ROSTER);
  p.say("role_b", "我把帳整理好了", 2000);
  assert.equal(p.get("role_b").speech.text, "我把帳整理好了");
  assert.equal(p.get("role_c").speech, null);
});

test("speech expires after its duration", () => {
  const p = port();
  spawnRoster(p, ROSTER);
  p.say("main", "hi", 500);
  p.tick(300);
  assert.ok(p.get("main").speech);
  p.tick(300);
  assert.equal(p.get("main").speech, null);
});

test("empty speech is rejected", () => {
  const p = port();
  spawnRoster(p, ROSTER);
  assert.throws(() => p.say("main", "   "), /non-empty text/);
});

test("snapshot carries the speech text", () => {
  const p = port();
  spawnRoster(p, ROSTER);
  p.say("role_c", "先吃飯", 1000);
  const snap = p.snapshot().actors.find((a) => a.id === "role_c");
  assert.equal(snap.speech, "先吃飯");
});

// --------------------------------------------------------------------------
// visibility
// --------------------------------------------------------------------------
test("hiding an actor removes it from another role's view", () => {
  const p = port();
  spawnRoster(p, ROSTER);
  p.get("role_b").visibleTo = ["main", "role_b"];
  assert.deepEqual(
    p.visibleFrom("role_c").map((a) => a.id),
    ["main", "role_c"]
  );
  assert.deepEqual(
    p.visibleFrom("main").map((a) => a.id),
    ["main", "role_b", "role_c"]
  );
});

// --------------------------------------------------------------------------
// renderer
// --------------------------------------------------------------------------
test("renderer draws a speech bubble with the spoken text", () => {
  const { ctx, calls } = fakeContext();
  const p = port();
  spawnRoster(p, ROSTER);
  p.say("role_b", "我把今天的帳整理好了", 3000);
  drawStage(ctx, {
    room: { palette: { sky: ["#111", "#222"], wall: "#333" } },
    actors: [...p.actors.values()],
    camera: resolveCamera("medium"),
    viewport: { width: 960, height: 540, worldWidth: 16, worldHeight: 9 },
  });
  const texts = calls.filter(([name]) => name === "fillText").map(([, args]) => args[0]);
  assert.ok(texts.some((t) => String(t).includes("帳")), `bubble text missing: ${texts}`);
});

test("renderer survives three actors with no speech", () => {
  const { ctx } = fakeContext();
  const p = port();
  spawnRoster(p, ROSTER);
  assert.doesNotThrow(() =>
    drawStage(ctx, {
      room: { palette: { sky: ["#111", "#222"] } },
      actors: [...p.actors.values()],
      camera: resolveCamera("wide"),
      viewport: { width: 960, height: 540, worldWidth: 16, worldHeight: 9 },
    })
  );
});

// --------------------------------------------------------------------------
// Live2D seam
// --------------------------------------------------------------------------
test("live2d detection is honest about a missing runtime", () => {
  assert.equal(detectLive2D({}), false);
  assert.match(rendererLabel({}), /procedural/);
});

test("live2d detection sees a cubism runtime when present", () => {
  assert.equal(detectLive2D({ Live2DCubismCore: {} }), true);
  assert.match(rendererLabel({ Live2D: {} }), /not wired/);
});

test("actors keep independent state on one stage", () => {
  const p = port();
  spawnRoster(p, ROSTER);
  p.express("main", "smile");
  p.play("role_c", "idle_breath");
  assert.equal(p.get("main").expression, "smile");
  assert.equal(p.get("role_b").expression, "neutral");
  assert.equal(p.get("role_c").motion.id, "idle_breath");
  assert.equal(p.get("role_b").motion, null);
});

test("Actor.say is independent of motion playback", () => {
  const actor = new Actor({ id: "a", avatar: AVATARS.angela_base });
  actor.play(MOTIONS.idle_breath);
  actor.say("hello", 1000);
  actor.update(500);
  assert.ok(actor.speech);
  assert.ok(actor.motion);
});
