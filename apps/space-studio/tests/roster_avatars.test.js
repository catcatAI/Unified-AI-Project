/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Every roster avatarId must be preloaded, and every preloaded path must exist.
 *
 * ``SpacePort.spawn`` throws ``unknown avatar`` for an id missing from the map,
 * and ``spawnRoster`` runs during boot — so a roster entry without a profile is
 * a blank stage, not a degraded one. This test reads the shipped files.
 */

import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

import { AVATARS } from '../src/avatars.js'

const here = dirname(fileURLToPath(import.meta.url))
const roster = JSON.parse(readFileSync(join(here, '../../../space/roles.json'), 'utf8'))

test('every roster avatarId is preloaded', () => {
  const preloaded = new Set(Object.keys(AVATARS))
  for (const actor of roster.actors) {
    const avatarId = actor.avatar_id ?? 'angela_base'
    assert.ok(preloaded.has(avatarId), `${actor.role_id} needs avatar "${avatarId}" in AVATARS`)
  }
})

test('every preloaded avatar path exists', () => {
  for (const [avatarId, url] of Object.entries(AVATARS)) {
    assert.ok(url.startsWith('../../'), `${avatarId} path must be relative to the page`)
    const file = join(here, '..', url)
    assert.ok(existsSync(file), `${avatarId} points at a missing file: ${file}`)
  }
})

test('every avatar profile declares the id it is registered under', () => {
  for (const [avatarId, url] of Object.entries(AVATARS)) {
    const profile = JSON.parse(readFileSync(join(here, '..', url), 'utf8'))
    assert.equal(profile.avatar_id, avatarId, `${avatarId} profile id mismatch`)
  }
})
