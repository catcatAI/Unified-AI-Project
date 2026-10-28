/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * S3: motion library persistence and the on-disk format.
 */

import assert from "node:assert/strict";
import test from "node:test";

import { createMotion } from "../src/motion_editor.js";
import {
  deleteMotion,
  fromLibraryJson,
  listMotions,
  loadLibrary,
  persistLibrary,
  saveMotion,
  STORAGE_KEY,
  toLibraryJson,
} from "../src/motion_store.js";

class FakeStorage {
  constructor() {
    this.map = new Map();
  }

  getItem(key) {
    return this.map.get(key) ?? null;
  }

  setItem(key, value) {
    this.map.set(key, String(value));
  }
}

const wave = () =>
  createMotion({ id: "wave", durationMs: 1000, tracks: { arm_r: [[0, 0], [500, 1.2], [1000, 0]] } });

test("save and delete are immutable", () => {
  const library = {};
  const next = saveMotion(library, wave());
  assert.deepEqual(Object.keys(library), []);
  assert.deepEqual(Object.keys(next), ["wave"]);
  assert.deepEqual(Object.keys(deleteMotion(next, "wave")), []);
});

test("saveMotion needs an id", () => {
  assert.throws(() => saveMotion({}, {}), /needs a motion with an id/);
});

test("listMotions is sorted by id", () => {
  const library = {
    z: createMotion({ id: "z" }),
    a: createMotion({ id: "a" }),
  };
  assert.deepEqual(
    listMotions(library).map((m) => m.id),
    ["a", "z"]
  );
});

test("exported JSON matches the shipped library shape", () => {
  const json = toLibraryJson({ wave: wave() });
  const parsed = JSON.parse(json);
  assert.deepEqual(Object.keys(parsed), ["wave"]);
  assert.equal(parsed.wave.durationMs, 1000);
  assert.deepEqual(parsed.wave.tracks.arm_r[1], [500, 1.2]);
});

test("export → import round-trips", () => {
  const library = { wave: wave() };
  const back = fromLibraryJson(toLibraryJson(library));
  assert.deepEqual(back.wave, library.wave);
});

test("persist and load round-trip through storage", () => {
  const storage = new FakeStorage();
  assert.equal(persistLibrary(storage, { wave: wave() }), true);
  assert.ok(storage.getItem(STORAGE_KEY).includes("wave"));
  const loaded = loadLibrary(storage);
  assert.equal(loaded.wave.durationMs, 1000);
});

test("corrupt or hostile storage degrades to an empty library", () => {
  const storage = new FakeStorage();
  storage.setItem(STORAGE_KEY, "{broken");
  assert.deepEqual(loadLibrary(storage), {});

  const hostile = {
    getItem: () => {
      throw new Error("denied");
    },
    setItem: () => {
      throw new Error("denied");
    },
  };
  assert.deepEqual(loadLibrary(hostile), {});
  assert.equal(persistLibrary(hostile, { wave: wave() }), false);
});

test("missing storage is a no-op, not a crash", () => {
  assert.deepEqual(loadLibrary(null), {});
  assert.equal(persistLibrary(null, {}), false);
});
