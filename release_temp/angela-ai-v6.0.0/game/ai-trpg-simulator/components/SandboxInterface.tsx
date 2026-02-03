import React from 'react';
import { PlayerAction } from '../types';
import { useI18n } from '../context/i18n';
import { ArrowUpIcon, ArrowDownIcon, ArrowLeftIcon, ArrowRightIcon } from './icons';

interface SandboxInterfaceProps {
    onAction: (action: PlayerAction) => void;
    isBusy: boolean;
    contextualActionLabel: string;
}

const SandboxInterface: React.FC<SandboxInterfaceProps> = ({ onAction, isBusy, contextualActionLabel }) => {
    const { t } = useI18n();
    
    const handleDirectionalPress = (direction: 'up' | 'down' | 'left' | 'right') => {
        onAction({ type: 'move', direction });
    };

    const handleActionPress = (button: 'A' | 'B') => {
        onAction({ type: 'action', button });
    };
    
    const dPadButtonClasses = "p-3 bg-gray-700/80 hover:bg-gray-700 aspect-square flex items-center justify-center rounded-lg transition-all active:bg-indigo-600 active:scale-110 active:ring-2 ring-white disabled:opacity-30";
    const actionButtonClasses = "w-16 h-16 rounded-full font-bold text-white transition-all active:scale-110 active:ring-2 ring-white disabled:opacity-30 flex items-center justify-center text-xl";

    const buttonALabel = contextualActionLabel || t('game.ariaLabels.buttonA');

    return (
        <div className="flex justify-between items-center w-full px-4 py-2">
            {/* D-Pad on the left */}
            <div className="grid grid-cols-3 gap-1 w-32">
                <div />
                <button type="button" onClick={() => handleDirectionalPress('up')} className={dPadButtonClasses} disabled={isBusy} aria-label={t('game.ariaLabels.dpadUp')}><ArrowUpIcon className="w-6 h-6" /></button>
                <div />
                <button type="button" onClick={() => handleDirectionalPress('left')} className={dPadButtonClasses} disabled={isBusy} aria-label={t('game.ariaLabels.dpadLeft')}><ArrowLeftIcon className="w-6 h-6" /></button>
                <div />
                <button type="button" onClick={() => handleDirectionalPress('right')} className={dPadButtonClasses} disabled={isBusy} aria-label={t('game.ariaLabels.dpadRight')}><ArrowRightIcon className="w-6 h-6" /></button>
                <div />
                <button type="button" onClick={() => handleDirectionalPress('down')} className={dPadButtonClasses} disabled={isBusy} aria-label={t('game.ariaLabels.dpadDown')}><ArrowDownIcon className="w-6 h-6" /></button>
                <div />
            </div>
            {/* Action Buttons on the right */}
            <div className="flex items-center gap-4">
                <button type="button" onClick={() => handleActionPress('B')} className={`${actionButtonClasses} bg-yellow-500/80 hover:bg-yellow-600`} disabled={isBusy} aria-label={t('game.ariaLabels.buttonB')}>B</button>
                <div className="relative">
                    <button type="button" onClick={() => handleActionPress('A')} className={`${actionButtonClasses} bg-red-600/80 hover:bg-red-700`} disabled={isBusy} aria-label={buttonALabel}>A</button>
                    {contextualActionLabel && <div className="absolute -top-5 left-1/2 -translate-x-1/2 bg-black/50 text-white text-xs font-semibold px-2 py-1 rounded select-none pointer-events-none">{contextualActionLabel}</div>}
                </div>
            </div>
        </div>
    );
};

export default SandboxInterface;
