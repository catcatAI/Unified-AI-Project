import React, { createContext, useContext, ReactNode, useMemo } from 'react';
import useLocalStorage from '../hooks/useLocalStorage';
import { Settings } from '../types';

interface SettingsContextType extends Settings {
  setLocale: (locale: 'en' | 'zh') => void;
  setBgmVolume: (volume: number) => void;
  setSfxVolume: (volume: number) => void;
  setEnablePortraits: (enabled: boolean) => void;
  setEnableTts: (enabled: boolean) => void;
  setEnableMapImages: (enabled: boolean) => void;
  setEnableItemIcons: (enabled: boolean) => void;
  setEnableLocationImages: (enabled: boolean) => void;
  setEnableSfx: (enabled: boolean) => void;
  setEnableVoiceInput: (enabled: boolean) => void;
  setFollowPlot: (enabled: boolean) => void;
  setPrimaryTextModel: (model: string) => void;
  setFallbackTextModel: (model: string) => void;
  setImageModel: (model: string) => void;
  setImageEditModel: (model: string) => void;
  setVideoModel: (model: string) => void;
  setSfxModel: (model: string) => void;
  setTtsModel: (model: string) => void;
  setMusicModel: (model: string) => void;
  setAiCreativity: (creativity: number) => void;
  setQteDifficulty: (difficulty: 'easy' | 'normal' | 'hard') => void;
  setDisableQteTimer: (enabled: boolean) => void;
  setEnableMvalGen: (enabled: boolean) => void;
  setRoundRobinInitiative: (enabled: boolean) => void;
  setCharacterAgency: (enabled: boolean) => void;
  setEnableDragAndDrop: (enabled: boolean) => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const SettingsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [locale, setLocale] = useLocalStorage<'en' | 'zh'>('settings-locale', 'zh');
  const [bgmVolume, setBgmVolume] = useLocalStorage<number>('settings-bgmVolume', 0.2);
  const [sfxVolume, setSfxVolume] = useLocalStorage<number>('settings-sfxVolume', 1.0);
  const [enablePortraits, setEnablePortraits] = useLocalStorage<boolean>('settings-enablePortraits', true);
  const [enableTts, setEnableTts] = useLocalStorage<boolean>('settings-enableTts', true);
  const [enableMapImages, setEnableMapImages] = useLocalStorage<boolean>('settings-enableMapImages', true);
  const [enableItemIcons, setEnableItemIcons] = useLocalStorage<boolean>('settings-enableItemIcons', true);
  const [enableLocationImages, setEnableLocationImages] = useLocalStorage<boolean>('settings-enableLocationImages', true);
  const [enableSfx, setEnableSfx] = useLocalStorage<boolean>('settings-enableSfx', true);
  const [enableVoiceInput, setEnableVoiceInput] = useLocalStorage<boolean>('settings-enableVoiceInput', true);
  const [followPlot, setFollowPlot] = useLocalStorage<boolean>('settings-followPlot', true);
  const [primaryTextModel, setPrimaryTextModel] = useLocalStorage<string>('settings-primaryTextModel', 'gemini-2.5-flash');
  const [fallbackTextModel, setFallbackTextModel] = useLocalStorage<string>('settings-fallbackTextModel', 'gemini-flash-latest');
  const [imageModel, setImageModel] = useLocalStorage<string>('settings-imageModel', 'imagen-4.0-generate-001');
  const [imageEditModel, setImageEditModel] = useLocalStorage<string>('settings-imageEditModel', 'gemini-2.5-flash-image');
  const [videoModel, setVideoModel] = useLocalStorage<string>('settings-videoModel', 'veo-3.1-fast-generate-preview');
  const [sfxModel, setSfxModel] = useLocalStorage<string>('settings-sfxModel', 'gemini-2.5-flash-preview-tts');
  const [ttsModel, setTtsModel] = useLocalStorage<string>('settings-ttsModel', 'gemini-2.5-flash-preview-tts');
  const [musicModel, setMusicModel] = useLocalStorage<string>('settings-musicModel', 'simulated');
  const [aiCreativity, setAiCreativity] = useLocalStorage<number>('settings-aiCreativity', 0.8);
  const [qteDifficulty, setQteDifficulty] = useLocalStorage<'easy' | 'normal' | 'hard'>('settings-qteDifficulty', 'normal');
  const [disableQteTimer, setDisableQteTimer] = useLocalStorage<boolean>('settings-disableQteTimer', false);
  const [enableMvalGen, setEnableMvalGen] = useLocalStorage<boolean>('settings-enableMvalGen', false);
  const [roundRobinInitiative, setRoundRobinInitiative] = useLocalStorage<boolean>('settings-roundRobinInitiative', false);
  const [characterAgency, setCharacterAgency] = useLocalStorage<boolean>('settings-characterAgency', false);
  const [enableDragAndDrop, setEnableDragAndDrop] = useLocalStorage<boolean>('settings-enableDragAndDrop', true);


  const value: SettingsContextType = useMemo(() => ({
    locale, setLocale, bgmVolume, setBgmVolume, sfxVolume, setSfxVolume, enablePortraits, setEnablePortraits, enableTts, setEnableTts, enableMapImages, setEnableMapImages, enableItemIcons, setEnableItemIcons, enableLocationImages, setEnableLocationImages, enableSfx, setEnableSfx, enableVoiceInput, setEnableVoiceInput, followPlot, setFollowPlot, primaryTextModel, setPrimaryTextModel, fallbackTextModel, setFallbackTextModel, imageModel, setImageModel, imageEditModel, setImageEditModel, videoModel, setVideoModel, sfxModel, setSfxModel, ttsModel, setTtsModel, musicModel, setMusicModel, aiCreativity, setAiCreativity, qteDifficulty, setQteDifficulty, disableQteTimer, setDisableQteTimer, enableMvalGen, setEnableMvalGen, roundRobinInitiative, setRoundRobinInitiative, characterAgency, setCharacterAgency, enableDragAndDrop, setEnableDragAndDrop,
  }), [
      locale, bgmVolume, sfxVolume, enablePortraits, enableTts, enableMapImages,
      enableItemIcons, enableLocationImages, enableSfx, enableVoiceInput, followPlot,
      primaryTextModel, fallbackTextModel, imageModel, imageEditModel, videoModel,
      sfxModel, ttsModel, musicModel, aiCreativity, qteDifficulty, disableQteTimer,
      enableMvalGen, roundRobinInitiative, characterAgency, enableDragAndDrop,
      setLocale, setBgmVolume, setSfxVolume, setEnablePortraits, setEnableTts,
      setEnableMapImages, setEnableItemIcons, setEnableLocationImages, setEnableSfx,
      setEnableVoiceInput, setFollowPlot, setPrimaryTextModel, setFallbackTextModel,
      setImageModel, setImageEditModel, setVideoModel, setSfxModel, setTtsModel,
      setMusicModel, setAiCreativity, setQteDifficulty, setDisableQteTimer,
      setEnableMvalGen, setRoundRobinInitiative, setCharacterAgency, setEnableDragAndDrop
  ]);

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = (): SettingsContextType => {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};
