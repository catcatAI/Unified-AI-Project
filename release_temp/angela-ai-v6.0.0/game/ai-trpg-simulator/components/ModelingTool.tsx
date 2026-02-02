import React, { useState, useReducer, useCallback, useEffect } from 'react';
import { useI18n } from '../context/i18n';
import { useApiErrorHandler, getAssetUrl } from '../services/utils';
import { LoadingSpinner, SmallLoadingSpinner, CubeIcon, PaperclipIcon, CameraIcon } from './icons';
import { GenerateThreeViewTask, RefineThreeViewTask, GenerateThreeViewFromImageTask, CodexModelAsset, CodexAsset } from '../types';
import { addTask } from '../services/taskQueueService';
import { useCodex } from '../context/codex';
import { useSettings } from '../context/settings';
import AssetPickerModal from './AssetPickerModal';
import ContextPreview from './ContextPreview';
import CameraCaptureModal from './CameraCaptureModal';

type View = 'front' | 'side' | 'top';
type ViewStatus = 'idle' | 'blueprint-generating' | 'queued' | 'generating' | 'done' | 'error' | 'refining-blueprint' | 'regenerating';


interface ViewState {
    status: ViewStatus;
    url?: string;
    error?: string;
}

interface ComponentState {
    prompt: string;
    isBusy: boolean;
    error: string | null;
    blueprint: string;
    views: Record<View, ViewState>;
    codexId: string | null;
    sourceAsset: CodexAsset | null;
}

type Action =
    | { type: 'SET_PROMPT'; payload: string }
    | { type: 'SET_SOURCE_ASSET'; payload: CodexAsset | null }
    | { type: 'START_GENERATION'; payload: { prompt: string; codexId: string } }
    | { type: 'START_REFINEMENT'; payload: { front: string; side: string; top: string } }
    | { type: 'BLUEPRINT_GENERATED'; payload: string }
    | { type: 'VIEW_GENERATED'; payload: { view: View; url: string } }
    | { type: 'GENERATION_COMPLETE' }
    | { type: 'SET_ERROR'; payload: string }
    | { type: 'SET_VIEW_ERROR'; payload: { view: View; error: string } };

const initialState: ComponentState = {
    prompt: '',
    isBusy: false,
    error: null,
    blueprint: '',
    views: {
        front: { status: 'idle' },
        side: { status: 'idle' },
        top: { status: 'idle' },
    },
    codexId: null,
    sourceAsset: null,
};

const reducer = (state: ComponentState, action: Action): ComponentState => {
    switch (action.type) {
        case 'SET_PROMPT':
            return { ...state, prompt: action.payload, sourceAsset: null }; // Clear source asset if user types
        case 'SET_SOURCE_ASSET':
             return { ...state, sourceAsset: action.payload, prompt: action.payload?.name || '' };
        case 'START_GENERATION':
            return {
                ...initialState,
                prompt: action.payload.prompt,
                codexId: action.payload.codexId,
                isBusy: true,
                views: {
                    front: { status: 'blueprint-generating' },
                    side: { status: 'blueprint-generating' },
                    top: { status: 'blueprint-generating' },
                },
                sourceAsset: state.sourceAsset,
            };
        case 'START_REFINEMENT':
            return {
                ...state,
                isBusy: true,
                error: null,
                blueprint: '',
                views: {
                    front: { status: 'refining-blueprint', url: action.payload.front },
                    side: { status: 'refining-blueprint', url: action.payload.side },
                    top: { status: 'refining-blueprint', url: action.payload.top },
                },
            };
        case 'BLUEPRINT_GENERATED':
            const isRefining = state.views.front.status === 'refining-blueprint';
            return {
                ...state,
                blueprint: action.payload,
                views: {
                    front: { ...state.views.front, status: isRefining ? 'regenerating' : 'generating' },
                    side: { ...state.views.side, status: isRefining ? 'regenerating' : 'generating' },
                    top: { ...state.views.top, status: isRefining ? 'regenerating' : 'generating' },
                },
            };
        case 'VIEW_GENERATED':
            return {
                ...state,
                views: {
                    ...state.views,
                    [action.payload.view]: { status: 'done', url: `data:image/jpeg;base64,${action.payload.url}` },
                },
            };
        case 'GENERATION_COMPLETE':
            return { ...state, isBusy: false };
        case 'SET_ERROR':
            return { ...state, isBusy: false, error: action.payload, blueprint: '', views: initialState.views };
        case 'SET_VIEW_ERROR':
             return {
                ...state,
                views: {
                    ...state.views,
                    [action.payload.view]: { ...state.views[action.payload.view], status: 'error', error: action.payload.error },
                },
            };
        default:
            return state;
    }
};

