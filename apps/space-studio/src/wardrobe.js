/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Wardrobe — appearance is data, not art.
 *
 * An outfit is {slot: {item, tint}}. Changing clothes returns a new avatar with
 * a bumped revision, which is what "the AI changed its own look" means: one
 * call, no model rebuild.
 */

export const SLOTS = ["top", "bottom", "shoes", "accessory"];
export const FALLBACK_TINT = "#cccccc";

export function applyOutfit(avatar, { slot, item, tint }) {
  if (!SLOTS.includes(slot)) throw new Error(`unknown wardrobe slot: ${slot}`);
  if (!item) throw new Error("applyOutfit needs an item id");
  if (tint && !/^#[0-9a-fA-F]{6}$/.test(tint)) {
    throw new Error(`tint must be #rrggbb, got ${tint}`);
  }
  const current = avatar.wardrobe?.slots ?? {};
  return {
    ...avatar,
    rev: (avatar.rev ?? 0) + 1,
    wardrobe: {
      ...(avatar.wardrobe ?? {}),
      slots: {
        ...current,
        [slot]: { ...(current[slot] ?? {}), item, tint: tint ?? current[slot]?.tint ?? FALLBACK_TINT },
      },
    },
  };
}

/** Colours the renderer needs, one per slot, with a stable fallback. */
export function outfitColors(avatar) {
  const slots = avatar.wardrobe?.slots ?? {};
  return Object.fromEntries(SLOTS.map((slot) => [slot, slots[slot]?.tint ?? FALLBACK_TINT]));
}

/** Rotate a slot through a palette — the "let it pick another colour" action. */
export function cycleTint(avatar, slot, palette = ["#3b6ea5", "#6b4f3a", "#d94f70", "#4e8f6d"]) {
  const current = avatar.wardrobe?.slots?.[slot]?.tint;
  const next = palette[(palette.indexOf(current) + 1) % palette.length];
  return applyOutfit(avatar, { slot, item: avatar.wardrobe?.slots?.[slot]?.item ?? slot, tint: next });
}
