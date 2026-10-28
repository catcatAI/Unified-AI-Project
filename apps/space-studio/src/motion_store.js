/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Motion library — the user's edited motions, persisted and exportable.
 *
 * Same shape as the shipped `space/motions/index.json` (id → motion), so an
 * exported library can replace that file without conversion.
 */

import { parseMotion, serializeMotion } from "./motion_editor.js";

export const STORAGE_KEY = "space.motions.v1";

export function saveMotion(library, motion) {
  if (!motion || !motion.id) throw new Error("saveMotion needs a motion with an id");
  return { ...library, [motion.id]: motion };
}

export function deleteMotion(library, id) {
  const next = { ...library };
  delete next[id];
  return next;
}

export function listMotions(library) {
  return Object.values(library ?? {}).sort((a, b) => a.id.localeCompare(b.id));
}

/** JSON for `space/motions/index.json` (pretty, stable key order). */
export function toLibraryJson(library) {
  const ordered = {};
  for (const motion of listMotions(library)) ordered[motion.id] = JSON.parse(serializeMotion(motion));
  return JSON.stringify(ordered, null, 2) + "\n";
}

export function fromLibraryJson(json) {
  const raw = typeof json === "string" ? JSON.parse(json) : json;
  const library = {};
  for (const [id, spec] of Object.entries(raw ?? {})) {
    library[id] = parseMotion({ id, ...spec });
  }
  return library;
}

export function loadLibrary(storage, key = STORAGE_KEY) {
  if (!storage) return {};
  try {
    const raw = storage.getItem(key);
    if (!raw) return {};
    return fromLibraryJson(raw);
  } catch {
    return {};
  }
}

export function persistLibrary(storage, library, key = STORAGE_KEY) {
  if (!storage) return false;
  try {
    storage.setItem(key, toLibraryJson(library));
    return true;
  } catch {
    return false; // full/blocked storage must not break editing
  }
}
