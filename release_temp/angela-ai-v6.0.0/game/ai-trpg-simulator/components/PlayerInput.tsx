import React, { useState, useRef, useCallback, useLayoutEffect, useEffect } from 'react';
import { useI18n } from '../context/i18n';
import { useSettings } from '../context/settings';
import { PaperclipIcon, MicrophoneIcon } from './icons';
import { CodexAsset } from '../types';
import ContextPreview from './ContextPreview';
import { useGameContext } from './context/GameContext';

export const PlayerInput: React.FC<{
    onPlayerAction: (action: string) => void;
    suggestedActions: string[];
    attachedAsset: CodexAsset | null;
    onAttachAsset: () => void;
    onClearAttachment: () => void;
}> = ({ onPlayerAction, suggestedActions, attachedAsset, onAttachAsset, onClearAttachment }) => {
    const { t } = useI18n();
    const settings = useSettings();
    const { isBusy } = useGameContext();
    const [input, setInput] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const debounceLock = useRef(false);

    // Auto-resize textarea
    useLayoutEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    }, [input]);

    const handleSubmit = useCallback((e?: React.FormEvent) => {
        e?.preventDefault();
        if ((!input.trim() && !attachedAsset) || debounceLock.current || isBusy) return;
        debounceLock.current = true;
        onPlayerAction(input);
        setInput('');
        setTimeout(() => { debounceLock.current = false; }, 500);
    }, [input, attachedAsset, debounceLock, isBusy, onPlayerAction]);

    const handleSuggestedActionClick = useCallback((action: string) => {
        if (debounceLock.current || isBusy) return;
        debounceLock.current = true;
        onPlayerAction(action);
        setInput('');
        setTimeout(() => { debounceLock.current = false; }, 500);
    }, [debounceLock, isBusy, onPlayerAction]);

    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    }, [handleSubmit]);

    // Voice input (placeholder for now, actual implementation would be in a modal or dedicated component)
    const [isRecording, setIsRecording] = useState(false);
    const [recognition, setRecognition] = useState<any>(null); // State for SpeechRecognition object

    useEffect(() => {
        if (!settings.enableVoiceInput) {
            if (recognition) {
                recognition.stop();
                setRecognition(null);
            }
            return;
        }

        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn("Speech Recognition API not supported in this browser.");
            return;
        }

        const rec = new SpeechRecognition();
        rec.continuous = false; // Only get one result per utterance
        rec.interimResults = false;
        rec.lang = settings.locale === 'zh' ? 'zh-CN' : 'en-US';

        rec.onstart = () => setIsRecording(true);
        rec.onend = () => setIsRecording(false);
        rec.onerror = (event: any) => console.error("Speech recognition error:", event.error);
        rec.onresult = (event: any) => {
            const transcript = event.results[0][0].transcript;
            setInput(prev => prev + transcript);
        };

        setRecognition(rec);

        return () => {
            rec.stop();
            setRecognition(null);
        };
    }, [settings.enableVoiceInput, settings.locale]);

    const toggleVoiceInput = () => {
        if (isRecording) {
            recognition?.stop();
        } else {
            setInput(''); // Clear input before starting voice
            recognition?.start();
        }
    };

    return (
        <div className="p-4 bg-gray-900/60 backdrop-blur-sm border-t border-gray-700 flex flex-col gap-3">
            {attachedAsset && (
                <ContextPreview 
                    asset={attachedAsset} 
                    onClear={onClearAttachment}
                    contextMessage={t('playerInput.attachedContext')}
                    clearMessage={t('playerInput.clearContext')}
                />
            )}
            <div className="flex items-end gap-2">
                <button
                    onClick={onAttachAsset}
                    className="p-3 bg-gray-700/80 hover:bg-gray-700 text-gray-300 rounded-lg flex-shrink-0"
                    title={t('playerInput.attachAsset')}
                    aria-label={t('playerInput.attachAsset')}
                    disabled={isBusy}
                    aria-busy={isBusy}
                >
                    <PaperclipIcon className="w-5 h-5" />
                </button>
                {settings.enableVoiceInput && recognition && (
                    <button
                        onClick={toggleVoiceInput}
                        className={`p-3 rounded-lg flex-shrink-0 transition-colors ${isRecording ? 'bg-red-600 animate-pulse' : 'bg-gray-700/80 hover:bg-gray-700 text-gray-300'}`}
                        title={isRecording ? t('playerInput.stopVoiceInput') : t('playerInput.startVoiceInput')}
                        aria-label={isRecording ? t('playerInput.stopVoiceInput') : t('playerInput.startVoiceInput')}
                        disabled={isBusy}
                        aria-busy={isBusy}
                    >
                        <MicrophoneIcon className="w-5 h-5" />
                    </button>
                )}
                <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={t('playerInput.placeholder')}
                    rows={1}
                    className="flex-1 resize-none bg-gray-800/80 border border-gray-600 rounded-lg p-3 text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:outline-none transition-all duration-200 min-h-[48px]"
                    disabled={isBusy}
                    aria-label={t('playerInput.textAreaLabel')}
                    aria-busy={isBusy}
                />
                <button
                    onClick={handleSubmit}
                    className="p-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg flex-shrink-0 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={isBusy || (!input.trim() && !attachedAsset)}
                    aria-label={t('playerInput.submitButton')}
                    aria-busy={isBusy}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 rotate-90" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2l-11 20h22z" />
                    </svg>
                </button>
            </div>
            {suggestedActions && suggestedActions.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-700/50">
                    {suggestedActions.map((action, index) => (
                        <button
                            key={index}
                            onClick={() => handleSuggestedActionClick(action)}
                            disabled={isBusy}
                            className="text-xs bg-gray-700/80 hover:bg-gray-700 text-gray-300 px-3 py-1.5 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {action}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};