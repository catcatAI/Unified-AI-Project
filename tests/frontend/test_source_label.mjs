/**
 * Answer-source labels (node:test) — the chat UI must not show a lookup and a
 * generation the same way.
 *
 * The mapping is pure and CommonJS-exported precisely so this file can assert
 * it without a DOM. The Python bridge (test_source_label_node.py) additionally
 * checks that every `route` the backend can emit is covered here.
 *
 * Run: node --test tests/frontend/test_source_label.mjs
 */
import assert from 'node:assert/strict'
import path from 'node:path'
import { createRequire } from 'node:module'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..')
const require = createRequire(import.meta.url)
const { labelFor, SOURCE_LABELS, ROUTE_BUCKETS } = require(
  path.join(ROOT, 'packages', 'shared-js', 'js', 'source-label.js')
)

test('every bucket carries a non-empty label and hint', () => {
  const buckets = Object.entries(SOURCE_LABELS)
  assert.ok(buckets.length >= 6)
  for (const [key, value] of buckets) {
    assert.equal(value.key, key)
    assert.ok(value.label.length > 0, `${key} has no label`)
    assert.ok(value.hint.length > 0, `${key} has no hint`)
  }
})

test('each known route keeps its own bucket', () => {
  assert.equal(labelFor('computed').label, '計算')
  assert.equal(labelFor('knowledge').label, '知識')
  assert.equal(labelFor('memory').label, '記憶')
  assert.equal(labelFor('template').label, '模板')
  assert.equal(labelFor('llm').label, '生成')
  assert.equal(labelFor('fallback').label, '兜底')
})

test('engine names do not leak into the label', () => {
  // A user must not have to know which backend answered; "generated" is the
  // claim, and the engine name is not evidence of anything they can check.
  const engines = ['model_bus', 'ed3n', 'garden', 'unified', 'llm']
  const labels = new Set(engines.map((route) => labelFor(route).label))
  assert.deepEqual([...labels], ['生成'])
  assert.equal(labelFor('garden').route, 'garden')
})

test('an unknown route is reported as unknown, never guessed into a safer bucket', () => {
  for (const route of ['', null, undefined, 'some-new-engine', 'computed-ish']) {
    const meta = labelFor(route)
    assert.equal(meta.key, 'unknown', `route ${String(route)} was guessed`)
    assert.equal(meta.label, '未知')
  }
})

test('route matching tolerates case and whitespace', () => {
  assert.equal(labelFor('  COMPUTED ').key, 'computed')
  assert.equal(labelFor('Knowledge').key, 'knowledge')
})

test('every bucket in the route table exists in the label table', () => {
  for (const [route, bucket] of Object.entries(ROUTE_BUCKETS)) {
    assert.ok(SOURCE_LABELS[bucket], `${route} points at missing bucket ${bucket}`)
  }
})
