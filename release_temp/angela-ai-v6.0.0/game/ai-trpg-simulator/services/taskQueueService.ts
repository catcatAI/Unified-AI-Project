import { Task, ApiSettings, GenerateSummaryTask } from '../types';
import * as geminiService from './geminiService';
import { takeTurn as cognitiveTakeTurn } from './cognitiveEngineService';
import { setupResponseSchema } from './promptService';


// --- State ---
let taskQueue: Task[] = [];
let isProcessing = false;
let activeTask: Task | null = null;

// --- Listener Pattern for UI updates ---
type Listener = (isBusy: boolean, tasks: Task[], activeTask: Task | null) => void;
let listeners: Listener[] = [];

const notify = () => {
    const isBusy = isProcessing || taskQueue.length > 0;
    const tasksCopy = [...taskQueue];
    const activeTaskCopy = activeTask ? {...activeTask} : null;
    listeners.forEach(l => l(isBusy, tasksCopy, activeTaskCopy));
};

export const subscribe = (listener: Listener): (() => void) => {
    listeners.push(listener);
    listener(isProcessing || taskQueue.length > 0, [...taskQueue], activeTask ? {...activeTask} : null);
    return () => {
        listeners = listeners.filter(l => l !== listener);
    };
};

export const clearTasks = () => {
    taskQueue = [];
    // isProcessing will naturally become false when the current loop finishes
    // No need to force it, as that could interrupt a running task.
    // The while loop in processQueue will simply terminate.
    notify();
};


// --- Queue Management ---
export const addTask = (task: Task | Task[]) => {
    const tasksToAdd = Array.isArray(task) ? task : [task];
    tasksToAdd.forEach(t => {
        const insertIndex = taskQueue.findIndex(existing => existing.priority > t.priority);
        if (insertIndex === -1) {
            taskQueue.push(t);
        } else {
            taskQueue.splice(insertIndex, 0, t);
        }
    });
    notify();
    processQueue();
};

