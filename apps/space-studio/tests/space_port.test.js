/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * SpacePort + Actor — lifecycle, movement, visibility, snapshots.
 */

import assert from "node:assert/strict";
import test from "node:test";

import { Actor } from "../src/actors.js";
import { SpacePort } from "../src/space_port.js";

const AVATAR = {
  avatar_id: "angela_base",
  display_name: "Angela",
  expression_channels: ["neutral", "smile", "wink"],
  wardrobe: { slots: { top: { item: "hoodie_blue", tint: "#3b6ea5" } } },
  rev: 0,
};

const MOTIONS = {
  idle_breath: { id: "idle_breath", durationMs: 2600, loop: true },
  wave_hello: { id: "wave_hello", durationMs: 1800, loop: false },
};

const ROOM = { room_id: "studio_a", spawn_points: [{ id: "center", x: 8, y: 0 }] };

function makePort() {
  return new SpacePort({ room: ROOM, avatars: { angela_base: AVATAR }, motions: MOTIONS });
}

test("spawn puts an actor on the spawn point", () => {
  const port = makePort();
  const actor = port.spawn("main", { avatarId: "angela_base" });
  assert.equal(actor.roleId, "main");
  assert.deepEqual(actor.position, [8, 0]);
});

test("duplicate spawn is rejected", () => {
  const port = makePort();
  port.spawn("main", { avatarId: "angela_base" });
  assert.throws(() => port.spawn("main", { avatarId: "angela_base" }), /already spawned/);
});

test("unknown avatar is rejected", () => {
  assert.throws(() => makePort().spawn("main", { avatarId: "nobody" }), /unknown avatar/);
});

test("despawn removes the actor and reports whether it existed", () => {
  const port = makePort();
  port.spawn("main", { avatarId: "angela_base" });
  assert.equal(port.despawn("main"), true);
  assert.equal(port.despawn("main"), false);
});

test("unknown actor operations throw", () => {
  const port = makePort();
  assert.throws(() => port.move("ghost", [1, 1]), /unknown actor/);
  assert.throws(() => port.play("ghost", "nod"), /unknown actor/);
});

test("move interpolates and lands exactly on target", () => {
  const port = makePort();
  port.spawn("main", { avatarId: "angela_base" });
  port.move("main", [10, 0], 1000);
  port.tick(400);
  const mid = port.get("main").position[0];
  assert.ok(mid > 8 && mid < 10, `midpoint should be between 8 and 10, got ${mid}`);
  port.tick(600);
  assert.deepEqual(port.get("main").position, [10, 0]);
});

test("move with zero duration snaps immediately", () => {
  const port = makePort();
  port.spawn("main", { avatarId: "angela_base" });
  port.move("main", [3, 0], 0);
  port.tick(16);
  assert.deepEqual(port.get("main").position, [3, 0]);
});

test("non-looping motion clears itself when done", () => {
  const port = makePort();
  port.spawn("main", { avatarId: "angela_base" });
  port.play("main", "wave_hello");
  assert.equal(port.get("main").motion.id, "wave_hello");
  port.tick(1900);
  assert.equal(port.get("main").motion, null);
});

test("looping motion survives past its duration", () => {
  const port = makePort();
  port.spawn("main", { avatarId: "angela_base" });
  port.play("main", "idle_breath");
  port.tick(9000);
  assert.equal(port.get("main").motion.id, "idle_breath");
});

test("unknown motion is rejected", () => {
  const port = makePort();
  port.spawn("main", { avatarId: "angela_base" });
  assert.throws(() => port.play("main", "moonwalk"), /unknown motion/);
});

test("expression must exist on the avatar", () => {
  const port = makePort();
  port.spawn("main", { avatarId: "angela_base" });
  port.express("main", "wink");
  assert.equal(port.get("main").expression, "wink");
  assert.throws(() => port.express("main", "angry"), /unknown expression/);
});

test("look turns the actor towards its target", () => {
  const port = makePort();
  port.spawn("main", { avatarId: "angela_base" });
  port.spawn("role_b", { avatarId: "angela_base", position: [8, 4] });
  port.look("main", "role_b");
  assert.ok(Math.abs(port.get("main").facing - Math.PI / 2) < 1e-9);
});

test("visibility hides actors from viewers not on the list", () => {
  const port = makePort();
  port.spawn("main", { avatarId: "angela_base" });
  port.spawn("role_b", { avatarId: "angela_base", visibleTo: ["main"] });
  assert.deepEqual(
    port.visibleFrom("main").map((a) => a.id),
    ["main", "role_b"]
  );
  assert.deepEqual(
    port.visibleFrom("role_c").map((a) => a.id),
    ["main"]
  );
});

test("snapshot is plain data with a rounded position", () => {
  const port = makePort();
  port.spawn("main", { avatarId: "angela_base" });
  const snap = port.snapshot();
  assert.equal(snap.roomId, "studio_a");
  assert.deepEqual(Object.keys(snap.actors[0]).sort(), [
    "avatarRev",
    "expression",
    "facing",
    "id",
    "motion",
    "position",
    "roleId",
  ]);
});

test("capabilities advertise what the stage can do", () => {
  const caps = makePort().capabilities();
  for (const name of ["spawn", "move", "play", "express", "look", "snapshot"]) {
    assert.ok(caps.includes(name), `missing capability ${name}`);
  }
});

test("actor breathing phase wraps instead of growing forever", () => {
  const actor = new Actor({ id: "a", avatar: AVATAR });
  for (let i = 0; i < 100; i += 1) actor.update(1000);
  assert.ok(actor.breathPhase >= 0 && actor.breathPhase < 1);
});
