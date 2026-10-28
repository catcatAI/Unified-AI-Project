/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Recorder — canvas → WebM, with feature detection instead of hoping.
 *
 * Chrome/Firefox give VP9; Safari falls back to MP4/H.264. The caller gets a
 * Blob and decides where it goes; the site never blocks on recording support.
 */

const MIME_CANDIDATES = [
  "video/webm;codecs=vp9",
  "video/webm;codecs=vp8",
  "video/webm",
  "video/mp4",
];

export function isRecordingSupported(canvas, scope = globalThis) {
  return !!(
    canvas &&
    typeof canvas.captureStream === "function" &&
    typeof scope.MediaRecorder === "function"
  );
}

export function pickMimeType(MediaRecorderCtor) {
  const supported = MediaRecorderCtor?.isTypeSupported?.bind(MediaRecorderCtor);
  if (typeof supported !== "function") return "";
  return MIME_CANDIDATES.find((type) => supported(type)) ?? "";
}

export function startRecording(canvas, { fps = 30, mimeType, scope = globalThis } = {}) {
  if (!isRecordingSupported(canvas, scope)) {
    throw new Error("recording is not supported in this browser");
  }
  const stream = canvas.captureStream(fps);
  const type = mimeType ?? pickMimeType(scope.MediaRecorder);
  const recorder = new scope.MediaRecorder(stream, type ? { mimeType: type } : undefined);
  const chunks = [];

  recorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0) chunks.push(event.data);
  };
  recorder.start();

  return {
    get state() {
      return recorder.state;
    },
    get mimeType() {
      return type || "video/webm";
    },
    stop() {
      return new Promise((resolve) => {
        recorder.onstop = () => resolve(new Blob(chunks, { type: type || "video/webm" }));
        recorder.stop();
        for (const track of stream.getTracks?.() ?? []) track.stop();
      });
    },
  };
}
