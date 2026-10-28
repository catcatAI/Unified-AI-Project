/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Space socket + snapshot sync, with a fake WebSocket (no browser needed).
 */

import assert from "node:assert/strict";
import test from "node:test";

import { SpacePort } from "../src/space_port.js";
import { applySnapshot } from "../src/snapshot_sync.js";
import { createSpaceSocket } from "../src/ws_client.js";

class FakeSocket {
  static instances = [];

  constructor(url) {
    this.url = url;
    this.readyState = 0;
    this.sent = [];
    this.closed = false;
    FakeSocket.instances.push(this);
  }

  open() {
    this.readyState = 1;
    this.onopen?.();
  }

  message(payload) {
    this.onmessage?.({ data: JSON.stringify(payload) });
  }

  send(text) {
    this.sent.push(JSON.parse(text));
  }

  close() {
    this.closed = true;
    this.readyState = 3;
    this.onclose?.();
  }
}

function makeSocket(overrides = {}) {
  FakeSocket.instances = [];
  const snapshots = [];
  const statuses = [];
  const socket = createSpaceSocket({
    url: "ws://localhost:8000/ws/space",
    roomId: "studio_a",
    WebSocketImpl: FakeSocket,
    onSnapshot: (message) => snapshots.push(message),
    onStatus: (status) => statuses.push(status),
    autoReconnect: false,
    ...overrides,
  });
  return { socket, snapshots, statuses, fake: () => FakeSocket.instances.at(-1) };
}

// --------------------------------------------------------------------------
// socket
// --------------------------------------------------------------------------
test("connect includes the room in the query string", () => {
  const { socket, fake } = makeSocket();
  socket.connect();
  assert.equal(fake().url, "ws://localhost:8000/ws/space?room_id=studio_a");
});

test("open flips the status to connected", () => {
  const { socket, statuses, fake } = makeSocket();
  socket.connect();
  fake().open();
  assert.equal(socket.status, "connected");
  assert.deepEqual(statuses, ["connected"]);
});

test("snapshots are forwarded, garbage is ignored", () => {
  const { socket, snapshots, fake } = makeSocket();
  socket.connect();
  fake().message({ type: "space.snapshot", data: { actors: [] } });
  fake().message({ type: "space.pong" });
  fake().onmessage({ data: "not json" });
  assert.equal(snapshots.length, 1);
});

test("send wraps actions and only works when open", () => {
  const { socket, fake } = makeSocket();
  socket.connect();
  assert.equal(socket.send({ type: "say", actor_id: "main", text: "hi" }), false);
  fake().open();
  assert.equal(socket.send({ type: "say", actor_id: "main", text: "hi" }), true);
  assert.deepEqual(fake().sent[0], {
    type: "space.action",
    data: { type: "say", actor_id: "main", text: "hi" },
  });
});

test("close stops reconnecting", () => {
  const scheduled = [];
  const { socket, fake } = makeSocket({
    autoReconnect: true,
    schedule: (fn) => scheduled.push(fn),
  });
  socket.connect();
  fake().open();
  fake().close();
  assert.equal(scheduled.length, 1); // scheduled while still open to retries
  socket.close();
  scheduled.forEach((fn) => fn());
  assert.equal(socket.status, "closed");
});

test("without a WebSocket implementation the stage reports unsupported", () => {
  const statuses = [];
  const socket = createSpaceSocket({
    url: "ws://x/ws/space",
    WebSocketImpl: null,
    onStatus: (s) => statuses.push(s),
  });
  assert.equal(socket.connect(), false);
  assert.deepEqual(statuses, ["unsupported"]);
});

// --------------------------------------------------------------------------
// snapshot → port
// --------------------------------------------------------------------------
function port() {
  return new SpacePort({
    room: { room_id: "studio_a" },
    avatars: {
      angela_base: { avatar_id: "angela_base", display_name: "Angela", expression_channels: ["neutral", "smile"], wardrobe: { slots: {} }, rev: 0 },
      gemma_b: { avatar_id: "gemma_b", display_name: "Gemma", expression_channels: ["neutral"], wardrobe: { slots: {} }, rev: 0 },
    },
    motions: { idle_breath: { id: "idle_breath", durationMs: 2600, loop: true } },
  });
}

function snapshot(actors) {
  return { type: "space.snapshot", rev: 3, data: { room_id: "studio_a", actors } };
}

test("snapshot creates actors that are not on the local stage yet", () => {
  const p = port();
  applySnapshot(
    p,
    snapshot([
      { actor_id: "main", role_id: "main", avatar_id: "angela_base", position: [5.5, 0], facing: 0 },
      { actor_id: "role_b", role_id: "role_b", avatar_id: "gemma_b", position: [8, 0], facing: 0 },
    ])
  );
  assert.deepEqual([...p.actors.keys()], ["main", "role_b"]);
  assert.deepEqual(p.get("role_b").position, [8, 0]);
});

test("snapshot updates pose, expression, motion and speech", () => {
  const p = port();
  applySnapshot(p, snapshot([{ actor_id: "main", role_id: "main", avatar_id: "angela_base" }]));
  applySnapshot(
    p,
    snapshot([
      {
        actor_id: "main",
        role_id: "main",
        avatar_id: "angela_base",
        position: [10, 0],
        facing: 1.2,
        expression: "smile",
        motion: "idle_breath",
        speech: { text: "我回來了" },
      },
    ])
  );
  const actor = p.get("main");
  assert.deepEqual(actor.position, [10, 0]);
  assert.equal(actor.expression, "smile");
  assert.equal(actor.motion.id, "idle_breath");
  assert.equal(actor.speech.text, "我回來了");
});

test("actors missing from the snapshot are removed", () => {
  const p = port();
  applySnapshot(
    p,
    snapshot([
      { actor_id: "main", role_id: "main", avatar_id: "angela_base" },
      { actor_id: "role_b", role_id: "role_b", avatar_id: "gemma_b" },
    ])
  );
  applySnapshot(p, snapshot([{ actor_id: "main", role_id: "main", avatar_id: "angela_base" }]));
  assert.deepEqual([...p.actors.keys()], ["main"]);
});

test("malformed snapshots are ignored", () => {
  const p = port();
  applySnapshot(p, { type: "space.snapshot" });
  applySnapshot(p, null);
  assert.equal(p.actors.size, 0);
});

test("snapshot outfit changes are applied to the avatar", () => {
  const p = port();
  applySnapshot(
    p,
    snapshot([
      {
        actor_id: "role_b",
        role_id: "role_b",
        avatar_id: "gemma_b",
        outfit: { top: { item: "jacket_purple", tint: "#6a4f9e" } },
        outfit_rev: 3,
      },
    ])
  );
  const actor = p.get("role_b");
  assert.equal(actor.avatar.wardrobe.slots.top.item, "jacket_purple");
  assert.equal(actor.avatar.wardrobe.slots.top.tint, "#6a4f9e");
  assert.equal(actor.avatar.rev, 3);
});

test("snapshots without an outfit leave the avatar alone", () => {
  const p = port();
  applySnapshot(p, snapshot([{ actor_id: "main", role_id: "main", avatar_id: "angela_base" }]));
  const before = p.get("main").avatar.wardrobe.slots;
  applySnapshot(p, snapshot([{ actor_id: "main", role_id: "main", avatar_id: "angela_base" }]));
  assert.deepEqual(p.get("main").avatar.wardrobe.slots, before);
});
