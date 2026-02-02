import React, { useState, useEffect } from 'react';
import { useI18n } from '../context/i18n';
import { useApiErrorHandler } from '../services/utils';
import { LoadingSpinner, ImageIcon } from './icons';
import { Toast, GenerateImageTask } from '../types';
import { addTask, subscribe } from '../services/taskQueueService';
import { useCodex } from '../context/codex';
import { useSettings } from '../context/settings';

interface ImageGeneratorProps {
  addToast: (message: string, type?: Toast['type']) => void;
}

const ImageGenerator: React.FC<ImageGeneratorProps> = ({ addToast }) => {
    const { t } = useI18n();
    const [isBusy, setIsBusy] = useState(false);
    const { parseApiError } = useApiErrorHandler();
    const { addCodexEntry } = useCodex();
    const settings = useSettings();
    
    const [prompt, setPrompt] = useState('');
    const [imageUrl, setImageUrl] = useState('');
    const [error, setError] = useState('');

    useEffect(() => {
        const unsubscribe = subscribe((busy) => setIsBusy(busy));
        return unsubscribe;
    }, []);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!prompt.trim() || isBusy) return;

        setError('');
        setImageUrl('');
        
        const task: GenerateImageTask = {
            type: 'generate-image',
            id: `task-img-${Date.now()}`,
            description: t('imageGenerator.generating'),
            status: 'queued',
            priority: 20,
            prompt,
            aspectRatio: '16:9',
            model: settings.imageModel,
            onSuccess: (url) => {
                const dataUrl = `data:image/jpeg;base64,${url}`;
                setImageUrl(dataUrl);
                addCodexEntry({
                    type: 'image',
                    id: `img-gen-${Date.now()}`,
                    name: prompt,
                    description: 'Generated from Image Generator tool.',
                    url: dataUrl,
                });
            },
            onError: (err) => setError(parseApiError(err, 'generic')),
        };
        addTask(task);
    };

    return (
        <div className="flex-1 w-full max-w-4xl mx-auto p-4 md:p-8 flex flex-col items-center">
            <div className="text-center mb-8">
                <h1 className="text-4xl font-bold text-indigo-400">{t('imageGenerator.title')}</h1>
                <p className="text-gray-400 mt-2">{t('imageGenerator.subtitle')}</p>
            </div>

            <form onSubmit={handleSubmit} className="w-full bg-gray-800/50 p-6 rounded-lg border border-gray-700 shadow-lg">
                <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder={t('imageGenerator.promptPlaceholder')}
                    disabled={isBusy}
                    rows={4}
                    className="w-full bg-gray-900/50 border border-gray-600 rounded-lg p-4 text-gray-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition resize-y disabled:opacity-50"
                />
                <button
                    type="submit"
                    disabled={isBusy || !prompt.trim()}
                    className="mt-4 w-full bg-indigo-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-indigo-700 disabled:bg-indigo-800/50 disabled:cursor-not-allowed flex items-center justify-center transition-colors text-lg"
                >
                    {isBusy ? (
                        <>
                            <LoadingSpinner />
                            <span className="ml-2">{t('imageGenerator.generating')}</span>
                        </>
                    ) : (
                        t('imageGenerator.generateButton')
                    )}
                </button>
            </form>

            {error && (
                <div className="mt-6 w-full bg-red-500/20 border border-red-500 text-red-300 px-4 py-3 rounded-md" role="alert">
                    {error}
                </div>
            )}

            <div className="mt-6 w-full flex-1 flex items-center justify-center bg-gray-900/50 rounded-lg border border-gray-700 min-h-[300px] p-4">
                {imageUrl ? (
                    <img src={imageUrl} alt={prompt} className="max-w-full max-h-full object-contain rounded-md" />
                ) : !isBusy && (
                    <div className="text-center text-gray-500">
                        <ImageIcon className="w-16 h-16 mx-auto mb-2" />
                        <p>Your generated image will appear here.</p>
                    </div>
                )}
                 {isBusy && !imageUrl && <LoadingSpinner />}
            </div>
        </div>
    );
};

export default ImageGenerator;