const processQueue = async () => {
    if (isProcessing) return;
    isProcessing = true;

    while (taskQueue.length > 0) {
        const task = taskQueue.shift()!;
        activeTask = task;
        task.status = 'in-progress';
        notify();

        try {
            let result: any;
            switch (task.type) {
                case 'generate-setup': {
                    const fullSetupPrompt = `You are a creative and detailed Game Master setting up a new tabletop role-playing game.
Your response MUST be a single JSON object without any markdown formatting.

SETUP PARAMETERS:
- Game Style: ${task.gameStyle}
- Number of AI Companions: ${task.aiCount}
- Difficulty Settings: ${JSON.stringify(task.difficulty)}
- Language for response: ${task.locale}

CORE SCENARIO:
${task.prompt}

Your JSON response MUST contain: "playerCharacter", "aiCharacters", "openingScene", "gameSummary", "genreAndTone", "startingLocation", "suggestedActions".
Optionally include: "partyStash", "vehicles", "realEstate", "locationItems", "knownLocations", "mapImagePrompt", "locationImagePrompt", "map" (if sandbox style).
Characters need stats and inventory. Items need name, description, quantity.`;

                    const setupParams = {
                        model: task.settings.primaryTextModel,
                        contents: fullSetupPrompt,
                        config: {
                            temperature: task.temperature,
                            responseMimeType: "application/json",
                            responseSchema: setupResponseSchema
                        }
                    };
                    result = await geminiService.generateFullGameSetup(setupParams, task.settings, task.onFallback);
                    break;
                }
                case 'generate-summary':
                    result = await geminiService.generateSummary(task.textToSummarize, task.settings, task.onFallback);
                    break;
                case 'generate-scenario-suggestion':
                    result = await geminiService.generateScenarioSuggestion(task.currentPrompt, task.locale, task.settings.primaryTextModel, task.settings.fallbackTextModel, task.onFallback);
                    break;
                case 'generate-action-suggestions':
                    result = await geminiService.generateSuggestionsOnly(task.gameLog, task.locale, task.settings.primaryTextModel, task.settings.fallbackTextModel, task.onFallback);
                    break;
                 case 'generate-player-auto-action':
                    result = await geminiService.generatePlayerAutoAction(task.gameState, task.settings, task.onFallback);
                    break;
                case 'player-action':
                    result = await cognitiveTakeTurn(task.gameState, task.action, task.settings, task.onFallback, task.attachedAsset);
                    break;
                case 'generate-portrait':
                case 'generate-cinematic':
                case 'generate-map-image':
                case 'generate-location-image':
                case 'generate-icon': {
                    const aspectRatioForImage = (task.type === 'generate-cinematic' || task.type === 'generate-location-image') ? '16:9' : '1:1';
                    result = await geminiService.generateImage(task.prompt, aspectRatioForImage, task.model);
                    break;
                }
                case 'generate-image':
                    result = await geminiService.generateImage(task.prompt, task.aspectRatio, task.model, task.sourceImageUrl);
                    break;
                case 'generate-video':
                    result = await geminiService.generateVideo(task.prompt, task.model, task.sourceImageUrl, task.lastFrameUrl); // Pass lastFrameUrl
                    break;
                case 'generate-sfx':
                    result = await geminiService.generateAudioFromText(task.prompt, task.model);
                    break;
                case 'generate-tts': {
                    let gender: 'male' | 'female' | 'other' | 'gm' = 'gm';
                    if (!task.message.isGM && task.character) gender = task.character.gender || 'other';
                    const textToPlay = task.message.dialogue ?? task.message.content ?? '';
                    const base64Audio = await geminiService.generateSpeech(textToPlay, gender, task.model);
                    result = { messageId: task.message.id, base64Audio };
                    break;
                }
                case 'load-game':
                    const savedData = JSON.parse(task.fileContent);
                    result = { gameState: savedData.gameState };
                    break;
                case 'generate-three-view': {
                    const { primaryTextModel, fallbackTextModel, imageModel } = task.settings;
                    
                    const blueprint = await geminiService.generateObjectBlueprint(task.prompt, primaryTextModel, fallbackTextModel, task.onFallback);
                    task.onBlueprintGenerated?.(blueprint);

                    const frontViewUrl = await geminiService.generateImage(`Front view of: ${blueprint}`, '1:1', imageModel);
                    task.onViewGenerated?.('front', frontViewUrl);

                    const sideViewUrl = await geminiService.generateImage(`Side view of: ${blueprint}`, '1:1', imageModel);
                    task.onViewGenerated?.('side', sideViewUrl);
                    
                    const topViewUrl = await geminiService.generateImage(`Top view of: ${blueprint}`, '1:1', imageModel);
                    task.onViewGenerated?.('top', topViewUrl);
                    
                    result = { frontViewUrl, sideViewUrl, topViewUrl };
                    break;
                }
                case 'refine-three-view': {
                    const { primaryTextModel, fallbackTextModel, imageModel } = task.settings;

                    const blueprint = await geminiService.refineBlueprintFromImages(task.prompt, task.frontViewUrl, task.sideViewUrl, task.topViewUrl, primaryTextModel, fallbackTextModel, task.onFallback);
                    task.onBlueprintGenerated?.(blueprint);

                    const frontViewUrl = await geminiService.generateImage(`Front view of: ${blueprint}`, '1:1', imageModel);
                    task.onViewGenerated?.('front', frontViewUrl);

                    const sideViewUrl = await geminiService.generateImage(`Side view of: ${blueprint}`, '1:1', imageModel);
                    task.onViewGenerated?.('side', sideViewUrl);

                    const topViewUrl = await geminiService.generateImage(`Top view of: ${blueprint}`, '1:1', imageModel);
                    task.onViewGenerated?.('top', topViewUrl);

                    result = { frontViewUrl, sideViewUrl, topViewUrl };
                    break;
                }
                case 'generate-three-view-from-image': {
                    const { primaryTextModel, fallbackTextModel, imageModel } = task.settings;

                    const blueprint = await geminiService.generateObjectBlueprintFromImage(task.sourceImageUrl, primaryTextModel, fallbackTextModel, task.onFallback);
                    task.onBlueprintGenerated?.(blueprint);

                    const frontPrompt = `Front view of: ${blueprint}`;
                    const sidePrompt = `Side view of: ${blueprint}`;
                    const topPrompt = `Top view of: ${blueprint}`;

                    const frontViewUrl = await geminiService.generateImage(frontPrompt, '1:1', imageModel);
                    task.onViewGenerated?.('front', frontViewUrl);

                    const sideViewUrl = await geminiService.generateImage(sidePrompt, '1:1', imageModel);
                    task.onViewGenerated?.('side', sideViewUrl);

                    const topViewUrl = await geminiService.generateImage(topPrompt, '1:1', imageModel);
                    task.onViewGenerated?.('top', topViewUrl);

                    result = { frontViewUrl, sideViewUrl, topViewUrl };
                    break;
                }
                case 'describe-image':
                    result = await geminiService.describeImage(task.sourceImageUrl, task.settings, task.onFallback);
                    break;
                case 'transcribe-audio':
                    result = await geminiService.transcribeAudio(task.sourceAudioUrl);
                    break;
                case 'generate-sfx-from-audio':
                    result = await geminiService.generateSfxFromAudio(task.sourceAudioUrl, task.prompt, task.model);
                    break;
                case 'generate-music-from-text':
                    result = await geminiService.generateMusicFromText(task.prompt, task.model);
                    break;
                case 'generate-music-from-audio':
                    result = await geminiService.generateMusicFromAudio(task.sourceAudioUrl, task.prompt, task.model);
                    break;
            }
            task.onSuccess?.(result);
        } catch (error) {
            task.onError?.(error as Error);
        } finally {
            activeTask = null;
            notify();
        }
    }

    isProcessing = false;
    notify();
};