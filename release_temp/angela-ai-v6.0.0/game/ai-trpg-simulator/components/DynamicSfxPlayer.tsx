import React from 'react';
import { Sfx } from '../types';
import { useI18n } from '../context/i18n';
import { PlayIcon, SmallLoadingSpinner, RefreshIcon } from './icons';
import { useSettings } from '../context/settings';

interface DynamicSfxPlayerProps {
    sfx: Sfx;
    messageId: string;
    assetCache: Record<string, string>;
}

const DynamicSfxPlayer: React.FC<DynamicSfxPlayerProps> = ({ sfx, messageId, assetCache }) => {
    const { t } = useI18n();
    const { sfxVolume } = useSettings();
    const audioUrl = sfx.assetKey ? assetCache[sfx.assetKey] : undefined;

    const playSound = () => {
        if (audioUrl && sfxVolume > 0) {
            const audio = new Audio(audioUrl);
            audio.volume = sfxVolume;
            audio.play().catch(e => console.error("Error playing dynamic SFX:", e));
        }
    };

    const renderStatus = () => {
        switch (sfx.status) {
            case 'done':
                return (
                    <button 
                        onClick={playSound}
                        className="inline-flex items-center gap-1 bg-gray-700/50 hover:bg-gray-700 text-gray-300 px-1.5 py-0.5 rounded mx-1 text-xs"
                        title={t('game.sfx.play', { prompt: sfx.prompt })}
                    >
                        <PlayIcon className="w-2.5 h-2.5" />
                        <span className="italic truncate max-w-[200px]">{sfx.prompt}</span>
                    </button>
                );
            case 'loading':
            case 'queued':
                return (
                     <div className="inline-flex items-center gap-1 bg-gray-700/50 text-gray-400 px-1.5 py-0.5 rounded mx-1 text-xs">
                        <SmallLoadingSpinner />
                        <span className="italic truncate max-w-[200px]">{sfx.prompt}</span>
                    </div>
                );
            case 'error':
                 return (
                     <div className="inline-flex items-center gap-1 bg-red-900/50 text-red-400 px-1.5 py-0.5 rounded mx-1 text-xs">
                        <RefreshIcon className="w-2.5 h-2.5" />
                        <span className="italic truncate max-w-[200px]">{sfx.prompt}</span>
                    </div>
                );
            default:
                return null;
        }
    }

    return (
        <div className="my-2">
            {renderStatus()}
        </div>
    );
};

export default DynamicSfxPlayer;