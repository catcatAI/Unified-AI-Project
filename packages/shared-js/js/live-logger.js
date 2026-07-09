/**
 * =============================================================================
 * ANGELA-MATRIX: [L1] [B] [C] [L0]
 * =============================================================================
 *
 * Live-status logger — single updating line for steady-state loops.
 * Node.js: uses process.stdout.write with ANSI codes for terminal live updates.
 * Browser: falls back to console.debug with rate limiting.
 */

class LiveLogger {
    constructor() {
        this._lastLine = '';
        this._suppressed = 0;
        this._suppressedKey = '';
        this._isNode = typeof process !== 'undefined' && !!process.stdout;
        this._lastLog = 0;
        this._minInterval = 1.0;
    }

    _ts() {
        return new Date().toISOString().replace('T', ' ').substring(0, 19);
    }

    _clear() {
        if (this._isNode) process.stdout.write('\r\x1b[K');
    }

    _write(text) {
        if (this._isNode) {
            process.stdout.write(text);
        } else if (Date.now() - this._lastLog > this._minInterval * 1000) {
            console.debug(text.trimEnd());
            this._lastLog = Date.now();
        }
    }

    status(text) {
        const ts = this._ts();
        this._clear();
        const line = '\r\u230A[' + ts + '] ' + text;
        this._write(line);
        this._lastLine = line.trim();
    }

    statusInterval(text, intervalMs) {
        const ts = this._ts();
        const sec = (intervalMs / 1000).toFixed(1);
        this._clear();
        const line = '\r\u230A[' + ts + '][' + sec + 's] ' + text;
        this._write(line);
        this._lastLine = line.trim();
    }

    statusDone(text) {
        this._clear();
        if (text) this._write('\r' + text + '\n');
        this._lastLine = '';
    }

    error(msg, key) {
        const ts = this._ts();
        if (key && key === this._suppressedKey) {
            this._suppressed++;
            return;
        }
        if (this._suppressed > 0) this._flushSuppressed();
        if (this._lastLine && this._isNode) process.stdout.write('\n');
        this._clear();
        this._write('\r\x1b[31m\u26A0 [' + ts + '] ' + msg + '\x1b[0m\n');
        this._suppressed = 0;
        this._suppressedKey = key || '';
        if (this._lastLine) {
            this._clear();
            this._write('\r' + this._lastLine);
        }
    }

    _flushSuppressed() {
        const ts = this._ts();
        this._write('\r\x1b[33m  \u26A0 [' + ts + '] ... and ' + this._suppressed + ' more suppressed (' + this._suppressedKey + ')\x1b[0m\n');
        this._suppressed = 0;
        this._suppressedKey = '';
    }

    warn(msg) {
        const ts = this._ts();
        if (this._lastLine && this._isNode) process.stdout.write('\n');
        this._clear();
        this._write('\r\x1b[33m\u26A0 [' + ts + '] ' + msg + '\x1b[0m\n');
        if (this._lastLine) {
            this._clear();
            this._write('\r' + this._lastLine);
        }
    }

    info(msg) {
        const ts = this._ts();
        if (this._lastLine && this._isNode) process.stdout.write('\n');
        this._clear();
        this._write('\r[' + ts + '] ' + msg + '\n');
        if (this._lastLine) {
            this._clear();
            this._write('\r' + this._lastLine);
        }
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = LiveLogger;
}
