import React, { useState, useRef, useCallback, useMemo } from 'react';
import { useCodex } from '../context/codex';
import { useI18n } from '../context/i18n';
import { GlobalCodex, CodexAsset, CodexCategory, GameState, CodexModelAsset, Toast, CodexSaveAsset } from '../types';
import { UserIcon, PackageIcon, TruckIcon, HomeIcon, ImageIcon, PenIcon, UploadIcon, DownloadIcon, VideoIcon, MapIcon, SpeakerIcon, CubeIcon, SparklesIcon, TrashIcon, SaveIcon, RefreshIcon } from './icons';
import CodexEditModal from './CodexEditModal';
import { Tool } from './Header';
import { useSettings } from '../context/settings';
import { getAssetUrl } from '../services/utils';

interface CodexScreenProps {
  addToast: (message: string, type?: Toast['type']) => void;
  onSendAssetToTool?: (asset: CodexAsset, tool: Tool) => void;
  onLoadSave: (asset: CodexSaveAsset) => void;
  onImportFileToCodex: (file: File) => Promise<void>;
  onReconstructSave: (saveAssetId: string) => Promise<void>;
}

const categoryIcons: Record<CodexCategory, React.ReactNode> = {
    character: <UserIcon className="w-5 h-5" />,
    item: <PackageIcon className="w-5 h-5" />,
    block: <CubeIcon className="w-5 h-5" />,
    location: <MapIcon className="w-5 h-5" />,
    vehicle: <TruckIcon className="w-5 h-5" />,
    realEstate: <HomeIcon className="w-5 h-5" />,
    image: <ImageIcon className="w-5 h-5" />,
    video: <VideoIcon className="w-5 h-5" />,
    audio: <SpeakerIcon className="w-5 h-5" />,
    model: <CubeIcon className="w-5 h-5" />,
    save: <SaveIcon className="w-5 h-5" />,
};

const getCategoryKey = (type: CodexCategory): keyof GlobalCodex => {
    switch (type) {
        case 'audio': return 'audio';
        case 'realEstate': return 'realEstate';
        case 'block': return 'blocks';
        default: return `${type}s` as keyof GlobalCodex;
    }
};

