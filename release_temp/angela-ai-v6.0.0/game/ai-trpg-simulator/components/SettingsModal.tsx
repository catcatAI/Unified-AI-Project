import React from 'react';
import { useSettings } from '../context/settings';
import { useI18n } from '../context/i18n';
import { useFocusTrap } from '../hooks/useFocusTrap';
import { CloseIcon, VolumeUpIcon, VolumeOffIcon } from './icons';
import { useApiKey } from '../context/apiKey';

interface SettingsModalProps {
  onClose: () => void;
}

const ToggleSwitch: React.FC<{ label: string; enabled: boolean; onChange: (enabled: boolean) => void; }> = ({ label, enabled, onChange }) => {
    return (
        <div className="flex items-center justify-between">
            <span className="text-gray-300">{label}</span>
            <button
                type="button"
                role="switch"
                aria-checked={enabled}
                onClick={() => onChange(!enabled)}
                className={`relative inline-flex items-center h-6 rounded-full w-11 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-indigo-500 ${
                enabled ? 'bg-indigo-600' : 'bg-gray-600'
                }`}
            >
                <span
                className={`inline-block w-4 h-4 transform bg-white rounded-full transition-transform ${
                    enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
                />
            </button>
        </div>
    );
};

const VolumeSlider: React.FC<{ label: string; volume: number; onChange: (volume: number) => void; labelId: string; }> = ({ label, volume, onChange, labelId }) => (
    <div className="flex items-center justify-between gap-4">
        <label htmlFor={labelId} className="text-gray-300 flex-shrink-0">{label}</label>
        <div className="flex items-center gap-2 w-full">
             {volume > 0 ? <VolumeUpIcon className="w-5 h-5 text-gray-400" /> : <VolumeOffIcon className="w-5 h-5 text-gray-500" />}
            <input
                id={labelId}
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={volume}
                onChange={(e) => onChange(parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                aria-valuetext={`${Math.round(volume * 100)}%`}
            />
        </div>
    </div>
);

const SettingsGroup: React.FC<{title: string; children: React.ReactNode}> = ({title, children}) => (
    <div className="space-y-4 p-4 bg-gray-900/50 rounded-lg border border-gray-700">
        <h3 className="font-semibold text-gray-200">{title}</h3>
        {children}
    </div>
);


const SettingsModal: React.FC<SettingsModalProps> = ({ onClose }) => {
  const { t } = useI18n();
  const settings = useSettings();
  const modalRef = useFocusTrap<HTMLDivElement>();
  const { isKeySelected, selectKey } = useApiKey();
  
  const textModelOptions = [
      { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash' },
      { id: 'gemini-2.5-pro', name: 'Gemini 2.5 Pro' },
      { id: 'gemini-flash-latest', name: 'Gemini Flash (Latest)' },
      { id: 'gemini-flash-lite-latest', name: 'Gemini Flash Lite (Gemma)' },
  ];

  const imageModelOptions = [
    { id: 'imagen-4.0-generate-001', name: 'Imagen 4 (Quality)' },
    { id: 'gemini-2.5-flash-image', name: 'Gemini 2.5 Flash Image (Fast)' },
  ];

  const videoModelOptions = [
    { id: 'veo-3.1-fast-generate-preview', name: 'Veo 3.1 Fast (720p)' },
    { id: 'veo-3.1-generate-preview', name: 'Veo 3.1 (1080p)' },
  ];

  const audioModelOptions = [
      { id: 'gemini-2.5-flash-preview-tts', name: 'Gemini TTS' },
  ];
  
  const musicModelOptions = [
      { id: 'simulated', name: 'Simulated Engine' },
  ];

  const creativityOptions = [
    { label: t('setup.creativityBalanced'), value: 0.5 },
    { label: t('setup.creativityCreative'), value: 0.8 },
    { label: t('setup.creativityWild'), value: 1.0 },
  ];

  const qteDifficultyOptions: { labelKey: string, value: 'easy' | 'normal' | 'hard' }[] = [
    { labelKey: 'suite.settings.qteDifficulties.easy', value: 'easy' },
    { labelKey: 'suite.settings.qteDifficulties.normal', value: 'normal' },
    { labelKey: 'suite.settings.qteDifficulties.hard', value: 'hard' },
  ];

  return (
    <div 
        className="fixed inset-0 bg-black/70 z-[100] flex items-center justify-center p-4 backdrop-blur-sm"
        onClick={onClose}
    >
        <div 
            ref={modalRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="settings-title"
            className="bg-gray-800 rounded-lg border-2 border-gray-700 shadow-lg w-full max-w-md text-white p-6 max-h-[90vh] overflow-y-auto scrollbar-thin"
            onClick={(e) => e.stopPropagation()}
        >
            <div className="flex justify-between items-center mb-6">
                <h2 id="settings-title" className="text-2xl font-bold text-indigo-400">{t('suite.settings.title')}</h2>
                <button
                    onClick={onClose}
                    className="p-1 rounded-full text-gray-400 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-indigo-500"
                    aria-label={t('game.ariaLabels.closeModal')}
                >
                    <CloseIcon className="w-6 h-6" />
                </button>
            </div>

            <div className="space-y-6">
                <SettingsGroup title={t('suite.settings.title')}>
                    <div role="group" aria-labelledby="language-group-label" className="flex">
                        <button onClick={() => settings.setLocale('en')} className={`flex-1 py-2 text-sm rounded-l-md transition-colors ${settings.locale === 'en' ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}>EN</button>
                        <button onClick={() => settings.setLocale('zh')} className={`flex-1 py-2 text-sm rounded-r-md transition-colors ${settings.locale === 'zh' ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}>中文</button>
                    </div>
                </SettingsGroup>

                <SettingsGroup title={t('suite.settings.gameplay')}>
                     <div>
                        <label className="block text-sm text-gray-300 mb-2">{t('suite.settings.qteDifficulty')}</label>
                         <div className={`flex bg-gray-900/50 border border-gray-700 rounded-lg p-1`}>
                            {qteDifficultyOptions.map(opt => (
                            <button key={opt.value} type="button" onClick={() => settings.setQteDifficulty(opt.value)} aria-pressed={settings.qteDifficulty === opt.value} className={`flex-1 text-center text-sm font-semibold py-1 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-indigo-500 ${settings.qteDifficulty === opt.value ? 'bg-indigo-600 text-white' : 'text-gray-300 hover:bg-gray-700'}`}>
                                {t(opt.labelKey)}
                            </button>
                            ))}
                        </div>
                    </div>
                    <ToggleSwitch label={t('suite.settings.disableQteTimer')} enabled={settings.disableQteTimer} onChange={settings.setDisableQteTimer} />
                    <ToggleSwitch label={t('suite.settings.roundRobin')} enabled={settings.roundRobinInitiative} onChange={settings.setRoundRobinInitiative} />
                    <ToggleSwitch label={t('suite.settings.characterAgency')} enabled={settings.characterAgency} onChange={settings.setCharacterAgency} />
                    <ToggleSwitch label={t('suite.settings.enableDragAndDrop')} enabled={settings.enableDragAndDrop} onChange={settings.setEnableDragAndDrop} />
                </SettingsGroup>

                 <SettingsGroup title={t('suite.settings.audio')}>
                    <ToggleSwitch label={t('suite.settings.tts')} enabled={settings.enableTts} onChange={settings.setEnableTts} />
                    <ToggleSwitch label={t('game.soundEffects')} enabled={settings.enableSfx} onChange={settings.setEnableSfx} />
                    <ToggleSwitch label={t('suite.settings.voiceInput')} enabled={settings.enableVoiceInput} onChange={settings.setEnableVoiceInput} />
                    <VolumeSlider label={t('game.backgroundMusic')} volume={settings.bgmVolume} onChange={settings.setBgmVolume} labelId="bgm-volume-slider"/>
                    <VolumeSlider label={t('game.soundEffects')} volume={settings.sfxVolume} onChange={settings.setSfxVolume} labelId="sfx-volume-slider"/>
                </SettingsGroup>

                <SettingsGroup title={t('suite.settings.generation')}>
                    <ToggleSwitch label={t('suite.settings.portraits')} enabled={settings.enablePortraits} onChange={settings.setEnablePortraits} />
                    <ToggleSwitch label={t('suite.settings.mapImages')} enabled={settings.enableMapImages} onChange={settings.setEnableMapImages} />
                    <ToggleSwitch label={t('suite.settings.locationImages')} enabled={settings.enableLocationImages} onChange={settings.setEnableLocationImages} />
                    <ToggleSwitch label={t('suite.settings.itemIcons')} enabled={settings.enableItemIcons} onChange={settings.setEnableItemIcons} />
                    <ToggleSwitch label={t('suite.settings.enableMvalGen')} enabled={settings.enableMvalGen} onChange={settings.setEnableMvalGen} />
                </SettingsGroup>

                <SettingsGroup title={t('suite.settings.apiKey')}>
                     <p className="text-xs text-gray-400">{t('suite.settings.apiKeyDesc')}</p>
                    <button onClick={selectKey} className="w-full bg-gray-700 hover:bg-gray-600 text-white font-semibold py-2 px-4 rounded-md transition-colors">
                        {isKeySelected ? t('suite.settings.apiKeySelected') : t('suite.settings.selectApiKey')}
                    </button>
                     <p className="text-xs text-gray-500 text-center pt-1">
                        For more information, visit the{' '}
                        <a href="https://ai.google.dev/gemini-api/docs/billing" target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline">
                            billing documentation
                        </a>.
                    </p>
                </SettingsGroup>
                
                 <SettingsGroup title={t('suite.settings.modelSettings')}>
                     <div>
                        <label className="block text-sm text-gray-300 mb-2">{t('setup.aiOptimizationTitle')}</label>
                         <div className={`flex bg-gray-900/50 border border-gray-700 rounded-lg p-1`}>
                            {creativityOptions.map(opt => (
                            <button key={opt.value} type="button" onClick={() => settings.setAiCreativity(opt.value)} aria-pressed={settings.aiCreativity === opt.value} className={`flex-1 text-center text-sm font-semibold py-1 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-indigo-500 ${settings.aiCreativity === opt.value ? 'bg-indigo-600 text-white' : 'text-gray-300 hover:bg-gray-700'}`}>
                                {opt.label}
                            </button>
                            ))}
                        </div>
                    </div>
                    <div>
                        <label htmlFor="primary-model-select" className="block text-sm text-gray-300 mb-2">{t('suite.settings.primaryModel')}</label>
                        <select
                            id="primary-model-select"
                            value={settings.primaryTextModel}
                            onChange={(e) => settings.setPrimaryTextModel(e.target.value)}
                            className="w-full bg-gray-700 border border-gray-500 rounded-md p-2 text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none transition"
                        >
                           {textModelOptions.map(opt => <option key={opt.id} value={opt.id}>{opt.name}</option>)}
                        </select>
                    </div>
                     <div>
                        <label htmlFor="fallback-model-select" className="block text-sm text-gray-300 mb-2">{t('suite.settings.fallbackModel')}</label>
                        <select
                            id="fallback-model-select"
                            value={settings.fallbackTextModel}
                            onChange={(e) => settings.setFallbackTextModel(e.target.value)}
                            className="w-full bg-gray-700 border border-gray-500 rounded-md p-2 text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none transition"
                        >
                           {textModelOptions.map(opt => <option key={opt.id} value={opt.id}>{opt.name}</option>)}
                        </select>
                    </div>
                     <div>
                        <label htmlFor="image-model-select" className="block text-sm text-gray-300 mb-2 mt-2">{t('suite.settings.imageModel.primary')}</label>
                        <select
                            id="image-model-select"
                            value={settings.imageModel}
                            onChange={(e) => settings.setImageModel(e.target.value)}
                            className="w-full bg-gray-700 border border-gray-500 rounded-md p-2 text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none transition"
                        >
                           {imageModelOptions.map(opt => <option key={opt.id} value={opt.id}>{opt.name}</option>)}
                        </select>
                    </div>
                     <div>
                        <label htmlFor="image-edit-model-select" className="block text-sm text-gray-300 mb-2 mt-2">{t('suite.settings.imageModel.edit')}</label>
                        <select
                            id="image-edit-model-select"
                            value={settings.imageEditModel}
                            onChange={(e) => settings.setImageEditModel(e.target.value)}
                            className="w-full bg-gray-700 border border-gray-500 rounded-md p-2 text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none transition"
                        >
                           {imageModelOptions.map(opt => <option key={opt.id} value={opt.id}>{opt.name}</option>)}
                        </select>
                    </div>
                    <div>
                        <label htmlFor="video-model-select" className="block text-sm text-gray-300 mb-2 mt-2">{t('suite.settings.videoModel.primary')}</label>
                        <select
                            id="video-model-select"
                            value={settings.videoModel}
                            onChange={(e) => settings.setVideoModel(e.target.value)}
                            className="w-full bg-gray-700 border border-gray-500 rounded-md p-2 text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none transition"
                        >
                           {videoModelOptions.map(opt => <option key={opt.id} value={opt.id}>{opt.name}</option>)}
                        </select>
                    </div>
                </SettingsGroup>

                <SettingsGroup title={t('suite.settings.audioGenerationModels')}>
                    <div>
                        <label htmlFor="sfx-model-select" className="block text-sm text-gray-300 mb-2">{t('suite.settings.sfxModel')}</label>
                        <select
                            id="sfx-model-select"
                            value={settings.sfxModel}
                            onChange={(e) => settings.setSfxModel(e.target.value)}
                            className="w-full bg-gray-700 border border-gray-500 rounded-md p-2 text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none transition"
                        >
                           {audioModelOptions.map(opt => <option key={opt.id} value={opt.id}>{opt.name}</option>)}
                        </select>
                    </div>
                    <div>
                        <label htmlFor="tts-model-select" className="block text-sm text-gray-300 mb-2 mt-2">{t('suite.settings.tts')}</label>
                        <select
                            id="tts-model-select"
                            value={settings.ttsModel}
                            onChange={(e) => settings.setTtsModel(e.target.value)}
                            className="w-full bg-gray-700 border border-gray-500 rounded-md p-2 text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none transition"
                        >
                           {audioModelOptions.map(opt => <option key={opt.id} value={opt.id}>{opt.name}</option>)}
                        </select>
                    </div>
                    <div>
                        <label htmlFor="music-model-select" className="block text-sm text-gray-300 mb-2">{t('suite.settings.musicModel')}</label>
                        <select
                            id="music-model-select"
                            value={settings.musicModel}
                            onChange={(e) => settings.setMusicModel(e.target.value)}
                            className="w-full bg-gray-700 border border-gray-500 rounded-md p-2 text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none transition"
                        >
                           {musicModelOptions.map(opt => <option key={opt.id} value={opt.id}>{opt.name}</option>)}
                        </select>
                    </div>
                </SettingsGroup>

            </div>

        </div>
    </div>
  );
};

export default SettingsModal;