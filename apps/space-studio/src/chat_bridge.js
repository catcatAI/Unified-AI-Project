/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * chat_bridge — the stage's one call into the real chat pipeline.
 *
 * The stage may *show* an answer; it may not invent one. This module therefore
 * has exactly two outcomes: a reply that the backend actually produced (with
 * the layer that produced it), or a failure that says what failed. There is no
 * fallback sentence and no local canned answer — an offline backend means the
 * character is silent, not that the page speaks for her.
 *
 * Contract: POST /api/v1/chat/unified (apps/backend/src/api/routes/chat_routes.py).
 */

export const DEFAULT_CHAT_ENDPOINT = '/api/v1/chat/unified'

function describeError(error) {
  if (!error) return 'unknown'
  if (typeof error === 'string') return error
  return error.message || error.name || 'unknown'
}

/**
 * @param {object} options
 * @param {string} [options.endpoint] chat endpoint (absolute when the stage is
 *   served from a different origin than the backend)
 * @param {Function} [options.fetchImpl] injected for tests
 * @param {number} [options.timeoutMs] 0 disables the timeout
 * @param {string} [options.userId] stable identity key (never the display name)
 * @param {string} [options.tenantId] tenant partition
 * @param {string} [options.personaId] persona the reply should come from
 * @param {string} [options.clientId] origin tag recorded by the backend
 */
export function createChatBridge({
  endpoint = DEFAULT_CHAT_ENDPOINT,
  fetchImpl = globalThis.fetch,
  timeoutMs = 30000,
  userId = 'space_guest',
  tenantId = 'default',
  personaId = 'angela',
  clientId = 'space_studio',
} = {}) {
  async function send({ message, sessionId, roleId, history, signal } = {}) {
    const text = typeof message === 'string' ? message.trim() : ''
    if (!text) return { ok: false, reason: 'empty_message' }
    if (typeof fetchImpl !== 'function') return { ok: false, reason: 'fetch_unavailable' }

    const body = {
      message: text,
      user_id: userId,
      tenant_id: tenantId,
      persona_id: personaId,
      client_id: clientId,
    }
    if (sessionId) body.session_id = sessionId
    if (roleId) body.role_id = roleId
    if (Array.isArray(history) && history.length) body.history = history

    const requestSignal =
      signal ||
      (timeoutMs > 0 && globalThis.AbortSignal?.timeout
        ? globalThis.AbortSignal.timeout(timeoutMs)
        : undefined)

    let response
    try {
      response = await fetchImpl(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: requestSignal,
      })
    } catch (error) {
      // A disconnected backend is a *reason*, not a prompt to improvise.
      return { ok: false, reason: 'offline', error: describeError(error) }
    }

    if (!response || !response.ok) {
      return {
        ok: false,
        reason: `http_${response?.status ?? 'unknown'}`,
        status: response?.status ?? null,
      }
    }

    let data
    try {
      data = await response.json()
    } catch (error) {
      return { ok: false, reason: 'invalid_response', error: describeError(error) }
    }

    const reply = data?.response ?? data?.message ?? ''
    if (typeof reply !== 'string' || !reply.trim()) {
      return { ok: false, reason: 'empty_response', raw: data }
    }

    return {
      ok: true,
      text: reply,
      // Which layer produced it, straight from the backend: the UI must be
      // able to show "this was a lookup / computed / abstained", not just text.
      route: data.route ?? 'unknown',
      backend: data.backend ?? 'unknown',
      source: data.source ?? '',
      abstain: data.abstain ?? null,
      raw: data,
    }
  }

  return { endpoint, send }
}
