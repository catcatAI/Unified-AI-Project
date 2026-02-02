import React from 'react';
import { AdventureState } from '../types';
import { useI18n } from '../context/i18n';

interface AdventureGameProps {
    state: AdventureState;
    onChoice: (choice: string) => void;
    error: string | null;
    onRetry: () => void;
}

const AdventureGame: React.FC<AdventureGameProps> = ({ state, onChoice, error, onRetry }) => {
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
        <div className="bg-cyan-900/20 p-4 rounded-lg border border-cyan-700/50">
            <p className="whitespace-pre-wrap text-gray-300 mb-4 min-h-[8em]">{state.narrative}</p>
            <div className="grid grid-cols-1 gap-2">
                {state.choices.map((choice, index) => (
                    <button
                        key={index}
                        onClick={() => onChoice(choice)}
                        className="bg-cyan-800/50 hover:bg-cyan-700/70 text-white font-semibold py-2 px-3 rounded-md transition-colors text-left"
                    >
                        {choice}
                    </button>
                ))}
            </div>
        </div>
    );
};

export default AdventureGame;