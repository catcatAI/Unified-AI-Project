import React, { useState } from 'react';
import { Item, InventoryContainer, Vehicle, Character } from '../types';
import { useI18n } from '../context/i18n';
import { useSettings } from '../context/settings';
import CollapsiblePanel from './CollapsiblePanel';
import QuantityModal from './QuantityModal';
import { SmallLoadingSpinner, RefreshIcon, InfoIcon, PackageIcon } from './icons';

export interface DraggableItemData {
    item: Item;
    source: InventoryContainer;
}

interface MoveAction {
    item: Item;
    from: InventoryContainer;
    to: InventoryContainer;
}

interface BagTabProps {
  playerInventory: Item[];
  partyStash: Item[];
  locationItems: Item[];
  vehicles: Vehicle[];
  characters: Character[];
  onItemClick: (item: Item) => void;
  onItemMove: (item: Item, quantity: number, from: InventoryContainer, to: InventoryContainer) => void;
  assetCache: Record<string, string>;
  selectedItemData: DraggableItemData | null;
  onSelectItem: (data: DraggableItemData | null) => void;
}

const BagItem: React.FC<{ 
    item: Item; 
    onSelect: () => void;
    onViewDetails: () => void;
    onDragStart: (e: React.DragEvent<HTMLButtonElement>) => void; 
    isSelected: boolean; 
    iconUrl?: string;
    isDraggable: boolean;
}> = ({ item, onSelect, onViewDetails, onDragStart, isSelected, iconUrl, isDraggable }) => {
    const { t } = useI18n();

    const renderIcon = () => {
        if (iconUrl) return <img src={iconUrl} alt={item.name} className="w-full h-full object-contain" />;
        switch (item.iconStatus) {
            case 'loading':
            case 'queued':
                return <SmallLoadingSpinner />;
            case 'error':
                return <RefreshIcon className="w-5 h-5 text-red-400" />;
            case 'pending':
            default:
                // Intelligent fallback placeholder
                return <PackageIcon className="w-6 h-6 text-gray-500" />;
        }
    };

    return (
        <div className="flex items-center gap-2 group">
            <button
                draggable={isDraggable}
                onDragStart={isDraggable ? onDragStart : undefined}
                onClick={onSelect}
                aria-label={item.name}
                aria-pressed={isSelected}
                className={`flex-1 text-left p-2 rounded-md transition-colors flex items-center gap-3 ${isSelected ? 'bg-indigo-800/50 ring-2 ring-indigo-500' : 'bg-gray-800/50 hover:bg-gray-700/80'}`}
            >
                <div className="w-8 h-8 bg-gray-900 rounded-md flex items-center justify-center flex-shrink-0 p-1" style={{ imageRendering: 'pixelated' }}>
                    {renderIcon()}
                </div>
                <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-200 truncate text-sm">{item.name}</p>
                    <p className="text-xs text-gray-400">{t('common.quantity')}: {item.quantity}</p>
                </div>
            </button>
            <button 
                onClick={onViewDetails} 
                className="p-2 rounded-md text-gray-500 hover:text-white hover:bg-gray-700/50 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity"
                aria-label={t('game.itemDetail.viewItemDetails', { itemName: item.name })}
                title={t('game.itemDetail.viewItemDetails', { itemName: item.name })}
            >
                <InfoIcon className="w-5 h-5" />
            </button>
        </div>
    );
};

const InventoryPanelContent: React.FC<{
    items: Item[], 
    source: InventoryContainer, 
    onViewDetails: (item: Item) => void,
    onItemSelect: (item: Item, source: InventoryContainer) => void, 
    handleDragStart: (e: React.DragEvent<HTMLButtonElement>, data: DraggableItemData) => void,
    selectedItemData?: DraggableItemData | null;
    assetCache: Record<string, string>;
    isDraggable: boolean;
}> = ({items, source, onViewDetails, onItemSelect, handleDragStart, selectedItemData, assetCache, isDraggable}) => {
    const { t } = useI18n();
    const validItems = Array.isArray(items) ? items : [];
    if (validItems.length === 0) return <p className="text-center text-xs text-gray-500 italic p-4">{t('game.empty')}</p>;
    const sortedItems = [...validItems].sort((a, b) => a.name.localeCompare(b.name));
    return (
    <div className="space-y-1">
        {sortedItems.map(item => 
            <BagItem 
                key={item.id} 
                item={item} 
                onViewDetails={() => onViewDetails(item)}
                onSelect={() => onItemSelect(item, source)} 
                onDragStart={(e) => handleDragStart(e, { item, source })} 
                isSelected={selectedItemData?.item.id === item.id} 
                iconUrl={item.iconAssetKey ? assetCache[item.iconAssetKey] : undefined}
                isDraggable={isDraggable}
            />
        )}
    </div>);
};


