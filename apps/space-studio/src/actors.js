/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Actor — one body standing in the room.
 *
 * Pure state machine, no DOM: the renderer reads it, the tests drive it. That
 * split is what lets S0 ship a stage before the Live2D renderer exists.
 */

export class Actor {
  /**
   * @param {object} spec
   * @param {string} spec.id
   * @param {string} [spec.roleId]
   * @param {object} spec.avatar      avatar JSON (see space/avatars/*.json)
   * @param {[number, number]} [spec.position]
   * @param {number} [spec.facing]    radians
   * @param {string[]|null} [spec.visibleTo]
   */
  constructor({ id, roleId = id, avatar, position = [0, 0], facing = 0, visibleTo = null }) {
    this.id = id;
    this.roleId = roleId;
    this.avatar = avatar;
    this.position = [position[0], position[1]];
    this.facing = facing;
    this.visibleTo = visibleTo;

    this.expression = "neutral";
    this.motion = null; // { id, durationMs, loop }
    this.motionElapsed = 0;
    this.breathPhase = 0;
    this.speech = null; // { text, remainingMs }
    this._move = null;
  }

  /** Advance one frame. dtMs is wall time since the previous frame. */
  update(dtMs) {
    if (!(dtMs > 0)) return;
    this.breathPhase = (this.breathPhase + dtMs / 2600) % 1;

    if (this.speech) {
      this.speech.remainingMs -= dtMs;
      if (this.speech.remainingMs <= 0) this.speech = null;
    }

    if (this.motion) {
      this.motionElapsed += dtMs;
      if (!this.motion.loop && this.motionElapsed >= this.motion.durationMs) {
        this.clearMotion();
      }
    }

    if (this._move) {
      const m = this._move;
      m.elapsed += dtMs;
      const t = m.durationMs <= 0 ? 1 : Math.min(1, m.elapsed / m.durationMs);
      const ease = t * t * (3 - 2 * t); // smoothstep: no robot-linear stops
      this.position[0] = m.from[0] + (m.to[0] - m.from[0]) * ease;
      this.position[1] = m.from[1] + (m.to[1] - m.from[1]) * ease;
      if (t >= 1) this._move = null;
    }
  }

  moveTo(position, durationMs = 800) {
    this._move = {
      from: [this.position[0], this.position[1]],
      to: [position[0], position[1]],
      elapsed: 0,
      durationMs,
    };
  }

  get isMoving() {
    return this._move !== null;
  }

  face(angle) {
    this.facing = angle;
  }

  /** Turn towards another actor; throws if the target does not exist. */
  lookAt(target) {
    if (!target) throw new Error("lookAt needs a target actor");
    const dx = target.position[0] - this.position[0];
    const dy = target.position[1] - this.position[1];
    this.facing = Math.atan2(dy, dx);
    return this.facing;
  }

  play(motion) {
    if (!motion || !motion.id) throw new Error("play needs a motion with an id");
    this.motion = { id: motion.id, durationMs: motion.durationMs ?? 1000, loop: !!motion.loop };
    this.motionElapsed = 0;
  }

  clearMotion() {
    this.motion = null;
    this.motionElapsed = 0;
  }

  express(expression) {
    const channels = this.avatar.expression_channels ?? ["neutral"];
    if (!channels.includes(expression)) {
      throw new Error(`unknown expression ${expression} for avatar ${this.avatar.avatar_id}`);
    }
    this.expression = expression;
  }

  /** Speak for a while; the bubble is stage state, not a chat log. */
  say(text, durationMs = 4000) {
    const spoken = String(text ?? "").trim();
    if (!spoken) throw new Error("say needs non-empty text");
    this.speech = { text: spoken, remainingMs: durationMs };
    return this.speech;
  }

  /** Serialisable state — what the stage broadcasts over a socket later. */
  snapshot() {
    return {
      id: this.id,
      roleId: this.roleId,
      position: [round3(this.position[0]), round3(this.position[1])],
      facing: round3(this.facing),
      expression: this.expression,
      motion: this.motion ? this.motion.id : null,
      speech: this.speech ? this.speech.text : null,
      avatarRev: this.avatar.rev ?? 0,
    };
  }
}

function round3(n) {
  return Math.round(n * 1000) / 1000;
}
