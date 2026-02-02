import React, { useState, useRef } from 'react';
import { Item } from '../types';
import { useI18n } from '../context/i18n';
import { CloseIcon, SmallLoadingSpinner, RefreshIcon, PackageIcon } from './icons';
import { useGameContext } from './context/GameContext';

interface CraftingTabProps {
  playerInventory: Item[];
  ingredients: Item[];
  onAddIngredient: (item: Item) => void;
  onRemoveIngredient: (item: Item) => void;
  onClearIngredients: () => void;
}

const ItemIcon: React.FC<{ item: Item; iconUrl?: string }> = ({ item, iconUrl }) => {
    if (iconUrl) return <img src={iconUrl} alt={item.name} className="w-full h-full object-contain" />;
    switch (item.iconStatus) {
        case 'loading':
        case 'queued':
            return <SmallLoadingSpinner />;
        case 'error':
            return <RefreshIcon className="w-5 h-5 text-red-400" />;
        case 'pending':
        default:
            return <PackageIcon className="w-6 h-6 text-gray-500" />;
    }
};

const CraftingTab: React.FC<CraftingTabProps> = ({ 
    playerInventory, 
    ingredients,
    onAddIngredient,
    onRemoveIngredient,
    onClearIngredients
}) => {
    const { t } = useI18n();
    const { isBusy, onPlayerAction, gameState: { assetCache } } = useGameContext();
    const [craftingType, setCraftingType] = useState('alchemy');
    const debounceLock = useRef(false);

    const handleCraftAction = () => {
        if (ingredients.length === 0 || debounceLock.current || isBusy) return;
        debounceLock.current = true;
        const typeText = t(`game.crafting.types.${craftingType}`);
        const itemNames = ingredients.map(i => i.name).join(', ');
        onPlayerAction(t('game.crafting.action', { type: typeText, items: itemNames }), null);
        onClearIngredients();
        setTimeout(() => { debounceLock.current = false; }, 500);
    };

    const craftingTypes = ['alchemy', 'forging', 'processing'];
    const sortedInventory = [...(playerInventory || [])].sort((a, b) => a.name.localeCompare(b.name));

    return (
        <div className="flex flex-col gap-4">
            <div>
                <label htmlFor="crafting-type" className="block text-sm font-medium text-gray-300 mb-1">{t('game.crafting.selectType')}</label>
                <select id="crafting-type" value={craftingType} onChange={(e) => setCraftingType(e.target.value)} className="w-full bg-gray-900/50 border border-gray-600 rounded-lg p-2 text-gray-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                    {craftingTypes.map(type => <option key={type} value={type}>{t(`game.crafting.types.${type}`)}</option>)}
                </select>
            </div>
            <div className="p-2 rounded-lg border-2 border-dashed border-gray-600 bg-black/20 min-h-[80px]">
                {ingredients.length === 0 ? <div className="flex items-center justify-center h-full"><p className="text-sm text-gray-500 text-center">{t('game.crafting.dropPrompt')}</p></div>
                : <div className="grid grid-cols-4 gap-2">
                    {ingredients.map(item => (
                         <div key={item.id} className="relative group aspect-square">
                            <button onClick={() => onRemoveIngredient(item)} className="w-full h-full bg-gray-800 rounded-md flex items-center justify-center p-1 border-2 border-transparent group-hover:border-red-500" aria-label={`Remove ${item.name}`}>
                                <div className="w-8 h-8 flex-shrink-0" style={{ imageRendering: 'pixelated' }}><ItemIcon item={item} iconUrl={assetCache[`icon-${item.name.toLowerCase()}`]} /></div>
                                <div className="absolute -top-1.5 -right-1.5 bg-red-600 rounded-full p-0.5 opacity-0 group-hover:opacity-100"><CloseIcon className="w-3 h-3 text-white" /></div>
                            </button>
                        </div>
                    ))}
                  </div>
                }
            </div>
            <div className="flex flex-col">
                <h3 className="text-sm font-semibold text-gray-300 mb-2 flex-shrink-0">{t('game.crafting.inventoryTitle')}</h3>
                <div className="bg-gray-900/50 p-2 rounded-md border border-gray-700">
                    <div className="space-y-1">
                        {sortedInventory.length > 0 ? sortedInventory.map(item => (
                            <button key={item.id} onClick={() => onAddIngredient(item)} disabled={ingredients.some(i => i.id === item.id)} aria-label={t('game.crafting.addIngredient', { itemName: item.name })} className="w-full text-left p-1.5 rounded-md flex items-center gap-2 bg-gray-800/50 hover:bg-gray-700/80 disabled:opacity-40 disabled:cursor-not-allowed">
                                <div className="w-6 h-6 bg-gray-900 rounded-md flex items-center justify-center flex-shrink-0 p-0.5" style={{ imageRendering: 'pixelated' }}><ItemIcon item={item} iconUrl={assetCache[`icon-${item.name.toLowerCase()}`]} /></div>
                                <div className="flex-1 min-w-0"><p className="font-semibold text-gray-300 truncate text-xs">{item.name}</p></div>
                                <span className="text-xs text-gray-400 font-mono pr-1">x{item.quantity}</span>
                            </button>
                        )) : <p className="text-center text-xs text-gray-500 italic p-4">{t('game.inventoryEmpty')}</p>}
                    </div>
                </div>
            </div>
            <button onClick={handleCraftAction} disabled={ingredients.length === 0 || isBusy} className="w-full bg-indigo-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-indigo-700 disabled:bg-indigo-800/50 disabled:cursor-not-allowed text-lg flex-shrink-0 active:scale-95">
                {isBusy ? t('game.crafting.crafting') : t('game.crafting.button')}
            </button>
        </div>
    );
};

export default CraftingTab;