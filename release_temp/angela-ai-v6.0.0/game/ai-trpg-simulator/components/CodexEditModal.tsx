import React, { useState, useEffect, useRef } from 'react';
import { CodexAsset } from '../types';
import { useI18n } from '../context/i18n';
import { useCodex } from '../context/codex';
import { useFocusTrap } from '../hooks/useFocusTrap';

interface CodexEditModalProps {
    asset: CodexAsset;
    onClose: () => void;
    addToast: (message: string, type: 'success' | 'info' | 'error') => void;
}

const CodexEditModal: React.FC<CodexEditModalProps> = ({ asset, onClose, addToast }) => {
    const { t } = useI18n();
    const { updateCodexEntry } = useCodex();
    
    const initialName = asset.isPreset ? t(asset.name) : asset.name;
    const initialDescription = asset.isPreset ? t(asset.description) : asset.description;
    
    const [name, setName] = useState(initialName);
    const [description, setDescription] = useState(initialDescription);
    const saveButtonRef = useRef<HTMLButtonElement>(null);
    const modalRef = useFocusTrap<HTMLDivElement>(saveButtonRef);

    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape') onClose();
        };
        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [onClose]);

    const handleSave = () => {
        const updatedAsset = { 
            ...asset, 
            name, 
            description, 
            isPreset: false 
        };
        updateCodexEntry(updatedAsset);
        addToast(t('codex.edit.saveSuccess', { name }), 'success');
        onClose();
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
                aria-labelledby="codex-edit-title"
                className="bg-gray-800 rounded-lg border-2 border-gray-700 shadow-lg w-full max-w-lg p-6"
                onClick={(e) => e.stopPropagation()}
            >
                <h2 id="codex-edit-title" className="text-xl font-bold text-indigo-400 mb-4">{t('codex.edit.title')}</h2>
                
                <div className="space-y-4">
                    <div>
                        <label htmlFor="asset-name" className="block text-sm font-medium text-gray-300 mb-1">{t('codex.edit.name')}</label>
                        <input 
                            id="asset-name"
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            className="w-full bg-gray-900/50 border border-gray-600 rounded-lg p-2 text-gray-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                        />
                    </div>
                     <div>
                        <label htmlFor="asset-description" className="block text-sm font-medium text-gray-300 mb-1">{t('codex.edit.description')}</label>
                        <textarea
                            id="asset-description"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            rows={5}
                            className="w-full bg-gray-900/50 border border-gray-600 rounded-lg p-2 text-gray-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                        />
                    </div>
                </div>

                <div className="flex gap-2 mt-6">
                    <button onClick={onClose} className="flex-1 bg-gray-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors">{t('common.cancel')}</button>
                    <button ref={saveButtonRef} onClick={handleSave} className="flex-1 bg-indigo-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors">{t('common.save')}</button>
                </div>
            </div>
        </div>
    );
};

export default CodexEditModal;