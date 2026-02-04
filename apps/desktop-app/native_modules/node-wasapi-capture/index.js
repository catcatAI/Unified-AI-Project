const WASAPI_BINDING = require('./build/Release/wasapi-capture.node');

class WASAPICapture {
    constructor() {
        this._native = new WASAPI_BINDING.WASAPICapture();
        this._isCapturing = false;
    }

    async start(deviceId = null, callback = null) {
        if (this._isCapturing) {
            throw new Error('Already capturing');
        }

        return new Promise((resolve, reject) => {
            try {
                const wrappedCallback = callback ? (data) => {
                    if (callback) callback(data);
                } : null;

                const result = this._native.start(deviceId || '', wrappedCallback);
                
                if (result) {
                    this._isCapturing = true;
                    resolve(true);
                } else {
                    reject(new Error('Failed to start capture'));
                }
            } catch (error) {
                reject(error);
            }
        });
    }

    async stop() {
        if (!this._isCapturing) {
            return true;
        }

        return new Promise((resolve, reject) => {
            try {
                const result = this._native.stop();
                this._isCapturing = false;
                resolve(result);
            } catch (error) {
                reject(error);
            }
        });
    }

    getFormat() {
        return this._native.getFormat();
    }

    get isCapturing() {
        return this._isCapturing;
    }

    static getDevices() {
        return WASAPI_BINDING.WASAPICapture.getDevices();
    }

    static getDefaultDevice() {
        return WASAPI_BINDING.WASAPICapture.getDefaultDevice();
    }
}

module.exports = WASAPICapture;
