/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Snapshot sync — apply the backend's authoritative stage onto the local port.
 *
 * The local stage stays the renderer; this only overwrites the state it draws.
 * Actors missing from the snapshot are removed, so closing a viewer does not
 * leave a ghost on someone else's screen.
 */

export function applySnapshot(port, message, { defaultSpeechMs = 4000 } = {}) {
  const actors = message?.data?.actors
  if (!Array.isArray(actors)) return port

  const seen = new Set()
  for (const incoming of actors) {
    const actorId = incoming.actor_id ?? incoming.role_id
    if (!actorId) continue
    seen.add(actorId)

    if (!port.actors.has(actorId)) {
      port.spawn(actorId, {
        roleId: incoming.role_id,
        avatarId: incoming.avatar_id,
        position: incoming.position,
        visibleTo: incoming.visible_to ?? null,
      })
    }
    const actor = port.get(actorId)
    actor.position = [Number(incoming.position?.[0] ?? 8), Number(incoming.position?.[1] ?? 0)]
    actor.facing = Number(incoming.facing ?? 0)
    actor.expression = incoming.expression ?? 'neutral'
    actor.visibleTo = incoming.visible_to ?? null

    // S2: the backend owns outfit changes too (a role may dress itself).
    if (incoming.outfit && typeof incoming.outfit === 'object') {
      const slots = { ...(actor.avatar.wardrobe?.slots ?? {}), ...incoming.outfit }
      actor.avatar = {
        ...actor.avatar,
        rev: incoming.outfit_rev ?? actor.avatar.rev ?? 0,
        wardrobe: { ...(actor.avatar.wardrobe ?? {}), slots },
      }
    }

    const motion = incoming.motion ? port.motions?.[incoming.motion] : null
    actor.motion = motion
      ? { id: motion.id, durationMs: motion.durationMs ?? 1000, loop: !!motion.loop }
      : null
    actor.motionElapsed = 0

    actor.speech = incoming.speech?.text
      ? { text: String(incoming.speech.text), remainingMs: defaultSpeechMs }
      : null
  }

  for (const actorId of [...port.actors.keys()]) {
    if (!seen.has(actorId)) port.despawn(actorId)
  }
  return port
}
