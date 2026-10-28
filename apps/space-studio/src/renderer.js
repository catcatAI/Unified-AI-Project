/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Renderer — canvas 2.5D. Draws the room, then each actor back-to-front.
 *
 * Deliberately the only file that touches a 2D context: swapping in Live2D or
 * three.js later means replacing this file, not the SpacePort or the Actor.
 */

import { project, unitScale } from "./camera.js";
import { outfitColors } from "./wardrobe.js";

const EXPRESSIONS = {
  neutral: { eye: "line", mouth: 0 },
  smile: { eye: "arc", mouth: 0.35 },
  happy: { eye: "arc", mouth: 0.6 },
  blush: { eye: "line", mouth: 0.3, cheeks: true },
  wink: { eye: "wink", mouth: 0.3 },
  sad: { eye: "line", mouth: -0.3 },
};

export function drawStage(ctx, { room, actors, camera, viewport, timeMs = 0 }) {
  const { width, height } = viewport;
  ctx.clearRect(0, 0, width, height);
  drawRoom(ctx, { room, viewport });
  drawFloorShadow(ctx, { camera, viewport });

  // World +y is further from the camera, so paint far rows first: a nearer
  // actor must overlap a farther one, never the other way round.
  const ordered = [...actors].sort((a, b) => b.position[1] - a.position[1]);
  for (const actor of ordered) drawActor(ctx, { actor, camera, viewport, timeMs });
}

function drawRoom(ctx, { room, viewport }) {
  const { width, height } = viewport;
  const sky = room?.palette?.sky ?? ["#151922", "#232b3a"];
  const gradient = ctx.createLinearGradient(0, 0, 0, height);
  gradient.addColorStop(0, sky[0]);
  gradient.addColorStop(1, sky[1]);
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, width, height);

  // Back wall panel — a light seam so the stage reads as a room, not a void.
  ctx.fillStyle = room?.palette?.wall ?? "#242a36";
  ctx.fillRect(width * 0.08, height * 0.12, width * 0.84, height * 0.56);
  ctx.strokeStyle = "rgba(255,255,255,0.06)";
  ctx.strokeRect(width * 0.08, height * 0.12, width * 0.84, height * 0.56);
}

function drawFloorShadow(ctx, { camera, viewport }) {
  const y = viewport.height * (0.8 - camera.panY);
  const grad = ctx.createLinearGradient(0, y, 0, viewport.height);
  grad.addColorStop(0, "#3a2f2a");
  grad.addColorStop(1, "#1d1815");
  ctx.fillStyle = grad;
  ctx.fillRect(0, y, viewport.width, viewport.height - y);
  ctx.strokeStyle = "rgba(255,255,255,0.08)";
  ctx.beginPath();
  ctx.moveTo(0, y);
  ctx.lineTo(viewport.width, y);
  ctx.stroke();
}

