/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Camera and wardrobe — the two pure modules the renderer depends on.
 */

import assert from 'node:assert/strict'
import test from 'node:test'

import { PRESETS, project, resolveCamera, unitScale } from '../src/camera.js'
import { applyOutfit, cycleTint, outfitColors, SLOTS } from '../src/wardrobe.js'

const VIEWPORT = { width: 960, height: 540, worldWidth: 16, worldHeight: 9 }

const AVATAR = {
  avatar_id: 'angela_base',
  rev: 0,
  wardrobe: {
    slots: {
      top: { item: 'hoodie_blue', tint: '#3b6ea5' },
      bottom: { item: 'skirt_plaid', tint: '#6b4f3a' },
    },
  },
}

test('presets are known and overrides win', () => {
  assert.equal(resolveCamera('close').zoom, PRESETS.close.zoom)
  const cam = resolveCamera('wide', { panX: 0.5 })
  assert.equal(cam.preset, 'wide')
  assert.equal(cam.panX, 0.5)
})

test('unknown preset throws instead of silently defaulting', () => {
  assert.throws(() => resolveCamera('dutch_angle'), /unknown camera preset/)
})

test('zooming in increases the distance between two projected points', () => {
  const wide = resolveCamera('wide')
  const close = resolveCamera('close')
  const spread = (cam) => project([10, 0], cam, VIEWPORT)[0] - project([6, 0], cam, VIEWPORT)[0]
  assert.ok(spread(close) > spread(wide))
})

test('pan shifts the projection without changing scale', () => {
  const base = resolveCamera('medium')
  const panned = { ...base, panX: 0.1 }
  const [x1] = project([8, 0], base, VIEWPORT)
  const [x2] = project([8, 0], panned, VIEWPORT)
  assert.ok(Math.abs(x2 - x1 - 96) < 1e-9)
  assert.equal(unitScale(base, VIEWPORT), unitScale(panned, VIEWPORT))
})

test('higher world y projects to a smaller pixel y (up is up)', () => {
  const cam = resolveCamera('wide')
  assert.ok(project([8, 2], cam, VIEWPORT)[1] < project([8, 0], cam, VIEWPORT)[1])
})

test('applyOutfit bumps the revision and replaces the slot', () => {
  const next = applyOutfit(AVATAR, { slot: 'top', item: 'jacket_red', tint: '#aa2233' })
  assert.equal(next.rev, 1)
  assert.equal(next.wardrobe.slots.top.item, 'jacket_red')
  assert.equal(next.wardrobe.slots.top.tint, '#aa2233')
  assert.equal(AVATAR.wardrobe.slots.top.item, 'hoodie_blue', 'input must not mutate')
})

test('applyOutfit keeps an existing tint when none is given', () => {
  const next = applyOutfit(AVATAR, { slot: 'bottom', item: 'shorts' })
  assert.equal(next.wardrobe.slots.bottom.tint, '#6b4f3a')
})

test('applyOutfit rejects unknown slots, missing items and bad tints', () => {
  assert.throws(() => applyOutfit(AVATAR, { slot: 'hat', item: 'beret' }), /unknown wardrobe slot/)
  assert.throws(() => applyOutfit(AVATAR, { slot: 'top' }), /needs an item/)
  assert.throws(() => applyOutfit(AVATAR, { slot: 'top', item: 'x', tint: 'red' }), /#rrggbb/)
})

test('outfitColors fills every slot with a stable fallback', () => {
  const colors = outfitColors(AVATAR)
  assert.deepEqual(Object.keys(colors).sort(), [...SLOTS].sort())
  assert.equal(colors.top, '#3b6ea5')
  assert.equal(colors.shoes, '#cccccc')
})

test('cycleTint rotates through the palette', () => {
  const palette = ['#111111', '#222222']
  const first = cycleTint(AVATAR, 'top', palette)
  assert.equal(first.wardrobe.slots.top.tint, '#111111')
  const second = cycleTint(first, 'top', palette)
  assert.equal(second.wardrobe.slots.top.tint, '#222222')
  const third = cycleTint(second, 'top', palette)
  assert.equal(third.wardrobe.slots.top.tint, '#111111')
})
