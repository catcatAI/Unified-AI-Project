import React from 'react';
import { DiceRoll } from '../types';
import { useI18n } from '../context/i18n';
import { DiceIcon } from './icons';

interface DiceRollDisplayProps {
    roll: DiceRoll;
}

const DiceRollDisplay: React.FC<DiceRollDisplayProps> = ({ roll }) => {
    const { t } = useI18n();
    const successColor = roll.successLevel.includes('success') ? 'text-green-400 border-green-500/50' : 'text-red-400 border-red-500/50';

    return (
        <div className={`mt-2 p-3 rounded-md border-l-4 ${successColor} bg-gray-900/50`}>
            <div className="flex items-center gap-3">
                <DiceIcon className={`w-6 h-6 flex-shrink-0 ${successColor}`} />
                <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-200 truncate">
                        {roll.characterName} {t('game.diceRoll.attempts')} <span className="italic">"{roll.action}"</span>
                    </p>
                    <p className={`text-xs font-mono ${successColor}`}>
                        {t('game.diceRoll.roll')}: {roll.roll} → <span className="font-bold text-base">{roll.result}</span> | <span className="capitalize">{roll.successLevel.replace('_', ' ')}</span>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default DiceRollDisplay;
