import React, { useEffect, useRef } from 'react';
import { Item } from '../types';
import { useI18n } from '../context/i18n';
import { useFocusTrap } from '../hooks/useFocusTrap';
import { SmallLoadingSpinner, RefreshIcon, PackageIcon } from './icons';

interface ItemDetailModalProps {
    item: Item;
    onClose: () => void;
    assetCache: Record<string, string>;
}

const ItemDetailModal: React.FC<ItemDetailModalProps> = ({ item, onClose, assetCache }) => {
    const { t } = useI18n();
    const closeButtonRef = useRef<HTMLButtonElement>(null);
    const modalRef = useFocusTrap<HTMLDivElement>(closeButtonRef);

    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose(); };
        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [onClose]);

    const renderIcon = () => {
        const iconUrl = assetCache[`icon-${item.name.toLowerCase()}`];
        if (iconUrl) return <img src={iconUrl} alt={item.name} className="w-full h-full object-contain" />;

        switch (item.iconStatus) {
            case 'loading':
            case 'queued':
                return <SmallLoadingSpinner />;
            case 'error':
                return <RefreshIcon className="w-12 h-12 text-red-400" />;
            case 'pending':
            default:
                return <PackageIcon className="w-16 h-16 text-gray-500" />;
        }
    };

    return (
        <div className="fixed inset-0 bg-black/70 z-[100] flex items-center justify-center p-4 backdrop-blur-sm" onClick={onClose}>
            <div ref={modalRef} role="dialog" aria-modal="true" aria-labelledby="item-detail-title" className="bg-gray-800 rounded-lg border-2 border-gray-700 shadow-lg w-full max-w-sm text-center p-6" onClick={(e) => e.stopPropagation()}>
                <div className="w-24 h-24 bg-gray-900/50 border-2 border-gray-700 rounded-md flex items-center justify-center p-2 mx-auto" style={{ imageRendering: 'pixelated' }}>
                    {renderIcon()}
                </div>
                <h2 id="item-detail-title" className="text-2xl font-bold mt-4 text-white">{item.name}</h2>
                <p className="text-sm text-gray-400 mb-4">{t('common.quantity')}: {item.quantity}</p>
                <p className="text-gray-300 mb-6 text-sm">{item.description}</p>
                <button ref={closeButtonRef} onClick={onClose} className="w-full bg-indigo-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-indigo-500">
                    {t('game.itemDetail.close')}
                </button>
            </div>
        </div>
    );
};

export default ItemDetailModal;