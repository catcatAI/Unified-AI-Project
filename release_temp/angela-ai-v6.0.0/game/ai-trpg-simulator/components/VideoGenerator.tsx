import React, { useState, useEffect } from 'react';
import { useI18n } from '../context/i18n';
import { useApiErrorHandler } from '../services/utils';
import { LoadingSpinner, VideoIcon } from './icons';
import VeoModal from './VeoModal';
import { useApiKey } from '../context/apiKey';
import { Toast } from '../types';
import { subscribe } from '../services/taskQueueService';
import { useCodex } from '../context/codex';

interface VideoGeneratorProps {
  addToast: (message: string, type?: Toast['type']) => void;
}

const VideoGenerator: React.FC<VideoGeneratorProps> = ({ addToast }) => {
    const { t } = useI18n();
    const [isBusy, setIsBusy] = useState(false);
    const { parseApiError } = useApiErrorHandler();
    const { isKeySelected, selectKey, resetKeySelection } = useApiKey();
    const { addCodexEntry } = useCodex();
    
    const [prompt, setPrompt] = useState('');
    const [videoUrl, setVideoUrl] = useState('');
    const [error, setError] = useState('');
    const [videoRequest, setVideoRequest] = useState<{ prompt: string } | null>(null);

    useEffect(() => {
        const unsubscribe = subscribe((busy) => setIsBusy(busy));
        return unsubscribe;
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!prompt.trim() || isBusy || videoRequest) return;
        
        if (!isKeySelected) {
            addToast(t('suite.settings.apiKeyToast'), 'info');
            await selectKey();
            const hasKeyNow = await window.aistudio.hasSelectedApiKey();
            if (!hasKeyNow) {
                return; 
            }
        }
        
        setError('');
        setVideoUrl('');
        setVideoRequest({ prompt });
    };

    const handleVideoComplete = (url: string) => {
        setVideoUrl(url);
        if (videoRequest) {
            addCodexEntry({
                type: 'video',
                id: `vid-gen-${Date.now()}`,
                name: videoRequest.prompt,
                description: 'Generated from Video Generator tool.',
                url: url,
            });
        }
        setVideoRequest(null);
    };

    const handleVideoCancel = (err: Error) => {
        if (err.message === 'API_KEY_NOT_FOUND') {
            resetKeySelection();
        } else {
            setError(parseApiError(err, 'generic'));
        }
        setVideoRequest(null);
    };

    return (
        <div className="flex-1 w-full max-w-4xl mx-auto p-4 md:p-8 flex flex-col items-center">
            
            {videoRequest && (
                <VeoModal
                    request={videoRequest}
                    onComplete={handleVideoComplete}
                    onCancel={handleVideoCancel}
                />
            )}

            <div className="text-center mb-8">
                <h1 className="text-4xl font-bold text-indigo-400">{t('videoGenerator.title')}</h1>
                <p className="text-gray-400 mt-2">{t('videoGenerator.subtitle')}</p>
            </div>

            <form onSubmit={handleSubmit} className="w-full bg-gray-800/50 p-6 rounded-lg border border-gray-700 shadow-lg">
                <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder={t('videoGenerator.promptPlaceholder')}
                    disabled={isBusy || !!videoRequest}
                    rows={4}
                    className="w-full bg-gray-900/50 border border-gray-600 rounded-lg p-4 text-gray-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition resize-y disabled:opacity-50"
                />
                <button
                    type="submit"
                    disabled={isBusy || !prompt.trim() || !!videoRequest}
                    className="mt-4 w-full bg-indigo-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-indigo-700 disabled:bg-indigo-800/50 disabled:cursor-not-allowed flex items-center justify-center transition-colors text-lg"
                >
                    {isBusy || videoRequest ? (
                        <>
                            <LoadingSpinner />
                            <span className="ml-2">{t('videoGenerator.generating')}</span>
                        </>
                    ) : (
                        t('videoGenerator.generateButton')
                    )}
                </button>
            </form>

            {error && (
                <div className="mt-6 w-full bg-red-500/20 border border-red-500 text-red-300 px-4 py-3 rounded-md" role="alert">
                    {error}
                </div>
            )}

            <div className="mt-6 w-full flex-1 flex items-center justify-center bg-gray-900/50 rounded-lg border border-gray-700 min-h-[300px] p-4">
                {videoUrl ? (
                    <video src={videoUrl} controls className="max-w-full max-h-full object-contain rounded-md" />
                ) : !isBusy && !videoRequest && (
                    <div className="text-center text-gray-500">
                        <VideoIcon className="w-16 h-16 mx-auto mb-2" />
                        <p>Your generated video will appear here.</p>
                    </div>
                )}
                 {(isBusy || videoRequest) && !videoUrl && <LoadingSpinner />}
            </div>
        </div>
    );
};

export default VideoGenerator;