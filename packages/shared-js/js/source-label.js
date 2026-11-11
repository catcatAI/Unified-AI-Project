/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [β] [B] [L3]
 * =============================================================================
 * Source labels — what produced an answer, in words a user can check.
 *
 * The backend already reports the layer behind a reply (`route`: computed /
 * knowledge / memory / template / llm / fallback), but the chat UI used to
 * throw it away, so a looked-up sentence and a generated one looked identical.
 * This module is the single mapping from that route to a label + hint.
 *
 * Pure by design: no DOM, no network, CommonJS-exported so it can be tested
 * under Node. Browsers get `window.AngelaSourceLabel`.
 *
 * Labels are deliberately about the layer, not the engine name: "did this come
 * from a calculation, a lookup, your own earlier words, or was it generated?"
 * A user who cannot tell those apart cannot judge whether to trust the reply.
 */

const SOURCE_LABELS = {
  computed: {
    key: 'computed',
    label: '計算',
    hint: '由確定性引擎算出（數字、單位、公式），不是模型生成',
  },
  knowledge: {
    key: 'knowledge',
    label: '知識',
    hint: '從知識庫或百科檢索而來，可能附出處',
  },
  memory: {
    key: 'memory',
    label: '記憶',
    hint: '你先前告訴我的事，可能已經過時，可以更正',
  },
  template: {
    key: 'template',
    label: '模板',
    hint: '固定的說法，不是針對這句話生成的',
  },
  generated: {
    key: 'generated',
    label: '生成',
    hint: '由模型或神經引擎產生，可能出錯',
  },
  fallback: {
    key: 'fallback',
    label: '兜底',
    hint: '沒有找到可靠來源，這句可能是兜底話術',
  },
  unknown: {
    key: 'unknown',
    label: '未知',
    hint: '這條回覆沒有標示來源',
  },
}

// route -> bucket. `route` is derived server-side in
// api/routes/chat_routes.py::_format_chat_response; anything not listed here
// must fall through to `unknown` rather than be guessed into a safer bucket.
const ROUTE_BUCKETS = {
  computed: 'computed',
  knowledge: 'knowledge',
  memory: 'memory',
  template: 'template',
  llm: 'generated',
  model_bus: 'generated',
  ed3n: 'generated',
  garden: 'generated',
  unified: 'generated',
  fallback: 'fallback',
  error: 'fallback',
}

function labelFor(route) {
  const key = String(route || '')
    .trim()
    .toLowerCase()
  const bucket = ROUTE_BUCKETS[key] || 'unknown'
  return { ...SOURCE_LABELS[bucket], route: key || 'unknown' }
}

if (typeof window !== 'undefined') {
  window.AngelaSourceLabel = { SOURCE_LABELS, ROUTE_BUCKETS, labelFor }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { SOURCE_LABELS, ROUTE_BUCKETS, labelFor }
}
