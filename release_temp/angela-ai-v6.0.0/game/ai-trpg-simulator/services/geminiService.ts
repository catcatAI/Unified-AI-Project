import { GoogleGenAI, Type, Modality, GenerateContentResponse, Chat, GenerateImagesResponse, VideosOperation } from "@google/genai";
import { PlayerActionSuccessResult, ApiSettings, Message, GameState } from '../types';
import { blobToBase64, dataUrlToBase64, createWavBlob } from "./utils";
import { actionMusic, calmMusic, epicMusic, mysteriousMusic, sadMusic, horrorMusic, suspenseMusic } from './audioAssets';

if (!process.env.API_KEY) {
    throw new Error("API_KEY environment variable not set");
}

// Function to get a fresh GoogleGenAI instance for each API call
const getGenAIInstance = () => {
    return new GoogleGenAI({ apiKey: process.env.API_KEY });
};

// --- API Rate Limiting ---
type ApiCategory = 'TEXT' | 'IMAGE' | 'VIDEO' | 'TTS' | 'AUDIO';

const baseCategoryCooldowns: Record<ApiCategory, number> = {
    TEXT: 1000,
    IMAGE: 13000,
    VIDEO: 20000,
    TTS: 2000,
    AUDIO: 2000,
};

const dynamicCooldowns = { ...baseCategoryCooldowns };
const GLOBAL_COOLDOWN = 4500; 

const lastRequestTimes: Partial<Record<ApiCategory | 'GLOBAL', number>> = {};
let sequences: Partial<Record<ApiCategory, Promise<any>>> = {};


export function rateLimitedRequest<T>(category: ApiCategory, apiCall: () => Promise<T>): Promise<T> {
  // Use a different promise chain for each category to prevent blocking
  const sequence = sequences[category] || Promise.resolve();
  
  const newPromise = sequence.then(() => {
    const now = Date.now();
    
    const lastCategoryRequestTime = lastRequestTimes[category] || 0;
    const categoryCooldown = dynamicCooldowns[category];
    const timeSinceLastCategory = now - lastCategoryRequestTime;
    const categoryDelay = timeSinceLastCategory < categoryCooldown ? categoryCooldown - timeSinceLastCategory : 0;
    
    const lastGlobalRequestTime = lastRequestTimes['GLOBAL'] || 0;
    const timeSinceLastGlobal = now - lastGlobalRequestTime;
    const globalDelay = timeSinceLastGlobal < GLOBAL_COOLDOWN ? GLOBAL_COOLDOWN - timeSinceLastGlobal : 0;

    const delay = Math.max(categoryDelay, globalDelay);
    
    return new Promise(resolve => setTimeout(resolve, delay)).then(() => {
        const callTime = Date.now();
        lastRequestTimes[category] = callTime;
        lastRequestTimes['GLOBAL'] = callTime;
        return apiCall();
    });
  });

  sequences[category] = newPromise.catch(() => {});
  return newPromise;
}


// --- API Retry Wrapper ---
const MAX_RETRIES = 3;
const INITIAL_BACKOFF_MS = 2000;

