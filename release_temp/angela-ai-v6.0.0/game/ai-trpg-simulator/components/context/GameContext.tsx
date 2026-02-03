import React, { createContext, useContext } from 'react';
import { GameState, CombinedTrpgGameAction, Toast, PlayerAction, CodexAsset, CodexSaveAsset, Task } from '../../types';

interface GameContextType {
    gameState: GameState;
    dispatch: React.Dispatch<CombinedTrpgGameAction>;
    addToast: (message: string, type: Toast['type']) => void;
    isBusy: boolean;
    tasks: Task[];
    onGameStart: (newGameState: GameState) => void;
    onImportFileToCodex: (file: File) => Promise<void>;
    onLoadFromCodex: (asset: CodexAsset) => void;
    onReconstructSave: (saveAssetId: string) => Promise<void>;
    onSaveGame: () => void;
    onRestartGame: () => void;
    onGeneratePortrait: (characterName: string) => void;
    changeMusicByMood: (mood: string) => void;
    onPlayTtsRequest: (messageId: string) => void;
    playingMessageKey: string | null;
    onGenerateVideoClick: (messageId: string, prompt: string) => void;
    onPlayerAction: (action: PlayerAction, attachedAsset: CodexAsset | null) => void;
    onNavigateToCodex: () => void;
    isAutoPlaying: boolean;
    onToggleAutoPlay: () => void;
}

const GameContext = createContext<GameContextType | undefined>(undefined);

export const GameProvider = GameContext.Provider;

export const useGameContext = (): GameContextType => {
    const context = useContext(GameContext);
    if (context === undefined) {
        throw new Error('useGameContext must be used within a GameProvider');
    }
    return context;
};