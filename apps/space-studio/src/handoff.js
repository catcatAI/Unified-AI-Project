/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * handoff — the host opens the scene, then gives the floor to the main role.
 *
 * This is a deliberate gate, not decoration: chat stays closed until the
 * opening has been spoken, so a conversation cannot begin by itself and the
 * page cannot imply the host already greeted the visitor. The state machine is
 * the only authority on that; the UI merely mirrors `canChat()`.
 *
 * The handover line is fixed stage copy (the host is handing over), never a
 * substitute for a backend reply — a failed chat request leaves the stage
 * silent instead of filling the gap here.
 */

export const HANDOFF_STATE = Object.freeze({
  CLOSED: 'closed',
  OPENING: 'opening',
  OPEN: 'open',
})

/**
 * @param {object} options
 * @param {Function} options.say `(roleId, text, durationMs)` — the stage.
 * @param {Function} [options.schedule] injected timer for tests.
 * @param {string} [options.host] role that opens.
 * @param {string} [options.main] role that takes over.
 * @param {string} [options.opening] host line.
 * @param {string} [options.handover] main line at the handover.
 * @param {number} [options.openingMs] how long the opening bubble lives.
 * @param {number} [options.gapMs] pause between opening and handover.
 */
export function createHandoff({
  say,
  schedule = (fn, ms) => setTimeout(fn, ms),
  host = 'host',
  main = 'main',
  opening = '歡迎來到這裡。接下來交給 Angela 陪你聊聊。',
  handover = '交給我吧。你想聊什麼？',
  openingMs = 2600,
  gapMs = 600,
} = {}) {
  if (typeof say !== 'function') throw new Error('handoff needs a say(roleId, text, ms) function')

  const listeners = new Set()
  let state = HANDOFF_STATE.CLOSED
  let lastError = null
  let timer = null

  function notify() {
    for (const listener of listeners) {
      try {
        listener(state)
      } catch {
        // A broken UI subscriber must not stall the handover.
      }
    }
  }

  function speak(roleId, text, durationMs) {
    try {
      say(roleId, text, durationMs)
      return true
    } catch (error) {
      // The stage lacking an actor is worth reporting, but it must not hold
      // chat hostage forever: the intent (host opened, main takes over) still
      // stands, and the UI surfaces `lastError`.
      lastError = `${roleId}: ${error?.message ?? error}`
      return false
    }
  }

  function tick() {
    timer = null
    speak(main, handover, openingMs)
    state = HANDOFF_STATE.OPEN
    notify()
  }

  function canChat() {
    return state === HANDOFF_STATE.OPEN
  }

  function open() {
    if (state !== HANDOFF_STATE.CLOSED) {
      return { ok: false, state, reason: 'already_started' }
    }
    state = HANDOFF_STATE.OPENING
    speak(host, opening, openingMs)
    notify()
    try {
      timer = schedule(tick, openingMs + gapMs)
    } catch (error) {
      // Same rule as a failing speaker: never leave the gate permanently shut.
      lastError = `schedule: ${error?.message ?? error}`
      tick()
    }
    return { ok: true, state }
  }

  function subscribe(listener) {
    if (typeof listener !== 'function') throw new Error('subscribe needs a function')
    listeners.add(listener)
    return () => listeners.delete(listener)
  }

  return {
    open,
    canChat,
    subscribe,
    get state() {
      return state
    },
    get lastError() {
      return lastError
    },
    get pending() {
      return timer !== null
    },
  }
}
