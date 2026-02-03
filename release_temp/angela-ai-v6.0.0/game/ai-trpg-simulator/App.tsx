import React, { useState, Suspense, lazy, useReducer, useCallback, useRef, useMemo, useEffect } from 'react';
import { I18nProvider } from './context/i18n';
import { SettingsProvider, useSettings } from './context/settings';
import { ApiKeyProvider } from './context/apiKey';
import { CodexProvider, useCodex } from './context/codex';
import Header, { Tool } from './components/Header';
import SettingsModal from './components/SettingsModal';
import ToastComponent from './components/Toast';
import { Toast, CodexAsset, GameState, GamePhase, PlayerAction, Task, GeneratePortraitTask, PlayerActionTask, GenerateTtsTask, ApiSettings, CodexSaveAsset, GeneratePlayerAutoActionTask, Character, GlobalCodex, GenerateActionSuggestionsTask, GenerateSfxTask } from './types';
import { LoadingSpinner, RefreshIcon } from './components/icons';
import { useI18n } from './context/i18n';
import { useApiErrorHandler, createWavBlob, blobToBase64, decode, decodeAudioData } from './services/utils';
import { addTask, subscribe, clearTasks } from './services/taskQueueService';
import VeoModal from './components/VeoModal';
import { rootReducer, initialGameState } from './reducers';
import { produce } from 'immer';
import { GameProvider } from './components/context/GameContext';
import { reconstructGameState } from './services/gameStateService';
import SummoningQTE from './components/SummoningQTE';

// Lazy load the main tool components
const AdventureForge = lazy(() => import('./components/TrpgGame'));
const CodexScreen = lazy(() => import('./components/CodexScreen'));
const CreativeHub = lazy(() => import('./components/CreativeHub'));
const ModelingTool = lazy(() => import('./components/ModelingTool'));

