/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Roster — which roles stand in the room, and where.
 *
 * The roster mirrors the server-side role registry (configs/system/roles.default.yaml):
 * same role ids, one stage position each. Visibility is per actor so a private
 * role can be absent from another role's view without leaving the stage.
 */

export function spawnRoster(port, roster) {
  if (!roster || !Array.isArray(roster.actors)) {
    throw new Error("roster needs an actors array");
  }
  const spawned = [];
  for (const entry of roster.actors) {
    const roleId = entry.role_id;
    if (!roleId) throw new Error("roster entry needs a role_id");
    spawned.push(
      port.spawn(entry.actor_id ?? roleId, {
        roleId,
        avatarId: entry.avatar_id,
        position: entry.position ?? [8, 0],
        facing: entry.facing ?? 0,
        visibleTo: entry.visible_to ?? null,
      })
    );
  }
  return spawned;
}

/** Who a viewer can see, in stage order — privacy is data on the actor. */
export function visibleFrom(port, viewerId) {
  return port.visibleFrom(viewerId);
}

/**
 * A canned three-way beat: everyone speaks once, staggered, so the stage shows
 * the turn-taking that the backend will later drive for real.
 */
export function scriptedBeat(port, lines, gapMs = 900) {
  const timers = [];
  lines.forEach((line, index) => {
    timers.push(
      setTimeout(() => {
        port.say(line.role_id, line.text, line.durationMs ?? 4000);
      }, index * gapMs)
    );
  });
  return () => timers.forEach(clearTimeout);
}
