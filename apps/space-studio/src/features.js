/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Feature flags — half-finished stage features can ship without being visible.
 *
 * Resolution order: window.SPACE_FEATURES → localStorage → defaults. Unknown
 * names are kept (so a typo is visible in the UI as "no such section" rather
 * than silently enabling everything).
 */

export const DEFAULT_FEATURES = ["wardrobe", "motion", "camera", "record", "visibility"];

export function parseFeatures(raw, defaults = DEFAULT_FEATURES) {
  if (raw === undefined || raw === null || String(raw).trim() === "") {
    return new Set(defaults);
  }
  return new Set(
    String(raw)
      .split(",")
      .map((name) => name.trim().toLowerCase())
      .filter(Boolean)
  );
}

export function resolveFeatures(scope = globalThis, defaults = DEFAULT_FEATURES) {
  const fromWindow = scope?.SPACE_FEATURES;
  if (fromWindow !== undefined) return parseFeatures(fromWindow, defaults);
  try {
    const stored = scope?.localStorage?.getItem("space.features");
    if (stored) return parseFeatures(stored, defaults);
  } catch {
    // storage blocked: fall through to defaults
  }
  return parseFeatures(undefined, defaults);
}

export function hasFeature(features, name) {
  return features.has(String(name).toLowerCase());
}
