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
  const pose = actor.pose ?? {};
  const [wx, wy] = project(actor.position, camera, viewport);
  // Motion channels are in world units / radians; convert once here so the
  // rest of the drawing code stays in pixels.
  const px = wx + (pose.offset_x ?? 0) * scale;
  const py = wy - (pose.offset_y ?? 0) * scale;
  const headDx = (pose.tilt ?? 0) * w0(scale) * 0.6;
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

  // arms — left stays a rect, right rotates with pose.arm_r (0 = hanging down)
  ctx.fillStyle = colors.top;
  ctx.fillRect(px - w * 0.46, py - h * 0.8, w * 0.14, h * 0.3);
  const shoulderX = px + w * 0.38;
  const shoulderY = py - h * 0.78;
  const armLen = h * 0.3;
  const armAngle = pose.arm_r ?? 0;
  ctx.strokeStyle = colors.top;
  ctx.lineWidth = w * 0.14;
  ctx.beginPath();
  ctx.moveTo(shoulderX, shoulderY);
  ctx.lineTo(shoulderX + Math.sin(armAngle) * armLen, shoulderY + Math.cos(armAngle) * armLen);
  ctx.stroke();

  // neck + head
  ctx.fillStyle = skin;
  ctx.fillRect(px + headDx - w * 0.07, py - h * 0.9, w * 0.14, h * 0.08);
  ctx.beginPath();
  ctx.ellipse(px + headDx, py - h * 0.97, w * 0.24, w * 0.27, 0, 0, Math.PI * 2);
  ctx.fill();

  // hair cap
  ctx.fillStyle = hair;
  ctx.beginPath();
  ctx.ellipse(px + headDx, py - h * 1.04, w * 0.25, w * 0.17, 0, Math.PI, Math.PI * 2);
  ctx.fill();

  drawFace(ctx, { px: px + headDx, py: py - h * 0.97, w, expression: actor.expression, skin });

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

  if (actor.speech) drawSpeechBubble(ctx, { px, py: py - h * 1.24, w, text: actor.speech.text });
}

function drawSpeechBubble(ctx, { px, py, w, text }) {
  const maxWidth = Math.max(160, w * 4.2);
  const fontSize = Math.max(11, Math.round(w * 0.12));
  ctx.font = `${fontSize}px system-ui, sans-serif`;
  const lines = wrapText(ctx, text, maxWidth);
  const lineHeight = fontSize * 1.35;
  const boxW = Math.min(maxWidth, Math.max(...lines.map((line) => ctx.measureText(line).width)) + 16);
  const boxH = lines.length * lineHeight + 10;
  const x = px - boxW / 2;
  const y = py - boxH;

  ctx.fillStyle = "rgba(250,250,255,0.94)";
  roundRect(ctx, x, y, boxW, boxH, 6);
  ctx.fill();
  // tail
  ctx.beginPath();
  ctx.moveTo(px - 5, y + boxH);
  ctx.lineTo(px + 5, y + boxH);
  ctx.lineTo(px, y + boxH + 7);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = "#1b1f2a";
  ctx.textAlign = "center";
  lines.forEach((line, index) => {
    ctx.fillText(line, px, y + 6 + fontSize + index * lineHeight);
  });
}

function wrapText(ctx, text, maxWidth) {
  const raw = String(text);
  // CJK has no spaces to break on, so fall back to per-character wrapping.
  if (!/\s/.test(raw)) return chunkByChar(ctx, raw, maxWidth);
  const words = raw.split(/\s+/);
  const lines = [];
  let current = "";
  for (const word of words) {
    const next = current ? `${current} ${word}` : word;
    if (ctx.measureText(next).width > maxWidth && current) {
      lines.push(current);
      current = word;
    } else {
      current = next;
    }
  }
  if (current) lines.push(current);
  return lines.length > 0 ? lines : [raw];
}

function chunkByChar(ctx, text, maxWidth) {
  const lines = [];
  let current = "";
  for (const ch of text) {
    if (current && ctx.measureText(current + ch).width > maxWidth) {
      lines.push(current);
      current = ch;
    } else {
      current += ch;
    }
  }
  if (current) lines.push(current);
  return lines.length > 0 ? lines : [text];
}

function w0(scale) {
  return 0.52 * scale;
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
