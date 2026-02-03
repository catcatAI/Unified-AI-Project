import React, { useState, useCallback } from 'react';
import { GameState, Item, InventoryContainer, Task, Message, Character, PlayerAction } from '../types';
import { useI18n } from '../context/i18n';
import StatusTab from './StatusTab';
import PartyTab from './PartyTab';
import BagTab from './BagTab';
export type { DraggableItemData } from './BagTab';
import { DraggableItemData } from './BagTab';
import CraftingTab from './CraftingTab';
import AssetsTab from './AssetsTab';
import GameControls from './GameControls';
import { CloseIcon } from './icons';
import ItemDetailModal from './ItemDetailModal';
import TaskQueue from './TaskQueue';
import MessageLog from './MessageLog';
import { PlayerInput } from './PlayerInput';
import { useGameContext } from './context/GameContext';

interface SidePanelProps {
    playerCharacter: Character;
    onItemMove: (item: Item, quantity: number, from: InventoryContainer, to: InventoryContainer) => void;
    selectedItemData: DraggableItemData | null;
    onSelectItem: (data: DraggableItemData | null) => void;
    isAutoPlaying: boolean;
    onToggleAutoPlay: () => void;
    isMobile?: boolean;
    onClose?: () => void;
}

type Tab = 'status' | 'party' | 'bag' | 'craft' | 'assets' | 'log';