const ViewPanel: React.FC<{ title: string; state: ViewState; view: View }> = ({ title, state, view }) => {
    const { t } = useI18n();

    const renderContent = () => {
        switch (state.status) {
            case 'idle':
                return null;
            case 'blueprint-generating':
                return <div className="flex items-center gap-2 text-sm text-gray-400"><SmallLoadingSpinner /> {t('modelingTool.generatingBlueprint')}</div>;
            case 'refining-blueprint':
                return <div className="flex items-center gap-2 text-sm text-gray-400"><SmallLoadingSpinner /> {t('modelingTool.refiningBlueprint')}</div>;
            case 'queued':
                return <div className="flex items-center gap-2 text-sm text-gray-400">{t('modelingTool.queued')}</div>;
            case 'generating':
                return <div className="flex items-center gap-2 text-sm text-gray-400"><SmallLoadingSpinner /> {t('modelingTool.generatingView', { view: title.toLowerCase() })}</div>;
            case 'regenerating':
                return <div className="flex items-center gap-2 text-sm text-gray-400"><SmallLoadingSpinner /> {t('modelingTool.regeneratingView', { view: title.toLowerCase() })}</div>;
            case 'done':
                return <img src={state.url} alt={title} className="w-full h-full object-contain" />;
            case 'error':
                return <p className="text-red-400 text-sm">{state.error || t('modelingTool.error')}</p>;
        }
    };
    
    return (
        <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700 flex flex-col">
            <h3 className="text-lg font-semibold text-gray-200 mb-2">{title}</h3>
            <div className="flex-1 flex items-center justify-center aspect-square bg-black/20 rounded-md overflow-hidden">
                {renderContent()}
            </div>
        </div>
    );
};


