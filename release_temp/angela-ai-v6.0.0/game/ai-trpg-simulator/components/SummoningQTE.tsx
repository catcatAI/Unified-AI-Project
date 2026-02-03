import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useI18n } from '../context/i18n';
import { ArrowUpIcon, ArrowDownIcon, ArrowLeftIcon, ArrowRightIcon } from './icons';
import { useFocusTrap } from '../hooks/useFocusTrap';

interface SummoningQTEProps {
    challenge: {
        sequence: string[];
        timeLimit: number;
    };
    onResolve: (result: 'critical_failure' | 'failure' | 'success' | 'critical_success') => void;
    disableTimer?: boolean;
    enableVoiceInput?: boolean;
}

const keyMap: Record<string, string> = {
    'ArrowUp': '↑', 'ArrowDown': '↓', 'ArrowLeft': '←', 'ArrowRight': '→',
    'a': 'A', 'A': 'A', 'b': 'B', 'B': 'B'
};

const voiceCommandMap: Record<string, string> = {
    'up': '↑', 'down': '↓', 'left': '←', 'right': '→', 'a': 'A', 'b': 'B',
    '上': '↑', '下': '↓', '左': '←', '右': '→',
};

const iconMap: Record<string, React.ReactNode> = {
    '↑': <ArrowUpIcon className="w-6 h-6" />,
    '↓': <ArrowDownIcon className="w-6 h-6" />,
    '←': <ArrowLeftIcon className="w-6 h-6" />,
    '→': <ArrowRightIcon className="w-6 h-6" />,
    'A': <span className="font-bold text-xl">A</span>,
    'B': <span className="font-bold text-xl">B</span>,
};

const MicrophoneIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.49 6-3.31 6-6.72h-1.7z" />
  </svg>
);