function drawActor(ctx, { actor, camera, viewport }) {
  const colors = outfitColors(actor.avatar);
  const scale = unitScale(camera, viewport);
  const [px, py] = project(actor.position, camera, viewport);
  const breath = 1 + 0.012 * Math.sin(actor.breathPhase * Math.PI * 2);
  const h = 1.7 * scale * breath;
  const w = 0.52 * scale;
  const skin = actor.avatar.palette?.skin ?? "#f0d3b8";
  const hair = actor.avatar.palette?.hair ?? "#2f2430";

  // shadow
  ctx.fillStyle = "rgba(0,0,0,0.35)";
  ctx.beginPath();
  ctx.ellipse(px, py, w * 0.75, w * 0.22, 0, 0, Math.PI * 2);
  ctx.fill();

  // legs
  ctx.fillStyle = colors.bottom;
  ctx.fillRect(px - w * 0.26, py - h * 0.46, w * 0.2, h * 0.44);
  ctx.fillRect(px + w * 0.06, py - h * 0.46, w * 0.2, h * 0.44);

  // shoes
  ctx.fillStyle = colors.shoes;
  ctx.fillRect(px - w * 0.3, py - h * 0.07, w * 0.26, h * 0.06);
  ctx.fillRect(px + w * 0.04, py - h * 0.07, w * 0.26, h * 0.06);

  // torso
  ctx.fillStyle = colors.top;
  roundRect(ctx, px - w * 0.32, py - h * 0.82, w * 0.64, h * 0.4, w * 0.18);
  ctx.fill();

  // arms
  ctx.fillStyle = colors.top;
  ctx.fillRect(px - w * 0.46, py - h * 0.8, w * 0.14, h * 0.3);
  ctx.fillRect(px + w * 0.32, py - h * 0.8, w * 0.14, h * 0.3);

  // neck + head
  ctx.fillStyle = skin;
  ctx.fillRect(px - w * 0.07, py - h * 0.9, w * 0.14, h * 0.08);
  ctx.beginPath();
  ctx.ellipse(px, py - h * 0.97, w * 0.24, w * 0.27, 0, 0, Math.PI * 2);
  ctx.fill();

  // hair cap
  ctx.fillStyle = hair;
  ctx.beginPath();
  ctx.ellipse(px, py - h * 1.04, w * 0.25, w * 0.17, 0, Math.PI, Math.PI * 2);
  ctx.fill();

  drawFace(ctx, { px, py: py - h * 0.97, w, expression: actor.expression, skin });

  // accessory (ribbon)
  ctx.fillStyle = colors.accessory;
  ctx.beginPath();
  ctx.ellipse(px + w * 0.18, py - h * 1.02, w * 0.09, w * 0.05, -0.4, 0, Math.PI * 2);
  ctx.fill();

  // label
  ctx.fillStyle = "rgba(255,255,255,0.85)";
  ctx.font = `${Math.max(11, Math.round(scale * 0.16))}px system-ui, sans-serif`;
  ctx.textAlign = "center";
  const name = actor.avatar.display_name ?? actor.id;
  ctx.fillText(name, px, py - h * 1.18);
  if (actor.motion) {
    ctx.fillStyle = "rgba(160,220,255,0.8)";
    ctx.font = `${Math.max(10, Math.round(scale * 0.12))}px system-ui, sans-serif`;
    ctx.fillText(`▶ ${actor.motion.id}`, px, py - h * 1.1);
  }
}

function drawFace(ctx, { px, py, w, expression, skin }) {
  const spec = EXPRESSIONS[expression] ?? EXPRESSIONS.neutral;
  ctx.strokeStyle = "#2a2320";
  ctx.lineWidth = Math.max(1, w * 0.02);

  const eyeY = py - w * 0.05;
  const eyeDx = w * 0.1;
  if (spec.eye === "arc") {
    for (const dx of [-eyeDx, eyeDx]) {
      ctx.beginPath();
      ctx.arc(px + dx, eyeY + w * 0.02, w * 0.045, Math.PI * 1.1, Math.PI * 1.9);
      ctx.stroke();
    }
  } else if (spec.eye === "wink") {
    ctx.beginPath();
    ctx.arc(px - eyeDx, eyeY + w * 0.02, w * 0.045, Math.PI * 1.1, Math.PI * 1.9);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(px + eyeDx - w * 0.04, eyeY);
    ctx.lineTo(px + eyeDx + w * 0.04, eyeY);
    ctx.stroke();
  } else {
    for (const dx of [-eyeDx, eyeDx]) {
      ctx.beginPath();
      ctx.moveTo(px + dx - w * 0.035, eyeY);
      ctx.lineTo(px + dx + w * 0.035, eyeY);
      ctx.stroke();
    }
  }

  const mouthY = py + w * 0.12;
  ctx.beginPath();
  ctx.moveTo(px - w * 0.05, mouthY);
  ctx.quadraticCurveTo(px, mouthY + w * 0.09 * spec.mouth, px + w * 0.05, mouthY);
  ctx.stroke();

  if (spec.cheeks) {
    ctx.fillStyle = "rgba(235,120,140,0.35)";
    for (const dx of [-eyeDx - w * 0.02, eyeDx + w * 0.02]) {
      ctx.beginPath();
      ctx.ellipse(px + dx, mouthY - w * 0.02, w * 0.045, w * 0.025, 0, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
