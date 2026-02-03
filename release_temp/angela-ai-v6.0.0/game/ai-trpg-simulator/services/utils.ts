import { useI18n } from '../context/i18n';
import { CodexAsset } from '../types';

/**
 * A hook that returns a function to parse API errors into user-friendly strings.
 * It handles specific, known errors and provides context-aware fallbacks for unknown errors.
 */
export const useApiErrorHandler = () => {
    const { t } = useI18n();

    const parseApiError = (e: unknown, context: 'init' | 'turn' | 'load' | 'generic' = 'turn'): string => {
        const errorMessage = e instanceof Error ? e.message : String(e);

        // --- Specific, Identifiable Errors ---
        // These take priority and are shown regardless of context.
        
        // Concurrency Conflict
        if (errorMessage === 'BUSY_CONFLICT') {
            return t('service.errorConflict');
        }

        // Rate Limit & Quota
        if (errorMessage.includes('RESOURCE_EXHAUSTED') || errorMessage.includes('429') || /quota/i.test(errorMessage)) {
            return t('service.errorRateLimit');
        }

        // Invalid API Key (covers general and specific VEO case)
        if (/API key not valid/i.test(errorMessage) || errorMessage.includes("API_KEY_NOT_FOUND")) {
            return t('service.errorInvalidApiKey');
        }

        // Prompt Blocked due to Safety Settings
        if (/safety|blocked/i.test(errorMessage) && /response/i.test(errorMessage)) {
             return t('service.errorPromptBlocked');
        }
        
        // Server-side errors (5xx)
        if (/5\d{2}/.test(errorMessage)) {
             return t('service.errorServer');
        }

        // --- Context-Specific Fallbacks for Unknown Errors ---
        // Log the technical error for debugging, but show a user-friendly message.
        console.error(`Unhandled API Error (context: ${context}):`, errorMessage, e);

        switch (context) {
            case 'init':
                return t('service.errorInit');
            case 'turn':
                return t('service.errorTurn');
            case 'load':
                return t('service.errorLoad');
            case 'generic':
            default:
                // A more generic message for tools outside the main game loop
                return t('service.errorUnexpected');
        }
    };

    return { parseApiError };
};


/**
 * Converts a Blob object to a base64 data URI string.
 * This is used to make video files saveable in JSON.
 * @param blob The blob to convert.
 * @returns A promise that resolves with the base64 data URI.
 */
export const blobToBase64 = (blob: Blob): Promise<string> => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result as string);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
};

/**
 * Extracts the raw base64 data from a data URI string.
 * @param dataUrl The data URI (e.g., "data:image/jpeg;base64,xxxxxxxx").
 * @returns The raw base64 string, or an empty string if invalid.
 */
export const dataUrlToBase64 = (dataUrl: string): string => {
    if (!dataUrl || !dataUrl.includes(',')) {
        return '';
    }
    return dataUrl.split(',')[1];
};

/**
 * Extracts the primary image URL from various Codex asset types.
 * @param asset The CodexAsset to extract the URL from.
 * @returns The image URL string, or undefined if not applicable.
 */
export const getAssetUrl = (asset: CodexAsset): string | undefined => {
    switch (asset.type) {
        case 'character':
        case 'location':
            return asset.imageUrl;
        case 'item':
            return asset.iconUrl;
        case 'image':
        case 'video':
        case 'audio':
            return asset.url;
        case 'model':
             // For models, we'll default to the side view as a representative image
            return asset.sideViewUrl;
        default:
            return undefined;
    }
}


function writeString(view: DataView, offset: number, string: string) {
    for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
}

/**
 * Creates a WAV file blob from raw PCM audio data.
 * @param pcmData The raw PCM data as a Uint8Array.
 * @param sampleRate The sample rate of the audio.
 * @param numChannels The number of channels.
 * @param bitsPerSample The number of bits per sample.
 * @returns A Blob object representing the WAV file.
 */
export const createWavBlob = (pcmData: Uint8Array, sampleRate: number, numChannels: number, bitsPerSample: number): Blob => {
    const dataSize = pcmData.length;
    const buffer = new ArrayBuffer(44 + dataSize);
    const view = new DataView(buffer);

    // RIFF header
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + dataSize, true);
    writeString(view, 8, 'WAVE');
    // "fmt " sub-chunk
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true); // Subchunk1Size for PCM
    view.setUint16(20, 1, true); // AudioFormat: 1 for PCM
    view.setUint16(22, numChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * numChannels * (bitsPerSample / 8), true); // ByteRate
    view.setUint16(32, numChannels * (bitsPerSample / 8), true); // BlockAlign
    view.setUint16(34, bitsPerSample, true);
    // "data" sub-chunk
    writeString(view, 36, 'data');
    view.setUint32(40, dataSize, true);
    
    // Write PCM data
    new Uint8Array(view.buffer, 44).set(pcmData);

    return new Blob([view], { type: 'audio/wav' });
};

// --- Centralized Audio Decoding ---

/**
 * Decodes a base64 string into a Uint8Array.
 * @param base64 The base64 encoded string.
 * @returns The decoded Uint8Array.
 */
export function decode(base64: string): Uint8Array {
    const binaryString = atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes;
}

/**
 * Decodes raw PCM audio data into an AudioBuffer for playback.
 * This is necessary because the TTS/SFX models return raw audio, not a file format.
 * @param data The raw audio data.
 * @param ctx The AudioContext to create the buffer in.
 * @param sampleRate The sample rate of the audio (e.g., 24000 for TTS).
 * @param numChannels The number of audio channels.
 * @returns A promise that resolves with the decoded AudioBuffer.
 */
export async function decodeAudioData(
    data: Uint8Array,
    ctx: AudioContext,
    sampleRate: number,
    numChannels: number,
): Promise<AudioBuffer> {
    // The raw data is 16-bit signed integers (Int16).
    const dataInt16 = new Int16Array(data.buffer);
    const frameCount = dataInt16.length / numChannels;
    const buffer = ctx.createBuffer(numChannels, frameCount, sampleRate);

    for (let channel = 0; channel < numChannels; channel++) {
        const channelData = buffer.getChannelData(channel);
        for (let i = 0; i < frameCount; i++) {
            // Convert Int16 sample to a float in the range [-1.0, 1.0]
            channelData[i] = dataInt16[i * numChannels + channel] / 32768.0;
        }
    }
    return buffer;
}
