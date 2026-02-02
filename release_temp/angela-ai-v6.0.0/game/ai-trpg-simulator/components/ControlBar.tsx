import React from 'react';
import { PlayerAction, CodexAsset } from '../types';
import { PlayerInput } from './PlayerInput';
import SandboxInterface from './SandboxInterface';
import CognitiveHud from './CognitiveHud';
import { MenuIcon } from './icons';
import FullscreenButton from './FullscreenButton';
import { useI18n } from '../context/i18n';
import { useGameContext } from './context/GameContext';

interface ControlBarProps {
    onPlayerAction: (action: PlayerAction) => void;
    onSandboxAction: (action: PlayerAction) => void;
    attachedAsset: CodexAsset | null;
    onAttachAsset: () => void;
    onClearAttachment: () => void;
    onOpenSidebar: () => void;
    isFullscreen: boolean;
    onToggleFullscreen: () => void;
}

const ControlBar: React.FC<ControlBarProps> = (props) => {
    const { t } = useI18n();
    const { gameState, isBusy } = useGameContext();
    const { onPlayerAction, onSandboxAction, onOpenSidebar, isFullscreen, onToggleFullscreen } = props;

    const renderMainInterface = () => {
        if (gameState.gameStyle === 'sandbox') {
            const contextualActionLabel = ''; // This can be expanded later
            return <SandboxInterface onAction={onSandboxAction} isBusy={isBusy} contextualActionLabel={contextualActionLabel} />;
        }
        return (
            <PlayerInput
                onPlayerAction={onPlayerAction}
                suggestedActions={gameState.suggestedActions}
                attachedAsset={props.attachedAsset}
                onAttachAsset={props.onAttachAsset}
                onClearAttachment={props.onClearAttachment}
            />
        );
    };

    return (
        <div className="flex-shrink-0 bg-gray-900/80 backdrop-blur-sm border-t border-gray-700 z-20">
            {/* Desktop Layout */}
            <div className="hidden lg:flex items-end justify-between p-2 gap-4">
                <div className="w-64 flex-shrink-0">
                    <CognitiveHud cognitiveState={gameState.cognitiveState} />
                </div>
                <div className="flex-1 min-w-0">
                    {renderMainInterface()}
                </div>
                 <div className="flex items-center gap-2">
                    <FullscreenButton isFullscreen={isFullscreen} toggleFullscreen={onToggleFullscreen} />
                    {!isFullscreen && (
                        <button onClick={onOpenSidebar} className="p-2 rounded-md text-gray-200 bg-gray-900/40 hover:bg-gray-800/60" aria-label={t('game.mobile.menu')}>
                            <MenuIcon className="w-5 h-5" />
                        </button>
                    )}
                </div>
            </div>

            {/* Mobile Layout */}
            <div className="lg:hidden flex flex-col">
                {/* Unified Top Bar for Mobile */}
                <div className="flex items-center p-2 gap-2 border-b border-gray-700/50">
                    <button onClick={onOpenSidebar} className="p-2 rounded-md text-gray-200 bg-gray-900/40 hover:bg-gray-800/60" aria-label={t('game.mobile.menu')}>
                        <MenuIcon className="w-5 h-5" />
                    </button>
                    <div className="flex-1">
                        <CognitiveHud cognitiveState={gameState.cognitiveState} />
                    </div>
                    <FullscreenButton isFullscreen={isFullscreen} toggleFullscreen={onToggleFullscreen} />
                </div>
                
                {/* Main Interaction Area */}
                {renderMainInterface()}
            </div>
        </div>
    );
};

export default ControlBar;