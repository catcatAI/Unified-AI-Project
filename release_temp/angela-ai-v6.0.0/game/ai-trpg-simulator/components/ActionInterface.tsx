import React, { useState, useEffect, useRef } from 'react';
import { Character, Enemy } from '../types';

interface ActionInterfaceProps {
    player: Character;
    enemies: Enemy[];
    choices: string[];
    onChoice: (choice: string) => void;
    isBusy: boolean;
}

const HealthBar: React.FC<{ name: string; hp: number; maxHp: number; color: string; isSelected?: boolean }> = ({ name, hp, maxHp, color, isSelected = false }) => {
    const percentage = Math.max(0, (hp / maxHp) * 100);
    return (
        <div className={`p-2 rounded-md transition-all duration-200 ${isSelected ? 'bg-gray-700 ring-2 ring-red-500' : 'bg-gray-900/50'}`}>
            <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-gray-300">{name}</span>
                <span className="text-sm font-mono text-gray-400">{hp} / {maxHp}</span>
            </div>
            <div className="w-full bg-gray-600 rounded-full h-2">
                <div className={`${color} h-2 rounded-full transition-all duration-500`} style={{ width: `${percentage}%` }}></div>
            </div>
        </div>
    );
};

const ActionInterface: React.FC<ActionInterfaceProps> = ({ player, enemies, choices, onChoice, isBusy }) => {
    const [selectedEnemyName, setSelectedEnemyName] = useState<string | null>(enemies.length > 0 ? enemies[0].name : null);
    const debounceLock = useRef(false);

    useEffect(() => {
        if (selectedEnemyName && !enemies.some(e => e.name === selectedEnemyName)) {
            setSelectedEnemyName(enemies.length > 0 ? enemies.find(e => e.hp > 0)?.name ?? null : null);
        }
        if (!selectedEnemyName && enemies.length > 0) {
            setSelectedEnemyName(enemies.find(e => e.hp > 0)?.name ?? null);
        }
    }, [enemies, selectedEnemyName]);

    const handleChoice = (choice: string) => {
        if (debounceLock.current || isBusy) return;
        debounceLock.current = true;

        if (selectedEnemyName) {
            onChoice(`${choice} (Target: ${selectedEnemyName})`);
        } else {
            onChoice(choice);
        }
        
        setTimeout(() => {
            debounceLock.current = false;
        }, 500);
    };

    const aliveEnemies = enemies.filter(e => e.hp > 0);
    const defeatedEnemies = enemies.filter(e => e.hp <= 0);

    return (
        <div className="flex-shrink-0 p-2 border-t border-gray-700">
            <div className="bg-red-900/20 p-2 rounded-lg border border-red-700/50">
                <div className="space-y-2 mb-2">
                    <HealthBar name={player.name} hp={player.stats.hp} maxHp={player.stats.maxHp} color="bg-green-500" />
                    {aliveEnemies.map(enemy => (
                         <button 
                            key={enemy.name} 
                            onClick={() => setSelectedEnemyName(enemy.name)}
                            className="w-full text-left"
                            aria-pressed={selectedEnemyName === enemy.name}
                        >
                            <HealthBar name={enemy.name} hp={enemy.hp} maxHp={enemy.maxHp} color="bg-red-500" isSelected={selectedEnemyName === enemy.name} />
                        </button>
                    ))}
                    {defeatedEnemies.map(enemy => (
                        <div key={enemy.name} className="opacity-50">
                             <HealthBar name={enemy.name} hp={enemy.hp} maxHp={enemy.maxHp} color="bg-gray-500" />
                        </div>
                    ))}
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    {choices.map((choice, index) => (
                        <button
                            key={index}
                            onClick={() => handleChoice(choice)}
                            disabled={isBusy}
                            className="bg-red-800/50 hover:bg-red-700/70 text-white font-semibold py-2 px-3 rounded-md transition-colors active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {choice}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ActionInterface;