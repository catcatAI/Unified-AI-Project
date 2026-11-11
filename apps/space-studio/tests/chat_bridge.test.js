/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * chat_bridge — a reply that the backend produced, or an honest failure.
 *
 * The point of these tests is the *absence* of a fallback: an offline or
 * failing backend must not turn into locally invented dialogue.
 */

import assert from 'node:assert/strict'
import test from 'node:test'

import { createChatBridge } from '../src/chat_bridge.js'

function jsonResponse(data, status = 200) {
  return { ok: status >= 200 && status < 300, status, json: async () => data }
}

function recorder(payload, status = 200) {
  const calls = []
  const fetchImpl = async (url, init) => {
    calls.push({ url, init })
    return jsonResponse(payload, status)
  }
  return { calls, fetchImpl }
}

test('sends the message through the unified chat endpoint', async () => {
  const { calls, fetchImpl } = recorder({
    response: '巴黎。',
    route: 'knowledge',
    backend: 'knowledge_pipeline',
  })
  const bridge = createChatBridge({
    endpoint: 'http://127.0.0.1:8000/api/v1/chat/unified',
    fetchImpl,
  })

  const result = await bridge.send({
    message: ' 法国的首都是哪里？ ',
    sessionId: 's1',
    roleId: 'main',
  })

  assert.equal(result.ok, true)
  assert.equal(result.text, '巴黎。')
  assert.equal(result.route, 'knowledge')
  assert.equal(result.backend, 'knowledge_pipeline')

  assert.equal(calls.length, 1)
  assert.equal(calls[0].url, 'http://127.0.0.1:8000/api/v1/chat/unified')
  assert.equal(calls[0].init.method, 'POST')
  assert.equal(calls[0].init.headers['Content-Type'], 'application/json')
  const body = JSON.parse(calls[0].init.body)
  assert.equal(body.message, '法国的首都是哪里？')
  assert.equal(body.session_id, 's1')
  assert.equal(body.role_id, 'main')
  assert.equal(body.user_id, 'space_guest')
  assert.equal(body.client_id, 'space_studio')
})

test('passes the abstain envelope through instead of hiding it', async () => {
  const abstain = { v: 1, reason: 'no_answer', language: 'zh', tier: 'honest' }
  const { fetchImpl } = recorder({
    response: '我不知道。',
    route: 'fallback',
    backend: 'local-fallback',
    abstain,
  })
  const bridge = createChatBridge({ fetchImpl })

  const result = await bridge.send({ message: '為什麼天空是藍的？' })

  assert.equal(result.ok, true)
  assert.deepEqual(result.abstain, abstain)
  assert.equal(result.route, 'fallback')
})

test('accepts the legacy message field', async () => {
  const { fetchImpl } = recorder({ message: 'old shape' })
  const result = await createChatBridge({ fetchImpl }).send({ message: 'hi' })
  assert.equal(result.ok, true)
  assert.equal(result.text, 'old shape')
})

test('an unreachable backend is a reason, never a fabricated reply', async () => {
  const bridge = createChatBridge({
    fetchImpl: async () => {
      throw new Error('ECONNREFUSED')
    },
  })

  const result = await bridge.send({ message: '你好' })

  assert.equal(result.ok, false)
  assert.equal(result.reason, 'offline')
  assert.match(result.error, /ECONNREFUSED/)
  assert.equal('text' in result, false, 'no text means the stage stays silent')
})

test('a missing fetch implementation is reported, not papered over', async () => {
  const bridge = createChatBridge({ fetchImpl: null })
  const result = await bridge.send({ message: '你好' })
  assert.equal(result.ok, false)
  assert.equal(result.reason, 'fetch_unavailable')
  assert.equal('text' in result, false)
})

test('an HTTP error reports the status', async () => {
  const bridge = createChatBridge({ fetchImpl: async () => jsonResponse({}, 500) })
  const result = await bridge.send({ message: '你好' })
  assert.equal(result.ok, false)
  assert.equal(result.reason, 'http_500')
  assert.equal(result.status, 500)
})

test('a non-JSON body is an invalid response', async () => {
  const bridge = createChatBridge({
    fetchImpl: async () => ({
      ok: true,
      status: 200,
      json: async () => {
        throw new SyntaxError('Unexpected token')
      },
    }),
  })
  const result = await bridge.send({ message: '你好' })
  assert.equal(result.ok, false)
  assert.equal(result.reason, 'invalid_response')
})

test('an empty backend reply does not become a stage line', async () => {
  const bridge = createChatBridge({ fetchImpl: async () => jsonResponse({ response: '   ' }) })
  const result = await bridge.send({ message: '你好' })
  assert.equal(result.ok, false)
  assert.equal(result.reason, 'empty_response')
})

test('an empty message never reaches the network', async () => {
  const calls = []
  const bridge = createChatBridge({
    fetchImpl: async (...args) => {
      calls.push(args)
      return jsonResponse({ response: 'never' })
    },
  })

  assert.equal((await bridge.send({ message: '' })).reason, 'empty_message')
  assert.equal((await bridge.send({ message: '   ' })).reason, 'empty_message')
  assert.equal((await bridge.send({})).reason, 'empty_message')
  assert.equal(calls.length, 0)
})
