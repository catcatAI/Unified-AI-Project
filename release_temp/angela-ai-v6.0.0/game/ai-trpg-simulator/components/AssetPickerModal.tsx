import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useI18n } from '../context/i18n';
import { useCodex } from '../context/codex';
import { CodexAsset, CodexCategory, CodexSaveAsset } from '../types';
import { useFocusTrap } from '../hooks/useFocusTrap';
import { CloseIcon, UserIcon, PackageIcon, MapIcon, TruckIcon, HomeIcon, ImageIcon, VideoIcon, SpeakerIcon, CubeIcon, SaveIcon } from './icons';
import { getAssetUrl } from '../services/utils';

interface AssetPickerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (asset: CodexAsset) => void;
  filter?: (asset: CodexAsset) => boolean;
  initialCategory?: CodexCategory;
}

const categoryIcons: Record<CodexCategory, React.ReactNode> = {
    character: <UserIcon className="w-4 h-4" />,
    item: <PackageIcon className="w-4 h-4" />,
    block: <CubeIcon className="w-4 h-4" />,
    location: <MapIcon className="w-4 h-4" />,
    vehicle: <TruckIcon className="w-4 h-4" />,
    realEstate: <HomeIcon className="w-4 h-4" />,
    image: <ImageIcon className="w-4 h-4" />,
    video: <VideoIcon className="w-4 h-4" />,
    audio: <SpeakerIcon className="w-4 h-4" />,
    model: <CubeIcon className="w-4 h-4" />,
    save: <SaveIcon className="w-4 h-4" />,
};

const MemoizedAssetButton = React.memo<{ asset: CodexAsset; onSelect: (asset: CodexAsset) => void }>(({ asset, onSelect }) => {
    const { t } = useI18n();
    
    const handleSelect = () => {
        onSelect(asset);
    };

    const displayName = asset.isPreset ? t(asset.name) : asset.name;

    return (
        <button
            onClick={handleSelect}
            className="bg-gray-900/50 p-2 rounded-lg border border-gray-700 flex flex-col group relative transition-all hover:shadow-lg hover:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
            <div className="aspect-square w-full bg-black/20 rounded-md flex items-center justify-center overflow-hidden">
                { getAssetUrl(asset) ? 
                    <img src={getAssetUrl(asset)} alt={displayName} className="w-full h-full object-cover" /> :
                    React.cloneElement(categoryIcons[asset.type] as React.ReactElement, { className: "w-8 h-8 text-gray-500" })
                }
            </div>
            <p className="font-semibold text-xs text-gray-200 truncate mt-2 text-center" title={displayName}>{displayName}</p>
        </button>
    );
});


