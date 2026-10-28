/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Live2D adapter — checks the real runtime, refuses to pretend.
 *
 * The viewer at apps/web-live2d-viewer has a Cubism 3 model (Epsilon_free) and
 * the Cubism Core runtime. Wiring the full draw loop into this stage is S1.5's
 * remaining half; this module covers the two things that can be verified
 * headlessly: "is the core loadable?" and "is the model metadata well-formed?".
 *
 * If either fails the stage keeps drawing the procedural figure — a broken
 * Live2D must never be a blank screen.
 */

export const CORE_URL = '../../apps/web-live2d-viewer/libs/live2dcubismcore.min.js'
export const MODEL_URL =
  '../../apps/web-live2d-viewer/models/Epsilon_free/runtime/Epsilon_free.model3.json'

export function coreAvailable(scope = globalThis) {
  return Boolean(scope && scope.Live2DCubismCore)
}

export function defaultLoader(url) {
  return new Promise((resolve, reject) => {
    if (typeof document === 'undefined') {
      reject(new Error('no document: cannot load the Cubism core'))
      return
    }
    const script = document.createElement('script')
    script.src = url
    script.onload = () => resolve(true)
    script.onerror = () => reject(new Error(`failed to load ${url}`))
    document.head.appendChild(script)
  })
}

export async function ensureCore({
  scope = globalThis,
  loader = defaultLoader,
  url = CORE_URL,
} = {}) {
  if (coreAvailable(scope)) return { ok: true, loaded: false }
  try {
    await loader(url)
  } catch (err) {
    return { ok: false, loaded: false, error: err.message }
  }
  return coreAvailable(scope)
    ? { ok: true, loaded: true }
    : { ok: false, loaded: true, error: 'core script loaded but Live2DCubismCore is undefined' }
}

export async function loadModelMeta(url = MODEL_URL, fetchImpl = globalThis.fetch) {
  if (typeof fetchImpl !== 'function') throw new Error('no fetch available')
  const response = await fetchImpl(url, { cache: 'no-store' })
  if (!response.ok) throw new Error(`model metadata HTTP ${response.status}`)
  const meta = await response.json()
  const refs = meta && meta.FileReferences
  if (!refs || !refs.Moc) throw new Error('model metadata has no FileReferences.Moc')
  return meta
}

/** One call for the UI: returns a human-readable verdict, never throws. */
export async function inspectLive2D(options = {}) {
  const core = await ensureCore(options)
  if (!core.ok) return { ok: false, stage: 'core', reason: core.error }
  try {
    const meta = await loadModelMeta(options.modelUrl ?? MODEL_URL, options.fetchImpl)
    return { ok: true, stage: 'metadata', moc: meta.FileReferences.Moc }
  } catch (err) {
    return { ok: false, stage: 'metadata', reason: err.message }
  }
}
