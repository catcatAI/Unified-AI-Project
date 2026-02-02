import React from 'react';
import { ActionState } from '../types';
import { useI18n } from '../context/i18n';

interface ActionGameProps {
    state: ActionState;
    onChoice: (choice: string) => void;
    error: string | null;
    onRetry: () => void;
}

const HealthBar: React.FC<{ name: string, hp: number, maxHp: number, color: string }> = ({ name, hp, maxHp, color }) => {
    const percentage = Math.max(0, (hp / maxHp) * 100);
    return (
        <div>
            <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-gray-300">{name}</span>
                <span className="text-sm font-mono text-gray-400">{hp} / {maxHp}</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-4">
                <div className={`${color} h-4 rounded-full transition-all duration-500`} style={{ width: `${percentage}%` }}></div>
            </div>
        </div>
    );
};

const ActionGame: React.FC<ActionGameProps> = ({ state, onChoice, error, onRetry }) => {
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
    
    const isGameOver = state.playerHP <= 0 || state.enemyHP <= 0;

    return (
        <div className="bg-red-900/20 p-4 rounded-lg border border-red-700/50">
            <div className="space-y-3 mb-4">
                <HealthBar name={t('frameworkGenerator.actionGame.player')} hp={state.playerHP} maxHp={100} color="bg-green-500" />
                <HealthBar name={t('frameworkGenerator.actionGame.enemy')} hp={state.enemyHP} maxHp={100} color="bg-red-500" />
            </div>
            <p className="whitespace-pre-wrap text-gray-300 mb-4 min-h-[6em]">{state.narrative}</p>
            
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {!isGameOver ? state.choices.map((choice, index) => (
                    <button
                        key={index}
                        onClick={() => onChoice(choice)}
                        className="bg-red-800/50 hover:bg-red-700/70 text-white font-semibold py-2 px-3 rounded-md transition-colors"
                    >
                        {choice}
                    </button>
                )) : (
                    <p className="col-span-3 text-center font-bold text-xl py-4">{state.playerHP > 0 ? "You Won!" : "Game Over"}</p>
                )}
            </div>
        </div>
    );
};

export default ActionGame;