import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Character, PlayerAction, Item, InventoryContainer } from '../types';
import SidePanel, { DraggableItemData } from './SidePanel';
import GameView from './GameView';
import { useFullscreen } from '../hooks/useFullscreen';
import MessageLog from './MessageLog';
import ControlBar from './ControlBar';
import { useGameContext } from './context/GameContext';

interface GameScreenProps {
    playerCharacter: Character;
}

export const GameScreen: React.FC<GameScreenProps> = ({ playerCharacter }) => {
    const { gameState, dispatch, onPlayerAction, isAutoPlaying, onToggleAutoPlay } = useGameContext();

    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const mainContentRef = useRef<HTMLDivElement>(null);
    const { isFullscreen, toggleFullscreen } = useFullscreen(mainContentRef);
    
    // State local to GameScreen for UI management
    const [attachedAsset, setAttachedAsset] = useState<any | null>(null);
    const [selectedItemData, setSelectedItemData] = useState<DraggableItemData | null>(null);

    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape' && isSidebarOpen) {
                setIsSidebarOpen(false);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => {
            window.removeEventListener('keydown', handleKeyDown);
        };
    }, [isSidebarOpen]);
    
    // --- Callbacks derived from context dispatch ---
    const handlePlayerAction = useCallback((action: PlayerAction) => {
        onPlayerAction(action, attachedAsset);
        setAttachedAsset(null); // Clear attachment after action
    }, [onPlayerAction, attachedAsset]);

    const handleItemMove = useCallback((item: Item, quantity: number, from: InventoryContainer, to: InventoryContainer) => {
      dispatch({ type: 'MOVE_ITEM', payload: { item, quantity, from, to } });
    }, [dispatch]);
    
    return (
        <div className="flex-1 flex flex-col lg:flex-row h-full max-h-screen overflow-hidden relative bg-gray-900">
            {/* Main Content Area */}
            <div 
                ref={mainContentRef} 
                className="flex-1 flex flex-col min-h-0"
                aria-hidden={isSidebarOpen}
                // @ts-ignore - 'inert' is a new attribute and may not be in all TS definitions yet
                inert={isSidebarOpen ? "true" : undefined}
            >
                 <div className="flex-1 flex flex-col min-h-0 relative">
                    {gameState.gameStyle === 'sandbox' ? (
                        <GameView isFullscreen={isFullscreen} />
                    ) : (
                        <>
                            {/* Background Image */}
                            <div className="absolute inset-0 z-0">
                                <GameView isFullscreen={isFullscreen} isBackground={true} />
                            </div>
                            {/* Foreground Content */}
                            <div className="relative z-10 flex-1 flex flex-col min-h-0">
                                <MessageLog playerCharacterName={playerCharacter.name} />
                            </div>
                        </>
                    )}
                </div>
                
                <ControlBar
                    onPlayerAction={handlePlayerAction}
                    onSandboxAction={handlePlayerAction}
                    attachedAsset={attachedAsset}
                    onAttachAsset={() => { /* Need to implement Asset Picker logic here or lift state */ }}
                    onClearAttachment={() => setAttachedAsset(null)}
                    onOpenSidebar={() => setIsSidebarOpen(true)}
                    isFullscreen={isFullscreen}
                    onToggleFullscreen={toggleFullscreen}
                />
            </div>

            {/* Sidebar */}
            <aside className={`hidden lg:block w-full lg:w-[380px] flex-shrink-0 min-h-0 ${isFullscreen ? 'lg:hidden' : ''}`}>
                 <SidePanel 
                    playerCharacter={playerCharacter}
                    onItemMove={handleItemMove}
                    selectedItemData={selectedItemData}
                    onSelectItem={setSelectedItemData}
                    isAutoPlaying={isAutoPlaying}
                    onToggleAutoPlay={onToggleAutoPlay}
                 />
            </aside>
            
            {/* Mobile Sidebar Panel */}
            {isSidebarOpen && (
                <div className="lg:hidden fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" onClick={() => setIsSidebarOpen(false)}>
                    <div className="absolute inset-y-0 right-0 w-full max-w-sm h-full bg-gray-800 shadow-2xl" onClick={(e) => e.stopPropagation()}>
                        <SidePanel 
                            isMobile={true}
                            onClose={() => setIsSidebarOpen(false)}
                            playerCharacter={playerCharacter}
                            onItemMove={handleItemMove}
                            selectedItemData={selectedItemData}
                            onSelectItem={setSelectedItemData}
                            isAutoPlaying={isAutoPlaying}
                            onToggleAutoPlay={onToggleAutoPlay}
                         />
                    </div>
                </div>
            )}
        </div>
    );
};