import React, { useRef, useState, useCallback, useEffect, useReducer } from 'react';
import { LoadingSpinner, SmallLoadingSpinner, RefreshIcon, UserIcon, ImageIcon, PaperclipIcon, CloseIcon, UploadIcon, BookIcon, SaveIcon } from './icons';
import { useI18n } from '../context/i18n';
import { useSettings } from '../context/settings';
import { worldviews, stories, characters } from '../presets';
import { Character, Item, Vehicle, CharacterStats, Toast, DifficultySettings, RealEstate, Task, GenerateSetupTask, CodexAsset, PortraitStatus, ApiSettings, GameState, GamePhase, GameStyle, GenerateSummaryTask, GenerateMapImageTask, GenerateLocationImageTask, CodexSaveAsset } from '../types';
import { useApiErrorHandler } from '../services/utils';
import { addTask, subscribe } from '../services/taskQueueService';
import AssetPickerModal from './AssetPickerModal';
import { useGameContext } from './context/GameContext';
import { useCodex } from '../context/codex';

export interface SetupScreenProps {
  onStartAdventure: () => void;
}

// Simplified state for the form UI only
interface FormState {
  worldviewPrompt: string;
  storyPrompt: string;
  characterPrompt: string;
  gameStyle: GameStyle;
  aiCount: number;
  difficulty: DifficultySettings;
  selectedWorldview: string;
  selectedStory: string;
  selectedCharacter: string;
  playerCodexAsset: CodexAsset | null;
  aiCodexAssets: (CodexAsset | null)[];
}

type FormAction =
  | { type: 'SET_FIELD'; field: keyof FormState; value: any }
  | { type: 'SET_DIFFICULTY'; payload: Partial<Omit<DifficultySettings, 'preset'>> }
  | { type: 'SET_DIFFICULTY_PRESET'; preset: DifficultySettings['preset'] }
  | { type: 'SET_AI_CODEX_ASSET'; payload: { index: number; asset: CodexAsset | null } };

const defaultDifficulty: DifficultySettings = {
    preset: 'normal',
    showAiParty: true,
    enableVehicles: true,
    enableRealEstate: false,
    followPlot: true,
};

const getInitialFormState = (settings: any): FormState => ({
  worldviewPrompt: '',
  storyPrompt: '',
  characterPrompt: '',
  gameStyle: 'narrative',
  aiCount: 2,
  difficulty: { ...defaultDifficulty, followPlot: settings.followPlot },
  selectedWorldview: 'cyberpunk',
  selectedStory: 'soul-tuner',
  selectedCharacter: 'zero',
  playerCodexAsset: null,
  aiCodexAssets: [null, null, null, null],
});

const formReducer = (state: FormState, action: FormAction): FormState => {
  switch (action.type) {
    case 'SET_FIELD':
      return { ...state, [action.field]: action.value };
    case 'SET_DIFFICULTY': return { ...state, difficulty: { ...state.difficulty, ...action.payload, preset: 'custom' } };
    case 'SET_DIFFICULTY_PRESET': {
        const preset = action.preset;
        let newSettings: Partial<Omit<DifficultySettings, 'preset'>> = {};
        switch(preset) {
            case 'easy': newSettings = { showAiParty: true, enableVehicles: true, enableRealEstate: true, followPlot: true }; break;
            case 'normal': newSettings = { showAiParty: true, enableVehicles: true, enableRealEstate: false, followPlot: true }; break;
            case 'hard': newSettings = { showAiParty: false, enableVehicles: false, enableRealEstate: false, followPlot: false }; break;
            case 'custom': return { ...state, difficulty: { ...state.difficulty, preset: 'custom' } };
        }
        return { ...state, difficulty: { ...state.difficulty, ...newSettings, preset } };
    }
    case 'SET_AI_CODEX_ASSET': {
        const newAssets = [...state.aiCodexAssets];
        newAssets[action.payload.index] = action.payload.asset;
        return { ...state, aiCodexAssets: newAssets };
    }
    default:
      return state;
  }
};

