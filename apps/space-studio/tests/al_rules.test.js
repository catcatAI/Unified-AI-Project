/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * S3 finish: AL vitals → motion rules.
 */

import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

import { parseRules, pickMotion } from '../src/al_rules.js'

const here = dirname(fileURLToPath(import.meta.url))
const shipped = JSON.parse(readFileSync(join(here, '../../../space/rules/al_motion.json'), 'utf8'))

test('the shipped rules parse and are sorted by priority', () => {
  const { ok, errors, rules } = parseRules(shipped)
  assert.equal(ok, true, errors.join(', '))
  assert.equal(rules.length, 4)
  assert.deepEqual(
    rules.map((r) => r.motion),
    ['sit_down', 'nod', 'wave_hello', 'nod']
  )
})

test('very tired prefers sitting down', () => {
  const { rules } = parseRules(shipped)
  assert.equal(pickMotion({ fatigue: 0.9, stress: 0.1, valence: 0.5 }, rules).motion, 'sit_down')
})

test('high stress beats a good mood', () => {
  const { rules } = parseRules(shipped)
  assert.equal(pickMotion({ fatigue: 0.2, stress: 0.85, valence: 0.9 }, rules).motion, 'nod')
})

test('happy and calm waves', () => {
  const { rules } = parseRules(shipped)
  assert.equal(pickMotion({ fatigue: 0.1, stress: 0.1, valence: 0.8 }, rules).motion, 'wave_hello')
})

test('neutral emotion falls through to the low-priority rule', () => {
  const { rules } = parseRules(shipped)
  const picked = pickMotion({ fatigue: 0.1, stress: 0.1, valence: 0.2, emotion: 'neutral' }, rules)
  assert.equal(picked.motion, 'nod')
  assert.equal(picked.priority, 10)
})

test('no matching rule returns null, not a default', () => {
  const { rules } = parseRules(shipped)
  assert.equal(pickMotion({ fatigue: 0.1, stress: 0.1, valence: 0.2 }, rules), null)
})

test('a missing field means the rule does not match', () => {
  const { rules } = parseRules({ rules: [{ motion: 'x', when: { stress: { gte: 0.5 } } }] })
  assert.equal(pickMotion({}, rules), null)
  assert.equal(pickMotion({ stress: 0.6 }, rules).motion, 'x')
})

test('parseRules reports structural errors', () => {
  assert.equal(parseRules({ rules: [{ when: { stress: { gte: 0.5 } } }] }).ok, false)
  assert.equal(parseRules({ rules: [{ motion: 'x' }] }).ok, false)
  assert.equal(parseRules({ rules: [{ motion: 'x', when: { stress: { between: 1 } } }] }).ok, false)
})

test('a JSON string is accepted', () => {
  const { ok } = parseRules(
    JSON.stringify({ rules: [{ motion: 'x', when: { stress: { gte: 1 } } }] })
  )
  assert.equal(ok, true)
})

test('lte and eq operators work', () => {
  const { rules } = parseRules({
    rules: [
      { motion: 'calm', when: { stress: { lte: 0.2 } }, priority: 2 },
      { motion: 'sad', when: { emotion: { eq: 'sad' } }, priority: 1 },
    ],
  })
  assert.equal(pickMotion({ stress: 0.1 }, rules).motion, 'calm')
  assert.equal(pickMotion({ emotion: 'sad' }, rules).motion, 'sad')
})
