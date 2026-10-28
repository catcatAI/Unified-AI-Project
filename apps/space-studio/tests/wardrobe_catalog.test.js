/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * The wardrobe catalogue must only offer outfits that actually apply.
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { applyOutfit, SLOTS } from "../src/wardrobe.js";

const here = dirname(fileURLToPath(import.meta.url));
const catalog = JSON.parse(readFileSync(join(here, "../../../space/wardrobe/catalog.json"), "utf8"));

const AVATAR = {
  avatar_id: "angela_base",
  rev: 0,
  wardrobe: { slots: { top: { item: "hoodie_blue", tint: "#3b6ea5" } } },
};

test("catalog covers every wardrobe slot", () => {
  assert.deepEqual(Object.keys(catalog.slots).sort(), [...SLOTS].sort());
});

test("every slot has at least two items with valid hex tints", () => {
  for (const [slot, spec] of Object.entries(catalog.slots)) {
    assert.ok(spec.label, `${slot} needs a label`);
    assert.ok(spec.items.length >= 2, `${slot} needs at least two items`);
    for (const item of spec.items) {
      assert.ok(item.id, `${slot} item needs an id`);
      assert.ok(item.label, `${item.id} needs a label`);
      assert.ok(item.tints.length >= 1, `${item.id} needs tints`);
      for (const tint of item.tints) {
        assert.match(tint, /^#[0-9a-fA-F]{6}$/, `${item.id} tint ${tint}`);
      }
    }
  }
});

test("item ids are unique within a slot", () => {
  for (const [slot, spec] of Object.entries(catalog.slots)) {
    const ids = spec.items.map((item) => item.id);
    assert.equal(new Set(ids).size, ids.length, `${slot} has duplicate item ids`);
  }
});

test("every catalogue entry applies without throwing", () => {
  let avatar = AVATAR;
  for (const [slot, spec] of Object.entries(catalog.slots)) {
    for (const item of spec.items) {
      avatar = applyOutfit(avatar, { slot, item: item.id, tint: item.tints[0] });
      assert.equal(avatar.wardrobe.slots[slot].item, item.id);
    }
  }
  assert.ok(avatar.rev > 0);
});
