import React, { useState, useEffect, useCallback } from 'react';
import { LoadingSpinner } from './icons';
import { useI18n } from '../context/i18n';
import { useApiKey } from '../context/apiKey';
import { GenerateVideoTask } from '../types';
import { addTask } from '../services/taskQueueService';
import { useSettings } from '../context/settings';

interface VeoModalProps {
  request: { prompt: string; sourceImageUrl?: string }; // Allow optional source image for video
  onComplete: (url: string) => void;
  onCancel: (error: Error) => void;
}

const VeoModal: React.FC<VeoModalProps> = ({ request, onComplete, onCancel }) => {
    const { t } = useI18n();
    const { resetKeySelection } = useApiKey();
    const settings = useSettings();
    
    const loadingMessages = [
        t('game.veo.loading1'),
        t('game.veo.loading2'),
        t('game.veo.loading3'),
        t('game.veo.loading4')
    ];
    const [loadingMessage, setLoadingMessage] = useState(loadingMessages[0]);

    useEffect(() => {
        const interval = window.setInterval(() => {
            setLoadingMessage(prev => {
                const currentIndex = loadingMessages.indexOf(prev);
                const nextIndex = (currentIndex + 1) % loadingMessages.length;
                return loadingMessages[nextIndex];
            });
        }, 5000);

        const task: GenerateVideoTask = {
            type: 'generate-video',
            id: `task-vid-${Date.now()}`,
            description: t('game.generatingVideo'),
            status: 'queued',
            priority: 20,
            prompt: request.prompt,
            model: settings.videoModel,
            sourceImageUrl: request.sourceImageUrl, // Pass source image URL if present
            onSuccess: onComplete,
            onError: (error) => {
                if (error instanceof Error && error.message.includes("API_KEY_NOT_FOUND")) { // Check for specific error message
                    resetKeySelection();
                }
                onCancel(error);
            }
        };
        addTask(task);

        return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [request.prompt, request.sourceImageUrl]); // Add sourceImageUrl to dependencies
    
    return (
        <div className="fixed inset-0 bg-gray-900/80 z-50 flex items-center justify-center backdrop-blur-sm p-4">
            <div className="bg-gray-800 rounded-lg p-8 text-center max-w-lg w-full border border-gray-700">
                <h2 className="text-2xl font-bold text-indigo-400 mb-4">{t('game.veo.title')}</h2>
                <p className="text-gray-300 mb-6">{loadingMessage}</p>
                <LoadingSpinner />
            </div>
        </div>
    );
};

export default VeoModal;