const MemoizedAssetItem: React.FC<{
  asset: CodexAsset;
  onEdit: (asset: CodexAsset) => void;
  onLoadSave: (asset: CodexSaveAsset) => void;
  onReconstructSave: (saveAssetId: string) => void;
  onSendAssetToTool?: (asset: CodexAsset, tool: Tool) => void;
  canSendToModel: boolean;
  addToast: (message: string, type?: Toast['type']) => void;
}> = React.memo(({ asset, onEdit, onLoadSave, onReconstructSave, onSendAssetToTool, canSendToModel, addToast }) => {
    const { t } = useI18n();
    const { deleteCodexEntry } = useCodex();

    const displayName = asset.isPreset ? t(asset.name) : asset.name;
    const displayDescription = asset.isPreset ? t(asset.description) : asset.description;

    const isOldFormat = useMemo(() => {
        if (asset.type !== 'save') return false;
        const gameStateString = JSON.stringify((asset as CodexSaveAsset).gameState);
        return gameStateString.includes('"imageUrl"') || gameStateString.includes('"mapImageUrl"') || gameStateString.includes('"iconUrl"') || gameStateString.includes('"url"');
    }, [asset]);

    const handleDelete = () => {
        if (asset.isPreset) {
            addToast(t('codex.delete.presetError'), 'error');
            return;
        }
        if (window.confirm(t('codex.delete.confirm', { name: displayName }))) {
            deleteCodexEntry(asset.id, asset.type);
        }
    };
    
    const handleExportThisSave = () => {
        if (asset.type !== 'save') return;
        try {
            const saveData = {
                type: 'AITRPG_SAVE',
                gameState: (asset as CodexSaveAsset).gameState,
            };
            const dataStr = JSON.stringify(saveData, null, 2);
            const blob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const linkElement = document.createElement('a');
            linkElement.href = url;
            const filename = `${displayName.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_save.json`;
            linkElement.download = filename;
            document.body.appendChild(linkElement);
            linkElement.click();
            document.body.removeChild(linkElement);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error("Failed to export save:", error);
            addToast("Failed to export save.", 'error');
        }
    };

    const renderMedia = () => {
         const getMediaInfo = (asset: CodexAsset): { url?: string, type: 'image' | 'video' | 'icon' | 'audio' | 'model' } => {
            switch (asset.type) {
                case 'character': return { url: asset.imageUrl, type: 'image' };
                case 'location': return { url: asset.imageUrl, type: 'image' };
                case 'item': return { url: asset.iconUrl, type: 'icon' };
                case 'block': return { url: asset.iconUrl, type: 'icon' };
                case 'image': return { url: asset.url, type: 'image' };
                case 'video': return { url: asset.url, type: 'video' };
                case 'audio': return { url: asset.url, type: 'audio' };
                case 'model': return { type: 'model' };
                default: return { type: 'image' };
            }
        }
        
        const media = getMediaInfo(asset);

        if (media.type === 'model') {
            const modelAsset = asset as CodexModelAsset;
            const views = [modelAsset.frontViewUrl, modelAsset.sideViewUrl, modelAsset.topViewUrl].filter(Boolean);
            if (views.length > 0) {
                return (
                    <div className="grid gap-1 w-full h-full" style={{ gridTemplateColumns: `repeat(${views.length}, minmax(0, 1fr))` }}>
                       {views.map((url, i) => url && <img key={i} src={url} className="w-full h-full object-cover rounded-sm" alt={`${asset.name} view ${i+1}`}/>)}
                    </div>
                );
            }
        }

        if (media.url) {
            if (media.type === 'video') {
                 return <video src={media.url} controls className="w-full h-full object-cover" />;
            }
            if (media.type === 'audio') {
                return <audio src={media.url} controls className="w-full h-10" />;
            }
            const imageStyling = media.type === 'icon' 
                ? "w-20 h-20 object-contain" 
                : "w-full h-full object-cover";
            return <img src={media.url} alt={displayName} className={imageStyling} style={{imageRendering: media.type === 'icon' ? 'pixelated' : 'auto'}} />;
        }
        
        return <div className="w-full h-full flex items-center justify-center text-gray-500">{React.cloneElement(categoryIcons[asset.type] as React.ReactElement, { className: "w-12 h-12" })}</div>;
    };
    
    const MainWrapper: React.FC<{children: React.ReactNode}> = ({ children }) => {
        if (asset.type === 'save') {
            return <button onClick={() => onLoadSave(asset as CodexSaveAsset)} className="w-full h-full text-left">{children}</button>
        }
        return <div className="w-full h-full">{children}</div>;
    };

    return (
         <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700 flex flex-col group relative transition-shadow hover:shadow-lg hover:border-gray-600 focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/50">
            <MainWrapper>
                {asset.isPreset && (
                    <div className="absolute top-2 left-2 bg-gray-700 text-gray-300 text-xs font-semibold px-1.5 py-0.5 rounded-sm z-10 select-none">PRESET</div>
                )}
                <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-lg text-gray-100 truncate pr-20" title={displayName}>{displayName}</h3>
                    <p className="text-xs text-gray-400 mt-2 line-clamp-3">{displayDescription}</p>
                    {isOldFormat && (
                         <div className="mt-1 text-xs text-yellow-400 font-semibold">Old Format</div>
                    )}
                </div>
                <div className="mt-4 pt-4 border-t border-gray-700/50 flex-shrink-0 flex items-center justify-center h-28">
                    {renderMedia()}
                </div>
            </MainWrapper>
             <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity">
                {onSendAssetToTool && asset.type !== 'save' && (
                    <div className="relative">
                        <button onClick={() => onSendAssetToTool(asset, 'creativeHub')} className="text-gray-500 hover:text-indigo-400 p-1 rounded-full bg-gray-800/50" aria-label={t('codex.createWith')} title={t('codex.createWith')}>
                            <SparklesIcon className="w-4 h-4" />
                        </button>
                    </div>
                )}
                {onSendAssetToTool && canSendToModel && asset.type !== 'save' && (
                    <div className="relative">
                        <button onClick={() => onSendAssetToTool(asset, 'model')} className="text-gray-500 hover:text-indigo-400 p-1 rounded-full bg-gray-800/50" aria-label={t('creativeHub.imageActions.create3DModel')} title={t('creativeHub.imageActions.create3DModel')}>
                            <CubeIcon className="w-4 h-4" />
                        </button>
                    </div>
                )}
                 {asset.type === 'save' && (
                    <button onClick={handleExportThisSave} className="text-gray-500 hover:text-indigo-400 p-1 rounded-full bg-gray-800/50" aria-label={`Export ${displayName}`} title={`Export ${displayName}`}>
                        <DownloadIcon className="w-4 h-4" />
                    </button>
                )}
                {asset.type === 'save' && isOldFormat && (
                    <button onClick={() => onReconstructSave(asset.id)} className="text-gray-500 hover:text-green-400 p-1 rounded-full bg-gray-800/50" aria-label={`Reconstruct ${displayName}`} title={`Reconstruct ${displayName}`}>
                        <RefreshIcon className="w-4 h-4" />
                    </button>
                )}
                {asset.type !== 'save' && (
                    <button onClick={() => onEdit(asset)} className="text-gray-500 hover:text-indigo-400 p-1 rounded-full bg-gray-800/50" aria-label={`Edit ${displayName}`} title={`Edit ${displayName}`}>
                        <PenIcon className="w-4 h-4" />
                    </button>
                )}
                <button 
                    onClick={handleDelete} 
                    disabled={!!asset.isPreset} 
                    className="text-gray-500 hover:text-red-400 p-1 rounded-full bg-gray-800/50 disabled:text-gray-700 disabled:cursor-not-allowed" 
                    title={asset.isPreset ? t('codex.delete.presetError') : `Delete ${displayName}`}
                    aria-label={asset.isPreset ? t('codex.delete.presetError') : `Delete ${displayName}`}
                >
                    <TrashIcon className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
});


const CodexScreen: React.FC<CodexScreenProps> = ({ addToast, onSendAssetToTool, onLoadSave, onImportFileToCodex, onReconstructSave }) => {
    const { t } = useI18n();
    const { codex, getRawCodex } = useCodex();
    const settings = useSettings();
    const [activeCategory, setActiveCategory] = useState<CodexCategory>('save');
    const [editingAsset, setEditingAsset] = useState<CodexAsset | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [searchTerm, setSearchTerm] = useState('');


    const categories: CodexCategory[] = ['save', 'character', 'item', 'block', 'location', 'model', 'image', 'video', 'audio', 'vehicle', 'realEstate'];
    const activeAssets = useMemo(() => {
        const assets = Object.values(codex[getCategoryKey(activeCategory)] || {});
        
        const filtered = assets.filter(asset => {
            const displayName = asset.isPreset ? t(asset.name) : asset.name;
            const description = asset.isPreset ? t(asset.description) : asset.description;
            const term = searchTerm.toLowerCase();
            return displayName.toLowerCase().includes(term) || description.toLowerCase().includes(term);
        });

        if (activeCategory === 'save') {
             return filtered.sort((a,b) => new Date((b as CodexSaveAsset).createdAt).getTime() - new Date((a as CodexSaveAsset).createdAt).getTime())
        }
        return filtered.sort((a,b) => (a.isPreset ? t(a.name) : a.name).localeCompare(b.isPreset ? t(b.name) : b.name));
    }, [codex, activeCategory, t, searchTerm]);

    const handleImportClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files;
        if (!files || files.length === 0) return;
        
        for (const file of Array.from(files)) {
            await onImportFileToCodex(file);
        }

        if(event.target) event.target.value = '';
    };
    
    const handleExport = useCallback(() => {
        try {
            const rawCodex = getRawCodex();
            const exportData = {
                type: 'AITRPG_CODEX',
                ...rawCodex
            };
            const dataStr = JSON.stringify(exportData, null, 2);
            const blob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const linkElement = document.createElement('a');
            linkElement.href = url;
            linkElement.download = 'ai-trpg-codex.json';
            document.body.appendChild(linkElement);
            linkElement.click();
            document.body.removeChild(linkElement);
            URL.revokeObjectURL(url);
            addToast(t('codex.exportSuccess'), 'success');
        } catch (error) {
            console.error("Failed to export codex:", error);
            addToast(t('codex.exportError'), 'error');
        }
    }, [getRawCodex, addToast, t]);

    return (
        <div className="w-full max-w-7xl mx-auto p-4 md:p-8 flex flex-col flex-1 min-h-0">
            {editingAsset && <CodexEditModal asset={editingAsset} onClose={() => setEditingAsset(null)} addToast={addToast} />}
            <input type="file" ref={fileInputRef} onChange={handleFileChange} accept=".json" multiple className="hidden" />

            <div className="text-center mb-8 flex-shrink-0">
                <h1 className="text-4xl font-bold text-indigo-400">{t('codex.title')}</h1>
                <p className="text-gray-400 mt-2">{t('codex.subtitle')}</p>
            </div>
            
            {/* Main layout container */}
            <div className="flex flex-col md:flex-row gap-8 flex-1 min-h-0">
                
                {/* Desktop Sidebar Navigation */}
                <aside className="hidden md:flex w-64 flex-shrink-0 flex-col gap-4">
                    <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700 space-y-2">
                        <button onClick={handleImportClick} className="w-full bg-indigo-600 text-white font-semibold py-2 px-4 rounded-md hover:bg-indigo-700 transition-colors flex items-center justify-center gap-2">
                            <UploadIcon className="w-5 h-5" /> {t('codex.importButton')}
                        </button>
                        <button onClick={handleExport} className="w-full bg-gray-700 text-white font-semibold py-2 px-4 rounded-md hover:bg-gray-600 transition-colors flex items-center justify-center gap-2">
                            <DownloadIcon className="w-5 h-5" /> {t('codex.exportButton')}
                        </button>
                    </div>
                    <nav className="bg-gray-800/50 p-2 rounded-lg border border-gray-700 space-y-1 flex-1 overflow-y-auto scrollbar-thin">
                        {categories.map(cat => (
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

                {/* Main Content Area */}
                <main className="flex-1 bg-gray-800/50 rounded-lg border border-gray-700 flex flex-col min-h-0">
                    
                    {/* Mobile Top Controls */}
                    <div className="md:hidden flex-shrink-0 border-b border-gray-700">
                        <div className="overflow-x-auto whitespace-nowrap scrollbar-thin p-2">
                            <div className="flex gap-2">
                                {categories.map(cat => (
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
                        <div className="p-2 flex gap-2 border-t border-gray-700/50">
                           <button onClick={handleImportClick} className="flex-1 bg-indigo-600/80 text-white font-semibold py-2 px-3 rounded-md hover:bg-indigo-700 transition-colors flex items-center justify-center gap-2 text-sm">
                                <UploadIcon className="w-4 h-4" /> {t('codex.importButton')}
                            </button>
                            <button onClick={handleExport} className="flex-1 bg-gray-700/80 text-white font-semibold py-2 px-3 rounded-md hover:bg-gray-600 transition-colors flex items-center justify-center gap-2 text-sm">
                                <DownloadIcon className="w-4 h-4" /> {t('codex.exportButton')}
                            </button>
                        </div>
                    </div>

                    {/* Scrollable Asset Grid */}
                    <div className="flex-1 overflow-y-auto scrollbar-thin p-4 flex flex-col">
                        <div className="p-2 mb-4 flex-shrink-0">
                            <input
                                type="search"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                placeholder={t('assetPicker.searchPlaceholder')}
                                className="w-full bg-gray-900/80 border border-gray-600 rounded-md p-2 text-gray-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                            />
                        </div>

                        <div className="flex-1 min-h-0 overflow-y-auto scrollbar-thin">
                            <h2 className="text-2xl font-bold mb-4 text-gray-100 hidden md:block">{t(`codex.categories.${activeCategory}`)} ({activeAssets.length})</h2>
                            {activeAssets.length === 0 ? (
                                <p className="text-gray-500 text-center py-10">{t('codex.emptyCategory')}</p>
                            ) : (
                                <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                                    {activeAssets.map(asset => {
                                        const canSendToModel = (asset.type === 'image' || asset.type === 'character' || asset.type === 'location') && !!getAssetUrl(asset);
                                        return <MemoizedAssetItem key={asset.id} asset={asset} onEdit={setEditingAsset} onLoadSave={onLoadSave} onReconstructSave={onReconstructSave} onSendAssetToTool={onSendAssetToTool} canSendToModel={settings.enableMvalGen && canSendToModel} addToast={addToast} />
                                    })}
                                </div>
                            )}
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
};

export default CodexScreen;