const ModelingTool: React.FC<{ 
    addToast: (message: string, type?: 'info' | 'success' | 'error') => void; 
    initialAsset: CodexAsset | null;
    onInitialAssetConsumed: () => void;
}> = ({ addToast, initialAsset, onInitialAssetConsumed }) => {
    const { t } = useI18n();
    const { parseApiError } = useApiErrorHandler();
    const { updateCodexEntry, addCodexEntry } = useCodex();
    const [state, dispatch] = useReducer(reducer, initialState);
    const { primaryTextModel, fallbackTextModel, imageModel } = useSettings();
    const [isPickerOpen, setIsPickerOpen] = useState(false);
    const [isCameraOpen, setIsCameraOpen] = useState(false);

    useEffect(() => {
        if (initialAsset) {
            const assetName = initialAsset.isPreset ? t(initialAsset.name) : initialAsset.name;
            const payloadWithTranslatedName = { ...initialAsset, name: assetName };
            dispatch({ type: 'SET_SOURCE_ASSET', payload: payloadWithTranslatedName });
            onInitialAssetConsumed();
        }
    }, [initialAsset, onInitialAssetConsumed, t]);

    const handleFallback = useCallback(() => {
        addToast(t('service.fallbackMessage'), 'info');
    }, [addToast, t]);

    useEffect(() => {
        const allDone = Object.values(state.views).every((v: ViewState) => v.status === 'done');
        const hasUrls = state.views.front.url && state.views.side.url && state.views.top.url;
        if (allDone && hasUrls && !state.isBusy && state.codexId) {
            const asset: CodexModelAsset = {
                id: state.codexId,
                type: 'model',
                name: state.prompt,
                description: state.blueprint || t('modelingTool.defaultDescription', { name: state.prompt }),
                frontViewUrl: state.views.front.url!,
                sideViewUrl: state.views.side.url!,
                topViewUrl: state.views.top.url!,
                blueprint: state.blueprint,
            };
            addCodexEntry(asset); 
        }
    }, [state.isBusy, state.views, state.prompt, state.blueprint, state.codexId, addCodexEntry, t]);

    const handleGenerate = (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!state.prompt.trim() || state.isBusy) return;
        
        const codexId = state.sourceAsset?.id ? `model-from-${state.sourceAsset.id}-${Date.now()}` : state.prompt.toLowerCase().replace(/\s+/g, '-').slice(0, 50) + `-${Date.now()}`;
        dispatch({ type: 'START_GENERATION', payload: { prompt: state.prompt.trim(), codexId } });

        const sourceImageUrl = state.sourceAsset ? getAssetUrl(state.sourceAsset) : undefined;
        
        if (sourceImageUrl) {
            const task: GenerateThreeViewFromImageTask = {
                type: 'generate-three-view-from-image',
                id: `task-3view-img-${Date.now()}`,
                description: t('modelingTool.generating'),
                status: 'queued',
                priority: 20,
                prompt: state.prompt,
                sourceImageUrl,
                settings: { primaryTextModel, fallbackTextModel, imageModel },
                onFallback: handleFallback,
                onBlueprintGenerated: (blueprint) => dispatch({ type: 'BLUEPRINT_GENERATED', payload: blueprint }),
                onViewGenerated: (view, url) => dispatch({ type: 'VIEW_GENERATED', payload: { view, url } }),
                onSuccess: () => dispatch({ type: 'GENERATION_COMPLETE' }),
                onError: (err) => dispatch({ type: 'SET_ERROR', payload: parseApiError(err, 'generic') }),
            };
            addTask(task);
        } else {
            const task: GenerateThreeViewTask = {
                type: 'generate-three-view',
                id: `task-3view-${Date.now()}`,
                description: t('modelingTool.generating'),
                status: 'queued',
                priority: 20,
                prompt: state.prompt,
                settings: { primaryTextModel, fallbackTextModel, imageModel },
                onFallback: handleFallback,
                onBlueprintGenerated: (blueprint) => dispatch({ type: 'BLUEPRINT_GENERATED', payload: blueprint }),
                onViewGenerated: (view, url) => dispatch({ type: 'VIEW_GENERATED', payload: { view, url } }),
                onSuccess: () => dispatch({ type: 'GENERATION_COMPLETE' }),
                onError: (err) => dispatch({ type: 'SET_ERROR', payload: parseApiError(err, 'generic') }),
            };
            addTask(task);
        }
    };
    
    const handleRefine = () => {
        if (state.isBusy) return;
        const allDone = Object.values(state.views).every((v: ViewState) => v.status === 'done');
        if (!allDone) return;
        
        const urls = {
            front: state.views.front.url!,
            side: state.views.side.url!,
            top: state.views.top.url!,
        };

        dispatch({ type: 'START_REFINEMENT', payload: urls });
        
        const task: RefineThreeViewTask = {
            type: 'refine-three-view',
            id: `task-refine-${Date.now()}`,
            description: t('modelingTool.refining'),
            status: 'queued',
            priority: 20,
            prompt: state.prompt,
            frontViewUrl: urls.front,
            sideViewUrl: urls.side,
            topViewUrl: urls.top,
            settings: { primaryTextModel, fallbackTextModel, imageModel },
            onFallback: handleFallback,
            onBlueprintGenerated: (blueprint) => dispatch({ type: 'BLUEPRINT_GENERATED', payload: blueprint }),
            onViewGenerated: (view, url) => dispatch({ type: 'VIEW_GENERATED', payload: { view, url } }),
            onSuccess: () => dispatch({ type: 'GENERATION_COMPLETE' }),
            onError: (err) => dispatch({ type: 'SET_ERROR', payload: parseApiError(err, 'generic') }),
        };
        addTask(task);
    };

    const handleAssetSelect = (asset: CodexAsset) => {
        const assetName = asset.isPreset ? t(asset.name) : asset.name;
        const payloadWithTranslatedName = { ...asset, name: assetName };
        dispatch({ type: 'SET_SOURCE_ASSET', payload: payloadWithTranslatedName });
        setIsPickerOpen(false);
    };

    const handleCameraCapture = (dataUrl: string) => {
        setIsCameraOpen(false);
        const asset: CodexAsset = {
            id: `cam-capture-${Date.now()}`,
            type: 'image',
            name: t('modelingTool.captureName', { time: new Date().toLocaleTimeString() }),
            description: '',
            url: dataUrl
        };
        addCodexEntry(asset);
        addToast(t('modelingTool.captureSuccessToast'), 'success');
        dispatch({ type: 'SET_SOURCE_ASSET', payload: asset });
    }

    const showRefineButton = !state.isBusy && Object.values(state.views).every((v: ViewState) => v.status === 'done');

    return (
        <div className="w-full max-w-4xl mx-auto p-4 md:p-8 flex flex-col flex-1 overflow-y-auto scrollbar-thin">
             <AssetPickerModal 
                isOpen={isPickerOpen}
                onClose={() => setIsPickerOpen(false)}
                onSelect={handleAssetSelect}
                filter={(asset) => !!getAssetUrl(asset)}
            />
             <CameraCaptureModal 
                isOpen={isCameraOpen}
                onClose={() => setIsCameraOpen(false)}
                onCapture={handleCameraCapture}
             />
            <div className="text-center mb-8 flex-shrink-0">
                <h1 className="text-4xl font-bold text-indigo-400">{t('modelingTool.title')}</h1>
                <p className="text-gray-400 mt-2">{t('modelingTool.subtitle')}</p>
            </div>
            
            <div className="w-full bg-gray-800/50 p-6 rounded-lg border border-gray-700 shadow-lg flex-shrink-0">
                {state.sourceAsset && (
                    <ContextPreview 
                        asset={state.sourceAsset} 
                        onClear={() => dispatch({ type: 'SET_SOURCE_ASSET', payload: null })}
                        contextMessage={t('modelingTool.attachedContext')}
                        clearMessage={t('modelingTool.clearContext')}
                    />
                )}
                <textarea
                    value={state.prompt}
                    onChange={(e) => dispatch({ type: 'SET_PROMPT', payload: e.target.value })}
                    placeholder={t('modelingTool.promptPlaceholder')}
                    disabled={state.isBusy}
                    rows={2}
                    className="w-full bg-gray-900/50 border border-gray-600 rounded-lg p-4 text-gray-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition resize-y disabled:opacity-50"
                />
                <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                     <button
                        type="button"
                        onClick={() => setIsPickerOpen(true)}
                        disabled={state.isBusy}
                        className="w-full bg-gray-700 text-white font-bold py-3 px-4 rounded-lg hover:bg-gray-600 disabled:bg-gray-700/50 disabled:cursor-not-allowed flex items-center justify-center transition-colors text-lg"
                    >
                       <PaperclipIcon className="w-5 h-5 mr-2" /> {t('modelingTool.generateFromAssetButton')}
                    </button>
                    <button
                        onClick={handleGenerate}
                        disabled={state.isBusy || !state.prompt.trim()}
                        className="w-full bg-indigo-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-indigo-700 disabled:bg-indigo-800/50 disabled:cursor-not-allowed flex items-center justify-center transition-colors text-lg"
                    >
                        {state.isBusy ? (
                            <>
                                <LoadingSpinner />
                                <span className="ml-2">{state.views.front.status === 'refining-blueprint' ? t('modelingTool.refining') : t('modelingTool.generating')}</span>
                            </>
                        ) : (
                            t('modelingTool.generateButton')
                        )}
                    </button>
                </div>
            </div>
            
            {state.error && (
                <div className="mt-6 w-full bg-red-500/20 border border-red-500 text-red-300 px-4 py-3 rounded-md" role="alert">
                    {state.error}
                </div>
            )}
            
            {showRefineButton && (
                <div className="mt-4 text-center">
                    <button
                        onClick={handleRefine}
                        disabled={state.isBusy}
                        className="bg-green-600 text-white font-bold py-2 px-6 rounded-lg hover:bg-green-700 disabled:bg-green-800/50 disabled:cursor-not-allowed flex items-center justify-center transition-colors mx-auto"
                    >
                        {t('modelingTool.refineButton')}
                    </button>
                </div>
            )}
            
            {state.blueprint && (
                 <div className="mt-6 w-full bg-gray-900/50 p-4 rounded-lg border border-gray-700">
                    <h3 className="text-lg font-semibold text-gray-200 mb-2">{t('modelingTool.blueprintTitle')}</h3>
                    <p className="text-gray-300 whitespace-pre-wrap text-sm">{state.blueprint}</p>
                </div>
            )}

            <div className="mt-6 w-full">
                {state.views.front.status === 'idle' ? (
                     <div className="h-full flex items-center justify-center bg-gray-900/20 rounded-lg border-2 border-dashed border-gray-700 min-h-[300px] p-4">
                        <div className="text-center text-gray-500">
                            <CubeIcon className="w-16 h-16 mx-auto mb-2" />
                            <p>{t('modelingTool.idlePrompt')}</p>
                        </div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <ViewPanel title={t('modelingTool.views.front')} view="front" state={state.views.front} />
                        <ViewPanel title={t('modelingTool.views.side')} view="side" state={state.views.side} />
                        <ViewPanel title={t('modelingTool.views.top')} view="top" state={state.views.top} />
                    </div>
                )}
            </div>
        </div>
    );
};

export default ModelingTool;