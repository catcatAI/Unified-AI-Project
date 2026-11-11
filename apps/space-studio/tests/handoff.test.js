/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * handoff — the host opens, the main role takes over, chat is gated in between.
 */

import assert from 'node:assert/strict'
import test from 'node:test'

import { createHandoff, HANDOFF_STATE } from '../src/handoff.js'

function stage() {
  const calls = []
  const say = (roleId, text, durationMs) => calls.push({ roleId, text, durationMs })
  return { calls, say }
}

function manualSchedule() {
  const timers = []
  const schedule = (fn, ms) => {
    timers.push({ fn, ms })
    return timers.length
  }
  return { timers, schedule }
}

test('chat is closed until the host has actually opened', () => {
  const { say } = stage()
  const handoff = createHandoff({ say })

  assert.equal(handoff.state, HANDOFF_STATE.CLOSED)
  assert.equal(handoff.canChat(), false)
})

test('opening speaks the host line, then hands over to the main role', () => {
  const { calls, say } = stage()
  const { timers, schedule } = manualSchedule()
  const handoff = createHandoff({ say, schedule, openingMs: 2000, gapMs: 500 })

  const result = handoff.open()

  assert.deepEqual(result, { ok: true, state: HANDOFF_STATE.OPENING })
  assert.equal(handoff.canChat(), false, 'the opening is not the handover')
  assert.equal(calls.length, 1)
  assert.equal(calls[0].roleId, 'host')
  assert.equal(calls[0].text, '歡迎來到這裡。接下來交給 Angela 陪你聊聊。')
  assert.equal(calls[0].durationMs, 2000)

  assert.equal(timers.length, 1)
  assert.equal(timers[0].ms, 2500, 'wait for the opening bubble before the handover')

  timers[0].fn()

  assert.equal(handoff.state, HANDOFF_STATE.OPEN)
  assert.equal(handoff.canChat(), true)
  assert.equal(calls.length, 2)
  assert.equal(calls[1].roleId, 'main')
  assert.match(calls[1].text, /交給我/)
})

test('a second open does not restart the handover', () => {
  const { calls, say } = stage()
  const handoff = createHandoff({ say, schedule: () => 1 })

  handoff.open()
  const second = handoff.open()

  assert.equal(second.ok, false)
  assert.equal(second.reason, 'already_started')
  assert.equal(calls.length, 1, 'the host does not clear their throat twice')
})

test('subscribers see the state change and can unsubscribe', () => {
  const { say } = stage()
  const { timers, schedule } = manualSchedule()
  const handoff = createHandoff({ say, schedule })
  const seen = []
  const unsubscribe = handoff.subscribe((state) => seen.push(state))

  handoff.open()
  timers[0].fn()
  unsubscribe()
  handoff.subscribe(() => seen.push('late'))

  assert.deepEqual(seen, [HANDOFF_STATE.OPENING, HANDOFF_STATE.OPEN])
})

test('a missing host actor is reported but does not lock the gate', () => {
  const say = (roleId) => {
    if (roleId === 'host') throw new Error('unknown actor: host')
  }
  const { timers, schedule } = manualSchedule()
  const handoff = createHandoff({ say, schedule })

  handoff.open()

  assert.equal(handoff.lastError, 'host: unknown actor: host')
  timers[0].fn()
  assert.equal(handoff.canChat(), true, 'a stage defect must not hold chat shut forever')
})

test('a broken scheduler still completes the handover', () => {
  const calls = []
  const handoff = createHandoff({
    say: (roleId) => calls.push(roleId),
    schedule: () => {
      throw new Error('no timers here')
    },
  })

  handoff.open()

  assert.equal(handoff.state, HANDOFF_STATE.OPEN)
  assert.equal(handoff.canChat(), true)
  assert.deepEqual(calls, ['host', 'main'])
  assert.match(handoff.lastError, /schedule/)
})

test('a failing subscriber cannot stall the handover', () => {
  const { say } = stage()
  const { timers, schedule } = manualSchedule()
  const handoff = createHandoff({ say, schedule })
  handoff.subscribe(() => {
    throw new Error('bad listener')
  })

  assert.doesNotThrow(() => handoff.open())
  assert.doesNotThrow(() => timers[0].fn())
  assert.equal(handoff.canChat(), true)
})

test('say is mandatory', () => {
  assert.throws(() => createHandoff({}), /say/)
})
