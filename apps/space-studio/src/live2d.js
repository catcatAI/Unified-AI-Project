/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Live2D seam — detection only.
 *
 * The viewer at apps/web-live2d-viewer ships Cubism models (Epsilon_free,
 * miara_pro_en), but wiring the Cubism runtime into this stage is a separate
 * job (S1.5): it needs the SDK bundle, a model loader and the draw order.
 *
 * Until then this module only answers "is a Cubism runtime present?", so the
 * stage can say honestly which renderer it is using instead of pretending.
 */

export function detectLive2D(scope = globalThis) {
  return Boolean(scope?.Live2D || scope?.Live2DCubismCore || scope?.CubismSdkForWeb);
}

export function rendererLabel(scope = globalThis) {
  return detectLive2D(scope)
    ? "Live2D SDK detected — loader not wired yet (procedural renderer active)"
    : "procedural renderer (Live2D loader is S1.5)";
}
