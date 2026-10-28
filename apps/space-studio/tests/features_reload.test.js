/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * S6: feature flags and JSON hot reload.
 */

import assert from "node:assert/strict";
import test from "node:test";

import { DEFAULT_FEATURES, hasFeature, parseFeatures, resolveFeatures } from "../src/features.js";
import { watchJson } from "../src/reload.js";

// --------------------------------------------------------------------------
// features
// --------------------------------------------------------------------------
test("empty input enables the defaults", () => {
  const features = parseFeatures(undefined);
  assert.deepEqual([...features], DEFAULT_FEATURES);
});

test("a comma list replaces the defaults", () => {
  const features = parseFeatures("wardrobe, camera ,RECORD");
  assert.deepEqual([...features], ["wardrobe", "camera", "record"]);
  assert.equal(hasFeature(features, "motion"), false);
});

test("window value wins over storage", () => {
  const scope = {
    SPACE_FEATURES: "camera",
    localStorage: { getItem: () => "record,wardrobe" },
  };
  assert.deepEqual([...resolveFeatures(scope)], ["camera"]);
});

test("storage is used when the window value is absent", () => {
  const scope = { localStorage: { getItem: () => "record" } };
  assert.deepEqual([...resolveFeatures(scope)], ["record"]);
});

test("blocked storage falls back to defaults", () => {
  const scope = {
    localStorage: {
      getItem() {
        throw new Error("denied");
      },
    },
  };
  assert.deepEqual([...resolveFeatures(scope)], DEFAULT_FEATURES);
});

// --------------------------------------------------------------------------
// hot reload
// --------------------------------------------------------------------------
function harness(responses) {
  let index = 0;
  const changes = [];
  const errors = [];
  const timers = [];
  const watcher = watchJson("room.json", {
    fetchImpl: async () => {
      const next = responses[Math.min(index, responses.length - 1)];
      index += 1;
      if (next instanceof Error) throw next;
      return { ok: true, json: async () => next };
    },
    setIntervalImpl: (fn) => {
      timers.push(fn);
      return timers.length;
    },
    clearIntervalImpl: () => {},
    onChange: (data) => changes.push(data),
    onError: (err) => errors.push(err),
  });
  return { watcher, changes, errors, timers };
}

test("first tick always reports the loaded value", async () => {
  const { watcher, changes } = harness([{ room_id: "a" }]);
  await watcher.tick();
  assert.deepEqual(changes, [{ room_id: "a" }]);
});

test("unchanged payloads are not reported again", async () => {
  const { watcher, changes } = harness([{ room_id: "a" }, { room_id: "a" }]);
  await watcher.tick();
  await watcher.tick();
  assert.equal(changes.length, 1);
});

test("changed payloads are reported", async () => {
  const { watcher, changes } = harness([{ palette: 1 }, { palette: 2 }]);
  await watcher.tick();
  await watcher.tick();
  assert.deepEqual(changes.map((c) => c.palette), [1, 2]);
});

test("fetch failures are reported but do not stop the watcher", async () => {
  const { watcher, errors } = harness([new Error("offline"), { ok: true }]);
  await watcher.tick();
  assert.equal(errors.length, 1);
  assert.equal(watcher.stopped, false);
});

test("stop clears the interval and ignores further ticks", async () => {
  const { watcher, changes } = harness([{ a: 1 }]);
  watcher.stop();
  assert.equal(watcher.stopped, true);
  await watcher.tick();
  assert.equal(changes.length, 0);
});

test("watchJson refuses to run without fetch", () => {
  assert.throws(() => watchJson("x.json", { fetchImpl: null }), /needs fetch/);
  assert.throws(() => watchJson("", {}), /needs a url/);
});
