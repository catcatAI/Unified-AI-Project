import React from 'react';
import { FullscreenEnterIcon, FullscreenExitIcon } from './icons';
import { useI18n } from '../context/i18n';

interface FullscreenButtonProps {
    isFullscreen: boolean;
    toggleFullscreen: () => void;
}

const FullscreenButton: React.FC<FullscreenButtonProps> = ({ isFullscreen, toggleFullscreen }) => {
    const { t } = useI18n();
    const label = isFullscreen ? t('fullscreen.exit') : t('fullscreen.enter');
    return (
        <button
            onClick={toggleFullscreen}
            className="p-2 rounded-md text-gray-200 bg-gray-900/40 hover:bg-gray-800/60 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-400"
            aria-label={label}
            title={label}
        >
            {isFullscreen ? (
                <FullscreenExitIcon className="w-5 h-5" />
            ) : (
                <FullscreenEnterIcon className="w-5 h-5" />
            )}
        </button>
    );
};

export default FullscreenButton;
