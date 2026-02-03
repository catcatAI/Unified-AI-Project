import React from 'react';
import { PuzzleState } from '../types';
import { useI18n } from '../context/i18n';

interface PuzzleGameProps {
    state: PuzzleState;
    onChoice: (choice: string) => void;
    error: string | null;
    onRetry: () => void;
}

const PuzzleGame: React.FC<PuzzleGameProps> = ({ state, onChoice, error, onRetry }) => {
    const { t } = useI18n();
    
    if (error) {
        return (
            <div className="text-center p-4">
                <p className="text-red-400 mb-4">{error}</p>
                <button onClick={onRetry} className="bg-red-800/80 hover:bg-red-700 text-white font-semibold py-1 px-3 rounded-md text-sm transition-colors">
                    {t('frameworkGenerator.retry')}
                </button>
            </div>
        );
    }
    
    return (
        <div className="bg-purple-900/20 p-4 rounded-lg border border-purple-700/50">
            <p className="whitespace-pre-wrap text-gray-300 mb-4 min-h-[8em]">{state.narrative}</p>
            <div className="grid grid-cols-1 gap-2">
                {state.choices.map((choice, index) => (
                    <button
                        key={index}
                        onClick={() => onChoice(choice)}
                        className="bg-purple-800/50 hover:bg-purple-700/70 text-white font-semibold py-2 px-3 rounded-md transition-colors text-left"
                    >
                        {choice}
                    </button>
                ))}
            </div>
        </div>
    );
};

export default PuzzleGame;