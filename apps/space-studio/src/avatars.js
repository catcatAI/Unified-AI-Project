/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Avatars — which avatar profiles the stage preloads.
 *
 * The roster (``space/roles.json``) names an ``avatar_id`` per role; every id
 * that appears there must have a profile here, or ``SpacePort.spawn`` throws
 * ``unknown avatar`` and the stage never boots. Kept in its own module so the
 * roster/avatar contract can be tested without a DOM.
 *
 * Paths are relative to the page (``apps/space-studio/``), not to this file.
 */

export const AVATARS = {
  angela_base: '../../space/avatars/angela_base.json',
  gemma_b: '../../space/avatars/gemma_b.json',
  qwen_c: '../../space/avatars/qwen_c.json',
  deepseek_d: '../../space/avatars/deepseek_d.json',
  lucifaella: '../../space/avatars/lucifaella.json',
}
