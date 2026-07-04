/**
 * MultimodalPanel — frontend controller for the multimodal panel.
 *
 * P34: Full multimodal UI for Electron Desktop app.
 * Handles tab navigation, file uploads, audio recording, API calls,
 * and rendering results for all multimodal operations.
 */

class MultimodalPanel {
    constructor() {
        this.client = new MultimodalAPIClient(localStorage.getItem('backend_ip') || 'http://localhost:8000');
        this.visionData = null;
        this.audioData = null;
        this.visionPreview = null;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.initialized = false;
    }

    async init() {
        if (this.initialized) return;
        this.initialized = true;

        // Check backend connection
        const connected = await this.client.checkHealth();
        this._updateStatus(connected);

        // Bind UI events
        this._bindTabEvents();
        this._bindVisionUpload();
        this._bindAudioUpload();
        this._bindEncodeDecode();
        this._bindCompare();
        this._bindGenerate();
        this._bindTrain();
        this._bindQuality();
        this._bindRecording();

        // Initial refresh
        await this._refreshItems();
        await this._refreshQuality();
    }

    // ========== Status ==========

    _updateStatus(connected) {
        const dot = document.getElementById('status-dot');
        const text = document.getElementById('status-text');
        if (connected) {
            dot.className = 'status-dot';
            text.textContent = 'Connected';
        } else {
            dot.className = 'status-dot offline';
            text.textContent = 'Disconnected';
        }
    }

    // ========== Tab Navigation ==========