const SummoningQTE: React.FC<SummoningQTEProps> = ({ challenge, onResolve, disableTimer = false, enableVoiceInput = false }) => {
    const { t, locale } = useI18n();
    const [currentIndex, setCurrentIndex] = useState(0);
    const [timeLeft, setTimeLeft] = useState(challenge.timeLimit * 1000);
    const [isListening, setIsListening] = useState(false);
    const timerRef = useRef<number | null>(null);
    const recognitionRef = useRef<any | null>(null);
    const modalRef = useFocusTrap<HTMLDivElement>();

    const resolve = useCallback((result: 'critical_failure' | 'failure' | 'success' | 'critical_success') => {
        if (timerRef.current) clearInterval(timerRef.current);
        if (recognitionRef.current) recognitionRef.current.stop();
        onResolve(result);
    }, [onResolve]);

    const handleButtonPress = useCallback((input: string) => {
         if (input === challenge.sequence[currentIndex]) {
            const newIndex = currentIndex + 1;
            if (newIndex === challenge.sequence.length) {
                const timeRatio = timeLeft / (challenge.timeLimit * 1000);
                resolve(timeRatio > 0.6 ? 'critical_success' : 'success');
            } else {
                setCurrentIndex(newIndex);
            }
        } else {
            resolve('failure');
        }
    }, [challenge.sequence, currentIndex, timeLeft, challenge.timeLimit, resolve]);
    
    useEffect(() => {
        if (disableTimer) return;

        timerRef.current = window.setInterval(() => {
            setTimeLeft(prev => {
                if (prev <= 100) {
                    resolve('critical_failure');
                    return 0;
                }
                return prev - 100;
            });
        }, 100);

        return () => {
            if (timerRef.current) clearInterval(timerRef.current);
        };
    }, [resolve, disableTimer]);
    
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                e.preventDefault();
                resolve('failure');
                return;
            }
            const input = keyMap[e.key];
            if (!input) return;
            e.preventDefault();
            handleButtonPress(input);
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [currentIndex, challenge, timeLeft, resolve, handleButtonPress]);

    const toggleVoiceInput = () => {
        if (isListening) {
            recognitionRef.current?.stop();
            return;
        }

        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert('Speech recognition not supported in this browser.');
            return;
        }

        if (!recognitionRef.current) {
            const recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = false;
            recognition.lang = locale === 'zh' ? 'zh-CN' : 'en-US';

            recognition.onstart = () => setIsListening(true);
            recognition.onend = () => setIsListening(false);
            recognition.onerror = (event: any) => {
                console.error('Speech recognition error', event.error);
                setIsListening(false);
            };
            recognition.onresult = (event: any) => {
                const last = event.results.length - 1;
                const command = event.results[last][0].transcript.trim().toLowerCase();
                const mappedCommand = voiceCommandMap[command];
                if (mappedCommand) {
                    handleButtonPress(mappedCommand);
                }
            };
            recognitionRef.current = recognition;
        }
        
        recognitionRef.current.start();
    };

    const timePercentage = (timeLeft / (challenge.timeLimit * 1000)) * 100;
    const dPadButtonClasses = "p-3 bg-gray-700/80 hover:bg-gray-700 aspect-square flex items-center justify-center rounded-lg transition-all active:bg-indigo-600 active:scale-110 active:ring-2 ring-white";
    const actionButtonClasses = "w-20 h-20 rounded-full font-bold text-white transition-all active:scale-110 active:ring-2 ring-white";

    return (
        <div className="fixed inset-0 bg-black/80 z-[100] flex items-center justify-center p-4 backdrop-blur-sm">
            <div ref={modalRef} role="dialog" aria-modal="true" aria-labelledby="qte-title" className="bg-gray-900/80 rounded-lg border-2 border-indigo-500/50 shadow-lg w-full max-w-md text-center p-8">
                <h2 id="qte-title" className="text-2xl font-bold text-indigo-400 mb-2">{t('summon.qte.title')}</h2>
                <p className="text-gray-300 mb-6">{t('summon.qte.instruction')}</p>
                
                <div className="flex justify-center items-center gap-2 h-16 bg-black/30 p-4 rounded-md">
                    {challenge.sequence.map((char, index) => (
                        <div key={index} className={`w-10 h-10 flex items-center justify-center rounded-md border-2 transition-colors ${
                            index < currentIndex ? 'bg-green-500/50 border-green-400 text-white' : 
                            index === currentIndex ? 'bg-indigo-500/50 border-indigo-400 text-white animate-pulse' : 
                            'bg-gray-700 border-gray-600 text-gray-400'
                        }`}>
                            {iconMap[char]}
                        </div>
                    ))}
                </div>

                {!disableTimer && (
                    <div className="w-full bg-gray-600 rounded-full h-2.5 mt-6">
                        <div className="bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 h-2.5 rounded-full transition-all duration-100 ease-linear" style={{ width: `${timePercentage}%` }}></div>
                    </div>
                )}

                {enableVoiceInput && (
                    <div className="mt-6 flex justify-center items-center gap-4">
                        <button onClick={toggleVoiceInput} aria-label={t('summon.qte.ariaLabels.toggleVoice')} className={`p-3 rounded-full transition-colors ${isListening ? 'bg-red-500 animate-pulse' : 'bg-gray-600 hover:bg-gray-500'}`}>
                            <MicrophoneIcon className="w-6 h-6 text-white" />
                        </button>
                        {isListening && <p className="text-sm text-gray-300">{t('summon.qte.listening')}</p>}
                    </div>
                )}
                
                 {/* On-screen controls for mobile */}
                <div className="mt-8 flex gap-8 p-4 items-center justify-center sm:hidden">
                    <div className="grid grid-cols-3 gap-2 w-40 h-40">
                        <div />
                        <button type="button" onClick={() => handleButtonPress('↑')} className={dPadButtonClasses}><ArrowUpIcon className="w-10 h-10" /></button>
                        <div />
                        <button type="button" onClick={() => handleButtonPress('←')} className={dPadButtonClasses}><ArrowLeftIcon className="w-10 h-10" /></button>
                        <div />
                        <button type="button" onClick={() => handleButtonPress('→')} className={dPadButtonClasses}><ArrowRightIcon className="w-10 h-10" /></button>
                        <div />
                        <button type="button" onClick={() => handleButtonPress('↓')} className={dPadButtonClasses}><ArrowDownIcon className="w-10 h-10" /></button>
                        <div />
                    </div>
                    <div className="flex items-center gap-4">
                        <button type="button" onClick={() => handleButtonPress('B')} className={`${actionButtonClasses} bg-yellow-500 hover:bg-yellow-600`}>B</button>
                        <button type="button" onClick={() => handleButtonPress('A')} className={`${actionButtonClasses} bg-red-600 hover:bg-red-700`}>A</button>
                    </div>
                </div>

                <div className="mt-6">
                    <button onClick={() => resolve('failure')} className="text-gray-400 hover:text-white text-sm underline">
                        {t('summon.qte.cancel')}
                    </button>
                </div>

            </div>
        </div>
    );
};

export default SummoningQTE;