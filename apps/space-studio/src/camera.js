/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Camera — presets, pan, zoom, and world→pixel projection.
 *
 * Pure functions so the framing maths is testable without a browser. The
 * renderer only consumes the result.
 */

export const PRESETS = {
  wide: { zoom: 1.0, panX: 0, panY: 0 },
  medium: { zoom: 1.55, panX: 0, panY: 0.04 },
  close: { zoom: 2.3, panX: 0, panY: 0.12 },
  over_shoulder: { zoom: 1.8, panX: 0.18, panY: 0.06 },
  free: { zoom: 1.0, panX: 0, panY: 0, free: true },
}

export function resolveCamera(preset = 'wide', overrides = {}) {
  const base = PRESETS[preset]
  if (!base) throw new Error(`unknown camera preset: ${preset}`)
  return { ...base, ...overrides, preset }
}

/**
 * World is laid out on a 0..worldWidth / 0..worldHeight plane; y=0 is the
 * floor and grows upwards. Returns [px, py] in canvas pixels.
 */
export function project([x, y], camera, viewport) {
  const { width, height, worldWidth = 16, worldHeight = 9 } = viewport
  const base = Math.min(width / worldWidth, height / worldHeight)
  const scale = base * camera.zoom
  const cx = width / 2 + camera.panX * width
  const floor = height * (0.8 - camera.panY)
  return [cx + (x - worldWidth / 2) * scale, floor - y * scale]
}

/** Pixel height of one world unit at the current zoom (used for actor size). */
export function unitScale(camera, viewport) {
  const { width, height, worldWidth = 16, worldHeight = 9 } = viewport
  return Math.min(width / worldWidth, height / worldHeight) * camera.zoom
}