const SidePanel: React.FC<SidePanelProps> = (props) => {
    const { t } = useI18n();
    const { 
        gameState, 
        dispatch,
        isBusy, 
        tasks,
        onSaveGame,
        onImportFileToCodex,
        onRestartGame,
        onNavigateToCodex,
        onPlayerAction,
    } = useGameContext();
    
    const { playerCharacter, onItemMove, selectedItemData, onSelectItem, isAutoPlaying, onToggleAutoPlay } = props;
    const { assetCache, difficulty, characters, partyStash, location, vehicles, realEstate, mapAssetKey, locationItems, knownLocations, gameStyle } = gameState;

    const [activeTab, setActiveTab] = useState<Tab>('status');
    const [modalItem, setModalItem] = useState<Item | null>(null);
    
    let tabs: { id: Tab, label: string }[] = [
        { id: 'status', label: t('game.tabStatus') },
    ];
    
    if (difficulty.showAiParty) tabs.push({ id: 'party', label: t('game.tabParty') });
    tabs.push({ id: 'bag', label: t('game.tabInventory') });
    tabs.push({ id: 'craft', label: t('game.tabCraft') });
    tabs.push({ id: 'assets', label: t('game.tabAssets') });
    if (gameStyle === 'sandbox' && props.isMobile) {
        tabs.push({ id: 'log', label: t('game.mobile.log') });
    }
    
    const handleAddCraftingIngredient = useCallback((item: Item) => dispatch({ type: 'ADD_CRAFTING_INGREDIENT', payload: item }), [dispatch]);
    const handleRemoveCraftingIngredient = useCallback((item: Item) => dispatch({ type: 'REMOVE_CRAFTING_INGREDIENT', payload: { itemId: item.id } }), [dispatch]);
    const handleClearCraftingIngredients = useCallback(() => dispatch({ type: 'CLEAR_CRAFTING_INGREDIENTS' }), [dispatch]);
    const handleTravel = useCallback((locationName: string) => onPlayerAction(t('game.world.travelTo', { location: locationName }), null), [onPlayerAction, t]);

    return (
        <>
            {modalItem && (
                <ItemDetailModal 
                    item={modalItem} 
                    onClose={() => setModalItem(null)} 
                    assetCache={assetCache}
                />
            )}
            <div className="bg-gray-800/80 backdrop-blur-sm rounded-lg border-2 border-gray-700 shadow-lg flex flex-col h-full overflow-hidden">
                <div className="flex-shrink-0 border-b-2 border-gray-700 p-1 flex items-center">
                    <div role="tablist" aria-label="Game Information Tabs" className="flex bg-gray-900/50 rounded-md p-1 gap-1 flex-grow overflow-x-auto scrollbar-thin">
                        {tabs.map(tab => (
                            <button
                                key={tab.id}
                                role="tab"
                                id={`${tab.id}-tab`}
                                aria-selected={activeTab === tab.id}
                                aria-controls={`${tab.id}-panel`}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex-shrink-0 text-center text-sm font-semibold py-1.5 px-3 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-indigo-500 ${
                                    activeTab === tab.id ? 'bg-indigo-600 text-white' : 'text-gray-300 hover:bg-gray-700/50'
                                }`}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>
                    {props.isMobile && (
                        <button onClick={props.onClose} className="ml-2 p-2 text-gray-400 hover:text-white" aria-label={t('game.ariaLabels.closeModal')}>
                            <CloseIcon className="w-6 h-6" />
                        </button>
                    )}
                </div>
                
                <div className="flex-1 min-h-0">
                    <div className="h-full overflow-y-auto p-3 space-y-4 scrollbar-thin">
                        <div role="tabpanel" id="status-panel" hidden={activeTab !== 'status'}>
                            <StatusTab character={playerCharacter} />
                        </div>
                         {difficulty.showAiParty && <div role="tabpanel" id="party-panel" hidden={activeTab !== 'party'}>
                            <PartyTab characters={characters} assetCache={assetCache} />
                        </div>}
                        <div role="tabpanel" id="bag-panel" hidden={activeTab !== 'bag'}>
                            <BagTab 
                                playerInventory={playerCharacter.inventory}
                                partyStash={partyStash}
                                locationItems={locationItems}
                                vehicles={vehicles}
                                characters={characters}
                                onItemClick={setModalItem}
                                onItemMove={onItemMove}
                                assetCache={assetCache}
                                selectedItemData={selectedItemData}
                                onSelectItem={onSelectItem}
                            />
                        </div>
                        <div role="tabpanel" id="craft-panel" hidden={activeTab !== 'craft'}>
                            <CraftingTab
                                playerInventory={playerCharacter.inventory}
                                ingredients={gameState.craftingIngredients}
                                onAddIngredient={handleAddCraftingIngredient}
                                onRemoveIngredient={handleRemoveCraftingIngredient}
                                onClearIngredients={handleClearCraftingIngredients}
                            />
                        </div>
                        <div role="tabpanel" id="assets-panel" hidden={activeTab !== 'assets'}>
                            <AssetsTab 
                                location={location} 
                                onTravel={handleTravel}
                                vehicles={vehicles}
                                realEstate={realEstate}
                                difficulty={difficulty}
                                mapAssetKey={mapAssetKey}
                                assetCache={assetCache}
                                knownLocations={knownLocations}
                            />
                        </div>
                        {gameStyle === 'sandbox' && props.isMobile && (
                             <div role="tabpanel" id="log-panel" className={activeTab === 'log' ? 'flex flex-col h-full' : 'hidden'}>
                                <div className="flex-1 min-h-0">
                                    <MessageLog playerCharacterName={playerCharacter.name} />
                                </div>
                                <div className="flex-shrink-0 mt-2 border-t border-gray-700">
                                   <PlayerInput 
                                     onPlayerAction={(action) => onPlayerAction(action, null)} 
                                     suggestedActions={[]} 
                                     attachedAsset={null}
                                     onAttachAsset={() => {}}
                                     onClearAttachment={() => {}}
                                   />
                                </div>
                            </div>
                        )}
                    </div>
                </div>
                
                <div className="flex-shrink-0 border-t-2 border-gray-700 p-3 space-y-3">
                    <TaskQueue tasks={tasks} isBusy={isBusy} />
                    <GameControls 
                        onSaveGame={onSaveGame} 
                        onImportFileToCodex={onImportFileToCodex}
                        onRestartGame={onRestartGame}
                        onNavigateToCodex={onNavigateToCodex}
                        onToggleAutoPlay={onToggleAutoPlay}
                        isAutoPlaying={isAutoPlaying}
                        isBusy={isBusy}
                    />
                </div>
            </div>
        </>
    );
};

export default SidePanel;