const ensureArray = (value: any) => Array.isArray(value) ? value : [];

const sanitizeStats = (stats: any): CharacterStats => {
    const defaultStats: CharacterStats = { maxHp: 100, hp: 100, maxMp: 50, mp: 50, maxStamina: 100, stamina: 100, strength: 10, agility: 10, intelligence: 10, maxM3LogicStress: 10, m3LogicStress: 0, maxM6SecurityShield: 10, m6SecurityShield: 10 };
    if (!stats || typeof stats !== 'object' || Object.keys(stats).length === 0) {
        return defaultStats;
    }
    const mergedStats = { ...defaultStats, ...stats };
    mergedStats.maxHp = Number(mergedStats.maxHp) || defaultStats.maxHp;
    mergedStats.hp = Math.min(Number(mergedStats.hp) || mergedStats.maxHp, mergedStats.maxHp);
    mergedStats.maxMp = Number(mergedStats.maxMp) || defaultStats.maxMp;
    mergedStats.mp = Math.min(Number(mergedStats.mp) || mergedStats.maxMp, mergedStats.maxMp);
    mergedStats.maxStamina = Number(mergedStats.maxStamina) || defaultStats.maxStamina;
    mergedStats.stamina = Math.min(Number(mergedStats.stamina) || mergedStats.maxStamina, mergedStats.maxStamina);
    mergedStats.strength = Number(mergedStats.strength) || defaultStats.strength;
    mergedStats.agility = Number(mergedStats.agility) || defaultStats.agility;
    mergedStats.intelligence = Number(mergedStats.intelligence) || defaultStats.intelligence;
    return mergedStats;
};


const ensureItemIds = <T extends Partial<Item>>(items: any): (T & { id: string })[] => {
    if (!Array.isArray(items)) return [];
    return items
        .filter(item => item && typeof item === 'object' && item.name)
        .map(item => ({
            ...item,
            id: item.id || `item-init-${Math.random().toString(36).substr(2, 9)}`,
            name: String(item.name || 'Unknown Item'),
            description: String(item.description || 'No description available.'),
            quantity: typeof item.quantity === 'number' && item.quantity > 0 ? item.quantity : 1,
        })) as (T & { id: string })[];
};