// --- AUDIO HOOK (Moved into AppContent to access state) ---
const useAudioEngine = (bgmVolume: number, sfxVolume: number, enableTts: boolean, addToast: (message: string, type: Toast['type']) => void, parseApiError: (e: unknown, context?: 'init' | 'turn' | 'load' | 'generic') => string) => {
    const [currentMood, setCurrentMood] = useState('Default');
    const [playingMessageKey, setPlayingMessageKey] = useState<string | null>(null);

    const audioContextRef = useRef<AudioContext | null>(null);
    const musicSourceRef = useRef<AudioBufferSourceNode | null>(null);
    const musicGainRef = useRef<GainNode | null>(null);
    const audioBufferCacheRef = useRef<Record<string, Promise<AudioBuffer>>>({});
    
    const ttsAudioContextRef = useRef<AudioContext | null>(null);
    const ttsAudioSourceRef = useRef<AudioBufferSourceNode | null>(null);
    const ttsAudioBufferCacheRef = useRef<Record<string, AudioBuffer>>({});
    const { codex, addCodexEntry } = useCodex();

    const getAudioContext = useCallback(() => {
        if (!audioContextRef.current) audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
        return audioContextRef.current;
    }, []);

    const getTtsAudioContext = useCallback(() => {
        if (!ttsAudioContextRef.current) ttsAudioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
        return ttsAudioContextRef.current;
    }, []);

    const getAudioBuffer = useCallback(async (name: string, dataUri: string): Promise<AudioBuffer> => {
        if (audioBufferCacheRef.current[name]) return audioBufferCacheRef.current[name];
        const promise = (async () => {
            try {
                const audioCtx = getAudioContext();
                const response = await fetch(dataUri);
                const arrayBuffer = await response.arrayBuffer();
                return await audioCtx.decodeAudioData(arrayBuffer);
            } catch (e) {
                console.error(`Failed to decode audio '${name}':`, e);
                delete audioBufferCacheRef.current[name];
                throw e;
            }
        })();
        audioBufferCacheRef.current[name] = promise;
        return promise;
    }, [getAudioContext]);
      
    const changeMusicByMood = useCallback(async (mood: string) => {
        if (mood === currentMood) return;
        
        const assetId = `${mood.toLowerCase()}music`;
        const musicAsset = codex.audio[assetId];
        
        const audioCtx = getAudioContext();
        if (!musicGainRef.current) {
            musicGainRef.current = audioCtx.createGain();
            musicGainRef.current.connect(audioCtx.destination);
        }
        musicGainRef.current.gain.setValueAtTime(bgmVolume, audioCtx.currentTime);
        setCurrentMood(mood);
        if (musicSourceRef.current) { musicSourceRef.current.stop(); musicSourceRef.current = null; }

        const musicData = musicAsset?.url;
        if (musicData && bgmVolume > 0) {
            try {
                const buffer = await getAudioBuffer(`bgm-${assetId}`, musicData);
                const source = audioCtx.createBufferSource();
                source.buffer = buffer;
                source.loop = true;
                source.connect(musicGainRef.current);
                source.start();
                musicSourceRef.current = source;
            } catch (e) { console.error(`Failed to play music for mood ${mood}`, e); }
        }
    }, [getAudioContext, getAudioBuffer, bgmVolume, currentMood, codex]);
      
    useEffect(() => {
        if (musicGainRef.current) {
            musicGainRef.current.gain.value = bgmVolume;
            if (bgmVolume > 0 && !musicSourceRef.current && currentMood !== 'Default') {
                changeMusicByMood(currentMood);
            } else if (bgmVolume === 0 && musicSourceRef.current) {
                 musicSourceRef.current.stop();
                 musicSourceRef.current = null;
            }
        }
    }, [bgmVolume, currentMood, changeMusicByMood]);
    
    const stopTts = useCallback(() => {
        if (ttsAudioSourceRef.current) { ttsAudioSourceRef.current.stop(); ttsAudioSourceRef.current.disconnect(); ttsAudioSourceRef.current = null; }
        setPlayingMessageKey(null);
    }, []);

    const stopAllAudio = useCallback(() => {
        stopTts();
        if (musicSourceRef.current) {
            musicSourceRef.current.stop();
            musicSourceRef.current = null;
        }
        setCurrentMood('Default');
    }, [stopTts]);

    const handlePlayTtsRequest = useCallback(async (message: any, character: Character | undefined, model: string) => {
        if (!enableTts) return;
        const messageId = message.id;
        if (playingMessageKey === messageId) { stopTts(); return; }
        stopTts();
        setPlayingMessageKey(messageId + '-loading');

        if (ttsAudioBufferCacheRef.current[messageId]) {
            try {
                const audioCtx = getTtsAudioContext();
                const source = audioCtx.createBufferSource();
                source.buffer = ttsAudioBufferCacheRef.current[messageId];
                source.connect(audioCtx.destination);
                source.onended = stopTts;
                source.start(0);
                ttsAudioSourceRef.current = source;
                setPlayingMessageKey(messageId);
            } catch (e) { console.error("Error playing cached TTS", e); stopTts(); }
            return;
        }

        if (!model) {
            addToast('TTS model not configured in settings.', 'error');
            stopTts();
            return;
        }

        const task: GenerateTtsTask = {
            type: 'generate-tts', id: `task-tts-${messageId}`, description: `TTS: ${message.author}`, status: 'queued', priority: 25, message, character, model,
            onSuccess: async ({ base64Audio }) => {
                const textToPlay = message.dialogue || message.content;
                const decodedData = decode(base64Audio);
                try {
                    const wavBlob = createWavBlob(decodedData, 24000, 1, 16);
                    const dataUrl = await blobToBase64(wavBlob);
                    await addCodexEntry({ id: `tts-${message.id}`, type: 'audio', name: textToPlay, description: `TTS for ${message.author}.`, url: dataUrl });
                } catch (e) { console.error("Failed to create WAV for codex", e); }
    
                try {
                    const audioCtx = getTtsAudioContext();
                    const buffer = await decodeAudioData(decodedData, audioCtx, 24000, 1);
                    ttsAudioBufferCacheRef.current[messageId] = buffer;
                    const source = audioCtx.createBufferSource();
                    source.buffer = buffer;
                    source.connect(audioCtx.destination);
                    source.onended = stopTts;
                    source.start(0);
                    ttsAudioSourceRef.current = source;
                    setPlayingMessageKey(messageId);
                } catch(e) { console.error("Error decoding/playing TTS", e); stopTts(); }
            },
            onError: (error) => { addToast(parseApiError(error, 'generic'), 'error'); stopTts(); }
        };
        addTask(task);
    }, [enableTts, playingMessageKey, stopTts, getTtsAudioContext, addToast, parseApiError, addCodexEntry]);

    return { changeMusicByMood, handlePlayTtsRequest, playingMessageKey, stopAllAudio };
};

