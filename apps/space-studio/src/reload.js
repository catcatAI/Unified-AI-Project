/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Hot reload — poll a JSON file and hand back a new value only when it changed.
 *
 * The stage's room, wardrobe and motion data are plain JSON; editing them
 * should not require a restart. Polling (not SSE) on purpose: it works from a
 * static file server with no backend, which is how the stage is usually run.
 */

export function watchJson(
  url,
  {
    intervalMs = 5000,
    fetchImpl = globalThis.fetch,
    setIntervalImpl = (fn, ms) => setInterval(fn, ms),
    clearIntervalImpl = (handle) => clearInterval(handle),
    onChange = () => {},
    onError = () => {},
    initial = null,
  } = {}
) {
  if (!url) throw new Error("watchJson needs a url");
  if (typeof fetchImpl !== "function") throw new Error("watchJson needs fetch");

  let last = initial === null ? null : JSON.stringify(initial);
  let stopped = false;

  async function tick() {
    if (stopped) return;
    try {
      const response = await fetchImpl(url, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const serialised = JSON.stringify(data);
      if (serialised !== last) {
        last = serialised;
        onChange(data);
      }
    } catch (err) {
      onError(err);
    }
  }

  const handle = setIntervalImpl(tick, intervalMs);

  function stop() {
    stopped = true;
    clearIntervalImpl(handle);
  }

  return { stop, tick, get stopped() { return stopped; } };
}