const AssetPickerModal: React.FC<AssetPickerModalProps> = ({ isOpen, onClose, onSelect, filter, initialCategory }) => {
    const { t } = useI18n();
    const { codex } = useCodex();
    const [searchTerm, setSearchTerm] = useState('');
    const [activeCategory, setActiveCategory] = useState<CodexCategory>(initialCategory || 'character');
    const searchInputRef = useRef<HTMLInputElement>(null);
    const modalRef = useFocusTrap<HTMLDivElement>(searchInputRef);


    const getCategoryKey = (type: CodexCategory): keyof typeof codex => {
        switch (type) {
            case 'audio': return 'audio';
            case 'realEstate': return 'realEstate';
            case 'block': return 'blocks';
            case 'save': return 'saves';
            default: return `${type}s` as keyof typeof codex;
        }
    };
    
    const availableCategories = (Object.keys(categoryIcons) as CodexCategory[]);

    const filteredAssets = useMemo(() => {
        const categoryKey = getCategoryKey(activeCategory);
        const assets = Object.values(codex[categoryKey] || {});
        
        return assets
            .filter(asset => {
                const displayName = asset.isPreset ? t(asset.name) : asset.name;
                const searchMatch = displayName.toLowerCase().includes(searchTerm.toLowerCase());
                const customFilterMatch = filter ? filter(asset) : true;
                return searchMatch && customFilterMatch;
            })
            .sort((a, b) => {
                if (a.type === 'save' && b.type === 'save') {
                    return new Date((b as CodexSaveAsset).createdAt).getTime() - new Date((a as CodexSaveAsset).createdAt).getTime();
                }
                const nameA = a.isPreset ? t(a.name) : a.name;
                const nameB = b.isPreset ? t(b.name) : b.name;
                return nameA.localeCompare(nameB);
            });
    }, [codex, activeCategory, searchTerm, filter, t]);

    useEffect(() => {
        if (!isOpen) {
            setSearchTerm('');
            setActiveCategory(initialCategory || 'character');
        }
    }, [isOpen, initialCategory]);
    
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose(); };
        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [onClose]);
    
    const handleSelect = useCallback((asset: CodexAsset) => {
        onSelect(asset);
        onClose();
    }, [onSelect, onClose]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/70 z-[101] flex items-center justify-center p-4 backdrop-blur-sm" onClick={onClose}>
            <div
                ref={modalRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby="asset-picker-title"
                className="bg-gray-800 rounded-lg border-2 border-gray-700 shadow-lg w-full max-w-4xl h-[80vh] flex flex-col p-4"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="flex justify-between items-center mb-4 flex-shrink-0">
                    <h2 id="asset-picker-title" className="text-xl font-bold text-indigo-400">{t('assetPicker.title')}</h2>
                    <button onClick={onClose} className="p-1 rounded-full text-gray-400 hover:bg-gray-700" aria-label={t('game.ariaLabels.closeModal')}>
                        <CloseIcon className="w-6 h-6" />
                    </button>
                </div>
                <div className="flex flex-col md:flex-row gap-4 flex-1 min-h-0">
                    {/* Desktop Sidebar */}
                    <aside className="hidden md:block w-full md:w-48 flex-shrink-0 overflow-y-auto scrollbar-thin pr-2">
                         <nav className="space-y-1">
                            {availableCategories.map(cat => (
                                <button
                                    key={cat}
                                    onClick={() => setActiveCategory(cat)}
                                    className={`w-full text-left flex items-center gap-3 p-2 rounded-md transition-colors text-sm ${activeCategory === cat ? 'bg-indigo-600/30 text-indigo-300 font-semibold' : 'text-gray-400 hover:bg-gray-700/50 hover:text-gray-200'}`}
                                >
                                    {categoryIcons[cat]}
                                    <span className="capitalize">{t(`codex.categories.${cat}`)}</span>
                                </button>
                            ))}
                        </nav>
                    </aside>
                    <main className="flex-1 flex flex-col min-h-0">
                        {/* Mobile Category Scroller */}
                         <div className="md:hidden flex-shrink-0 mb-4">
                            <div className="overflow-x-auto whitespace-nowrap scrollbar-thin">
                                <div className="flex gap-2">
                                    {availableCategories.map(cat => (
                                        <button
                                            key={cat}
                                            onClick={() => setActiveCategory(cat)}
                                            className={`flex-shrink-0 text-center text-sm font-semibold py-1.5 px-3 rounded-md transition-colors flex items-center gap-2 ${activeCategory === cat ? 'bg-indigo-600 text-white' : 'text-gray-300 bg-gray-700/50 hover:bg-gray-700'}`}
                                        >
                                            {categoryIcons[cat]}
                                            <span className="capitalize">{t(`codex.categories.${cat}`)}</span>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <input
                            ref={searchInputRef}
                            type="search"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            placeholder={t('assetPicker.searchPlaceholder')}
                            className="w-full bg-gray-900/80 border border-gray-600 rounded-md p-2 mb-4 text-gray-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                        />
                        <div className="flex-1 overflow-y-auto scrollbar-thin pr-2">
                             {filteredAssets.length === 0 ? (
                                <p className="text-gray-500 text-center py-10">{t('assetPicker.noResults')}</p>
                            ) : (
                                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                                    {filteredAssets.map(asset => (
                                        <MemoizedAssetButton
                                            key={asset.id}
                                            asset={asset}
                                            onSelect={handleSelect}
                                        />
                                    ))}
                                </div>
                            )}
                        </div>
                    </main>
                </div>
            </div>
        </div>
    );
};

export default AssetPickerModal;