    _bindTabEvents() {
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                tab.classList.add('active');
                const content = document.getElementById(`tab-${tab.dataset.tab}`);
                if (content) content.classList.add('active');
            });
        });
    }

    // ========== Vision Upload ==========

    _bindVisionUpload() {
        const zone = document.getElementById('vision-upload');
        const input = document.getElementById('vision-file-input');

        zone.addEventListener('click', () => input.click());

        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });

        zone.addEventListener('dragleave', () => {
            zone.classList.remove('dragover');
        });

        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) this._handleVisionFile(files[0]);
        });

        input.addEventListener('change', () => {
            if (input.files.length > 0) this._handleVisionFile(input.files[0]);
        });
    }

    _handleVisionFile(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            this.visionData = e.target.result;
            const preview = document.getElementById('vision-preview');
            preview.innerHTML = `<img class="preview-img" src="${e.target.result}" alt="Preview">`;
            this.visionPreview = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    // ========== Audio Upload ==========

    _bindAudioUpload() {
        const zone = document.getElementById('audio-upload');
        const input = document.getElementById('audio-file-input');

        zone.addEventListener('click', () => input.click());

        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });

        zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));

        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) this._handleAudioFile(e.dataTransfer.files[0]);
        });

        input.addEventListener('change', () => {
            if (input.files.length > 0) this._handleAudioFile(input.files[0]);
        });
    }

    _handleAudioFile(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            this.audioData = e.target.result;
        };
        reader.readAsArrayBuffer(file);
    }

    // ========== Audio Recording ==========

    _bindRecording() {
        const btn = document.getElementById('record-btn');
        btn.addEventListener('click', () => this._toggleRecording());
    }

    async _toggleRecording() {
        if (this.isRecording) {
            this._stopRecording();
        } else {
            await this._startRecording();
        }
    }

    async _startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) this.audioChunks.push(e.data);
            };

            this.mediaRecorder.onstop = async () => {
                stream.getTracks().forEach(t => t.stop());
                const blob = new Blob(this.audioChunks, { type: 'audio/webm' });
                const buffer = await blob.arrayBuffer();
                this.audioData = buffer;

                // Convert to WAV for the API
                this._showResult('audio-result', { status: 'Recorded', size: buffer.byteLength }, true);
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            document.getElementById('record-btn').classList.add('recording');
        } catch (err) {
            this._showResult('audio-result', { error: `Recording failed: ${err.message}` }, false);
        }
    }

    _stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
        this.isRecording = false;
        document.getElementById('record-btn').classList.remove('recording');
    }

    // ========== Encode/Decode ==========

    _bindEncodeDecode() {
        document.getElementById('btn-vision-encode').addEventListener('click', () => this._doVisionEncode());
        document.getElementById('btn-vision-decode').addEventListener('click', () => this._doVisionDecode());
        document.getElementById('btn-audio-encode').addEventListener('click', () => this._doAudioEncode());
        document.getElementById('btn-audio-decode').addEventListener('click', () => this._doAudioDecode());
        document.getElementById('btn-refresh-items').addEventListener('click', () => this._refreshItems());
        document.getElementById('btn-clear-items').addEventListener('click', () => this._clearItems());
    }

    async _doVisionEncode() {
        if (!this.visionData) return this._showResult('vision-result', { error: 'No image uploaded' }, false);
        const base64 = this.visionData.split(',')[1];
        const bytes = Uint8Array.from(atob(base64), c => c.charCodeAt(0));
        const result = await this.client.encode(bytes, 'vision');
        this._showResult('vision-result', result, result.success);
        await this._refreshItems();
    }

    async _doVisionDecode() {
        const items = await this._getItems();
        const visionItems = Object.entries(items).filter(([_, v]) => v.modality === 'vision');
        if (visionItems.length === 0) return this._showResult('vision-result', { error: 'No vision items to decode' }, false);
        const result = await this.client.decode(visionItems[0][0], 'vision');
        this._showResult('vision-result', result, result.success);
        // Show decoded image
        if (result.decoded) {
            const preview = document.getElementById('vision-preview');
            preview.innerHTML = `<img class="preview-img" src="${result.decoded}" alt="Decoded">`;
        }
    }

    async _doAudioEncode() {
        if (!this.audioData) return this._showResult('audio-result', { error: 'No audio recorded/uploaded' }, false);
        const bytes = new Uint8Array(this.audioData);
        const result = await this.client.encode(bytes, 'audio');
        this._showResult('audio-result', result, result.success);
        await this._refreshItems();
    }

    async _doAudioDecode() {
        const items = await this._getItems();
        const audioItems = Object.entries(items).filter(([_, v]) => v.modality === 'audio');
        if (audioItems.length === 0) return this._showResult('audio-result', { error: 'No audio items to decode' }, false);
        const result = await this.client.decode(audioItems[0][0], 'audio');
        this._showResult('audio-result', result, result.success);
    }

    // ========== Compare ==========

    _bindCompare() {
        document.getElementById('btn-compare').addEventListener('click', () => this._doCompare());
    }

    async _doCompare() {
        const a = document.getElementById('compare-item-a').value;
        const b = document.getElementById('compare-item-b').value;
        if (!a || !b) return this._showResult('compare-result', { error: 'Select both items' }, false);
        const result = await this.client.compare(a, b);
        this._showResult('compare-result', result, result.success);
    }

    // ========== Generate ==========

    _bindGenerate() {
        document.getElementById('btn-generate').addEventListener('click', () => this._doGenerate());
        document.getElementById('btn-cross-infer').addEventListener('click', () => this._doCrossInfer());
    }

    async _doGenerate() {
        const src = document.getElementById('generate-source').value;
        const target = document.getElementById('generate-target').value;
        if (!src) return this._showResult('generate-result', { error: 'Select source item' }, false);
        const result = await this.client.generate(src, target);
        this._showResult('generate-result', result, result.success);
    }

    async _doCrossInfer() {
        const mod = document.getElementById('cross-modality').value;
        const mode = document.getElementById('cross-mode').value;
        const result = await this.client.crossInfer(mod, mode);
        this._showResult('cross-result', result, result.success);
    }

    // ========== Train ==========

    _bindTrain() {
        document.getElementById('btn-train').addEventListener('click', () => this._doTrain());
        document.getElementById('btn-evaluate').addEventListener('click', () => this._doEvaluate());
    }

    async _doTrain() {
        const mode = document.getElementById('train-mode').value;
        const epochs = parseInt(document.getElementById('train-epochs').value) || 5;
        const result = await this.client.train(mode, epochs);
        this._showResult('train-result', result, result.status === 'completed');
    }

    async _doEvaluate() {
        const result = await this.client.evaluate(null, 'vision', 5);
        this._showResult('train-result', result, result.success);
    }

    // ========== Quality Dashboard ==========

    _bindQuality() {
        document.getElementById('btn-refresh-quality').addEventListener('click', () => this._refreshQuality());
    }

    async _refreshQuality() {
        try {
            const data = await this.client.qualityDashboard();
            if (data.success === false) {
                this._setMetric('q-ssim', 'N/A', '');
                this._setMetric('q-psnr', 'N/A', '');
                this._setMetric('q-vision-calls', '0', '');
                this._setMetric('q-vision-time', 'N/A', '');
                this._setMetric('q-snr', 'N/A', '');
                this._setMetric('q-audio-calls', '0', '');
                this._setMetric('q-audio-time', 'N/A', '');
                return;
            }

            const vision = data.vision || {};
            const audio = data.audio || {};
            const health = data.overall_health || 'unknown';

            this._setMetric('q-ssim', vision.avg_ssim?.toFixed(4) ?? 'N/A', vision.avg_ssim >= 0.7 ? 'good' : vision.avg_ssim >= 0.3 ? 'warn' : 'bad');
            this._setMetric('q-psnr', vision.avg_psnr?.toFixed(1) ?? 'N/A', vision.avg_psnr >= 25 ? 'good' : vision.avg_psnr >= 15 ? 'warn' : 'bad');
            this._setMetric('q-vision-calls', vision.total_calls ?? 0, '');
            this._setMetric('q-vision-time', vision.avg_time_ms ? `${vision.avg_time_ms.toFixed(0)}ms` : 'N/A', '');

            this._setMetric('q-snr', audio.avg_snr?.toFixed(1) ?? 'N/A', audio.avg_snr >= 15 ? 'good' : audio.avg_snr >= 5 ? 'warn' : 'bad');
            this._setMetric('q-audio-calls', audio.total_calls ?? 0, '');
            this._setMetric('q-audio-time', audio.avg_time_ms ? `${audio.avg_time_ms.toFixed(0)}ms` : 'N/A', '');

            // Overall health bar
            const fill = document.getElementById('health-bar-fill');
            const label = document.getElementById('health-label');
            const score = document.getElementById('health-score');

            if (health === 'healthy') {
                fill.style.width = '85%';
                fill.className = 'health-bar-fill good';
                label.textContent = '✅ Healthy';
            } else if (health === 'degraded') {
                fill.style.width = '50%';
                fill.className = 'health-bar-fill warn';
                label.textContent = '⚠️ Degraded';
            } else {
                fill.style.width = '25%';
                fill.className = 'health-bar-fill bad';
                label.textContent = '🔴 Unhealthy';
            }
            score.textContent = `${data.total_requests || 0} total requests`;
        } catch (err) {
            console.error('Quality refresh failed:', err);
        }
    }

    _setMetric(id, value, cls) {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = value;
            el.className = 'metric-value' + (cls ? ` ${cls}` : '');
        }
    }

    // ========== Items Management ==========

    async _refreshItems() {
        try {
            const health = await this.client.multimodalHealth();
            const items = await this._getItems();
            const list = document.getElementById('items-list');
            const entries = Object.entries(items);
            if (entries.length === 0) {
                list.textContent = 'No items registered.';
            } else {
                list.innerHTML = entries.map(([id, item]) =>
                    `<div style="padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.05)">
                        <span style="color:var(--accent)">${id}</span>
                        <span style="color:var(--text-dim);margin-left:8px">[${item.modality}]</span>
                        <span style="color:var(--text-dim);float:right;font-size:12px">${new Date(item.timestamp * 1000).toLocaleTimeString()}</span>
                    </div>`
                ).join('');
            }

            // Update select dropdowns
            this._populateSelect('compare-item-a', entries);
            this._populateSelect('compare-item-b', entries);
            this._populateSelect('generate-source', entries);

            this._updateStatus(true);
        } catch (err) {
            this._updateStatus(false);
        }
    }

    async _getItems() {
        try {
            const result = await this.client.listItems();
            if (result.success && result.items) {
                return result.items;
            }
            return {};
        } catch (err) {
            console.warn('[MultimodalPanel] Failed to get items:', err.message);
            return {};
        }
    }

    _populateSelect(id, entries) {
        const sel = document.getElementById(id);
        if (!sel) return;
        const current = sel.value;
        sel.innerHTML = '<option value="">Select...</option>';
        entries.forEach(([key, item]) => {
            const opt = document.createElement('option');
            opt.value = key;
            opt.textContent = `${key} [${item.modality}]`;
            sel.appendChild(opt);
        });
        if (current) sel.value = current;
    }

    async _clearItems() {
        try {
            const result = await this.client.clearItems();
            this._showResult('vision-result', result, result.success);
            await this._refreshItems();
        } catch (err) {
            console.warn('[MultimodalPanel] Failed to clear items:', err.message);
            this._refreshItems();
        }
    }

    // ========== Result Display ==========

    _showResult(containerId, data, isSuccess) {
        const el = document.getElementById(containerId);
        if (!el) return;
        el.style.display = 'block';

        if (!isSuccess || data.error) {
            el.innerHTML = `<div style="color:var(--danger)">❌ ${data.error || 'Operation failed'}</div>`;
            return;
        }

        const html = Object.entries(data)
            .filter(([k]) => !['decoded', 'generated', 'decoded_image', 'decoded_array', 'feature_vector', 'latent'].includes(k))
            .map(([k, v]) => {
                let val = typeof v === 'object' ? JSON.stringify(v, null, 2) : v;
                if (typeof val === 'string' && val.length > 100) val = val.substring(0, 100) + '...';
                return `<div><span class="key">${k}:</span> <span class="value">${val}</span></div>`;
            })
            .join('');

        el.innerHTML = html;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const panel = new MultimodalPanel();
    panel.init();
    window.multimodalPanel = panel;
});
