/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * S2: wardrobe store — apply, undo, persist, rehydrate.
 */

import assert from 'node:assert/strict'
import test from 'node:test'

import { OutfitStore, loadOutfits } from '../src/outfit_store.js'

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

class FakeStorage {
  constructor() {
    this.map = new Map()
  }

  getItem(key) {
    return this.map.get(key) ?? null
  }

  setItem(key, value) {
    this.map.set(key, String(value))
  }
}

test('set changes one slot and bumps the revision', () => {
  const store = new OutfitStore({ ...AVATAR, wardrobe: { slots: { ...AVATAR.wardrobe.slots } } })
  const next = store.set({ slot: 'top', item: 'jacket_purple', tint: '#6a4f9e' })
  assert.equal(next.rev, 1)
  assert.equal(store.avatar.wardrobe.slots.top.item, 'jacket_purple')
  assert.equal(store.avatar.wardrobe.slots.top.tint, '#6a4f9e')
})

test('undo restores the previous outfit', () => {
  const store = new OutfitStore({ ...AVATAR, wardrobe: { slots: { ...AVATAR.wardrobe.slots } } })
  store.set({ slot: 'top', item: 'jacket_purple', tint: '#6a4f9e' })
  assert.equal(store.canUndo, true)
  const back = store.undo()
  assert.equal(back.wardrobe.slots.top.item, 'hoodie_blue')
  assert.equal(store.canUndo, false)
  assert.equal(store.undo(), store.avatar, 'undo on empty history is a no-op')
})

test('history is bounded', () => {
  const store = new OutfitStore(
    { ...AVATAR, wardrobe: { slots: { ...AVATAR.wardrobe.slots } } },
    { historyLimit: 2 }
  )
  store.set({ slot: 'top', item: 'a', tint: '#111111' })
  store.set({ slot: 'top', item: 'b', tint: '#222222' })
  store.set({ slot: 'top', item: 'c', tint: '#333333' })
  store.undo()
  store.undo()
  assert.equal(store.canUndo, false)
})

test('outfit is persisted under the avatar id and reloads', () => {
  const storage = new FakeStorage()
  const store = new OutfitStore(
    { ...AVATAR, wardrobe: { slots: { ...AVATAR.wardrobe.slots } } },
    { storage }
  )
  store.set({ slot: 'accessory', item: 'ribbon', tint: '#d94f70' })

  const saved = loadOutfits(storage)
  assert.equal(saved.angela_base.wardrobe.slots.accessory.item, 'ribbon')

  const reloaded = new OutfitStore(
    { ...AVATAR, wardrobe: { slots: { ...AVATAR.wardrobe.slots } } },
    { storage }
  )
  assert.equal(reloaded.avatar.wardrobe.slots.accessory.tint, '#d94f70')
  assert.equal(reloaded.avatar.rev, 1)
})

test("corrupt storage falls back to the avatar's own outfit", () => {
  const storage = new FakeStorage()
  storage.setItem('space.outfits.v1', '{broken')
  const store = new OutfitStore(
    { ...AVATAR, wardrobe: { slots: { ...AVATAR.wardrobe.slots } } },
    { storage }
  )
  assert.equal(store.avatar.wardrobe.slots.top.item, 'hoodie_blue')
})

test('storage failures never break dressing', () => {
  const hostile = {
    getItem() {
      throw new Error('denied')
    },
    setItem() {
      throw new Error('denied')
    },
  }
  const store = new OutfitStore(
    { ...AVATAR, wardrobe: { slots: { ...AVATAR.wardrobe.slots } } },
    { storage: hostile }
  )
  assert.doesNotThrow(() => store.set({ slot: 'top', item: 'x', tint: '#123456' }))
})

test('unknown slot and bad tint are rejected', () => {
  const store = new OutfitStore({ ...AVATAR, wardrobe: { slots: {} } })
  assert.throws(() => store.set({ slot: 'hat', item: 'beret' }), /unknown wardrobe slot/)
  assert.throws(() => store.set({ slot: 'top', item: 'x', tint: 'red' }), /#rrggbb/)
})

test('restore replaces the wardrobe without touching history', () => {
  const store = new OutfitStore({ ...AVATAR, wardrobe: { slots: {} } })
  store.set({ slot: 'top', item: 'a', tint: '#111111' })
  store.restore({ rev: 7, wardrobe: { slots: { top: { item: 'z', tint: '#222222' } } } })
  assert.equal(store.avatar.rev, 7)
  assert.equal(store.avatar.wardrobe.slots.top.item, 'z')
  assert.equal(store.canUndo, false)
})
