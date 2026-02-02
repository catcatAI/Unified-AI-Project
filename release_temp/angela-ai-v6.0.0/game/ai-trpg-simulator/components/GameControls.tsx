import React, { useRef, useState, useEffect } from 'react';
import { useI18n } from '../context/i18n';
import { useSettings } from '../context/settings';
import { MusicNoteIcon, MusicOffIcon, VolumeUpIcon, VolumeOffIcon, SaveIcon, UploadIcon, RefreshIcon, BookIcon, PlayIcon } from './icons';

interface GameControlsProps {
    onSaveGame: () => void;
    onImportFileToCodex: (file: File) => void;
    onRestartGame: () => void;
    onNavigateToCodex: () => void;
    onToggleAutoPlay: () => void;
    isAutoPlaying: boolean;
    isBusy: boolean;
}

const ControlButton: React.FC<{onClick: () => void; children: React.ReactNode; disabled?: boolean; 'aria-pressed'?: boolean, className?: string}> = ({ onClick, children, disabled = false, className, ...props }) => (
    <button
        onClick={onClick}
        disabled={disabled}
        className={`w-full text-left bg-gray-700 hover:bg-gray-600 text-white font-semibold py-2 px-4 rounded-md transition-colors flex items-center gap-3 disabled:bg-gray-700/50 disabled:text-gray-500 disabled:cursor-not-allowed ${className}`}
        {...props}
    >
        {children}
    </button>
);


const GameControls: React.FC<GameControlsProps> = ({ onSaveGame, onImportFileToCodex, onRestartGame, onNavigateToCodex, onToggleAutoPlay, isAutoPlaying, isBusy }) => {
    const { t } = useI18n();
    const settings = useSettings();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [lastBgmVolume, setLastBgmVolume] = useState(settings.bgmVolume);
    const [lastSfxVolume, setLastSfxVolume] = useState(settings.sfxVolume);

    useEffect(() => {
        if (settings.bgmVolume > 0) setLastBgmVolume(settings.bgmVolume);
    }, [settings.bgmVolume]);

    useEffect(() => {
        if (settings.sfxVolume > 0) setLastSfxVolume(settings.sfxVolume);
    }, [settings.sfxVolume]);

    const handleImportClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            onImportFileToCodex(file);
            if (event.target) {
                event.target.value = '';
            }
        }
    };
    
    const isBgmOn = settings.bgmVolume > 0;
    const isSfxOn = settings.sfxVolume > 0;

    const toggleBgm = () => {
        settings.setBgmVolume(isBgmOn ? 0 : lastBgmVolume > 0 ? lastBgmVolume : 0.2);
    };

    const toggleSfx = () => {
        settings.setSfxVolume(isSfxOn ? 0 : lastSfxVolume > 0 ? lastSfxVolume : 1.0);
    };


    return (
        <div>
            <h2 className="text-lg font-bold text-gray-300 border-b-2 border-gray-700 pb-2 mb-3">{t('game.controls.title')}</h2>
            <div className="bg-gray-800/50 p-3 rounded-lg border border-gray-700 space-y-2">
                <ControlButton onClick={toggleBgm} aria-pressed={isBgmOn} aria-label={isBgmOn ? t('game.ariaLabels.toggleBgmOff') : t('game.ariaLabels.toggleBgmOn')}>
                    {isBgmOn ? <MusicNoteIcon className="w-5 h-5 text-green-400" /> : <MusicOffIcon className="w-5 h-5 text-red-400" />}
                    <span>{t('game.backgroundMusic')}</span>
                </ControlButton>
                 <ControlButton onClick={toggleSfx} aria-pressed={isSfxOn} aria-label={isSfxOn ? t('game.ariaLabels.toggleSfxOff') : t('game.ariaLabels.toggleSfxOn')}>
                    {isSfxOn ? <VolumeUpIcon className="w-5 h-5 text-green-400" /> : <VolumeOffIcon className="w-5 h-5 text-red-400" />}
                    <span>{t('game.soundEffects')}</span>
                </ControlButton>
                <div className="pt-2 border-t border-gray-700/50 space-y-2">
                    <ControlButton 
                        onClick={onToggleAutoPlay} 
                        disabled={isBusy && !isAutoPlaying}
                        className={isAutoPlaying ? 'bg-green-600/50 hover:bg-green-700/50' : ''}
                    >
                        <PlayIcon className={`w-5 h-5 ${isAutoPlaying ? 'animate-pulse' : ''}`} />
                        {isAutoPlaying ? t('game.controls.autoPlayStop') : t('game.controls.autoPlayStart')}
                    </ControlButton>
                    <ControlButton onClick={onSaveGame} disabled={isBusy}><SaveIcon className="w-5 h-5" />{t('game.controls.save')}</ControlButton>
                    <ControlButton onClick={onNavigateToCodex} disabled={isBusy}><BookIcon className="w-5 h-5" />{t('game.controls.load')}</ControlButton>
                    <ControlButton onClick={handleImportClick} disabled={isBusy}><UploadIcon className="w-5 h-5" />{t('codex.importButton')}</ControlButton>
                    <ControlButton onClick={onRestartGame} disabled={isBusy}><RefreshIcon className="w-5 h-5" />{t('game.controls.restart')}</ControlButton>
                </div>

                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    accept=".json"
                    className="hidden"
                />
            </div>
        </div>
    );
};

export default GameControls;