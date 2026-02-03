import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useI18n } from '../context/i18n';
import { useFocusTrap } from '../hooks/useFocusTrap';
import { CloseIcon, MicrophoneIcon, PlayIcon, AudioWaveIcon } from './icons';
import { blobToBase64 } from '../services/utils';

interface AudioRecordingModalProps {
    isOpen: boolean;
    onClose: () => void;
    onRecordComplete: (dataUrl: string) => void;
}

type RecordingState = 'idle' | 'recording' | 'recorded';

const AudioRecordingModal: React.FC<AudioRecordingModalProps> = ({ isOpen, onClose, onRecordComplete }) => {
    const { t } = useI18n();
    const modalRef = useFocusTrap<HTMLDivElement>();
    const streamRef = useRef<MediaStream | null>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const audioRef = useRef<HTMLAudioElement>(null);

    const [error, setError] = useState('');
    const [recordingState, setRecordingState] = useState<RecordingState>('idle');
    const [audioUrl, setAudioUrl] = useState<string | null>(null);

    const cleanup = useCallback(() => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
            mediaRecorderRef.current.stop();
        }
        mediaRecorderRef.current = null;
        audioChunksRef.current = [];
        if (audioUrl) {
            URL.revokeObjectURL(audioUrl);
            setAudioUrl(null);
        }
    }, [audioUrl]);

    useEffect(() => {
        if (!isOpen) {
            cleanup();
            setRecordingState('idle');
            setError('');
            return;
        }

        const startMic = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                streamRef.current = stream;
            } catch (err) {
                console.error("Microphone error:", err);
                setError(t('creativeHub.audioModal.error'));
            }
        };

        startMic();

        return cleanup;
    }, [isOpen, cleanup, t]);
    
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose(); };
        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [onClose]);

    const startRecording = () => {
        if (!streamRef.current) {
            setError(t('creativeHub.audioModal.error'));
            return;
        }
        audioChunksRef.current = [];
        const recorder = new MediaRecorder(streamRef.current);
        mediaRecorderRef.current = recorder;

        recorder.ondataavailable = event => {
            audioChunksRef.current.push(event.data);
        };

        recorder.onstop = () => {
            const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
            const url = URL.createObjectURL(audioBlob);
            setAudioUrl(url);
            setRecordingState('recorded');
        };

        recorder.start();
        setRecordingState('recording');
    };

    const stopRecording = () => {
        mediaRecorderRef.current?.stop();
    };

    const handleRetake = () => {
        setRecordingState('idle');
        if (audioUrl) {
            URL.revokeObjectURL(audioUrl);
            setAudioUrl(null);
        }
    };

    const handleUseAudio = async () => {
        if (audioUrl) {
            const blob = await fetch(audioUrl).then(r => r.blob());
            const dataUrl = await blobToBase64(blob);
            onRecordComplete(dataUrl);
        }
    };

    return isOpen ? (
        <div className="fixed inset-0 bg-black/70 z-[101] flex items-center justify-center p-4 backdrop-blur-sm" onClick={onClose}>
            <div
                ref={modalRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby="audio-record-title"
                className="bg-gray-800 rounded-lg border-2 border-gray-700 shadow-lg w-full max-w-md p-4 flex flex-col"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="flex justify-between items-center mb-4 flex-shrink-0">
                    <h2 id="audio-record-title" className="text-xl font-bold text-indigo-400">{t('creativeHub.audioModal.title')}</h2>
                    <button onClick={onClose} className="p-1 rounded-full text-gray-400 hover:bg-gray-700" aria-label={t('game.ariaLabels.closeModal')}>
                        <CloseIcon className="w-6 h-6" />
                    </button>
                </div>
                
                <div className="w-full h-48 bg-black/30 rounded-md flex items-center justify-center">
                    {error ? <p className="text-red-400 p-4">{error}</p>
                     : recordingState === 'recorded' && audioUrl ? <audio ref={audioRef} src={audioUrl} controls className="w-full px-4" />
                     : <AudioWaveIcon className={`w-20 h-20 text-gray-500 ${recordingState === 'recording' ? 'text-red-500 animate-pulse' : ''}`} />
                    }
                </div>
                
                <p className="text-center text-sm text-gray-400 mt-2 h-5">
                    {recordingState === 'recording' && t('creativeHub.audioModal.recording')}
                    {recordingState === 'recorded' && t('creativeHub.audioModal.preview')}
                </p>

                <div className="mt-4 flex gap-2 justify-center">
                    {recordingState === 'idle' && (
                        <button onClick={startRecording} disabled={!!error} className="bg-red-600 text-white font-bold py-3 px-6 rounded-full hover:bg-red-700 transition-colors disabled:bg-gray-500 flex items-center gap-2">
                           <MicrophoneIcon className="w-5 h-5"/> {t('creativeHub.audioModal.start')}
                        </button>
                    )}
                    {recordingState === 'recording' && (
                        <button onClick={stopRecording} className="bg-gray-600 text-white font-bold py-3 px-6 rounded-full hover:bg-gray-700 transition-colors">
                           {t('creativeHub.audioModal.stop')}
                        </button>
                    )}
                     {recordingState === 'recorded' && (
                        <>
                            <button onClick={handleRetake} className="flex-1 bg-gray-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors">
                                {t('creativeHub.audioModal.retake')}
                            </button>
                            <button onClick={handleUseAudio} className="flex-1 bg-indigo-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors">
                                {t('creativeHub.audioModal.use')}
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div>
    ) : null;
};

export default AudioRecordingModal;