async function generateContentWithRetry(
    params: any,
    primaryModelName: string,
    fallbackModelName: string,
    onFallbackCallback?: () => void
): Promise<GenerateContentResponse> {
    const isRateLimitError = (e: any): boolean => {
        const errorMessage = e instanceof Error ? e.message : String(e);
        return errorMessage.includes('RESOURCE_EXHAUSTED') || errorMessage.includes('429') || /quota/i.test(errorMessage);
    };

    let currentParams = { ...params };
    let lastError: any;
    let hasFallenBack = false;

    for (let i = 0; i < MAX_RETRIES; i++) {
        try {
            const ai = getGenAIInstance();
            const response: GenerateContentResponse = await rateLimitedRequest('TEXT', () => ai.models.generateContent(currentParams));
            // We can no longer assume response.text is a string, as it could be a function call.
            // The calling function will now be responsible for validation.
            return response; // Success, exit function
        } catch (error) {
            lastError = error;
            console.warn(`API call attempt ${i + 1} of ${MAX_RETRIES} failed.`, error);

            if (i === MAX_RETRIES - 1) {
                // Last attempt failed, break loop to throw error at the end.
                break;
            }

            if (isRateLimitError(error)) {
                // Increase cooldown for future requests to be safer.
                dynamicCooldowns['TEXT'] = Math.min(dynamicCooldowns['TEXT'] * 1.5, 60000);

                // Attempt to switch to the fallback model if we haven't already.
                if (onFallbackCallback && !hasFallenBack && currentParams.model === primaryModelName) {
                    console.warn(`Rate limit on primary model. Switching to ${fallbackModelName} for subsequent retries.`);
                    onFallbackCallback();
                    currentParams.model = fallbackModelName;
                    hasFallenBack = true;
                }
            }

            // Wait with exponential backoff before the next attempt for any type of retryable error.
            const delay = INITIAL_BACKOFF_MS * Math.pow(2, i) + Math.random() * 1000;
            console.warn(`Waiting ${delay.toFixed(0)}ms before retry #${i + 2}.`);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }

    // After all retries, throw a proper error object.
    console.error(`API call failed after ${MAX_RETRIES} attempts. Aborting.`, lastError);
    if (lastError instanceof Error) {
        throw lastError;
    } else {
        const errorString = (typeof lastError === 'object' && lastError !== null) 
            ? JSON.stringify(lastError) 
            : String(lastError);
        throw new Error(`API call failed after ${MAX_RETRIES} retries: ${errorString}`);
    }
}


// --- Helper function for safe JSON parsing ---
export function safeJsonParse(text: string | undefined | null): any {
  let jsonString = (typeof text === 'string' ? text : '').trim();
  
  if (!jsonString) {
    throw new Error("AI response was empty, likely due to safety filters or an empty response.");
  }

  const markdownMatch = jsonString.match(/```json\n?([\s\S]*)\n?```/);
  if (markdownMatch && markdownMatch[1]) {
    jsonString = markdownMatch[1];
  }

  try {
    return JSON.parse(jsonString);
  } catch (error) {
    console.error("Failed to parse JSON:", text);
    throw new Error(`The AI returned a malformed response that could not be parsed as JSON. Raw response: ${text}`);
  }
}

export async function generateSummary(
    textToSummarize: string,
    settings: Pick<ApiSettings, 'primaryTextModel' | 'fallbackTextModel'>,
    onFallback: () => void
): Promise<string> {
    const { primaryTextModel, fallbackTextModel } = settings;
    const prompt = `Summarize the following text into a single, dense paragraph. Focus on the key characters, setting, and immediate conflict.

TEXT TO SUMMARIZE:
---
${textToSummarize}
---

SUMMARY:`;

    const response = await generateContentWithRetry({
        model: primaryTextModel,
        contents: prompt
    }, primaryTextModel, fallbackTextModel, onFallback);

    return (response.text || "").trim();
}

export async function generateScenarioSuggestion(currentPrompt: string, locale: 'en' | 'zh', primaryTextModel: string, fallbackTextModel: string, onFallback: () => void) {
    const ai = getGenAIInstance();
    const prompt = `Based on the following scenario prompt, suggest one creative and interesting alternative or addition.
    Respond with only the new prompt text, nothing else. The language of your response should be ${locale === 'zh' ? 'Chinese' : 'English'}.
    
    Current Prompt:
    "${currentPrompt}"`;

    const response = await generateContentWithRetry({ model: primaryTextModel, contents: prompt }, primaryTextModel, fallbackTextModel, onFallback);
    return (response.text || "").trim();
}

export async function generateFullGameSetup(
    params: any,
    settings: ApiSettings,
    onFallback: () => void,
) {
    const { primaryTextModel, fallbackTextModel } = settings;

    const response = await generateContentWithRetry(
        params,
        primaryTextModel,
        fallbackTextModel,
        onFallback
    );

    return safeJsonParse(response.text);
}


export async function generateTurnResponse(
    params: any,
    settings: ApiSettings,
    onFallback: () => void,
): Promise<GenerateContentResponse> {
    const { primaryTextModel, fallbackTextModel } = settings;
    
    // This function now returns the raw response so the calling service
    // can check for function calls before attempting to parse JSON.
    return await generateContentWithRetry(
        params,
        primaryTextModel,
        fallbackTextModel,
        onFallback
    );
}

export async function generatePlayerAutoAction(
    gameState: GameState,
    settings: Pick<ApiSettings, 'primaryTextModel' | 'fallbackTextModel' | 'aiCreativity'>,
    onFallback: () => void
): Promise<string> {
    const { primaryTextModel, fallbackTextModel, aiCreativity } = settings;
    const playerCharacter = gameState.characters.find(c => !c.isAI);
    if (!playerCharacter) return "Wait.";

    const context = `
        **Game Summary:** ${gameState.gameSummary}
        **Current Location:** ${gameState.location}
        **Recent Events:**
        ${gameState.gameLog.slice(-5).map(m => `${m.author}: ${m.content}`).join('\n')}
    `;

    const prompt = `You are role-playing as the character '${playerCharacter.name}'.
        Character Description: ${playerCharacter.description}
        Based on the current situation, decide on the most logical and in-character next action.
        The action should be a short, single sentence (e.g., "I will ask the bartender about the strange noise," or "I attack the goblin with my sword.").
        Your response must be ONLY the action string, in ${gameState.locale === 'zh' ? 'Chinese' : 'English'}.

        ${context}
        
        What is your next action?
    `;
    
    const response = await generateContentWithRetry({
        model: primaryTextModel,
        contents: prompt,
        config: {
            temperature: aiCreativity,
        }
    }, primaryTextModel, fallbackTextModel, onFallback);

    return (response.text || "").trim().replace(/["']/g, ""); // Remove quotes
}


export async function generateSimpleText(
    params: any,
    settings: Pick<ApiSettings, 'primaryTextModel' | 'fallbackTextModel'>,
    onFallback: () => void,
): Promise<string> {
     const { primaryTextModel, fallbackTextModel } = settings;
     const response = await generateContentWithRetry(
        params,
        primaryTextModel,
        fallbackTextModel,
        onFallback
    );
    return (response.text || "").trim();
}


export async function generateSuggestionsOnly(
    gameLog: Message[],
    locale: 'en' | 'zh',
    primaryTextModel: string,
    fallbackTextModel: string,
    onFallback: () => void
): Promise<{ suggestedActions: string[] }> {
    const ai = getGenAIInstance();
    const history = gameLog.slice(-6).map(m => `${m.author}: ${m.content}`).join('\n');
    
    const prompt = `Based on the following recent events in a tabletop RPG, provide exactly three diverse and interesting suggested actions for the player. The language of your response should be ${locale === 'zh' ? 'Chinese' : 'English'}.
    
    RECENT EVENTS:
    ${history}
    `;

    const response = await generateContentWithRetry({
        model: primaryTextModel,
        contents: prompt,
        config: {
            responseMimeType: 'application/json',
            responseSchema: {
                type: Type.OBJECT,
                properties: {
                    suggestedActions: {
                        type: Type.ARRAY,
                        items: { type: Type.STRING }
                    }
                },
                required: ['suggestedActions']
            }
        }
    }, primaryTextModel, fallbackTextModel, onFallback);

    return safeJsonParse(response.text);
}

export async function generateImage(prompt: string, aspectRatio: '16:9' | '1:1', model: string, sourceImageUrl?: string): Promise<string> {
    const ai = getGenAIInstance();
    
    const defaultImageGenModel = 'imagen-4.0-generate-001';
    const defaultImageEditModel = 'gemini-2.5-flash-image';
    let actualModel = model;

    if (sourceImageUrl) { // This is an edit/image-to-image task.
        // If no specific model was provided, or if the quality model was provided by mistake,
        // default to the correct model for this task type.
        if (!actualModel || actualModel === defaultImageGenModel) {
            actualModel = defaultImageEditModel;
        }

        const mimeTypeMatch = sourceImageUrl.match(/data:(image\/[a-zA-Z]+);base64,/);
        if (!mimeTypeMatch) {
            throw new Error("Invalid source image format.");
        }
        
        const response: GenerateContentResponse = await rateLimitedRequest('IMAGE', () => ai.models.generateContent({
            model: actualModel,
            contents: {
                parts: [
                    { inlineData: { data: dataUrlToBase64(sourceImageUrl), mimeType: mimeTypeMatch[1] }},
                    { text: prompt },
                ],
            },
            config: {
                responseModalities: [Modality.IMAGE],
            },
        }));
    
        for (const part of response.candidates[0].content.parts) {
            if (part.inlineData) {
                return part.inlineData.data;
            }
        }
        throw new Error('Image generation failed to produce an image from the source.');

    } else { // This is a text-to-image task.
        // If no specific model was provided, or if the edit model was provided by mistake,
        // default to the correct model for this task type.
        if (!actualModel || actualModel === defaultImageEditModel) {
            actualModel = defaultImageGenModel;
        }

        const response: GenerateImagesResponse = await rateLimitedRequest('IMAGE', () => ai.models.generateImages({
            model: actualModel,
            prompt: prompt,
            config: {
              numberOfImages: 1,
              outputMimeType: 'image/jpeg',
              aspectRatio: aspectRatio,
            },
        }));
    
        if (response.generatedImages && response.generatedImages.length > 0) {
            return response.generatedImages[0].image.imageBytes;
        }
        throw new Error('Image generation failed to produce an image.');
    }
}

// Consolidate generateImageFromImage into generateImage
export const generateImageFromImage = generateImage;


// Unified generateVideo function
export async function generateVideo(prompt: string, model: string, sourceImageUrl?: string, lastFrameUrl?: string): Promise<string> {
    const ai = getGenAIInstance();
    let operation: VideosOperation;

    const defaultVideoModel = 'veo-3.1-fast-generate-preview';
    let actualModel = model || defaultVideoModel;

    const payload: any = {
        model: actualModel,
        prompt,
        config: {
            numberOfVideos: 1,
            resolution: actualModel === 'veo-3.1-generate-preview' ? '1080p' : '720p', 
            aspectRatio: '16:9'
        }
    };
    
    if (sourceImageUrl) {
        const mimeTypeMatch = sourceImageUrl.match(/data:(image\/[a-zA-Z]+);base64,/);
        if (!mimeTypeMatch) {
            throw new Error("Invalid source image format.");
        }
        payload.image = {
            imageBytes: dataUrlToBase64(sourceImageUrl),
            mimeType: mimeTypeMatch[1],
        }
    }
    
    if (lastFrameUrl) { 
        const mimeTypeMatch = lastFrameUrl.match(/data:(image\/[a-zA-Z]+);base64,/);
        if (!mimeTypeMatch) {
            throw new Error("Invalid last frame image format.");
        }
        payload.config.lastFrame = {
            imageBytes: dataUrlToBase64(lastFrameUrl),
            mimeType: mimeTypeMatch[1],
        }
    }


    operation = await rateLimitedRequest('VIDEO', () => ai.models.generateVideos(payload));
    
    if (!operation.name) {
        throw new Error("Video generation operation did not return a name.");
    }

    while (!operation.done) {
        await new Promise(resolve => setTimeout(resolve, 10000));
        operation = await ai.operations.getVideosOperation({ operation: operation }); 
    }

    const downloadLink = operation.response?.generatedVideos?.[0]?.video?.uri;
    if (!downloadLink) {
        throw new Error("Video generation did not return a download link.");
    }
    const response = await fetch(`${downloadLink}&key=${process.env.API_KEY}`);
    if (!response.ok) {
        if (response.status === 404) { 
             throw new Error("API_KEY_NOT_FOUND");
        }
        throw new Error(`Failed to download video: ${response.statusText}`);
    }
    const blob = await response.blob();
    return await blobToBase64(blob);
}

export async function generateAudioFromText(prompt: string, model: string): Promise<string> {
    const ai = getGenAIInstance();

    const response: GenerateContentResponse = await rateLimitedRequest('AUDIO', () => ai.models.generateContent({
        model: model, // should be 'gemini-2.5-flash-preview-tts'
        contents: [{ parts: [{ text: `Sound effect of: ${prompt}` }] }], // Instruct it to generate a sound effect
        config: {
            responseModalities: [Modality.AUDIO],
        },
    }));

    const base64Audio = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
    if (!base64Audio) {
        throw new Error("SFX generation failed, no audio data received.");
    }
    return base64Audio; // Return raw base64 PCM data
}

export async function generateSpeech(text: string, gender: 'male' | 'female' | 'other' | 'gm', model: string): Promise<string> {
    const ai = getGenAIInstance();
    type VoiceName = 'Kore' | 'Puck' | 'Zephyr' | 'Charon' | 'Fenrir'; // Define exact types
    let voiceName: VoiceName = 'Kore'; 
    if (gender === 'male') voiceName = 'Puck';
    else if (gender === 'female') voiceName = 'Zephyr';

    const response: GenerateContentResponse = await rateLimitedRequest('TTS', () => ai.models.generateContent({
        model: model,
        contents: [{ parts: [{ text: text }] }],
        config: {
            responseModalities: [Modality.AUDIO],
            speechConfig: {
                voiceConfig: {
                    prebuiltVoiceConfig: { voiceName: voiceName },
                },
            },
        },
    }));

    const base64Audio = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
    if (!base64Audio) {
        throw new Error("TTS generation failed, no audio data received.");
    }
    return base64Audio;
}

export async function generateObjectBlueprint(prompt: string, primaryTextModel: string, fallbackTextModel: string, onFallback: () => void): Promise<string> {
    const ai = getGenAIInstance();
    const systemInstructionConst = `You are a technical designer. Your task is to create a detailed, non-visual, text-only blueprint for an object based on a user's prompt.
    Describe the object's components, materials, textures, and shape from the front, side, and top views. Be precise and literal.
    This description will be used by another AI to generate three separate, consistent orthographic images. Do not describe the background or lighting.
    Example: "A ceramic coffee mug. Front view: C-shaped handle on the right. Side view: Handle is not visible. Top view: Circular rim with a dark interior."
    Respond ONLY with the blueprint description.`;

    const response = await generateContentWithRetry({
        model: primaryTextModel,
        contents: prompt,
        config: { systemInstruction: systemInstructionConst }
    }, primaryTextModel, fallbackTextModel, onFallback);

    return (response.text || "").trim();
}

export async function refineBlueprintFromImages(originalPrompt: string, frontViewUrl: string, sideViewUrl: string, topViewUrl: string, primaryTextModel: string, fallbackTextModel: string, onFallback: () => void): Promise<string> {
     const ai = getGenAIInstance();
     const systemInstructionConst = `You are a senior technical designer. Your task is to analyze three orthographic views of an object, identify inconsistencies, and generate a single, corrected, unified text blueprint.
     The goal is to create a blueprint that will allow an image generation AI to create perfectly aligned and consistent front, side, and top views.
     - Analyze the provided "Original Prompt" for the user's intent.
     - Analyze the "Front View Image", "Side View Image", and "Top View Image" for their visual details.
     - Identify discrepancies between the views (e.g., a handle is on the right in the front view but on the left in the top view).
     - Write a new, single, coherent blueprint that reconciles these differences and provides a clear, consistent description for all three views.
     - Respond ONLY with the final, corrected blueprint description.`;
     
     const response = await generateContentWithRetry({
        model: primaryTextModel,
        contents: {
            parts: [
                { text: `Original Prompt: "${originalPrompt}"` },
                { text: "Analyze the following three images and produce a corrected, unified blueprint." },
                { text: "Front View Image:" },
                { inlineData: { data: dataUrlToBase64(frontViewUrl), mimeType: 'image/jpeg' } },
                { text: "Side View Image:" },
                { inlineData: { data: dataUrlToBase64(sideViewUrl), mimeType: 'image/jpeg' } },
                { text: "Top View Image:" },
                { inlineData: { data: dataUrlToBase64(topViewUrl), mimeType: 'image/jpeg' } },
            ]
        },
        config: { systemInstruction: systemInstructionConst },
     }, primaryTextModel, fallbackTextModel, onFallback);

     return (response.text || "").trim();
}


export async function generateObjectBlueprintFromImage(sourceImageUrl: string, primaryTextModel: string, fallbackTextModel: string, onFallback: () => void): Promise<string> {
    const ai = getGenAIInstance();
    const systemInstructionConst = `You are a technical designer. Your task is to create a detailed, non-visual, text-only blueprint for the primary object in the provided image.
    Describe the object's components, materials, textures, and shape from the front, side, and top views. Be precise and literal. Infer the other views based on the image provided.
    This description will be used by another AI to generate three separate, consistent orthographic images. Do not describe the background or lighting.
    Example response for an image of a coffee mug: "A ceramic coffee mug. Front view: C-shaped handle on the right in the front view. Side view: Handle is not visible. Top view: Circular rim with a dark interior."
    Respond ONLY with the blueprint description.`;

    const response = await generateContentWithRetry({
        model: primaryTextModel,
        contents: {
            parts: [
                { text: "Create a blueprint for the object in this image." },
                { inlineData: { data: dataUrlToBase64(sourceImageUrl), mimeType: 'image/jpeg' } },
            ]
        },
        config: {
            systemInstruction: systemInstructionConst
        }
    }, primaryTextModel, fallbackTextModel, onFallback);

    return (response.text || "").trim();
}


export async function describeImage(sourceImageUrl: string, settings: Pick<ApiSettings, 'primaryTextModel' | 'fallbackTextModel'>, onFallback: () => void): Promise<string> {
    const { primaryTextModel, fallbackTextModel } = settings;
    const mimeTypeMatch = sourceImageUrl.match(/data:(image\/[a-zA-Z]+);base64,/);
    if (!mimeTypeMatch) {
        throw new Error("Invalid source image format for description.");
    }
    
    const response = await generateContentWithRetry({
        model: primaryTextModel,
        contents: {
            parts: [
                { text: "Describe this image in detail. If there is text, transcribe it exactly." },
                { inlineData: { data: dataUrlToBase64(sourceImageUrl), mimeType: mimeTypeMatch[1] } }
            ]
        }
    }, primaryTextModel, fallbackTextModel, onFallback);
    return response.text || '';
}

export async function transcribeAudio(sourceAudioUrl: string): Promise<string> {
    await new Promise(res => setTimeout(res, 1000)); 
    return "This is a placeholder transcription. The full functionality would require a dedicated speech-to-text service.";
}

export async function generateSfxFromAudio(sourceAudioUrl: string, prompt: string, model: string): Promise<string> {
    await new Promise(res => setTimeout(res, 2000));
    return generateAudioFromText(prompt || "abstract sound", model);
}

export async function generateMusicFromText(prompt: string, model: string): Promise<string> {
    const text = prompt;
    if (typeof text !== 'string') {
        console.warn('generateMusicFromText received non-string prompt, returning calm music.');
        return calmMusic;
    }
    const keywords = text.toLowerCase();
    if (keywords.includes('action') || keywords.includes('fight') || keywords.includes('battle')) {
      return actionMusic;
    }
    if (keywords.includes('epic') || keywords.includes('heroic') || keywords.includes('triumphant')) {
      return epicMusic;
    }
    if (keywords.includes('suspense') || keywords.includes('tense') || keywords.includes('danger')) {
      return suspenseMusic;
    }
    if (keywords.includes('horror') || keywords.includes('scary') || keywords.includes('eerie')) {
      return horrorMusic;
    }
    if (keywords.includes('sad') || keywords.includes('somber') || keywords.includes('melancholy')) {
      return sadMusic;
    }
    if (keywords.includes('mysterious') || keywords.includes('wonder') || keywords.includes('magic')) {
      return mysteriousMusic;
    }
    return calmMusic;
}

export async function generateMusicFromAudio(sourceAudioUrl: string, prompt: string, model: string): Promise<string> {
    // For the simulated engine, we'll just use the text prompt, same as generateMusicFromText.
    await new Promise(res => setTimeout(res, 2000)); // Simulate processing time
    return generateMusicFromText(prompt, model);
}