export const SetupScreen: React.FC<SetupScreenProps> = ({ onStartAdventure }) => {
  const { t, locale } = useI18n();
  const settings = useSettings();
  const { gameState: currentGameState, dispatch: globalDispatch, addToast, onImportFileToCodex, onLoadFromCodex, isBusy } = useGameContext();
  const { codex } = useCodex();
  const [formState, formDispatch] = useReducer(formReducer, getInitialFormState(settings));
  
  const { parseApiError } = useApiErrorHandler();
  
  const [step, setStep] = useState<'form' | 'generating' | 'review' | 'error'>('form');
  const [view, setView] = useState<'start' | 'new' | 'load'>('start');
  const [error, setError] = useState<string|null>(null);
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const [isFallbackActive, setIsFallbackActive] = useState(false);

  const [isPickerOpen, setIsPickerOpen] = useState(false);
  const [pickerTarget, setPickerTarget] = useState<'player' | number | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFallback = useCallback(() => {
    if (!isFallbackActive) {
      addToast(t('service.fallbackMessage'), 'info');
      setIsFallbackActive(true);
      globalDispatch({ type: 'SET_FALLBACK_STATUS', payload: true });
    }
  }, [isFallbackActive, addToast, t, globalDispatch]);
  
  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      await onImportFileToCodex(file);
      if (event.target) {
        event.target.value = '';
      }
    }
  };
  
  const handleLoadFromCodexSelect = (asset: CodexAsset) => {
    if (asset.type === 'save') {
        onLoadFromCodex(asset as CodexSaveAsset);
    }
    setIsPickerOpen(false);
  };

  useEffect(() => {
    const initPrompts = () => {
        if (formState.selectedWorldview !== 'custom') {
            const worldviewPreset = worldviews.find(w => w.id === formState.selectedWorldview);
            if (worldviewPreset) formDispatch({ type: 'SET_FIELD', field: 'worldviewPrompt', value: t(worldviewPreset.descriptionKey) });
        }
        if (formState.selectedStory !== 'custom') {
            const storyPreset = stories.find(s => s.id === formState.selectedStory);
            if (storyPreset) formDispatch({ type: 'SET_FIELD', field: 'storyPrompt', value: t(storyPreset.descriptionKey) });
        }
        if (formState.selectedCharacter !== 'custom') {
            const characterPreset = characters.find(c => c.id === formState.selectedCharacter);
            if (characterPreset) formDispatch({ type: 'SET_FIELD', field: 'characterPrompt', value: t(characterPreset.descriptionKey) });
        }
    };
    initPrompts();
  }, [t, locale, formState.selectedWorldview, formState.selectedStory, formState.selectedCharacter]);

  useEffect(() => {
    const unsubscribe = subscribe((_, __, active) => {
        setActiveTask(active);
    });
    return unsubscribe;
  }, []);
  
  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>, type: 'worldview' | 'story' | 'character') => {
    const value = e.target.value;
    const selectedField = `selected${type.charAt(0).toUpperCase() + type.slice(1)}`;
    const promptField = `${type}Prompt`;
    formDispatch({ type: 'SET_FIELD', field: selectedField, value });
    
    if (type === 'character') {
      formDispatch({ type: 'SET_FIELD', field: 'playerCodexAsset', value: null });
    }

    if (value !== 'custom') {
        const presets = { worldview: worldviews, story: stories, character: characters }[type];
        const preset = presets.find(p => p.id === value);
        if (preset) formDispatch({ type: 'SET_FIELD', field: promptField, value: t(preset.descriptionKey) });
    } else {
        formDispatch({ type: 'SET_FIELD', field: promptField, value: '' });
    }
  };

  const handleTextAreaChange = (e: React.ChangeEvent<HTMLTextAreaElement>, type: 'worldview' | 'story' | 'character') => {
      const value = e.target.value;
      const selectedField = `selected${type.charAt(0).toUpperCase() + type.slice(1)}`;
      const promptField = `${type}Prompt`;
      formDispatch({ type: 'SET_FIELD', field: promptField, value });
      formDispatch({ type: 'SET_FIELD', field: selectedField, value: 'custom' });
      
      if (type === 'character') {
          formDispatch({ type: 'SET_FIELD', field: 'playerCodexAsset', value: null });
      }
  };
  
  const handleOpenPicker = (target: 'player' | number) => {
      setPickerTarget(target);
      setIsPickerOpen(true);
  };

  const handleAssetSelect = (asset: CodexAsset) => {
    if (asset.type !== 'character') return;
    if (pickerTarget === 'player') {
        formDispatch({ type: 'SET_FIELD', field: 'playerCodexAsset', value: asset });
        const name = asset.isPreset ? t(asset.name) : asset.name;
        const desc = asset.isPreset ? t(asset.description) : asset.description;
        formDispatch({ type: 'SET_FIELD', field: 'characterPrompt', value: `${name}\n${desc}` });
        formDispatch({ type: 'SET_FIELD', field: 'selectedCharacter', value: 'custom' });
    } else if (typeof pickerTarget === 'number') {
        formDispatch({ type: 'SET_AI_CODEX_ASSET', payload: { index: pickerTarget, asset }});
    }
    setIsPickerOpen(false);
  };


  const handleMainButtonClick = async () => {
    if (isBusy) return;

    if (!formState.worldviewPrompt.trim() || !formState.storyPrompt.trim() || !formState.characterPrompt.trim()) {
        addToast(t('setup.validationError'), 'error');
        return;
    }

    const finalPrompt = t('setup.promptTemplate', {
        world: formState.worldviewPrompt.trim(),
        story: formState.storyPrompt.trim(),
        character: formState.characterPrompt.trim()
    });

    setStep('generating');
    setError(null);
    // Reset any previous generation data from the global state
    globalDispatch({ type: 'RESTART_GAME' });
    
    const apiSettings: ApiSettings = { primaryTextModel: settings.primaryTextModel, fallbackTextModel: settings.fallbackTextModel, imageModel: settings.imageModel, imageEditModel: settings.imageEditModel, videoModel: settings.videoModel, sfxModel: settings.sfxModel, ttsModel: settings.ttsModel, musicModel: settings.musicModel, enableItemIcons: settings.enableItemIcons, enablePortraits: settings.enablePortraits, enableMapImages: settings.enableMapImages, enableLocationImages: settings.enableLocationImages, enableSfx: settings.enableSfx, qteDifficulty: settings.qteDifficulty, disableQteTimer: settings.disableQteTimer, roundRobinInitiative: settings.roundRobinInitiative, characterAgency: settings.characterAgency, aiCreativity: settings.aiCreativity };

    const processGenerationSuccess = (result: any) => {
        // Construct the initial game state directly into the global reducer
        const player = {
            ...result.playerCharacter,
            isAI: false,
            stats: sanitizeStats(result.playerCharacter.stats),
            inventory: ensureItemIds(result.playerCharacter.inventory),
            portraitStatus: 'pending' as PortraitStatus,
        };

        const aiCharacters = ensureArray(result.aiCharacters).map((c: any) => ({
            ...c,
            isAI: true,
            stats: sanitizeStats(c.stats),
            inventory: ensureItemIds(c.inventory),
            portraitStatus: 'pending' as PortraitStatus,
        }));

        const initialCharacters = [player, ...aiCharacters];
        
        // Use a temporary GameState object to dispatch all initial data
        const tempGameState: GameState = {
            ...currentGameState,
            gamePhase: GamePhase.SETUP, // Keep in setup phase for review
            characters: initialCharacters,
            partyStash: ensureItemIds(result.partyStash),
            locationItems: ensureItemIds(result.locationItems),
            vehicles: (Array.isArray(result.vehicles) ? result.vehicles : []).map((v: Vehicle) => ({ ...v, inventory: ensureItemIds(v.inventory) })),
            realEstate: result.realEstate || [],
            gameLog: [{ id: `msg-opening-${Date.now()}`, author: t('game.gameMaster'), content: result.openingScene, isGM: true }],
            gameLogSummary: result.gameLogSummary || result.openingScene,
            genreAndTone: result.genreAndTone,
            gameSummary: result.gameSummary,
            location: result.startingLocation,
            mapImagePrompt: result.mapImagePrompt || '',
            locationImagePrompt: result.locationImagePrompt || '',
            gameStyle: formState.gameStyle,
            knownLocations: result.knownLocations || [],
            map: formState.gameStyle === 'sandbox' ? result.map : null,
            suggestedActions: result.suggestedActions || [],
            // Ensure other fields are reset or set appropriately
            assetCache: {},
            activeEnemies: [],
            initiativeOrder: [],
            currentInitiativeIndex: 0,
        };
        
        // This single dispatch sets up the entire game world but keeps it in the SETUP phase
        globalDispatch({ type: 'POPULATE_GENERATED_DATA', payload: { gameState: tempGameState } });
        setStep('review');

        // Now, queue up asset generation tasks that will update the global state
        if (settings.enablePortraits && !isFallbackActive) {
            initialCharacters.forEach(char => {
                const assetKey = `portrait-${char.name}`;
                globalDispatch({ type: 'UPDATE_CHARACTER_PORTRAIT_STATUS', payload: { charName: char.name, status: 'queued', assetKey } });
                addTask({
                    type: 'generate-portrait', id: `task-portrait-${char.name}-${Date.now()}`, description: t('setup.generatingImages'), status: 'queued', priority: 30,
                    character: char,
                    prompt: t('service.imagePrompt.character', { description: char.description }),
                    model: settings.imageModel,
                    onSuccess: (url) => globalDispatch({ type: 'UPDATE_CHARACTER_PORTRAIT_STATUS', payload: { charName: char.name, status: 'done', imageUrl: `data:image/jpeg;base64,${url}`, assetKey } }),
                    onError: (e) => { addToast(parseApiError(e, 'generic'), 'error'); globalDispatch({ type: 'UPDATE_CHARACTER_PORTRAIT_STATUS', payload: { charName: char.name, status: 'error' } }); }
                });
            });
        }
        if (settings.enableMapImages && !isFallbackActive && result.mapImagePrompt) {
            const assetKey = 'world-map';
            addTask({
                type: 'generate-map-image', id: `task-map-image-${Date.now()}`, description: t('setup.task.generateMap'), status: 'queued', priority: 25,
                prompt: result.mapImagePrompt, model: settings.imageModel,
                onSuccess: (url) => globalDispatch({ type: 'SET_MAP_ASSET', payload: { key: assetKey, url: `data:image/jpeg;base64,${url}` } }),
                onError: (e) => addToast(parseApiError(e, 'generic'), 'error')
            });
        }
        if (settings.enableLocationImages && !isFallbackActive && result.locationImagePrompt) {
            const assetKey = `location-${result.startingLocation.replace(/\s+/g, '-')}`;
            addTask({
                type: 'generate-location-image', id: `task-loc-image-${Date.now()}`, description: t('setup.task.generateLocation'), status: 'queued', priority: 25,
                prompt: result.locationImagePrompt, model: settings.imageModel,
                onSuccess: (url) => globalDispatch({ type: 'SET_LOCATION_ASSET', payload: { key: assetKey, url: `data:image/jpeg;base64,${url}` } }),
                onError: (e) => addToast(parseApiError(e, 'generic'), 'error')
            });
        }
    };


    const task: GenerateSetupTask = {
        type: 'generate-setup', id: `task-setup-${Date.now()}`, description: t('setup.generatingFullGame'), status: 'queued', priority: 10,
        prompt: finalPrompt, gameStyle: formState.gameStyle, aiCount: formState.aiCount, difficulty: formState.difficulty, locale, temperature: settings.aiCreativity,
        settings: apiSettings,
        playerCodexAsset: formState.playerCodexAsset || undefined,
        aiCodexAssets: formState.aiCodexAssets.slice(0, formState.aiCount).filter(a => a) as CodexAsset[] | undefined,
        onFallback: handleFallback,
        onSuccess: (result) => {
            if (result.openingScene && result.openingScene.length > 500) {
                addTask({
                    type: 'generate-summary', id: `task-summary-${Date.now()}`, description: 'Summarizing opening scene...', status: 'queued', priority: 9,
                    textToSummarize: result.openingScene,
                    settings: { primaryTextModel: settings.primaryTextModel, fallbackTextModel: settings.fallbackTextModel },
                    onFallback: handleFallback,
                    onSuccess: (summary) => processGenerationSuccess({ ...result, gameLogSummary: summary }),
                    onError: (e) => {
                        console.warn("Failed to generate summary, using full text.", e);
                        processGenerationSuccess({ ...result, gameLogSummary: result.openingScene });
                    }
                } as GenerateSummaryTask);
            } else {
                processGenerationSuccess({ ...result, gameLogSummary: result.openingScene });
            }
        },
        onError: (e) => { setError(parseApiError(e, 'init')); setStep('error'); },
    };
    addTask(task);
  };
  
  const handleStartAdventure = () => {
    onStartAdventure();
  };
  
  const currentTaskDescription = activeTask ? activeTask.description : t('setup.generating');

  const renderAiCompanionSetup = (index: number) => {
    const asset = formState.aiCodexAssets[index];
    const name = asset ? (asset.isPreset ? t(asset.name) : asset.name) : `${t('setup.aiCompanionsLabel')} ${index + 1}`;

    return(
        <div key={`ai-${index}`}>
            <label className="block text-sm font-medium text-gray-300 mb-1">{`${t('setup.aiCompanionsLabel')} ${index+1}`}</label>
            <div className="flex gap-2">
                 <button
                    type="button"
                    onClick={() => handleOpenPicker(index)}
                    className="flex-1 bg-gray-700 hover:bg-gray-600 p-2 rounded-lg text-sm text-center flex items-center justify-center gap-2"
                >
                    <PaperclipIcon className="w-4 h-4" />
                    {asset ? t('setup.codex.selected', { name: name }) : t('setup.codex.choose')}
                </button>
                {asset && <button type="button" onClick={() => formDispatch({type: 'SET_AI_CODEX_ASSET', payload: {index, asset: null}})} className="p-2 bg-red-800/50 hover:bg-red-700 rounded-lg text-xs">X</button>}
            </div>
        </div>
    )
  }

  const renderFormContent = () => {
    if (view === 'start') {
        return (
            <div className="space-y-4">
                <button onClick={() => setView('new')} className="w-full bg-indigo-600 text-white font-bold py-4 px-4 rounded-lg hover:bg-indigo-700 transition-colors text-xl">
                    {t('setup.newAdventure')}
                </button>
                <button onClick={() => setView('load')} className="w-full bg-gray-700 text-white font-bold py-4 px-4 rounded-lg hover:bg-gray-600 transition-colors text-xl">
                    {t('setup.loadAdventure')}
                </button>
            </div>
        );
    }
    
    if (view === 'load') {
        const saves = Object.values(codex.saves).sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

        return (
             <div className="space-y-4 animate-fade-in">
                <button onClick={() => setView('start')} className="text-sm text-gray-400 hover:text-white mb-4">&larr; {t('common.back')}</button>
                
                <button 
                  type="button" 
                  onClick={handleImportClick}
                  disabled={isBusy}
                  className="w-full bg-gray-700/80 text-white font-semibold py-3 px-4 rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                >
                    <UploadIcon className="w-5 h-5" />
                    {t('codex.importButton')}
                </button>
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    accept=".json"
                    className="hidden"
                />

                <div className="border-t border-gray-700 my-4"></div>
                
                <h2 className="text-xl font-semibold text-center text-gray-200">{t('setup.loadAdventure')}</h2>

                <div className="space-y-2 max-h-96 overflow-y-auto scrollbar-thin pr-2">
                    {saves.length === 0 ? (
                        <p className="text-center text-gray-500 py-8 italic">{t('assetPicker.noResults')}</p>
                    ) : (
                        saves.map(save => (
                            <button 
                                key={save.id}
                                onClick={() => handleLoadFromCodexSelect(save)}
                                disabled={isBusy}
                                className="w-full text-left p-3 bg-gray-900/50 hover:bg-gray-700/80 rounded-lg transition-colors disabled:opacity-50 flex items-center gap-3"
                            >
                                <SaveIcon className="w-6 h-6 text-indigo-400 flex-shrink-0" />
                                <div className="flex-1 min-w-0">
                                    <p className="font-bold text-gray-100 truncate">{save.name}</p>
                                    <p className="text-xs text-gray-400">{new Date(save.createdAt).toLocaleString(locale)}</p>
                                </div>
                            </button>
                        ))
                    )}
                </div>
             </div>
        );
    }

    if (view === 'new') {
        return (
            <form onSubmit={(e) => { e.preventDefault(); handleMainButtonClick(); }} className="space-y-4 animate-fade-in">
                <button onClick={() => setView('start')} className="text-sm text-gray-400 hover:text-white mb-2">&larr; {t('common.back')}</button>
                <div className="space-y-2">
                    <label htmlFor="worldview-select" className="block text-sm font-medium text-gray-300">{t('presets.worldview.title')}</label>
                    <select id="worldview-select" value={formState.selectedWorldview} onChange={(e) => handleSelectChange(e, 'worldview')} className="w-full bg-gray-900/50 border border-gray-600 rounded-lg p-2 text-gray-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none mb-1">
                        {worldviews.map(w => <option key={w.id} value={w.id}>{t(w.titleKey)}</option>)}
                        <option value="custom">{t('presets.character.customTitle')}</option>
                    </select>
                    <textarea value={formState.worldviewPrompt} onChange={(e) => handleTextAreaChange(e, 'worldview')} rows={3} className="w-full bg-gray-900/80 border border-gray-600 rounded-lg p-2 text-gray-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition resize-y text-sm" />
                </div>
                <div className="space-y-2">
                    <label htmlFor="story-select" className="block text-sm font-medium text-gray-300">{t('presets.story.title')}</label>
                    <select id="story-select" value={formState.selectedStory} onChange={(e) => handleSelectChange(e, 'story')} className="w-full bg-gray-900/50 border border-gray-600 rounded-lg p-2 text-gray-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none mb-1">
                        {stories.map(s => <option key={s.id} value={s.id}>{t(s.titleKey)}</option>)}
                        <option value="custom">{t('presets.character.customTitle')}</option>
                    </select>
                    <textarea value={formState.storyPrompt} onChange={(e) => handleTextAreaChange(e, 'story')} rows={3} className="w-full bg-gray-900/80 border border-gray-600 rounded-lg p-2 text-gray-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition resize-y text-sm" />
                </div>
                <div className="space-y-2">
                    <div className="flex justify-between items-center">
                        <label htmlFor="character-select" className="block text-sm font-medium text-gray-300">{t('presets.character.title')}</label>
                        <button type="button" onClick={() => handleOpenPicker('player')} className="bg-gray-700 hover:bg-gray-600 p-2 rounded-lg text-xs flex items-center gap-1" aria-label={t('setup.codex.choose')}>
                            <PaperclipIcon className="w-4 h-4" /> <span>{t('setup.codex.choose')}</span>
                        </button>
                    </div>
                    {formState.playerCodexAsset && (
                        <div className="p-2 bg-gray-900/50 rounded-md flex items-center justify-between animate-fade-in border border-indigo-500/50 text-sm">
                            <p className="text-gray-200 font-semibold truncate" title={formState.playerCodexAsset.isPreset ? t(formState.playerCodexAsset.name) : formState.playerCodexAsset.name}>
                                {t('setup.codex.selected', { name: formState.playerCodexAsset.isPreset ? t(formState.playerCodexAsset.name) : formState.playerCodexAsset.name })}
                            </p>
                            <button type="button" onClick={() => formDispatch({type: 'SET_FIELD', field: 'playerCodexAsset', value: null})} className="p-1 rounded-full text-gray-400 hover:bg-gray-700 flex-shrink-0" aria-label={t('playerInput.clearContext')}>
                                <CloseIcon className="w-4 h-4" />
                            </button>
                        </div>
                    )}
                    <select id="character-select" value={formState.selectedCharacter} onChange={(e) => handleSelectChange(e, 'character')} className="w-full bg-gray-900/50 border border-gray-600 rounded-lg p-2 text-gray-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none mb-1">
                        {characters.map(c => <option key={c.id} value={c.id}>{t(c.titleKey)}</option>)}
                        <option value="custom">{t('presets.character.customTitle')}</option>
                    </select>
                    <textarea id="character-prompt" value={formState.characterPrompt} onChange={(e) => handleTextAreaChange(e, 'character')} placeholder={t('setup.scenarioPromptPlaceholder')} rows={4} className="w-full bg-gray-900/80 border border-gray-600 rounded-lg p-2 text-gray-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition resize-y text-sm" />
                </div>
                 <div>
                  <label htmlFor="ai-count-slider" className="block text-sm font-medium text-gray-300">{t('setup.aiCompanionsLabel', { count: formState.aiCount })}</label>
                  <input id="ai-count-slider" type="range" min="0" max="4" value={formState.aiCount} onChange={(e) => formDispatch({ type: 'SET_FIELD', field: 'aiCount', value: parseInt(e.target.value) })} className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer" />
                </div>
                {Array.from({ length: formState.aiCount }).map((_, i) => renderAiCompanionSetup(i))}
                <div className="mt-6">
                  <button type="submit" disabled={isBusy} className="w-full bg-indigo-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-indigo-700 disabled:bg-indigo-800/50 disabled:cursor-not-allowed flex items-center justify-center transition-colors text-lg">
                    {isBusy ? (<><LoadingSpinner /><span className="ml-2">{currentTaskDescription}</span></>) : t('setup.generateStoryButton')}
                  </button>
                </div>
            </form>
        );
    }
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-8 flex flex-col items-start bg-gray-900 text-gray-100 scrollbar-thin">
      <AssetPickerModal 
        isOpen={isPickerOpen} 
        onClose={() => setIsPickerOpen(false)} 
        onSelect={view === 'load' ? handleLoadFromCodexSelect : handleAssetSelect}
        initialCategory={view === 'load' ? 'save' : 'character'}
        filter={(asset) => view === 'load' ? asset.type === 'save' : asset.type === 'character'}
      />
      <div className="w-full max-w-3xl mx-auto bg-gray-800/50 p-6 rounded-lg border border-gray-700 shadow-lg">
        <h1 className="text-4xl font-bold text-center text-indigo-400 mb-2">{t('setup.title')}</h1>
        <p className="text-gray-400 text-center mb-6">{t('setup.subtitle')}</p>

        {step === 'form' && renderFormContent()}

        {step === 'review' && (
            <div className="space-y-4 animate-fade-in">
                <h2 className="text-2xl font-bold text-gray-100 mb-4">{t('setup.generatedCharactersTitle')}</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {currentGameState.characters.map(char => (
                        <div key={char.name} className="bg-gray-900/50 p-3 rounded-lg border border-gray-700 flex flex-col items-center text-center">
                            <div className="w-24 h-24 rounded-full bg-gray-700 flex items-center justify-center mb-2 overflow-hidden border-2 border-gray-600 flex-shrink-0" style={{ imageRendering: 'pixelated' }}>
                                {(char.portraitStatus === 'loading' || char.portraitStatus === 'queued') && <SmallLoadingSpinner />}
                                {char.portraitStatus === 'error' && <RefreshIcon className="w-8 h-8 text-red-400" />}
                                {(char.portraitStatus === 'done' && char.portraitAssetKey && currentGameState.assetCache[char.portraitAssetKey]) && <img src={currentGameState.assetCache[char.portraitAssetKey]} alt={char.name} className="w-full h-full object-cover" />}
                                {((char.portraitStatus === 'pending' || (char.portraitStatus === 'done' && !char.portraitAssetKey)) && settings.enablePortraits) && <ImageIcon className="w-8 h-8 text-indigo-400" />}
                                {!settings.enablePortraits && <UserIcon className="w-8 h-8 text-gray-500" />}
                            </div>
                            <h3 className="text-lg font-bold text-gray-100">{char.name}</h3>
                            <p className="text-sm text-gray-400 line-clamp-3">{char.description}</p>
                        </div>
                    ))}
                </div>
                <div className="mt-6 flex gap-2">
                    <button onClick={handleStartAdventure} disabled={isBusy} className="flex-1 bg-indigo-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-indigo-700 disabled:bg-indigo-800/50 disabled:cursor-not-allowed transition-colors text-lg">
                         {isBusy ? (<><LoadingSpinner /><span className="ml-2">{currentTaskDescription}</span></>) : t('game.startAdventureButton')}
                    </button>
                    <button onClick={() => { setStep('form'); setView('new'); }} className="bg-gray-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-gray-700 disabled:bg-gray-700/50 disabled:cursor-not-allowed transition-colors text-lg" disabled={isBusy}>
                        {t('setup.retryButton')}
                    </button>
                </div>
            </div>
        )}

        {(step === 'generating' || step === 'error') && (
          <div className="text-center py-10 space-y-4">
             {step === 'generating' && <LoadingSpinner />}
             <p className={`text-xl font-semibold ${step === 'error' ? 'text-red-400' : 'text-indigo-400'}`}>{error || currentTaskDescription}</p>
             {step === 'error' && <button onClick={() => { setStep('form'); setView('start'); }} className="bg-red-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-red-700 transition-colors">{t('setup.retryButton')}</button>}
          </div>
        )}
      </div>
    </div>
  );
};

export default SetupScreen;