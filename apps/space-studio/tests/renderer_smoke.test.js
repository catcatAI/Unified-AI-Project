/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Renderer smoke test — draws into a recording fake context.
 *
 * No browser and no image comparison: the point is that every expression and a
 * moving actor can be drawn without throwing, and that the room actually gets
 * painted. Catches the class of bug a screenshot would catch, but headless.
 */

import assert from "node:assert/strict";
import test from "node:test";

import { resolveCamera } from "../src/camera.js";
import { drawStage } from "../src/renderer.js";
import { Actor } from "../src/actors.js";

const ROOM = {
  room_id: "studio_a",
  palette: { sky: ["#151922", "#232b3a"], wall: "#242a36", floor: "#3a2f2a" },
};

const AVATAR = {
  avatar_id: "angela_base",
  display_name: "Angela",
  expression_channels: ["neutral", "smile", "happy", "blush", "wink", "sad"],
  palette: { skin: "#f0d3b8", hair: "#2f2430" },
  wardrobe: { slots: { top: { tint: "#3b6ea5" } } },
  rev: 0,
};

const VIEWPORT = { width: 960, height: 540, worldWidth: 16, worldHeight: 9 };

function fakeContext() {
  const calls = [];
  const gradient = { addColorStop() {} };
  const ctx = new Proxy(
    {},
    {
      get(_target, prop) {
        if (prop === "createLinearGradient") return () => gradient;
        return (...args) => {
          calls.push([prop, args]);
          return undefined;
        };
      },
      set() {
        return true;
      },
    }
  );
  return { ctx, calls };
}

function actor(expression = "neutral") {
  const a = new Actor({ id: "main", avatar: AVATAR, position: [8, 0] });
  a.express(expression);
  return a;
}

test("drawStage paints the room and the actor", () => {
  const { ctx, calls } = fakeContext();
  drawStage(ctx, {
    room: ROOM,
    actors: [actor()],
    camera: resolveCamera("wide"),
    viewport: VIEWPORT,
  });
  const names = calls.map(([name]) => name);
  for (const required of ["fillRect", "ellipse", "fillText", "beginPath", "fill", "stroke"]) {
    assert.ok(names.includes(required), `renderer never called ${required}`);
  }
  assert.ok(calls.some(([name, args]) => name === "fillText" && args[0] === "Angela"));
});

test("every expression channel renders without throwing", () => {
  for (const expression of AVATAR.expression_channels) {
    const { ctx } = fakeContext();
    assert.doesNotThrow(() =>
      drawStage(ctx, {
        room: ROOM,
        actors: [actor(expression)],
        camera: resolveCamera("close"),
        viewport: VIEWPORT,
      })
    );
  }
});

test("a moving, mid-motion actor renders and shows its motion tag", () => {
  const { ctx, calls } = fakeContext();
  const a = actor("smile");
  a.moveTo([10, 0], 1000);
  a.play({ id: "wave_hello", durationMs: 1800, loop: false });
  a.update(300);
  drawStage(ctx, { room: ROOM, actors: [a], camera: resolveCamera("medium"), viewport: VIEWPORT });
  assert.ok(
    calls.some(([name, args]) => name === "fillText" && String(args[0]).includes("wave_hello")),
    "motion tag missing"
  );
});

test("actors are drawn back-to-front by world y", () => {
  const back = new Actor({ id: "back", avatar: AVATAR, position: [6, 2] });
  back.avatar = { ...AVATAR, display_name: "Back" };
  const front = new Actor({ id: "front", avatar: { ...AVATAR, display_name: "Front" }, position: [6, 0] });
  const { ctx, calls } = fakeContext();
  drawStage(ctx, { room: ROOM, actors: [front, back], camera: resolveCamera("wide"), viewport: VIEWPORT });
  const labels = calls.filter(([name]) => name === "fillText").map(([, args]) => args[0]);
  assert.ok(labels.indexOf("Back") < labels.indexOf("Front"));
});
