/**
 * MultimodalAPIClient — extends AngelaAPIClient with multimodal API methods.
 *
 * P34: Frontend multimodal API client for Electron Desktop.
 * Provides methods for all /multimodal/* and /api/v1/* endpoints.
 */

class MultimodalAPIClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.apiBase = `${baseURL}/api/v1`;
    }

    /** Test backend connection. */
    async checkHealth() {
        try {
            const res = await fetch(`${this.baseURL}/api/v1/health`, {
                signal: AbortSignal.timeout(5000)
            });
            return res.ok;
        } catch {
            return false;
        }
    }

    /** Encode image or audio data. */
    async encode(data, modality = 'vision', itemId = null) {
        const form = new FormData();
        const blob = new Blob([data], { type: modality === 'vision' ? 'image/png' : 'audio/wav' });
        form.append('file', blob, `input.${modality === 'vision' ? 'png' : 'wav'}`);
        form.append('modality', modality);
        if (itemId) form.append('item_id', itemId);
        const res = await fetch(`${this.apiBase}/multimodal/encode`, {
            method: 'POST', body: form,
            signal: AbortSignal.timeout(30000)
        });
        return res.json();
    }

    /** Decode a previously encoded item. */
    async decode(itemId, modality = 'vision', format = 'base64') {
        const form = new FormData();
        form.append('item_id', itemId);
        form.append('modality', modality);
        form.append('output_format', format);
        const res = await fetch(`${this.apiBase}/multimodal/decode`, {
            method: 'POST', body: form,
            signal: AbortSignal.timeout(30000)
        });
        return res.json();
    }

    /** Compare two items cross-modally. */
    async compare(itemA, itemB) {
        const form = new FormData();
        form.append('item_a', itemA);
        form.append('item_b', itemB);
        const res = await fetch(`${this.apiBase}/multimodal/compare`, {
            method: 'POST', body: form,
            signal: AbortSignal.timeout(15000)
        });
        return res.json();
    }

    /** Retrieve top-k similar items. */
    async retrieve(queryId, topK = 5, modalityFilter = null) {
        const form = new FormData();
        form.append('query_id', queryId);
        form.append('top_k', topK);
        if (modalityFilter) form.append('modality_filter', modalityFilter);
        const res = await fetch(`${this.apiBase}/multimodal/retrieve`, {
            method: 'POST', body: form,
            signal: AbortSignal.timeout(15000)
        });
        return res.json();
    }

    /** Trigger training pipeline. */
    async train(mode = 'full', epochs = 5, lr = 0.01, useReal = false) {
        const form = new FormData();
        form.append('mode', mode);
        form.append('epochs', epochs);
        form.append('lr', lr);
        form.append('use_real', useReal);
        const res = await fetch(`${this.apiBase}/multimodal/train`, {
            method: 'POST', body: form,
            signal: AbortSignal.timeout(120000)
        });
        return res.json();
    }

    /** Evaluate quality. */
    async evaluate(itemId = null, modality = 'vision', nSamples = 5) {
        const form = new FormData();
        if (itemId) form.append('item_id', itemId);
        form.append('modality', modality);
        form.append('n_samples', nSamples);
        const res = await fetch(`${this.apiBase}/multimodal/evaluate`, {
            method: 'POST', body: form,
            signal: AbortSignal.timeout(30000)
        });
        return res.json();
    }

    /** Cross-modal generation. */
    async generate(sourceItemId, targetModality = 'audio') {
        const form = new FormData();
        form.append('source_item_id', sourceItemId);
        form.append('target_modality', targetModality);
        const res = await fetch(`${this.apiBase}/multimodal/generate`, {
            method: 'POST', body: form,
            signal: AbortSignal.timeout(60000)
        });
        return res.json();
    }

    /** Cross-modal inference via router. */
    async crossInfer(modality = 'cross', mode = 'compare', data = null) {
        const form = new FormData();
        form.append('source_modality', modality);
        form.append('mode', mode);
        if (data) {
            const mime = modality === 'vision' ? 'image/png' : 'audio/wav';
            form.append('file', new Blob([data], { type: mime }), `input.${modality === 'vision' ? 'png' : 'wav'}`);
        }
        const res = await fetch(`${this.apiBase}/multimodal/cross-infer`, {
            method: 'POST', body: form,
            signal: AbortSignal.timeout(30000)
        });
        return res.json();
    }

    /** Get quality dashboard. */
    async qualityDashboard() {
        const res = await fetch(`${this.apiBase}/multimodal/quality/dashboard`, {
            signal: AbortSignal.timeout(10000)
        });
        return res.json();
    }

    /** List all registered items. */
    async listItems() {
        const res = await fetch(`${this.apiBase}/multimodal/items`, {
            signal: AbortSignal.timeout(5000)
        });
        return res.json();
    }

    /** Clear all registered items. */
    async clearItems() {
        const res = await fetch(`${this.apiBase}/multimodal/clear`, {
            method: 'POST',
            signal: AbortSignal.timeout(5000)
        });
        return res.json();
    }

    /** Get multimodal system health. */
    async multimodalHealth() {
        const res = await fetch(`${this.apiBase}/multimodal/health`, {
            signal: AbortSignal.timeout(5000)
        });
        return res.json();
    }
}

// Export for use in renderer
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MultimodalAPIClient;
}
