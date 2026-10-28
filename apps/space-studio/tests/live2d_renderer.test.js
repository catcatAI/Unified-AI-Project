/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * S1.5 probe: Live2D core/model detection with a fake loader and fake fetch.
 */

import assert from 'node:assert/strict'
import test from 'node:test'

import {
  coreAvailable,
  ensureCore,
  inspectLive2D,
  loadModelMeta,
  MODEL_URL,
} from '../src/live2d_renderer.js'

const META = { Version: 3, FileReferences: { Moc: 'Epsilon_free.moc3' } }

test('core detection is a plain global check', () => {
  assert.equal(coreAvailable({}), false)
  assert.equal(coreAvailable({ Live2DCubismCore: {} }), true)
})

test('ensureCore short-circuits when the core is already there', async () => {
  let called = 0
  const result = await ensureCore({
    scope: { Live2DCubismCore: {} },
    loader: async () => {
      called += 1
    },
  })
  assert.deepEqual(result, { ok: true, loaded: false })
  assert.equal(called, 0)
})

test('ensureCore reports a failed script load', async () => {
  const result = await ensureCore({
    scope: {},
    loader: async () => {
      throw new Error('404')
    },
  })
  assert.equal(result.ok, false)
  assert.match(result.error, /404/)
})

test('ensureCore reports a script that loads but defines nothing', async () => {
  const result = await ensureCore({ scope: {}, loader: async () => true })
  assert.equal(result.ok, false)
  assert.match(result.error, /undefined/)
})

test('a loader that installs the global is accepted', async () => {
  const scope = {}
  const result = await ensureCore({
    scope,
    loader: async () => {
      scope.Live2DCubismCore = {}
    },
  })
  assert.deepEqual(result, { ok: true, loaded: true })
})

test('loadModelMeta reads the moc reference', async () => {
  const meta = await loadModelMeta(MODEL_URL, async () => ({ ok: true, json: async () => META }))
  assert.equal(meta.FileReferences.Moc, 'Epsilon_free.moc3')
})

test('loadModelMeta rejects HTTP errors and malformed metadata', async () => {
  await assert.rejects(
    () => loadModelMeta(MODEL_URL, async () => ({ ok: false, status: 404 })),
    /HTTP 404/
  )
  await assert.rejects(
    () => loadModelMeta(MODEL_URL, async () => ({ ok: true, json: async () => ({}) })),
    /no FileReferences/
  )
})

test('inspectLive2D returns a verdict instead of throwing', async () => {
  const bad = await inspectLive2D({
    scope: {},
    loader: async () => {
      throw new Error('blocked')
    },
  })
  assert.equal(bad.ok, false)
  assert.equal(bad.stage, 'core')

  const good = await inspectLive2D({
    scope: { Live2DCubismCore: {} },
    fetchImpl: async () => ({ ok: true, json: async () => META }),
  })
  assert.equal(good.ok, true)
  assert.equal(good.moc, 'Epsilon_free.moc3')
})
