/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * S3: a motion's tracks actually move the drawn actor.
 */

import assert from 'node:assert/strict'
import test from 'node:test'

import { Actor } from '../src/actors.js'
import { resolveCamera } from '../src/camera.js'
import { createMotion } from '../src/motion_editor.js'
import { drawStage } from '../src/renderer.js'

const AVATAR = {
  avatar_id: 'angela_base',
  display_name: 'Angela',
  expression_channels: ['neutral'],
  wardrobe: { slots: { top: { tint: '#3b6ea5' } } },
  rev: 0,
}
const VIEWPORT = { width: 960, height: 540, worldWidth: 16, worldHeight: 9 }
const ROOM = { palette: { sky: ['#111', '#222'] } }

function fakeContext() {
  const calls = []
  const ctx = new Proxy(
    {},
    {
      get(_t, prop) {
        if (prop === 'createLinearGradient') return () => ({ addColorStop() {} })
        if (prop === 'measureText') return (text) => ({ width: String(text).length * 6 })
        return (...args) => {
          calls.push([prop, args])
        }
      },
      set() {
        return true
      },
    }
  )
  return { ctx, calls }
}

function shadowY(actor) {
  const { ctx, calls } = fakeContext()
  drawStage(ctx, { room: ROOM, actors: [actor], camera: resolveCamera('wide'), viewport: VIEWPORT })
  const ellipse = calls.find(([name]) => name === 'ellipse')
  return ellipse[1][1]
}

const bounce = () =>
  createMotion({
    id: 'bounce',
    durationMs: 1000,
    tracks: {
      offset_y: [
        [0, 0],
        [500, 0.6],
        [1000, 0],
      ],
    },
  })

test('a motion with tracks samples a pose', () => {
  const actor = new Actor({ id: 'a', avatar: AVATAR })
  actor.play(bounce())
  actor.update(500)
  assert.equal(actor.pose.offset_y, 0.6)
})

test('pose offset_y lifts the drawn actor off the floor', () => {
  const still = new Actor({ id: 'a', avatar: AVATAR })
  const lifted = new Actor({ id: 'a', avatar: AVATAR })
  lifted.play(bounce())
  lifted.update(500)
  assert.ok(shadowY(lifted) < shadowY(still) - 5, 'pose should move the shadow up')
})

test('clearing the motion resets the pose', () => {
  const actor = new Actor({ id: 'a', avatar: AVATAR })
  actor.play(bounce())
  actor.update(500)
  actor.clearMotion()
  assert.deepEqual(actor.pose, {})
})

test('motions without tracks leave the pose empty', () => {
  const actor = new Actor({ id: 'a', avatar: AVATAR })
  actor.play({ id: 'idle_breath', durationMs: 2600, loop: true })
  actor.update(100)
  assert.deepEqual(actor.pose, {})
})

test('renderer draws a rotated right arm when arm_r is set', () => {
  const motion = createMotion({
    id: 'wave',
    durationMs: 1000,
    tracks: {
      arm_r: [
        [0, 1.2],
        [1000, 1.2],
      ],
    },
  })
  const actor = new Actor({ id: 'a', avatar: AVATAR })
  actor.play(motion)
  actor.update(500)
  const { ctx, calls } = fakeContext()
  drawStage(ctx, { room: ROOM, actors: [actor], camera: resolveCamera('wide'), viewport: VIEWPORT })
  assert.ok(
    calls.some(([name]) => name === 'stroke'),
    'arm stroke missing'
  )
})