const BagTab: React.FC<BagTabProps> = ({ playerInventory, partyStash, locationItems, vehicles, characters, onItemClick, onItemMove, assetCache, selectedItemData, onSelectItem }) => {
  const { t } = useI18n();
  const settings = useSettings();
  const [moveAction, setMoveAction] = useState<MoveAction | null>(null);

  const isDifferentContainer = (source: InventoryContainer, target: InventoryContainer): boolean => JSON.stringify(source) !== JSON.stringify(target);
  
  const initiateMove = (item: Item, from: InventoryContainer, to: InventoryContainer) => {
    if (item.quantity > 1) {
        setMoveAction({ item, from, to });
    } else {
        onItemMove(item, 1, from, to);
    }
    onSelectItem(null);
  };
  
  const handleDragStart = (e: React.DragEvent<HTMLButtonElement>, data: DraggableItemData) => {
    if (!settings.enableDragAndDrop) {
        e.preventDefault();
        return;
    }
    e.dataTransfer.setData("application/json", JSON.stringify(data));
    onSelectItem(null); // Clear keyboard selection when drag starts
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>, to: InventoryContainer) => {
    if (!settings.enableDragAndDrop) return;
    e.preventDefault();
    try {
      const data: DraggableItemData = JSON.parse(e.dataTransfer.getData("application/json"));
      if (isDifferentContainer(data.source, to)) {
        initiateMove(data.item, data.source, to);
      }
    } catch (error) { console.error("Failed to parse dropped item data", error); }
  };

  const handleItemSelect = (item: Item, source: InventoryContainer) => {
    if (selectedItemData?.item.id === item.id) {
        onSelectItem(null); // Deselect if clicking the same item
    } else {
        onSelectItem({ item, source }); // Select the clicked item
    }
  };

  const handlePanelHeaderClick = (targetContainer: InventoryContainer): boolean => {
    if (selectedItemData && isDifferentContainer(selectedItemData.source, targetContainer)) {
      initiateMove(selectedItemData.item, selectedItemData.source, targetContainer);
      return true; // An action was taken
    }
    return false; // No action was taken, so the panel should just toggle
  };
  
  const playerContainer: InventoryContainer = { type: 'player' };
  const groundContainer: InventoryContainer = { type: 'ground' };
  const stashContainer: InventoryContainer = { type: 'stash' };
  const sortedCharacters = [...characters.filter(c => c.isAI)].sort((a, b) => a.name.localeCompare(b.name));
  const sortedVehicles = [...vehicles].sort((a, b) => a.name.localeCompare(b.name));

  return (
    <>
        {moveAction && <QuantityModal item={moveAction.item} onClose={() => setMoveAction(null)} onConfirm={(quantity) => { onItemMove(moveAction.item, quantity, moveAction.from, moveAction.to); setMoveAction(null); }} />}
        <div className="space-y-3">
            {selectedItemData && (
                <div className="p-2 bg-indigo-900/50 border border-indigo-700 rounded-md text-center text-xs text-indigo-200 animate-pulse">
                    {t('game.inventory.itemSelected', { itemName: selectedItemData.item.name })}
                </div>
            )}
            <CollapsiblePanel title={t('game.inventory.ground')} onDrop={(e) => handleDrop(e, groundContainer)} onClickHeader={() => handlePanelHeaderClick(groundContainer)} isDropTarget={!!selectedItemData && isDifferentContainer(selectedItemData.source, groundContainer)}>
                <InventoryPanelContent items={locationItems} source={groundContainer} onViewDetails={onItemClick} onItemSelect={handleItemSelect} handleDragStart={handleDragStart} selectedItemData={selectedItemData} assetCache={assetCache} isDraggable={settings.enableDragAndDrop}/>
            </CollapsiblePanel>
            <CollapsiblePanel title={t('game.inventory.player')} onDrop={(e) => handleDrop(e, playerContainer)} defaultOpen={true} onClickHeader={() => handlePanelHeaderClick(playerContainer)} isDropTarget={!!selectedItemData && isDifferentContainer(selectedItemData.source, playerContainer)}>
                <InventoryPanelContent items={playerInventory} source={playerContainer} onViewDetails={onItemClick} onItemSelect={handleItemSelect} handleDragStart={handleDragStart} selectedItemData={selectedItemData} assetCache={assetCache} isDraggable={settings.enableDragAndDrop}/>
            </CollapsiblePanel>
            <CollapsiblePanel title={t('game.inventory.stash')} onDrop={(e) => handleDrop(e, stashContainer)} onClickHeader={() => handlePanelHeaderClick(stashContainer)} isDropTarget={!!selectedItemData && isDifferentContainer(selectedItemData.source, stashContainer)}>
                <InventoryPanelContent items={partyStash} source={stashContainer} onViewDetails={onItemClick} onItemSelect={handleItemSelect} handleDragStart={handleDragStart} selectedItemData={selectedItemData} assetCache={assetCache} isDraggable={settings.enableDragAndDrop}/>
            </CollapsiblePanel>
            {sortedCharacters.map(char => {
                const charContainer: InventoryContainer = { type: 'character', name: char.name };
                return (<CollapsiblePanel key={char.name} title={char.name} onDrop={(e) => handleDrop(e, charContainer)} onClickHeader={() => handlePanelHeaderClick(charContainer)} isDropTarget={!!selectedItemData && isDifferentContainer(selectedItemData.source, charContainer)}><InventoryPanelContent items={char.inventory} source={charContainer} onViewDetails={onItemClick} onItemSelect={handleItemSelect} handleDragStart={handleDragStart} selectedItemData={selectedItemData} assetCache={assetCache} isDraggable={settings.enableDragAndDrop} /></CollapsiblePanel>)
            })}
            {sortedVehicles.map(vehicle => {
                const vehicleContainer: InventoryContainer = { type: 'vehicle', id: vehicle.id };
                return (<CollapsiblePanel key={vehicle.id} title={t('game.inventory.vehicleCargo', { name: vehicle.name })} onDrop={(e) => handleDrop(e, vehicleContainer)} onClickHeader={() => handlePanelHeaderClick(vehicleContainer)} isDropTarget={!!selectedItemData && isDifferentContainer(selectedItemData.source, vehicleContainer)}><InventoryPanelContent items={vehicle.inventory} source={vehicleContainer} onViewDetails={onItemClick} onItemSelect={handleItemSelect} handleDragStart={handleDragStart} selectedItemData={selectedItemData} assetCache={assetCache} isDraggable={settings.enableDragAndDrop} /></CollapsiblePanel>)
            })}
        </div>
    </>
  );
};

export default BagTab;