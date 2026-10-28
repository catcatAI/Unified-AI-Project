/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * S3: motion model — keyframes, interpolation, validation, round-trip.
 */

import assert from "node:assert/strict";
import test from "node:test";

import {
  addKeyframe,
  CHANNELS,
  createMotion,
  moveKeyframe,
  parseMotion,
  removeKeyframe,
  sampleChannel,
  sampleMotion,
  serializeMotion,
  validateMotion,
} from "../src/motion_editor.js";

const base = () =>
  createMotion({
    id: "wave",
    durationMs: 1000,
    tracks: { arm_r: [[0, 0], [500, 1.2], [1000, 0]] },
  });

// --------------------------------------------------------------------------
// construction
// --------------------------------------------------------------------------
test("createMotion normalises and sorts keys", () => {
  const motion = createMotion({ id: "m", durationMs: 800, tracks: { tilt: [[400, 0.2], [0, 0]] } });
  assert.deepEqual(motion.tracks.tilt, [
    [0, 0],
    [400, 0.2],
  ]);
});

test("unknown channel is rejected", () => {
  assert.throws(() => createMotion({ id: "m", tracks: { tail: [[0, 1]] } }), /unknown motion channel/);
});

test("key past the duration is rejected", () => {
  assert.throws(() => createMotion({ id: "m", durationMs: 500, tracks: { tilt: [[600, 1]] } }), /past the duration/);
});

test("motion needs a positive duration", () => {
  assert.throws(() => createMotion({ id: "m", durationMs: 0 }), /positive/);
  assert.throws(() => createMotion({}), /needs an id/);
});

// --------------------------------------------------------------------------
// editing
// --------------------------------------------------------------------------
test("addKeyframe inserts in time order", () => {
  const motion = addKeyframe(base(), "arm_r", 250, 0.6);
  assert.deepEqual(
    motion.tracks.arm_r.map(([t]) => t),
    [0, 250, 500, 1000]
  );
});

test("addKeyframe at an existing time replaces it", () => {
  const motion = addKeyframe(base(), "arm_r", 500, -1);
  assert.deepEqual(motion.tracks.arm_r[1], [500, -1]);
});

test("addKeyframe is immutable", () => {
  const motion = base();
  addKeyframe(motion, "arm_r", 100, 9);
  assert.equal(motion.tracks.arm_r.length, 3);
});

test("addKeyframe validates channel, time and value", () => {
  assert.throws(() => addKeyframe(base(), "tail", 0, 1), /unknown motion channel/);
  assert.throws(() => addKeyframe(base(), "tilt", -1, 1), />= 0/);
  assert.throws(() => addKeyframe(base(), "tilt", 2000, 1), /past the duration/);
  assert.throws(() => addKeyframe(base(), "tilt", 100, NaN), /finite/);
});

test("removeKeyframe drops the key and the empty channel", () => {
  let motion = createMotion({ id: "m", durationMs: 100, tracks: { tilt: [[0, 1]] } });
  motion = removeKeyframe(motion, "tilt", 0);
  assert.equal(motion.tracks.tilt, undefined);
  assert.throws(() => removeKeyframe(base(), "arm_r", 99), /no keyframe/);
});

// --------------------------------------------------------------------------
// sampling
// --------------------------------------------------------------------------
test("sampling interpolates linearly", () => {
  assert.equal(sampleChannel([[0, 0], [1000, 1]], 250), 0.25);
  assert.equal(sampleChannel([[0, 0], [1000, 1]], 500), 0.5);
});

test("sampling clamps outside the key range", () => {
  assert.equal(sampleChannel([[200, 5], [800, 9]], 0), 5);
  assert.equal(sampleChannel([[200, 5], [800, 9]], 1000), 9);
});

test("empty or missing keys sample to zero", () => {
  assert.equal(sampleChannel([], 100), 0);
  assert.equal(sampleChannel(undefined, 100), 0);
});

test("sampleMotion returns every channel at that instant", () => {
  const motion = createMotion({
    id: "m",
    durationMs: 1000,
    tracks: { tilt: [[0, 0], [1000, 1]], offset_y: [[0, 2], [1000, 2]] },
  });
  assert.deepEqual(sampleMotion(motion, 500), { tilt: 0.5, offset_y: 2 });
});

// --------------------------------------------------------------------------
// validation and round-trip
// --------------------------------------------------------------------------
test("validateMotion flags a bad duration and empty tracks", () => {
  const bad = { id: "m", durationMs: -1, tracks: { tilt: [] } };
  const result = validateMotion(bad);
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((e) => e.includes("duration")));
  assert.ok(result.errors.some((e) => e.includes("no keys")));
});

test("serialize/parse round-trips a motion", () => {
  const motion = base();
  assert.deepEqual(parseMotion(serializeMotion(motion)), motion);
});

test("parseMotion rejects garbage", () => {
  assert.throws(() => parseMotion({ id: "m", durationMs: 100, tracks: { tail: [[0, 1]] } }), /unknown motion channel/);
});

test("every declared channel is usable", () => {
  for (const channel of CHANNELS) {
    const motion = createMotion({ id: `m_${channel}`, durationMs: 100, tracks: { [channel]: [[0, 1]] } });
    assert.equal(sampleMotion(motion, 50)[channel], 1);
  }
});

test("moveKeyframe keeps the value and re-sorts", () => {
  const motion = moveKeyframe(base(), "arm_r", 1, 900);
  assert.deepEqual(
    motion.tracks.arm_r.map(([t]) => t),
    [0, 900, 1000]
  );
  assert.equal(motion.tracks.arm_r[1][1], 1.2);
});

test("moveKeyframe onto an existing time replaces it", () => {
  const motion = moveKeyframe(base(), "arm_r", 1, 0);
  assert.equal(motion.tracks.arm_r.length, 2);
  assert.deepEqual(motion.tracks.arm_r[0], [0, 1.2]);
});

test("moveKeyframe validates index and time", () => {
  assert.throws(() => moveKeyframe(base(), "arm_r", 9, 100), /no keyframe/);
  assert.throws(() => moveKeyframe(base(), "arm_r", 0, 9999), /past the duration/);
});
