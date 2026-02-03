import React, { useState, useEffect, useRef } from 'react';
import { Item } from '../types';
import { useI18n } from '../context/i18n';
import { useFocusTrap } from '../hooks/useFocusTrap';

interface QuantityModalProps {
    item: Item;
    onConfirm: (quantity: number) => void;
    onClose: () => void;
}

const QuantityModal: React.FC<QuantityModalProps> = ({ item, onConfirm, onClose }) => {
    const { t } = useI18n();
    const [quantity, setQuantity] = useState(1);
    const confirmButtonRef = useRef<HTMLButtonElement>(null);
    const modalRef = useFocusTrap<HTMLDivElement>(confirmButtonRef);

    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                onClose();
            } else if (event.key === 'Enter') {
                handleConfirm();
            }
        };
        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [onClose, onConfirm, quantity]);

    const handleConfirm = () => {
        if (quantity > 0 && quantity <= item.quantity) {
            onConfirm(quantity);
        }
    };

    return (
        <div 
            className="fixed inset-0 bg-black/70 z-[101] flex items-center justify-center p-4 backdrop-blur-sm"
            onClick={onClose}
        >
            <div 
                ref={modalRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby="quantity-title"
                className="bg-gray-800 rounded-lg border-2 border-gray-700 shadow-lg w-full max-w-xs p-6"
                onClick={(e) => e.stopPropagation()}
            >
                <h2 id="quantity-title" className="text-lg font-bold text-center text-white mb-2">{t('game.quantityModal.title', { itemName: item.name })}</h2>
                <div className="flex items-center justify-center gap-4 my-4">
                    <input 
                        type="range" 
                        min="1" 
                        max={item.quantity} 
                        value={quantity} 
                        onChange={(e) => setQuantity(parseInt(e.target.value))}
                        className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer" 
                    />
                    <input 
                        type="number" 
                        value={quantity}
                        min="1"
                        max={item.quantity}
                        onChange={(e) => setQuantity(Math.max(1, Math.min(item.quantity, parseInt(e.target.value) || 1)))} 
                        className="w-20 bg-gray-900/50 border border-gray-600 rounded-lg p-2 text-center text-gray-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none" 
                    />
                </div>
                <div className="flex gap-2">
                    <button onClick={onClose} className="flex-1 bg-gray-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors">{t('game.quantityModal.cancel')}</button>
                    <button ref={confirmButtonRef} onClick={handleConfirm} className="flex-1 bg-indigo-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors">{t('game.quantityModal.confirm')}</button>
                </div>
            </div>
        </div>
    );
};

export default QuantityModal;