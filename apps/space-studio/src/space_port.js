/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * SpacePort — the seam between brains and stage.
 *
 * The concrete stage (2.5D canvas today, Luanti or three.js later) implements
 * this; `RolePlayAgent` never learns which one it is talking to.
 */

import { Actor } from "./actors.js";

export class SpacePort {
  constructor({ room = null, avatars = {}, motions = {} } = {}) {
    this.room = room;
    this.avatars = avatars;
    this.motions = motions;
    this.actors = new Map();
  }

  /** What this stage can do; callers must not assume a capability exists. */
  capabilities() {
    return ["spawn", "despawn", "move", "face", "play", "express", "look", "say", "snapshot"];
  }

  spawn(actorId, { roleId = actorId, avatarId, position, facing = 0, visibleTo = null } = {}) {
    if (this.actors.has(actorId)) throw new Error(`actor already spawned: ${actorId}`);
    const avatar = this.avatars[avatarId];
    if (!avatar) throw new Error(`unknown avatar: ${avatarId}`);
    const point = position ?? this._spawnPoint();
    const actor = new Actor({ id: actorId, roleId, avatar, position: point, facing, visibleTo });
    this.actors.set(actorId, actor);
    return actor;
  }

  /** Room spawn points are {id,x,y}; actors want [x,y]. */
  _spawnPoint() {
    const sp = this.room?.spawn_points?.[0];
    return sp ? [sp.x, sp.y] : [0, 0];
  }

  despawn(actorId) {
    return this.actors.delete(actorId);
  }

  get(actorId) {
    const actor = this.actors.get(actorId);
    if (!actor) throw new Error(`unknown actor: ${actorId}`);
    return actor;
  }

  move(actorId, position, durationMs = 800) {
    this.get(actorId).moveTo(position, durationMs);
    return this;
  }

  face(actorId, angle) {
    this.get(actorId).face(angle);
    return this;
  }

  play(actorId, motionId) {
    const actor = this.get(actorId); // actor first: "unknown actor" beats "unknown motion"
    const motion = this.motions[motionId];
    if (!motion) throw new Error(`unknown motion: ${motionId}`);
    actor.play(motion);
    return this;
  }

  express(actorId, expression) {
    this.get(actorId).express(expression);
    return this;
  }

  say(actorId, text, durationMs = 4000) {
    this.get(actorId).say(text, durationMs);
    return this;
  }

  look(actorId, targetId) {
    this.get(actorId).lookAt(this.get(targetId));
    return this;
  }

  /** Who this viewer can see (privacy lives in the port, not the renderer). */
  visibleFrom(viewerId) {
    return [...this.actors.values()]
      .filter((a) => a.visibleTo === null || a.visibleTo.includes(viewerId))
      .map((a) => a.snapshot());
  }

  tick(dtMs) {
    for (const actor of this.actors.values()) actor.update(dtMs);
    return this;
  }

  snapshot() {
    return {
      roomId: this.room?.room_id ?? null,
      actors: [...this.actors.values()].map((a) => a.snapshot()),
    };
  }
}
