/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Outfit store — the wardrobe's memory.
 *
 * One avatar in, an undo stack out. Persistence is injected (localStorage in
 * the browser, a fake in tests) so nothing here depends on a DOM.
 */

import { applyOutfit, SLOTS } from './wardrobe.js'

const STORAGE_KEY = 'space.outfits.v1'

export class OutfitStore {
  constructor(avatar, { storage = null, key = STORAGE_KEY, historyLimit = 20 } = {}) {
    this._avatar = avatar
    this._history = []
    this._storage = storage
    this._key = key
    this._historyLimit = historyLimit
    this._restore()
  }

  get avatar() {
    return this._avatar
  }

  get canUndo() {
    return this._history.length > 0
  }

  /** Change one slot; returns the new avatar. */
  set({ slot, item, tint }) {
    if (!SLOTS.includes(slot)) throw new Error(`unknown wardrobe slot: ${slot}`)
    this._history.push(this._avatar)
    if (this._history.length > this._historyLimit) this._history.shift()
    this._avatar = applyOutfit(this._avatar, { slot, item, tint })
    this._persist()
    return this._avatar
  }

  undo() {
    const previous = this._history.pop()
    if (!previous) return this._avatar
    this._avatar = previous
    this._persist()
    return this._avatar
  }

  /** Serialisable: only the wardrobe + revision matter for rehydration. */
  toJSON() {
    return { rev: this._avatar.rev ?? 0, wardrobe: this._avatar.wardrobe ?? {} }
  }

  restore(snapshot) {
    if (!snapshot || typeof snapshot !== 'object') return this._avatar
    this._avatar = {
      ...this._avatar,
      rev: Number(snapshot.rev ?? this._avatar.rev ?? 0),
      wardrobe: { ...(this._avatar.wardrobe ?? {}), ...(snapshot.wardrobe ?? {}) },
    }
    this._history = []
    return this._avatar
  }

  clearHistory() {
    this._history = []
  }

  _persist() {
    if (!this._storage) return
    try {
      const all = JSON.parse(this._storage.getItem(this._key) ?? '{}')
      all[this._avatar.avatar_id] = this.toJSON()
      this._storage.setItem(this._key, JSON.stringify(all))
    } catch {
      // A full or disabled storage must not break dressing.
    }
  }

  _restore() {
    if (!this._storage) return
    try {
      const all = JSON.parse(this._storage.getItem(this._key) ?? '{}')
      const saved = all[this._avatar.avatar_id]
      if (saved) this.restore(saved)
    } catch {
      // Corrupt payload: start from the avatar's own outfit.
    }
  }
}

/** Read every saved outfit (used by the stage to rehydrate all actors). */
export function loadOutfits(storage, key = STORAGE_KEY) {
  if (!storage) return {}
  try {
    return JSON.parse(storage.getItem(key) ?? '{}')
  } catch {
    return {}
  }
}
