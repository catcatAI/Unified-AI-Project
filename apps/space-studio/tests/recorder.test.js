/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Recorder — feature detection and the Blob handoff, with a fake MediaRecorder.
 */

import assert from 'node:assert/strict'
import test from 'node:test'

import { isRecordingSupported, pickMimeType, startRecording } from '../src/recorder.js'

const canvas = {
  captureStream: () => ({ getTracks: () => [{ stop() {} }] }),
}

class FakeRecorder {
  static isTypeSupported = (type) => type.startsWith('video/webm')

  constructor(stream, options) {
    this.stream = stream
    this.options = options
    this.state = 'inactive'
  }

  start() {
    this.state = 'recording'
  }

  stop() {
    this.state = 'inactive'
    this.ondataavailable?.({ data: new Blob(['frame'], { type: 'video/webm' }) })
    this.onstop?.()
  }
}

test('recording is unsupported without MediaRecorder', () => {
  assert.equal(isRecordingSupported(canvas, {}), false)
  assert.equal(isRecordingSupported({}, { MediaRecorder: FakeRecorder }), false)
  assert.equal(isRecordingSupported(canvas, { MediaRecorder: FakeRecorder }), true)
})

test('mime type prefers vp9 and falls back in order', () => {
  assert.equal(pickMimeType(FakeRecorder), 'video/webm;codecs=vp9')
  assert.equal(pickMimeType(undefined), '')
})

test('startRecording throws instead of silently doing nothing', () => {
  assert.throws(() => startRecording({}, { scope: {} }), /not supported/)
})

test('stop resolves to a Blob and stops the tracks', async () => {
  let tracksStopped = 0
  const localCanvas = {
    captureStream: () => ({
      getTracks: () => [
        {
          stop: () => {
            tracksStopped += 1
          },
        },
      ],
    }),
  }
  const handle = startRecording(localCanvas, { scope: { MediaRecorder: FakeRecorder } })
  assert.equal(handle.state, 'recording')
  assert.equal(handle.mimeType, 'video/webm;codecs=vp9')

  const blob = await handle.stop()
  assert.ok(blob instanceof Blob)
  assert.ok(blob.size > 0)
  assert.equal(tracksStopped, 1)
})
