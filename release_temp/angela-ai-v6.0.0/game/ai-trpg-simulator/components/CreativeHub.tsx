import React, { useState, useCallback, useEffect } from 'react';
import { useI18n } from '../context/i18n';
import { useCodex } from '../context/codex';
import { useSettings } from '../context/settings';
import { useApiErrorHandler, getAssetUrl } from '../services/utils';
import { addTask } from '../services/taskQueueService';
import { CodexAsset, CodexImageAsset, DescribeImageTask, TranscribeAudioTask, GenerateSfxFromAudioTask, GenerateImageTask, GenerateMusicFromAudioTask, GenerateMusicFromTextTask, GenerateSfxTask, ApiSettings } from '../types';
import { SparklesIcon, CameraIcon, MicrophoneIcon, PaperclipIcon, CloseIcon } from './icons';
import CameraCaptureModal from './CameraCaptureModal';
import AudioRecordingModal from './AudioRecordingModal';
import { Tool } from './Header';
import AssetPickerModal from './AssetPickerModal';

interface CreativeHubProps {
  addToast: (message: string, type?: 'info' | 'success' | 'error') => void;
  onSendAssetToTool: (asset: CodexAsset, tool: Tool) => void;
  initialAsset?: CodexAsset | null;
  onInitialAssetConsumed?: () => void;
}

type InputMode = 'selection' | 'text' | 'image' | 'audio';

