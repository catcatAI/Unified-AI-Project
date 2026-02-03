import React from 'react';
import { CodexAsset } from '../types';
import { getAssetUrl } from '../services/utils';
import { CloseIcon, ImageIcon, VideoIcon } from './icons';

interface ContextPreviewProps {
    asset: CodexAsset;
    onClear: () => void;
    contextMessage: string;
    clearMessage: string;
}

const ContextPreview: React.FC<ContextPreviewProps> = ({ asset, onClear, contextMessage, clearMessage }) => {
    const url = getAssetUrl(asset);

    const renderIcon = () => {
        if (url) {
            if (asset.type === 'video') {
                return <video src={url} className="w-10 h-10 rounded object-cover flex-shrink-0" />;
            }
            if (asset.type === 'model') { // Special case for model, use side view as preview
                return <img src={asset.sideViewUrl} className="w-10 h-10 rounded object-cover flex-shrink-0" />;
            }
            return <img src={url} className="w-10 h-10 rounded object-cover flex-shrink-0" />;
        }
        if (asset.type === 'video') return <VideoIcon className="w-6 h-6 text-gray-400" />;
        return <ImageIcon className="w-6 h-6 text-gray-400" />;
    };

    return (
        <div className="mb-2 p-2 bg-gray-900/50 rounded-md flex items-center justify-between animate-fade-in border border-indigo-500/50">
            <div className="flex items-center gap-3 overflow-hidden">
                <div className="w-10 h-10 flex items-center justify-center flex-shrink-0 bg-black/20 rounded">
                    {renderIcon()}
                </div>
                <div className="flex-1 min-w-0">
                    <p className="text-xs text-gray-400 truncate">{contextMessage}</p>
                    <p className="text-sm text-gray-200 font-semibold truncate" title={asset.name}>{asset.name}</p>
                </div>
            </div>
            <button onClick={onClear} className="p-1 rounded-full text-gray-400 hover:bg-gray-700 flex-shrink-0" aria-label={clearMessage}>
                <CloseIcon className="w-4 h-4" />
            </button>
        </div>
    );
};

export default ContextPreview;
