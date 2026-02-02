import React, { useState } from 'react';
import { Character, Item } from '../types';
import { useI18n } from '../context/i18n';
import ItemDetailModal from './ItemDetailModal';
import { SmallLoadingSpinner, RefreshIcon, PackageIcon } from './icons';

const StatBar: React.FC<{ value: number; max: number; colorClass: string; label: string }> = ({ value, max, colorClass, label }) => (
    <div className="w-full bg-gray-900/80 rounded-full h-1.5" title={`${label}: ${value}/${max}`}>
        <div className={`${colorClass} h-1.5 rounded-full`} style={{ width: `${Math.max(0, (value / max) * 100)}%` }}></div>
    </div>
);

const ItemIcon: React.FC<{ item: Item; iconUrl?: string }> = ({ item, iconUrl }) => {
    if (iconUrl) return <img src={iconUrl} alt={item.name} className="w-full h-full object-contain" />;
    switch (item.iconStatus) {
        case 'loading':
        case 'queued':
            return <SmallLoadingSpinner />;
        case 'error':
            return <RefreshIcon className="w-4 h-4 text-red-400" />;
        case 'pending':
        default:
            return <PackageIcon className="w-5 h-5 text-gray-500" />;
    }
};

const CharacterCard: React.FC<{ character: Character, onItemClick: (item: Item) => void, assetCache: Record<string, string> }> = ({ character, onItemClick, assetCache }) => {
    const { t } = useI18n();
    const inventory = character.inventory || [];
    const imageUrl = character.portraitAssetKey ? assetCache[character.portraitAssetKey] : undefined;
    
    return (
        <div className="bg-gray-900/50 p-2 rounded-lg border border-gray-700 flex gap-3">
            <div className="w-16 h-16 rounded-md border-2 border-gray-600 bg-gray-900 flex-shrink-0 overflow-hidden" style={{ imageRendering: 'pixelated' }}>
                {imageUrl && <img src={imageUrl} alt={character.name} className="w-full h-full object-cover" />}
            </div>
            <div className="flex-1 min-w-0">
                <p className="font-bold text-gray-100 truncate">{character.name}</p>
                <div className="space-y-1 mt-1">
                    <StatBar value={character.stats.hp} max={character.stats.maxHp} colorClass="bg-red-500" label="HP" />
                    <StatBar value={character.stats.mp} max={character.stats.maxMp} colorClass="bg-blue-500" label="MP" />
                    <StatBar value={character.stats.stamina} max={character.stats.maxStamina} colorClass="bg-green-500" label="SP" />
                </div>
                 <div className="mt-2 flex flex-wrap gap-1">
                    {inventory.slice(0, 4).map(item => (
                         <button 
                            key={item.id}
                            onClick={() => onItemClick(item)}
                            className="w-6 h-6 bg-gray-800 rounded border border-gray-600 flex items-center justify-center text-sm p-0.5" 
                            title={`${item.name} (x${item.quantity})`}
                            aria-label={t('game.itemDetail.viewItemDetails', { itemName: item.name })}
                            style={{ imageRendering: 'pixelated' }}
                         >
                            <ItemIcon item={item} iconUrl={item.iconAssetKey ? assetCache[item.iconAssetKey] : undefined} />
                         </button>
                    ))}
                    {inventory.length > 4 && <div className="text-xs text-gray-500 self-end">...</div>}
                </div>
            </div>
        </div>
    );
};

interface PartyTabProps {
  characters: Character[];
  assetCache: Record<string, string>;
}

const PartyTab: React.FC<PartyTabProps> = ({ characters, assetCache }) => {
    const { t } = useI18n();
    const [modalItem, setModalItem] = useState<Item | null>(null);
    const aiCharacters = characters.filter(c => c.isAI);

    if (aiCharacters.length === 0) return <p className="text-center text-gray-500 italic">{t('game.party.noCompanions')}</p>;

    return (
        <>
            {modalItem && <ItemDetailModal item={modalItem} onClose={() => setModalItem(null)} assetCache={assetCache} />}
            <div className="space-y-3">
                {aiCharacters.map(char => <CharacterCard key={char.name} character={char} onItemClick={setModalItem} assetCache={assetCache} />)}
            </div>
        </>
    );
};

export default PartyTab;