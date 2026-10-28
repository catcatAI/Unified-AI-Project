/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Motion model — tracks, keyframes, sampling. Pure data, no canvas.
 *
 * A motion is a duration plus channels of `[timeMs, value]` keys. The renderer
 * only ever asks "what is the pose at time t", so adding a channel (or a new
 * export format) never touches the drawing code.
 */

export const CHANNELS = ["offset_x", "offset_y", "tilt", "arm_r"];

const isFiniteNumber = (value) => typeof value === "number" && Number.isFinite(value);

function normaliseKeys(keys) {
  if (!Array.isArray(keys)) throw new Error("keys must be an array");
  const sorted = keys
    .map(([t, v]) => [Number(t), Number(v)])
    .sort((a, b) => a[0] - b[0]);
  for (const [t, v] of sorted) {
    if (!isFiniteNumber(t) || !isFiniteNumber(v)) throw new Error("keys must be finite numbers");
    if (t < 0) throw new Error("key time must be >= 0");
  }
  return sorted;
}

function normaliseTracks(tracks = {}) {
  const out = {};
  for (const [channel, keys] of Object.entries(tracks)) {
    if (!CHANNELS.includes(channel)) throw new Error(`unknown motion channel: ${channel}`);
    out[channel] = normaliseKeys(keys);
  }
  return out;
}

export function createMotion({ id, durationMs = 2000, loop = false, tracks = {} } = {}) {
  if (!id) throw new Error("motion needs an id");
  if (!isFiniteNumber(durationMs) || durationMs <= 0) {
    throw new Error("durationMs must be a positive number");
  }
  const motion = { id, durationMs: Math.round(durationMs), loop: !!loop, tracks: normaliseTracks(tracks) };
  for (const [channel, keys] of Object.entries(motion.tracks)) {
    const tooLate = keys.find(([t]) => t > motion.durationMs);
    if (tooLate) throw new Error(`${channel} key at ${tooLate[0]}ms is past the duration`);
  }
  return motion;
}

/** Immutable insert/replace at time t (same t replaces, like a keyframe editor). */
export function addKeyframe(motion, channel, tMs, value) {
  if (!CHANNELS.includes(channel)) throw new Error(`unknown motion channel: ${channel}`);
  if (!isFiniteNumber(tMs) || tMs < 0) throw new Error("key time must be >= 0");
  if (tMs > motion.durationMs) throw new Error(`key time ${tMs} is past the duration`);
  if (!isFiniteNumber(value)) throw new Error("key value must be a finite number");

  const keys = [...(motion.tracks[channel] ?? [])].filter(([t]) => t !== tMs);
  keys.push([tMs, value]);
  return {
    ...motion,
    tracks: { ...motion.tracks, [channel]: normaliseKeys(keys) },
  };
}

export function removeKeyframe(motion, channel, index) {
  const keys = motion.tracks[channel] ?? [];
  if (index < 0 || index >= keys.length) throw new Error(`no keyframe ${index} in ${channel}`);
  const next = keys.filter((_, i) => i !== index);
  const tracks = { ...motion.tracks };
  if (next.length === 0) delete tracks[channel];
  else tracks[channel] = next;
  return { ...motion, tracks };
}

/** Linear interpolation, clamped at both ends. */
export function sampleChannel(keys, tMs) {
  if (!keys || keys.length === 0) return 0;
  if (tMs <= keys[0][0]) return keys[0][1];
  const last = keys[keys.length - 1];
  if (tMs >= last[0]) return last[1];
  for (let i = 1; i < keys.length; i += 1) {
    const [t1, v1] = keys[i];
    if (tMs === t1) return v1;
    if (tMs < t1) {
      const [t0, v0] = keys[i - 1];
      const span = t1 - t0;
      if (span <= 0) return v1;
      const ratio = (tMs - t0) / span;
      return v0 + (v1 - v0) * ratio;
    }
  }
  return last[1];
}

export function sampleMotion(motion, tMs) {
  const pose = {};
  for (const [channel, keys] of Object.entries(motion.tracks ?? {})) {
    pose[channel] = sampleChannel(keys, tMs);
  }
  return pose;
}

export function validateMotion(motion) {
  const errors = [];
  if (!motion || typeof motion !== "object") return { ok: false, errors: ["motion must be an object"] };
  if (!motion.id) errors.push("missing id");
  if (!isFiniteNumber(motion.durationMs) || motion.durationMs <= 0) errors.push("bad durationMs");
  for (const [channel, keys] of Object.entries(motion.tracks ?? {})) {
    if (!CHANNELS.includes(channel)) errors.push(`unknown channel ${channel}`);
    if (!Array.isArray(keys) || keys.length === 0) errors.push(`${channel} has no keys`);
    for (const [t, v] of keys ?? []) {
      if (!isFiniteNumber(t) || t < 0) errors.push(`${channel} key time invalid`);
      if (!isFiniteNumber(v)) errors.push(`${channel} key value invalid`);
      if (isFiniteNumber(t) && motion.durationMs > 0 && t > motion.durationMs) {
        errors.push(`${channel} key past duration`);
      }
    }
  }
  return { ok: errors.length === 0, errors };
}

export function serializeMotion(motion) {
  const result = validateMotion(motion);
  if (!result.ok) throw new Error(`invalid motion: ${result.errors.join(", ")}`);
  return JSON.stringify({ id: motion.id, durationMs: motion.durationMs, loop: !!motion.loop, tracks: motion.tracks });
}

export function parseMotion(json) {
  const raw = typeof json === "string" ? JSON.parse(json) : json;
  const motion = createMotion(raw);
  const result = validateMotion(motion);
  if (!result.ok) throw new Error(`invalid motion: ${result.errors.join(", ")}`);
  return motion;
}