const AppLoader: React.FC = () => {
    const { t } = useI18n();
    return (
        <div className="flex-1 flex items-center justify-center bg-gray-900">
            <div className="text-center">
                <LoadingSpinner />
                <p className="mt-4 text-gray-400">{t('codex.loading')}</p>
            </div>
        </div>
    );
};

const AppContent: React.FC = () => {
  const [activeTool, setActiveTool] = useState<Tool>('adventureForge');
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [assetToSend, setAssetToSend] = useState<CodexAsset | null>(null);
  
  const settings = useSettings();
  const [gameState, dispatch] = useReducer(rootReducer, {
    ...initialGameState,
    locale: settings.locale, 
    isTtsEnabled: settings.enableTts, 
  });
  const [videoRequest, setVideoRequest] = useState<{ messageId: string, prompt: string } | null>(null);
  const [summonChallenge, setSummonChallenge] = useState<{ sequence: string[]; timeLimit: number; originalAction: string } | null>(null);
  
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isTaskQueueBusy, setIsTaskQueueBusy] = useState(false);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);
  const autoPlayIntervalRef = useRef<number | null>(null);
  const isAutoPlayingRef = useRef(isAutoPlaying);
  useEffect(() => { isAutoPlayingRef.current = isAutoPlaying; }, [isAutoPlaying]);
  
  const { t, locale } = useI18n();
  // @fix: Destructure `addCodexEntry` from useCodex to make it available in this component's scope.
  const { codex, addCodexEntry, importFromFile, saveGame, reconstructSaveAsset, rehydrateGameStateFromCodex, isLoading: isCodexLoading } = useCodex();
  const { parseApiError } = useApiErrorHandler();
  const processedLogCount = useRef(0);
  const previousGameStateRef = useRef<GameState | null>(null);
  
  const isBusy = useMemo(() => isTaskQueueBusy || isCodexLoading, [isTaskQueueBusy, isCodexLoading]);
  
  const addToast = useCallback((message: string, type: Toast['type'] = 'info') => {
      const newToast: Toast = { id: Date.now(), message, type };
      setToasts(currentToasts => [...currentToasts, newToast]);
  }, []);

  const { changeMusicByMood, handlePlayTtsRequest, playingMessageKey, stopAllAudio } = useAudioEngine(settings.bgmVolume, settings.sfxVolume, settings.enableTts, addToast, parseApiError);

  useEffect(() => {
    const unsubscribe = subscribe((busy, taskList) => {
        setIsTaskQueueBusy(busy);
        setTasks(taskList);
    });
    return unsubscribe;
  }, []);
  
  const handleFallback = useCallback(() => {
    if (!gameState.isFallbackActive) {
      addToast(t('service.fallbackMessage'), 'info');
      dispatch({ type: 'SET_FALLBACK_STATUS', payload: true });
    }
  }, [gameState.isFallbackActive, addToast, t]);
  
  const generateSuggestionsIfNeeded = useCallback((currentState: GameState) => {
    const task: GenerateActionSuggestionsTask = {
        type: 'generate-action-suggestions',
        id: `task-suggest-fallback-${Date.now()}`,
        description: 'Generating suggestions...',
        status: 'queued',
        priority: 2,
        gameLog: currentState.gameLog,
        locale: locale,
        settings: { primaryTextModel: settings.primaryTextModel, fallbackTextModel: settings.fallbackTextModel },
        onFallback: handleFallback,
        onSuccess: (result) => {
            dispatch({ type: 'SET_SUGGESTED_ACTIONS', payload: result.suggestedActions });
        },
        onError: (e) => addToast(parseApiError(e, 'turn'), 'error')
    };
    addTask(task);
  }, [locale, settings.primaryTextModel, settings.fallbackTextModel, handleFallback, addToast, parseApiError]);

  const handleCinematicGenerationComplete = useCallback((messageId: string, url: string, type: 'image' | 'video') => {
    const assetKey = `cinematic-${messageId}`;
    const dataUrl = type === 'image' ? `data:image/jpeg;base64,${url}` : `data:video/mp4;base64,${url}`;
    dispatch({ type: 'UPDATE_CINEMATIC_STATUS', payload: { messageId, status: 'done', assetKey, url: dataUrl }});
  }, []);
  
  const handleCinematicGenerationError = useCallback((messageId: string) => dispatch({ type: 'UPDATE_CINEMATIC_STATUS', payload: { messageId, status: 'error' }}), []);
  
  const handleGameStart = useCallback((newGameState: GameState) => {
    stopAllAudio();
    clearTasks();
    setIsAutoPlaying(false);
    processedLogCount.current = 0;
    
    // Explicitly set the phase and tool
    const stateWithPhase = produce(newGameState, draft => {
        draft.gamePhase = GamePhase.PLAYING;
    });
    dispatch({ type: 'START_GAME', payload: { gameState: stateWithPhase } });
    setActiveTool('adventureForge');

    if (!newGameState.suggestedActions || newGameState.suggestedActions.length === 0) {
        generateSuggestionsIfNeeded(newGameState);
    }
  }, [generateSuggestionsIfNeeded, stopAllAudio]);
  
 const handleSaveGame = useCallback(async () => {
    const saveName = window.prompt(t('game.saveModal.prompt'), `${t('game.saveModal.defaultName')} - ${new Date().toLocaleString()}`);
    if (saveName) {
        try {
            await saveGame(gameState, saveName);
            addToast(t('game.saveModal.success', { name: saveName }), 'success');
        } catch (e: any) {
            const errorMessage = e instanceof Error ? e.message : String(e);
            addToast(`${t('game.saveFailed')}: ${errorMessage}`, 'error');
            console.error("Save failed:", e);
        }
    }
}, [t, addToast, gameState, saveGame]);
  
  const handleImportFileToCodex = useCallback(async (file: File) => {
    try {
        const count = await importFromFile(file);
        addToast(t('codex.importSuccess', { count }), 'success');
    } catch (e) {
        addToast(parseApiError(e, 'load'), 'error');
        console.error("Failed to import from file:", e);
    }
  }, [addToast, t, importFromFile, parseApiError]);

  const handleLoadFromCodex = useCallback((asset: CodexAsset) => {
    if (asset.type !== 'save') return;

    // Check for old format and warn user
    const isOldFormat = JSON.stringify((asset as CodexSaveAsset).gameState).includes('"imageUrl"');
    if (isOldFormat) {
        if (!window.confirm("This save appears to be from an old version and may not load correctly. It's recommended to use the 'Reconstruct' feature in the Codex first. Continue loading anyway?")) {
            return;
        }
    }

    if (window.confirm(t('game.loadConfirm.codexMessage', { name: asset.name }))) {
        try {
            const savedGameState = (asset as CodexSaveAsset).gameState;
            const reconstructedState = reconstructGameState(savedGameState, initialGameState);
            const rehydratedState = rehydrateGameStateFromCodex(reconstructedState);
            
            handleGameStart(rehydratedState);
            addToast(t('game.loadConfirm.codexSuccess', { name: asset.name }), 'success');
        } catch (e) {
            addToast(parseApiError(e, 'load'), 'error');
            console.error("Failed to load from codex:", e);
        }
    }
  }, [t, addToast, handleGameStart, rehydrateGameStateFromCodex, parseApiError]);

  const handleReconstructSave = useCallback(async (saveAssetId: string) => {
    try {
        await reconstructSaveAsset(saveAssetId);
        addToast('Save reconstructed successfully! A new version has been added to your saves.', 'success');
    } catch (e) {
        addToast('Failed to reconstruct save.', 'error');
        console.error("Reconstruction failed:", e);
    }
  }, [reconstructSaveAsset, addToast]);

  const handleRestartGame = useCallback(() => {
    if (window.confirm(t('game.restartConfirm.message'))) {
      stopAllAudio();
      clearTasks();
      setIsAutoPlaying(false);
      processedLogCount.current = 0;
      dispatch({ type: 'RESTART_GAME' });
      // Go back to the main setup screen view
      // This state is managed inside SetupScreen, but we can trigger a reset by changing the tool
      setActiveTool('adventureForge');
      // A slightly hacky way to ensure SetupScreen re-renders to its initial state
      setTimeout(() => setActiveTool('adventureForge'), 0);
    }
  }, [t, stopAllAudio]);
  
  const handleGeneratePortrait = useCallback((characterName: string) => {
    const character = gameState.characters.find(c => c.name === characterName);
    if (!character || gameState.isFallbackActive) return;
    const assetKey = `portrait-${characterName}`;
    dispatch({ type: 'UPDATE_CHARACTER_PORTRAIT_STATUS', payload: { charName: characterName, status: 'queued', assetKey } });
    const task: GeneratePortraitTask = {
      type: 'generate-portrait',
      id: `task-portrait-${characterName}-${Date.now()}`,
      description: `Generating portrait for ${characterName}`,
      status: 'queued',
      priority: 30,
      character,
      prompt: t('service.imagePrompt.character', { description: character.description }),
      model: settings.imageModel,
      onSuccess: (url) => dispatch({ type: 'UPDATE_CHARACTER_PORTRAIT_STATUS', payload: { charName: characterName, status: 'done', imageUrl: `data:image/jpeg;base64,${url}`, assetKey } }),
      onError: (e) => { addToast(parseApiError(e, 'generic'), 'error'); dispatch({ type: 'UPDATE_CHARACTER_PORTRAIT_STATUS', payload: { charName: characterName, status: 'error', assetKey }}); }
    };
    addTask(task);
  }, [gameState, settings.imageModel, t, addToast, parseApiError]);
  
    const handlePlayerAction = useCallback((action: PlayerAction, attachedAsset: CodexAsset | null) => {
    if (isBusy || gameState.gamePhase !== GamePhase.PLAYING) return;
    const currentPlayerCharacter = gameState.characters.find(c => !c.isAI);
    if (!currentPlayerCharacter) return;
  
    previousGameStateRef.current = gameState;
  
    dispatch({ type: 'ADD_PLAYER_MESSAGE_TO_LOG', payload: { action: action, author: currentPlayerCharacter.name } });
    dispatch({ type: 'SET_SUGGESTED_ACTIONS', payload: [] });
  
    const apiSettings: ApiSettings = { primaryTextModel: settings.primaryTextModel, fallbackTextModel: settings.fallbackTextModel, imageModel: settings.imageModel, imageEditModel: settings.imageEditModel, videoModel: settings.videoModel, sfxModel: settings.sfxModel, ttsModel: settings.ttsModel, musicModel: settings.musicModel, enableItemIcons: settings.enableItemIcons, enablePortraits: settings.enablePortraits, enableMapImages: settings.enableMapImages, enableLocationImages: settings.enableLocationImages, enableSfx: settings.enableSfx, qteDifficulty: settings.qteDifficulty, disableQteTimer: settings.disableQteTimer, roundRobinInitiative: settings.roundRobinInitiative, characterAgency: settings.characterAgency, aiCreativity: settings.aiCreativity };
    
    const nextState = rootReducer(gameState, { type: 'ADD_PLAYER_MESSAGE_TO_LOG', payload: { action: action, author: currentPlayerCharacter.name } });

    const task: PlayerActionTask = {
      type: 'player-action',
      id: `task-action-${Date.now()}`,
      description: t('game.playerTurn'),
      status: 'queued',
      priority: 1,
      action,
      gameState: nextState,
      attachedAsset: attachedAsset || undefined,
      settings: apiSettings,
      onFallback: handleFallback,
      onSuccess: (result) => {
          previousGameStateRef.current = null;
          const { turnResult, ...cognitiveState } = result;
          
          dispatch({ type: 'UPDATE_COGNITIVE_STATE', payload: cognitiveState });
          dispatch({ type: 'PROCESS_AI_RESPONSE', payload: { result: turnResult, gmName: t('game.gameMaster'), settings: { roundRobinInitiative: settings.roundRobinInitiative, characterAgency: settings.characterAgency } } });

          if (turnResult.summonChallenge) {
              setSummonChallenge({ ...turnResult.summonChallenge, originalAction: (task as PlayerActionTask).action as string });
          }
          
          if (!turnResult.suggestedActions || turnResult.suggestedActions.length === 0) {
              dispatch((latestState: GameState) => {
                  generateSuggestionsIfNeeded(latestState);
                  return latestState; 
              });
          }
      },
      onError: (e) => {
        if (previousGameStateRef.current) {
            dispatch({ type: 'RESTORE_GAME_STATE', payload: previousGameStateRef.current });
            addToast(t('service.errorRollback'), 'error');
        } else {
            addToast(parseApiError(e, 'turn'), 'error');
        }
        dispatch((latestState: GameState) => {
            generateSuggestionsIfNeeded(latestState);
            return latestState;
        });
        previousGameStateRef.current = null;
      },
    };
    addTask(task);
  }, [isBusy, gameState, settings, handleFallback, t, addToast, parseApiError, generateSuggestionsIfNeeded]);

  useEffect(() => {
    if (gameState.gamePhase !== GamePhase.PLAYING || gameState.isFallbackActive || !settings.enableSfx) return;
    const newMessages = gameState.gameLog.slice(processedLogCount.current);
    if (newMessages.length === 0) return;
    const tasksToQueue: GenerateSfxTask[] = [];
    newMessages.forEach(msg => {
        const sfxTagRegex = /\[SFX:([^\]]+)\]/g;
        let match;
        while ((match = sfxTagRegex.exec(msg.content)) !== null) {
            const prompt = match[1].trim();
            if (prompt) {
                const assetKey = `sfx-${msg.id}`;
                dispatch({ type: 'UPDATE_SFX_STATUS', payload: { messageId: msg.id, status: 'queued', assetKey } });
                tasksToQueue.push({
                    type: 'generate-sfx', id: `task-sfx-${msg.id}-${Date.now()}`, description: t('setup.task.generateSfx', { prompt }), status: 'queued', priority: 35, messageId: msg.id, prompt: prompt, model: settings.sfxModel,
                    onSuccess: async (url) => {
                         const wavBlob = createWavBlob(decode(url), 24000, 1, 16);
                         const dataUrl = await blobToBase64(wavBlob);
                         await addCodexEntry({ id: assetKey, type: 'audio', name: prompt, description: `SFX from game log`, url: dataUrl });
                         dispatch({ type: 'UPDATE_SFX_STATUS', payload: { messageId: msg.id, status: 'done', url: dataUrl, assetKey } });
                    },
                    onError: (e) => {
                        addToast(parseApiError(e, 'generic'), 'error');
                        dispatch({ type: 'UPDATE_SFX_STATUS', payload: { messageId: msg.id, status: 'error', assetKey } });
                    }
                });
            }
        }
    });
    if (tasksToQueue.length > 0) addTask(tasksToQueue);
    processedLogCount.current = gameState.gameLog.length;
  }, [gameState.gameLog, settings.enableSfx, settings.sfxModel, addToast, parseApiError, t, addCodexEntry, gameState.gamePhase, gameState.isFallbackActive]);
  
  const handleToggleAutoPlay = useCallback(() => {
    setIsAutoPlaying(prev => {
        const nextState = !prev;
        addToast(nextState ? t('game.autoPlayStarted') : t('game.autoPlayStopped'), 'info');
        return nextState;
    });
  }, [addToast, t]);

  useEffect(() => {
    if (autoPlayIntervalRef.current) {
        clearInterval(autoPlayIntervalRef.current);
        autoPlayIntervalRef.current = null;
    }
    if (isAutoPlaying && !isBusy && gameState.gamePhase === GamePhase.PLAYING) {
        autoPlayIntervalRef.current = window.setInterval(() => {
            // Check ref inside interval to get the latest value
            if (!isAutoPlayingRef.current || isBusy) {
                 if (autoPlayIntervalRef.current) clearInterval(autoPlayIntervalRef.current);
                 return;
            }
            const task: GeneratePlayerAutoActionTask = {
                type: 'generate-player-auto-action', id: `task-auto-action-${Date.now()}`, description: t('setup.task.autoAction'), status: 'queued', priority: 5,
                gameState: gameState,
                settings: { primaryTextModel: settings.primaryTextModel, fallbackTextModel: settings.fallbackTextModel, aiCreativity: settings.aiCreativity, },
                onFallback: handleFallback,
                onSuccess: (action) => {
                    if (action && isAutoPlayingRef.current) {
                        handlePlayerAction(action, null);
                    }
                },
                onError: (e) => {
                    addToast(parseApiError(e, 'turn'), 'error');
                    setIsAutoPlaying(false);
                    addToast(t('game.autoPlayError'), 'error');
                }
            };
            addTask(task);
        }, 8000);
    }
    return () => { if (autoPlayIntervalRef.current) clearInterval(autoPlayIntervalRef.current); };
  }, [isAutoPlaying, isBusy, gameState, handlePlayerAction, addToast, parseApiError, settings, t, handleFallback]);


  const handleQteResolve = useCallback((qteResult: 'critical_failure' | 'failure' | 'success' | 'critical_success') => {
    if (!summonChallenge) return;
    const action = t(`summon.${qteResult}.resolutionAction`, { originalAction: summonChallenge.originalAction });
    setSummonChallenge(null);
    handlePlayerAction(action, null);
  }, [summonChallenge, handlePlayerAction, t]);

  const gameProviderValue = useMemo(() => ({
      gameState, dispatch, addToast, isBusy, tasks,
      onGameStart: handleGameStart,
      onImportFileToCodex: handleImportFileToCodex,
      onLoadFromCodex: handleLoadFromCodex,
      onReconstructSave: handleReconstructSave,
      onSaveGame: handleSaveGame,
      onRestartGame: handleRestartGame,
      onGeneratePortrait: handleGeneratePortrait,
      changeMusicByMood,
      onPlayTtsRequest: (messageId: string) => {
        const msg = gameState.gameLog.find(m => m.id === messageId);
        if (msg) {
            const character = gameState.characters.find(c => c.name === msg.author);
            handlePlayTtsRequest(msg, character, settings.ttsModel);
        }
      },
      playingMessageKey,
      onGenerateVideoClick: (messageId: string, prompt: string) => setVideoRequest({ messageId, prompt }),
      onPlayerAction: handlePlayerAction,
      onNavigateToCodex: () => setActiveTool('codex'),
      onToggleAutoPlay: handleToggleAutoPlay,
      isAutoPlaying: isAutoPlaying,
  }), [gameState, dispatch, addToast, isBusy, tasks, handleGameStart, handleImportFileToCodex, handleLoadFromCodex, handleReconstructSave, handleSaveGame, handleRestartGame, handleGeneratePortrait, changeMusicByMood, handlePlayTtsRequest, playingMessageKey, settings.ttsModel, handlePlayerAction, handleToggleAutoPlay, isAutoPlaying]);

  if(isCodexLoading) {
    return <AppLoader />;
  }

  return (
    <div className="bg-gray-900 text-gray-100 flex flex-col h-screen font-sans">
      <Header activeTool={activeTool} setActiveTool={setActiveTool} onOpenSettings={() => setIsSettingsModalOpen(true)} />

      {isSettingsModalOpen && <SettingsModal onClose={() => setIsSettingsModalOpen(false)} />}
      {videoRequest && <VeoModal request={videoRequest} onComplete={(url) => handleCinematicGenerationComplete(videoRequest.messageId, url, 'video')} onCancel={(e) => { handleCinematicGenerationError(videoRequest.messageId); addToast(parseApiError(e, 'generic')); }} />}
      {summonChallenge && <SummoningQTE challenge={summonChallenge} onResolve={handleQteResolve} disableTimer={settings.disableQteTimer} enableVoiceInput={settings.enableVoiceInput} />}

      <main className="flex-1 flex flex-col min-h-0">
          <GameProvider value={gameProviderValue}>
              <Suspense fallback={<AppLoader />}>
                {activeTool === 'adventureForge' && <AdventureForge />}
                {activeTool === 'creativeHub' && <CreativeHub addToast={addToast} onSendAssetToTool={setAssetToSend} initialAsset={assetToSend} onInitialAssetConsumed={() => setAssetToSend(null)} />}
                {activeTool === 'model' && <ModelingTool addToast={addToast} initialAsset={assetToSend} onInitialAssetConsumed={() => setAssetToSend(null)} />}
                {activeTool === 'codex' && <CodexScreen addToast={addToast} onSendAssetToTool={(asset, tool) => { setAssetToSend(asset); setActiveTool(tool); }} onLoadSave={handleLoadFromCodex} onImportFileToCodex={handleImportFileToCodex} onReconstructSave={handleReconstructSave} />}
              </Suspense>
          </GameProvider>
      </main>
      <div className="fixed top-4 right-4 z-[200] space-y-2">
        {toasts.map(toast => (
          <ToastComponent key={toast.id} {...toast} onDismiss={() => setToasts(current => current.filter(t => t.id !== toast.id))} />
        ))}
      </div>
    </div>
  );
};


const App: React.FC = () => (
  <SettingsProvider>
    <I18nProvider>
      <ApiKeyProvider>
        <CodexProvider>
          <AppContent />
        </CodexProvider>
      </ApiKeyProvider>
    </I18nProvider>
  </SettingsProvider>
);

export default App;
