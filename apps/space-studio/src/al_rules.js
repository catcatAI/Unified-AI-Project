/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * AL state → motion rules.
 *
 * The stage already knows the three vitals (fatigue / stress / valence) because
 * the same numbers feed the persona prompt. This module turns them into a body
 * action, so "tired" is something you can see, not only something the model says.
 *
 * Rules are JSON (not YAML): the browser has no YAML parser and this file must
 * load from a static server with zero dependencies.
 */

const OPERATORS = {
  gte: (value, threshold) => value >= threshold,
  lte: (value, threshold) => value <= threshold,
  eq: (value, expected) => String(value) === String(expected),
};

export const DEFAULT_RULES = [
  { motion: "nod", when: { fatigue: { gte: 0.7 } }, priority: 10 },
];

/** Validate a rules document; returns {ok, errors, rules}. */
export function parseRules(doc) {
  const raw = typeof doc === "string" ? JSON.parse(doc) : doc;
  const errors = [];
  const rules = [];
  for (const [index, rule] of (raw?.rules ?? []).entries()) {
    if (!rule || typeof rule !== "object") {
      errors.push(`rule ${index} is not an object`);
      continue;
    }
    if (!rule.motion) errors.push(`rule ${index} has no motion`);
    const when = rule.when ?? {};
    if (Object.keys(when).length === 0) errors.push(`rule ${index} has no conditions`);
    for (const [key, condition] of Object.entries(when)) {
      // `key` is a state field (fatigue/stress/valence/emotion); the operators
      // live inside the condition, so only those are validated here.
      if (!condition || typeof condition !== "object") {
        errors.push(`rule ${index}: ${key} needs {gte|lte|eq}`);
        continue;
      }
      for (const [op, value] of Object.entries(condition)) {
        if (!(op in OPERATORS)) errors.push(`rule ${index}: ${key} uses unknown ${op}`);
        if (value === undefined || value === null) errors.push(`rule ${index}: ${key}.${op} empty`);
      }
    }
    rules.push({
      motion: String(rule.motion),
      when,
      priority: Number.isFinite(rule.priority) ? Number(rule.priority) : 0,
    });
  }
  rules.sort((a, b) => b.priority - a.priority);
  return { ok: errors.length === 0, errors, rules };
}

function matches(rule, state) {
  for (const [field, condition] of Object.entries(rule.when)) {
    const actual = state[field];
    if (actual === undefined || actual === null) return false;
    for (const [op, expected] of Object.entries(condition)) {
      const check = OPERATORS[op];
      if (!check) return false;
      if (!check(actual, expected)) return false;
    }
  }
  return true;
}

/**
 * First matching rule by priority, or null. Returning null (instead of a
 * default motion) is deliberate: "no rule matched" and "the rule says idle"
 * are different answers, and callers should be able to tell them apart.
 */
export function pickMotion(state = {}, rules = DEFAULT_RULES) {
  const list = Array.isArray(rules) ? [...rules] : parseRules(rules).rules;
  list.sort((a, b) => b.priority - a.priority);
  for (const rule of list) {
    if (matches(rule, state)) return { motion: rule.motion, priority: rule.priority, rule };
  }
  return null;
}
