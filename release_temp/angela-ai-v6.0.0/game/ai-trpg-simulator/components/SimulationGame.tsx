import React from 'react';
import { SimulationState } from '../types';
import { useI18n } from '../context/i18n';

interface SimulationGameProps {
    state: SimulationState;
    onChoice: (choice: string) => void;
    error: string | null;
    onRetry: () => void;
}

const SimulationGame: React.FC<SimulationGameProps> = ({ state, onChoice, error, onRetry }) => {
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
        <div className="bg-yellow-900/20 p-4 rounded-lg border border-yellow-700/50">
            <div className="flex justify-around items-center mb-4 p-2 bg-black/20 rounded-md">
                {Object.entries(state.resources).map(([key, value]) => (
                    <div key={key} className="text-center">
                        <p className="text-xs text-yellow-300 capitalize">{key}</p>
                        <p className="text-xl font-bold text-white">{value}</p>
                    </div>
                ))}
            </div>
            <p className="whitespace-pre-wrap text-gray-300 mb-4 min-h-[6em]">{state.narrative}</p>
            <div className="grid grid-cols-1 gap-2">
                {state.choices.map((choice, index) => (
                    <button
                        key={index}
                        onClick={() => onChoice(choice)}
                        className="bg-yellow-800/50 hover:bg-yellow-700/70 text-white font-semibold py-2 px-3 rounded-md transition-colors text-left"
                    >
                        {choice}
                    </button>
                ))}
            </div>
        </div>
    );
};

export default SimulationGame;