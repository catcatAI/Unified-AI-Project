/**
 * sounds.js — Procedural sound effects using Web Audio API
 * No external audio files needed
 */

class SoundEngine {
  constructor() {
    this.ctx = null;
    this.volume = 0.7;
    this.enabled = true;
  }

  init() {
    try {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    } catch (e) {
      console.warn('Web Audio not available');
      this.enabled = false;
    }
  }

  setVolume(v) {
    this.volume = Math.max(0, Math.min(1, v));
  }

  _gain(vol = 1) {
    if (!this.ctx) return null;
    const g = this.ctx.createGain();
    g.gain.value = vol * this.volume;
    g.connect(this.ctx.destination);
    return g;
  }

  // ── Card pickup ──
  cardPickup() {
    if (!this.ctx || !this.enabled) return;
    const osc = this.ctx.createOscillator();
    const gain = this._gain(0.15);
    osc.type = 'sine';
    osc.frequency.setValueAtTime(800, this.ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(1200, this.ctx.currentTime + 0.08);
    osc.connect(gain);
    osc.start(this.ctx.currentTime);
    osc.stop(this.ctx.currentTime + 0.1);
  }

  // ── Card place ──
  cardPlace() {
    if (!this.ctx || !this.enabled) return;
    const osc = this.ctx.createOscillator();
    const gain = this._gain(0.12);
    osc.type = 'sine';
    osc.frequency.setValueAtTime(600, this.ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(400, this.ctx.currentTime + 0.1);
    osc.connect(gain);
    osc.start(this.ctx.currentTime);
    osc.stop(this.ctx.currentTime + 0.12);
  }

  // ── Stack / Craft ──
  craft() {
    if (!this.ctx || !this.enabled) return;
    const notes = [523, 659, 784, 1047]; // C5, E5, G5, C6
    notes.forEach((freq, i) => {
      const osc = this.ctx.createOscillator();
      const gain = this._gain(0.1);
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime + i * 0.08);
      osc.connect(gain);
      osc.start(this.ctx.currentTime + i * 0.08);
      osc.stop(this.ctx.currentTime + i * 0.08 + 0.15);
    });
  }

  // ── Combat hit ──
  combatHit() {
    if (!this.ctx || !this.enabled) return;
    // Noise burst
    const bufferSize = this.ctx.sampleRate * 0.1;
    const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / bufferSize, 2);
    }
    const source = this.ctx.createBufferSource();
    source.buffer = buffer;
    const gain = this._gain(0.2);
    const filter = this.ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.value = 800;
    source.connect(filter);
    filter.connect(gain);
    source.start(this.ctx.currentTime);
  }

  // ── Dialog open ──
  dialogOpen() {
    if (!this.ctx || !this.enabled) return;
    const osc = this.ctx.createOscillator();
    const gain = this._gain(0.08);
    osc.type = 'sine';
    osc.frequency.setValueAtTime(400, this.ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(600, this.ctx.currentTime + 0.15);
    osc.connect(gain);
    osc.start(this.ctx.currentTime);
    osc.stop(this.ctx.currentTime + 0.2);
  }

  // ── Button click ──
  click() {
    if (!this.ctx || !this.enabled) return;
    const osc = this.ctx.createOscillator();
    const gain = this._gain(0.06);
    osc.type = 'sine';
    osc.frequency.value = 1000;
    osc.connect(gain);
    osc.start(this.ctx.currentTime);
    osc.stop(this.ctx.currentTime + 0.05);
  }

  // ── Resource collect ──
  collect() {
    if (!this.ctx || !this.enabled) return;
    const osc = this.ctx.createOscillator();
    const gain = this._gain(0.1);
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(880, this.ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(1320, this.ctx.currentTime + 0.12);
    osc.connect(gain);
    osc.start(this.ctx.currentTime);
    osc.stop(this.ctx.currentTime + 0.15);
  }

  // ── Warning / damage ──
  warning() {
    if (!this.ctx || !this.enabled) return;
    const osc = this.ctx.createOscillator();
    const gain = this._gain(0.12);
    osc.type = 'square';
    osc.frequency.setValueAtTime(300, this.ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(150, this.ctx.currentTime + 0.2);
    osc.connect(gain);
    osc.start(this.ctx.currentTime);
    osc.stop(this.ctx.currentTime + 0.25);
  }

  // ── Night ambience (loop) ──
  _nightLoop = null;
  startNightAmbience() {
    if (!this.ctx || !this.enabled || this._nightLoop) return;
    const osc = this.ctx.createOscillator();
    const gain = this._gain(0.03);
    osc.type = 'sine';
    osc.frequency.value = 100;
    gain.gain.setValueAtTime(0.03 * this.volume, this.ctx.currentTime);
    gain.gain.linearRampToValueAtTime(0.06 * this.volume, this.ctx.currentTime + 2);
    osc.connect(gain);
    osc.start();
    this._nightLoop = { osc, gain };
  }

  stopNightAmbience() {
    if (this._nightLoop) {
      this._nightLoop.gain.gain.linearRampToValueAtTime(0, this.ctx.currentTime + 0.5);
      this._nightLoop.osc.stop(this.ctx.currentTime + 0.6);
      this._nightLoop = null;
    }
  }

  // ── Day transition ──
  dayTransition() {
    if (!this.ctx || !this.enabled) return;
    const notes = [262, 330, 392, 523]; // C4, E4, G4, C5
    notes.forEach((freq, i) => {
      const osc = this.ctx.createOscillator();
      const gain = this._gain(0.06);
      osc.type = 'sine';
      osc.frequency.value = freq;
      osc.connect(gain);
      osc.start(this.ctx.currentTime + i * 0.15);
      osc.stop(this.ctx.currentTime + i * 0.15 + 0.3);
    });
  }
}

window.sounds = new SoundEngine();