const CreativeHub: React.FC<CreativeHubProps> = ({ addToast, onSendAssetToTool, initialAsset, onInitialAssetConsumed }) => {
    const { t } = useI18n();
    const { addCodexEntry } = useCodex();
    const settings = useSettings();
    const { parseApiError } = useApiErrorHandler();
    
    const [inputMode, setInputMode] = useState<InputMode>('selection');
    const [sourceAsset, setSourceAsset] = useState<{data: string, type: 'image' | 'audio', name: string} | null>(null);
    const [isCameraOpen, setIsCameraOpen] = useState(false);
    const [isMicOpen, setIsMicOpen] = useState(false);
    const [isPickerOpen, setIsPickerOpen] = useState(false);
    const [prompt, setPrompt] = useState('');

    const handleInitialAsset = useCallback((asset: CodexAsset) => {
        const url = getAssetUrl(asset);
        // Translate name and description if it's a preset
        const name = asset.isPreset ? t(asset.name) : asset.name;
        const description = asset.isPreset ? t(asset.description) : asset.description;

        if (url) {
             if (asset.type === 'audio') {
                setSourceAsset({ data: url, type: 'audio', name });
                setInputMode('audio');
             } else { // Assume image-like
                setSourceAsset({ data: url, type: 'image', name });
                setInputMode('image');
             }
        } else {
            // Handle text-based assets
            setPrompt(description ? `${name}\n${description}`: name);
            setInputMode('text');
        }
    }, [t]);

    useEffect(() => {
        if (initialAsset && onInitialAssetConsumed) {
            handleInitialAsset(initialAsset);
            onInitialAssetConsumed();
        }
    }, [initialAsset, onInitialAssetConsumed, handleInitialAsset]);


    const resetState = () => {
        setInputMode('selection');
        setSourceAsset(null);
        setPrompt('');
    };

    const handleCaptureComplete = (dataUrl: string) => {
        setIsCameraOpen(false);
        const name = t('creativeHub.captureName', { time: new Date().toLocaleTimeString() });
        setSourceAsset({ data: dataUrl, type: 'image', name });
        setInputMode('image');
    };

    const handleRecordComplete = (dataUrl: string) => {
        setIsMicOpen(false);
        const name = t('creativeHub.recordName', { time: new Date().toLocaleTimeString() });
        setSourceAsset({ data: dataUrl, type: 'audio', name });
        setInputMode('audio');
    };
    
    const handleAssetSelect = (asset: CodexAsset) => {
        handleInitialAsset(asset);
        setIsPickerOpen(false);
    };

    const handleAction = (action: 'avatar' | 'portrait' | 'icon' | 'scene' | 'describe' | 'model' | 'transcribe' | 'sfx' | 'music' | 'audio-to-image' | 'text-to-image' | 'text-to-sfx' | 'text-to-music') => {
        const currentPrompt = prompt;

        const createAssetAndToast = (asset: CodexAsset) => {
            addCodexEntry(asset);
            addToast(t('creativeHub.success', { assetName: asset.name }), 'success');
        };

        const onFallback = () => addToast(t('service.fallbackMessage'), 'info');

        switch (action) {
            // Image-based actions
            case 'avatar':
            case 'portrait':
            case 'icon':
            case 'scene': {
                if (!sourceAsset || sourceAsset.type !== 'image') return;
                const task: GenerateImageTask = {
                    type: 'generate-image', id: `task-img-from-img-${Date.now()}`, description: t(`creativeHub.task.${action}`), status: 'queued', priority: 20,
                    prompt: currentPrompt || `Generate a ${action} based on this image.`,
                    sourceImageUrl: sourceAsset.data,
                    model: settings.imageEditModel,
                    aspectRatio: '1:1', // Aspect ratio is required, but ignored by the model for image-to-image
                    onSuccess: (url) => {
                        const dataUrl = `data:image/jpeg;base64,${url}`;
                        const assetMap: Record<string, { type: 'character' | 'item' | 'location'; name: string; }> = { 
                            avatar: { type: 'character', name: `${sourceAsset.name} ${t('creativeHub.assetSuffix.avatar')}` }, 
                            portrait: { type: 'character', name: `${sourceAsset.name} ${t('creativeHub.assetSuffix.portrait')}` }, 
                            icon: { type: 'item', name: `${sourceAsset.name} ${t('creativeHub.assetSuffix.icon')}` }, 
                            scene: { type: 'location', name: `${sourceAsset.name} ${t('creativeHub.assetSuffix.scene')}` }
                        };
                        const partialAsset = assetMap[action];
                        const description = t('creativeHub.generatedAssetDescription', { sourceName: sourceAsset.name });
                        createAssetAndToast({ ...partialAsset, id: `${action}-${Date.now()}`, description: description, [action === 'icon' ? 'iconUrl' : 'imageUrl']: dataUrl } as CodexAsset);
                    },
                    onError: (err) => addToast(parseApiError(err), 'error')
                };
                addTask(task);
                break;
            }
            case 'describe': {
                if (!sourceAsset || sourceAsset.type !== 'image') return;
                const task: DescribeImageTask = {
                    type: 'describe-image',
                    id: `task-describe-${Date.now()}`,
                    description: t('creativeHub.task.describe'),
                    status: 'queued',
                    priority: 20,
                    sourceImageUrl: sourceAsset.data,
                    settings: { primaryTextModel: settings.primaryTextModel, fallbackTextModel: settings.fallbackTextModel },
                    onFallback: onFallback,
                    onSuccess: (text) => addToast(text, 'info'),
                    onError: (err) => addToast(parseApiError(err), 'error')
                };
                addTask(task);
                break;
            }
            case 'model': {
                if (!sourceAsset || sourceAsset.type !== 'image') return;
                 const newAsset: CodexImageAsset = { id: `img-hub-${Date.now()}`, type: 'image', name: sourceAsset.name, description: t('creativeHub.generatedAssetDescription', { sourceName: 'Creative Hub' }), url: sourceAsset.data };
                addCodexEntry(newAsset);
                onSendAssetToTool(newAsset, 'model');
                break;
            }
            // Audio-based actions
            case 'transcribe': {
                if (!sourceAsset || sourceAsset.type !== 'audio') return;
                addTask({ type: 'transcribe-audio', id: `task-transcribe-${Date.now()}`, description: t('creativeHub.task.transcribe'), status: 'queued', priority: 20, sourceAudioUrl: sourceAsset.data,
                    onSuccess: (text) => addToast(`Transcription: ${text}`, 'info'),
                    onError: (err) => addToast(parseApiError(err), 'error')
                });
                break;
            }
             case 'sfx': {
                if (!sourceAsset || sourceAsset.type !== 'audio') return;
                addTask({ type: 'generate-sfx-from-audio', id: `task-sfx-from-audio-${Date.now()}`, description: t('creativeHub.task.sfx'), status: 'queued', priority: 25, sourceAudioUrl: sourceAsset.data, prompt: currentPrompt, model: settings.sfxModel,
                    onSuccess: (url) => createAssetAndToast({ type: 'audio', id: `sfx-gen-${Date.now()}`, name: currentPrompt || sourceAsset.name, description: t('creativeHub.generatedAssetDescription', { sourceName: sourceAsset.name }), url }),
                    onError: (err) => addToast(parseApiError(err), 'error')
                });
                break;
            }
            case 'music': {
                 if (!sourceAsset || sourceAsset.type !== 'audio') return;
                 addTask({ type: 'generate-music-from-audio', id: `task-music-from-audio-${Date.now()}`, description: t('creativeHub.task.music'), status: 'queued', priority: 25, sourceAudioUrl: sourceAsset.data, prompt: currentPrompt, model: settings.musicModel,
                    onSuccess: (url) => createAssetAndToast({ type: 'audio', id: `music-gen-${Date.now()}`, name: currentPrompt || `Music for ${sourceAsset.name}`, description: t('creativeHub.generatedAssetDescription', { sourceName: sourceAsset.name }), url }),
                    onError: (err) => addToast(parseApiError(err), 'error')
                });
                break;
            }
            // Text-based actions
            case 'text-to-image': {
                if (!currentPrompt) return;
                addTask({ type: 'generate-image', id: `task-txt-to-img-${Date.now()}`, description: t('creativeHub.task.image'), status: 'queued', priority: 20, prompt: currentPrompt, aspectRatio: '16:9', model: settings.imageModel,
                    onSuccess: (url) => createAssetAndToast({ type: 'image', id: `img-gen-${Date.now()}`, name: currentPrompt, description: t('creativeHub.generatedAssetDescription', { sourceName: 'Text Prompt' }), url: `data:image/jpeg;base64,${url}` }),
                    onError: (err) => addToast(parseApiError(err), 'error')
                });
                break;
            }
            case 'text-to-sfx': {
                if (!currentPrompt) return;
                addTask({ type: 'generate-sfx', id: `task-txt-to-sfx-${Date.now()}`, description: t('creativeHub.task.sfx'), status: 'queued', priority: 25, prompt: currentPrompt, messageId: '', model: settings.sfxModel,
                    onSuccess: (url) => createAssetAndToast({ type: 'audio', id: `sfx-txt-gen-${Date.now()}`, name: currentPrompt, description: t('creativeHub.generatedAssetDescription', { sourceName: 'Text Prompt' }), url }),
                    onError: (err) => addToast(parseApiError(err), 'error')
                });
                break;
            }
            case 'text-to-music': {
                 if (!currentPrompt) return;
                 addTask({ type: 'generate-music-from-text', id: `task-txt-to-music-${Date.now()}`, description: t('creativeHub.task.music'), status: 'queued', priority: 25, prompt: currentPrompt, model: settings.musicModel,
                    onSuccess: (url) => createAssetAndToast({ type: 'audio', id: `music-txt-gen-${Date.now()}`, name: currentPrompt, description: t('creativeHub.generatedAssetDescription', { sourceName: 'Text Prompt' }), url }),
                    onError: (err) => addToast(parseApiError(err), 'error')
                });
                break;
            }
        }
        resetState();
    };


    const renderContent = () => {
        if (inputMode === 'selection') {
            return (
                <div>
                    <h2 className="text-lg font-semibold text-center mb-4 text-gray-300">{t('creativeHub.inputPrompt')}</h2>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                         <button onClick={() => setInputMode('text')} className="bg-gray-700/80 hover:bg-gray-700 p-6 rounded-lg flex flex-col items-center justify-center gap-2 transition-colors"><PaperclipIcon className="w-8 h-8"/><span>{t('creativeHub.fromText')}</span></button>
                         <button onClick={() => setIsPickerOpen(true)} className="bg-gray-700/80 hover:bg-gray-700 p-6 rounded-lg flex flex-col items-center justify-center gap-2 transition-colors"><SparklesIcon className="w-8 h-8"/><span>{t('game.tabAssets')}</span></button>
                         <button onClick={() => setIsCameraOpen(true)} className="bg-gray-700/80 hover:bg-gray-700 p-6 rounded-lg flex flex-col items-center justify-center gap-2 transition-colors"><CameraIcon className="w-8 h-8"/><span>{t('creativeHub.fromCamera')}</span></button>
                         <button onClick={() => setIsMicOpen(true)} className="bg-gray-700/80 hover:bg-gray-700 p-6 rounded-lg flex flex-col items-center justify-center gap-2 transition-colors"><MicrophoneIcon className="w-8 h-8"/><span>{t('creativeHub.fromMic')}</span></button>
                    </div>
                </div>
            );
        }

        let actions: React.ReactNode = null;
        let inputDisplay: React.ReactNode = null;

        if (inputMode === 'image' && sourceAsset) {
            inputDisplay = <img src={sourceAsset.data} alt="Input" className="w-full h-full object-contain" />;
            actions = (
                <>
                    <button onClick={() => handleAction('avatar')} className="bg-gray-700/80 hover:bg-gray-700 p-3 rounded-lg text-left">{t('creativeHub.imageActions.generateAvatar')}</button>
                    <button onClick={() => handleAction('portrait')} className="bg-gray-700/80 hover:bg-gray-700 p-3 rounded-lg text-left">{t('creativeHub.imageActions.generatePortrait')}</button>
                    <button onClick={() => handleAction('icon')} className="bg-gray-700/80 hover:bg-gray-700 p-3 rounded-lg text-left">{t('creativeHub.imageActions.generateItemIcon')}</button>
                    <button onClick={() => handleAction('scene')} className="bg-gray-700/80 hover:bg-gray-700 p-3 rounded-lg text-left">{t('creativeHub.imageActions.generateScene')}</button>
                    <button onClick={() => handleAction('describe')} className="bg-gray-700/80 hover:bg-gray-700 p-3 rounded-lg text-left">{t('creativeHub.imageActions.describeImage')}</button>
                    <button onClick={() => handleAction('model')} className="bg-gray-700/80 hover:bg-gray-700 p-3 rounded-lg text-left">{t('creativeHub.imageActions.create3DModel')}</button>
                </>
            );
        } else if (inputMode === 'audio' && sourceAsset) {
            inputDisplay = <audio src={sourceAsset.data} controls className="w-full" />;
            actions = (
                <>
                    <button onClick={() => handleAction('transcribe')} className="bg-gray-700/80 hover:bg-gray-700 p-3 rounded-lg text-left">{t('creativeHub.audioActions.transcribe')}</button>
                    <button onClick={() => handleAction('sfx')} className="bg-gray-700/80 hover:bg-gray-700 p-3 rounded-lg text-left">{t('creativeHub.audioActions.generateSfx')}</button>
                    <button onClick={() => handleAction('music')} className="bg-gray-700/80 hover:bg-gray-700 p-3 rounded-lg text-left">{t('creativeHub.audioActions.generateMusic')}</button>
                </>
            );
        } else if (inputMode === 'text') {
            inputDisplay = (
                 <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder={t('creativeHub.promptPlaceholder')}
                    rows={8}
                    className="w-full h-full bg-gray-900/50 border border-gray-600 rounded-lg p-2 text-gray-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition resize-y"
                />
            );
            actions = (
                <>
                    <button onClick={() => handleAction('text-to-image')} disabled={!prompt.trim()} className="bg-gray-700/80 hover:bg-gray-700 p-3 rounded-lg text-left disabled:opacity-50 disabled:cursor-not-allowed">{t('creativeHub.textActions.generateImage')}</button>
                    <button onClick={() => handleAction('text-to-sfx')} disabled={!prompt.trim()} className="bg-gray-700/80 hover:bg-gray-700 p-3 rounded-lg text-left disabled:opacity-50 disabled:cursor-not-allowed">{t('creativeHub.textActions.generateSfx')}</button>
                    <button onClick={() => handleAction('text-to-music')} disabled={!prompt.trim()} className="bg-gray-700/80 hover:bg-gray-700 p-3 rounded-lg text-left disabled:opacity-50 disabled:cursor-not-allowed">{t('creativeHub.textActions.generateMusic')}</button>
                </>
            );
        }

        return (
            <div className="relative">
                <button onClick={resetState} className="absolute -top-4 -right-4 z-10 p-1 bg-gray-600 rounded-full text-white hover:bg-gray-500" aria-label="Close"><CloseIcon className="w-4 h-4" /></button>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
                    <div className="flex flex-col gap-4">
                        <div className="relative aspect-video w-full bg-black/30 rounded-md overflow-hidden flex items-center justify-center p-2">
                          {inputDisplay}
                        </div>
                        {(inputMode === 'image' || inputMode === 'audio') && (
                            <textarea
                                value={prompt}
                                onChange={(e) => setPrompt(e.target.value)}
                                placeholder={t('creativeHub.optionalPromptPlaceholder')}
                                rows={2}
                                className="w-full bg-gray-900/50 border border-gray-600 rounded-lg p-2 text-gray-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition resize-y"
                            />
                        )}
                    </div>
                    <div className="flex flex-col gap-4">
                        <h2 className="text-lg font-semibold text-center text-gray-300">{t('creativeHub.actionPrompt')}</h2>
                        <div className="grid grid-cols-1 gap-2">
                            {actions}
                        </div>
                    </div>
                </div>
            </div>
        )
    };


    return (
        <div className="w-full max-w-4xl mx-auto flex flex-col flex-1 overflow-y-auto scrollbar-thin">
            <div className="p-4 md:p-8">
                <CameraCaptureModal isOpen={isCameraOpen} onClose={() => setIsCameraOpen(false)} onCapture={handleCaptureComplete} />
                <AudioRecordingModal isOpen={isMicOpen} onClose={() => setIsMicOpen(false)} onRecordComplete={handleRecordComplete} />
                 <AssetPickerModal 
                    isOpen={isPickerOpen}
                    onClose={() => setIsPickerOpen(false)}
                    onSelect={handleAssetSelect}
                />
                
                <div className="text-center mb-8">
                    <h1 className="text-4xl font-bold text-indigo-400">{t('creativeHub.title')}</h1>
                    <p className="text-gray-400 mt-2">{t('creativeHub.subtitle')}</p>
                </div>
                
                <div className="w-full bg-gray-800/50 p-6 rounded-lg border border-gray-700 shadow-lg flex flex-col gap-6">
                    {renderContent()}
                </div>
            </div>
        </div>
    );
};

export default CreativeHub;